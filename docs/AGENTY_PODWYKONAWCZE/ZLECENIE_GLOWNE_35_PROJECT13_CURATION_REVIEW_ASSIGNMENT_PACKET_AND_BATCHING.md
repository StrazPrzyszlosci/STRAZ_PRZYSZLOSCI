# Zlecenie Glowne 35 Project13 Curation Review Assignment Packet And Batching

## 1. Misja zadania

Zamien placeholder `REVIEW_ASSIGNMENT_PACKET.md` w aktualny, queue-aware packet dla sesji ludzkiego review. Packet ma enumerowac obecne `14` cases `pending_human_approval`, zaproponowac sensowny batching i zostawic jawne miejsca na prawdziwych reviewerow bez wpisywania fikcyjnych osob.

## 2. Wyzszy cel organizacji

Po `31` mechanizm review recording juz istnieje.
To zadanie ma sprawic, ze pierwszy prawdziwy review session da sie zaplanowac i przeprowadzic bez ponownego skladania kontekstu z kilku plikow.

## 3. Read First

- `docs/AGENTY_PODWYKONAWCZE/ODBIOR_PORTFELA_09_ZADAN_29_34_2026-04-28.md`
- `docs/AGENTY_PODWYKONAWCZE/MINI_HANDOFF_ZADANIE_29.md`
- `docs/AGENTY_PODWYKONAWCZE/MINI_HANDOFF_ZADANIE_31.md`
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/curation_review_queue.jsonl`
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/export_gate_packet.json`
- `PROJEKTY/13_baza_czesci_recykling/docs/HUMAN_APPROVAL_LEDGER.md`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-curation-01/REVIEW_ASSIGNMENT_PACKET.md`
- `PROJEKTY/13_baza_czesci_recykling/docs/PILOT_REVIEW_ASSIGNMENT_AND_APPROVAL_PATH.md`

## 4. Write Scope

- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-curation-01/REVIEW_ASSIGNMENT_PACKET.md`
- `PROJEKTY/13_baza_czesci_recykling/docs/HUMAN_APPROVAL_LEDGER.md`
- `PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py`
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/`

## 5. Deliverables

- zaktualizowany `REVIEW_ASSIGNMENT_PACKET.md` z aktualna lista `14` pending cases
- propozycja batchingu albo grupowania cases, zeby maintainer nie rozdzielal ich po jednej sztuce w ciemno
- jawne pola dla `primary` / `backup` reviewerow i trybu review (`per-candidate` albo `per-batch`)
- jesli to pomaga: drobny helper lub stabilny format eksportu listy pending cases
- mini-handoff z tym, jak packet ma byc uzywany przy pierwszej sesji review

## 6. Acceptance Criteria

- packet enumeruje wszystkie obecne `pending_human_approval` z `candidate_id`, `part_number`, `device` i minimalnym kontekstem decyzji
- kolejny maintainer nie musi juz szukac tych cases recznie w `curation_review_queue.jsonl`
- packet nie wpisuje zadnych fikcyjnych reviewerow ani approvali
- flow nadal prowadzi przez `record-review` i `export-gate`, a nie przez reczna edycje JSONL

## 7. Walidacja

- kontrola counts wzgledem `curation_review_queue.jsonl`
- kontrola zgodnosci listy wzgledem `export_gate_packet.json`
- jesli zmieniasz skrypt: `python3 -m py_compile PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py`
- `python3 PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py review-status`
- `git diff --check`

## 8. Blokery

Jesli kolejka review zostanie w miedzyczasie wygenerowana ponownie i counts sie zmienia, zsynchronizuj packet z nowa wersja.
Nie wolno jednak samodzielnie wymyslac tozsamosci reviewerow ani oznaczac review jako wykonane.

## 9. Mini-handoff

Zapisz:

- jak zaktualizowano packet,
- jaki batching albo grouping zaproponowano,
- ile cases jest gotowych do przypisania,
- co nadal musi dopisac prawdziwy maintainer przed review.
