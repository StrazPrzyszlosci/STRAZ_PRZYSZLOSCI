# Stabilna ewolucja — T58

Cel: rzeczywista produkcja kandydatów zmian, niezależne testowanie, review i zachowanie wyniku/feedbacku po restarcie. Merge main pozostaje pod review człowieka. Sam zielony kod wyjścia procesu albo mock nie jest dowodem ewolucji.

## Ścieżka wykonania

1. `EvolutionLoop.pending` zbiera aktualny handoff i cele, sprawdza zajętość, konstytucję i kompletność danych. Brak danych blokuje zadanie przed wywołaniem modelu.
2. LLM proponuje ranking. Lokalny basal dobiera tryb i model według cech, nie fragmentów nazw. Parametr backlog jest rzeczywistą liczbą zadań gotowych.
3. `EvolutionStore` atomowo przydziela lease. Po błędzie ponowienie ma cooldown, limit prób i poprzedni feedback. Obcy/stary lease nie może nadpisać wyniku. Nowa wersja wejść może rozpocząć nową serię prób.
4. Hermes otrzymuje `/input/task.json`, konkretne fragmenty źródeł i repo `/repo` tylko do odczytu. Wynik zapisuje wyłącznie jako `output/PROPOSAL.md` i, dla kodu, `output/changes.patch`.
5. Kontroler sprawdza scope patcha i składnię. Test odbioru pochodzący z kontraktu jest montowany oddzielnie: baseline musi zawieść, kandydat przejść, a pełna regresja kandydata ma być zielona. Producent nie może zmienić tego programu odbioru.
6. Review otrzymuje cały mały patch i wyniki walidacji. Gotowy kandydat trafia do trwałego archiwum; nie jest aplikowany do main ani uznawany za human acceptance.

## Przygotowanie środowiska

```bash
python3 tools/prepare_hermes_runtime.py --source /sciezka/do/hermes-agent --destination scratch/selfopt/hermes_runtimes

# Lokalny basal musi już działać. Klucz najpierw z env; flaga dopuszcza jawnie autoryzowany fallback lokalnej bazy.
SELFOPT_BASAL_URL=http://127.0.0.1:8000 node tools/run_swarm_pilot.mjs \
  --real --evolve --use-omniroute-db-key \
  --state-dir scratch/selfopt/stable-evolution \
  --quota-ledger /sciezka/do/ISTNIEJACEJ/quota_ledger.json \
  --runtime scratch/selfopt/hermes_runtimes/COMMIT_HERMESA --max-calls 64
```

Powyższy limit jest łącznym limitem istniejącej doby, nie nową pulą po restarcie. Nie usuwaj ledgeru. `--continuous` znosi limit dwóch batchy, zachowując limity czasu i doby; `--pause`, `--turns` i `--max-seconds` ustawiają parametry. Brak gotowych danych albo budżetu oznacza oczekiwanie bez wykonywania workera.

Runtime jest kopią publicznego Git i istniejących zależności CPython 3.12, bez konfiguracji operatora i `.pth`. Nie pobiera pakietów. Sandbox nie ma hostowego HOME ani sieci; wyjście API prowadzi przez kontrolowany Unix proxy. Klucz providera pozostaje w kontrolerze. Pełny pakiet wejściowy musi odpowiadać committed snapshotowi; nie uruchamiaj produkcji z niespójnym WIP.

## Odbiór i dalsza praca

Sprawdzaj `evolution_index.json`, `last_evolution_plan.json`, `evolution_queue/*/evolution_receipt.json`, `validations/*/` oraz `candidate_archive/`. `ready` wymaga wszystkich bramek. `needs_fixes` jest ponawiane z feedbackiem, nie traktowane jak ukończone. Lease wygasa po przerwaniu procesu; ten sam input po sukcesie nie uruchamia ponownie zadania.

T58 zawiera rzeczywisty cel naprawy kodu wyjścia daemona z niezależnym testem odbioru. Błąd wykryto w uruchomieniu T53: oba workery zawiodły, lecz daemon zwrócił 0. Kod tej naprawy ma wytworzyć rój; kontroler nie dostarcza gotowego patcha. Pozostałe etapy pełnego celu — publikacja draft PR, odbiór człowieka, adaptacja po ocenach i dłuższa obserwacja operacyjna — muszą mieć własne dowody przed uznaniem całej ewolucji za stabilną.
