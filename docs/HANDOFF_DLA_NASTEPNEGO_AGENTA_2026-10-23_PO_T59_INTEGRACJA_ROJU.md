# Handoff T59 — integracja i odbiór rzeczywistej ewolucji

Status: zakończony etap T59 integracji, odbioru i przekazania. Cel „pracuj, żeby rój stabilnie ewoluował” pozostaje nieudowodniony. Operator przekazuje dalszą implementację GLM 5.3; aktualny punkt wejścia: [instrukcja GLM 5.3](HANDOFF_DLA_NASTEPNEGO_AGENTA_2026-10-23_PO_T59_ZALECENIA_GLM_5_3.md).

Operator potwierdził zakończenie pracy Kilo. Jego claim ma abandoned-duplicate; commit 2a72b37 i WIP claimu zachowano bez zmian. Codex utworzył osobny branch codex/T59-swarm-integration w worktree codex-swarm-integration na bazie T58 77cf830 i atomowo zarezerwował własny zakres T59 przed edycją kodu.

Zastosowano przygotowany patch SHA256 3f311b8e756ebde2ed81f3b0fa3749eac84ad36e839893106907d3d156ae4570, odebrany wcześniej na odseparowanej kopii (527 Python OK). Integracja obejmuje lokalny styl API i instrukcje Basal z Kilo, addytywną regułę charteru, 11 dostosowanych scenariuszy oraz naprawę simulated→real. Weryfikacja bieżącego worktree i rzeczywisty pilot są w toku.

Odbiór bieżącego worktree: **527 Python OK; 378 JavaScript pass / 0 fail; 12 manifestów poprawnych; approvals ważne; 7 aktywnych claimów bez konfliktów; git diff --check OK**. Nie dotykano plików JavaScript, więc osobna kontrola składni zmienionych JS nie ma wejść. Stan pilota `scratch/selfopt/t59-live` zachowuje indeks i feedback poprzedniego pilota, ale współdzieli oryginalny ledger; jego początkowe 66 prób nie zostało wyzerowane. Rzeczywiste wyniki pilota pozostają do odbioru.

## Zakres tej tury (do pięciu etapów)

1. Zintegrować odebrane zmiany bez nadpisywania istniejącego ledgeru, sandboxa i retencji.
2. Odebrać pełną regresję i atomowe wznowienie symulacji po uzbrojeniu; brak ponowienia zaakceptowanej wersji.
3. Wykonać ograniczony pilot mock→real na identycznym snapshotcie i stanie, z lokalnym Basal i istniejącym współdzielonym ledgerem; startowe zużycie 66, operator cap 80.
4. Sprawdzić rzeczywistą produkcję, niezależny odbiór baseline FAIL/candidate PASS/regresja PASS oraz osobne review; porażka nie jest sukcesem ani human acceptance.
5. Zachować dowody, metryki, przydział zadań i restart bez duplikatów; przygotować draft PR. Nie merge do main.

## Otwarte warunki

Bezpieczny defer i kod zakończenia daemona pozostają zadaniami ewolucji do rzeczywistego odbioru. Nie przypisywać ręcznym poprawkom autorstwa modelu. Lokalny Basal jako decydent jest potwierdzony; osobny FreeApiEngine z modelem basal-omni-pico przekroczył limit 30 s i nie został uznany za wdrożony lokalny backend ogólny. Charter, bezpieczeństwo i brak aktuacji nadal obowiązują.

## Pierwszy ograniczony pilot rzeczywisty

Snapshot 94b8f9f: batch 1 mock wybrał target_daemon_failure_exit. Po restarcie realnym batch 2 podjął ten sam hash wejść `125d9a93b9a6e1e9ccf02164500e634392f888cc5629d10381782926803d1c06`, z attempts=1 i simulation_history długości 1. Zatem naprawa promocji została sprawdzona również rzeczywistym uruchomieniem workera, nie tylko fixture.

Strategię podało Cohere; priorytety: daemon_failure_exit (100), następnie deferred_job_selection (90). Lokalny Basal wybrał single, direct_patch (confidence 0.6233) i NVIDIA (0.555). NVIDIA zakończyła się connection_error po 60060 ms; automatyczny fallback Cohere zwrócił bad_response/empty response. Nie powstał patch, walidacja ani pozytywne review. Ledger: **66→69**, zgodnie z 1 wywołaniem strategii i 2 próbami producenta. Kolejny batch nie wywołał modeli, bo oba były w cooldownie, błędnie opisanym jako waiting_budget. Proces zakończył się; nie restartowano go z powodu timeoutu obserwacji.

Na podstawie tych wyników dodano rozróżnienie cooldown/RPM/RPD/globalnego limitu, bezpieczną diagnostykę kształtu odpowiedzi (liczby i znane pola, bez tekstu/sekretów), rzeczywistą latencję błędnej odpowiedzi i per-attempt receipty producenta. Wybór modelu dostaje teraz rzeczywiste sukcesy/porażki transportu; nie jest to ocena jakości merytorycznej ani human label. Launcher przyjmuje --batches 1..8 dla krótszego odbioru. Odbiór po zmianach: **533 Python OK**, 6 nowych testów; składnia launchera i diff OK. Poprzednie 378 testów JS dotyczą niezmienionych plików tests/*.mjs i cloudflare/src; pełne CI ponowi je na PR.

Następna próba: jeden batch na tym samym stanie i ledgerze 69/80, max 300 s. Nie resetować zużycia ani zwiększać automatycznie limitu. Cel stabilnej ewolucji pozostaje aktywny; sam poprawny start workera nie jest produkcją ulepszenia.

## Diagnoza limitu odpowiedzi

Snapshot 35e15fb, batch 4: NVIDIA zwróciła `finish_reason=length`, content_chars=0, completion_tokens=4096 i reasoning_tokens=4096 (latencja 54780 ms). Producent nie miał żadnego końcowego kodu; reasoning nie został uznany za artefakt ani zapisany w diagnostyce. Fallback Cohere przekroczył 60 s. Ledger **69→72**, nadal dokładnie 1 strategia + 2 próby producenta. Zero nowych patchy i brak review. Oba procesy pilota zakończone.

Producent kodu ma teraz jawny budżet 8192 tokenów (konfigurowalny 1024..16384), zapisany w receipcie; pozostałe role nie dostały podwyższenia. Następna pojedyncza próba ma limit żądania 150 s i batcha 480 s, z niezmienionym ledgerem 72/80. Zmiana wynika z danych, a nie z traktowania pustej odpowiedzi jako powodzenia.

Sprawdzono też kontrakt zainstalowanego lokalnego basal-serve: confidence jest maksimum rozkładu probabilities. Most odrzuca błędne typy, NaN, brakujące opcje, złą normalizację i sprzeczne confidence; poprawny wybór modelu nadal jest respektowany. Stary fixture z probabilities 0.2/0.8 i confidence 0.91 skorygowano do faktycznego kontraktu 0.8, a osobny test wymaga odrzucenia niespójnego rozkładu. **535 Python OK**. Walidacja protokołu nie jest dowodem kalibracji jakości decyzji Basal: w ostatnim przebiegu poprawne protokołowo p=1 wybrało NVIDIĘ mimo wyższego heurystycznego score Cohere.

## Aktualny audyt działania i puli modeli, 18:10 Europe/Warsaw

Na polecenie operatora sprawdzono host poza sandboxem: działają dwa procesy Kilo (PID 1130876 zwykły i 1222173 evolve-only), oba na `kilo-selfopt` b9cbb71 i tym samym stanie. T59 4528e2d nie jest uruchomiony. Zwykłe cykle 18–20 blokuje missing_snapshot; batche ewolucji 15–17 są puste. Kolektor: 13 zadań przed dedup, 0 po dedup; 21 fingerprintów obejmuje także potwierdzone błędy workera. Nie restartowano ani nie zatrzymywano tych procesów podczas audytu.

Aktualny katalog: 2474 wpisy, 53 wpisy :free z aliasami, w tym 13 pełnych nazw modeli Kilo. Aktywne konfiguracje połączeń: Kilo/Mistral/NVIDIA; katalog i status active nie potwierdzają dostępności każdego modelu ani zerowego kosztu. Wersja Kilo rozbudowuje listę do 316 kandydatów i wysyła całość do lokalnego Basal, którego OllamaBackend obsługuje maks. 20 opcji. Próba 21 opcji zwróciła HTTP 422. **21/21 zapisanych wyborów modelu Kilo ma engine=builtin**, więc lokalny Basal, choć zdrowy, nie wykonywał tych wyborów. Dodatkowo DDG bez tool calling był przydzielany Hermesowi, a routing Kilo opiera się na fast/smart w nazwie.

Pełny odbiór i rekomendacja: `docs/AUDYT_MODELI_ROJU_T59_2026-10-23.md`. Metadane katalogu, konfiguracji, historii wywołań i procesów zapisano bez sekretów w scratch/selfopt/llm-audit-20261023. Nie wysłano nowych promptów do publicznych LLM i nie zwiększono ledgeru T59 (nadal 72/80). Wniosek: nie uruchamiać ślepo wszystkich wpisów; najpierw kanonizacja i kwalifikacja, twarde filtry ról/kwot, potem shortlista <=20 dla Basal i pomiar artefaktów. Cel pozostaje aktywny i nieudowodniony.

Doprecyzowanie po sprawdzeniu /proc starttime: zwykły proces ruszył 16:13, przed HEAD b9cbb71 (17:33), więc HEAD nie dowodzi jego załadowanych importów. Evolve-only ruszył 17:36 po commicie. 21 wyborów builtin dotyczy zachowanej historii wcześniejszych batchy; obecny daemon ma tasks=[] i nie wykonuje nowych wyborów. Błąd 316>20 pozostaje w aktualnym kodzie i został niezależnie odtworzony kontraktową próbą 21 opcji.

## Zastąpienie starych instancji i kwalifikacja ról

Po ponownej kontroli pustej kolejki wysłano SIGTERM wyłącznie do PID 1130876 i 1222173; stan Kilo zachowano. O 19:03 potwierdzono zakończenie obu PID-ów, a nie sam fakt wysłania sygnału. Basal/Ollama/OmniRoute nie były zatrzymywane. Dowód: `scratch/selfopt/t59-live/cutover.json` i wynik kontroli hosta.

Ograniczony pilot snapshotu 26b0215 z budżetem kodu 8192 uruchomił batch 5: NVIDIA przekroczyła 150 s, fallback Cohere odpowiedział po 15.8 s, ale zwrócił obiekt tool_call_id/tool_name/content zamiast planu patcha. Nie przyjęto go jako produkcji. Ledger **72→75**, zgodnie z jedną strategią i dwiema próbami producenta. Proces pilota zakończył się; nie działa w tle.

Naprawy wynikające z odbioru: producent otrzymuje systemowy zakaz żądania narzędzi i ścisły response_format/json_schema (proposal, edits, new_files); kontroler niezależnie odrzuca obce obiekty narzędzi. Shortlista filtruje koszt/prywatność, role, tier, code/JSON, obsługę narzędzi, kontekst i dostępność przed Basal: domyślnie 8, twardo maks.20. Jedna opcja jest deterministyczna i nie wywołuje lokalnego API wymagającego min.2 opcji. Brak pasującego profilu blokuje zadanie przed płatnym w sensie zużycia limitu planowaniem.

Launcher zapisuje pełną kanoniczną inwentaryzację :free Kilo, bez duplikatów kc/ oraz skrótowych aliasów. Bieżący odczyt bez inferencji: **13 modeli, 2 profile do ograniczonych prób, 11 discovered_needs_role_qualification**. Profile nie deklarują zweryfikowanej jakości: North Mini do kodu i planowania, Lightning do reasoning/review, poza produkcją kodu po obserwowanych błędach. Kontekst i tool calling pochodzą z katalogu; to nadal deklaracje wymagające kwalifikacji. `--inventory-only` nie uruchamia orkiestratora i nie zmieniło ledgeru.

Odbiór poprawionej wersji: **541 Python OK; 378 JS pass / 0 fail we właściwym worktree; składnia launchera, 12 manifestów i approvals poprawne; brak konfliktów claimów; diff OK**. Sześć nowych testów obejmuje pulę 316 modeli, filtr ról/tools/context, singleton, brak kosztu przy niegotowej roli i rzeczywisty kształt requestu JSON oraz odrzucenie obcego tool-call. Dwa stare fixture DirectPatch uzupełniono o wymagane new_files=[], zachowując testy exact-match i traversal.

Następny krok: jeden batch rzeczywisty na tym snapshotcie, ledger **75/80**, max 480 s, timeout 150 s. Producent i recenzent mają oddzielne role; priorytet daemon_failure_exit pozostaje pierwszy. Nie wdrożono ręcznie poprawki tego celu ani nie przypisano fixture autorstwa roju. Pełna kwalifikacja pozostałych 11 modeli i stabilna ewolucja pozostają otwarte.

## Końcowy odbiór i przekazanie GLM 5.3

Batch 6 snapshotu 051c987: lokalny Basal wybrał single i Hermes. Po filtrach pozostał Cohere jako jedyny model kodowy. Strategia zużyła 1 request, Hermes 4; ledger **75→80/80**. Kolejne żądanie zatrzymał lokalny limit. Cztery wykonane narzędzia terminala czytały repo; nie powstał artefakt. Receipt needs_fixes, gate false, walidacja/review nieprzeprowadzone. Exit daemona nadal 0 mimo błędu. Nie ma nowego gotowego patcha ani PR wytworzonego przez rój.

W odpowiedzi dodano preflight budżetu wykonawcy (strategia + próby/turns + review) z uwzględnieniem puli providera. Jest to oszacowanie, nie rezerwacja współbieżna. Basal wybiera model także do strategii i review; krótka lista uwzględnia wymagane capabilities i tier właściwy dla rodzaju zadania. Uzupełniono nieaktualne opisy podziału odpowiedzialności OmniRoute/Basal.

Na polecenie operatora dodano odczytowy hardware_context: host CPU/affinity/cgroup, RAM, dysk i obecność GPU, bez sekretów/identyfikatorów. Kontekst trafia do Basal oraz wejść strategii/wykonawcy i nie zmienia hash wersji zadania. Doprecyzowanie operatora: sprzęt ogranicza dopiero przyszły wybór lokalnego LLM; obecnie lokalny jest tylko Basal, a rozmiar modeli zdalnych nie jest filtrowany RAM/GPU hosta.

Końcowa regresja: **550 Python OK; 378 JS pass / 0 fail w 38 plikach**, składnia launchera, 12 manifestów i approvals poprawne. Basal/Ollama mają aktywne transient units użytkownika; ograniczony pilot jest zakończony, starych instancji Kilo nie ma. Nie odebrano wdrożenia 24/7/reboot. Stan i dowody zachowano. GLM otrzymuje pięć etapów T60–T64 z warunkami odbioru; claim T59 zamknięto jako done dla tego etapu, nie jako potwierdzenie celu stabilnej ewolucji.
