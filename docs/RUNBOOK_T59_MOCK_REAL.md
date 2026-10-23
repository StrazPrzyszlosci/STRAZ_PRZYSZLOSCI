# Odbiór T59: symulacja, restart, realne wykonanie

Uruchamiaj na własnym, czystym commicie T59. Lokalny Basal: http://127.0.0.1:8000, istniejący Ollama: 127.0.0.1:11434. Nie pobieraj modeli ani nie restartuj usług wyłącznie z powodu timeoutu obserwacji.

Stan pilota musi być odrębny od historycznego pilota T58, ale używać tego samego quota ledger: `.kilo/worktrees/codex-swarm-recommendations/scratch/selfopt/pilot-live/quota_ledger.json` od głównego katalogu repo. Zachowaj wcześniejszy indeks i feedback jako wejście odniesienia; nie kopiuj ledgeru do nowego pustego licznika. Stan początkowy: 66 prób łącznie, limit operatora 80 (nie jest zweryfikowaną kwotą providera).

Najpierw uruchom jeden batch mock, max_tasks=1, bez sieci API i bez Hermesa. Zapisz hash wejść i receipt simulated. Następnie uruchom realny ograniczony pilot na tym samym snapshotcie i stanie: max 2 batche, jedno zadanie na batch, max 600 s, max_calls=80 na istniejącym ledgerze, wyłącznie jawne zarejestrowane modele :free.

Launcher: `node tools/run_swarm_pilot.mjs --real --evolve --state-dir <STATE> --quota-ledger <EXISTING_LEDGER> --runtime <PREPARED_HERMES_RUNTIME> --max-calls 80 --max-seconds 600 --pause 5 --turns 8 --use-omniroute-db-key`. Zmienna SELFOPT_OMNIROUTE_KEY ma pierwszeństwo; wskazany fallback do jednej aktywnej wartości lokalnej bazy został jawnie autoryzowany przez operatora w rozmowie. Klucz pozostaje wyłącznie w pamięci i środowisku procesu, nie w argv, dokumentach ani logach.

Odbiór: ta sama wersja wejść przechodzi simulated→real, poprzedni receipt pozostaje w simulation_history, a po restarcie gotowa wersja nie jest ponownie produkowana. Liczniki przed/po muszą zgadzać się z faktycznymi próbami, także nieudanymi, strategią i review. Priorytety, model i decyzje lokalnego Basal mają być zapisane jako dowody, a nie odtworzone z opisu.

Stan ready wymaga wykonania, artefaktów, bezpieczeństwa, niezależnej walidacji i review. Opis, mock, green regex gate oraz brak nowych jobów nie są dowodem ewolucji. Publikacja wyłącznie jako draft PR na osobnym branchu, no_auto_merge/no_direct_push/suggest-only. W razie braku budżetu lub nieprzechodzącego odbioru zapisz faktyczny stan; nie zwiększaj automatycznie limitu i nie resetuj historii.

Po pierwszym ograniczonym pilocie pozostało 11 prób do cap 80 (ledger 69). Dla diagnostycznego ponowienia użyj dodatkowo `--batches 1 --max-seconds 300`. Tryb waiting_provider oznacza cooldown, waiting_rate_limit okno RPM, a waiting_budget wyczerpany limit; sprawdź resource_status. response_diagnostic pokazuje tylko kształt/rozmiary/tokeny i finish_reason, nie tekst odpowiedzi ani reasoning. Nie traktuj reasoningu jako gotowej produkcji.

Po diagnozie batcha 4 ledger ma 72 próby. NVIDIA zużyła 4096 tokenów wyłącznie na reasoning i zakończyła length. Kolejna pojedyncza próba używa domyślnego budżetu producenta 8192 oraz `SELFOPT_REQUEST_TIMEOUT=150`, `--batches 1 --max-seconds 480`; cap nadal 80. SELFOPT_CODE_MAX_TOKENS dopuszcza 1024..16384, bez automatycznego zwiększania po porażce. Zapisuj faktyczny budżet i wynik, nie tylko status HTTP.

Po batchu 5 ledger wynosi 75. Nowa wersja ma jawne role w runtime_model_profiles.json i schemat odpowiedzi producenta. `--real --inventory-only` odświeża odkryte modele i profile bez inferencji; `discovered_needs_role_qualification` nie oznacza modelu gotowego do produkcji. Nie dodawaj do ról kodowych modeli moderation/safety tylko dlatego, że widnieją w katalogu. Przed Basal lista jest filtrowana i ograniczana do 20; singleton nie wymaga inferencji decyzyjnej. Pozostałe modele kwalifikuj oddzielnymi, ograniczonymi próbami z rzeczywistą walidacją artefaktów.
