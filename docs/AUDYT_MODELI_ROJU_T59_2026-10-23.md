# Działający rój i dobór darmowych LLM — odbiór 2026-10-23

Ostatnia kontrola procesów i kolejek: **18:10 Europe/Warsaw**. Katalog bramki odczytany o 17:52. Zakres: rzeczywiste procesy hosta, aktywna gałąź Kilo `b9cbb71`, integracja T59 `4528e2d`, uwierzytelniony katalog OmniRoute, niesekretne metadane połączeń i historia wywołań wybranego aktywnego klucza z ostatnich sześciu godzin. Nie odczytywano treści historycznych żądań/odpowiedzi ani innych poświadczeń; nie wykonywano nowych wywołań publicznych LLM podczas audytu.

**Werdykt: aktywny rój nie wykorzystuje prawidłowo pełnej puli darmowych LLM i nie przydziela ich konsekwentnie według zdolności. Procesy działają, ale obecnie nie wykonują zadań. Sam katalog nie dowodzi, że wszystkie jego modele są dostępne i bezpłatne na danym koncie.**

## Co rzeczywiście jest uruchomione

| Proces | Worktree | Bieżący wynik |
|---|---|---|
| PID 1130876, zwykły orkiestrator | `kilo-selfopt`, `b9cbb71` | cykle 18–20: `skipped_quota_gate`, `missing_snapshot` |
| PID 1222173, `--evolve-only` | ten sam worktree i stan | batche 15–17: `tasks=[]`, `deterministic_fallback` |
| Integracja T59 | `codex-swarm-integration`, `4528e2d` | brak aktywnego orkiestratora tej wersji; ostatnie ograniczone próby zakończone |
| Lokalny Basal i Ollama | localhost:8000 / :11434 | oba odpowiadają; Basal health=ok |

Kod CLI Kilo przekazuje quota snapshot tylko dla `free-api`, mimo że jego bramka obejmuje też `omniroute`. Dlatego zwykłe cykle są blokowane niezależnie od rzeczywistej dostępności modeli. Nie należy usuwać bramki; trzeba przekazać jej prawidłowy snapshot i stosować wspólny ledger.

Kolektor Kilo widzi **13 zadań**, ale po uwzględnieniu `evolution_processed.json` zwraca **0**. Indeks ma 21 fingerprintów. Potwierdzono zadania z niezerowym wyjściem workera, które są nadal traktowane jako przetworzone i wyłączone z ponowienia. To przyczyna bezczynności, a nie dowód zakończonej ewolucji.

W zachowanej kolejce Kilo jest 27 receiptów Hermesa, z czego **24 mają scanned_files=0**. Osiem procesów zakończyło się kodem 0; nie jest to dowód poprawnego artefaktu. Nie znaleziono `changes.patch` w `evolution_queue`; cztery `PROPOSAL.md` obejmują także symulacje. Historia zawiera wyniki bramek z różnych wersji, więc nie liczyć każdego starego `ok=true` jako obecnego, zweryfikowanego ulepszenia. Aktualne pliki batchy są nadpisywane po restartach i nie rekonstruują całej historii.

## Ile modeli jest dostępnych w katalogu

- OmniRoute zwraca **2474 wpisy**, obejmujące także aliasy, usługi wymagające innych kont i modele bez potwierdzonej darmowości.
- **53 wpisy mają końcówkę `:free`**: 52 aliasy Kilo oraz `auto/coding:free`. Pełnych identyfikatorów `kilocode/<dostawca>/<model>:free` jest **13**. Nie są to 53 różne modele ani 2474 potwierdzone darmowe modele.
- W konfiguracji połączeń są aktywne wpisy **Kilo, Mistral i NVIDIA**. Status konfiguracji `active` nie potwierdza działania każdego modelu. W historii są m.in. 404 dla modeli NIM i 429 dla części Mistrala.
- Bazowy rejestr repo deklaruje 13 modeli / 8 providerów, w tym dwa lokalne placeholdery. Obecność zmiennej środowiskowej Google/OpenRouter nie jest testem poprawności uprawnień ani darmowej kwoty.
- Launcher T59 ma na stałe listę trzech preferencji, po czym robi `candidates.slice(0, 2)`. Pilot używa tylko North Mini Code i Nemotron 3.5 Lightning. Dla obu wpisuje jednakowe `quality_tier=4`, `speed_class=fast`, capabilities i kontekst 32768 — wartości heurystyczne.
- Bieżący katalog podaje dla North Mini kontekst 256000 / wyjście 64000, a dla Lightning 1000000 / 65536. Metadane pilota nie odzwierciedlają więc nawet danych bramki. Same deklaracje bramki także wymagają prób kontraktowych; nie są benchmarkiem jakości.

Kwalifikowane nazwy `:free` Kilo: Nemotron 3.5 Super VL, Flint, Xing4.0, Dots3 Note Preview, LFM2.5, Nemotron 3.5 Lightning, Laguna S, Laguna XS, North Mini Code, Nemotron 3.5 Content Safety, Nemotron 3 Ultra, Nemotron 3 Nano Omni i Nemotron 3 Super. To lista do kwalifikacji, nie informacja, że każda trasa została przetestowana i ma obecnie wolną kwotę.

## Dlaczego przydział nie jest adekwatny

### Basal otrzymuje zbyt wiele opcji

Polityka Kilo rozszerza allowlistę modelami całych providerów i nazwami `:free`. Dla odczytanego katalogu daje to **316 kandydatów**, z których 303 nie mają profilu w bazowym rejestrze. `_lane_model()` przekazuje całą tę listę do Basal.

Lokalny backend Ollama obsługuje maksymalnie **20 opcji**. Kontrolowane żądanie z 21 opcjami zwróciło HTTP **422**: `OllamaBackend reads at most 20`. W logu Kilo wszystkie **21/21 wyborów modelu** mają `engine=builtin`, a ostatnie osiem ma options_count=316 i komunikat fallbacku. Basal jest zdrowy, ale te decyzje nie są wykonywane przez lokalny LLM. Komunikat o jego nieosiągalności maskuje błędny kontrakt wejścia.

Przy niemal równych score'ach confidence wynosi ok. 0.0032; następuje defer i wybór domyślnego modelu pasma. To zachowanie kolejności/round-robin, nie świadoma kwalifikacja zdolności 316 modeli.

### Brak twardych profili zadań

Kilo przyznaje dodatkowy score za słowa `fast` / `smart` w nazwie modelu. Nie filtruje kandydatów do ewolucji według code/JSON/tool calling, kontekstu ani zmierzonej przydatności do konkretnej roli.

Przykład: modele `ddgw/...` mają w bieżącym katalogu `tool_calling=false`, ale były kierowane do narzędziowego Hermesa. Mogą być badane jako modele odpowiedzi tekstowych lub osobnego review, natomiast ich zgodności z protokołem agenta narzędziowego nie potwierdzono. Sam fakt, że model zwróci tekst albo proces CLI zakończy się kodem 0, nie wystarcza.

Preferowany recenzent Kilo jest modelem NIM, ale fallback wraca do aliasu producenta `auto/coding:free`; nie egzekwuje to założenia „mocniejszy sprawdza słabszego”. W T59 minimalny tier `review=3` jest niższy niż `code_draft=4`, więc sama nazwa funkcji `review_by_strong_model` też nie stanowi gwarancji silniejszego recenzenta.

### Budżety i niezawodność nie wynikają z profilu modelu

Zmierzony przykład T59: Lightning zakończył `length`, zużył **4096 completion/reasoning tokens** i zwrócił content_chars=0. Przydział 4096 tokenów był niewystarczający dla tej produkcji. Kolejna wersja T59 ma budżet producenta 8192, ale nie została jeszcze odebrana rzeczywistym przebiegiem po tej zmianie.

Kilo zwiększyło ogólny timeout do 600 s i dodało retry, lecz to nie zastępuje osobnych limitów dla planowania, drobnej ekstrakcji, kodu i review, ani wspólnego rachunku rzeczywistych prób. Jego aktywne daemony nie używają ledgeru T59. Licznik **72/80** dotyczy ograniczonego pilota T59; nie obejmuje całej aktywności Kilo ani wewnętrznych prób fallbacków bramki.

## Co mówią zachowane odpowiedzi bramki

Okno sześciogodzinne i wybrany aktywny klucz obejmują także próby diagnostyczne. Nie przypisujemy każdego z tych wywołań samemu daemonowi. `gateway_success` oznacza status zapisany przez bramkę, nie poprawność kodu ani niezależną walidację.

| Model / trasa | Requests | Gateway success | Wniosek |
|---|---:|---:|---|
| North Mini Code `:free` | 11 | 9 | sensowny kandydat do badań produkcji kodu; brak gwarancji poprawności artefaktów |
| Nemotron 3.5 Lightning `:free` | 29 | 19 | osobno mierzyć reasoning i końcową treść; znany przypadek 4096 tokenów bez odpowiedzi |
| Mistral Codestral | 18 | 12 | są odpowiedzi 200, ale też 422; HTTP 200 nie potwierdza adekwatnego kodu; darmowość puli wymaga jawnego potwierdzenia |
| DDG GPT-5.6 Luna | 49 | 0 | nie kwalifikuje się obecnie do podstawowej produkcji bez ponownego testu dostępności |
| DDG GPT-5.4 Mini | 12 | 0 | analogicznie; nie ignorować braku tool calling |
| DDG Claude Haiku | 26 | 4 | brak podstaw do traktowania trasy jako niezawodnego wykonawcy |
| Dwie dominujące trasy Cloudflare | 290 | 0 | nie powinny konsumować kolejnych automatycznych prób bez circuit breakera i ponownej kwalifikacji |

Koszt raportowany jest 0 dla części wywołań Kilo, a dla wielu innych jest NULL. **NULL nie jest potwierdzeniem darmowości.** Alias z napisem `free` i sam provider nie zastępują polityki kosztu, limitów konta i kontroli rzeczywistego modelu.

## Rekomendowana kolejność zmian

1. Ujednolicić uruchomiony runtime z odebraną integracją i poprawnie przekazać quota snapshot. Zachować stan i accounting; nie wyzerować indeksu ani zużycia przy przełączeniu. Nie uruchamiać równolegle drugiej, niezależnej implementacji roju na tych samych zadaniach.
2. Utrzymywać pełny rejestr kwalifikowanej darmowej puli: jeden kanoniczny model, aliasy, faktyczna trasa/konto, potwierdzenie kosztu i status `discovered / tested / available / cooldown`. Nie uznawać dodania całego katalogu za kwalifikację.
3. Przed Basal zastosować twarde filtry: prywatność, typ API, code/JSON/tools/vision, rozmiar wejścia, wolny wspólny budżet i rzeczywista dostępność. Z tej puli wybrać krótką listę **nie większą niż 20**; preferowane 4–8 kandydatów na dane zadanie.
4. Osobno kwalifikować role: lokalny Basal do decyzji; modele szybkich krótkich odpowiedzi do klasyfikacji/ekstrakcji; sprawdzone modele kodowe do draftu; niezależny recenzent do review; modele vision i safety tylko do odpowiadających im zadań. Dla Hermesa wymagać rzeczywiście działającego tool calling, a dla DirectPatchWorker kontraktu JSON i przechodzącej niezależnej walidacji.
5. Zmierzyć na stałym małym zbiorze zadań odsetek prawidłowych artefaktów, format JSON/tools, latency p50/p95, tokeny reasoning/output oraz koszt i dostępność. Dopiero wyniki nadają tier/speed i przydziały produkcyjne. Sprawny transport nie jest oceną jakości merytorycznej.

Pełna pula powinna być znana i kwalifikowana. W konkretnym cyklu należy używać podzbioru pasującego do rzeczywistych zadań; nie ma powodu uruchamiać każdego modelu tylko dlatego, że występuje w katalogu.

## Dowody i granice

Artefakty niesekretne: `scratch/selfopt/llm-audit-20261023/{gateway_inventory.json,gateway_configuration_metadata.json,gateway_usage_metadata.json,host_processes.json,kilo_runtime_snapshot.json,audit_summary.json}` w worktree T59. Katalog sprawdzono jednym uwierzytelnionym odczytem, wykorzystując autoryzowany fallback klucza wyłącznie w pamięci. Audyt nie zwiększył licznika wywołań LLM pilota i nie zatrzymywał procesów.

Źródła kodu aktywnej gałęzi: `selfopt_chain/orchestrator.py` (`_run_evolution`, `main`), `evolver.py` (`_lane_model`, `run`), `omniroute.py` (`load_free_catalog`, polityka kosztu). Źródła T59: launcher, router, ledger i receipty producenta. Kontrakt limitu Basal potwierdzono odpowiedzią lokalnego serwera i źródłem zainstalowanego `OllamaBackend`.

Ten odbiór nie jest benchmarkiem 13 modeli ani potwierdzeniem ich pełnej dostępności. Cel stabilnej ewolucji pozostaje aktywny: obecne procesy nie potwierdzają ani poprawnego przydziału wszystkich ról, ani zamkniętego cyklu użytecznego ulepszenia.
