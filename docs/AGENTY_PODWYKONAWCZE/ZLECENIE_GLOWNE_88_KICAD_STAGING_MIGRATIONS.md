# ZLECENIE GŁÓWNE 88 - Migracje D1/SQLite dla staging KiCad

## Cel

Dodać migracje schematu dla staging/provenance CERN KiCad Library po zatwierdzeniu raportu dry-run z Z87.

## Docelowe tabele

- `kicad_library_sources`
- `kicad_library_components`
- `recycled_part_kicad_links`

## Indeksy minimalne

- `kicad_library_components(normalized_part_number)`
- `kicad_library_components(mpn)`
- `kicad_library_components(symbol_name)`
- `kicad_library_components(footprint_name)`
- `recycled_part_kicad_links(master_part_id)`
- `recycled_part_kicad_links(review_status)`

## Kryteria odbioru

- Migracje idempotentne.
- Testy lokalnego mock D1/SQLite.
- Brak automatycznego nadpisywania pól ecoEDA/NSIP.

## Status

TODO — zależy od Z87.
