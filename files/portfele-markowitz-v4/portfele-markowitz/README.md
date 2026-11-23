# Portfele – optymalizacja Markowitza 

## Układ badania
- **Horyzont:** 2012–2025. **Okres uczący** (estymacja wag): 2012–2020. **Okresy testowe:** 2021, 2021–2023, 2021–2025.
- **Strategie w każdym portfelu:** równe wagi (1/N), minimalna wariancja, maksymalny Sharpe (Markowitz, long-only).
- **Stopa wolna od ryzyka:** stopa referencyjna NBP (przy konstrukcji: z 31.12.2020 = 0,10%; w teście: średnia ze stóp na koniec lat okresu). Tabela: `data/stopa_referencyjna_NBP.csv`.
- **Test:** kup-i-trzymaj, kapitał początkowy 10 000 zł; miary (zwrot, CAGR, zmienność, Sharpe, maks. obsunięcie) liczone dla próby uczącej i każdego okresu testowego.
- **Waluta:** wszystko w PLN (kursy USD/PLN w `data/USDPLN.csv`).
- **Wrażliwość:** wagi liczone dodatkowo z limitem wagi pojedynczego aktywa (50%, 40%, 30%, 20%, 10% – tam, gdzie wykonalne).
- **Kontrola optymalizacji:** sprawdzenie zbieżności, sumy wag i ograniczeń; kilka punktów startowych.

## Portfele
| Skrypt | Portfel | Dane |
|---|---|---|
| `src/portfel_1_gpw.py` | akcje GPW (PLN) | `data/portfel_1_GPW_2012_2025.csv` |
| `src/portfel_2_sp500.py` | akcje S&P 500 (USD→PLN) | `data/portfel_2_SP500_2012_2025.csv` |
| `src/portfel_3_etf_akcyjne.py` | ETF akcyjne: EEM, EFA, SPY (QQQ usunięty – silnie skorelowany z SPY) | `data/portfel_3_ETF_20261013_1548.csv` |
| `src/portfel_4_etf_wieloaktywowy.py` | ETF akcyjne + GLD, TLT, VNQ | j.w. |

`src/markowitz_core.py` – wspólna logika. `src/porownanie.py` – wspólny wykres granic efektywnych i tabela zbiorcza.

## Uruchomienie
```bash
pip install -r requirements.txt
python src/pobierz_dane.py        # raz: pobiera dane portfeli 1 i 2 oraz kurs USD/PLN do data/
python src/portfel_1_gpw.py
python src/portfel_2_sp500.py
python src/portfel_3_etf_akcyjne.py
python src/portfel_4_etf_wieloaktywowy.py
python src/porownanie.py
```
Wyniki trafiają do `wyniki/`. Wersja pierwsza (3 lata danych, bez podziału na próbę uczącą i testową) jest w `archiwum/`.

## Stan prac i zastrzeżenia
- Wszystkie cztery portfele przeliczone w PLN (dane 2012–2025, kursy USD/PLN z Yahoo Finance).
- Spółki bez pełnej historii w okresie uczącym (2012–2020) są automatycznie pomijane (lista w arkuszu "Parametry").
- Stopy NBP sprzed 2025 r. wpisane z pamięci – do weryfikacji na nbp.pl (kolumna `status`).
- Do zrobienia: uzasadnienie doboru spółek, testy istotności różnic (na końcu badania).
