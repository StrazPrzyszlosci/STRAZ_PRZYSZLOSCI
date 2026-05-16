# ZLECENIE GŁÓWNE 98 - ecoEDA approved export smoke

## Cel

Po Z91 przygotować smoke test eksportu ecoEDA/NSIP, który bierze wyłącznie linki `approved` i odrzuca przypadki `suggested`, `rejected`, `needs_more_data`.

## Kryteria odbioru

- Fixture zawiera minimum po jednym rekordzie w każdym statusie review.
- Eksport smoke zawiera tylko rekord `approved`.
- Test sprawdza obecność provenance CERN: `source_slug`, `source_url` lub równoważne pola z tabel staging.
- Raport smoke opisuje, że wynik nie oznacza jeszcze realnej walidacji symbolu/footprintu na hardware.

## Status

TODO — zależy od Z91.
