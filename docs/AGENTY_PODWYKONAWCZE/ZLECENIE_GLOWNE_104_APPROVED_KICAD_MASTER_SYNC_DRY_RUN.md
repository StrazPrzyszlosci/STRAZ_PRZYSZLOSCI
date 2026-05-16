# ZLECENIE GŁÓWNE 104 - Approved KiCad master sync dry-run

## Cel

Przygotować dry-run synchronizacji pól `kicad_symbol`, `kicad_footprint`, `kicad_reference` do `recycled_part_master` wyłącznie dla linków `approved`, bez wykonywania UPDATE w pierwszym kroku.

## Kryteria odbioru

- Dry-run pokazuje planowane zmiany per `master_part_id` z before/after.
- Pomija rekordy `suggested`, `needs_more_data`, `rejected`.
- Nie wykonuje UPDATE bez osobnej flagi w przyszłym zadaniu.
- Test potwierdza, że rekord z istniejącym konfliktem jest oznaczony jako wymagający ręcznego review.

## Status

TODO — zależy od Z91 i Z96.
