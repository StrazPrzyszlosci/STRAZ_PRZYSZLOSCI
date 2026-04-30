# Zlecenie Glowne 48 Project13 Export Gate Open Apply Export Release After Review

## 1. Misja zadania

Jesli zadanie `47` otworzy `export-gate`, wykonaj sekwencje `apply -> validate -> export-all -> validate -> release receipt`.

Jesli gate jest nadal `BLOCKED`, nie uruchamiaj `apply` ani `export-all`.

## 2. Wyzszy cel organizacji

Po `41-45` i korekcie OCR dane sa technicznie czyste, ale eksport publiczny musi poczekac na ludzkie approvale.

## 3. Read First

- `docs/AGENTY_PODWYKONAWCZE/ODBIOR_PORTFELA_11_ZADAN_41_45_2026-04-30.md`
- `docs/AGENTY_PODWYKONAWCZE/ZLECENIE_GLOWNE_47_PROJECT13_CURATION_REAL_HUMAN_REVIEW_14_PENDING_AND_LEDGER_CLOSEOUT.md`
- `PROJEKTY/13_baza_czesci_recykling/docs/EXPORT_OPEN_READINESS_PACKET.md`
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/export_gate_packet.json`
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/export_release_receipt_TEMPLATE.json`

## 4. Write Scope

- `PROJEKTY/13_baza_czesci_recykling/data/`
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/export_release_receipt_*.json`
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/export_blocker_receipt_*.json`
- `docs/AGENTY_PODWYKONAWCZE/MINI_HANDOFF_ZADANIE_48.md`

## 5. Deliverables

- jesli `OPEN`: release receipt z komendami, counts i checksumami/uzasadnieniem brakow
- jesli `BLOCKED`: blocker receipt z aktualnymi gate checks
- mini-handoff z jasna informacja, czy katalog zostal zapisany

## 6. Acceptance Criteria

- `export-gate` musi byc `OPEN` bezposrednio przed `apply`
- `apply` nie jest uruchamiany "na probe"
- po `apply` przechodzi `curate_candidates.py validate`
- po `export-all` przechodzi walidacja downstream
- release receipt odroznia dane wygenerowane od danych zatwierdzonych

## 7. Walidacja

- `python3 PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py export-gate`
- `python3 PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py apply`
- `python3 PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py validate`
- `python3 PROJEKTY/13_baza_czesci_recykling/scripts/build_catalog_artifacts.py export-all`
- `python3 PROJEKTY/13_baza_czesci_recykling/scripts/build_catalog_artifacts.py validate`
- `git diff --check`

## 8. Blokery

`BLOCKED` gate zatrzymuje zadanie. Najbardziej prawdopodobny blocker: nadal brak prawdziwych human approvals po `47`.

## 9. Mini-handoff

Zapisz:

- wynik `export-gate`,
- czy uruchomiono `apply`,
- czy uruchomiono `export-all`,
- sciezke do release albo blocker receipt,
- liste kolejnych blockerow, jesli gate nadal jest `BLOCKED`.
