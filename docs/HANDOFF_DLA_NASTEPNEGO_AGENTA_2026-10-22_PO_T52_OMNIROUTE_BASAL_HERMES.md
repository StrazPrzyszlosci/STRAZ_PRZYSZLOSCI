# Handoff dla Następnego Agenta — po T52 (OmniRoute + basal-serve + Hermes + samoewolucja repo) — 2026-10-22

## Kontekst wejściowy

Przeczytano: `AGENTS.md`, handoffy PO_T50/PO_T51, claimy (T45–T47 zajęte).
PR #18/#19 zmergowane; PR #20 (T50), #21 (T51) OPEN — T52 rebasowany na
origin/main 6e05e20 i stackowany (PR pokaże T50+T51+T52 do czasu merge).

Kierunki operatora (2026-10-22, poranek/wieczór — seria wiadomości):

1. **Usuń sekcję zrzutki Trash-to-Cash z README** (wykonane; polecenie
   bezpośrednie operatora — usunięte linie 169–181 root README).
2. „Czy rój już działa?" → **TAK**: offline end-to-end (patrz smoke poniżej);
   realne darmowe LLM czekają na uzbrojenie (OmniRoute do instalacji,
   sekrety, SELFOPT_NETWORK=1).
3. Zintegruj **OmniRoute** jako warstwę wykonawczą darmowych LLM
   (basal decyduje CO i JAKIEJ JAKOŚCI, OmniRoute dobiera model;FreeOnly
   bezwzględnie; STRICT_ZERO_COST upstream domyślnie OFF — nasza polityka
   egzekwowana niezależnie).
4. Zintegruj **najnowszy silnik basal** (basal-serve przez SELFOPT_BASAL_URL,
   fallback do rdzenia wbudowanego; log zawsze mówi, który silnik liczył).
5. **Hermes headless** jako gotowe środowisko agenticzne roju
   (REUSE_OSS → ADAPT → SYNTHESIZE → VALIDATE) + **mechanizm bezpieczeństwa,
   żeby zły kod nie wszedł do roju** (SecurityGate + kwarantanna).
6. **OpenClaw** — tryb roju subagentów: basal decyduje wide/deep;
   „szybki gorszy model pisze, potem duży model sprawdza i poprawia".
7. **Repo ma samo ewoluować** — nie „jeden model w Kilo Code rozbudowuje":
   daemon na komputerze operatora zamienia własny backlog w PR-drafty.
8. **Izolacja działania roju na tym komputerze** (sandbox, scrub env,
   safe-mode, kwarantanna).
9. Klasy sprzętu z odzysku: sterowniki ze starych smartfonów, **czujniki
   z zużytych zmywarek/pralek**, płytki ESP (InteliZagroda = zewn. repo
   ODCZYT — wzorce optymalizacji zarządzania zasobami).

Claim: `docs/AGENT_CLAIMS/T52-kilo-omniroute-basal-hermes.md` (in_progress → done).
Branch: `codex/T52-omniroute-basal-hermes-kilo` (rebase na main 6e05e20).

## Co zrobiono — T52

1. **`selfopt_chain/omniroute.py`** — OmniRouteAdapter + FreeOnlyPolicy:
   walidacja aliasu PRZED (`auto*` lub model z free_models.json) i realnego
   modelu PO odpowiedzi (naruszenie = `free_only_violation`, nigdy płatny
   fallback); SELFOPT_NETWORK=1; privacy public only; OpenAI-compatible.
2. **`swarm.py`** — realny basal-serve: przy SELFOPT_BASAL_URL decyzje idą
   POST `/v1/systemone` (tolerancyjny parser answers.*, wersjo-odporny);
   błąd → fallback builtin + `remote_note` w decyzji (audyt mówi prawdę).
3. **`selfopt_chain/hermes_worker.py`** — izolowany headless worker:
   command builder zweryfikowany wobec zainstalowanego hermes CLI
   (`--oneshot --query-file --format stream-json --safe-mode --worktree
   --in DIR --run-budget --max-turns -t`); `scrub_env()` (whitelistka, zero
   sekretów); sandbox `scratch/selfopt/hermes_sandbox/<id>`; produkcja →
   **kwarantanna** `hermes_quarantine/<id>`; **SecurityGate**: wzorce
   zakazane (sekrety AKIA/sk-/PEM/generic, rm -rf /, sudo, pipe-to-shell,
   exfiltracja env, physical_actuation, network w testach, eval/exec) +
   licencje copyleft → review; `inspect_code`/`inspect_tree`.
   Rzeczywisty run tylko przy `SELFOPT_HERMES=1`.
4. **`selfopt_chain/evolver.py` + `evolution_targets.json`** — SAMOEWOLUCJA
   REPO: zadania z (a) parsera sekcji „Następne zadania" handoffów,
   (b) insightów optimization_proposals z cykli, (c) celowników operatora;
   basal decyduje tryb `single|wide|deep` (decide_parallel_mode); wykonanie
   mock-lane (offline) lub Hermes (uzbrojony); artefakty
   `scratch/selfopt/evolution_queue/<id>/PROPOSAL.md` + gate_report.json;
   **auto_applied=false** — merge wyłącznie człowiek przez PR.
5. **`orchestrator.py`**: `--engine omniroute`, `--evolve`,
   `--evolve-max-tasks`, `--subagent-mode auto|single|wide|deep`;
   receipt zyskuje sekcję `evolution` (mode, executor, taski, gate).
6. **Klasy zasobów**: HARDWARE_KINDS += `appliance_sensors`
   (temp/przepływ/ciśnienie/poziom z pralek/zmywarek) i `esp_boards`
   (edge control); capability_map += oba wpisy (refs m.in. PROJEKTY/34 —
   pilot łączności węzłów farm; nazwa pliku zweryfikowana).
7. **README root**: usunięto sekcję zrzutki Trash-to-Cash (polecenie
   operatora; sekcja lines 169–181).
8. **Runbook**: `docs/INTEGRACJA_OMNIROUTE_BASAL_HERMES_OPENCLAW.md`
   (komponenty, uzbrojenie krok po kroku, env, izolacja, FREE-ONLY,
   równoległość subagentów, OpenClaw w roadmapie).

## Weryfikacja (liczby obowiązkowe)

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
# Ran 473 tests — OK  ✅ (T51: 447 + 26 nowych test_selfopt_integrations.py)
node --test tests/*.mjs
# tests 378, pass 378, fail 0  ✅ (JS nietknięty)
python3 agentic_cells/validate_cell_manifest.py    # OK: 12 manifest(s) valid  ✅
# smoke --evolve (offline): basal wybrał tryb single; 4 taski ewolucyjne
# SPARSOWANE Z RZECZYWISTEGO HANDOFFU PO_T51 (T52 baza części, T53 drabina
# autonomii, T54 free-api, T55 consumer spoola) — gate_ok=true, auto_applied=false  ✅
```

## Uruchomienie na komputerze operatora (wykonane)

- Daemon roju uruchomiony offline z `--evolve` (patrz `scratch/selfopt/`,
  kill switch: `touch scratch/selfopt/KILL_SWITCH`).
- Uzbrojenie realnych darmowych LLM: runbook §Uzbrojenie (OmniRoute install
  + STRICT_ZERO_COST + sekrety + SELFOPT_NETWORK=1 + SELFOPT_HERMES=1).

## Następne zadania (propozycje T53+, ≤5 na turę)

1. **T53 atomizacja + kontrakt ProcessAtom** (rekomendacja zewn. operatora):
   minimalne procesy z input/output/deps/costs/verification; biblioteka
   algorytmów + REUSE_LOCAL przed REUSE_OSS (Hermes) przed SYNTHESIZE.
2. **T54 OpenClaw lane**: adapter CLI OpenClaw jako drugi worker headless
   (obok Hermesa) + realny run subagentów wide/deep na OmniRoute.
3. **T55 drabina autonomii polowej** (observe→suggest→act w charter) +
   pierwszy realny run free-api/omniroute (sekrety operatora).
4. **T56 consumer spoola LoRa w moście** (koordynacja z HYC) + żywy inbox
   EDGE→HUB.
5. **T57 metryki ewolucji**: evolution_queue → automation_metrics
   (nowa tabela D1 ⇒ §5.6) + benchmark wariantów A–D (rekomendacja zewn.).

## Ryzyka

- OmniRoute nie jest jeszcze zainstalowany — daemon offline produkuje
  PR-drafty w trybie mock; realne LLM dopiero po uzbrojeniu (runbook).
- STRICT_ZERO_COST upstream OFF — nasz FreeOnlyPolicy jest gwarantem
  (walidacja po odpowiedzi), ale operator powinien też włączyć flagę
  upstream dla drugiej warstwy.
- `--evolve` w mock-lane NIE pisze kodu — zamienia backlog w propozycje;
  pisanie kodu wchodzi z uzbrojonym Hermesem (kwarantanna + gate + PR).
- Stack na PR #20/#21: po ich merge PR #22 pokaże tylko T52.
- InteliZagroda pozostaje zewn. repozytorium-wzorcem (ODCZYT): tick
  OptimizationEngine + routing rekomendatora — kandydaci do adaptacji
  w T53 (procesy minimalne), bez kopiowania kodu.
