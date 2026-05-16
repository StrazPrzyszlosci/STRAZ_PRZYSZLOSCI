# Odbiór Portfela 25 - Z96 - 2026-05-16

## Zakres odbioru

Wykonano i odebrano Z96: lekki eksport/audit log decyzji KiCad review dla maintainerów.

## Audyt jakości poprzedniego zadania

| ID | Zakres | Status jakości | Uzasadnienie |
|----|--------|----------------|--------------|
| Z91 | ecoEDA/NSIP export z provenance CERN | PASS + FOLLOW-UP | Ponownie uruchomiono `node --check cloudflare/src/kicad_export.js`, `node --test tests/kicad_export_test.mjs`, pełny `node --test tests/*.mjs` oraz `python3 -m unittest tests/test_recycled_parts_catalog.py`. Eksport Z91 nadal filtruje `approved` i nie modyfikuje `inventory.csv`. Follow-up: dodać receipt/hash przy operatorskim release. |

## Wynik odbioru Z96

| ID | Zakres | Status | Uwagi odbioru |
|----|--------|--------|---------------|
| Z96 | KiCad review audit export | PASS | Rozszerzono `cloudflare/src/kicad_export.js` o audit headers, mapowanie wiersza, CSV i odczyt z `kicad_review_events` z dołączonym stanem linku oraz provenance CERN. |

## Co zweryfikowano

- Eksport audytowy czyta z `kicad_review_events` i `recycled_part_kicad_links` oraz dołącza `kicad_library_components` i `kicad_library_sources`.
- Wynik zawiera `master_part_id`, `kicad_component_id`, `previous_status`, `next_status`, `reviewed_by`, `reason`, `event_created_at` oraz provenance źródła KiCad.
- Query filtruje statusy do znanego zestawu KiCad review: `suggested`, `approved`, `rejected`, `needs_more_data`.
- Eksport jest tylko audytem; nie wykonuje UPDATE i nie jest aktem zatwierdzenia.

## Testy odbiorowe

```bash
node --check cloudflare/src/kicad_export.js
node --check tests/kicad_export_test.mjs
node --test tests/kicad_export_test.mjs
node --test tests/discord_kicad_review_actions_test.mjs tests/kicad_review_test.mjs tests/kicad_export_test.mjs tests/schema_migrations_test.mjs
node --test tests/*.mjs
python3 -m unittest tests/test_recycled_parts_catalog.py
```

## Decyzja odbiorowa

Z96 jest odebrane. Najlepszy następny krok to Z97: metryki SLA kolejki KiCad review, a potem Z101/Z102: operator preview eksportu i release receipt z hashem CSV.
