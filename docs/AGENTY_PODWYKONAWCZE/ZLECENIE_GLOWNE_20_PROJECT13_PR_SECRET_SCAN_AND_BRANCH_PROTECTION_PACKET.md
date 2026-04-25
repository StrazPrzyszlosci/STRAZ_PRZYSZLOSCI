# Zlecenie Glowne 20 Project13 PR Secret Scan And Branch Protection Packet

## 1. Misja zadania

Przygotuj repo-ready baseline dla dwoch pozostalych luk pilota publicznego: wykrywanie sekretow w PR oraz jawna instrukcja operacyjna, jak maintainer ma potwierdzac branch protection przed pierwszym pilotem.

## 2. Wyzszy cel organizacji

To zadanie zmniejsza ryzyko wycieku sekretow i niejawnego obejscia review, bez czekania na kolejne ogolne dokumenty.

## 3. Read First

- `docs/HANDOFF_DLA_NASTEPNEGO_AGENTA_2026-04-24.md`
- `docs/AGENTY_PODWYKONAWCZE/ODBIOR_PORTFELA_06_ZADAN_11_16_2026-04-24.md`
- `PROJEKTY/13_baza_czesci_recykling/docs/PUBLIC_VOLUNTEER_RUN_READINESS.md`
- `PROJEKTY/13_baza_czesci_recykling/docs/PILOT_REVIEW_ASSIGNMENT_AND_APPROVAL_PATH.md`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-kaggle-enrichment-01/REVIEW_CHECKLIST.md`

## 4. Write Scope

- `.github/`
- `PROJEKTY/13_baza_czesci_recykling/docs/`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-kaggle-enrichment-01/REVIEW_CHECKLIST.md`
- ewentualnie `README.md`

## 5. Deliverables

- baseline secret scan dla PR albo jawny pre-PR check script/workflow
- operator packet dla branch protection verification
- aktualizacja readiness po zmianach

## 6. Acceptance Criteria

- istnieje jawny, reviewowalny mechanizm wykrywania sekretow w PR albo przed PR
- maintainer ma krok po kroku packet, jak potwierdzic branch protection
- readiness dokument po zmianach redukuje przynajmniej jedna otwarta pozycje z sekcji pilotowej

## 7. Walidacja

- kontrola spojnosci z `PUBLIC_VOLUNTEER_RUN_READINESS.md`
- kontrola spojnosci z `REVIEW_CHECKLIST.md`
- `git diff --check`

## 8. Blokery

Jesli nie da sie jeszcze wymusic branch protection z poziomu repo, dowiez przynajmniej jawny operator packet i nie udawaj, ze ustawienie po stronie GitHub jest juz wykonane.

## 9. Mini-handoff

Zapisz:

- jaki secret scan albo pre-PR check dodano,
- jak maintainer ma potwierdzac branch protection,
- ktore pozycje readiness zostaly domkniete,
- co nadal wymaga decyzji poza repo.
