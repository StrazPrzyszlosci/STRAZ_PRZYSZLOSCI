# Zlecenie Glowne 41 Project13 Curation Real Review Session And Ledger Execution

## 1. Misja zadania

Przeprowadz pierwsza realna sesje review dla `14` cases `pending_human_approval`, korzystajac z gotowego `REVIEW_ASSIGNMENT_PACKET.md` i mechanizmu `record-review`.

To zadanie nie polega na dopisaniu kolejnego packetu. Celem jest zapisanie prawdziwych decyzji reviewera albo uczciwe potwierdzenie, ze review nie moglo sie odbyc, bo brak realnych osob.

## 2. Wyzszy cel organizacji

Po `35` wiemy juz, kto i co powinien reviewowac.
Teraz trzeba zamienic przygotowanie w audytowalny ledger decyzji, bez self-approval i bez fikcyjnych reviewerow.

## 3. Read First

- `docs/HANDOFF_DLA_NASTEPNEGO_AGENTA_2026-04-29.md`
- `docs/AGENTY_PODWYKONAWCZE/ODBIOR_PORTFELA_10_ZADAN_35_40_2026-04-29.md`
- `docs/AGENTY_PODWYKONAWCZE/MINI_HANDOFF_ZADANIE_35.md`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-curation-01/REVIEW_ASSIGNMENT_PACKET.md`
- `PROJEKTY/13_baza_czesci_recykling/docs/HUMAN_APPROVAL_LEDGER.md`
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/curation_review_queue.jsonl`
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/export_gate_packet.json`

## 4. Write Scope

- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/curation_review_queue.jsonl`
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/human_review_ledger.jsonl`
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/export_gate_packet.json`
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/review_session_receipt_*.json`
- `docs/AGENTY_PODWYKONAWCZE/MINI_HANDOFF_ZADANIE_41.md`

## 5. Deliverables

- prawdziwe wpisy `record-review` dla przypisanego batcha lub calej listy `14` pending cases
- `review_session_receipt_YYYY-MM-DD.json` z lista rozstrzygnietych kandydatow, reviewerami, decyzjami i komendami walidacyjnymi
- odswiezony `review-status` i `export-gate`
- jesli review nie moglo sie odbyc: blocker receipt z powodem, bez zmieniania statusow
- mini-handoff z decyzjami i pozostala liczba pending/deferred

## 6. Acceptance Criteria

- kazda zmiana statusu pochodzi z komendy `record-review`, nie z recznej edycji JSONL
- kazdy `reviewed_by` jest prawdziwym identyfikatorem reviewera, nie placeholderem
- `human_review_ledger.jsonl` zawiera audytowalny wpis dla kazdej wykonanej decyzji
- `review-status` pokazuje aktualne counts po sesji
- `export-gate` nadal nie udaje `OPEN`, jesli pozostaja pending albo deferred

## 7. Walidacja

- `python3 PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py review-status`
- `python3 PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py export-gate`
- kontrola, ze `human_review_ledger.jsonl` nie zawiera placeholderow
- `git diff --check`

## 8. Blokery

Brak prawdziwego reviewera blokuje wykonanie decyzji.
W takiej sytuacji zapisz tylko blocker receipt i mini-handoff. Nie wpisuj approvali "technicznie", "testowo" ani w imieniu kogos.

## 9. Mini-handoff

Zapisz:

- ktory batch albo ktore candidate_id zostaly rozstrzygniete,
- kto byl reviewerem,
- ile pozostalo `pending_human_approval`,
- ile pozostalo `deferred`,
- jaki jest wynik `export-gate`.
