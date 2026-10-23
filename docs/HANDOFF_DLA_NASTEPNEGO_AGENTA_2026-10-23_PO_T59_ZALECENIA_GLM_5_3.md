# Instrukcja dla GLM 5.3 — dokończenie procesu roju po T59

Stan sprawdzony 2026-10-23, około 19:50 Europe/Warsaw. Ten dokument jest punktem wejścia do dalszej implementacji. Cel stabilnej ewolucji pozostaje otwarty. Uzgodnienia operatora z tego dokumentu mają pierwszeństwo przed dawnymi opisami architektury T48–T52.

## 1. Cel i uzgodnienia operatora

Zbuduj proces, który sam wybiera gotowe zadania, dobiera odpowiednie darmowe modele, wytwarza przydatne artefakty, niezależnie je sprawdza i zachowuje wyniki oraz feedback. Doprowadź go do powtarzalnej pracy ciągłej. Kod trafia do draft PR; wdrożenie do chronionego `main` wymaga człowieka.

- **Lokalny Basal jest decydentem.** Wybiera konkretny model do zadania z dopuszczonej krótkiej listy. Gdy lista ma jedną pozycję, wybór jest deterministyczny i nie wymaga RPC do Basal. Log ma pokazywać rzeczywisty sposób wyboru.
- **OmniRoute jest bramką wykonawczą.** Modele wykonujące zadania są obecnie zdalne. Wysyłaj jawne ID kwalifikowanego darmowego modelu; odpowiedź nie może pochodzić od nieznanego lub płatnego modelu.
- **Pula ma obejmować dostępne darmowe modele odpowiednio do ich zdolności.** Nie wystarczy używanie dwóch stałych modeli ani dopisanie całego katalogu do allowlisty. Model może mieć kwalifikację tylko do wybranej roli. Nie trzeba uruchamiać każdego modelu w każdym cyklu.
- **Kontekst sprzętowy dotyczy hosta, a ograniczenie wielkości modelu — przyszłej inferencji lokalnej.** Obecnie lokalny jest tylko Basal. RAM/GPU hosta nie ograniczają wielkości modelu wykonywanego przez OmniRoute. Nie instaluj dodatkowych lokalnych LLM w ramach tego zadania.
- Zachowaj `suggest-only`, `no_auto_merge`, `no_direct_push`, izolację OS i blokadę fizycznej aktuacji. Prywatne wejście, np. domyślne dane LoRa, nie może trafić do publicznego API. Sam lokalny Basal nie stanowi lokalnego wykonawcy takich zadań.

Operator zezwolił na używanie klucza `SELFOPT_OMNIROUTE_KEY`, a przy jego braku — jednej aktywnej wartości z lokalnej bazy OmniRoute. Zezwolił też na wysłanie zadania i potrzebnych fragmentów kodu przez OmniRoute do darmowych Cohere/NVIDIA w ograniczonym pilocie. Istniejący launcher obsługuje ten fallback. Klucz pozostaje w pamięci/środowisku procesu: bez argv, logów, receiptów, dokumentów i commitów. Prób dla kolejnych modeli nie traktuj jako zgody na zmianę limitu pilota lub wysyłanie prywatnych danych.

## 2. Właściwa baza i bezpieczne przejęcie pracy

Repo główne: `/home/krzysiek/Dokumenty/INFO_GROUP/STRAZ_POLSKIEGO_Ai`.

Kod do kontynuacji: branch **`codex/T59-swarm-integration`**, worktree **`.kilo/worktrees/codex-swarm-integration`**, draft [PR #28](https://github.com/StrazPrzyszlosci/STRAZ_PRZYSZLOSCI/pull/28). Ten plik i końcowy commit T59 są przekazywaną wersją; potwierdź SHA przez `git rev-parse HEAD` i porównanie z remote. Ostatni rzeczywisty pilot korzystał z **`051c987d4a4303338ba037785ac27572d30ec1a1`**; późniejsze poprawki mają odbiór testowy, a nie nowy udany odbiór rzeczywisty.

Stos zależności: **#26 → #27 → #28**. #28 bazuje na `codex/T58-stable-swarm-evolution`, nie bezpośrednio na `main`. Nie zmerge'owano tych PR-ów. Stary audyt `origin/main=5d95aed` nie opisuje całej przygotowanej integracji.

Pierwsze działanie: odbierz końcowy T59, utwórz **własny worktree/branch i claim T60**, a następnie odtwórz bazową regresję. W głównym katalogu jest inny branch i istnieją cudze worktree — zachowaj je.

```bash
REPO_ROOT=/home/krzysiek/Dokumenty/INFO_GROUP/STRAZ_POLSKIEGO_Ai
git -C "$REPO_ROOT" fetch origin
git -C "$REPO_ROOT" worktree list
git -C "$REPO_ROOT" status --short --branch
git -C "$REPO_ROOT" worktree add -b codex/T60-glm53-swarm \
  "$REPO_ROOT/.kilo/worktrees/glm53-swarm" origin/codex/T59-swarm-integration
cd "$REPO_ROOT/.kilo/worktrees/glm53-swarm"
python3 tools/agent_claims.py check --all-worktrees
python3 human_approval/validate_record.py
```

Przeczytaj bieżące `AGENTS.md`, claimy i ten handoff. Zarezerwuj rzeczywiście potrzebne pliki narzędziem `tools/agent_claims.py reserve` albo zgodnie z formatem claimu. Nie edytuj cudzych claimów. T60–T64 to zalecana kolejność; jeśli numer został zajęty, uzgodnij aktualny numer przed pisaniem kodu. Nie rezerwuj całego repo z wyprzedzeniem.

Kilo zakończyło pracę; jego claim ma `abandoned-duplicate`. Worktree `kilo-selfopt` z HEAD `b9cbb71…` zachowano jako odniesienie. Nie przenoś go w całości na T59 i nie nadpisuj jego WIP. Istotne zmiany z Kilo zostały już selektywnie odebrane i zintegrowane.

## 3. Stan sprawdzony, a nie deklarowany

### Implementacja

- Węzły łańcucha przekazują poprzednie wyniki; zależność po błędzie jest zatrzymywana. Istnieją retry/fallback i raportowanie degradacji.
- Jeden trwały ledger rozlicza próby, także strategię, review i żądania Hermesa. Uwzględnia pule providera, dzienne limity, okno RPM, cooldown i globalny cap.
- Trwały `EvolutionStore` ma lease, ograniczone próby, feedback, dedup i zachowanie gotowej wersji po restarcie. Promocja `simulated→real` zachowuje historię i była uruchomiona rzeczywiście.
- Hermes ma izolację `bubblewrap`, odseparowane wejścia i rozliczany proxy socket. Puste wykonanie i brak artefaktów nie przechodzą bramki.
- DirectPatchWorker wymaga struktury `proposal/edits/new_files`, dokładnych zmian w dozwolonym zakresie oraz niezależnej walidacji. Obce obiekty tool-call są odrzucane.
- Basal dostaje shortlistę po filtrach kosztu, roli, capabilities, kontekstu, tools i dostępności. Domyślnie 8, twardo maks.20 opcji. Zła odpowiedź lokalnego Basal jest jawnie logowana jako fallback, nie jako decyzja modelu.
- Końcowy T59 dodaje wybór modelu przez Basal także dla strategii/review, szacowanie pozostałego budżetu wykonawcy przed strategią oraz pomiar sprzętu przekazywany do kontekstu decyzji i zadań.
- `remaining_daily_calls()` i preflight są **oszacowaniem**, nie atomową rezerwacją całego procesu. Współbieżność i rezerwa review wymagają dokończenia.
- Istnieje kontroler publikacji: `request_publication()`, `stage_branch()`, `record_published()`. Żądanie publikacji na dysku nie oznacza utworzenia PR na GitHub.

Regresja końcowej wersji: **550 Python OK; 378 JS pass / 0 fail, 38 plików; 12 manifestów komórek; approvals ważne; kontrola claimów bez konfliktów**. W tym środowisku `node --test tests/*.mjs` raportowało tylko 38 plików; rzeczywiste 378 przypadków potwierdzono także uruchomieniem każdego pliku bezpośrednio przez `node`. Nie zamieniaj liczby plików na liczbę przypadków.

Po przekazaniu potwierdzono również [Repository Checks dla 0e598ae](https://github.com/StrazPrzyszlosci/STRAZ_PRZYSZLOSCI/actions/runs/39999162601): completed/success, a log zadania 120570438866 zawiera **550 Python, 378 JS, 0 JS failures i 12 manifestów**. [PR Secret Scan](https://github.com/StrazPrzyszlosci/STRAZ_PRZYSZLOSCI/actions/runs/39999162465) również ma completed/success. Dowody zapisano lokalnie w `scratch/selfopt/t59-live/handoff_evidence.json`. To odbiór regresji kodu, nie dowód udanej ewolucji.

### Usługi i sprzęt

`straz-basal-local.service` i `straz-ollama-local.service` są aktywnymi **przejściowymi jednostkami systemd użytkownika**, z restartem po błędzie. Basal: `127.0.0.1:8000`; Ollama: `127.0.0.1:11434`; OmniRoute: `127.0.0.1:20128/v1`. Potwierdzono health Basal i listę modeli Ollama. Nie pobierano modeli. Nie potwierdzono trwałego startu po restarcie hosta/wylogowaniu.

`straz-swarm-pilot-t59.service` zakończyła ograniczony pilot i jest nieaktywna. Stare dwa procesy Kilo zakończono przez SIGTERM po sprawdzeniu pustej kolejki; ich zakończenie potwierdzono. **Nie działa teraz potwierdzony daemon ewolucji 24/7.** Przed startem sprawdź stan ponownie; PID i stary raport nie są aktualnym dowodem.

Pomiar hosta w `hardware_context.json`: Intel i3-10110U, 4 wątki dostępne procesowi, około 15 GiB RAM łącznie i około 2.4 GiB dostępnego podczas pomiaru, około 17.5 GiB wolnego na filesystemie worktree. Wykryto urządzenie Intel GPU; gotowość backendu inferencji GPU nie jest potwierdzona. Wartości wolnej pamięci/dysku są chwilowe. Kolektor czyta limity cgroup wraz z przodkami; nie zbiera hostname, numerów seryjnych, env ani sekretów. Nie traktuj ofert odzyskanego sprzętu jako sprzętu już zainstalowanego.

### Darmowe modele

Katalog zawierał 2474 wpisy, 53 wpisy `:free` z aliasami i **13 kanonicznych pełnych ID Kilo**. Bieżący launcher uzbraja **2 profile do prób**: Cohere North Mini Code do kodu/planowania i NVIDIA Nemotron 3.5 Lightning do reasoning/review. **11 modeli czeka na kwalifikację.** Żaden profil nie deklaruje zweryfikowanej jakości. Dodatkowe skonfigurowane połączenia Mistral/NVIDIA nie dowodzą darmowości ani dostępności całego katalogu.

Źródła: `selfopt_chain/runtime_model_profiles.json`, `scratch/selfopt/t59-live/discovered_models.json`, `armed_registry.json` i `docs/AUDYT_MODELI_ROJU_T59_2026-10-23.md`. Nie przywracaj starego mechanizmu przekazującego 316 modeli bezpośrednio do Basal, którego backend obsługuje maks.20 opcji.

### Ostatni rzeczywisty pilot

Stan: `scratch/selfopt/t59-live` w worktree T59. Batch **6**, snapshot `051c987…`. Basal rzeczywiście wybrał `single` i `hermes`; po filtrach kodowych pozostał jeden model — Cohere — więc jego wybór nie wymagał RPC.

Strategia: 1 wywołanie Cohere. Hermes: 4 rozliczone wywołania Cohere i 4 polecenia terminala czytające repo. Kolejne żądanie zatrzymał lokalny cap, prezentowany workerowi jako HTTP 429. **Brak artefaktów, patcha, walidacji i pozytywnego review.** Gate poprawnie odrzucił puste wykonanie. Receipt ma `needs_fixes`, lecz proces daemona zwrócił 0 — to nadal otwarty błąd, nie sukces.

Dowody w worktree T59:

- `scratch/selfopt/t59-live/evolution_batches/batch_6.json`
- `scratch/selfopt/t59-live/evolution_queue/task_aeb1a219c2c69ac0_1ebb9b99/evolution_receipt.json`
- `scratch/selfopt/t59-live/evolution_queue/task_aeb1a219c2c69ac0_1ebb9b99/hermes_receipt.json`
- `scratch/selfopt/t59-live/hermes_quarantine/14d3a1189314/output.json` — JSONL zdarzeń, nie pojedynczy dokument JSON
- `scratch/selfopt/t59-live/decisions.jsonl`, `evolution_index.json`, `hardware_context.json`

**Współdzielony ledger, którego nie wolno zerować ani kopiować do nowego pustego licznika:**

```text
/home/krzysiek/Dokumenty/INFO_GROUP/STRAZ_POLSKIEGO_Ai/.kilo/worktrees/codex-swarm-recommendations/scratch/selfopt/pilot-live/quota_ledger.json
```

Stan dobowy UTC 2026-10-23: **80/80** — NVIDIA 40, Cohere 40. Ostatni pilot: **75→80**. To cap ograniczonego pilota zaakceptowany przez operatora, nie potwierdzona kwota darmowego konta. Nie zwiększaj go automatycznie i nie manipuluj datą. Kolejne realne próby wymagają rzeczywistego odnowienia dobowego okna lub decyzji operatora o nowym limicie. Można kontynuować lokalną implementację i testy bez inferencji.

Wcześniejszy T58 wytworzył prawdziwy patch dla deferred selection, który przeszedł niezależny odbiór techniczny, ale dostał `needs_fixes` od recenzenta. Feedback znajduje się w zachowanym indeksie/receipcie; nie opisuj tej propozycji jako zaakceptowanej. Nadal brak opublikowanego i przyjętego ulepszenia wytworzonego przez ten pilot.

## 4. Łańcuch prac — maksymalnie pięć zadań

### T60 — domknij planowanie zasobów i stany błędów

Zacznij od `quota.py`, `quota_proxy.py`, `hermes_worker.py`, `orchestrator.py`, `evolution_store.py` i odpowiednich testów. Dokończ admission/rezerwę na cały wybrany proces: strategia, producent, ewentualny fallback i niezależne review. Uwzględnij limit modelu i współdzielonej puli. Basal wybiera tylko wykonalne opcje i dostaje faktyczne ograniczenia w kontekście.

Odróżnij lokalne `quota_exhausted` od HTTP 429 providera i od merytorycznej porażki kodu. Brak budżetu nie może zużywać limitu prób poprawy treści. Zachowuj poprawny artefakt oczekujący na review; nie produkuj go ponownie. Rozlicz każdy faktyczny request dokładnie raz.

Odbiór: przy pozostałych 5 wywołaniach nie wybieraj ośmioturowego Hermesa; przy budżecie niewystarczającym dla całego procesu nie wysyłaj strategii. Test współbieżnych lane'ów ma wykazać zachowanie rezerwy i capu. Niezerowy kod zakończenia ograniczonego daemona musi odpowiadać porażce wykonania. Możesz wykorzystać ten błąd jako pierwszy target prawdziwej ewolucji w T62; nie przedstawiaj ręcznej naprawy jako autorstwa roju.

**Odtworzony przypadek graniczny dla T60, źródło 0e598ae:** dwa syntetyczne modele w odrębnych pulach: `producer` ma role `reason/code_draft` i RPD=100, `reviewer` wyłącznie `review` i RPD=1. Globalny cap=5. Po uprzednim zużyciu jedynego requestu recenzenta pozostaje globalnie 4, ale reviewer ma `daily_limit`. `_run_evolution()` mimo to wybiera direct_patch i dopuszcza jedno wywołanie strategii na producencie. Kontrola z wolnym recenzentem również poprawnie dopuszcza strategię. W reprodukcji transport i wykonawca były zastąpione atrapami, sieć była zabroniona, a produkcję zatrzymano przed generowaniem; rzeczywisty ledger nie został dotknięty.

Lokalny raport: `scratch/selfopt/t59-live/preflight_review_gap.json`. Do testu regresyjnego użyj rzeczywistego targetu `daemon_failure_exit` oraz tymczasowego rejestru/stanu. Wymagaj, aby wyczerpana pula jedynego dopuszczonego recenzenta zatrzymywała admission **przed** strategią, z jawnym powodem i bez zużycia requestu producenta. Wolny recenzent ma nadal dopuszczać wykonalny plan. Osobno sprawdź cooldown recenzenta, brak profilu review i wyścig dwóch wykonawców o ostatni slot; sama suma globalnego headroomu nie dowodzi wykonalności procesu.

### T61 — zakwalifikuj pełną darmową pulę do ról

Zacznij od launchera, `model_selection.py`, `router.py`, profili i inwentaryzacji. Kanonizuj ID i aliasy. Zachowaj dowód kosztu/trasy, status dostępności, limit i wiek danych. Rozróżnij `discovered`, próbę kwalifikacyjną, potwierdzoną rolę, cooldown i nieobsługiwany model. Lista nazw providera nie jest allowlistą darmowości.

Przygotuj ograniczone, powtarzalne próby na publicznych/syntetycznych danych: klasyfikacja/JSON, ekstrakcja, kod z wykonywalnym odbiorem, review, faktyczne tool calling, a dla odpowiednich modeli vision/safety. Nie przydzielaj modelu safety do kodu ani modelu bez działających narzędzi do Hermesa. Nie oceniaj szybkości i jakości po nazwie `fast/smart`.

Odbiór: każdy z 13 odkrytych modeli ma wynik kwalifikacji do konkretnych ról albo jawny powód niewłączenia; nowe połączenia OmniRoute mają równie jawne kryteria. Basal wybiera spośród dopasowanych modeli, otrzymuje maks.20 opcji i nie wpada bezgłośnie w builtin. Zachowaj minimum tieru dla lekkich zadań, aby nie kierować wszystkich zadań do najsilniejszego modelu. Sprzęt hosta nie ogranicza modeli zdalnych. Nie zużywaj na kwalifikację budżetu zarezerwowanego na właściwą pracę i review.

### T62 — udowodnij jeden pełny cykl rzeczywistej ewolucji

Użyj kompletnych kontraktów z `selfopt_chain/evolution_targets.json`. Priorytet 100: `target_daemon_failure_exit`, odbiór `selfopt_chain/evolution_acceptance/daemon_exit.py`. Następnie priorytet 90: `target_deferred_job_selection`, odbiór `selfopt_chain/evolution_acceptance/deferred_selection.py`. Ten drugi ma respektować `decision.final` przy defer; poprzednie review ma być wejściem kolejnej próby.

Przebieg: lokalny Basal wybiera → wybrany model OmniRoute wytwarza patch → osobna izolowana kopia daje **baseline FAIL / candidate PASS / regresja PASS** → niezależny recenzent ocenia konkretny patch → kontroler sprawdza hash → osobny branch i rzeczywisty **draft PR** → zapis URL i retencja.

Odbiór: artefakt ma autorstwo i pochodzenie z rzeczywistego wykonania, hash po walidacji jest niezmieniony, a PR istnieje na GitHub. Restart i drugi cykl nie powtarzają gotowej wersji. Pusty output, exit 0, `PROPOSAL.md`, zielony regex gate i lokalny publication request nie zastępują tego odbioru. Review modelu nie jest human acceptance. Producent nie otrzymuje poświadczeń GitHub.

### T63 — domknij uczenie z wyników i mierzenie skuteczności

Zacznij od `calibrate.py`, typed decision log, ścieżki etykiet i trwałego feedbacku. Target uczenia wag routera jest obecnie blokowany przez brak `labels.jsonl`; ten brak ma zostać jawny, dopóki nie ma prawdziwych danych.

Zbieraj osobno: wynik testów, review, transport, akceptację/odrzucenie człowieka i późniejszą regresję. Zapisuj provenance etykiet i ID decyzji. Sukces transportu nie jest etykietą jakości decyzji. Kalibracja ma być używana przez następne decyzje; ponowne przetworzenie tych samych etykiet nie może dodawać pozornego uczenia.

Odbiór: konkretna etykieta zmienia odpowiedni typ decyzji, następny cykl używa właściwej kalibracji, a restart zachowuje stan. Raportuj: użyteczne zwalidowane artefakty/100 faktycznych requestów, udział pozytywnych review, human acceptance, pokrycie etykiet, duplikaty, czas i wywołania na przyjętą propozycję. Ujawniaj mianowniki oraz brak danych.

### T64 — dopiero po odbiorze uruchom pracę ciągłą

Przygotuj trwałe jednostki usług, zależności Basal/Ollama/OmniRoute, pojedynczą instancję na stanie, watchdog, ograniczony restart/backoff i czytelny status `working / idle / waiting_inputs / waiting_models / waiting_provider / waiting_budget / stopped / failed`. Ustal restart po wylogowaniu/reboocie według konfiguracji hosta; transient unit nie dowodzi trwałego wdrożenia.

Najpierw ograniczony soak na odebranym commicie, potem wznowienie z tego samego stanu i ledgeru. Sprawdź SIGTERM, kill switch w trakcie pracy, padnięcie Basal/bramki, timeout providera, brak budżetu i odzyskanie wygasłego lease. Nie restartuj istniejącego procesu tylko dlatego, że skończył się timeout obserwacji narzędzia.

Odbiór: dwa rzeczywiste zadania przechodzą pełny proces, resumption nie dubluje zaakceptowanych wersji, błędy nie są raportowane jako sukces, quota nie przekracza capu, a nadzorca i operator widzą stan. Po merge człowieka odnotuj, jaka wersja kodu faktycznie działa. Zakończ własny claim, handoff i PR; nie wykonuj auto-merge ani aktuacji.

## 5. Narzędzia, walidacja i warunki zatrzymania

Przygotowany runtime Hermesa już istnieje lokalnie:

```text
/home/krzysiek/Dokumenty/INFO_GROUP/STRAZ_POLSKIEGO_Ai/.kilo/worktrees/codex-stable-evolution/scratch/selfopt/hermes_runtimes/493208879a3248c6a4b844981d2c31c78ae00929
```

Sprawdź `READY.json`; nie przebudowuj go ani nie instaluj paczek bez przyczyny. Launcher: `tools/run_swarm_pilot.mjs`; procedura: `docs/RUNBOOK_T59_MOCK_REAL.md`. Gdy budżet jest dostępny, zaczynaj od **jednego batcha**, na czystym commicie, z istniejącym ledgerem i jawnym `--state-dir`. Nie uruchamiaj poniższego realnego pilota przy stanie 80/80:

```bash
SELFOPT_REQUEST_TIMEOUT=150 node tools/run_swarm_pilot.mjs \
  --real --evolve --state-dir <NOWY_STAN_Z_ZACHOWANĄ_HISTORIĄ> \
  --quota-ledger <ISTNIEJĄCY_WSPÓŁDZIELONY_LEDGER> \
  --runtime <PRZYGOTOWANY_RUNTIME> --max-calls 80 \
  --batches 1 --max-seconds 480 --pause 5 --turns 8 --use-omniroute-db-key
```

Historię i feedback można migrować z zapisem pochodzenia. Nie kopiuj/zeruj ledgeru i nie usuwaj błędów z historii, żeby zadanie wyglądało na świeże. Artefakty `scratch/` są lokalne, nie stanowią części klona Git; jeśli ich brakuje, zgłoś brak dowodu i odtwórz wyłącznie autoryzowany ograniczony eksperyment.

Po zmianach uruchom:

```bash
SELFOPT_NETWORK=0 SELFOPT_HERMES=0 SELFOPT_BASAL_URL= \
  python3 -m unittest discover -s tests -p 'test_*.py'
bash -c 'for test_file in tests/*.mjs; do node "$test_file" || exit "$?"; done'
node --check tools/run_swarm_pilot.mjs
python3 agentic_cells/validate_cell_manifest.py
python3 human_approval/validate_record.py
python3 tools/agent_claims.py check --all-worktrees
git diff --check
```

Weryfikuj kod zakończenia każdego testu. Testy API Pythona wymagają lokalnego gniazda HTTP; ograniczony sandbox może dać `PermissionError`, co nie oznacza regresji aplikacji. W T59 pełne 550 przypadków wykonano w środowisku z dopuszczonym lokalnym socketem. Nowa komórka wymaga manifestu; nowy moduł w istniejącym `selfopt_chain` sam w sobie nie jest nową komórką.

Zatrzymaj zależne działania przy braku wymaganej zgody, wolnego budżetu, wejść, kwalifikacji modelu lub konfliktach claimów. Zachowaj artefakty i diagnozę. Kontynuuj niezależne lokalne naprawy. Nie obchodź bramek przez płatny fallback, usunięcie stanu, zmianę daty, wyłączenie walidacji lub uznanie mocka za realny wynik.

Końcowy raport ma podać rzeczywisty commit i aktywną usługę, modele oraz role, liczniki przed/po, konkretne artefakty i PR-y, wyniki testów, odnotowane etykiety i otwarte warunki. **Cel jest osiągnięty dopiero po wykazaniu stabilnego procesu; sam przyrost liczby cykli lub zielonych testów infrastruktury tego nie dowodzi.**
