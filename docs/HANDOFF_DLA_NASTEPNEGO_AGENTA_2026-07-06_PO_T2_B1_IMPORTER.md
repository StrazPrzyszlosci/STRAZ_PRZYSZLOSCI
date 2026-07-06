# Handoff dla Następnego Agenta - po T2 (B1 scheduled KiCad importer) - 2026-07-06

## Kontekst

Repo NSIP/Straż Przyszłości przygotowuje bazę i interfejsy dla przyszłych autonomicznych automatyzacji: AI + tani/upcyklingowany hardware, boty jako interfejs operacyjny, D1/SQLite jako pamięć/audyt. Zasada nienaruszalna: **AI sugeruje, człowiek zatwierdza zmiany produkcyjne**.

## Odczytane przed pracą

- Ostatnie commity: `bd27366` (B4 metryki), `133a3b4` (handoff S1-S5/T1-T9), wcześniejsze Z87-Z95 i edge-hardening.
- Handoff wejściowy: `docs/HANDOFF_DLA_NASTEPNEGO_AGENTA_2026-07-06_PO_T1_B4_METRYKI.md`.
- Zlecenie priorytetowe: `docs/AGENTY_PODWYKONAWCZE/ZLECENIE_GLOWNE_B1_IMPORTER_AGENT_SCHEDULED.md`.

## ZALECENIE TRWAŁE (cyberbezpieczeństwo programistyczne)

Kontynuować zasady z poprzedniego handoffu:

1. Brak injection przez bash interpolation — payloady przez argv/JSON, nie interpolację shell.
2. Biała-lista kluczy env i brak sekretów w repo.
3. HTTPS-only w prod dla tokenów/API.
4. Sekretne pliki 0600, katalogi 0700.
5. D1/rate-limit fail-open tam, gdzie brak DB nie może odciąć providerów.
6. AI NIGDY `approved`; `reviewed_by=ai` dla approve pozostaje blokowane.
7. `trust_level >= 2` dla `kind=decision`.
8. Tokeny rotowalne, provider_id stały.
9. Testy cyber dla każdego skryptu/modułu z tokenami lub uprawnieniami.

## Co zrobiono w tej turze

### T2 — B1 Importer agent harmonogramowany — DONE (wersja Worker/D1)

Zrealizowano część produkcyjną B1 możliwą w Cloudflare Worker bez uruchamiania procesu Pythona wewnątrz Workera:

1. Dodano `cloudflare/src/scheduled_kicad_importer.js`:
   - `runScheduledKicadImport(env)` jako funkcję cron/scheduled.
   - `parseScheduledKicadComponents(env)` — czyta deterministyczne JSON rows z `KICAD_IMPORT_COMPONENTS_JSON`; brak konfiguracji kończy się bezpiecznym no-op.
   - `ingestKicadComponents(env, rows)` — zapisuje tylko do staging D1: `kicad_library_sources`, `kicad_library_components`, `kicad_library_events`.
   - `computeKicadImportDedupChecksum(row)` — SHA-256 z `source_slug + upstream_commit + symbol_name + footprint_name + mpn`.
   - dedup po `dedup_checksum`; duplikaty są pomijane, ale ingest event nadal audytuje `inserted_count` i `skipped_count`.
   - `import_status='staged'`; brak zapisu do `recycled_part_master` i brak zapisu do `recycled_part_kicad_links`.
2. Dodano `scheduled()` handler w `cloudflare/src/worker.js`:
   - uruchamia `applyMigrations(env.DB)`.
   - wywołuje `runScheduledKicadImport(env)`.
3. Dodano cron trigger w `cloudflare/wrangler.toml`:
   - `17 2 * * *` (co najmniej 1x/dzień, zgodnie z kryterium B1).
4. Rozszerzono migracje D1 w `cloudflare/src/schema_migrations.js`:
   - `import_status` na `kicad_library_components`.
   - `dedup_checksum` + unique index `idx_kicad_components_dedup_checksum`.
   - tabela eventów `kicad_library_events` + indeks `idx_kicad_library_events_kind_created`.
5. Dodano testy:
   - `tests/scheduled_kicad_importer_test.mjs` — checksum stable, dedup, event ingest, cron smoke z JSON, fail-open no DB.
   - `tests/schema_migrations_test.mjs` — asercje migracji B1.

## Ważne ograniczenie architektoniczne

Cloudflare Worker nie może bezpośrednio uruchomić `pipelines/import_cern_kicad_library.py` ani `git fetch` jako procesu systemowego. Dlatego B1 jest zaimplementowane jako **D1 scheduled ingestion surface**: Worker przyjmuje już sparsowane rows (np. z pipeline/CI/operatora/offline agenta Pythona) przez konfigurację/env i zapisuje je harmonogramowo z dedup + event ledger. Następny krok może dodać CI/offline job, który generuje JSON rows z realnego checkoutu CERN i aktualizuje wejście dla Workera albo wywoła endpoint/queue w przyszłym wariancie.

## Testy wykonane

```bash
node --test tests/scheduled_kicad_importer_test.mjs tests/schema_migrations_test.mjs
node --check cloudflare/src/scheduled_kicad_importer.js cloudflare/src/worker.js
node --test tests/*.mjs
python3 -m unittest tests.test_cern_kicad_importer
```

Wynik:

- `tests/*.mjs`: 252 PASS.
- `tests.test_cern_kicad_importer`: 5 PASS.

## Status backlogu po tej turze

### T1/B4 — DONE (poprzedni agent)
Dashboard metryk D1, `GET /v1/metrics`, `/metrics` Discord/Telegram, 252 mjs obecnie przechodzą.

### T2/B1 — DONE (ta tura)
Scheduled importer surface: cron daily, staging writes, dedup checksum, event per ingest, tests.

### T3/B2 — NEXT / PRIORYTET 1
Verifier agent:
- schema-diff, dedup, OCR deferred (`needs_more_data`).
- każde przejście statusu → event.
- deterministyczny, zero AI, zero false-positive.
- NIE pisać do `recycled_part_master`.
- testy mjs z mock D1.
- Zlecenie: `docs/AGENTY_PODWYKONAWCZE/ZLECENIE_GLOWNE_B2_VERIFIER_AGENT_SCHEMA_DEDUP_OCR.md`.

### T4/B3 — PRIORYTET 2
Curator AI normalizacja:
- AI tylko sugeruje KiCad→NSIP jako `suggested` w `recycled_part_kicad_links`.
- AI nigdy `approved`.
- `recycled_part_master` nie nadpisywać.
- test integracyjny curator→maintainer approve.

### T5/B5 — PRIORYTET 3
Bot execution_pack initiator:
- `!execution-pack start <id>` → fork/branch → PR CANARY → reviewer.
- bot nie merge do main, brak write do `recycled_part_master`.

### T6 — Auto-deactivate provider >72h bez heartbeat
Nadal OPEN, po B2/B3/B5 lub jako hardening równoległy.

### T7 — WebSocket events stream
OPEN dla H3, po gate H2.

### T8/T9 — operator/tester
Realny checkout CERN i hardware/proot/BLE pozostają poza agentem bez sprzętu/operatora.

## Pliki kluczowe zmienione

- `cloudflare/src/scheduled_kicad_importer.js` — nowy scheduled importer D1.
- `cloudflare/src/worker.js` — `scheduled()` handler.
- `cloudflare/src/schema_migrations.js` — B1 migration set.
- `cloudflare/wrangler.toml` — daily cron trigger.
- `tests/scheduled_kicad_importer_test.mjs` — testy B1.
- `tests/schema_migrations_test.mjs` — testy migracji B1.

## Commit tej tury

- (ten commit) `feat(importer): T2 B1 scheduled KiCad importer staging dedup`.
