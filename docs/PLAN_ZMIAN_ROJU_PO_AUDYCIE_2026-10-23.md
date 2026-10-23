# Plan zmian roju po weryfikacji audytu T48–T52

Data: 2026-10-23. Status: implementacja wznowiona poleceniem operatora; domknięto podstawowe wykonanie i ograniczony pilot. Pełny plan nie jest oznaczony jako ukończony.

## 1. Zakres i stan prac

Odniesienie: zdalny main `68594803acff91bdfa61f7b3703e192ff96d00a6`, pobrany do lokalnego `origin/main`. Dostarczony audyt dotyczy `5d95aed`; między tymi commitami zmieniło się osiem plików. Wnioski poniżej rozróżniają kod main, zachowany runtime i rozpoczęte poprawki.

Operator po wskazaniu kolizji dwóch claimów T53 polecił: „zatrzymałem kilo.. rób ty”. Powstał własny claim `T53-codex-recommendations.md` i worktree `.kilo/worktrees/codex-swarm-recommendations` na branchu `codex/T53-T55-swarm-recommendations`. Cudze claimy i zmiany pozostają zachowane. Późniejsze polecenie nakazuje najpierw sporządzić dokładny plan i sprawdzić dodatkowy audyt.

Stan przy sporządzeniu listy, przed wznowieniem: rozpoczęty WIP obejmował zmiany w `selfopt_chain/{run_loop,router,engine,omniroute,swarm}.py` oraz nowy `selfopt_chain/quota.py`. Wtedy nie było jeszcze pełnej weryfikacji, integracji z orkiestratorem, commitu, PR ani uruchomienia rzeczywistych modeli. Aktualny stan po wznowieniu opisuje §8 i handoff PO_T53.

Historyczny punkt kontrolny z niezależnej kopii main: 481 Python OK, 378 JavaScript pass / 0 fail, 12 manifestów, 2 ważne seed approvals. Wynik ten nie dotyczy rozpoczętego WIP.

Pięć pakietów poniżej porządkuje zakres. Są to nazwy etapów, nie nowe numery zadań T54/T55: wcześniejsze handoffy już proponują pod tymi numerami inne zadania. Numerację backlogu trzeba uzgodnić w rejestrze, bez przypisywania jednego numeru dwóm pracom.

## 2. Sprawdzenie dostarczonego audytu

| Twierdzenie audytu | Wynik sprawdzenia na main / w zachowanych logach | Konsekwencja dla planu |
|---|---|---|
| Review nie widzi draftu; etapy otrzymują pierwotny payload | Potwierdzone na main: `ChainRunner.make_node_fn` nie dodaje wcześniejszych wyników do promptu. | Naprawa obowiązkowa, K2.1. |
| Brak etykiet i zastosowanej kalibracji | Potwierdzone dla zachowanych 12 cykli; nie jest to dowód braku etykiet we wszystkich możliwych uruchomieniach. | Feedback i test jego użycia, K5.1–K5.3. |
| Wszystkie decyzje mają choice | W zachowanych logach 13/13. W main główne decyzje planisty nadal używają choice, lecz nowy wybór modelu używa model_selection. | Rozróżnienie typów, bez twierdzenia, że każdy typ w nowym kodzie jest choice. |
| Fit od stałego seeda oznacza, że uczenie nie istnieje | Zbyt mocny wniosek. Dopasowanie od zera na całym aktualnym zbiorze etykiet jest poprawnym trybem batch. Obecny fit jest prostą heurystyką, nie optymalizacją jakości decyzji. | Nie dodawać ślepej kumulacji ±0.15 co cykl. Idempotentny fit, ocena na etykietach i jawny model aktualizacji. |
| Ewolucja nie uruchamia się przy no_new_jobs | Nieaktualne dla nowego main: run_cycle wywołuje _run_evolution także w tej gałęzi; dodano evolve-only. | Test obu ścieżek i wspólne bramki, zamiast ponownej implementacji już dodanej funkcji. |
| Dziesięć katalogów to dokładnie to samo zadanie | W zachowanych receiptach jest 10 zadań: pierwszy wpis handoffu 7 razy, trzy kolejne po 1 razie. | Powtarzanie jest potwierdzone, liczba „10 identycznych” jest nieścisła. |
| Nie ma równoległego wykonania ani review mocniejszego modelu | Nieaktualne jako opis main: wide używa ThreadPoolExecutor; istnieje review_by_strong_model. Review ocenia tekst result i nie steruje gate_ok. | Domknąć istniejące mechanizmy, nie budować ich drugi raz. |
| Osiem wywołań daje cztery w daily_calls | Potwierdzone w logach i kodzie record_calls. | K3.1. |
| Podwójne odejmowanie budżetu, snapshot raz na cykl, RPM per run | Potwierdzone. Podwójne odejmowanie dotyczy planistycznego headroom; nie oznacza, że każda ścieżka księguje podwójnie. | Jedna reprezentacja limit/used/remaining, wspólny aktualny ledger. |
| OmniRoute i Hermes omijają wspólną bramkę i budżet | Potwierdzone w badanej pętli. Evolve-only ma osobną ścieżkę, bez zwykłej samokalibracji i quota_gate. | K3.3 oraz K5.3. |
| Free-only gwarantuje brak użycia płatnych zasobów | Nieudowodnione. Funkcja dopuszcza model na podstawie providera; główny adapter sprawdza ją bez argumentu provider, ale automatycznie rozszerza allowlistę katalogiem. Kontrola odpowiedzi następuje po żądaniu. | Jawne modele/poświadczenia/polityka gatewaya przed żądaniem; katalog nie może sam nadawać uprawnień. |
| Dwa z ośmiu wywołań zakończyły się 503 | W obecnie zachowanych traces jest 3/8 failed node_result z HTTP 503. Nie ustalono przyczyny różnicy historycznych liczb. | Używać aktualnie odczytanego wyniku i jawnego zakresu logów. |
| Status ok mimo częściowych błędów; statyczna latencja | Potwierdzone na main. Dodatkowo całkowicie nieudany job jest oznaczany processed. | K2.2–K2.6. |
| Brak obsługi timeoutu Hermesa i zatrzymania wewnątrz pracy | Potwierdzone w wrapperze. | K2.5. |
| Public-only chain i brak implementacji lokalnego stylu API | Potwierdzone na main. Sam router lokalny nie tworzy działającego lokalnego engine. | Najpierw propagacja privacy i odmowa; lokalny engine dopiero jako osobna zweryfikowana zdolność. |
| Flagi Hermesa i cwd są pełnym sandboxem | Wrapper nie ustanawia granicy systemowej. Nie jest to pełny audyt wewnętrznych zabezpieczeń zainstalowanego Hermesa. | K4.3, test rzeczywistych uprawnień. |
| Klucz w argv/receipt jest tylko WIP T52b | Nieaktualne: ta ścieżka jest już na main. Potwierdzenie mechanizmu wykonano na sztucznym kluczu. | K4.2 jako P0. |
| Pusta produkcja może otrzymać zieloną SecurityGate | Potwierdzone w kodzie i receiptach: exit_code=1, scanned_files=0, gate_ok=true. | K4.1 i K4.4. |
| Charter blokuje wytwarzanie/bronowanie i pomija procdev | Potwierdzone. Samo dodanie lewej granicy słowa nie naprawia bronowanie, bo zaczyna się od bron. | Rozpoznawanie słów/odmian z testami; bez blanket allowlisty production/food. |
| MAP-Elites traci archiwum między step i proposal | Potwierdzone: dwie instancje. Dodatkowo domyślna ścieżka nie dostarcza kandydatów. | K5.6; oddzielić naprawę instancji od uruchomienia rzeczywistego eksperymentu. |
| 234425 RPD to pojemność darmowych API; armed to 0.6% | Mylące porównanie. 200000 w tej sumie pochodzi z owned_hardware_low_cost; free_quota ma 34425 seed RPD. 1475/34425 to ok. 4.28%, nadal niezweryfikowanych i niekoniecznie niezależnych pul. | Nie sumować lokalnej przepustowości i limitów API. Brak kluczy/uprawnień jest uzasadnionym powodem wyłączenia części modeli. |
| 3456 calls/dzień i 23040 tur Hermesa/dzień to realny popyt | To scenariusz nasycenia przy wskazanych ustawieniach. Sleep jest po pracy cyklu; brak nowych jobów, błędy i dedup zmieniają obciążenie. Tura Hermesa nie jest jednostką równą jednemu wywołaniu API. | Planowanie po realnych próbach i wspólnych pulach, nie po samej liczbie cykli. |
| Trzeba oznaczyć stare claimy innych agentów abandoned | Sprzeczne z zakazem edycji cudzych claimów. Wiek sam nie dowodzi porzucenia. | Przejęcie tylko na podstawie decyzji operatora; właściciel zmienia własny claim; przypomnienia o starych rezerwacjach. |
| Ocena 2/5 potwierdza nieskuteczność | To ocena autora, nie wynik benchmarku. Negocjacje i emergencja nie są konieczne dla użytecznego systemu wieloagentowego. | Odbiór oparty na artefaktach i mierzalnych niezmiennikach. |

Werdykt po korektach: większość technicznych zarzutów pozostaje zasadna. Dokument jest użyteczny jako wejście do napraw, ale wymaga aktualizacji wersji, liczb i kilku zaleceń. Nie należy traktować go jako gotowej specyfikacji implementacji.

## 3. Dokładna lista potrzebnych zmian

P0 oznacza warunek uruchomienia rzeczywistej pętli po naprawach. P1 oznacza domknięcie procesu ulepszania. P2 oznacza dalszą optymalizację, dopiero po pomiarze.

### K1 — koordynacja, źródło prawdy i testy przed merge

| ID / priorytet | Pliki | Potrzebna zmiana | Kryterium odbioru |
|---|---|---|---|
| K1.1 / P0 | Własny claim T53, nowy handoff | Zapisać decyzję o przejęciu, zakres plików, bazowy commit i zachowane WIP. Uporządkować numery backlogu bez zmiany cudzych claimów. | Jeden faktyczny wykonawca zakresu, jawna decyzja operatora, odtwarzalny stan wejściowy. |
| K1.2 / P0 | NOWE tools/agent_claims.py, tests/test_agent_claim_coordination.py; AGENTS.md | Sprawdzać rezerwacje we wszystkich worktree i wspólnym rejestrze; atomowa rezerwacja pod wspólną blokadą. Obsłużyć odrębne bloki współdzielonego pliku i jawne przekazanie własności. | Dwie równoczesne rezerwacje tego samego zadania/zakresu: dokładnie jedna przyjęta; drugi agent dostaje konflikt przed edycją. Sam lokalny nowy plik nie jest rezerwacją globalną. |
| K1.3 / P1 | AGENTS.md, docs/AGENT_CLAIMS/README.md | Uaktualnić T40–T42 do DONE na podstawie commitów/testów; opisać heartbeat, limit aktywnych zadań i przypomnienia o starych claimach. | Zgodność tabeli i claimów; T45–T47 wymagają statusu od właściciela/operatora, bez automatycznej edycji ich plików. |
| K1.4 / P0 | NOWE .github/workflows/repository_checks.yml | Pełna suita na PR i po zmianach selfopt/testów/koordynacji; walidacja manifestów i approvals, składnia JS. | PR zmieniający wyłącznie selfopt uruchamia pełne kontrole; celowy błąd regresyjny blokuje check. Ustawienie required check w ochronie main jest osobnym krokiem administracyjnym do zweryfikowania. |

### K2 — poprawne wykonanie, porażki i obserwowalność

| ID / priorytet | Pliki | Potrzebna zmiana | Kryterium odbioru |
|---|---|---|---|
| K2.1 / P0 | run_loop.py, orchestrator.py; test_selfopt_chain.py | Przekazywać wyniki zależności do kolejnych etapów; review dostaje konkretny draft i dane źródłowe. Ograniczyć rozmiar kontekstu i zachować informację o pominięciu danych. | Mock sprawdza markery extract w draft i draft w review; przekroczenie limitu jest jawne i nie odcina po cichu materiału koniecznego do oceny. |
| K2.2 / P0 | run_loop.py, graph.py jeśli konieczne | Ustalić wymagane zależności; po błędzie nie uruchamiać etapu wymagającego brakującego wyniku. Rozróżnić failed, degraded, blocked, stopped oraz ich exit codes. | Żaden błąd wymaganego etapu, brak wyjścia, odmowa routingu ani nieudany dispatch nie kończy się ok. |
| K2.3 / P0 | orchestrator.py: run_cycle i stan | Oznaczać processed dopiero po spełnieniu kryteriów wyniku; przechowywać retryable/terminal failure i liczbę prób. Oddzielić technical success od human acceptance. | Całkowicie nieudany job pozostaje do ponowienia; zaakceptowany wynik nie wykonuje się drugi raz; rejected nie jest raportowany jako sukces. |
| K2.4 / P1 | run_loop.py, engine.py, omniroute.py | Ograniczone retry błędów przejściowych, Retry-After/backoff i fallback do dopuszczonego modelu. Brak ponawiania błędów privacy/policy/nieprawidłowego wejścia. | Symulowane 503 → dozwolony fallback; każda próba jest rozliczona; limit prób kończy pętlę; brak retry skutku ubocznego bez idempotencji. |
| K2.5 / P0 | orchestrator.py, hermes_worker.py | Stop przed każdym etapem i wywołaniem, przerwanie backoff/sleep, timeout procesu i zakończenie jego potomków. Zapisać powód i częściowy wynik. | Kill switch podczas pracy zatrzymuje nowe wywołania; lokalny proces testowy i jego potomek kończą się w zdefiniowanym limicie; TimeoutExpired nie zabija daemona bez receiptu. |
| K2.6 / P1 | engine.py, omniroute.py, tracer.py, run_loop.py | Mierzyć rzeczywisty czas monotoniczny; oddzielić measured od estimated latency/tokens; logować attempt_id, requested_model, actual_model i wynik próby. | Mock zegara daje oczekiwany czas; suma prób w trace, receipt i ledger jest zgodna; brak używania speed_class jako pomiaru czasu sieci. |
| K2.7 / P0 | swarm.py, orchestrator.py, run_loop.py | Podłączyć istniejący decision_core do run_chain; walidować typy, skończoność, zakres i zbiór opcji odpowiedzi basal. Wybrany model nadal musi spełniać twarde filtry. | Niepoprawna odpowiedź basal prowadzi do jawnego fallbacku; nigdy nie wybiera niedozwolonego modelu ani nie omija tier/privacy/quota. |

### K3 — jeden rachunek zasobów i egzekwowanie free-only

| ID / priorytet | Pliki | Potrzebna zmiana | Kryterium odbioru |
|---|---|---|---|
| K3.1 / P0 | NOWY quota.py, router.py, orchestrator.py, run_loop.py | Jeden trwały ledger per rzeczywista pula zasobów, atomowa rezerwacja przed żądaniem; osobno attempts/success/failure. Headroom obliczany raz z limitu i zużycia. | 8 prób → 8 attempts; 2 błędne próby nadal zużywają rezerwację. Dwa procesy nie mogą łącznie przekroczyć limitu; restart nie zeruje stanu. |
| K3.2 / P0 | quota.py, konfiguracja rejestru i limity runtime | Rzeczywiste okno RPM, rollover RPD bez restartu, limity per model oraz współdzielone pule konta/providera. Nie traktować niepotwierdzonych seedów jako dostępnego budżetu. | Test na sztucznym zegarze: 60 s, zmiana dnia i dzielona pula dwóch modeli; drugie zadanie widzi pierwsze; wyczerpanie prowadzi do kolejki/odmowy. |
| K3.3 / P0 | orchestrator.py, evolver.py, omniroute.py, hermes_worker.py; możliwy NOWY quota_proxy.py | Te same bramki w normalnym cyklu i evolve-only. Wliczać strategię, review, retry i każde faktyczne żądanie Hermesa. Jeśli Hermes nie udostępnia wiarygodnego hooka, użyć kontrolowanej bramki/proxy. | Zestaw node + strategy + review + Hermes daje identyczne liczby w ledger i logach żądań. Sama rezerwacja max_turns nie jest dokładnym accountingiem. Brak kanału rozliczania blokuje realnego workera. |
| K3.4 / P0 | omniroute.py, registry.py, dokumentacja konfiguracji gatewaya | Allowlista modeli z jawnym statusem kosztu; alias rozwiązywany przed żądaniem. Katalog /models jest informacją, nie zgodą na rozszerzenie listy. Wymagane ograniczenia po stronie gatewaya/poświadczeń. | Nieznany model u znanego providera, podobny alias i sam wpis katalogu nie autoryzują żądania. Naruszenie w odpowiedzi jest rejestrowane i zatrzymuje dalszą pracę. |
| K3.5 / P0 | orchestrator.py, quota.py, CLI | Twarde limity prób, batchy, czasu oraz liczby aktywnych pasm; walidacja dodatnich parametrów. Backlog pochodzi z kolejki, nie z numeru batcha. | Pilot kończy się po zadanym limicie także w evolve-only; brak ujemnych/zerowych nieskończonych pętli; numery batchy nie zwiększają sztucznie presji. |
| K3.6 / P1 | orchestrator.py: stan, quota.py, runbook migracji | Migracja starego daily_calls z użyciem receiptów tam, gdzie dowody istnieją; oznaczenie niepewności i brak resetu zużycia przy aktualizacji. Osobno raportować API i lokalny sprzęt. | Migracja jest idempotentna; nie dolicza dwa razy; brak historii nie staje się fikcyjnym zerowym zużyciem ani dostępną pulą. |

### K4 — prywatność, izolacja i wiarygodny artefakt

| ID / priorytet | Pliki | Potrzebna zmiana | Kryterium odbioru |
|---|---|---|---|
| K4.1 / P0 | orchestrator.py, router.py, engine.py, evolver.py | Klasyfikacja danych propagowana przez cały job, wyniki i podzadania; inbox domyślnie prywatny. Brak lokalnego engine daje kontrolowaną odmowę. | Prywatny marker nie pojawia się w żadnym żądaniu publicznego providera, strategii, review ani eksportowanym artefakcie. |
| K4.2 / P0 | hermes_worker.py, logowanie receiptów | Usunąć prawdziwy klucz z argv, command i logów; przekazywać go wyłącznie kontrolowanym kanałem. Minimalne środowisko i odrębny HOME bez konfiguracji operatora. | Sztuczny sekret nie występuje w poleceniu, output, receipt ani błędzie; worker nie odzyskuje kluczy z odziedziczonego HOME/PATH/config. |
| K4.3 / P0 | hermes_worker.py; możliwy NOWY sandbox.py; runbook | Wprowadzić izolację systemową z jawnymi mountami, prawami zapisu i egresem. Ustalić pakiet runtime Hermesa, bez montowania całego HOME. Brak działającej izolacji blokuje realny run. | Rzeczywisty lokalny proces nie czyta wskazanego pliku hosta ani nie zapisuje poza workspace; widzi tylko dopuszczone wejścia; sieć spełnia ustaloną politykę. Flaga CLI i mock nie wystarczają jako dowód. |
| K4.4 / P0 | hermes_worker.py: SecurityGate i run_isolated; evolver.py | Oddzielić execution_ok, artifacts_present, security_ok, review_ok, validation_ok i ready_for_human_review. Pusta produkcja, exit != 0, symlink poza katalogiem i nieobsługiwany plik nie mogą uzyskać gotowości. | Macierz przypadków: 0 plików; pusty plik; sam log; zły exit; traversal/symlink; poprawny artefakt. Każdy ma jednoznaczny wynik, a nie samo ok od regexów. |
| K4.5 / P0 | evolver.py: review_by_strong_model i _run_task | Recenzent otrzymuje faktyczne pliki/patch, manifest i wyniki walidacji. needs_fixes/fail/unreviewed blokują promocję; kontrolować kompletność materiału przy limitach kontekstu. | Zły plik z pozytywnym opisem result jest odrzucony; brak review nie daje gotowości; pełny patch z przechodzącą walidacją ma odtwarzalny receipt. |
| K4.6 / P1 | swarm.py, charter.json, orchestrator.py, evolver.py | Reguły konstytucji obejmują misje, procdev, inbox i zadania ewolucyjne. Dopasowanie słów/odmian usuwa false positives, bez ogólnego zwolnienia kategorii food/production. | wytwarzanie i bronowanie przechodzą; broń, inwigilacja oraz zakazany opis ukryty w payload są blokowane w każdej ścieżce. |

### K5 — retencja ulepszeń, feedback, optymalizacja i pilot

| ID / priorytet | Pliki | Potrzebna zmiana | Kryterium odbioru |
|---|---|---|---|
| K5.1 / P1 | swarm.py, calibrate.py, orchestrator.py | Oddzielić strategy/allocation/exec_mode/job_selection/model_selection; walidować decision_id i etykiety. Wiadomość feedback nie staje się równolegle nowym jobem procdev. | Etykieta konkretnego typu nie zmienia innych typów; nieznane ID i accepted="false" nie są interpretowane jako poprawna pozytywna etykieta; brak fikcyjnego zadania od feedbacku. |
| K5.2 / P1 | calibrate.py, test_selfopt_calibrate.py | Idempotentny, ograniczony fit na jednoznacznym zbiorze etykiet; polityka korekt/duplikatów, zapis wersji i provenance. Porównać kalibrację z baseline na oddzielonych danych. | Te same etykiety dają tę samą kalibrację; dopisanie duplikatu nie wzmacnia wyniku; korekta ma jawny skutek. Poprawa confidence jest oceniana, nie zakładana. |
| K5.3 / P1 | orchestrator.py: oba tryby, calibrate.py | W obu trybach przyjmować feedback i stosować ostatnią poprawną kalibrację przed decyzjami. Powiązać artifact/run/decision z etykietą i wynikiem human review. | Etykieta po batchu N jest widoczna w decyzji batcha N+1 również przy evolve-only i przy braku nowych jobów; niezmieniony feedback nie dryfuje temperatur. |
| K5.4 / P1 | evolver.py, NOWY trwały indeks ewolucji | Fingerprint treści/wersji zadania i celu, niezależny od losowego run_id i identyfikatora nadanego przez LLM; lifecycle queued/running/needs_fixes/ready/accepted/rejected z retry policy. Bezpieczne ID/ścieżki podzadań. | Po restarcie i przy dwóch workerach ta sama zaakceptowana wersja nie rusza ponownie; nowy identyfikator LLM nie omija dedupu; task_id ../ nie wychodzi poza kolejkę. |
| K5.5 / P1 | evolver.py: zbiór, strategia i wybór modelu | Przeplatać handoff/proposal/target, uwzględniać claimy i status wykonania; priorytetyzować przed obcięciem listy. Model wybierać po zdolnościach/limicie/jakości, nie po substring fast/smart w jego nazwie. Używać wstrzykniętego workera. | Żadne źródło nie jest stale głodzone; ukończone/zajęte zadanie nie wraca z handoffu; single i wide respektują tę samą politykę oraz konfigurację workera. |
| K5.6 / P2 | run_loop.py, optimizers.py, przykładowy benchmark | Zachować instancję i archiwum MAP-Elites; jawnie dostarczać kandydatów, ich zmienność, fitness i wyniki weryfikacji. Oddzielić wykrycie biblioteki od faktycznego użycia algorytmu. | Znany kandydat trafia do proposal; lepszy zastępuje gorszego w niszy; pusta lista raportuje brak eksperymentu. Sam insight nie jest dowodem ewolucyjnego wyszukiwania. |
| K5.7 / P1 | evolver.py; NOWY publisher draft PR i testy; dokumentacja | Tworzyć draft PR wyłącznie z konkretnego patcha po walidacji i spełnieniu warunków ready_for_human_review. Ograniczyć uprawnienia i docelowe ścieżki, użyć fingerprintu przeciw duplikatom. | Jedna zaakceptowana do publikacji propozycja → jeden draft PR z hashem patcha, testami i receiptami; ponowienie nie duplikuje; brak auto-merge i push do main. Lokalny PROPOSAL.md nie udaje PR. |
| K5.8 / P1 | NOWY raport metryk i bounded pilot; tracer.py, runbook | Mierzyć acceptance, useful artifacts/100 attempts, duplicate rate, false success, feedback coverage, real latency i zużycie pul. Stały zbiór wejść, limit czasu/prób/batchy i zapis baseline. | Powtarzalny pilot offline przechodzi wszystkie niezmienniki; następnie mały pilot realny ma jawne limity. Sam wzrost liczby batchy nie jest wzrostem jakości. |

## 4. Zależności i kolejność odbioru

1. K1: własność i punkt odniesienia; pełne CI przygotowane przed merge kolejnych pakietów.
2. K2 oraz fundament K3: rzeczywisty łańcuch, poprawne statusy i jeden licznik. Testy kontraktowe muszą wykazać porażkę na starym kodzie oraz sukces po poprawce.
3. K4 oraz pełne K3: prywatność, artefakt, sandbox i wszystkie wywołania objęte bramką. Dopiero po odbiorze wszystkich P0 możliwy ograniczony run rzeczywisty.
4. K5.1–K5.5: dedup, feedback i zastosowanie kalibracji; następnie K5.7 jako oddzielny etap publikacji po poprawnym artefakcie.
5. K5.8: odbiór pilota; K5.6 i zwiększanie równoległości dopiero po uzyskaniu baseline i wykazaniu korzyści.

Nie ma konieczności wdrażania całej listy jednym PR. Zalecane małe PR-y z jednym rezultatem odbioru, najwyżej pięć zadań na turę. Pliki współdzielone między pakietami oznaczają zależność sekwencyjną lub jawny rozdział bloków, nie zgodę na równoległą edycję.

## 5. Decyzje projektowe ustalone na potrzeby planu

- Prywatne dane: odmowa przy braku działającego lokalnego engine. Nie trzeba rozszerzać tej naprawy o budowę całego nowego lokalnego backendu.
- Kalibracja: domyślnie idempotentny fit batch na walidowanych etykietach. Kumulowanie poprzedniej temperatury jest dopuszczalne dopiero z polityką nowych danych i testem braku podwójnego naliczania.
- Bramka artefaktu: gotowość wymaga wszystkich warunków, nie samego skanu wzorców. Review i wykonanie testów to odrębne dowody.
- Hermes: preferowany istniejący hook request-level; kontrolowany proxy tylko jeśli hook nie zapewnia accounting i polityki. Szczegóły izolacji dobierać do rzeczywistej instalacji, nie do samej obecności polecenia bwrap.
- Free-only: katalog modeli nie autoryzuje użycia. Politykę sprawdzać przed requestem oraz sprawdzać zgodność odpowiedzi; ograniczenie billingu po stronie gatewaya/poświadczeń jest osobnym wymaganiem uruchomieniowym.
- Stare claimy: aktualizacja właściciela lub jawne przekazanie operatora. Nie zmieniać samodzielnie cudzych plików na abandoned.
- Nowe metryki początkowo jako artefakty lokalne. Jeśli później powstanie nowa tabela D1, obowiązuje dedup, audit event i automation_metrics z AGENTS.md.

## 6. Minimalny pakiet dowodów zakończenia

- Commit i zestaw wejść; zgodny claim, handoff i zakres PR.
- Pełne wyniki Python, tests/*.mjs, node --check, manifestów oraz approvals z bieżącego commitu.
- Testy zachowania: przekazanie draftu; failure/retry; 8 prób=8; równoległa rezerwacja; rollover; private bez wycieku; pusty/nieudany Hermes odrzucony; rzeczywisty test izolacji; dedup po restarcie; feedback użyty w następnym batchu.
- Receipty i hashe artefaktów; rozdzielone execution/security/review/validation/human acceptance; rzeczywiste czasy i liczniki prób.
- Pilot kończy się automatycznie po limitach. Stop przy wycieku prywatnych danych, niespójności ledgeru, fałszywym sukcesie wymaganej bramki lub powtarzaniu zaakceptowanej wersji zadania.

## 7. Powiązane dowody

- Wcześniejszy audyt lokalny: `Audyt_roju_selfopt_chain_T48-T52_2026-10-23.md` w głównym checkout.
- Niezależny audyt nowego main i próby offline: `/tmp/straz-swarm-audit-20261023-undjw_zh/AUDYT_ROJU_2026-10-23.md`, `audit_probes.py`, `probe_results.json`, `snapshot_metadata.json`.
- Rzeczywiste zachowane receipty: `.kilo/worktrees/kilo-selfopt/scratch/selfopt/{cycles,runs,evolution_queue,hermes_quarantine}` w głównym checkout. To historyczne uruchomienie; nie należy przypisywać mu wersji nowego main ani WIP.
- Odtworzenie liczby błędów: zliczyć wpisy type=node_result i ok=false w runs/*/traces.jsonl. Odtworzenie liczby duplikatów: zliczyć task_id w cycles/*.json → evolution.tasks.
- Weryfikację źródeł w tym planie wykonano na `git show origin/main:...`, żeby rozpoczęty WIP nie został pomylony ze stanem main.

## 8. Stan po wdrożeniu rdzenia i pilotach

Wdrożono przekazywanie kontekstu, zatrzymanie zależnych etapów po błędzie, poprawne degraded/failed, retryability zadań, wspólny atomowy ledger i konserwatywne pule providerów, bramkę OmniRoute, propagację privacy, jawne modele free, rozdzielone typy decyzji, idempotentny fit etykiet, dedup ewolucji, brak gotowości dla mocków, skan pustych/symlinkowych artefaktów, sandbox i proxy rozliczające API Hermesa, atomowe narzędzie claims, pełną suitę PR oraz launcher i metryki pilota.

Pozostają do osobnych etapów: pełny runtime rzeczywistego Hermesa, automatyczna publikacja draft PR przez rój, benchmark i generowanie kandydatów optymalizatorów, kalibracja oceniona na rzeczywistych etykietach, pełny lifecycle retry/lease ewolucji po przerwaniu oraz pomiar rzeczywistych limitów kont/providerów i ich stref resetu. Narzędzie claims sprawdza zakresy plików dla nowych claimów z metadanymi; stare claimy bez metadanych tylko po numerze zadania. Włączenie nowego checku jako required w GitHub branch protection wymaga osobnego sprawdzenia administracyjnego.

Szczegółowe wyniki i granice: handoff PO_T53 oraz RUNBOOK_PILOTA_ROJU_T53_2026-10-23.md. Pierwszy pilot rzeczywisty poprzedzał ostatnie poprawki. Każdy kolejny start ma własny source_manifest, a żadne wyniki pilota nie są dowodem human acceptance lub poprawy uczenia.
