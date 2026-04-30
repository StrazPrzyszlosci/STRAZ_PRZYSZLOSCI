# Portfel 11 Zlecen Dla Podwykonawcow 2026-04-29

Ten portfel powstaje po odbiorze portfela `10`.

Nie sluzy do produkowania kolejnych packetow dla tych samych blockerow.
Ma zamienic gotowe packet-docsy z `35-40` w realne ruchy wykonawcze albo w jawne blocker receipts, jesli brakuje ludzi, kluczy, wolontariusza albo hardware.

## Kolejnosc pracy

Najpierw dawaj zadania z priorytetu `A`, potem `B`, potem `C`.

## Portfel

1. `A` - `ZLECENIE_GLOWNE_41_PROJECT13_CURATION_REAL_REVIEW_SESSION_AND_LEDGER_EXECUTION.md`
   - zaleznosci: wynik `35`, `REVIEW_ASSIGNMENT_PACKET.md`, `HUMAN_APPROVAL_LEDGER.md`, `curation_review_queue.jsonl`
   - odbior: prawdziwe wpisy `record-review` albo jawny blocker receipt bez fikcyjnych reviewerow
2. `A` - `ZLECENIE_GLOWNE_42_PROJECT13_OCR_DEFERRED_REAL_OCR_RUN_AND_RESOLUTION_SYNC.md`
   - zaleznosci: wynik `36`, `OCR_DEFERRED_CASE_SELECTOR_AND_PROMPT_PACKET.md`, `ocr_deferred_case_packet.json`, `verify_candidates.py`
   - odbior: realny OCR run z `GEMINI_API_KEY` albo jawny blocker receipt bez zmiany statusow
3. `A` - `ZLECENIE_GLOWNE_43_PROJECT13_MANUAL_REVIEW_DECISION_RUN_AND_CURATION_SYNC.md`
   - zaleznosci: wynik `37`, `MANUAL_REVIEW_RUBRIC_AND_DECISION_PACKET.md`, `manual_review_decision_packet.json`
   - odbior: prawdziwe decyzje dla `candidate-0076` i `candidate-0077` albo jawny blocker receipt
4. `B` - `ZLECENIE_GLOWNE_44_PROJECT13_EXPORT_GATE_OPEN_APPLY_EXPORT_AND_RELEASE_RECEIPT_EXECUTION.md`
   - zaleznosci: wyniki `41-43`, `EXPORT_OPEN_READINESS_PACKET.md`, `export_release_receipt_TEMPLATE.json`
   - odbior: `apply`, `export-all`, walidacja i release receipt tylko jesli gate jest `OPEN`
5. `C` - `ZLECENIE_GLOWNE_45_PROJECT13_CANARY_GO_LIVE_DECISION_AND_FIRST_VOLUNTEER_RUN_RECEIPT.md`
   - zaleznosci: wynik `39`, `CANARY_GO_LIVE_OPERATOR_PACKET.md`, `CANARY_PILOT_PACKET.md`, `docs/WOLONTARIUSZE_GOTOWE_PRZYDZIALY.md`
   - odbior: decyzja `GO`/`NO-GO` maintainera i, tylko przy `GO`, pierwszy canary receipt
6. `C` - `ZLECENIE_GLOWNE_46_PROJECT13_ESP_RUNTIME_REAL_HARDWARE_BENCH_RUN_AND_GATE_UPDATE.md`
   - zaleznosci: wynik `40`, `REAL_HARDWARE_BENCH_PACKET.md`, `MEASUREMENT_LEDGER.md`, `READINESS_GATE_MAPPING.md`
   - odbior: realny bench run na fizycznej plytce albo blocker receipt bez zmyslonych pomiarow

## Zasada dla glownego agenta

Glowny agent:

- jako stan bazowy przyjmuje `docs/HANDOFF_DLA_NASTEPNEGO_AGENTA_2026-04-29.md`
- odbiera wyniki wzgledem acceptance criteria z plikow zadan
- nie pozwala podwykonawcom wpisywac fikcyjnych reviewerow, approvali, OCR wynikow, canary runow ani pomiarow hardware
- jesli brak zasobow blokuje realny ruch, wymaga krotkiego blocker receipt zamiast kolejnego duzego packetu
- po zakonczeniu portfela przygotowuje odbior `11` i kolejny handoff

Najwyzsza dzwignia jest w `41-43`.
`44` ma sens dopiero po `OPEN`.
`45-46` sa celowo nizej, bo wymagaja realnego wolontariusza albo fizycznej plytki.
