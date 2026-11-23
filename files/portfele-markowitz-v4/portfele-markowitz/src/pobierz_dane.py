"""
Pobiera ceny z Yahoo Finance (biblioteka yfinance) dla portfeli 1 i 2 oraz kurs USD/PLN.
Uruchom RAZ na swoim komputerze:   pip install yfinance   a potem   python src/pobierz_dane.py
Wynik: pliki CSV w katalogu data/ (w tym samym formacie co dotychczasowe).
Okres: 2011-12-01 – 2025-12-31 (horyzont badania 2012–2025).
"""
import os
import pandas as pd
import yfinance as yf

OD, DO = "2011-12-01", "2026-01-01"   # DO jest wyłączne -> ostatni dzień 2025-12-31
ZESTAWY = {
    "data/portfel_1_GPW_2012_2025.csv": ["ACP.WA", "ALR.WA", "BDX.WA", "BHW.WA", "CAR.WA", "CDR.WA", "CPS.WA",
        "DNP.WA", "DOM.WA", "JSW.WA", "KGH.WA", "KRU.WA", "KTY.WA", "LPP.WA", "MBK.WA", "MIL.WA", "OPL.WA",
        "PEO.WA", "PGE.WA", "PKN.WA", "PKO.WA", "PZU.WA", "ING.WA", "TPE.WA", "XTB.WA"],
    "data/portfel_2_SP500_2012_2025.csv": ["AAPL", "ABBV", "AMZN", "BAC", "COST", "CRM", "CVX", "GOOGL", "HD",
        "JNJ", "JPM", "KO", "LLY", "MA", "META", "MSFT", "NFLX", "NVDA", "PEP", "PG", "TSLA", "UNH", "V", "WMT", "XOM"],
    "data/USDPLN.csv": ["USDPLN=X"],
}
os.makedirs("data", exist_ok=True)
for plik, tickery in ZESTAWY.items():
    px = yf.download(tickery, start=OD, end=DO, auto_adjust=True, progress=False)["Close"]
    if isinstance(px, pd.Series):
        px = px.to_frame(tickery[0])
    px.index.name = "Date"
    px.to_csv(plik)
    puste = [c for c in px.columns if px[c].notna().sum() == 0]
    print(f"{plik}: {px.shape[0]} wierszy, {px.shape[1]} kolumn" + (f", PUSTE: {puste}" if puste else ""))
