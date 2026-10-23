# Odbiór T59: symulacja, restart, realne wykonanie

Uruchamiaj na własnym, czystym commicie T59. Lokalny Basal: http://127.0.0.1:8000, istniejący Ollama: 127.0.0.1:11434. Nie pobieraj modeli ani nie restartuj usług wyłącznie z powodu timeoutu obserwacji.

Stan pilota musi być odrębny od historycznego pilota T58, ale używać tego samego quota ledger: `.kilo/worktrees/codex-swarm-recommendations/scratch/selfopt/pilot-live/quota_ledger.json` od głównego katalogu repo. Zachowaj wcześniejszy indeks i feedback jako wejście odniesienia; nie kopiuj ledgeru do nowego pustego licznika. Stan początkowy: 66 prób łącznie, limit operatora 80 (nie jest zweryfikowaną kwotą providera).

Najpierw uruchom jeden batch mock, max_tasks=1, bez sieci API i bez Hermesa. Zapisz hash wejść i receipt simulated. Następnie uruchom realny ograniczony pilot na tym samym snapshotcie i stanie: max 2 batche, jedno zadanie na batch, max 600 s, max_calls=80 na istniejącym ledgerze, wyłącznie jawne zarejestrowane modele :free.

Launcher: `node tools/run_swarm_pilot.mjs --real --evolve --state-dir <STATE> --quota-ledger <EXISTING_LEDGER> --runtime <PREPARED_HERMES_RUNTIME> --max-calls 80 --max-seconds 600 --pause 5 --turns 8 --use-omniroute-db-key`. Zmienna SELFOPT_OMNIROUTE_KEY ma pierwszeństwo; wskazany fallback do jednej aktywnej wartości lokalnej bazy został jawnie autoryzowany przez operatora w rozmowie. Klucz pozostaje wyłącznie w pamięci i środowisku procesu, nie w argv, dokumentach ani logach.

Odbiór: ta sama wersja wejść przechodzi simulated→real, poprzedni receipt pozostaje w simulation_history, a po restarcie gotowa wersja nie jest ponownie produkowana. Liczniki przed/po muszą zgadzać się z faktycznymi próbami, także nieudanymi, strategią i review. Priorytety, model i decyzje lokalnego Basal mają być zapisane jako dowody, a nie odtworzone z opisu.

Stan ready wymaga wykonania, artefaktów, bezpieczeństwa, niezależnej walidacji i review. Opis, mock, green regex gate oraz brak nowych jobów nie są dowodem ewolucji. Publikacja wyłącznie jako draft PR na osobnym branchu, no_auto_merge/no_direct_push/suggest-only. W razie braku budżetu lub nieprzechodzącego odbioru zapisz faktyczny stan; nie zwiększaj automatycznie limitu i nie resetuj historii.
