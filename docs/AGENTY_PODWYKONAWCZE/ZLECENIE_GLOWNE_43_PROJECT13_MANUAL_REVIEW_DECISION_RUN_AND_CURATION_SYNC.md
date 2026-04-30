# Zlecenie Glowne 43 Project13 Manual Review Decision Run And Curation Sync

## 1. Misja zadania

Przeprowadz realna decyzje manual review dla `candidate-0076` (`BN44-00213A`) i `candidate-0077` (`QHAD01249`), korzystajac z rubricu z zadania `37`.

To zadanie ma zapisac prawdziwe decyzje czlowieka albo jawnie potwierdzic brak reviewera.

## 2. Wyzszy cel organizacji

Te dwa cases nie zostana uczciwie rozstrzygniete przez OCR ani sama heurystyke.
Potrzebna jest decyzja o scope katalogu i akceptowalnosci wpisow bez klasycznego datasheetu.

## 3. Read First

- `docs/HANDOFF_DLA_NASTEPNEGO_AGENTA_2026-04-29.md`
- `docs/AGENTY_PODWYKONAWCZE/MINI_HANDOFF_ZADANIE_37.md`
- `PROJEKTY/13_baza_czesci_recykling/docs/MANUAL_REVIEW_RUBRIC_AND_DECISION_PACKET.md`
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/manual_review_decision_packet.json`
- `PROJEKTY/13_baza_czesci_recykling/docs/HUMAN_APPROVAL_LEDGER.md`
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/curation_review_queue.jsonl`

## 4. Write Scope

- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/curation_review_queue.jsonl`
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/human_review_ledger.jsonl`
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/manual_review_receipt_*.json`
- `docs/AGENTY_PODWYKONAWCZE/MINI_HANDOFF_ZADANIE_43.md`

## 5. Deliverables

- decyzja `approved`, `rejected` albo `defer` dla `candidate-0076`
- decyzja `approved`, `rejected` albo `defer` dla `candidate-0077`
- uzasadnienie decyzji zapisane w `--note`
- manual review receipt z evidence, reviewerem i wynikiem walidacji
- odswiezony `review-status` i `export-gate`

## 6. Acceptance Criteria

- oba cases sa rozstrzygane osobno
- zadna decyzja nie jest wpisana bez prawdziwego `reviewed_by`
- `record-review` jest jedyna sciezka zmiany statusu
- decyzje odrozniaja board-level entry od custom-transformer entry
- jesli decyzja to `defer`, mini-handoff mowi konkretnie, czego brakuje

## 7. Walidacja

- `python3 PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py review-status`
- `python3 PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py export-gate`
- kontrola `human_review_ledger.jsonl` dla `candidate-0076` i `candidate-0077`
- `git diff --check`

## 8. Blokery

Brak reviewera z prawem podjecia decyzji blokuje to zadanie.
Nie wolno zastapic reviewera agentowa opinia, jesli decyzja ma trafic do ledgera.

## 9. Mini-handoff

Zapisz:

- decyzje dla `BN44-00213A`,
- decyzje dla `QHAD01249`,
- kto reviewowal,
- jakie uzasadnienie wpisano,
- czy oba manual-review blockers sa zamkniete.
