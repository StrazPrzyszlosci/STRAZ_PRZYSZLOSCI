# Zlecenie Glowne 47 Project13 Curation Real Human Review 14 Pending And Ledger Closeout

## 1. Misja zadania

Zamknij `14` cases `pending_human_approval` przez prawdziwe decyzje reviewera zapisane komenda `record-review`.

To nie jest zadanie dokumentacyjne. Jesli nie ma prawdziwego reviewera, zapisz krotki blocker receipt i przerwij.

## 2. Wyzszy cel organizacji

Po zadaniu `42` nie ma juz deferred. Jedyny realny blocker export gate to brak ludzkiego review i brak approvali.

## 3. Read First

- `docs/AGENTY_PODWYKONAWCZE/ODBIOR_PORTFELA_11_ZADAN_41_45_2026-04-30.md`
- `docs/AGENTY_PODWYKONAWCZE/MINI_HANDOFF_ZADANIE_41.md`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-curation-01/REVIEW_ASSIGNMENT_PACKET.md`
- `PROJEKTY/13_baza_czesci_recykling/docs/HUMAN_APPROVAL_LEDGER.md`
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/pending_human_approval_list.json`
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/curation_review_queue.jsonl`

## 4. Write Scope

- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/curation_review_queue.jsonl`
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/human_review_ledger.jsonl`
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/review_session_receipt_*.json`
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/export_gate_packet.json`
- `docs/AGENTY_PODWYKONAWCZE/MINI_HANDOFF_ZADANIE_47.md`

## 5. Deliverables

- `record-review` dla kazdego z `14` pending cases albo blocker receipt `NO_REAL_REVIEWER_AVAILABLE`
- review session receipt z lista candidate_id, decyzja, reviewerem i nota
- odswiezony `review-status`
- odswiezony `export-gate`
- mini-handoff z liczba pozostalych pending i wynikiem gate

## 6. Acceptance Criteria

- kazda decyzja ma prawdziwy `--reviewed-by`
- nie ma decyzji wpisanych recznie do JSONL
- `human_review_ledger.jsonl` istnieje tylko, jesli byly realne decyzje
- `export-gate` nie jest otwierany, jesli zostal jakikolwiek pending
- jesli nie ma reviewera, blocker receipt ma maksymalnie krotka liste: kto potrzebny, czego brakuje, jaki next move

## 7. Walidacja

- `python3 PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py list-pending`
- `python3 PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py review-status`
- `python3 PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py export-gate`
- kontrola `human_review_ledger.jsonl` pod katem placeholderow
- `git diff --check`

## 8. Blokery

Brak prawdziwego reviewera blokuje zadanie. Nie uzywaj `krzysiek`, `maintainer`, `agent` ani placeholdera jako `reviewed_by`, jesli ta osoba realnie nie podjela decyzji.

## 9. Mini-handoff

Zapisz:

- ktore candidate_id rozstrzygnieto,
- kto byl reviewerem,
- ile zostalo `pending_human_approval`,
- czy `human_review_ledger.jsonl` istnieje,
- czy `export-gate` jest `OPEN` czy `BLOCKED`.
