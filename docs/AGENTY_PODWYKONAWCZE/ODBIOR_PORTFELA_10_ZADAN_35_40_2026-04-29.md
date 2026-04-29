# Odbior Portfela 10 Zadan 35 40 2026-04-29

Ten odbior rozdziela dwa stany:

- `HEAD` - stan kanoniczny po ostatnim commicie
- `worktree` - lokalne, jeszcze niecommitowane rozszerzenia widoczne w repo w dniu `2026-04-29`

Jesli oba stany sa sprzeczne, `HEAD` jest prawda kanoniczna.
`worktree` sluzy tu do uczciwej oceny roboczej po weryfikacji zadan `35-40`.

## Werdykty kanoniczne (`HEAD`)

1. `35` - `NIEODEBRANE KANONICZNIE`
   - `HEAD` nie zawiera jeszcze helpera `list-pending`
   - `HEAD` nie zawiera jeszcze `pending_human_approval_list.json`
   - zaktualizowany `REVIEW_ASSIGNMENT_PACKET.md` pozostaje lokalny
2. `36` - `NIEODEBRANE KANONICZNIE`
   - `HEAD` nie zawiera jeszcze `ocr-selector`
   - `HEAD` nie zawiera jeszcze `ocr_deferred_case_packet.json`
   - brak kanonicznego packetu operatorskiego dla pojedynczych OCR cases
3. `37` - `NIEODEBRANE KANONICZNIE`
   - `HEAD` nie zawiera jeszcze `MANUAL_REVIEW_RUBRIC_AND_DECISION_PACKET.md`
   - `HEAD` nie zawiera jeszcze `manual_review_decision_packet.json`
4. `38` - `NIEODEBRANE KANONICZNIE`
   - `HEAD` nie zawiera jeszcze `EXPORT_OPEN_READINESS_PACKET.md`
   - `HEAD` nie zawiera jeszcze `export_release_receipt_TEMPLATE.json`
5. `39` - `NIEODEBRANE KANONICZNIE`
   - `HEAD` nie zawiera jeszcze `CANARY_GO_LIVE_OPERATOR_PACKET.md`
   - w `HEAD` nie ma tez mini-handoffu dla zadania `39`
6. `40` - `NIEODEBRANE KANONICZNIE`
   - `HEAD` nie zawiera jeszcze real-hardware bench packetu, measurement ledgera i mappingu gate
   - `HEAD` nie ma jeszcze metadata packa w stanie `real_hardware_bench_packet_ready`

## Ocena robocza (`worktree`)

1. `35` - `PASS roboczo z korekta`
   - `python3 .../curate_candidates.py list-pending` przechodzi i pokazuje `14` pending cases w `3` batchach
   - `REVIEW_ASSIGNMENT_PACKET.md` enumeruje wszystkie pending cases i jest zsynchronizowany z helperem
   - skorygowano narracje gate: `deferred` pozostaja poza `apply`, ale nadal blokuja `OPEN`
2. `36` - `PASS roboczo`
   - `python3 .../verify_candidates.py ocr-selector` przechodzi
   - packet obejmuje dokladnie `7` cases `ocr_needed` i daje execution surface per-case / per-group
3. `37` - `PASS roboczo`
   - packet rozdziela `candidate-0076` (`BN44-00213A`) od `candidate-0077` (`QHAD01249`)
   - decision packet nie wpisuje fikcyjnych reviewerow ani decyzji
4. `38` - `PASS roboczo z korekta`
   - readiness packet i receipt template sa gotowe
   - skorygowano zgodnosc ze skryptem: `export-gate` jest `BLOCKED` przez `14` pending, `9` deferred i brak human approval
   - `review-status` i `export-gate` teraz mowia to samo
5. `39` - `PASS roboczo z korekta`
   - `CANARY_GO_LIVE_OPERATOR_PACKET.md` uczciwie utrzymuje stan `NO-GO`
   - dodano brakujacy `docs/AGENTY_PODWYKONAWCZE/MINI_HANDOFF_ZADANIE_39.md`
   - `README.md` i readiness packet prowadza teraz rowniez do packetu maintainera
6. `40` - `PASS roboczo z korekta`
   - istnieja `REAL_HARDWARE_BENCH_PACKET.md`, `MEASUREMENT_LEDGER.md`, `OPERATOR_PRE_START_CHECKLIST.md`, `READINESS_GATE_MAPPING.md`
   - pack metadata sa spojne ze stanem `real_hardware_bench_packet_ready`
   - skorygowano `RUNBOOK.md`: jest `20` testow, a bench flow jest na razie manualny, bez nieistniejacego `bench_test_esp_runtime.py`

## Co faktycznie zostalo odblokowane

- curation ma juz nie tylko packet assignment, ale tez spojna logike statusow `review-status` i `export-gate`
- verification ma gotowy tor dla `7` OCR cases i osobny tor dla `2` manual-review cases
- export ma packet `OPEN -> apply -> export -> receipt`, ktory nie udaje gotowosci
- canary ma warstwe maintainera `go / no-go`, a nie tylko pakiet dla wolontariusza
- `esp-runtime` ma operator-ready przejscie z symulacji do realnego hardware

## Najwazniejsze luki po odbiorze

- wszystko powyzej nadal zyje w `worktree`, nie w stanie kanonicznym `HEAD`
- `14` cases `pending_human_approval` nadal czeka na prawdziwych reviewerow
- `7` cases `ocr_needed` i `2` cases `manual_review` nadal blokuja `export-gate`
- canary pozostaje `NO-GO`, bo blokery `C-1..C-5` sa nadal otwarte
- `esp-runtime` nie ma realnego bench testu na fizycznej plytce

## Rekomendacja portfelowa

Nastepny ruch nie powinien produkowac kolejnych packetow dla tych samych blokad.
Powinien:

1. uruchomic pierwsza prawdziwa sesje review dla `14` pending cases,
2. rownolegle zamknac `7` OCR i `2` manual-review deferred cases,
3. dopiero potem wracac do `apply`, canary `GO` albo realnego hardware bench,
4. a jesli brakuje ludzi albo hardware - przerwac tunelowanie `Project 13` i wrocic do wyzszych ruchow dossier/scouting.
