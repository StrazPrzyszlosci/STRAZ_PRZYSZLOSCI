# Zlecenie Glowne 45 Project13 Canary Go Live Decision And First Volunteer Run Receipt

## 1. Misja zadania

Domknij decyzje maintainera `GO` / `NO-GO` dla controlled canary, korzystajac z `CANARY_GO_LIVE_OPERATOR_PACKET.md`.

Jesli maintainer podpisze `GO` i blokery `C-1..C-5` sa zamkniete, przeprowadz pierwszy canary run z wolontariuszem i zapisz receipt. Jesli nie, zapisz `NO-GO` receipt.

## 2. Wyzszy cel organizacji

Po `39` mamy warstwe decyzyjna dla maintainera.
Teraz trzeba albo bezpiecznie otworzyc pierwszy canary, albo uczciwie powiedziec, co go nadal blokuje.

## 3. Read First

- `docs/HANDOFF_DLA_NASTEPNEGO_AGENTA_2026-04-29.md`
- `docs/AGENTY_PODWYKONAWCZE/MINI_HANDOFF_ZADANIE_39.md`
- `PROJEKTY/13_baza_czesci_recykling/docs/CANARY_GO_LIVE_OPERATOR_PACKET.md`
- `PROJEKTY/13_baza_czesci_recykling/docs/CANARY_PILOT_PACKET.md`
- `PROJEKTY/13_baza_czesci_recykling/docs/CANARY_RETRO_TEMPLATE.md`
- `docs/WOLONTARIUSZE_GOTOWE_PRZYDZIALY.md`
- `PROJEKTY/13_baza_czesci_recykling/docs/PUBLIC_VOLUNTEER_RUN_READINESS.md`

## 4. Write Scope

- `PROJEKTY/13_baza_czesci_recykling/docs/CANARY_GO_LIVE_OPERATOR_PACKET.md`
- `PROJEKTY/13_baza_czesci_recykling/docs/CANARY_RETRO_TEMPLATE.md`
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/canary_go_no_go_receipt_*.json`
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/canary_run_receipt_*.json`
- `docs/AGENTY_PODWYKONAWCZE/MINI_HANDOFF_ZADANIE_45.md`

## 5. Deliverables

- `GO` albo `NO-GO` receipt podpisany przez maintainera
- jesli `GO`: canary run receipt z wolontariuszem, czasem runu, stop conditions i wynikiem
- jesli `NO-GO`: blocker list `C-1..C-5` z ownerem i nastepnym ruchem
- wypelniony albo zaktualizowany retro template po realnym canary
- mini-handoff

## 6. Acceptance Criteria

- canary nie startuje, jesli choc jeden blocker `C-1..C-5` jest `OPEN`
- wolontariusz startuje z `docs/WOLONTARIUSZE_GOTOWE_PRZYDZIALY.md`
- sekrety wolontariusza nie trafiaja do repo ani do receiptu
- receipt odroznia przygotowanie od faktycznego runu
- jesli run zostal przerwany, stop condition jest jawnie zapisana

## 7. Walidacja

- kontrola zgodnosci `CANARY_GO_LIVE_OPERATOR_PACKET.md` z readiness docs
- kontrola, ze `GO` ma wszystkie `C-1..C-5` jako `CLOSED`
- kontrola, ze receipt nie zawiera sekretow
- `git diff --check`

## 8. Blokery

Brak maintainera, brak nazwanych reviewerow, brak branch protection, brak CODEOWNERS loginow albo brak realnego wolontariusza blokuje `GO`.
W takim przypadku zapisz `NO-GO` receipt.

## 9. Mini-handoff

Zapisz:

- decyzje `GO` albo `NO-GO`,
- kto ja podjal,
- status `C-1..C-5`,
- czy canary faktycznie sie odbyl,
- co wynika z retro albo blocker receipt.
