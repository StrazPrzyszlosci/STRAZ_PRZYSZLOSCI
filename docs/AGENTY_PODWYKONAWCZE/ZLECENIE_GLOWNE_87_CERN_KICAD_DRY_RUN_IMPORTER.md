# ZLECENIE GŁÓWNE 87 - CERN KiCad Library dry-run importer

## Cel

Zbudować audytowalny importer dry-run dla CERN KiCad Library, który nie zapisuje do D1, tylko generuje staging JSONL/CSV i raport jakości.

## Zakres

- Nowy skrypt: `pipelines/import_cern_kicad_library.py`.
- Wejście: lokalny checkout repo CERN albo katalog/archiwum przekazane argumentem CLI.
- Wyjście:
  - `reports/cern_kicad_import_preview_*.md`
  - `results/cern_kicad_components_sample.jsonl`
  - `results/cern_kicad_components_sample.csv`
- Tryb domyślny: sample limit, bez sieci i bez zapisu do produkcyjnej bazy.

## Wymagania jakości

- Zachować provenance: source slug, repo URL, commit SHA jeśli dostępny, raw path, typ artefaktu, licencja, wersja rodziny KiCad.
- Nie nadpisywać `recycled_part_master`.
- Raport musi wskazywać liczbę znalezionych symboli/footprintów, braki metadanych i przykładowych kandydatów do dopasowania.

## Kryteria odbioru

- Skrypt ma `--help` i test dry-run na sztucznym mini-fixture.
- Test jednostkowy nie wymaga pobrania pełnego repo CERN.
- Raport jasno odpowiada, czy potrzebna jest konwersja wersji KiCad przed importem.

## Status

TODO — najwyższy priorytet.
