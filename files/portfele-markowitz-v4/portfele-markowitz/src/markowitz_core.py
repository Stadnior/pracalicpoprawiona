"""
markowitz_core.py – wspólna logika dla wszystkich portfeli (metoda Markowitza, long-only).
import os
import numpy as np
import pandas as pd
from scipy.optimize import minimize, linprog
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ============================== PARAMETRY ==============================
DNI = 252
KAPITAL = 10_000                                   # kapitał początkowy w okresie testowym
OKRES_UCZACY = ("2012-01-01", "2020-12-31")
OKRESY_TESTOWE = {"2021": ("2021-01-01", "2021-12-31"),
                  "2021-2023": ("2021-01-01", "2023-12-31"),
                  "2021-2025": ("2021-01-01", "2025-12-31")}
LIMITY_WAGI = [1.0, 0.5, 0.4, 0.3, 0.2, 0.1]       # 1.0 = bez limitu (wariant główny)
PLIK_NBP = "data/stopa_referencyjna_NBP.csv"
PLIK_FX = "data/USDPLN.csv"
WYJSCIE = "wyniki/"
MIN_POKRYCIE = 0.95                                # min. udział dni z cenami w okresie uczącym
# =======================================================================


# ------------------------------------------------------------- dane
def rf_nbp(data):
    """Stopa referencyjna NBP (ułamek rocznie) obowiązująca w danym dniu."""
    t = pd.read_csv(PLIK_NBP, parse_dates=["obowiazuje_od"]).sort_values("obowiazuje_od")
    t = t[t["obowiazuje_od"] <= pd.Timestamp(data)]
    if t.empty:
        raise ValueError(f"Brak stopy NBP dla daty {data} w {PLIK_NBP}")
    return t["stopa_proc"].iloc[-1] / 100


def rf_okresu_testowego(koniec):
    """Średnia ze stóp NBP na koniec kolejnych lat okresu testowego (2021 .. rok końca)."""
    lata = range(2021, pd.Timestamp(koniec).year + 1)
    return float(np.mean([rf_nbp(f"{y}-12-31") for y in lata]))


def swieta_pl(lata):
    """Dni ustawowo wolne od pracy w Polsce (GPW nieczynna)."""
    sw = set()
    stale = [(1, 1), (1, 6), (5, 1), (5, 3), (8, 15), (11, 1), (11, 11), (12, 25), (12, 26)]
    for y in lata:
        for m, d in stale:
            sw.add(pd.Timestamp(y, m, d))
        a = y % 19
        b, c = divmod(y, 100)
        d, e = divmod(b, 4)
        f = (b + 8) // 25
        g = (b - f + 1) // 3
        h = (19 * a + b - d - g + 15) % 30
        i, k = divmod(c, 4)
        l = (32 + 2 * e + 2 * i - h - k) % 7
        m_val = (a + 11 * h + 22 * l) // 451
        month, day = divmod(h + l - 7 * m_val + 114, 31)
        wielkanoc = pd.Timestamp(y, month, day + 1)
        sw.add(wielkanoc + pd.Timedelta(days=1))   # Poniedziałek Wielkanocny
        sw.add(wielkanoc + pd.Timedelta(days=60))  # Boże Ciało
    return sw


def wczytaj_ceny(cfg):
    if not os.path.exists(cfg["plik"]):
        raise FileNotFoundError(
            f"Brak pliku {cfg['plik']}. Pobierz dane skryptem src/pobierz_dane.py "
            f"(albo wgraj plik do katalogu data/).")
    px = pd.read_csv(cfg["plik"], index_col=0, parse_dates=True).sort_index()
    if cfg.get("kolumny"):
        px = px[cfg["kolumny"]]
    px = px.drop(columns=[c for c in cfg.get("usun", []) if c in px.columns])
    return px


def na_pln(px, waluta):
    """Przelicza ceny na PLN (jeśli waluta = USD). Zwraca (ceny, etykieta waluty)."""
    if waluta == "PLN":
        return px, "PLN"
    if not os.path.exists(PLIK_FX):
        print(f"!!! UWAGA: brak {PLIK_FX} – obliczenia w USD, NIE w PLN (uzupełnij dane).")
        return px, "USD (bez przeliczenia na PLN)"
    fx = pd.read_csv(PLIK_FX, index_col=0, parse_dates=True).iloc[:, 0].sort_index()
    fx = fx.reindex(px.index.union(fx.index)).ffill().reindex(px.index)
    return px.mul(fx, axis=0), "PLN"


def przygotuj(px, waluta="PLN"):
    """Wybiera aktywa z kompletną historią i usuwa dni niehandlowe (błędy Yahoo dla GPW)."""
    start, koniec_ucz = OKRES_UCZACY
    koniec_test = max(k for _, k in OKRESY_TESTOWE.values())
    px = px.loc[start:koniec_test]
    ucz = px.loc[:koniec_ucz]
    odrzucone = {}
    for c in px.columns:
        s = ucz[c]
        if s.notna().mean() < MIN_POKRYCIE or s.first_valid_index() > ucz.index[0] + pd.Timedelta(days=30):
            odrzucone[c] = "za krótka/niepełna historia w okresie uczącym"
        elif px[c].last_valid_index() < pd.Timestamp(koniec_test) - pd.Timedelta(days=10):
            odrzucone[c] = "brak notowań do końca okresu testowego"
    px = px.drop(columns=list(odrzucone)).ffill(limit=5).dropna()

    # Usunięcie świąt i dni bez obrotu dla GPW (nie dotyka S&P 500 ani ETF-ów)
    if waluta == "PLN":
        sw = swieta_pl(range(px.index.year.min(), px.index.year.max() + 1))
        px = px.loc[~px.index.isin(sw)]
        if px.shape[1] >= 5:
            brak_handlu = (px.pct_change().abs() > 1e-12).mean(axis=1) < 0.20
            brak_handlu.iloc[0] = False
            px = px.loc[~brak_handlu]
    return px, odrzucone


# ------------------------------------------------------------- miary
def metryki(r, rf, lata=None):
    """r – dzienne proste stopy zwrotu; rf – roczna stopa wolna od ryzyka (ułamek)."""
    cum = (1 + r).cumprod()
    if lata is None:
        lata = (r.index[-1] - r.index[0]).days / 365.25
    sr, vol = r.mean() * DNI, r.std() * np.sqrt(DNI)
    return {"Całkowita stopa zwrotu": cum.iloc[-1] - 1,
            "CAGR": cum.iloc[-1] ** (1 / lata) - 1,
            "Śr. roczna stopa zwrotu": sr,
            "Zmienność roczna": vol,
            "Rf": rf,
            "Sharpe": (sr - rf) / vol,
            "Maks. obsunięcie": (cum / np.maximum(cum.cummax(), 1) - 1).min()}


def wartosc_buy_and_hold(px, w, kapital=KAPITAL):
    """Wartość portfela przy strategii kup-i-trzymaj; px zaczyna się od dnia bazowego."""
    return kapital * (px / px.iloc[0]).mul(w, axis=1).sum(axis=1)


# ------------------------------------------------------------- optymalizacja
def _rozwiaz(cel, startowe, gora, ograniczenia, nazwa, sprawdz_zwrot=None):
    """SLSQP z kontrolą: success, suma wag = 1, granice; kilka punktów startowych."""
    n = len(startowe[0])
    najlepszy = None
    for w0 in startowe:
        res = minimize(cel, w0, bounds=[(0, gora)] * n, constraints=ograniczenia,
                       method="SLSQP", options=dict(maxiter=1000, ftol=1e-12))
        w = res.x
        ok = (res.success and abs(w.sum() - 1) < 1e-6 and (w > -1e-8).all() and (w < gora + 1e-8).all())
        if ok and sprawdz_zwrot is not None:
            ok = abs(w @ sprawdz_zwrot[0] - sprawdz_zwrot[1]) < 1e-6
        if ok and (najlepszy is None or res.fun < najlepszy.fun):
            najlepszy = res
    if najlepszy is None:
        raise RuntimeError(f"Optymalizacja '{nazwa}' nie osiągnęła zbieżności z poprawnymi ograniczeniami.")
    return najlepszy.x


def _czysc(w):
    w = np.where(w < 1e-6, 0.0, w)
    return w / w.sum()


def wagi_markowitza(mu, cov, rf, limit):
    """Zwraca (w_min_wariancja, w_max_sharpe) dla limitu wagi pojedynczego aktywa."""
    n = len(mu)
    rng = np.random.default_rng(0)
    starty = [np.ones(n) / n] + [rng.dirichlet(np.ones(n)) for _ in range(5)]
    suma1 = [{"type": "eq", "fun": lambda w: w.sum() - 1}]
    vol = lambda w: np.sqrt(max(w @ cov @ w, 1e-16))
    w_mv = _rozwiaz(lambda w: w @ cov @ w, starty, limit, suma1, "min. wariancja")
    w_ms = _rozwiaz(lambda w: -(w @ mu - rf) / vol(w), starty, limit, suma1, "maks. Sharpe")
    return _czysc(w_mv), _czysc(w_ms)


def granica_efektywna(mu, cov, w_mv, limit=1.0, punkty=40):
    n = len(mu)
    suma1 = [{"type": "eq", "fun": lambda w: w.sum() - 1}]
    zwrot_max = -linprog(-mu, A_eq=np.ones((1, n)), b_eq=[1], bounds=[(0, limit)] * n).fun
    wynik, w_prev, pominiete = [], w_mv, 0
    for t in np.linspace(w_mv @ mu, zwrot_max, punkty):
        war = suma1 + [{"type": "eq", "fun": lambda w, t=t: w @ mu - t}]
        try:
            w = _rozwiaz(lambda w: w @ cov @ w, [w_prev, np.ones(n) / n], limit, war,
                         "granica", sprawdz_zwrot=(mu, t))
            w_prev = w
            wynik.append((np.sqrt(w @ cov @ w), t))
        except RuntimeError:
            pominiete += 1
    if pominiete:
        print(f"   (granica efektywna: pominięto {pominiete} z {punkty} punktów bez zbieżności)")
    return pd.DataFrame(wynik, columns=["Zmienność", "Zwrot"])


# ------------------------------------------------------------- główna procedura
def run_portfolio(cfg):
    os.makedirs(WYJSCIE, exist_ok=True)
    nazwa = cfg["nazwa"]
    print(f"\n######## {cfg['tytul']} ########")
    px, waluta = na_pln(wczytaj_ceny(cfg), cfg["waluta"])
    px, odrzucone = przygotuj(px, cfg["waluta"])
    for c, powod in odrzucone.items():
        print(f"   pominięto {c}: {powod}")
    n = px.shape[1]
    print(f"   aktywa: {n}, waluta: {waluta}, dane: {px.index[0].date()} – {px.index[-1].date()}")

    px_ucz = px.loc[:OKRES_UCZACY[1]]
    ret = px_ucz.pct_change().dropna()
    mu, cov = ret.mean().values * DNI, ret.cov().values * DNI
    rf0 = rf_nbp(OKRES_UCZACY[1])                      # Rf przy konstrukcji portfela
    print(f"   okres uczący: {ret.index[0].date()} – {ret.index[-1].date()} ({len(ret)} obs.), Rf = {rf0:.2%}")
    baza = px_ucz.index[-1]                            # ostatni dzień okresu uczącego

    # --- wagi dla wszystkich limitów
    limity = [l for l in LIMITY_WAGI if l * n >= 1 - 1e-9]
    wagi = {("Równe wagi (1/N)", 1.0): np.ones(n) / n}
    for l in limity:
        w_mv, w_ms = wagi_markowitza(mu, cov, rf0, l)
        wagi[("Min. wariancja", l)] = w_mv
        wagi[("Maks. Sharpe", l)] = w_ms

    # --- miary: próba ucząca (stałe wagi) i testowa (buy-and-hold)
    lata_ucz = pd.Timestamp(OKRES_UCZACY[1]).year - pd.Timestamp(OKRES_UCZACY[0]).year + 1
    wiersze = []
    for (strat, l), w in wagi.items():
        wiersze.append({"Portfel": nazwa, "Strategia": strat, "Limit wagi": l, "Okres": "uczący 2012-2020",
                        **metryki(ret @ w, rf0, lata=lata_ucz)})
        for okres, (od, do) in OKRESY_TESTOWE.items():
            pt = px.loc[baza:do]
            v = wartosc_buy_and_hold(pt, pd.Series(w, index=px.columns))
            lata_test = pd.Timestamp(do).year - pd.Timestamp(od).year + 1
            wiersze.append({"Portfel": nazwa, "Strategia": strat, "Limit wagi": l,
                            "Okres": f"test {okres}",
                            **metryki(v.pct_change().dropna(), rf_okresu_testowego(do), lata=lata_test)})
    tab = pd.DataFrame(wiersze)
    tab["Waluta"] = waluta

    # --- granica efektywna (wariant bez limitu)
    gr = granica_efektywna(mu, cov, wagi[("Min. wariancja", 1.0)])
    pun = pd.DataFrame([{"Strategia": s, "Zmienność": np.sqrt(w @ cov @ w), "Zwrot": w @ mu, "Waluta": waluta}
                        for (s, l), w in wagi.items() if l == 1.0])

    # --- zapis
    gr.to_csv(f"{WYJSCIE}{nazwa}_granica.csv", index=False)
    pun.to_csv(f"{WYJSCIE}{nazwa}_punkty.csv", index=False)
    tab.to_csv(f"{WYJSCIE}{nazwa}_metryki.csv", index=False)
    kol = [f"{s} | limit {l:.0%}" for (s, l) in wagi]
    W = pd.DataFrame(np.column_stack(list(wagi.values())), index=px.columns, columns=kol)
    glowne = W[[c for c in W.columns if c.endswith("limit 100%")]]
    glowne.columns = [c.split(" |")[0] for c in glowne.columns]
    param = pd.DataFrame({"Parametr": ["Waluta", "Okres uczący", "Okresy testowe", "Rf przy konstrukcji (NBP, 2020-12-31)",
                                       "Kapitał początkowy (test)", "Liczba aktywów", "Pominięte aktywa", "Plik danych"],
                          "Wartość": [waluta, " – ".join(OKRES_UCZACY), ", ".join(OKRESY_TESTOWE), f"{rf0:.2%}",
                                      KAPITAL, n, "; ".join(f"{c} ({p})" for c, p in odrzucone.items()) or "brak", cfg["plik"]]})
    with pd.ExcelWriter(f"{WYJSCIE}{nazwa}_markowitz.xlsx", engine="openpyxl") as xw:
        glowne.to_excel(xw, sheet_name="Wagi")
        tab.drop(columns=["Waluta"]).to_excel(xw, sheet_name="Metryki", index=False)
        W.to_excel(xw, sheet_name="Wagi - wrazliwosc na limit")
        gr.to_excel(xw, sheet_name="Granica efektywna", index=False)
        param.to_excel(xw, sheet_name="Parametry", index=False)

    # --- wykres wartości portfela w okresie testowym (wariant bez limitu)
    do_max = max(k for _, k in OKRESY_TESTOWE.values())
    fig, ax = plt.subplots(figsize=(10, 5.5))
    for (s, l), w in wagi.items():
        if l == 1.0:
            v = wartosc_buy_and_hold(px.loc[baza:do_max], pd.Series(w, index=px.columns))
            ax.plot(v.index, v.values, label=s)
    for okres, (od, do) in list(OKRESY_TESTOWE.items())[:-1]:
        ax.axvline(pd.Timestamp(do), color="grey", ls=":", lw=1)
    kap_txt = f"{KAPITAL:,.0f}".replace(",", " ")
    ax.set_title(
        f"{cfg['tytul']}\nWartość portfela w okresie testowym (start {kap_txt} {waluta}, kup i trzymaj)",
        fontsize=11,
    )
    ax.set_ylabel(f"Wartość ({waluta})"); ax.legend(); fig.tight_layout()
    fig.savefig(f"{WYJSCIE}{nazwa}_wartosc.png", dpi=130)
    plt.close(fig)

    # --- podsumowanie
    pd.options.display.float_format = "{:.3f}".format
    glowna = tab[tab["Limit wagi"] == 1.0].pivot(index="Strategia", columns="Okres", values="Sharpe")
    print("\n   Sharpe (wariant bez limitu wagi):"); print(glowna.to_string())
    for s in ["Min. wariancja", "Maks. Sharpe"]:
        w = pd.Series(wagi[(s, 1.0)], index=px.columns); w = w[w > 0.005].sort_values(ascending=False)
        print(f"   Wagi – {s}: " + ", ".join(f"{k} {v:.1%}" for k, v in w.items()))
    print(f"   Zapisano: {WYJSCIE}{nazwa}_markowitz.xlsx")
    return tab
