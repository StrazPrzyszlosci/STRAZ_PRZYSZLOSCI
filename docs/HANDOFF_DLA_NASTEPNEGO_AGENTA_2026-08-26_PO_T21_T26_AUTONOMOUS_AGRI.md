# Handoff dla Następnego Agenta - po T21 T22 T23 T25 T26 - 2026-08-26

## Kontekst wejściowy

Przeczytano ostatni handoff: `docs/HANDOFF_DLA_NASTEPNEGO_AGENTA_2026-07-07_PO_T16_T20_NEXT_CELLS.md` (T16–T20 DONE). Ostatni commit przed pracą: `d6d991a` (`feat(cells): T16-T20 human needs, provider quota, hermes queue, approval, sync test`).

Priorytety wejściowe z backlogu T20: T21 (B1 ingestion path, P1), T22 (events stream dla edge H3, P2), T23 (B5 follow-up, P3), T24 (operator — odroczone), T25 (sync-test automation, P5). W trakcie tury operator dodał kierunek strategiczny: **rolnictwo autonomiczne** — zaimplementowany jako T26.

## Co zrobiono

### FIX — wygasłe seed approvals (T19 regres czasowy)

`human_approval/seed_approvals.json`: oba rekordy wygasły 2026-08-06 (test `test_seed_validates` FAIL przy starcie tury). Odnawione do 2026-12-31, `granted_at=2026-08-26`, reason z notą "Renewed". Lekcja: **seedy z expiry wymagają cyklicznego odnawiania — rozważyć T-backlog generator renewali.**

### T21 — DONE: B1 realny upstream ingestion path (JSONL endpoint)

- `cloudflare/src/kicad_jsonl_ingest.js` — kontrakt NDJSON zgodny z wyjściem `pipelines/import_cern_kicad_library.py` (wymagane: `source_slug`, `upstream_commit`, `symbol_name|footprint_name`; limity 5000 linii / 64KB).
- Endpoint `POST /v1/kicad/ingest-jsonl` (worker.js), auth `X-Trust-Editor-Secret`.
- Dedup przez checksumę SHA-256 z T2/B1; audit eventy `kind='ingest'` + `kind='jsonl_ingest'`; **staging only** — zero promocji do katalogu bez verifier/curator/review.
- `tests/kicad_jsonl_ingest_test.mjs` — 5 testów.

### T22 — DONE: Polling-safe events stream dla edge H3

- Migracje D1: `20260826000001-edge-event-stream`, `20260826000002-edge-event-stream-index` (`schema_migrations.js`).
- `cloudflare/src/edge_events_stream.js` — `publishEdgeEvent()`, `listEdgeEventsSince(db, provider_id, since_id, limit)` z kursorem `next_cursor` + `has_more`; kind ∈ {recommendation, alarm, status, notice}, severity ∈ {info, warning, critical}.
- Endpoint `GET /v1/ws/events?provider_id=&since_id=&limit=` (auth tokenem providera). Alternatywa dla WebSocket bez Durable Objects — stateless, retry-safe.
- Integracja: `/v1/recommendations/fish-pond` publikuje rekomendację na stream (fail-open).
- `tests/edge_events_stream_test.mjs` — 4 testy.

### T23 — DONE: B5 follow-up status flow (start → PR → close bez merge)

- `cloudflare/src/execution_pack_initiator.js`: `EXECUTION_PACK_STATUS_TRANSITIONS` (started→closed→merged; merged tylko potwierdzenie merge'a wykonanego przez człowieka), `parseExecutionPackStatusCommand()` (`!execution-pack close <id>` / `!execution-pack merged <id> <reviewer>`), `updateExecutionPackStatus()` (ledger append-only w `execution_packs`), `closeGitHubPr()` (PATCH state=closed, **nigdy PUT /merge**), `ExecutionPackNotFoundError`.
- Komendy bota obsłużone reply-text bez rzucania wyjątków.
- `tests/execution_pack_status_flow_test.mjs` — 7 testów (rollback start→PR→close bez merge zweryfikowany na mock fetch).

### T25 — DONE: Cell manifest sync automation

- `.github/workflows/cell_manifest_sync.yml` — CI na push/PR dotykających komórek: `validate_cell_manifest.py` + `test_cell_manifest_sync.py` + `test_cell_manifest.py`.
- `.githooks/pre-commit` (executable) — ten sam zestaw lokalnie; instalacja: `git config core.hooksPath .githooks`.

### T26 — DONE: agri_autopilot — komórka rolnictwa autonomicznego (kierunek od operatora)

- `agri_autopilot/schema.json` — kontrakt `AgriGrowPolicy`: czujniki, pasma safe/alarm, advisory z `actuation_class` ∈ {advisory_only, edge_auto_within_safe_band, requires_human_approval}, `autopilot_limits.max_auto_actions_per_day`, kill switch.
- `agri_autopilot/validate_policy.py` — walidator blokujący: `physical_actuation` zabroniona (pompa/dozowanie/grzałka/zawory — spójnie z bramkami pack-phone-aquaponics-observer-01), spójność matematyczna pasm, budżet dzienny dla akcji auto, obowiązkowy kill switch + human control point.
- `agri_autopilot/evaluate_readings.py` — deterministyczny ewaluator odczytów → zdarzenia w formacie T22 (provider_id=grow_cell_id). Akcje auto tylko w dziennym budżecie, po wyczerpaniu fallback manualny z reason.
- `agri_autopilot/seed_policy.json` — 2 polityki: akwaponika (zielenina liściasta, grow_cell_id=phone-aquaponics-observer-01) + półka mikro-zieleni (e-waste grow light).
- Manifest `agri_autopilot` dodany do `agentic_cells/seed_cell_manifests.json` (**10 komórek**); `EXPECTED_CELL_IDS` (test_cell_manifest.py) i `EXPECTED_DIRS` (test_cell_manifest_sync.py) zaktualizowane 9→10.
- `tests/test_agri_autopilot.py` — 16 testów.

## Testy wykonane

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
# Ran 303 tests in ~4.5s — OK (było 287, +16 agri_autopilot)

# mjs: każdy plik tests/*.mjs przez node --test
# PASS=292 FAIL=0 (było 276, +16: jsonl 5 + edge_stream 4 + pack_status 7)

python3 human_approval/validate_record.py   # OK (po renewalu)
python3 agentic_cells/validate_cell_manifest.py  # OK: 10 manifest(s) valid
bash .githooks/pre-commit                   # OK (symulacja hooka CI)
python3 agri_autopilot/evaluate_readings.py --policy-id grow_policy_aquaponics_greens_01 --readings '{"ph": 5.3}'
# alarm critical, suggested buffer_dose_ph_up, execution_hint manual_by_operator
```

## Status backlogu

| Zadanie | Status | Opis |
|---|---|---|
| T1–T20 | DONE | Patrz handoff PO_T16_T20. |
| T21 | DONE (ta tura) | B1 JSONL ingestion endpoint + kontrakt + dedup/audit, staging only. |
| T22 | DONE (ta tura) | Edge events stream `/v1/ws/events` polling-safe + publikacja rekomendacji. |
| T23 | DONE (ta tura) | B5 status flow close/merged, PATCH-close PR bez merge, ledger append. |
| T24 | ODOCZONE | Realny checkout CERN S1, hardware S6, proot/BLE — fizyczny operator. |
| T25 | DONE (ta tura) | CI workflow + pre-commit hook dla cell manifest sync. |
| T26 | DONE (ta tura) | agri_autopilot — polityka uprawy, walidator, ewaluator zdarzeń T22. |
| T27 | NEXT / P1 | Agri evaluate endpoint: odczyty → publishEdgeEvent (zamknięcie pętli). |
| T28 | OPEN / P2 | Edge grow-agent (Termux/proot): poll `/v1/ws/events`, tryb advisory-only. |
| T29 | OPEN / P3 | Telemetria upraw: batch JSONL czujników (reuse kontraktu T21). |
| T30 | OPEN / P4 | GitHub webhook statusy execution_packs (auto started/closed/merged sync). |
| API/worker hardening | OPEN | background-rate-limity, floating-ip healthchecks, secret-rotation. |

## Następne zadania (T27+)

### T27 — PRIORYTET 1: Zamknięcie pętli rolniczej (evaluate → events)

Endpoint `POST /v1/agri/evaluate` (auth providera grow_cell): przyjmuje odczyty + policy_id, uruchamia logikę jak `evaluate_readings.py` (port JS lub submoduł), publikuje wynik przez `publishEdgeEvent`. Acceptance: brak aktuatorów, budżet dzienny liczony po stronie serwera (tabela liczników), testy mjs z mock DB.

### T28 — PRIORYTET 2: Grow-agent na węźle edge

Skrypt Termux/proot pollujący `/v1/ws/events?provider_id=<grow_cell_id>` z kursorem; render advisory po polsku w terminalu/powiadomieniu; **zero aktuatorów**, kill switch lokalny. Inspiracja: hermes proot installer.

### T29 — PRIORYTET 3: Telemetria czujników (batch JSONL)

Kontrakt NDJSON odczytów (sensor, value, ts, provenance) → endpoint staging (wzorzec T21) → agregaty dzienne do automation_metrics (B4).

### T30 — PRIORYTET 4: GitHub webhook sync dla execution_packs

Webhook `status` → aktualizacja ledgeru started/closed/merged (bez ręcznych komend); verify signature; rollback test start→close bez merge.

## Kierunki rozwoju (analiza repo, 2026-08-26)

1. **Rolnictwo autonomiczne jako główna pętla wartości** — repo ma już: obserwację (pack-phone-aquaponics-observer-01), model e-waste→żywność (potential_pipeline), zasoby (resource_scout), a od tej tury politykę uprawy + kanał zdarzeń. Brakujące ogniwa: telemetria czujników (T29), agent edge (T28), historyczne dane wzrostu (D1). Docelowo: pętla „czujnik → zdarzenie → advisory → człowiek" działa end-to-end na jednej półce.
2. **Zamknięcie chain KiCad B1→B4** — ingestion jest gotowe (T21); teraz realny checkout CERN (T24/operator) i przepływ staged→verified→curated→reviewed na prawdziwych danych (17k komponentów CERN OHL).
3. **Hermes jako operator cykliczny** — kolejki T18 są staged; pierwsze realne uruchomienie `repo_scout_daily` + `handoff_builder_after_commit` skróci cykl tur agentowych.
4. **Ekonomia modeli** — quota_snapshot nadal stale/blocked; bez uzupełnienia przez operatora chain AI nie startuje. To najszybszy pojedynczy unlock dla całego systemu.
5. **Referencje zewnętrzne do podglądu** (spójne z README/adapters): `KnowFlow/KnowFlow_AWM` i `pkErbynn/IoT-WQMS` (monitoring jakości wody — progi czujników akwaponiki), `espressif/esp-claw` (runtime edge), `Crosstalk-Solutions/project-nomad` (offline-first knowledge), `gnarzilla/deadmesh` (LoRa backhaul dla pól bez internetu).

## Zasady dla następnego agenta (konwencja bez zmian)

1. Handoff: `PO_T<n>_T<m>_<OPIS>.md`; pipeline liniowy T monotonicznie; **jeden handoff = jedna tura = do 5 wykonanych zadań** (odroczone T24 nie liczy się do puli).
2. Każda nowa komórka = manifest w `seed_cell_manifests.json` + aktualizacja `EXPECTED_CELL_IDS`/`EXPECTED_DIRS` (inaczej T25 zablokuje CI).
3. Testy obowiązkowe: Python discover (obecnie 303) + wszystkie `tests/*.mjs` (obecnie 292) — podawać liczby.
4. High-risk (hardware/production/biologia) = mandatory actuation gate; `physical_actuation` niedostępna dla autopilota.
5. Sekrety tylko po stronie env Workera; timing-safe porównania; no_auto_merge/no_direct_push w mocy.

## Ryzyka

- Seed approvals ponownie wygasną **2026-12-31** — dodać zadanie generowania renewali (np. pipeline sprawdzający expiry > 30 dni przed datą).
- `edge_event_stream` bez retencji — przy telemetrii T29 dodać pruningu/cap per provider.
- Publikacja rekomendacji fish-pond do streamu zwiększa write-rate D1 — obserwować limity globalne Z85.
- Zmiany w tym handoffie są **niezacommitowane** (working tree) — najpierw review operatora, potem commit wg konwencji repo.
