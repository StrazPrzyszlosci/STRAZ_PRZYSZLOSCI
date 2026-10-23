# Handoff T58 — praca nad stabilną ewolucją

Status: in_progress. Cel wątku „pracuj, żeby rój stabilnie ewoluował” pozostaje aktywny. Nie uznawać samej implementacji lub testów jednostkowych za zakończenie celu.

Branch: codex/T58-stable-swarm-evolution, baza ed63d23 (draft PR #26). Własny worktree codex-stable-evolution i atomowy claim T58; cudzych rezerwacji nie zmieniono.

Wdrożone w tej części: kontrakt i kompletne wejścia zadania; aktualny parser handoffu; lease/retry/feedback i trwałe numery batchy; prawdziwy backlog i cechy modeli; runtime Hermesa i niezależny walidator patcha z baseline fail / candidate pass / pełną regresją oraz archiwum kandydatów. Nie dopisano fikcyjnych etykiet ani akceptacji człowieka.

Dotychczasowa weryfikacja: 503 testy Python OK, 378 JavaScript pass / 0 fail, 12 manifestów, 2 ważne approvals, brak konfliktów claimów, składnia i diff OK. Walidator wykonano w prawdziwym sandboxie na kontrolowanym małym fixture: baseline rc=1, candidate rc=0, pełne testy fixture rc=0. Fixture sprawdza mechanizm, nie jest kandydatem wygenerowanym przez rój.

## Następne zadania

1. Uruchomić rzeczywisty cel daemon_failure_exit: pełny pakiet wejściowy, lokalny basal, Hermes i :free API. Zachować istniejący ledger i jawny łączny limit, bez resetu.
2. Zbadać patch, niezależny odbiór, pełną regresję i review; po błędzie sprawdzić realne ponowienie z feedbackiem i po restarcie.
3. Zachować gotowego kandydata i przygotować draft PR z dowodami, bez auto-merge. Nie przepisywać celu na „wystarczy jedna propozycja”.
4. Domknąć publikację/oceny i sprzężenie zwrotne oraz przeprowadzić dłuższą obserwację powtarzalności, ograniczeń i bezczynności bez duplikatów.
5. Dopiero po audycie wszystkich wymagań uznać cel za ukończony; do tego czasu pozostawić go aktywnym.

Nie dodano komórek ani tabel D1. T24 i aktuacja pozostają odroczone. Parametry i dowody środowiska opisuje STABLE_EVOLUTION_RUNBOOK.md.

## Aktualizacja: wynik pilota i ponowna praca Kilo, 2026-10-23

Ostatni opublikowany commit T58: `5ef0a59`, draft PR #27 (baza: branch draft PR #26). Ostatnia pełna regresja kontrolera: 512 testów Python OK; wcześniej 378 JS pass / 0 fail, 12 manifestów i 2 ważne approvals.

Rzeczywisty model Cohere wygenerował patch selekcji odroczonego zadania, SHA256 `6671f533346a2ab8891bde0e51b4612f9433dc4f2f68e5a48c676424360bc7ce`. Niezależny odbiór: baseline FAIL, kandydat PASS, pełna regresja kandydata PASS. Następnie rzeczywisty reviewer zwrócił `needs_fixes`: zmiana kolejności powinna być warunkowa względem `decision["deferred"]`. Patch nie został opublikowany ani przyjęty; feedback pozostaje w trwałym stanie. Nie jest to dowód stabilnej ewolucji. Receipt: `scratch/selfopt/stable-evolution-live/evolution_queue/revalidate_92a19a896ae6/evolution_receipt.json`.

Operator poinformował: „kilo code robi również poprawki teraz”. Potwierdzono zmiany robocze w worktree `kilo-selfopt`, branch `codex/T52b-basal-pico-contract-kilo`, HEAD `042bde4`. Zakres przecina T58: `evolver.py`, `hermes_worker.py`, `orchestrator.py`, `swarm.py`, `engine.py`, `run_loop.py`, `calibrate.py` oraz `tests/test_selfopt_integrations.py`; Kilo zmienia też `AGENTS.md` i `charter.json`. Dawny claim T53 Kilo nadal ma `in_progress` i wskazuje inną nazwę brancha niż faktyczna. Nie edytowano tego claimu.

Zastosowano AGENTS.md §6: „Podejrzenie kolizji (ten sam plik w dwóch claimach in_progress): nie koduj, dopisz sekcję do swojego handoffu i czekaj na decyzję operatora”. Wstrzymano nowe edycje kodu i poproszono o wskazanie podziału właścicieli. Kontynuować można odczyt różnic, weryfikację istniejących artefaktów i przygotowanie raportu integracji. Wcześniejsze polecenie zatrzymania Kilo nie stanowi podstawy do ignorowania jego obecnej pracy.

Uwaga: kontrola claimów może nadal raportować zero konfliktów, ponieważ poprzedni claim T53 został oznaczony metadanymi przejęcia przez Codex. Ten wynik nie zastępuje aktualnej informacji operatora i widocznych zmian plików. Nie uruchamiać kolejnej autonomicznej modyfikacji wspólnego runtime do rozstrzygnięcia zakresów; nie resetować quota ledger.

Operator rozstrzygnął podział: **„Kilo poprawia runtime; Codex weryfikuje i przygotowuje integrację”**. Zawężono własny claim T58 do dokumentacji i kontroli integracji; runtime pozostawiono Kilo. Raport: `docs/INTEGRACJA_T58_KILO_2026-10-23.md`. Dla migawki Kilo HEAD `042bde4` + diff SHA256 `96fa96da8199eb7db71e992964b1e279eafda2f5322eb2dcbc3f65bdefe1d795` pełny Python: 492 testy, 3 failures i 14 errors; integracyjne: 45 testów, 3 failures i 1 error. Potwierdzono też błędne pomijanie `needs_fixes` i dryf kalibracji na tych samych etykietach. Podgląd integracji z T58: konflikty tekstowe w 8 z 10 plików (24 obszary); brak rzeczywistego merge. Dowody i logi zachowano w `scratch/selfopt/integration-review/20261023-kilo/`. Nie utożsamiać tego WIP z `main` ani zielonym T58.

Końcowe kontrole migawki Kilo: JavaScript 378 pass / 0 fail, 12 manifestów poprawnych, seed approvals poprawne. Kontrola wszystkich worktree po zawężeniu własnego claimu: 6 aktywnych claimów, zero raportowanych konfliktów (z zastrzeżeniem dawnego supersession opisanym wyżej). Nie edytowano wspólnego runtime ani cudzych plików claimów.

## Kolejny odbiór podczas pracy Kilo

Poprzednia tura przyniosła postęp: utrwaliła decyzję operatora, dowody testów i raport integracji w `17e7882`; oba joby CI tego commitu zakończyły się sukcesem. Kolejna kontrola wykryła nowe zmiany Kilo, więc wykonano odbiór nowych, niezmiennych migawek zamiast ponawiać testy na tym samym wejściu. V2 diff SHA256 `0a6f8d30a47f23308f13b414e5cab2b8315c4a1ac3bbe5109bd063a59dc8522c`: 492 Python / 1 failure / 3 errors. V3 diff SHA256 `7eacc56fb5c5bb02ac2aa5bbe3f69bb816289d74da289ae3f3769ed54846bf67`: 492 Python / 1 error (`secret_env` w lokalnym `_call`). Import `re`, odwołanie do `model` przed przypisaniem oraz niespójność `inspect_tree.blocked` poprawiono między migawkami. Pozostałych ustaleń nie zamknięto na podstawie tych poprawek.

Nowe dowody: CLI OmniRoute gubi jawny `--quota-snapshot` (kontrolowana próba v2); selekcja zadań ignoruje bezpieczne `final` przy `deferred=true` (kontrolowana próba v3). Rzeczywiste lokalne planowanie v2: 6/6 decyzji `basal-serve`, strategia quality_first, telefon → akwaponika/on_device_model, selfhost → lokalny katalog/on_device_model; wybrany job selfhost, confidence 0.6524, bez defer. Było to wyłącznie planowanie suggest-only, bez publicznego API, generowania poprawek, wykonania na sprzęcie lub aktuacji. Planowanie nie stanowi dowodu stabilnej ewolucji. Wersjonowane dowody: `scratch/selfopt/integration-review/20261023-kilo-v{2,3}/`; szczegóły w raporcie integracji.

## Odbiór commitu 2a72b37 i przygotowany patch integracji

Kilo zapisało commit `2a72b3702e23b6335d6d2d47113308dc5e0a2d3f`; niezależny odbiór jego czystego archiwum: **492 Python OK**. Zakończono odbiór wcześniejszego błędu `secret_env` i parsera `local` w testach jednostkowych. Źródła aktywnych worktree pozostają bez zmian Codex w runtime.

Przygotowano `docs/INTEGRACJA_T58_KILO_2026-10-23.patch`, baza `866fdb9`, SHA256 `9576a25f8f1a038f74547df8bcb897d45196f7ed79c06756a12bf4bf9769ea57`. Przenosi lokalne API, instrukcje Basal, addytywną regułę charteru i 11 scenariuszy testów z jawną adaptacją kontraktów. Zachowuje silniejsze mechanizmy T58; nie przywraca dryfującej kumulacji kalibracji ani nieodwracalnego dedupu nieudanych zadań. Podgląd: **523 Python OK**; odtworzenie z samej bazy i patcha daje identyczne cztery pliki. Patch nie został zastosowany do źródeł runtime; jest artefaktem przygotowania integracji zgodnym z podziałem operatora. Szczegóły rozstrzygnięć i dowody w raporcie.

Nowa próba po zielonej regresji wykazała lukę również w T58: `simulated` jest stanem terminalnym; przy tych samych wejściach późniejsze uzbrojenie workera daje `duplicate_or_waiting` i zero wywołań realnej ścieżki. Właściciel runtime musi odebrać przejście mock→real z zachowaniem dedupu. Osobna rzeczywista próba lokalnego engine Kilo przez Ollama (istniejący basal-omni-pico, dane syntetyczne, bez publicznego API) przekroczyła 30 s i zwróciła connection_error, przy reported_latency_ms=0. Nie restartowano backendu na podstawie timeoutu. Lokalny Basal w roli decydenta był wcześniej potwierdzony osobno; nie utożsamiać tych dwóch ścieżek.

Cel stabilnej ewolucji pozostaje aktywny i nieudowodniony. Następna praca to odbiór poprawek lifecycle/defer/feedback oraz pełnej integracji, a potem ograniczony pilot na istniejącym ledgerze. Kolejne raporty z tego samego wejścia bez nowych dowodów nie są postępem.
