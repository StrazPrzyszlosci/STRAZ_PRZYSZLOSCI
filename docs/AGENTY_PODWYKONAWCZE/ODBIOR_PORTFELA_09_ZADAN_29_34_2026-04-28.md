# Odbior Portfela 09 Zadan 29 34 2026-04-28

Ten odbior rozdziela dwa stany:

- `HEAD` - stan kanoniczny po ostatnim commicie
- `worktree` - lokalne, jeszcze niecommitowane rozszerzenia widoczne w repo w dniu `2026-04-28`

Jesli oba stany sa sprzeczne, `HEAD` jest prawda kanoniczna.
`worktree` sluzy tu tylko do uczciwej oceny roboczej i przygotowania kolejnego ruchu.

## Werdykty kanoniczne (`HEAD`)

1. `29` - `PASS`
   - istnieja `curation_review_queue.jsonl` i `export_gate_packet.json`
   - review queue rozdziela `auto_approved`, `pending_human_approval`, `deferred`, `auto_rejected`
   - export gate mowi wprost `BLOCKED` i nie udaje gotowosci exportu
   - `curation_report.md` jest juz zgodny z gate packetem
2. `30` - `PASS z uwaga`
   - istnieja `deferred_resolution_workpack.json` i `deferred_resolution_workpack.md`
   - packet rozdziela `7` cases `ocr_needed` i `2` cases `manual_review`
   - kazdy case ma `candidate_id`, `part_number`, `device`, `evidence_url` i jawny `next_action`
   - uwaga: brak `docs/AGENTY_PODWYKONAWCZE/MINI_HANDOFF_ZADANIE_30.md`, wiec slady podwykonawcze sa slabsze niz w pozostalych zadaniach
3. `31` - `NIEODEBRANE KANONICZNIE`
   - `HEAD` nie zawiera jeszcze `HUMAN_APPROVAL_LEDGER.md`
   - `HEAD` nie zawiera jeszcze placeholder packetu `REVIEW_ASSIGNMENT_PACKET.md`
   - brak kanonicznego potwierdzenia helperow `record-review` i `review-status`
4. `32` - `NIEODEBRANE KANONICZNIE`
   - `HEAD` nie zawiera jeszcze `CANARY_PILOT_PACKET.md`
   - `HEAD` nie zawiera jeszcze `CANARY_RETRO_TEMPLATE.md`
   - wolontariacki tor nadal nie ma kanonicznego packetu controlled canary
5. `33` - `NIEODEBRANE KANONICZNIE`
   - `HEAD` nie zawiera jeszcze smoke test baseline z `2026-04-28`
   - `HEAD` nie zawiera jeszcze nowej walidacji wierszy briefu w stanie kanonicznym
6. `34` - `NIEODEBRANE KANONICZNIE`
   - `HEAD` ma juz output artifacts z simulated precheck
   - ale pack metadata nie sa jeszcze z nimi zrownane: `manifest`, `readiness_gate` i `task` nie sa jeszcze w stanie `simulated_precheck_pass` / `simulated_precheck_complete`

## Ocena robocza (`worktree`)

1. `29` - `PASS roboczo`
   - `export_gate_packet.json` uczciwie pozostaje `BLOCKED`
   - summary jest spojny z kolejka: `14` pending human approval, `9` deferred, `9` auto approved, `50` auto rejected
   - najkrotszy ruch do exportu jest jasno zapisany i nie omija ludzkiego review
2. `30` - `PASS z uwaga roboczo`
   - workpack nadal jest spojny z `7 + 2`
   - packet jest operator-ready, ale nadal nie ma osobnego mini-handoffu dla `30`
3. `31` - `PASS roboczo`
   - istnieja `PROJEKTY/13_baza_czesci_recykling/docs/HUMAN_APPROVAL_LEDGER.md`
   - istnieje `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-curation-01/REVIEW_ASSIGNMENT_PACKET.md`
   - nie istnieje jeszcze `human_review_ledger.jsonl`, co jest poprawne dopoki nie ma prawdziwego review
   - `export_gate_packet.json` nadal mowi `BLOCKED`, wiec zadanie nie wpisuje fikcyjnych approvali
4. `32` - `PASS roboczo`
   - istnieja `CANARY_PILOT_PACKET.md` i `CANARY_RETRO_TEMPLATE.md`
   - readiness, onboarding i runbook sa z nimi skrosowane
   - nadal nie ma realnego canary runu ani wypelnionego retro, co jest uczciwie zapisane
5. `33` - `PASS roboczo`
   - istnieje `INVALID_DESIGN_BRIEF_BAD_ROWS.md`
   - raport `smoke_test_blueprint_design_01_2026-04-28.md` ma `4/4 PASS`
   - sample valid brief nadal przechodzi, a invalid brief pada w przewidywalny sposob
6. `34` - `PASS roboczo`
   - istnieje raport `simulated_precheck_esp_runtime_01_2026-04-28.md`
   - wynik prechecku jest uczciwy: `conditional`, `38 pass`, `3 warn`, `0 fail`
   - lokalne metadata packa sa juz podniesione do stanu `simulated_precheck_pass` / `simulated_precheck_complete`
   - zadanie nadal nie udaje realnego bench testu

## Co faktycznie zostalo odblokowane

- curation ma juz jawny review queue i jawny export gate
- verification ma operator-ready packet dla ostatnich `9` deferred cases
- istnieje uczciwa sciezka review recording bez wymuszania recznej edycji JSONL
- wolontariacki tor ma juz ksztalt `controlled canary`, a nie tylko rozproszone checklisty
- `blueprint` i `esp-runtime` maja mocniejsze execution surface, ale bez udawania realnego `pass`

## Najwazniejsze luki po odbiorze

- `31-34` nie sa jeszcze stanem kanonicznym
- `30` nie ma osobnego mini-handoffu
- `14` kandydatow nadal czeka na prawdziwych reviewerow
- `7` cases `ocr_needed` i `2` cases `manual_review` nadal nie sa zamkniete
- brak realnego canary runu z wolontariuszem
- brak realnego bench testu `esp-runtime` na fizycznej plytce

## Rekomendacja portfelowa

Nastepny portfel nie powinien rozszerzac zakresu dla samego rozszerzania.
Powinien:

1. zamienic placeholder review packet w gotowy packet sesji approval dla `14` pending cases,
2. przygotowac bardziej chirurgiczny surface dla `7` cases `ocr_needed`,
3. przygotowac osobny rubric / decision packet dla `2` cases `manual_review`,
4. przygotowac export-open packet bez udawania, ze gate jest juz otwarty,
5. przygotowac go-live packet dla pierwszego canary,
6. przygotowac real-hardware bench packet dla `esp-runtime`.
