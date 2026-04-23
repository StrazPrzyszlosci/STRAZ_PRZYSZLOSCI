## Pack
- `pack_id`: `pack-project13-curation-01`
- `upstream_verification_pack`: `pack-project13-kaggle-verification-01`
- `downstream_export_pack`: `pack-project13-catalog-export-01`
- `input_verification_report_ref`:

## Run Provenance

- `operator_kind`:
- `branch_name`:
- `source_snapshot`: `autonomous_test/results/test_db_verified.jsonl`
- `verification_report_ref`:
- `curation_timestamp_utc`:

## Outputs

- [ ] `data/devices.jsonl`
- [ ] `data/parts_master.jsonl`
- [ ] `data/device_parts.jsonl`
- [ ] `autonomous_test/reports/curation_decisions.jsonl`
- [ ] `autonomous_test/reports/curation_report.md`

## Curation Summary

- liczba kandydatow z wejsciowego snapshotu:
- liczba kandydatow accepted:
- liczba kandydatow deferred:
- liczba kandydatow rejected:
- z czego confirmed z verification:
- z czego disputed z verification:
- z czego rejected z verification:
- najwazniejsze przypadki wymagajace review:
- nowe donor devices dodane do katalogu:
- nowe canonical parts dodane do katalogu:

## Scope Boundaries

Ten PR dotyczy **tylko curation** (decyzje o przyjeciu do katalogu). Nie zawiera:
- verification (OCR, frame check, disagreement scoring)
- downstream exportu (inventory.csv, seed.sql, mcp_reuse_catalog.json, inventree_import.jsonl)

## Handoff to Export

Po merge tego PR mozna uruchomic pack `pack-project13-catalog-export-01`:

```bash
python3 PROJEKTY/13_baza_czesci_recykling/scripts/build_catalog_artifacts.py export-all
python3 PROJEKTY/13_baza_czesci_recykling/scripts/build_catalog_artifacts.py validate
```

## Known Issues

-

## Integrity Notes

- [ ] curation nie promuje niesprawdzonych kandydatow do katalogu
- [ ] decyzje kuracyjne sa jawne w curation_decisions.jsonl z rationale
- [ ] PR przechodzi przez review przed merge
- [ ] curation nie miesza sie z exportem downstream
- [ ] nie ma duplikatow rekordow w kanonicznym katalogu
- [ ] kazdy zaakceptowany kandydat spelnia kryteria "gotowosci do katalogu" z REVIEW_CHECKLIST.md
