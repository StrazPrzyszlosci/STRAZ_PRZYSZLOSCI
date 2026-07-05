# Z93 Smoke Importer CERN — Blocker Receipt (2026-07-05)

## Status: BLOCKED — brak lokalnego checkout CERN KiCad Library

## Cel

Uruchomić dry-run importera CERN `pipelines/import_cern_kicad_library.py` na realnym lokalnym checkout repo CERN KiCad Library.

## Co jest zablokowane

- Brak lokalnego klona [CERN KiCad Library](https://gitlab.cern.ch/kicad/libraries/kicad-library) na maszynie deweloperskiej.
- Git checkout pełnej biblioteki CERN waży ~1-2 GB (symbole + footprinty + assets) — nie należy commitować do repo NSIP.
- Bez checkoutu nie można zweryfikować czy parser z Z87 działa na realnych danych, nie tylko na fixture.

## Co jest gotowe (niezablokowane)

- `pipelines/import_cern_kicad_library.py` istnieje — dry-run importer (Z87 partial).
- `results/cern_kicad_components_sample.csv` i `.../sample.jsonl` — próbki z fixture mini.
- `cloudflare/src/schema_migrations.js` — tabele `kicad_library_sources`, `kicad_library_components`, z `source_slug`, `license_spdx`, `kicad_version_family` (Z88).

## Kamienie milowe do odblokowania

1. **Operator/maintener** klonuje CERN repo lokalnie (nie w working copy NSIP):
   ```bash
   git clone --depth 1 https://gitlab.cern.ch/kicad/libraries/kicad-library.git /tmp/cern-kicad-lib
   ```
2. Uruchamia `pipelines/import_cern_kicad_library.py --source-dir /tmp/cern-kicad-lib --limit 200 --dry-run`.
3. Weryfikuje output: `reports/cern_kicad_import_preview_<data>.md`, `results/cern_kicad_components_sample.jsonl`.
4. Wypełnia checklist z `ZLECENIE_GLOWNE_93_CERN_KICAD_REAL_CHECKOUT_SMOKE.md`.

## Rekomendacja

Jeśli operator nie może/nie chce klonować CERN (limit dysku, internet), smoke **powinien być uruchomiony na fixture mini** który już jest w repo. To częściowo spełnia kryteria Z93 — raport z fixture jest lepszy od NIC. Brak realnego checkout = braker w kolumnie "commit SHA" raportu (wartość `unknown — fixture`).

## Powiązania

- `ZLECENIE_GLOWNE_87_CERN_KICAD_DRY_RUN_IMPORTER.md` — importer.
- `ZLECENIE_GLOWNE_88_KICAD_STAGING_MIGRATIONS.md` — migracje staging.
- `ZLECENIE_GLOWNE_93_CERN_KICAD_REAL_CHECKOUT_SMOKE.md` — smoke.
- `pipelines/import_cern_kicad_library.py` — główny skrypt.