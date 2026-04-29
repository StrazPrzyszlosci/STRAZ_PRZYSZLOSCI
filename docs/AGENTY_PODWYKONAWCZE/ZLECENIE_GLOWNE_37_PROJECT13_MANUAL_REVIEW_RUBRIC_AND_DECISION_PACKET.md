# Zlecenie Glowne 37 Project13 Manual Review Rubric And Decision Packet

## 1. Misja zadania

Zamien `2` cases `manual_review` z tasku `30` w packet decyzyjny dla czlowieka. Potrzebny jest rubric i packet, ktory rozroznia board-model case `BN44-00213A` od custom-transformer case `QHAD01249`, zbiera evidence i zapisuje, jakie warunki oznaczaja `accept`, `reject` albo `defer`.

## 2. Wyzszy cel organizacji

To zadanie zmniejsza tarcie w jedynym torze, ktorego nie rozwiaze OCR ani sama heurystyka.
Po nim manual review ma byc decyzja operacyjna, a nie ponowne sledztwo zaczynane od zera.

## 3. Read First

- `docs/AGENTY_PODWYKONAWCZE/ODBIOR_PORTFELA_09_ZADAN_29_34_2026-04-28.md`
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/deferred_resolution_workpack.json`
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/deferred_resolution_workpack.md`
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/verification_report.md`
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/verification_triage.jsonl`
- `PROJEKTY/13_baza_czesci_recykling/docs/HUMAN_APPROVAL_LEDGER.md`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-kaggle-verification-01/RUNBOOK.md`

## 4. Write Scope

- `PROJEKTY/13_baza_czesci_recykling/docs/`
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-kaggle-verification-01/`

## 5. Deliverables

- manual review rubric z rozdzieleniem dwoch typow cases
- jawny decision packet dla `BN44-00213A` i `QHAD01249`
- pola lub instrukcja, gdzie zapisac decyzje `accept` / `reject` / `defer`
- jesli to pomaga: evidence snapshot albo prosta tabela porownawcza dla reviewera
- mini-handoff z tym, jakie decyzje nadal musza podjac ludzie

## 6. Acceptance Criteria

- oba cases `manual_review` sa opisane osobno i nie sa wrzucone do jednego worka
- reviewer dostaje jasne kryteria `accept` / `reject` / `defer`
- packet nie udaje, ze decyzje juz zapadly
- kolejny maintainer moze wykonac review bez ponownego biegania po `verification_report`, `triage` i `workpack`

## 7. Walidacja

- kontrola, ze packet obejmuje dokladnie `2` cases `manual_review`
- kontrola zgodnosci `candidate_id`, `part_number` i `evidence_url` z packetem `30`
- `git diff --check`

## 8. Blokery

Brak prawdziwego reviewera nie blokuje przygotowania rubricu i packetu.
Nie wolno jednak wpisywac zadnych decyzji ani reviewerow z glowy.

## 9. Mini-handoff

Zapisz:

- jaki rubric dodano,
- jakie sa roznice miedzy dwoma manual-review cases,
- gdzie maintainer ma zapisac decyzje,
- co nadal jest nierozstrzygniete bez czlowieka.
