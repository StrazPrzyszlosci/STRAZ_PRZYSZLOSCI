# Zlecenie Glowne 13 Project13 Pilot Review Assignment And Approval

## 1. Misja zadania

Przeloz governance z `REVIEW_ROTATION_GOVERNANCE.md` na operacyjny scaffold pierwszego publicznego pilota `Project 13`: role, assignment template, approval path i wyjatki od rotacji.

## 2. Wyzszy cel organizacji

To zadanie zmniejsza ryzyko, ze governance pozostanie tylko dokumentem, a pierwszy publiczny pilot i tak przejdzie przez niejawny, jednoosobowy review chain.

## 3. Read First

- `docs/HANDOFF_DLA_NASTEPNEGO_AGENTA_2026-04-23.md`
- `docs/REVIEW_ROTATION_GOVERNANCE.md`
- `PROJEKTY/13_baza_czesci_recykling/docs/PUBLIC_VOLUNTEER_RUN_READINESS.md`
- `docs/ENCJE_I_WORKFLOWY_ORGANIZACJI_AGENTOWEJ.md`

## 4. Write Scope

- `PROJEKTY/13_baza_czesci_recykling/docs/`
- `docs/`
- ewentualnie `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-kaggle-enrichment-01/REVIEW_CHECKLIST.md`

## 5. Deliverables

- template przypisania reviewerow dla pierwszego pilota
- jawny approval path dla pierwszego publicznego PR
- doprecyzowanie exception flow, gdy reviewerow jest za malo

## 6. Acceptance Criteria

- da sie nazwac `primary_pack_reviewer`, `backup_reviewer` albo `integrity_reviewer` oraz `approver`
- dokument rozroznia zasady stale od pol `do_uzupelnienia`
- path approval jest czytelny dla maintainera przed pierwszym pilotem

## 7. Walidacja

- kontrola spojnosci z `REVIEW_ROTATION_GOVERNANCE.md`
- kontrola spojnosci z `PUBLIC_VOLUNTEER_RUN_READINESS.md`
- `git diff --check`

## 8. Blokery

Jesli nie ma jeszcze finalnych nazwisk ani loginow, nie zgaduj. Zostaw operacyjny scaffold z polami do wypelnienia przez maintainera.

## 9. Mini-handoff

Zapisz:

- jaki jest gotowy scaffold review/approval,
- co wymaga juz tylko wypelnienia przez maintainera,
- co nadal pozostaje ryzykiem.
