# Ograniczony pilot roju po T53

Komendy uruchamiaj z worktree zawierającego naprawy. `main` pozostaje pod review PR.

## Uruchomienie

```bash
# Dwa cykle offline, maksymalnie 8 prób silnika mock:
node tools/run_swarm_pilot.mjs

# Rzeczywiste modele, klucz tylko z SELFOPT_OMNIROUTE_KEY:
node tools/run_swarm_pilot.mjs --real

# Jawnie dozwolony fallback do aktywnego klucza lokalnego OmniRoute:
node tools/run_swarm_pilot.mjs --real --use-omniroute-db-key

# Jawna zmiana łącznego limitu dobowego istniejącego pilota, bez zerowania ledgeru:
node tools/run_swarm_pilot.mjs --real --use-omniroute-db-key --max-calls 16

# Wyniki:
python3 selfopt_chain/metrics.py --state-dir scratch/selfopt/pilot-live

# Zatrzymanie:
touch scratch/selfopt/pilot-live/KILL_SWITCH
```

Klucz z env ma pierwszeństwo. Odczyt bazy jest możliwy wyłącznie z jawną flagą; uruchomienie z nią wymaga zgody właściciela poświadczeń. W tej sesji operator wyraźnie zezwolił na ten fallback. Zaszyfrowany rekord jest dekodowany funkcją z zainstalowanego OmniRoute. Klucz nie trafia do źródeł, argv, manifestu ani logów. Launcher nie zmienia konfiguracji gatewaya i nie zapisuje klucza.

Launcher wybiera konkretne identyfikatory `:free` z uwierzytelnionego katalogu. Nie korzysta z aliasów auto ani z dowolnego modelu znanego providera. Domyślne limity: 2 cykle, 8 prób, 300 s całości, 60 s pojedynczego żądania. `--max-calls` dopuszcza 1–32 jako całkowity limit istniejącego ledgeru; ponowne uruchomienie nie odnawia zużytego budżetu. Przed zadaniem wymagane są przynajmniej cztery pozostałe próby; fallback może zużyć więcej i doprowadzić do kontrolowanej degradacji.

Wygenerowany quota_snapshot opisuje konserwatywne limity operatora. Nie stanowi pomiaru faktycznej dostępności limitów upstream; pliki i log startowy jawnie zapisują `upstream_quota_verified=false`. Katalog `:free` i kontrola identyfikatora odpowiedzi ograniczają wybór, lecz nie są audytem rozliczeń dostawcy.

## Dowody i interpretacja wyników

- `cycles/*.json`: wynik cyklu oraz przyczyna pominięcia/odmowy.
- `runs/*/{traces.jsonl,run_receipt.json,final_outputs.json}`: próby, statusy i wyniki etapów.
- `quota_ledger.json`: trwałe zużycie, okno RPM i dobowy budżet, wspólne dla zadań/pasm.
- `orchestrator_state.json`: ukończone zadania; błędny job pozostaje do ponowienia.
- `procdev_queue/*.md`: propozycje do review, bez auto-aplikacji.
- `source_manifest_*.json`: hashe kodu użytego w kolejnych uruchomieniach.
- `pilot_metrics.json`: wyniki techniczne; human acceptance jest osobną, niezałożoną wielkością.

Nie usuwaj ledgeru w celu ponowienia pilota. Jeśli źródło danych lub konfiguracja limitu ulegają zmianie, zachowaj poprzednie receipty i uzasadnienie zmiany. `daily_budget_exhausted` i `insufficient_budget` są stanami kolejki, nie dowodem ukończenia pracy.

## Hermes i ewolucja

Launcher pilota rzeczywistego ustawia `SELFOPT_HERMES=0`: sprawdza planistę, router i łańcuch API. Launcher offline dodatkowo sprawdza kolejkę ewolucji na mockach; mock nie uzyskuje `ready_for_human_review`.

Rzeczywisty worker Hermes wymaga osobno przygotowanego, pozbawionego sekretów runtime wskazanego przez `SELFOPT_HERMES_RUNTIME`, z plikiem `bin/hermes` działającym po montażu pod `/runtime`. Nie montuj całego hostowego HOME ani hostowego wrappera ze ścieżkami do prywatnej instalacji. Brak runtime blokuje workera.

Sandbox bubblewrap ma osobny namespace sieci, minimalne mounty, zapis do `/work`, własny HOME i jedyny kontrolowany kanał API przez socket Unix. Proxy dopuszcza ustalony model i księguje każdą próbę przed upstream. Producent nie dostaje klucza gatewaya. Timeout/stop kończy proces, a produkcja pozostaje w kwarantannie. Syntax/code tests, skan i review to osobne pola receiptu. Zrealizowano lokalny test tej ścieżki z atrapą Hermesa i atrapowym upstream; nie jest to dowód działania pełnego zainstalowanego Hermesa.

Automatyczna publikacja propozycji roju jako GitHub draft PR pozostaje osobnym zadaniem. Obecna kolejka nie nazywa lokalnego PROPOSAL.md rzeczywistym PR-em. Merge i aktuacja nadal wymagają dotychczasowych bramek.

## Kolejny etap

Najpierw oceń artefakty i oznacz prawdziwe decyzje przez istniejące `calibrate.py annotate`. Brak etykiet oznacza brak potwierdzonej poprawy decyzji. Następnie przygotuj runtime Hermesa i oddzielny ograniczony pilot produkcji patcha, testów, review oraz draft PR. Rozszerzenie na OpenClaw, nowe modele i szeroką równoległość wymaga pomiaru korzyści względem tego pilota.
