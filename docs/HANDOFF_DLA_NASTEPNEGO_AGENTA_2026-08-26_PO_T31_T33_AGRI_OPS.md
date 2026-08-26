# Handoff dla Następnego Agenta - po T31 T32 T33 - 2026-08-26 (cykl 3)

## Kontekst wejściowy

Przeczytano ostatni handoff: `docs/HANDOFF_DLA_NASTEPNEGO_AGENTA_2026-08-26_PO_T27_T30_AGRI_LOOP.md` (T27–T30 DONE). Priorytety wejściowe: T31 (retencja streamu + renewal approvals, P1), T32 (metryki upraw dla operatora, P2), T33 (versioning polityk uprawy, P3). Operator powtórzył cykl trzeci raz.

## Co zrobiono

### T31 — DONE: Retencja danych + wczesne ostrzeganie o wygasających approvals

- `edge_events_stream.js`: `pruneEdgeEvents(db, {retentionDays, maxPerProvider})` — usuwa wpisy starsze niż N dni oraz nadmiar ponad cap per provider (ROW_NUMBER window function); config z env `EDGE_EVENT_STREAM_RETENTION_DAYS` (default 14) i `EDGE_EVENT_STREAM_MAX_PER_PROVIDER` (default 1000) przez `resolveEdgeEventRetentionConfig()`.
- `sensor_telemetry.js`: `pruneSensorReadings()` — surowe odczyty starsze niż `SENSOR_READINGS_RETENTION_DAYS` (default 90); agregaty dzienne zostają w `automation_metrics`, więc nic nie ginie dla dashboardu.
- Oba prune podpięte w `scheduled()` workera (razem z cron import/verify/curate).
- `human_approval/expiry_report.py` — raport wygasania: WARNING po przekroczeniu progu `--warn-days` (default 30), ERROR + exit 1 dla już wygasłych/revoked; seed obecnie: ok=2. Do podpięcia w cronie/CI (skrypt gotowy, exit-code aware).
- Testy: retencja +2 (edge stream), +1 (telemetry), expiry +5 (`tests/test_expiry_report.py`).

### T32 — DONE: Dashboard metryk upraw (admin-only)

- `cloudflare/src/agri_metrics.js`: `parseTelemetryMetricKey()`, `groupTelemetryMetrics()` (avg/min/max per sensor+day z kluczy T29), `groupAutopilotUsage()` (rozbiór kluczy `policy_id|day` z T27), `computeAgriMetrics(env)` — jeden snapshot JSON.
- Endpoint `GET /v1/agri/metrics` (X-Trust-Editor-Secret, wzorem `/v1/metrics` B4).
- Komendy bota `/agri-metrics` (Discord/Telegram) celowo odłożone do T34 — endpoint jest fundamentem.
- `tests/agri_metrics_test.mjs` — 4 testy.

### T33 — DONE: Versioning polityk uprawy (rotacja sezonowa)

- Migracje D1: `20260826000010..12` — kolumny `active INTEGER DEFAULT 1`, `superseded_by TEXT`, `version INTEGER DEFAULT 1` na `agri_grow_policies`.
- `agri_evaluate.js`: `deactivateAgriPolicy(env, policyId, supersededBy)` (tylko aktywnych; idempotentnie `not_found_or_inactive`), `getActiveAgriPolicy(db, growCellId)` (najnowsza aktywna per komórka), `upsertAgriPolicy(..., {active})` z auto-bumpem `version` przy re-upsecie.
- Endpointy: evaluate przyjmuje teraz **albo** `policy_id`, **albo** `grow_cell_id` (aktywna wersja); `POST /v1/agri/policies/<id>/deactivate` z body `{superseded_by}` (admin-only).
- Budżet dzienny nadal per policy_id — świadomie; rozdzielenie per cell w backlogu ryzyk.
- `tests/agri_evaluate_test.mjs` — nowy test flow v1→deactivate→v2→evaluate-by-active (+mock DB rozbudowany o kolumny versioning).

## Testy wykonane

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
# Ran 318 tests in ~2.2s — OK (było 313, +5 expiry)

# mjs: wszystkie tests/*.mjs
# pass=314 fail=0 (było 307, +7: retencja 2+1, agri_metrics 4, versioning netto 0? -> patrz niżej)
# (agri_evaluate 5->6, edge_events_stream 4->5, sensor_telemetry 4->5, agri_metrics +4)

python3 human_approval/expiry_report.py
# SUMMARY: ok=2 expiring_soon=0 expired=0 invalid=0 ; exit=0
python3 agentic_cells/validate_cell_manifest.py   # OK: 11 manifest(s) valid
node --check cloudflare/src/{worker,agri_metrics}.js  # SYNTAX OK
```

## Status backlogu

| Zadanie | Status | Opis |
|---|---|---|
| T1–T30 | DONE | Patrz handoffy PO_T21_T26 i PO_T27_T30. |
| T31 | DONE (ta tura) | Pruning streamu+odczytów w scheduled; expiry_report.py z exit codes. |
| T32 | DONE (ta tura) | GET /v1/agri/metrics (telemetria dzienne + zużycie autopilota). |
| T33 | DONE (ta tura) | Wersjonowanie polityk: active/superseded_by/version, evaluate po grow_cell_id. |
| T24 | ODOCZONE | Fizyczny operator: checkout CERN S1, hardware S6, pilot półki. |
| T34 | NEXT / P1 | Komendy bota `/agri-metrics` (Discord+Telegram) na bazie computeAgriMetrics. |
| T35 | OPEN / P2 | Budżet autopilota per (policy_id, grow_cell) — instancje tej samej polityki na wielu komórkach. |
| T36 | OPEN / P3 | Rekord harvestu per grow_cell (plon → korelacja z telemetrią = pętla uczenia). |
| API/worker hardening | OPEN | background-rate-limity, floating-ip healthchecks, secret-rotation. |

## Następne zadania

### T34 — PRIORYTET 1: `/agri-metrics` w bocie (Discord+Telegram)

Wzorować się na istniejącym `/metrics` (automation_metrics B4): admin-gate, format PL, limity długości (Discord 2000 / Telegram 4096 — patrz Z68/Z77). Dane gotowe z `computeAgriMetrics`.

### T35 — PRIORYTET 2: Budżet per instancja

Klucz użycia `policy_id|day` → `(policy_id, grow_cell_id)|day`; migracja licznika lub nowa tabela; evaluate musi znać grow_cell przed odczytem budżetu (już zna — auth po grow_cell).

### T36 — PRIORYTET 3: Harvest ledger

Tabela `harvest_records` (grow_cell_id, crop_profile, mass_g, quality_note, harvested_at, provenance) + endpoint staging + agregat `harvest_<cell>_<month>` w automation_metrics. To domyka pętlę uczenia: telemetria (T29) ↔ plon.

## Kierunki rozwoju (po 3 cyklach)

1. **Warstwa agri jest kompletna funkcjonalnie** (czujnik→evaluate→stream→agent→wersje polityk→metryki). Jedyna rzecz, której brakuje do „autonomicznego rolnictwa" to dane rzeczywiste i pętla plonu: T36 + fizyczny pilot (T24). Po T36 można modelować „które pasma dawały najlepszy plon" i sugerować kalibrację polityk (KnowFlow/IoT-WQMS jako referencja progów).
2. **Bot jako panel operatorski**: `/metrics`, `/agri-metrics`, execution-pack commands — Discord/Telegram staje się CLI systemu; warto ujednolicić helper formatujący (jedna biblioteka reply-bloków zamiast trzech ad-hoc).
3. **KiCad**: bez zmian — czeka na operatora (S1). Endpoint ingestion gotowy od T21.
4. **Hermes**: queue dalej staged; pierwsze realne uruchomienie `repo_scout_daily` (najlepiej GH Actions cron) da systemowi cykliczność bez udziału człowieka.
5. **Hardening przed publicznym pilotem**: secret-rotation runbook, healthcheck floating-ip, rate-limity tła — trzy zadania jednego dnia pracy.

## Zasady (konwencja bez zmian)

1. `PO_T<n>_T<m>_<OPIS>.md`, pipeline liniowy, ≤5 wykonanych zadań na turę.
2. Nowa komórka ⇒ manifest + aktualizacje `EXPECTED_CELL_IDS`/`EXPECTED_DIRS` (CI T25 pilnuje).
3. Testy obowiązkowe z liczbami: Python discover (**318**) + `tests/*.mjs` (**314 pass / 0 fail**).
4. High-risk/biologia = actuation gate; bot nigdy nie merge'uje; sekrety tylko env Workera.
5. Nowe endpointy admin-only wymagają X-Trust-Editor-Secret; providera-auth wymaga tokenu.

## Ryzyka

- **Zbiorczy commit z trzech tur (T21–T33) nadal w working tree** — im dłużej leży, tym trudniejszy review; rozważyć commit partiami (agri / worker-webhook / docs).
- Pruning w scheduled działa dopiero po deployu Workera — lokalne testy nie pokrywają realnego D1 (ROW_NUMBER na produkcji zweryfikować przy pierwszym cronie).
- `expiry_report.py` nie jest jeszcze podpięty nigdzie cyklicznie — bez cron/CICD ostrzega tylko ręcznie.
- Budżet autopilota globalny per policy (patrz T35).

## Referencje zewnętrzne

Bez zmian z poprzedniej tury: `KnowFlow/KnowFlow_AWM` + `pkErbynn/IoT-WQMS` (kalibracja progów), `espressif/esp-claw` (edge runtime), `gnarzilla/deadmesh` (LoRa transport), `Crosstalk-Solutions/project-nomad` (offline-first).
