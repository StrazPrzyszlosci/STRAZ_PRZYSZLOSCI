# Weryfikacja poprawek Kilo i przygotowanie integracji z T58

Decyzja operatora z 2026-10-23: **Kilo poprawia runtime; Codex weryfikuje i przygotowuje integrację**. Codex zawęził własny claim T58 do dokumentacji tej pracy. Nie zmienia kodu runtime ani claimu Kilo.

**Najnowszy zakończony odbiór opisuje sekcja „Kolejne migawki Kilo” na końcu dokumentu:** dla migawki v3 pełny Python ma 492 testy i 1 błąd. Pierwsza część raportu zachowuje wyniki v1, zamiast przypisywać je późniejszym poprawkom. Kilo nadal edytuje pliki; odbiór nie dotyczy niezbadanych zmian po wskazanych hashach.

**Wynik badanej migawki: niegotowa do integracji ani uruchomienia autonomicznej ewolucji.** To ocena konkretnego WIP, nie późniejszych poprawek Kilo ani stanu `main`. T58 również nie ma jeszcze dowodu stabilnej ewolucji.

## Identyfikacja wejść

- Kilo: worktree `.kilo/worktrees/kilo-selfopt`, rzeczywisty branch `codex/T52b-basal-pico-contract-kilo`, HEAD `042bde4b8158d3f9eaf361a62817f78ec97228c5`.
- SHA256 roboczego `git diff --binary HEAD`: `96fa96da8199eb7db71e992964b1e279eafda2f5322eb2dcbc3f65bdefe1d795`.
- T58: `5ef0a59fc1fbfccea1fa0c2a94f961f8e2695f5b`, branch `codex/T58-stable-swarm-evolution`, draft PR #27 na bazie brancha draft PR #26.
- `git merge-base` potwierdza, że HEAD Kilo jest przodkiem T58.
- Odczyt diffu przed i po zebraniu migawki był identyczny. Testy uruchamiano w `/tmp/straz-kilo-audit-dq_7ra4d`, nie w edytowanym worktree Kilo. Plików nieśledzonych nie traktowano jako kodu migawki; w chwili kontroli był to tylko dawny claim T53.
- Dowody zachowano we własnym worktree: `scratch/selfopt/integration-review/20261023-kilo/` (patch, hashe wejść, logi, podglądy konfliktów). Odtworzenie: archiwum Git HEAD Kilo + zachowany patch.

## Wyniki wykonanych kontroli

| Kontrola | Wynik |
|---|---|
| Python: `test_selfopt_integrations.py` | 45 testów, 3 failures, 1 error |
| Pełny Python: `test_*.py` | 492 testy, 3 failures, 14 errors |
| JavaScript: `node --test --test-reporter=tap tests/*.mjs` | 378 pass / 0 fail |
| Manifesty komórek | 12 poprawnych |
| Seed approvals | walidator zakończony kodem 0 |
| CI istniejącego T58 `5ef0a59` | Repository Checks i PR Secret Scan: success |

Pierwsze wykonanie pełnego Pythona w sandboxie nie mogło otworzyć lokalnego serwera testowego API. Autorytatywny wynik powyżej pochodzi z ponowienia z dostępem do lokalnego socketu: `/tmp/straz-kilo-audit-full-python-unrestricted.log`. Nie wykonywano rzeczywistych wywołań modeli podczas tych testów. Komunikaty o celowo przeterminowanych rekordach w testach walidatora approvals nie oznaczają nieważności seed approvals.

Runner Node w sandboxie raportował wyłącznie 38 plików wejściowych, bez szczegółowych testów. Ponowienie z działającą komunikacją procesów dało właściwe 378 testów; autorytatywny log: `/tmp/straz-kilo-audit-javascript-unrestricted.log`. Nie utożsamiać liczby plików z liczbą sprawdzonych przypadków.

Testy kontrolera T58 (512 Python OK) i testy WIP Kilo (492 testy z błędami) dotyczą różnych drzew. Nie sumować ich ani nie przedstawiać wyniku T58 jako potwierdzenia poprawności WIP Kilo.

## Ustalenia wymagające poprawki lub rozstrzygnięcia przez właściciela runtime

1. **Blokada planowania przez brak importu.** `swarm.py:_stem_pattern()` wywołuje `re.compile`, ale moduł nie importuje `re`. Powtórzono `NameError` w 14 testach pełnego zestawu, obejmujących charter, planowanie i orkiestrację.

2. **Lokalny engine nie działa od wejścia do wyniku.** `FreeApiEngine.complete()` blokuje każde zadanie private przed wyborem stylu API; oba nowe testy lokalne nie przechodzą. Bezpośrednie diagnostyczne wywołanie `_call()` z lokalnym modelem daje ponadto `NameError: secret_env`. Po podstawieniu tej jednej nazwy wyłącznie w pamięci procesu, ze sztuczną odpowiedzią OpenAI i bez połączenia sieciowego, odczyt odpowiedzi kończy się `KeyError: candidates`: parser nadal rozpoznaje `local` jako odpowiedź Gemini. Nie poprawiano tych ścieżek w plikach. Odbiór powinien objąć prywatne zadanie na rzeczywistym lokalnym endpointcie, blokowanie private na publicznym API oraz brak klucza dla endpointu lokalnego. Lokalność Basal jest osobną, już istniejącą ścieżką i nie dowodzi działania lokalnego `FreeApiEngine`.

3. **Niespójne flagi bramki.** W `SecurityGate.inspect_tree()` zniknęło końcowe `blocked = bool(violations)`. Dla niepustego katalogu z zakazanym kodem może powstać `ok=false`, lecz `blocked=false` i `quarantine_required=false`. Potwierdza to istniejący `test_inspect_tree_scans_files`. Z kolei dopisanie naruszenia po niezerowym zakończeniu Hermesa nie przelicza `gate['ok']`; to dodatkowa niespójność widoczna w kodzie. Odbiór musi wymagać spójności wszystkich flag, a nie wyłącznie `ok`.

4. **Dedup usuwa możliwość naprawy nieudanego zadania.** Nowe `EvolutionLoop.run()` zapisuje fingerprint każdego wybranego zadania do `evolution_processed.json`, niezależnie od wyniku. W diagnostyce z rzeczywistym kolektorem i zastąpionym wykonawcą zwracającym `needs_fixes` pierwsze zadanie `target_router_weights_from_decisions` zostało zapisane jako przetworzone; kolejny cykl wybrał inne zadanie. Brak ponowienia po błędzie nie jest udaną deduplikacją. T58 ma już rozróżnienie stanów, lease, feedback, cooldown i ponowienia w `EvolutionStore`; nie zastępować tego listą wszystkich historycznie uruchomionych fingerprintów.

5. **Kalibracja wielokrotnie konsumuje te same etykiety.** Dla jednej identycznej negatywnej etykiety i identycznej decyzji kolejne wywołania nowego `fit_temperatures(..., base=...)` dały temperatury `1.0 → 1.15 → 1.30`. W `_auto_calibrate()` nie ma znacznika wykorzystanych etykiet ani nowej porcji danych, więc każdy cykl może przesuwać wynik bez nowej informacji. Ponadto poprzednia temperatura `allocation=1.2` zniknęła, gdy aktualny zestaw etykiet dotyczył tylko `strategy`. Nowy test `assertLessEqual` na zerowym kierunku korekty nie dowodzi poprawnej kumulacji. Odbiór: ponowne przetworzenie tych samych danych nie zmienia stanu, a nowe etykiety aktualizują odpowiedni typ bez utraty pozostałych typów.

6. **Redakcja receiptu nie usuwa klucza z argv.** WIP redaguje zapisaną listę `command`, lecz nadal dodaje rzeczywisty `--api-key` do uruchamianego procesu. Nie daje to izolacji systemowej ani ochrony listy procesów. Podczas integracji zachować sandbox, ograniczony proxy i przekazywanie wyłącznie tokenu proxy z T58, bez dostępu workera do klucza providera i katalogu domowego.

## Mapa konfliktów

Wykonano diagnostyczne `git merge-file --diff3` osobno dla każdego z 10 zmienionych plików: wersja T58, wspólna baza Kilo i niezmienna migawka WIP. Nie wykonywano merge do żadnego brancha. Wynik: **8 plików z konfliktami, łącznie 24 obszary konfliktów**.

| Plik | Obszary konfliktów | Co trzeba zachować podczas uzgadniania |
|---|---:|---|
| `AGENTS.md` | 1 | aktualne statusy i koordynację claimów; nie przywracać starszych zapisów |
| `selfopt_chain/calibrate.py` | 1 | typy decyzji i operacyjną obsługę etykiet; uzgodnić idempotencję dopasowania |
| `selfopt_chain/charter.json` | 1 | sprawdzony matcher i przypadki polskich słów; nie zmieniać samej listy bez testów |
| `selfopt_chain/evolver.py` | 4 | trwałe lease/retry, kompletne wejścia, niezależną walidację, review, archiwum i publikację |
| `selfopt_chain/hermes_worker.py` | 3 | sandbox OS, zatrzymywanie procesu, proxy, redakcję i spójność bramki |
| `selfopt_chain/orchestrator.py` | 10 | wspólny ledger i budżet wywołań, prawdziwy backlog, wznowienia oraz lokalny Basal |
| `selfopt_chain/run_loop.py` | 3 | kontekst zależności, zatrzymanie po błędzie, budżet każdego wywołania i rzeczywisty czas |
| `selfopt_chain/swarm.py` | 1 | osobne typy decyzji i sprawdzone reguły charteru |
| `selfopt_chain/engine.py` | 0 | brak konfliktu tekstowego nie naprawia opisanej wyżej lokalnej ścieżki |
| `tests/test_selfopt_integrations.py` | 0 | uzgodnić podklasy `ChainRunner` z nowymi argumentami `ledger`, `should_stop`, `max_attempts` |

Nie zalecam scalania całych starszych modułów Kilo na T58. Zalecam, aby właściciel runtime naniósł różnice funkcjonalne na uzgodnioną wspólną bazę PR #26/#27, zachowując istniejące mechanizmy bezpieczeństwa i wznawiania. Podglądy konfliktów są materiałem do tego uzgodnienia, nie gotowym rozwiązaniem konfliktów.

## Stan rzeczywistej ewolucji T58

Model Cohere wygenerował rzeczywisty patch selekcji odroczonego zadania (SHA256 `6671f533346a2ab8891bde0e51b4612f9433dc4f2f68e5a48c676424360bc7ce`). Niezależny odbiór dał baseline FAIL / candidate PASS / pełna regresja PASS. Następne rzeczywiste review zwróciło `needs_fixes`: zmiana kolejności musi być warunkowa względem `decision['deferred']`. Patch pozostaje nieprzyjęty i nieopublikowany; feedback zapisano w trwałym stanie. To potwierdza istnienie produkcji i selekcji, ale nie stabilnej ewolucji.

Receipt: `scratch/selfopt/stable-evolution-live/evolution_queue/revalidate_92a19a896ae6/evolution_receipt.json`. Nie regenerować ani nie ręcznie poprawiać kandydata w celu wymuszenia zielonego wyniku. Kolejna próba powinna wykorzystać feedback i pozostać odseparowana od kodu modyfikowanego przez Kilo.

## Kolejność dalszej pracy

1. Kilo kończy poprawki swojej migawki; Codex sprawdza kolejny wskazany commit lub nowy hash diffu. Powtórzyć testy po zmianach, nie nadpisywać tego raportu nowszymi wynikami bez nowej identyfikacji wejść.
2. Uzgodnić zmiany na wspólnej bazie z PR #26/#27 i rozstrzygnąć osiem konfliktujących plików. Codex przygotowuje kontrolę integracji; implementację wspólnego runtime prowadzi Kilo zgodnie z decyzją operatora.
3. Na niezmiennej wersji po integracji uruchomić pełny Python, JS, manifesty, approvals i testy regresyjne ustaleń powyżej. Zielony sam zestaw testów unit nie zastępuje prywatności, budżetu, restartu i odbioru artefaktów.
4. Dopiero potem uruchomić ograniczony rzeczywisty pilot z lokalnym Basal i tym samym quota ledger, bez resetu licznika. Zbadać przydział zadań, ponowienie z feedbackiem, restart bez duplikatów oraz brak nowych wywołań w stanie bezczynności.
5. Publikować kandydata wyłącznie po przejściu niezależnego odbioru i review, jako draft PR. Zachować `no_auto_merge`, `no_direct_push` i `suggest-only`. Dopóki nie ma powtarzalnego domknięcia tej ścieżki, cel stabilnej ewolucji pozostaje niezrealizowany.

## Kolejne migawki Kilo

Wszystkie poniższe migawki mają tę samą bazę `042bde4b8158d3f9eaf361a62817f78ec97228c5`; rozróżnia je SHA256 pełnego roboczego diffu. Ponowienia pełnego Pythona wynikały z nowych zmian kodu, nie z próby uzyskania innego wyniku na identycznym wejściu.

| Migawka | SHA256 diffu | Pełny Python |
|---|---|---|
| v1 | `96fa96da8199eb7db71e992964b1e279eafda2f5322eb2dcbc3f65bdefe1d795` | 492 testy; 3 failures, 14 errors |
| v2 | `0a6f8d30a47f23308f13b414e5cab2b8315c4a1ac3bbe5109bd063a59dc8522c` | 492 testy; 1 failure, 3 errors |
| v3 | `7eacc56fb5c5bb02ac2aa5bbe3f69bb816289d74da289ae3f3769ed54846bf67` | 492 testy; 1 error |

W v2 poprawiono import `re` oraz oczekiwany typ decyzji w teście kalibracji. Zmiana prywatności odwoływała się jednak do `model` przed jego przypisaniem; trzy testy wykazały `UnboundLocalError`. W v3 usunięto ten błąd oraz przywrócono wyliczanie `SecurityGate.blocked` z naruszeń. Zakończony odbiór v3 nadal wykazuje `NameError: secret_env` w `engine.py:_call()` dla lokalnego API. Po jego usunięciu wymaga osobnego odbioru również parser odpowiedzi lokalnej, opisany w ustaleniu 2; nie uznawać go za sprawdzony na podstawie samego usunięcia wyjątku.

Dowody v2: `scratch/selfopt/integration-review/20261023-kilo-v2/`. Dowody v3: `scratch/selfopt/integration-review/20261023-kilo-v3/`. Testy wykonywano odpowiednio w `/tmp/straz-kilo-audit-v2-f5fxbd31` i `/tmp/straz-kilo-audit-v3-rirvz7to`. Źródła 85 plików `tests/*.mjs` i `cloudflare/src/*.js` oraz manifest komórek porównano bajtowo z v1: bez zmian. Wynik JavaScript 378 pass / 0 fail pochodzi z wykonania na tych samych źródłach w v1; nie podawano fikcyjnego nowego uruchomienia JS dla każdej migawki.

Podgląd integracji v2 z T58 `17e7882` nadal ma 8 konfliktujących plików i 24 obszary konfliktów; dochodzi bezkonfliktowa tekstowo zmiana testu `tests/test_selfopt_calibrate.py`. Dla v3 nie wykonano nowego podglądu scalenia i nie przenoszono wyniku v2 jako pomiaru v3. CI T58 `17e7882` zakończyło oba joby sukcesem, w tym pełny Python, JS, manifesty i approvals; nie jest to CI WIP Kilo.

### Dodatkowe próby zachowania

- **CLI OmniRoute (v2):** przy wywołaniu `main(['--engine','omniroute','--once','--quota-snapshot',PATH])` i zastąpieniu wyłącznie wykonania `Orchestrator` rejestratorem konfiguracji przekazany `quota_snapshot_path` był `None`. Rzeczywista `quota_gate` dla tej konfiguracji zwróciła `allowed=false`, `quota_snapshot_blocked:missing_snapshot`. Przyczyna: końcowa konfiguracja CLI uwzględnia plik tylko dla `free-api`, choć bramka po poprawce obejmuje także `omniroute`. Nie wykonywano wywołań sieciowych ani modeli. Naprawa wymaga sprawdzenia propagacji pliku, jego ważności i budżetu, a nie usunięcia bramki.
- **Bezpieczny wybór przy defer (v3):** kontrolowany rdzeń zwrócił `deferred=true`, `final='job-safe'` i ranking `job-risk:0.6, job-safe:0.4`. `SwarmPlanner.decide_job_selection()` oddał kolejność `['job-risk','job-safe']`, ignorując bezpieczne `final`. To niezależny test znanego celu ewolucji, bez generowania nowej poprawki i bez przypisywania temu przypadkowi rzeczywistej decyzji modelu.
- **Dedup i kalibracja:** w v2 i v3 nie zmieniły się ścieżki odpowiedzialne za pomijanie `needs_fixes` oraz wielokrotne używanie tych samych etykiet. Ustalenia 4 i 5 pozostają otwarte. Zielony zestaw obecnych testów nie będzie sam w sobie odbiorem tych zachowań.

### Rzeczywisty przydział zadań przez lokalny Basal

Na niezmiennej migawce v2 wykonano jedynie planowanie dla dwóch przykładów zasobów i dwóch potrzeb z repozytorium. Lokalny `http://127.0.0.1:8000/health` zwrócił `ok`, a wszystkie **6/6 decyzji** miało `engine='basal-serve'`; nie użyto builtin ani publicznego API. Wybrana strategia: **quality_first**.

| Potrzeba | Przydzielony zasób | Tryb |
|---|---|---|
| `need_aquaponics_observer_food` | `hardware:phone:ewaste_phone_batch_local_001` | `on_device_model` |
| `need_local_edatabase_knowledge` | `hardware:selfhost:selfhost_compute_node_recovered_001` | `on_device_model` |

Do kolejki wykonania z limitem jednego joba wybrano `selfhost_compute_node_recovered_001`; confidence `0.6524`, próg `0.55`, `deferred=false`. Ten rzeczywisty przebieg nie uruchomił gałęzi defer opisanej w kontrolowanej próbie powyżej. Plan ma `policy='suggest-only'`, `auto_applied=false`; nie uruchamiano modeli na urządzeniach, fizycznej aktuacji, Hermesa ani produkcji nowego kodu. Dowody: `20261023-kilo-v2/local-basal/{plan,summary}.json` oraz `decisions.jsonl`. Przydział jest propozycją planisty, nie dowodem dostępności lub wdrożenia danego modelu na sprzęcie.

Następny odbiór runtime musi obejmować pozostałe błędy funkcjonalne i integrację, a następnie kontrolowany pilot ewolucji z trwałym ledgerem. Samo zejście z 17 błędów testów do 1 nie dowodzi retencji ulepszenia, poprawnego uczenia z nowych etykiet ani publikacji zaakceptowanego patcha.
