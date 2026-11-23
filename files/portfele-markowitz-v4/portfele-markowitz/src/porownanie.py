"""
Porównanie portfeli: wspólny wykres granic efektywnych i tabela zbiorcza.
Uruchom PO przeliczeniu portfeli (portfel_*.py) – korzysta z plików w wyniki/.
Uwaga interpretacyjna: położenie jednej granicy nad drugą nie dowodzi, że portfel osiągnie
lepsze wyniki w przyszłości – granice liczone są in-sample (okres uczący 2012–2020).
"""
import glob
import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

WYJSCIE = "wyniki/"
nazwy = sorted(os.path.basename(f)[:-len("_granica.csv")] for f in glob.glob(WYJSCIE + "*_granica.csv"))
if not nazwy:
    raise SystemExit("Brak wyników w wyniki/ – najpierw uruchom portfel_*.py")

fig, ax = plt.subplots(figsize=(10, 6.5))
waluty = set()
for nazwa, kolor in zip(nazwy, plt.rcParams["axes.prop_cycle"].by_key()["color"]):
    g = pd.read_csv(f"{WYJSCIE}{nazwa}_granica.csv")
    p = pd.read_csv(f"{WYJSCIE}{nazwa}_punkty.csv")
    waluty |= set(p["Waluta"])
    ax.plot(g["Zmienność"], g["Zwrot"], color=kolor, label=nazwa)
    for _, r in p.iterrows():
        if r["Strategia"] != "Równe wagi (1/N)":
            ax.scatter(r["Zmienność"], r["Zwrot"], color=kolor, marker="D" if "Sharpe" in r["Strategia"] else "o", s=45)
ax.set_xlabel("Zmienność roczna"); ax.set_ylabel("Roczna stopa zwrotu")
ax.set_title("Granice efektywne (okres uczący 2012–2020)\n● min. wariancja   ◆ maks. Sharpe")
ax.legend(); fig.tight_layout(); fig.savefig(WYJSCIE + "granice_efektywne_wspolny.png", dpi=130)
if len(waluty) > 1 or any("bez przeliczenia" in w for w in waluty):
    print("UWAGA: portfele są w różnych walutach lub nie przeliczono na PLN – porównanie jest niepełne:", waluty)

tab = pd.concat([pd.read_csv(f"{WYJSCIE}{n}_metryki.csv") for n in nazwy])
glowne = tab[tab["Limit wagi"] == 1.0]
with pd.ExcelWriter(WYJSCIE + "porownanie_portfeli.xlsx", engine="openpyxl") as xw:
    glowne.to_excel(xw, sheet_name="Metryki - bez limitu wagi", index=False)
    tab.to_excel(xw, sheet_name="Wszystkie limity wag", index=False)
print("Zapisano: wyniki/granice_efektywne_wspolny.png, wyniki/porownanie_portfeli.xlsx")
