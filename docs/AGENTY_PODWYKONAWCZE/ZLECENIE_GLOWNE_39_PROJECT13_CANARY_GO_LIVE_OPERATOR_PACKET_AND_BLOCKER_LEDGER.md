# Zlecenie Glowne 39 Project13 Canary Go Live Operator Packet And Blocker Ledger

## 1. Misja zadania

Przeloz controlled canary z tasku `32` na operator packet `go / no-go`. Packet ma zebrac w jednym miejscu blokery `C-1..C-5`, evidence linki, wlascicieli i miejsca na statusy, tak zeby maintainer widzial, czy canary naprawde mozna otworzyc, czy tylko "prawie".

## 2. Wyzszy cel organizacji

Po `32` mamy juz dobre materialy dla wolontariusza.
To zadanie ma doprowadzic do rownie dobrego materialu dla maintainera, ktory musi powiedziec: `startujemy` albo `jeszcze nie`.

## 3. Read First

- `docs/AGENTY_PODWYKONAWCZE/ODBIOR_PORTFELA_09_ZADAN_29_34_2026-04-28.md`
- `docs/AGENTY_PODWYKONAWCZE/MINI_HANDOFF_ZADANIE_32.md`
- `docs/WOLONTARIUSZE_GOTOWE_PRZYDZIALY.md`
- `PROJEKTY/13_baza_czesci_recykling/docs/CANARY_PILOT_PACKET.md`
- `PROJEKTY/13_baza_czesci_recykling/docs/CANARY_RETRO_TEMPLATE.md`
- `PROJEKTY/13_baza_czesci_recykling/docs/PUBLIC_VOLUNTEER_RUN_READINESS.md`
- `PROJEKTY/13_baza_czesci_recykling/docs/PILOT_REVIEW_ASSIGNMENT_AND_APPROVAL_PATH.md`
- `PROJEKTY/13_baza_czesci_recykling/docs/BRANCH_PROTECTION_OPERATOR_PACKET.md`

## 4. Write Scope

- `PROJEKTY/13_baza_czesci_recykling/docs/`
- `PROJEKTY/13_baza_czesci_recykling/README.md`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-kaggle-enrichment-01/`
- `docs/WOLONTARIUSZE_GOTOWE_PRZYDZIALY.md`

## 5. Deliverables

- operator packet `go / no-go` dla controlled canary
- blocker ledger z polami: status, owner, evidence, next move
- jawna lista czego jeszcze brakuje przed pierwszym realnym runem
- jesli to pomaga: template decyzji maintainera `otwieramy canary / nie otwieramy`
- mini-handoff z tym, co nadal nie jest potwierdzone bez realnego wolontariusza

## 6. Acceptance Criteria

- maintainer widzi w jednym miejscu, czy `C-1..C-5` sa zamkniete
- packet odroznia przygotowanie organizacyjne od faktycznego odbycia canary
- wolontariacki onboarding nadal startuje z `docs/WOLONTARIUSZE_GOTOWE_PRZYDZIALY.md`, a nie z katalogu podwykonawczego
- dokumenty nie udaja, ze branch protection, live contact i reviewer assignment sa juz realnie domkniete, jesli nadal sa placeholdery

## 7. Walidacja

- kontrola spojnosci miedzy `CANARY_PILOT_PACKET.md`, readiness, onboardingiem i nowym packetem operatora
- kontrola, ze wszystkie nowe pliki sa referencjonowane z kanonicznych dokumentow tam, gdzie trzeba
- `git diff --check`

## 8. Blokery

Brak prawdziwych osob, kontaktu na zywo albo potwierdzonego upstream enforcement nie blokuje przygotowania packetu.
Blokuje dopiero oznaczenie canary jako `go`, jesli te rzeczy nadal nie istnieja.

## 9. Mini-handoff

Zapisz:

- jaki operator packet i blocker ledger dodano,
- ktore blokery sa nadal otwarte,
- co musi wypelnic maintainer przed `go`,
- czego nadal nie da sie potwierdzic bez realnego wolontariusza.
