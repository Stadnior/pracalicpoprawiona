"""
Portfel 3 – ETF (USD) – optymalizacja Markowitza (long-only)

Wymagane biblioteki: numpy, pandas, scipy, matplotlib, openpyxl
"""
import os
import numpy as np
import pandas as pd
from scipy.optimize import minimize, linprog
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ============================== PARAMETRY ==============================
PLIK = "data/portfel_3_ETF_20261013_1548.csv"                      # ścieżka do pliku z cenami
KOLUMNY_DO_USUNIECIA = []
RF = 0.0                               # roczna stopa wolna od ryzyka (0.04 = 4%)
MAX_WAGA = 1.0                         # limit wagi jednego aktywa (1.0 = bez limitu, 0.2 = max 20%)
DNI = 252                              # dni sesyjne w roku (annualizacja)
NAZWA = "P3_ETF"                    # przedrostek plików wynikowych
WYJSCIE = "wyniki/"                    # katalog na wyniki
# =======================================================================


def wczytaj():
    px = pd.read_csv(PLIK, index_col=0, parse_dates=True).drop(columns=KOLUMNY_DO_USUNIECIA)
    ret = px.pct_change().dropna()          # dzienne proste stopy zwrotu
    print(f"Aktywa: {ret.shape[1]}, obserwacje: {ret.shape[0]}, "
          f"okres: {ret.index[0].date()} – {ret.index[-1].date()}")
    return ret


def optymalizuj(mu, cov):
    """Markowitz: long-only, suma wag = 1, waga każdego aktywa w [0, MAX_WAGA]."""
    n = len(mu)
    if MAX_WAGA * n < 1:
        raise ValueError("MAX_WAGA jest za małe: suma wag nie może wynieść 100%.")
    w0 = np.ones(n) / n
    granice = [(0, MAX_WAGA)] * n
    suma1 = {"type": "eq", "fun": lambda w: w.sum() - 1}
    ryzyko = lambda w: np.sqrt(w @ cov @ w)
    opcje = dict(maxiter=1000, ftol=1e-12)

    # (a) portfel minimalnej wariancji
    w_mv = minimize(lambda w: w @ cov @ w, w0, bounds=granice, constraints=[suma1],
                    method="SLSQP", options=opcje).x
    # (b) portfel maksymalnego Sharpe'a
    w_ms = minimize(lambda w: -(w @ mu - RF) / ryzyko(w), w0, bounds=granice,
                    constraints=[suma1], method="SLSQP", options=opcje).x
    # (c) granica efektywna: min. ryzyko dla rosnącego zwrotu docelowego
    zwrot_max = -linprog(-mu, A_eq=np.ones((1, n)), b_eq=[1], bounds=granice).fun
    granica, w_prev = [], w_mv
    for t in np.linspace(w_mv @ mu, zwrot_max, 40):
        warunki = [suma1, {"type": "eq", "fun": lambda w, t=t: w @ mu - t}]
        res = minimize(lambda w: w @ cov @ w, w_prev, bounds=granice,
                       constraints=warunki, method="SLSQP", options=opcje)
        if res.success:
            w_prev = res.x
            granica.append((ryzyko(res.x), t))

    czysc = lambda w: np.where(w < 1e-6, 0.0, w) / np.where(w < 1e-6, 0.0, w).sum()
    return czysc(w_mv), czysc(w_ms), pd.DataFrame(granica, columns=["Zmienność", "Zwrot"])


def main():
    os.makedirs(WYJSCIE, exist_ok=True)
    ret = wczytaj()
    mu, cov = ret.mean() * DNI, ret.cov() * DNI       # roczny zwrot i macierz kowariancji
    w_mv, w_ms, granica = optymalizuj(mu.values, cov.values)

    wagi = pd.DataFrame({"Min. wariancja": w_mv, "Maks. Sharpe": w_ms}, index=mu.index)
    portfele = pd.DataFrame({
        n: {"Roczna stopa zwrotu": wagi[n] @ mu,
            "Zmienność roczna": np.sqrt(wagi[n] @ cov @ wagi[n]),
            "Sharpe": (wagi[n] @ mu - RF) / np.sqrt(wagi[n] @ cov @ wagi[n])}
        for n in wagi}).T
    aktywa = pd.DataFrame({"Roczna stopa zwrotu": mu, "Zmienność roczna": np.sqrt(np.diag(cov))})

    # --- Excel
    plik_xlsx = f"{WYJSCIE}{NAZWA}_markowitz.xlsx"
    with pd.ExcelWriter(plik_xlsx, engine="openpyxl") as xw:
        wagi.to_excel(xw, sheet_name="Wagi")
        portfele.to_excel(xw, sheet_name="Portfele")
        aktywa.to_excel(xw, sheet_name="Aktywa")
        granica.to_excel(xw, sheet_name="Granica efektywna", index=False)

    # --- wykres granicy efektywnej
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.plot(granica["Zmienność"], granica["Zwrot"], "k-", label="Granica efektywna")
    ax.scatter(aktywa["Zmienność roczna"], aktywa["Roczna stopa zwrotu"], s=18, c="grey", label="Aktywa")
    for t in aktywa.index:
        ax.annotate(t, (aktywa.loc[t, "Zmienność roczna"], aktywa.loc[t, "Roczna stopa zwrotu"]),
                    fontsize=7, alpha=0.7)
    for n, m in zip(portfele.index, ["o", "D"]):
        ax.scatter(portfele.loc[n, "Zmienność roczna"], portfele.loc[n, "Roczna stopa zwrotu"],
                   s=110, marker=m, label=n, zorder=5)
    ax.set_xlabel("Zmienność roczna"); ax.set_ylabel("Roczna stopa zwrotu")
    ax.set_title("Portfel 3 – ETF (USD) – granica efektywna"); ax.legend()
    fig.tight_layout()
    fig.savefig(f"{WYJSCIE}{NAZWA}_markowitz.png", dpi=130)

    # --- podsumowanie w konsoli
    pd.options.display.float_format = "{:.3f}".format
    print("\n=== PORTFELE EFEKTYWNE ===")
    print(portfele.to_string())
    for n in wagi:
        w = wagi[n][wagi[n] > 0.005].sort_values(ascending=False)
        print(f"\nWagi – {n}:")
        print("\n".join(f"  {k:10s} {v:6.1%}" for k, v in w.items()))
    print(f"\nZapisano: {plik_xlsx}")


if __name__ == "__main__":
    main()
