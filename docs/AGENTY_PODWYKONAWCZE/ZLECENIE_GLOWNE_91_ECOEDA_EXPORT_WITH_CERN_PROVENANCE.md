# ZLECENIE GŁÓWNE 91 - Eksport ecoEDA/NSIP z provenance CERN

## Cel

Rozszerzyć eksport kompatybilny z ecoEDA tak, aby zachować dotychczasowe pola i opcjonalnie dodać źródło CERN jako provenance.

## Kryteria odbioru

- Brak regresji istniejącego `ecoEDA_inventory.csv`.
- Nowe pola provenance są opcjonalne i nie łamią obecnych konsumentów.
- Eksport pokazuje licencję i źródło dla rekordów z CERN.

## Status

DONE (2026-07-05) — `cloudflare/src/ecoeda_export.js` + `tests/ecoeda_export_test.mjs` (9 testow PASS).
Eksport tylko dla `review_status='approved'`. Provenance opcjonalne (`include_provenance`), nie laczy obecnego `ecoEDA_inventory.csv` (zwraca string do zapisu przez konsumenta). Format CSV i JSON.
