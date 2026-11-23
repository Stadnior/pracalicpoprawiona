"""Portfel 2 – akcje S&P 500"""
from markowitz_core import run_portfolio

CFG = dict(
    nazwa="P2_SP500",
    tytul="Portfel 2 – akcje S&P 500",
    plik="data/portfel_2_SP500_2012_2025.csv",
    waluta="USD",          # "PLN" – ceny już w złotych; "USD" – zostaną przeliczone na PLN
    usun=["^GSPC"],
    kolumny=None,
)

if __name__ == "__main__":
    run_portfolio(CFG)
