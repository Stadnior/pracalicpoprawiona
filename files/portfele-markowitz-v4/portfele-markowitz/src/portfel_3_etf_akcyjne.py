"""Portfel 3 – ETF akcyjne"""
from markowitz_core import run_portfolio

CFG = dict(
    nazwa="P3_ETF_AKCYJNE",
    tytul="Portfel 3 – ETF akcyjne",
    plik="data/portfel_3_ETF_20261013_1548.csv",
    waluta="USD",          # "PLN" – ceny już w złotych; "USD" – zostaną przeliczone na PLN
    usun=[],
    kolumny=["EEM", "EFA", "SPY"],
)

if __name__ == "__main__":
    run_portfolio(CFG)
