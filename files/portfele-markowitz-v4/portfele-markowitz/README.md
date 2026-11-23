# Portfele – optymalizacja Markowitza

## O co chodzi w badaniu (w skrócie)
- **Podział czasu (2012–2025):** dane dzielimy na **okres uczący (2012–2020)**, na którym model wylicza optymalne wagi, oraz trzy **okresy testowe (2021, 2021–2023, 2021–2025)**, gdzie sprawdzamy, jak te portfele poradziłyby sobie „na żywo” poza próbą.
- **Trzy strategie w każdym portfelu:** porównujemy naiwne dzielenie kapitału po równo (**1/N**), portfel najbezpieczniejszy (**min. wariancja**) oraz portfel o najlepszej relacji zysku do ryzyka (**maks. Sharpe**). Zakładamy brak krótkiej sprzedaży (*long-only*, wagi od 0% do 100%).
- **Symulacja testowa (*buy-and-hold*):** na koniec 2020 r. wrzucamy wirtualne **10 000 zł**, kupujemy aktywa według wyliczonych wag i nie ruszamy portfela do końca okresu. Dla każdego okresu liczymy: całkowitą stopę zwrotu, CAGR, zmienność, wskaźnik Sharpe'a i maksymalne obsunięcie (*max drawdown*).
- **Stopa wolna od ryzyka ($R_f$):** bierzemy stopę referencyjną NBP (z tabeli `data/stopa_referencyjna_NBP.csv`). Przy konstrukcji portfela na koniec 2020 r. wynosiła **0,10%**, a w okresach testowych przyjmujemy średnią ze stóp NBP na koniec poszczególnych lat.
- **Wszystko w PLN:** zagraniczne akcje i ETF-y przeliczamy po historycznym kursie USD/PLN (`data/USDPLN.csv`), żeby porównywać portfele z perspektywy polskiego inwestora.
- **Test wrażliwości i kontrola obliczeń:** sprawdzamy, jak zmieniają się wyniki po nałożeniu limitu na maksymalną wagę pojedynczego aktywa (50%, 40%, 30%, 20% i 10%), żeby portfel nie stawiał wszystkiego na 2–3 spółki. Dodatkowo kod sprawdza zbieżność optymalizacji z kilku punktów startowych.

## Portfele
| Skrypt | Co jest w środku | Dane |
|---|---|---|
| `src/portfel_1_gpw.py` | Polskie spółki z GPW (w PLN) | `data/portfel_1_GPW_2012_2025.csv` |
| `src/portfel_2_sp500.py` | Spółki z amerykańskiego S&P 500 (USD → PLN) | `data/portfel_2_SP500_2012_2025.csv` |
| `src/portfel_3_etf_akcyjne.py` | 3 ETF-y akcyjne na różne rynki: `EEM` (wschodzące), `EFA` (rozwinięte bez USA), `SPY` (USA) – `QQQ` usunięty przez silną korelację ze `SPY` | `data/portfel_3_ETF_20261013_1548.csv` |
| `src/portfel_4_etf_wieloaktywowy.py` | ETF-y akcyjne z P3 + złoto (`GLD`), obligacje USA (`TLT`) i nieruchomości (`VNQ`) – dywersyfikacja międzyklasowa | jak wyzej |

Cała wspólna logika siedzi w `src/markowitz_core.py`, a `src/porownanie.py` skleja wyniki ze wszystkich portfeli w jeden wspólny wykres granic efektywnych i zbiorczy plik Excela.

## Jak to uruchomić
```bash
pip install -r requirements.txt
python src/pobierz_dane.py        # raz: pobiera ceny portfeli 1 i 2 oraz kurs USD/PLN do data/
python src/portfel_1_gpw.py
python src/portfel_2_sp500.py
python src/portfel_3_etf_akcyjne.py
python src/portfel_4_etf_wieloaktywowy.py
python src/porownanie.py
```
Wygenerowane Excele i wykresy trafiają do `wyniki/`. Pierwsza, starsza wersja (na 3 latach danych, bez podziału train/test) jest w `archiwum/`.

## Stan prac i rzeczy do domknięcia
- **Gotowe:** wszystkie 4 portfele policzone w PLN na pełnym horyzoncie 2012–2025 (dane z Yahoo Finance).
- **Odsiew spółek:** jeśli spółka nie miała pełnej historii notowań od początku 2012 r. (np. Dino, XTB, Alior, Meta, AbbVie), skrypt automatycznie ją pomija – pełna lista odrzuconych tickerów jest w arkuszu *Parametry* w Excelu.
- **Do sprawdzenia:** stopy NBP sprzed 2025 r. wpisane z pamięci – trzeba je jeszcze potwierdzić w archiwum na `nbp.pl` (kolumna `status`).
