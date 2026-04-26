# Mini-Handoff Zadanie 25

## Co zostalo zrobione

- Utworzono skrypt pre-flight `PROJEKTY/13_baza_czesci_recykling/scripts/preflight_check.py` — automatyczny check przed pierwszym runem: `.env`, sekrety, pliki projektu, smoke notebooka, format `GITHUB_PAT`
- Utworzono dokument `PROJEKTY/13_baza_czesci_recykling/docs/VOLUNTEER_PREFLIGHT_CHECKLIST.md` — jawna reczna checklist scope `GITHUB_PAT`, quota YouTube/Gemini, runtime Kaggle, zrozumienie
- Zaktualizowano `PROJEKTY/13_baza_czesci_recykling/docs/PUBLIC_VOLUNTEER_RUN_READINESS.md` — dodano sekcje 1.2a Pre-flight check, zaktualizowano "DO POTWIERDZENIA", "DOMKNIETE W TEJ ITERACJI" i zrodla
- Zaktualizowano `PROJEKTY/13_baza_czesci_recykling/README.md` — dodano komende pre-flight, sekcje "Pre-flight check przed pierwszym runem", zaktualizowano "Decyzje wymagajace potwierdzenia operatora"
- Zaktualizowano `docs/WOLONTARIUSZE_GOTOWE_PRZYDZIALY.md` — dodano `VOLUNTEER_PREFLIGHT_CHECKLIST.md` do Czytaj najpierw dla VOL-P13-01 i VOL-P13-02, dodano pre-flight do roli lokalnego agenta
- Zaktualizowano `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-kaggle-enrichment-01/RUNBOOK.md` — dodano Krok 0 Pre-flight check

## Jakie pliki dotknieto

- `PROJEKTY/13_baza_czesci_recykling/scripts/preflight_check.py` (nowy)
- `PROJEKTY/13_baza_czesci_recykling/docs/VOLUNTEER_PREFLIGHT_CHECKLIST.md` (nowy)
- `PROJEKTY/13_baza_czesci_recykling/docs/PUBLIC_VOLUNTEER_RUN_READINESS.md` (edytowany)
- `PROJEKTY/13_baza_czesci_recykling/README.md` (edytowany)
- `docs/WOLONTARIUSZE_GOTOWE_PRZYDZIALY.md` (edytowany)
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-kaggle-enrichment-01/RUNBOOK.md` (edytowany)

## Co zweryfikowano

- Skrypt `preflight_check.py` uruchomiony lokalnie bez sekretow — daje czytelny wynik: 1 FAIL (brak .env), 2 WARN (markery notebooka), 3 MANUAL (scope/quota/remote), 9 PASS, 4 SKIP
- Skrypt konczy sie kodem 1 przy FAIL i 0 bez FAIL — prawidlowe zachowanie
- Spojnosc miedzy README.md, readiness, runbookiem i onboardingiem wolontariusza: pre-flight jest referencjonowany we wszystkich kanonicznych dokumentach
- Skrypt nie udaje, ze quota albo scope da sie sprawdzic automatycznie — te punkty sa oznaczone jako MANUAL

## Ktore punkty readiness to domknelo

- Brak jawnego pre-flight checku dla wolontariusza przed pierwszym realnym notebook runem — DOMKNIETE: skrypt + checklist
- Weryfikacja scope GITHUB_PAT — CZESCIOWO→RECZNA: skrypt sprawdza format, scope trzeba potwierdzic recznie
- Pre-flight check quota YouTube/Gemini — NIE GOTOWE→RECZNA: quota nie da sie sprawdzic offline, ale wolontariusz dostaje jawna instrukcje

## Czego nadal nie da sie potwierdzic bez realnego runu

- Scope `GITHUB_PAT` — skrypt sprawdza format (prefix `ghp_` / `github_pat_`), ale nie moze wywolac API GitHuba zeby potwierdzic uprawnienia. Wolontariusz musi recznie sprawdzic scope na https://github.com/settings/tokens
- Quota YouTube API — brak wiarygodnego sposobu sprawdzenia offline. Wolontariusz musi recznie sprawdzic w Google Cloud Console. Ewentualny blad 403/429 przy runie bedzie pierwszym realnym sygnalem wyczerpania quota
- Quota Gemini API — analogicznie. Limity RPM/TPM na darmowym tierze sa opisane na https://ai.google.dev/pricing, ale rzeczywiste zuzycie trzeba potwierdzic recznie
- Dostepnosc darmowego runtime Kaggle — wymaga zalogowania na konto Kaggle
- Wersje pakietow Python na Kaggle — potwierdza sie dopiero po pierwszym runie
- Test uzytecznosci runbooka i pre-flight checklist z osoba spoza projektu — nadal brak

## Co powinien zrobic kolejny wykonawca

- Przetestowac pre-flight z realnym wolontariuszem: czy checklist jest zrozumiala, czy skrypt daje czytelny wynik
- Jesli scope `GITHUB_PAT` bedzie mogl byc sprawdzony automatycznie (np. przez probe API call), dodac ten check do skryptu
- Jesli quota YouTube/Gemini bedzie mogla byc sprawdzona automatycznie (np. przez endpoint quota API), dodac ten check do skryptu
- Domknac pozostale otwarte punkty readiness: test uzytecznosci runbooka, branch protection, obsadzenie rotacji review
