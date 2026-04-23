# Review Checklist Dla Pack Project13 Curation 01

Ten checklist definiuje, co znaczy "gotowe do katalogu" dla kandydatow przechodzacych przez curation.

## Provenance i scope

- [ ] PR wskazuje pack (`pack-project13-curation-01`), wejsciowy verification report i provenance kuracji
- [ ] scope PR nie wychodzi poza curation — nie zawiera verification (OCR, frame check) ani exportu downstream (inventory.csv, seed.sql, mcp.json, inventree.jsonl)
- [ ] handoff point do exportu jest czytelny w opisie PR

## Decyzje kuracyjne

- [ ] `curation_decisions.jsonl` zawiera jawne decyzje accept/defer/reject z rationale dla kazdego kandydata
- [ ] kazdy wpis w `curation_decisions.jsonl` ma `candidate_id`, `decision`, `rationale`, `verification_status` i `provenance`
- [ ] decyzje dla kandydatow spornych (disputed) maja wyjasnienie, dlaczego accept albo defer zamiast reject
- [ ] decyzje dla kandydatow odrzuconych w verification sa rowniez zapisane jako `reject` w audit trail

## Kanoniczny katalog

- [ ] rekordy dodane do `devices.jsonl`, `parts_master.jsonl` i `device_parts.jsonl` sa zgodne z kanonicznymi schematami
- [ ] nie ma duplikatow rekordow w kanonicznym katalogu (sprawdzone po `device_id`, `part_number`)
- [ ] spojnosc relacji cross-file: kazdy `device_id` w `device_parts.jsonl` istnieje w `devices.jsonl`
- [ ] spojnosc relacji cross-file: kazdy `part_number` w `device_parts.jsonl` istnieje w `parts_master.jsonl`

## Co znaczy "gotowe do katalogu"

- [ ] kandydat ma poprawny `part_number` (MPN, nie designator lista ani placeholder)
- [ ] kandydat ma `device_id` powiazany z donor device w `devices.jsonl`
- [ ] kandydat ma uzupelnione kanoniczne pola: `category`, `parameters`, `donor_device`
- [ ] kandydat zostal potwierdzony w verification (`confirmed`) albo ma silny dowod z `disputed` + rationale w curation_decisions
- [ ] kandydat nie dubluje istniejacego rekordu w katalogu

## Bezpieczenstwo i integrity

- [ ] diff nie zawiera sekretow, plikow tymczasowych ani pobranych materialow binarnych
- [ ] pack nie wykonal przy okazji downstream exportu do ecoEDA, InvenTree ani D1
- [ ] reviewer moze odroznic, co jest gotowe do katalogu, a co nadal wymaga dalszej kuracji (defer)
- [ ] audit trail decyzji kuracyjnych jest kompletny i spojny z verification reportem

## Raport kuracyjny

- [ ] `curation_report.md` wyjasnia counts (accepted/deferred/rejected) z podzialam na verification status
- [ ] `curation_report.md` wskazuje najwazniejsze przypadki wymagajace review
- [ ] `curation_report.md` zawiera provenance do verification reportu i wejsciowego snapshotu
