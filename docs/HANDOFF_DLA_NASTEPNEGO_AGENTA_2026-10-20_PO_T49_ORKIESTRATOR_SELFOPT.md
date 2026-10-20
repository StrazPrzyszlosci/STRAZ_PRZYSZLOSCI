# Handoff dla Następnego Agenta — po T49 (rezydentny agent-orkiestrator) — 2026-10-20

## Kontekst wejściowy

Przeczytano: `AGENTS.md`, claimy (`T43–T47` zajęte: muse-2/muse-4/kilo-robotyka),
handoff `PO_T48_SELFOPT_CHAIN_LORA` oraz nowy kierunek operatora (2026-10-20):

1. „Po uruchomieniu ma chodzić agent orkiestrator, który używa dostępnych
   darmowych zasobów API AI w sposób zautomatyzowany i rozwija procesy w
   kierunku wykorzystywania fizycznych możliwości rozbudowy i produkcji
   opisanych w repo."
2. „Będzie badał i wykorzystywał dostępne np. elektrośmieci do rozbudowy
   swoich możliwości służenia ludziom."

Claim: `docs/AGENT_CLAIMS/T49-kilo-orchestrator.md` (in_progress → done).
Branch: `codex/T49-orchestrator-kilo` — **stack na `codex/T48-selfopt-chain-kilo`
(PR #18 OPEN)**; PR #19 pokaże commity T48+T49 do czasu merge #18, potem sam T49.
Uwaga o numeracji: pierwotna propozycja T49 (consumer spoola w moście LoRa)
wraca do puli jako kandydat na kolejną turę — priorytet operatora był wiążący.

## Co zrobiono — T49

**`selfopt_chain/orchestrator.py`** — rezydentny agent-orkiestrator:

- **Pętla cykli** (`--interval`, `--max-cycles`, `--once`), SIGTERM/SIGINT →
  graceful stop z receiptem; **kill switch** (domyślnie
  `scratch/selfopt/KILL_SWITCH`) sprawdzany przed każdym cyklem.
- **Bramka quota** (tylko `--engine free-api`): import read-only
  `provider_quota_monitor.snapshot.block_decision`; brak snapshotu lub status
  stale/missing → cykl pominięty (`skipped_quota_gate`). Realizuje human
  control point „no_agent_chain_without_ok_snapshot" — **operator uzbraja
  system**, podając quota_snapshot + sekrety w env; wtedy agent działa w pełni
  autonomicznie w budżetach. Tryb mock biega offline bez bramki.
- **Zbiór zadań**: rekordy `resource_scout` (default: przykłady z
  `resource_scout/examples/`), inbox LoRa EDGE→HUB (`--inbox-dir`,
  domknięcie pętli terenowej), **bootstrap_demo** gdy pusto (wbudowana
  próbka; cykle idle są darmowe — zero wywołań AI przy braku zadań).
  Dedup po odcisku rekordu (SHA-1), stan persystowany.
- **Budżety dobowe per model**: widok rejestru z odjętym zużyciem
  (wyczerpane modele wypadają z widoku; pełne wyczerpanie →
  `daily_budget_exhausted`); reset przy zmianie daty; RPM per cykl z ledgera
  run_loop. Router wybiera zamienniki automatycznie.
- **Draft rozbudowy zdolności** per zasób: `scratch/selfopt/procdev_queue/
  <job_id>.md` — łączy dane rekordu, wyniki łańcucha AI (classify → extract →
  draft → review na darmowych modelach przez router T48) i wpis z
  **`selfopt_chain/capability_map.json`** (resource_class → zdolność →
  referencje PROJEKTY/komórki → następny proces). Np.
  `old_smartphones → edge_sensing_and_control → PROJEKTY/06/21/08 →
  edge_flasher (suggest-only) → bench → pack draft → PR`. Każdy draft ma
  `auto_applied: false` i kroki pod bramką człowieka.
- **run_loop.py (dopisek w T48-pliku)**: zapis `final_outputs.json` w katalogu
  runu (orchestrator czyta treści węzłów do draftu) — jedyna zmiana istniejącego
  pliku.
- `.gitignore`: wpis `scratch/selfopt/` (stan daemona nie zaśmieca `git status`
  innych agentów; `scratch/` zawiera trackowane pliki, więc wpis precyzyjny).

## Weryfikacja (liczby obowiązkowe)

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
# Ran 399 tests — OK  ✅ (T48: 378 + 21 nowych test_selfopt_orchestrator.py)
node --test tests/*.mjs
# tests 378, pass 378, fail 0  ✅ (JS nietknięty)
python3 agentic_cells/validate_cell_manifest.py    # OK: 12 manifest(s) valid  ✅ (bez zmian)
python3 selfopt_chain/registry.py                  # OK: 13 darmowych modeli  ✅
# smoke live (offline): orchestrator --once przetwarza oba rekordy resource_scout,
# drafts: edge_sensing_and_control + sovereign_local_inference; kill switch stop z receiptem  ✅
```

## Jak to działa po uruchomieniu (dla operatora)

```bash
# 1) demo offline, jeden cykl:
python3 selfopt_chain/orchestrator.py --once
# 2) daemon na darmowych API (wymaga: sekrety w env + SELFOPT_NETWORK=1
#    + uzupełniony quota_snapshot z provider_quota_monitor):
SELFOPT_NETWORK=1 GEMINI_API_KEY=... GROQ_API_KEY=... \
  python3 selfopt_chain/orchestrator.py --engine free-api --interval 300
# 3) stop: touch scratch/selfopt/KILL_SWITCH (albo SIGTERM)
```

Artefakty ciągłe: `procdev_queue/*.md` (propozycje rozbudowy do review),
`cycles/cycle_<n>.json` (receipty), `orchestrator_state.json` (budżety/dedup),
`runs/` (ślady). Wszystko suggest-only, zero aktuation, zero auto-merge.

## Następne zadania (propozycje T50+, ≤5 na turę)

1. **T50 pierwszy realny run free-api**: operator uzupełnia
   `agent_runtime_plans/hermes_pilot/quota_snapshot.json` (status ok) + sekrety;
   run `--engine free-api --once`; wyniki → `limits_verified=true` w
   `free_models.json` + handoff z realnymi latencjami/ok_rate.
2. **T51 consumer spoola w moście LoRa** (dawne T49 z PR-listy) + żywy
   inbox EDGE→HUB: odpowiedzi z terena jako `field_feedback` w kolejnym cyklu
   orkiestratora (pętla samodoskonalenia na danych z pola).
3. **T52 agregacja metryk**: wpis `selfopt_chain` do `automation_metrics`
   (jobs/cycle, routing mix, ok_rate per provider) — po >0 realnych runów.
4. **T53 rozbudowa capability_map**: klasy z realnych rekordów Łowcy Części
   (kaggle) i kolejnych PROJEKTY (akwakultura, PV); mapa jest danymi, więc
   rozbudowa = edycja JSON bez kodu.

## Ryzyka

- Stack na PR #18: do czasu merge #18 PR #19 zawiera commity obu zadań
  (oczekiwane; po merge #19 pokaże tylko T49). Nic w T49 nie modyfikuje
  plików poza obszarem selfopt_chain (wyjątki: 1 linia .gitignore, dopisek
  final_outputs.json we własnym run_loop.py).
- Budżety RPM/RPD z rejestru to nadal SEEDY — T50 ustawia `limits_verified`.
- `field_feedback` w capability_map jest spinaszem: realny inbox ustawia
  T51; dziś obsługa jest przetestowana testami jednostkowymi.
- Daemon w trybie free-api wykonuje realne wywołania API publicznymi
  danymi — zgodnie z provider_matrix (allowed: read-only/suggest-only),
  ale operator musi świadomie uzbroić system (sekrety + snapshot ok).
