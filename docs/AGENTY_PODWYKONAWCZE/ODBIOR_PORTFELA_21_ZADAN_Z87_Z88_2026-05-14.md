# Odbiór Portfela 21 - Z87-Z88 - 2026-05-14

## Zakres odbioru

Wykonano pierwszą część Portfela 21: dry-run importer CERN KiCad Library oraz bazowe migracje staging/provenance KiCad.

## Wynik odbioru

| ID | Zakres | Status | Uwagi odbioru |
|----|--------|--------|---------------|
| Z87 | CERN KiCad Library dry-run importer | PASS | Dodano `pipelines/import_cern_kicad_library.py`, parser mini-fixture, CLI `--help`, JSONL/CSV/report output i testy bez pobierania pełnego repo CERN. |
| Z88 | Migracje D1/SQLite dla staging KiCad | PASS | Dodano idempotentne migracje dla `kicad_library_sources`, `kicad_library_components`, `recycled_part_kicad_links` oraz indeksy lookup/review. |

## Co zweryfikowano

- Importer nie zapisuje do D1/SQLite; generuje tylko pliki preview.
- Testy używają sztucznego mini-fixture `.kicad_sym` i `.kicad_mod`, bez sieci i bez pełnej biblioteki CERN.
- Raport importera jawnie utrzymuje decyzję: nie konwertować pełnej biblioteki CERN przed ingestem.
- Migracje mają `IF NOT EXISTS` i przechodzą istniejący framework `applyMigrations()`.

## Testy odbiorowe

```bash
python -m unittest tests.test_cern_kicad_importer -v
python pipelines/import_cern_kicad_library.py --help
node --check cloudflare/src/schema_migrations.js
node --test tests/schema_migrations_test.mjs
```

## Decyzja odbiorowa

Z87 i Z88 są odebrane. Najlepszy następny krok to Z89: wspólna warstwa lookup KiCad dla Discord/Telegram, korzystająca z `recycled_part_master` oraz nowych tabel staging KiCad.
