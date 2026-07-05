# ZLECENIE GŁÓWNE B1 - Importer agent harmonogramowany (H2 roadmapy)

## Cel

Przekuć istniejący dry-run importera `pipelines/import_cern_kicad_library.py` (Z87) w produkcyjny agent `importer` harmonogramowany (cron) z dedup przed zapisem do staging D1. Read-only upstream, write tylko do staging tables (Z88), bez nadpisywania `kicad_library_components` bez dedup.

## Zakres

- Harmonogram (cron / Cloudflare Cron Trigger / Agent Manager schedule) co N minut/hours:
  1. Pull nowych artefaktów CERN (git fetch --depth 1) lub lokalny checkout.
  2. Uruchom importer z `--source`, parse do `KicadComponent`.
  3. Dedup checksum: `hash(source_slug + upstream_commit + symbol_name + footprint_name + mpn)`.
  4. Insert tylko nowych rekordów do `kicad_library_components` (status `staged`).
  5. Event per ingest: `INSERT INTO kicad_library_events` (kind `ingest`, source SHA, count).
- Gate: read-only upstream, brak zapisu do `kicad_library_components` bez dedup.
- Rollback: `DROP` staging table + reingest z backup snapshotu (M+1 magazyn).
- Metryka: coverage % encji z consistent provenance (`source_url`, `license_spdx`, `kicad_version_family`, `upstream_commit`).

## Kryteria odbioru

- Cron/schedule picka harmonogramowo (co najmniej 1x/dzień).
- Dedup checksum gwarantuje brak duplikatów (`normalized_part_number` + `upstream_commit`) w `kicad_library_components`.
- Event per ingest zapisany w D1 (audytowalne).
- `recycled_part_master` NIE nadpisany.
- AI importer nie zapisuje bezpośrednio do `recycled_part_kicad_links` (tę robi `curator` z Z90/B3 jako sugestia).

## Blokery

- B4 (`automation_metrics`) zalecane wcześniej — do mierzenia coverage jako health-check.
- Realny checkout CERN dla pełni danych (S1 — operator z dyskiem/internetem). Fixture pozwala na smoke.

## Powiązania

- `pipelines/import_cern_kicad_library.py` (Z87 + S4 rozszerzenia) — bazowy parser.
- `cloudflare/src/schema_migrations.js` (Z88) — staging tables.
- `docs/ROADMAPA_AUTONOMICZNEJ_AUTOMATYZACJI_AI.md` (Z95) — H2 krok B1.
- `docs/KICAD_VERSION_CONVERSION_EXPORT_POLICY.md` (Z92) — importer respektuje policy (nie konwertuje przed ingest).

## Status

OPEN (2026-07-05) — utworzone przez agenta jako S5 z `HANDOFF_..._PO_R1_R5_R7_R8.md`. Czeka na realizacje (zalecane po B4).
