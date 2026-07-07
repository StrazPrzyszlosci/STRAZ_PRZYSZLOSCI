# Handoff dla Następnego Agenta - po T16 T17 T18 T19 T20 - 2026-07-07

## Kontekst wejściowy

Przeczytano ostatni handoff: `docs/HANDOFF_DLA_NASTEPNEGO_AGENTA_2026-07-06_PO_T15_AGENTIC_CELL_MANIFEST.md` (T15 DONE). Ostatnie commity przed pracą:

- `7bae08d` `docs(cells): update T15 handoff convention - up to 5 tasks per turn/handoff`,
- `4b2a7bb` `feat(cells): T15 agentic cell manifest standard`.

Konwencja wejściowa od T15+ (wdrożona w tej turze): **jeden handoff = jedna tura agenta = do 5 zadań naraz**. Nazwa pliku z zakresem zadań (np. `PO_T16_T20`). Pipeline liniowy T<n+1>, brak równoległych serii literowych.

Priorytet wejściowy z backlogu T15 (OPEN): T16 (Human needs intake, P1), T17 (Provider quota monitor = dawniej H2, P2), T18 (Hermes work queue = dawniej H3, P3), plus H4 (Human approval = planowane do wbudowania w T16+) oraz meta-test T20 dla implementacji komórek. Trzy stare zadania H przeniesione do głównej numeracji jako T17/T18/T19.

## Co zrobiono

### T16 — DONE: Human needs intake

Dodano `human_needs/`:

- `human_needs/intake_schema.json` — kontrakt `HumanNeedIntake` (id, submitted_by, visibility_scope, need_or_problem, location_or_area, cost_constraints (max_pln_or_free: free/50pln/200pln/any), energy_constraints (preferred_class + oze_required), origin (chosen_from_recommendation + provenance), expected_outcome).
- `human_needs/validate_records.py` — walidator blokujący: prywatne `contact_note` pod `visibility_scope.level=public`, high-energy bez `oze_required=true`, rekomendację preselekcjonującą `install/actuate/deploy/trigger_production`.
- `human_needs/seed_needs.json` — 2 przykladowe rekordy (akwaponika OZE + offline-first catalog wiedzy).
- `human_needs/README.md`.
- `tests/test_human_needs.py` — 11 testow.

Manifest komórki `human_needs_intake` dodany do `agentic_cells/seed_cell_manifests.json`.

### T17 — DONE: Provider quota monitor cell (dawniej H2)

Dodano `provider_quota_monitor/`:

- `provider_quota_monitor/snapshot.py` — czyta `agent_runtime_plans/hermes_pilot/provider_matrix.json`, generuje `quota_snapshot.json` z polami per provider: provider/model/source/checked_at/status/rpm/tpm/rpd/guaranteed/note. Polityki: NIM 40 RPM `guaranteed=false`, Google AI Studio wymaga notki z `AI Studio` lub `project`, chain blokowany gdy brak snapshotu lub dowolny entry `status != ok`.
- `provider_quota_monitor/README.md`.
- `agent_runtime_plans/hermes_pilot/quota_snapshot.json` — wygenerowany template (wszystkie entries `status=stale`, chain = blocked; operator uzupelnia recznie).
- `tests/test_provider_quota_monitor.py` — 13 testow.

Manifest komórki `provider_quota_monitor` dodany do `agentic_cells/seed_cell_manifests.json`.

### T18 — DONE: Hermes first work queue (dawniej H3)

Dodano `hermes_work_queue/`:

- `hermes_work_queue/queue_schema.json` — kontrakt `HermesWorkQueue`.
- `hermes_work_queue/validate_queue.py` — walidator: 5 konkretnych job_id zamiast dowolnych stringow (`repo_scout_daily`, `handoff_builder_after_commit`, `resource_scout_triage`, `execution_pack_draft_generator`, `audit_reviewer_before_pr`). Kazdy job wymaga `no_auto_merge=true`, `no_direct_push=true`, `next_disabled=true` (staged, nie auto-chained), `model_route.default_profile`.
- `hermes_work_queue/seed_queue.json` — 5 jobow z `model_route=free_public_small_model`, human_control_point per job (maintainer reviews before any merge/PR push).
- `hermes_work_queue/README.md`.
- `tests/test_hermes_work_queue.py` — 12 testow.

Manifest komórki `hermes_work_queue` dodany do `agentic_cells/seed_cell_manifests.json`.

### T19 — DONE: Human approval UI/command stub (dawniej H4)

Dodano `human_approval/`:

- `human_approval/record_schema.json` — kontrakt `HumanApprovalRecord`.
- `human_approval/validate_record.py` — walidator: expiry auto-rejects (timestamp expired), `revoked=true` blokuje, `code_review` nie moze pokryc `install/actuate/production`, `provider_cost_increase` wymaga `cost_ledger_ref`.
- `human_approval/seed_approvals.json` — 2 examples: code review dla T15 (expiry sierpień 2026) + dry_run_only dla hermes queue.
- `human_approval/README.md`.
- `tests/test_human_approval.py` — 10 testow.

Manifest komórki `human_approval` dodany do `agentic_cells/seed_cell_manifests.json`.

### T20 — DONE: Cell manifest sync test

Dodano `tests/test_cell_manifest_sync.py`:

- Weryfikuje, ze kazdy `implementation_ref.directory` w `seed_cell_manifests.json` istnieje jako katalog na dysku.
- Weryfikuje `implementation_ref.entry_artifact` istnieje jako plik.
- Mapuje wszystkie 9 komórek na oczekiwane katalogi (9: edge_flasher, resource_scout, model_resource_selector, potential_pipeline, aquaponics_observer_pack + 4 nowe T16–T19).
- 4 testy.

### Aktualizacja wyniku testów istniejacych

Test `test_seed_describes_all_five_expected_cells` w `tests/test_cell_manifest.py` zaktualizowany z 5 na 9 komórek — seed ma teraz 9 agentic manifestów (5 oryginalnych + 4 nowe).

### Konwencja

- NUMERACJA: T16..T20 monotonicznie rosnąca, NIE relokowane numery T1..T15.
- HANDOFF NAZWA: `PO_T16_T20` z zakresem zadań, zgodnie z nowym stylem (podobnie do starszego `PO_T11_T14_AGENTIC_CELLS`).
- PIPELINE: liniowy (nowy CONTINUE = T21+ po tej turze).
- STARE SERIE H: H2=T17, H3=T18, H4=T19, scalone z główną numeracją. Brak nowych serii literowych.
- KAŻDY NOWY MODUŁ ma manifest w `agentic_cells/seed_cell_manifests.json` z `implementation_ref` wskazującym realną implementację.
- Nie commitowano sekretów, nie użyto `physical_actuation`, nie użyto `auto_merge` ani `direct_push_main`.

## Testy wykonane

```bash
# Nowy suite T16–T20
python3 -m unittest tests.test_human_needs -v
# Ran 11 tests — OK

python3 -m unittest tests.test_provider_quota_monitor -v
# Ran 13 tests — OK

python3 -m unittest tests.test_hermes_work_queue -v
# Ran 12 tests — OK

python3 -m unittest tests.test_human_approval -v
# Ran 10 tests — OK

python3 -m unittest tests.test_cell_manifest_sync -v
# Ran 4 tests — OK

# Cell manifest (T15) adjusted + re-run
python3 -m unittest tests.test_cell_manifest -v
# Ran 15 tests — OK

# Walidatory manualne
python3 agentic_cells/validate_cell_manifest.py
# OK: 9 agentic cell manifest(s) valid

python3 human_needs/validate_records.py
# OK: human needs intake records valid

python3 provider_quota_monitor/snapshot.py
# chain: BLOCKED (stale entries need operator fill)
# ----- OK (snapshot structural valid, chain blocked until operator fills values)

python3 hermes_work_queue/validate_queue.py
# OK: hermes work queue valid

python3 human_approval/validate_record.py
# OK: human approval records valid

# Regresja Python
python3 -m unittest discover -s tests -p 'test_*.py'
# Ran 287 tests in 3.347s — OK

# Regresja mjs (Cloudflare Worker)
for f in tests/*.mjs; do node --test "$f" >/dev/null 2>&1; done
# 276 tests PASS, 0 FAIL
```

## Następne zadania

### T21 — PRIORYTET 1: B1 realny upstream ingestion path

Worker nadal nie uruchamia Pythona/git. Dodać CI/offline job albo endpoint/queue dla JSONL wygenerowanego przez `pipelines/import_cern_kicad_library.py`.

Acceptance criteria per handoffy T6/T7/T8 (zachowane):

- jawny kontrakt pliku/endpointu ingestion,
- test dedup + audit event,
- import nie promuje danych do katalogu bez verifier/curator/review.

Format handoffu: `docs/HANDOFF_DLA_NASTEPNEGO_AGENTA_2026-07-07_PO_T21_B1_INGESTION_PATH.md` (lub _PO_T21_T25_ gdy agentasz zdecyduje się na 5 zadań w turze).

### T22 — PRIORYTET 2: WebSocket events stream dla edge H3

Po stabilizacji T17/T21, dodać `/v1/ws/events?provider_id=<id>` albo alternatywny queue/polling-safe stream dla rekomendacji/alarmów do węzłów edge.

### T23 — PRIORYTET 3: B5 follow-up GitHub App/offline branch flow

Rozwinąć B5 z D1/draft PR surface do pełnego operator-safe flow: offline/CI branch creation, GitHub webhook status updates `started/closed/merged`, rollback test start → PR → close bez merge.

### T24 — PRIORYTET 4: Operator/tester tasks

Realny checkout CERN KiCad (S1), testy hardware (S6), proot/BLE na fizycznym sprzęcie (T8/T9-operator). ODOCZONE — potrzebuje fizycznego operatora/testera.

### T25 — PRIORYTET 5: Model sync test automation

Dodać CI-check albo pre-commit hook, który uruchamia `test_cell_manifest_sync.py` przed każdym commit — żeby implementacja nie rozjechała się z manifestem.

## Status backlogu

| Zadanie | Status | Opis |
|---|---|---|
| T1 / B4 | DONE | Dashboard metryk D1, `/metrics` Discord/Telegram, read-only. |
| T2 / B1 | DONE | Scheduled KiCad importer staging + dedup + ingest events + cron. |
| T3 / B2 | DONE | KiCad verifier schema/dedup/OCR deferred + verify events. |
| T4 / B3 | DONE | KiCad curator suggest-only + normalizacja + Z90 ledger. |
| T5 / B5 | DONE | Bot execution_pack initiator: CANARY branch/PR + reviewer gate. |
| T6 | DONE | Provider lifecycle auto-deactivate >72h. |
| T7 | DONE | Naprawa regresji Telegram/Python + Hermes jako inspiracja referencyjna. |
| T8 | DONE | Interpretacja docelowej automatyzacji + ExecutionPackSkill registry seed. |
| T9 | DONE | Potential Pipeline schema/generator/seed dossiers. |
| T10 | DONE | Edge flasher wizard scaffold 3 profili. |
| T11 | DONE | PotentialDossier → ExecutionPackSkill links (`validate_skill_links.py`). |
| T12 | DONE | Resource scout input format (`resource_scout/`). |
| T13 | DONE | Pierwszy food-loop execution pack `pack-phone-aquaponics-observer-01`. |
| T14 | DONE | Model/resource selector cell (`model_resource_selector/`). |
| T15 | DONE | Agentic cell manifest standard (`agentic_cells/`). |
| T16 | DONE (ta tura) | Human needs intake format + walidator. |
| T17 | DONE (ta tura) | Provider quota monitor cell (dawniej H2). |
| T18 | DONE (ta tura) | Hermes first work queue (dawniej H3). |
| T19 | DONE (ta tura) | Human approval UI/command stub (dawniej H4). |
| T20 | DONE (ta tura) | Cell manifest sync test (9 implementation_refs validated). |
| T21 | NEXT / P1 | B1 ingestion path — realny (CI/offline + test dedup + staging only). |
| T22 | OPEN / P2 | WebSocket events stream dla edge H3. |
| T23 | OPEN / P3 | B5 follow-up GitHub App/offline branch flow. |
| T24 | ODOCZONE (operator/tester) | S1 realny checkout CERN, S6 testy hardware, proot/BLE. |
| T25 | OPEN / P5 | Model sync test automation (CI pre-commit hook lub scheduled). |
| API/worker hardening | OPEN | background-rate-limity, floating-ip healthchecks, secret-rotation. |

## Zasady dla następnego agenta (trzymamy się konwencji)

Następny agent MUSI trzymać się dotychczasowej konwencji. Kluczowe punkty:

1. **Nazewnictwo handoffów**: `PO_T<n>_T<m>_<KRÓTKI OPIS>.md` przy zakresie zadań.
2. **Pipeline liniowy**: T<n> monotonicznie rosnące. NIE relokować istniejących numerów T1..T20.
3. **Jeden handoff = jedna tura = do 5 zadań**. Tura dokumentowana podsumowującym handoffem z zakresem (np. `PO_T21_T25`).
4. **Brak równoległych serii literowych** — wszystkie H są poprzypisywane do głównej numeracji.
5. **Każda nowa komórka MUSI mieć manifest** w `agentic_cells/seed_cell_manifests.json` z `implementation_ref.directory`.
6. **Testy obowiązkowe**: `python3 -m unittest discover -s tests -p 'test_*.py'` i `tests/*.mjs` — PASS z liczbami opisująca całość.
7. **Nie psuj audytowalności**: high-risk (hardware-lab/production) = mandatory actuation gate.
8. **Nie commitować sekretów ani przekraczać zasięgów** (blokady z T2–T6 w mocy).

## Ryzyka

- Nowe komórki T16–T19 mają seed data — jeśli ktoś zmieni implementację (np. zmieni nazwę pliku `snapshot.py` na `monitor.py`) bez aktualizacji `entry_artifact` w `agentic_cells/seed_cell_manifests.json`, `test_cell_manifest_sync.py` łapie rozjazd. To dobrze (catch early), ale wymaga dyscypliny przy refaktorze.
- `issue.py` (scheduled task) — rzadko przeglądany; trzyma starej-konwencje formaty, które mogę być niezgodne z nowymi manifests.