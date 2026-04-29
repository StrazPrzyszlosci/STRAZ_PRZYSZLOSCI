# Mini-Handoff Zadanie 32

## Co zostalo zrobione

1. Utworzono `CANARY_PILOT_PACKET.md` — operacyjny packet pierwszego pilota wolontariackiego:
   - sekwencja przed sesja (10 krokow C-1 do C-10), w trakcie (10 krokow R-1 do R-10), po sesji (7 krokow P-1 do P-7)
   - wolontariusz i maintainer widza te sama sekwencje
   - 5 stop conditions: STOP-QUOTA, STOP-HANG, STOP-DEPS, STOP-SCOPE, STOP-UNCLEAR
   - 3-poziomowa eskalacja: self-stop -> Issue -> maintainer na zywo
   - jawne zaznaczenie, ze packet przygotowuje canary, a nie udaje, ze juz sie odbyl

2. Utworzono `CANARY_RETRO_TEMPLATE.md` — template retro po pierwszym canary runie:
   - 9 sekcji: dane canary, przed sesja, w trakcie, po sesji, tarcie onboardingowe, zaskoczenia, rekomendacje wolontariusza, rekomendacje maintainera, decyzja o otwarciu runu
   - wszystkie pola DO_UZUPELNIENIA — template nie udaje, ze retro juz wykonano
   - sekcja "Co zostalo otwarte" na rzeczy nie do zasymulowania bez realnego wolontariusza

3. Zaktualizowano `PUBLIC_VOLUNTEER_RUN_READINESS.md`:
   - dodano sekcje 1.2b Canary pilot packet z 4 wierszami tabeli
   - dodano 2 nowe ryzyka z mitygacja (STOP-QUOTA, STOP-DEPS)
   - zmieniono "controlled pilot" na "controlled canary pilot" z referencja do packetu
   - dodano 3 pozycje do DOMKNIETE W TEJ ITERACJI
   - dodano canary dokumenty do zrodel

4. Zaktualizowano `PILOT_REVIEW_ASSIGNMENT_AND_APPROVAL_PATH.md`:
   - zmieniono zasade 7 z "controlled pilot" na "controlled canary pilot" z referencja do packetu
   - dodano zasade 8: retro wg CANARY_RETRO_TEMPLATE.md
   - zaktualizowano checklist maintainera: retro odsyla do template

5. Zaktualizowano `WOLONTARIUSZE_GOTOWE_PRZYDZIALY.md`:
   - dodano CANARY_PILOT_PACKET.md do "Czytaj najpierw" dla VOL-P13-01 i VOL-P13-02
   - dodano "pilnowac stop conditions z CANARY_PILOT_PACKET.md" do roli lokalnego agenta dla VOL-P13-01

6. Zaktualizowano `RUNBOOK.md`:
   - dodano sekcje "Canary pilot" z referencja do packetu i retro template

7. Zaktualizowano `README.md` projektu 13:
   - dodano sekcje "Canary pilot" z referencja do packetu i retro template

## Jakie pliki dotknieto

- `PROJEKTY/13_baza_czesci_recykling/docs/CANARY_PILOT_PACKET.md` (nowy)
- `PROJEKTY/13_baza_czesci_recykling/docs/CANARY_RETRO_TEMPLATE.md` (nowy)
- `PROJEKTY/13_baza_czesci_recykling/docs/PUBLIC_VOLUNTEER_RUN_READINESS.md` (edytowany)
- `PROJEKTY/13_baza_czesci_recykling/docs/PILOT_REVIEW_ASSIGNMENT_AND_APPROVAL_PATH.md` (edytowany)
- `docs/WOLONTARIUSZE_GOTOWE_PRZYDZIALY.md` (edytowany)
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-kaggle-enrichment-01/RUNBOOK.md` (edytowany)
- `PROJEKTY/13_baza_czesci_recykling/README.md` (edytowany)

## Co zweryfikowano

- `git diff --check` — brak bledow
- Spojnosc referencji: CANARY_PILOT_PACKET.md jest referencjonowany z 7 plikow, CANARY_RETRO_TEMPLATE.md z 6 plikow
- Zadne pole retro template nie jest wypelnione — template nie udaje, ze retro juz wykonano
- Stop conditions sa spojne z VOLUNTEER_FALLBACK_GUIDE.md i VOLUNTEER_PREFLIGHT_CHECKLIST.md
- Sekwencja canary jest spojna z PILOT_REVIEW_ASSIGNMENT_AND_APPROVAL_PATH.md (checklista maintainera, approval path)
- PUBLIC_VOLUNTEER_RUN_READINESS.md odnotowuje canary jako GOTOWE w sekcji 1.2b i DOMKNIETE W TEJ ITERACJI

## Czego nadal nie potwierdzono bez realnego wolontariusza

1. Test uzytecznosci runbooka — czy wolontariusz rozumie instrukcje bez pomocy
2. Test stop conditions — czy wolontariusz rzeczywiec przerwie zamiast "przepychac na sile"
3. Test escalation — czy Issue z labelka volunteer-support daje odpowiedz w 48h
4. Test retro template — czy template wychwytuje napotkane tarcie
5. Wersje pakietow na Kaggle — dopiero po pierwszym runie
6. Scope GITHUB_PAT — automatyczna weryfikacja nadal niejest mozliwa
7. Quota YouTube/Gemini — nie da sie sprawdzic offline

## Co powinien zrobic kolejny wykonawca

- Przetestowac canary packet z realnym wolontariuszem
- Po retro: naniesc poprawki do runbooka, pre-flighctu i readiness na podstawie wypelnionego template
- Jesli canary przejdzie pozytywnie: otworzyc run dla szerszego krgu wolontariuszy
- Jesli canary odkryje powazne tarcie: naprawic przed kolejnym wolontariuszem
- Domknac pozostale otwarte pozycje readiness: branch protection, CODEOWNERS loginy, obsadzenie rotacji review
