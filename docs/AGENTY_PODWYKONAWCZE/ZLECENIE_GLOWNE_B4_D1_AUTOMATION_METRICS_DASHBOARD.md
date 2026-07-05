# ZLECENIE GŁÓWNE B4 - Dashboard metryk D1 (H2 roadmapy)

## Cel

Tabela `automation_metrics` + dashboard metryk w D1/SQLite: coverage, false-positive, P50 czas do review, rollback success, liczba zaakceptowanych / sprint. Metryki są read-only dla agentów.

## Zakres

- Migracja D1: `CREATE TABLE IF NOT EXISTS automation_metrics`:
  - `metric_id INTEGER PRIMARY KEY`
  - `metric_key TEXT NOT NULL` (np. `coverage`, `false_positive`, `p50_review_hours`, `rollback_success`, `accepted_per_sprint`)
  - `metric_value REAL NOT NULL`
  - `measured_at TEXT NOT NULL` (ISO)
  - `window TEXT NOT NULL` (np. `daily`, `sprint`)
- Funkcja `compute_automation_metrics(env)` obliczająca 5 metryk minimalnych z `kicad_review_events` + `kicad_library_components`:
  1. **coverage** — % encji z consistent provenance (`source_url` + `license_spdx` + `kicad_version_family` + `upstream_commit` non-empty).
  2. **false_positive** — odrzucone / zatwierdzone zakończone events (`rejected` / `approved`).
  3. **p50_review_hours** — P50 od `suggested` do `approved`/`rejected` (time diff z events).
  4. **rollback_success** — % rollbacków (event `next_status` == poprzedni) bez utraty danych.
  5. **accepted_per_sprint** — liczba `approved` w ostatnim sprincie.
- Endpoint `GET /v1/metrics` zwraca metryki (read-only, uwierzytelniony).
- Bot komendy `!metrics` (Discord/Telegram) zwracają dashboard (read-only).
- Gate: metryki **read-only** dla agentów — mierzone z events, nie nadpisywane.
- Rollback: drop `automation_metrics` table, regen z `kicad_review_events`.
- Metryka: same 5 metryk minimalnych + brak brakujacych kluczy.

## Kryteria odbioru

- Migracja idempotentna (`CREATE TABLE IF NOT EXISTS`, `ALTER TABLE ... ADD COLUMN` z `ensureColumn`).
- `compute_automation_metrics` zwraca 5 metryk (z mock D1 w testach).
- Endpoint `GET /v1/metrics` 200 + JSON.
- Metryki nie write przez agentów (read-only) — komenda `!metrics` tylko GET.
- Testy jednostkowe `tests/*.mjs` dla migracji + compute.

## Blokery

- Brak (metryki zależą od events które już istnieją z Z90).

## Powiązania

- `cloudflare/src/schema_migrations.js` (Z88) — wzorzec migracji.
- `cloudflare/src/kicad_review.js` (Z90) — źródło events.
- `docs/ROADMAPA_AUTONOMICZNEJ_AUTOMATYZACJI_AI.md` (Z95) — metryki minimalne w H2.

## Status

OPEN (2026-07-05) — utworzone przez agenta jako S5 z `HANDOFF_..._PO_R1_R5_R7_R8.md`. Czeka na realizacje (zalecane pierwszy w kolejności B4→B1→B2→B3→B5).
