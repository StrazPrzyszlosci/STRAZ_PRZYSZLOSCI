# Rój selfopt_chain na Kaggle

Notatnik: [kaggle_selfopt_swarm.ipynb](kaggle_selfopt_swarm.ipynb)

Jest to samodzielny punkt startowy, który pobiera kod repozytorium i uruchamia istniejący `selfopt_chain/orchestrator.py` w ograniczonej czasowo sesji Kaggle. Domyślnie wykonuje bezpieczny cykl demonstracyjny (bez rzeczywistych wywołań API). Nie przepisuje roju na osobną implementację.

## Jak uruchomić

1. Kaggle -> Code -> New Notebook -> File -> Import Notebook i wybierz plik .ipynb z repozytorium.
2. Ustaw widoczność Private oraz Internet On w ustawieniach.
3. Uruchom wszystkie komórki z domyślnym `MODE = "demo"`. Archiwum i podsumowanie znajdziesz w /kaggle/working/swarm_outputs.
4. Do prawdziwej pracy ustaw `MODE = "real"`, `REAL_API_APPROVED = True`, `FREE_TIER_LIMITS_CONFIRMED = True` i skonfiguruj OmniRoute/providera.
5. Umieść klucz endpointu OmniRoute w Kaggle Secrets pod nazwą `OMNIROUTE_ENDPOINT_KEY`; opcjonalnie `NVIDIA_API_KEY` dla uprawnionego konta NIM free tier. Nie dodawaj sekretów do kodu, outputów ani publicznego datasetu.
6. W razie potrzeby przywróć zaszyfrowaną lub prywatną konfigurację OmniRoute do `OMNIROUTE_CONFIG_INPUT`. Na nowej maszynie usługa OmniRoute nie dziedziczy automatycznie lokalnych kont.
7. W przypadku aktywnej puli modeli z katalogu OmniRoute i potwierdzonego free tier notatnik tworzy osobny rejestr i snapshot limitów. Brak poprawnego modelu powoduje odmowę uruchomienia realnego runu, a nie płatny fallback.

## Co faktycznie startuje

- BasalDecisionCore z `selfopt_chain/swarm.py`: aktywny w demo i real. Opcjonalnie `BASAL_MODE = "mini_cpu"` uruchamia oficjalny `basal-serve` z Remek/basal-2.0-mini; wymaga pobrania wag i dodatkowej pamięci/czasu.
- OmniRoute: w real instalowany lokalnie przez npm, uruchamiany na 127.0.0.1:20128. Nie jest wymagany w demo.
- Orkiestrator i ewolucja: `selfopt_chain/orchestrator.py --evolve`, polityka suggest-only, jawnie ograniczone cykle i liczba wywołań.
- Hermes: możliwy po ustawieniu `HERMES_MODE = "isolated"`, wyłącznie po pozytywnym teście bubblewrap. Runtime można dołączyć jako prywatny dataset lub eksperymentalnie zbudować wewnątrz notebooka (`HERMES_BOOTSTRAP = True`). Jeżeli user namespaces są niedostępne, tryb Hermes jest blokowany. Bez Hermesa zadania mogą korzystać z wykonawcy `direct_patch` i standardowych walidacji repo.

## Ograniczenia

- Kaggle Notebook nie jest serwerem 24/7. Dokumentacja platformy przewiduje limit czasu dla sesji CPU/GPU (obecnie do 12 godzin); notebook celowo uruchamia krótsze przebiegi.
- Kaggle Schedule może uruchamiać kolejne sesje, ale nie daje gwarancji bezprzerwowej pracy. Wprowadza się osobną odpowiedzialność za kontrolowanie quota i unikanie równoczesnych przebiegów.
- Pliki w `/kaggle/working` należą do wersji uruchomienia. Aby zachować decyzje basal, ledger, rozstrzygnięcia i propozycje, pobierz `swarm_outputs/swarm_state.zip` i zamontuj go jako wejściowy prywatny Kaggle Dataset w kolejnym uruchomieniu (`STATE_ARCHIVE_INPUT`). Sam notebook nie aktualizuje datasetu.
- Profil OmniRoute i dane uwierzytelniające nie są eksportowane do `swarm_state.zip`. Konfigurację trzeba odtworzyć osobno, najlepiej bez publikacji sekretów.
- Źródła repo pochodzą z wybranej gałęzi. Plik `source.json` zapisuje dokładny commit użyty w danej sesji.
- Brak możliwości wykonania pełnego testu wewnątrz Kaggle z poziomu tego repozytorium. Działanie zależy od aktualnego obrazu Kaggle, dostawców modeli i uprawnień sieciowych.

## Test statyczny

```bash
python -m unittest tests.test_kaggle_swarm_notebook
```

Test sprawdza, że notatnik jest poprawnym JSON, kod komórek ma poprawną składnię Python i nie ma zapisanych wyników wykonania.

## Bezpieczeństwo

Nie uruchamiaj nieznanych fragmentów wygenerowanego kodu bez izolacji. Nie udostępniaj publicznie logów, archiwów runów i konfiguracji zawierających treści prywatne. Rój nie wykonuje automatycznego merge ani bezpośredniego zapisu do gałęzi main.
