# Odbiór Portfela 24 - Z91 - 2026-05-16

## Zakres odbioru

Wykonano i odebrano Z91: eksport ecoEDA/NSIP z opcjonalną provenance CERN dla linków KiCad po human review.

## Audyt jakości poprzedniego zadania

| ID | Zakres | Status jakości | Uzasadnienie |
|----|--------|----------------|--------------|
| Z94 | Discord KiCad review actions | PASS + FOLLOW-UP | Ponownie uruchomiono `node --check cloudflare/src/discord_api_handler.js`, `node --test tests/discord_kicad_review_actions_test.mjs` oraz pełny `node --test tests/*.mjs`. Warstwa Discord nadal jest cienka nad `kicad_review.js`; dalszy follow-up to połączenie UI z eksportem audit/release, a nie zmiana decyzji review. |

## Wynik odbioru Z91

| ID | Zakres | Status | Uwagi odbioru |
|----|--------|--------|---------------|
| Z91 | ecoEDA/NSIP export z provenance CERN | PASS | Dodano `cloudflare/src/kicad_export.js`, który czyta wyłącznie `review_status = 'approved'`, zachowuje bazowe nagłówki ecoEDA na początku CSV i dopina opcjonalne kolumny provenance CERN/review. |

## Co zweryfikowano

- Bazowy kontrakt ecoEDA pozostaje z przodu CSV: `Component Name,Species,Genus,...`.
- Nowe pola provenance są dopisane jako opcjonalne kolumny, więc istniejący `inventory.csv` nie jest modyfikowany.
- Eksport bierze wyłącznie linki `approved` z `recycled_part_kicad_links`.
- Wiersze eksportu przenoszą źródło, URL, licencję SPDX, commit upstream, rodzinę wersji KiCad oraz dane decyzji review.
- Jeśli `recycled_part_master` nie ma symbolu/footprintu, eksport może użyć zatwierdzonego symbolu/footprintu z komponentu KiCad staging.

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

Z91 jest odebrane. Najlepszy następny krok to Z96/Z97 z Portfela 25: eksport audytowy decyzji i metryki kolejki, a następnie Z101 z Portfela 26: operator command/release receipt dla eksportu approved provenance.
