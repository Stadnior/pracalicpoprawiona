"""Portfel 1 – akcje GPW"""
from markowitz_core import run_portfolio

CFG = dict(
    nazwa="P1_GPW",
    tytul="Portfel 1 – akcje GPW",
    plik="data/portfel_1_GPW_2012_2025.csv",
    waluta="PLN",          # usd bedzie przeliczone juz na pln
    usun=[],
    kolumny=None,
)

if __name__ == "__main__":
    run_portfolio(CFG)
