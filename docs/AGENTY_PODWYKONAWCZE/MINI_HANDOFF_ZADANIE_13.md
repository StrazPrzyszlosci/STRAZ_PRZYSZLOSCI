# Mini-Handoff Zadanie 13

## Co zostalo zrobione

Utworzono operacyjny scaffold review/approval dla pierwszego publicznego pilota `Project 13` w pliku:

- `PROJEKTY/13_baza_czesci_recykling/docs/PILOT_REVIEW_ASSIGNMENT_AND_APPROVAL_PATH.md`

Dokument zawiera:

- zasady stale pochodzace z `REVIEW_ROTATION_GOVERNANCE.md`,
- template przypisania reviewerow z 4 rolnymi polami `__DO_UZUPELNIENIA__` (`primary_pack_reviewer`, `backup_reviewer`/`integrity_reviewer`, `approver`, `review_coordinator`),
- jawny approval path z lancuchem `PR -> pack review -> review_ready -> integrity review -> integrity_ready -> Approval(pilot_run) -> merge`,
- exception flow z procedura, template komentarza w PR i granicami (max 2 exceptiony, brak self-approval dla sredniego/wysokiego ryzyka),
- checklist maintainera przed pierwszym pilotem,
- tablice spojnosci z `REVIEW_ROTATION_GOVERNANCE.md` i `PUBLIC_VOLUNTEER_RUN_READINESS.md`,
- otwarte decyzje dla maintainera.

## Jakie pliki zmieniono

- `PROJEKTY/13_baza_czesci_recykling/docs/PILOT_REVIEW_ASSIGNMENT_AND_APPROVAL_PATH.md` (nowy)

## Co zweryfikowano

- spojnosc z `REVIEW_ROTATION_GOVERNANCE.md`: role, reguly, exception flow, Wariant A — zgodne
- spojnosc z `PUBLIC_VOLUNTEER_RUN_READINESS.md`: odniesienia do statusow "CZESCIOWO" w sekcjach 3.1 i 5.2 — scaffold je zamyka
- `git diff --check`: brak bledow whitespace

## Co wymaga tylko wypelnienia przez maintainera

- 4 pola `__DO_UZUPELNIENIA__` w sekcji 2.1 (osoby i loginy GitHub)
- potwierdzenie branch protection na upstream (checklist sekcja 5)
- decyzje z sekcji 7 (scope Approval, limit rotacji, pula reviewerow, kanal na zywo)
- pole `notes` w rekordzie Approval po wydaniu approval

## Co nadal pozostaje ryzykiem

- maintainer moze wypelnic pola, ale pula moze liczyc nadal 1-2 osoby — wtedy exception flow bedzie musial wejsc
- brak kanalu na zywo (Discord/Telegram) — GitHub Issues jako baseline, ale komunikacja awaryjna nadal ma opoznienie
- brak testu uzytecznosci runbooka z osoba spoza projektu (status NIE GOTOWE w PUBLIC_VOLUNTEER_RUN_READINESS.md)
- Approval scope `pilot_run` nie promuje automatycznie do `knowledge_base_promotion` — trzeba osobnego Approval po retro

## Co powinien zrobic kolejny wykonawca

- odebrac ten scaffold wzgledem acceptance criteria z ZLECENIE_GLOWNE_13,
- jesli maintainer wypelnil pola, zaktualizowac PUBLIC_VOLUNTEER_RUN_READINESS.md sekcje 3.1 z "CZESCIOWO" na "GOTOWE",
- domknac kanal komunikacyjny dla pierwszego pilota,
- przeprowadzic test uzytecznosci runbooka.
