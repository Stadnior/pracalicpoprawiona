"""Portfel 4 – ETF akcyjne + pozostałe klasy aktywów"""
from markowitz_core import run_portfolio

CFG = dict(
    nazwa="P4_ETF_WIELOAKTYWOWY",
    tytul="Portfel 4 – ETF akcyjne + pozostałe klasy aktywów",
    plik="data/portfel_3_ETF_20261013_1548.csv",
    waluta="USD",          # "PLN" – ceny już w złotych; "USD" – zostaną przeliczone na PLN
    usun=[],
    kolumny=["EEM", "EFA", "SPY", "GLD", "TLT", "VNQ"],
)

if __name__ == "__main__":
    run_portfolio(CFG)
