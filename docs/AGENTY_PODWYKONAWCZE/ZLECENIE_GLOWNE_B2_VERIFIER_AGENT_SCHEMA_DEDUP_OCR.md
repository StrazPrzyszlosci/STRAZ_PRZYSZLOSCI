# ZLECENIE GŁÓWNE B2 - Verifier agent deterministyczny (H2 roadmapy)

## Cel

Agent `verifier` — walidacja schema, dedup, OCR deferred dla rekordów w staging. Deterministyczny (bez AI): fail = status `needs_more_data` + event. Nie nadpisuje master.

## Zakres

- Dla każdego rekordu w `kicad_library_components` ze statusem `staged`:
  1. **Schema-diff**: sprawdź istniejące pola (`symbol_name`, `footprint_name`, `mpn`, `license_spdx`) — czy non-empty i zgodne z `schema_version='v1'`.
  2. **Dedup**: sprawdź czy `normalized_part_number` + `upstream_commit` jest unikalny w staging; duplikat → status `duplicate` + event.
  3. **OCR deferred**: jeżeli `datasheet_url` prowadzi do skanu PDF (image), zakolejkuj OCR jako `needs_more_data` (asynchroniczne, później — bez blokowania pętli).
  4. Pass → status `verified` + event `verify_ok`.
- Gate: deterministyczny (żadna AI, zero false-positive). Fail → `needs_more_data` + event, NIE drop (wymaga curatora/humana).
- Rollback: re-verify z backupem (`kicad_library_components` snapshot).
- Metryka: false-positive ratio odrzuconych/zatwierdzonych (cel <30%, powyżej = pauza curatora).

## Kryteria odbioru

- Verifier przetwarza wszystkie `staged` rekordy i ustawia `verified`/`needs_more_data`/`duplicate`.
- Każe przejście statusu zapisane w `kicad_library_events` (kind `verify`).
- OCR deferred dla skanów PDF (status `needs_ocr`, oddzielna kolejka — nie blokuje głównego pętli).
- Verifier NIE pisze do `recycled_part_master` ani `recycled_part_kicad_links`.
- Testy jednostkowe (`tests/*.mjs` lub `tests/*.py`) dla schema-diff, dedup, OCR deferred.

## Blokery

- B1 (importer) zalecane wcześniej — bez ingest brak rekordów `staged` do weryfikacji.
- Z88 (migracje staging) — DONE (potwierdzone).

## Powiązania

- `cloudflare/src/schema_migrations.js` (Z88) — staging tables.
- `pipelines/import_cern_kicad_library.py` (Z87) — parser, dane wejściowe.
- `docs/ROADMAPA_AUTONOMICZNEJ_AUTOMATYZACJI_AI.md` (Z95) — H2 krok B2.

## Status

OPEN (2026-07-05) — utworzone przez agenta jako S5 z `HANDOFF_..._PO_R1_R5_R7_R8.md`. Czeka na realizacje (po B1).
