# Canary Pilot Packet

## Cel dokumentu

Ten dokument to operacyjny packet pierwszego pilota wolontariackiego dla `Project 13`. Spina wszystko, co wolontariusz i maintainer musza wiedc w jednej sekwencji: przed sesja, w trakcie i po sesji.

Canary packet nie udaje, ze pilot juz sie odbyl. Przygotowuje go tak, zeby pierwszy run nie byl chaosem, tylko kontrolowanym eksperymentem.

---

## Co to jest controlled canary

Pierwszy wolontariusz nie robi zwyklego publicznego runu. Robi **controlled canary** — co oznacza:

1. Przed startem maintainer potwierdza gotowosc organizacyjna (checklista ponizej).
2. Podczas runu obowiazuja jawne stop conditions — jesli cos nie dziala, przerywamy zamiast "przepychac na sile".
3. Po runie przeprowadzamy retro z wolontariuszem.
4. Dopiero po retro i poprawkach otwieramy run dla szerszego kregu wolontariuszy.

Canary NIE oznacza, ze ryzyko jest zerowe. Oznacza, ze ryzyko jest jawne i kontrolowane.

---

## Sekwencja: przed sesja, w trakcie, po sesji

Wolontariusz i maintainer widza te sama sekwencje:

### Przed sesja (maintainer + wolontariusz)

| Krok | Kto | Co robi | Artefakt |
|------|-----|---------|----------|
| C-1 | Maintainer | Wypelnia checklist maintainera z `PILOT_REVIEW_ASSIGNMENT_AND_APPROVAL_PATH.md` sekcja 5 | Wszystkie pola `__DO_UZUPELNIENIA__` wypelnione |
| C-2 | Maintainer | Potwierdza, ze branch protection na upstream jest wlaczona | Wynik weryfikacji wg `BRANCH_PROTECTION_OPERATOR_PACKET.md` |
| C-3 | Maintainer | Potwierdza, ze CODEOWNERS ma uzupelnione loginy | Loginy zamiast `@DO_UZUPELNIENIA_*` |
| C-4 | Maintainer | Wyznacza primary_pack_reviewer i approver dla pierwszego PR | Pola w sekcji 2.1 `PILOT_REVIEW_ASSIGNMENT_AND_APPROVAL_PATH.md` |
| C-5 | Maintainer | Potwierdza dostepnosc na zywo podczas runu (kanal tekstowy, PR comment, inny szybki kontakt) | Kanal komunikacji + ramy czasowe |
| C-6 | Wolontariusz | Uruchamia pre-flight check: `python3 PROJEKTY/13_baza_czesci_recykling/scripts/preflight_check.py` | Raport pre-flight: brak FAIL, MANUAL sprawdzony |
| C-7 | Wolontariusz | Przechodzi reczna checklist: `VOLUNTEER_PREFLIGHT_CHECKLIST.md` | Wszystkie checkboxy potwierdzone |
| C-8 | Wolontariusz | Czyta `VOLUNTEER_TERMS_OF_PARTICIPATION.md` | Uruchomienie notebooka = potwierdzenie terms |
| C-9 | Wolontariusz | Czyta `RUNBOOK.md` — 10 krokow | Zrozumienie przeplywu |
| C-10 | Wolontariusz | Czyta `VOLUNTEER_FALLBACK_GUIDE.md` — 4 sytuacje awaryjne | Zrozumienie, jak reagowac na problemy |

### W trakcie sesji (wolontariusz z lokalnym agentem, maintainer na stby)

| Krok | Kto | Co robi | Stop condition? |
|------|-----|---------|----------------|
| R-1 | Wolontariusz | Uruchamia komorki notebooka na Kaggle wg RUNBOOK.md krok 4 | Nie |
| R-2 | Wolontariusz | Obserwuje output i sprawdza, czy pliki powstaja | Tak: patrz stop conditions ponizej |
| R-3 | Wolontariusz | Jesli blad API (403, 429, quota) — przerywa | Tak: STOP-QUOTA |
| R-4 | Wolontariusz | Jesli notebook zawieszyl sie >15 min na komorce — przerywa | Tak: STOP-HANG |
| R-5 | Wolontariusz | Jesli blad wersji pakietu — zapisuje traceback, przerywa | Tak: STOP-DEPS |
| R-6 | Wolontariusz | Jesli wynik jest pusty — otwiera PR z opisem brakow | Nie (pusty wynik jest tez wynikiem) |
| R-7 | Wolontariusz | Jesli wszystko przeszlo — weryfikuje artefakty wg RUNBOOK.md krok 5 | Nie |
| R-8 | Wolontariusz | Push do forka wg RUNBOOK.md krok 6 | Nie |
| R-9 | Wolontariusz | Otwiera PR wg RUNBOOK.md krok 7 | Nie |
| R-10 | Wolontariusz | Dopina Artifact record wg RUNBOOK.md krok 8 | Nie |

### Po sesji (maintainer + wolontariusz)

| Krok | Kto | Co robi | Artefakt |
|------|-----|---------|----------|
| P-1 | Maintainer | Review PR wg `REVIEW_CHECKLIST.md` | Decyzja: approve / request changes / reject |
| P-2 | Maintainer | IntegrityRiskAssessment dla zmiany | Rekord integrity |
| P-3 | Maintainer | Approval z zakresem `pilot_run` | Rekord Approval wg `PILOT_REVIEW_ASSIGNMENT_AND_APPROVAL_PATH.md` sekcja 3.4 |
| P-4 | Maintainer | Merge PR | Zmiana w upstream |
| P-5 | Wolontariusz + Maintainer | Retro wg `CANARY_RETRO_TEMPLATE.md` | Wypelniony retro template |
| P-6 | Maintainer | Aktualizuje readiness i onboarding na podstawie retro | Poprawione dokumenty |
| P-7 | Maintainer | Decyduje, czy otwiera run dla szerszego krgu wolontariuszy | Decyzja + uzasadnienie |

---

## Stop conditions

Jawne warunki, kiedy przerwac run zamiast "przepychac na sile":

### STOP-QUOTA: Wyczerpana quota API

- **Sygnal:** blad 403 Forbidden albo 429 Too Many Requests z YouTube API albo Gemini API
- **Dzialanie:** przerwij notebook, zapisz output z komunikatem bledu, zglos problem
- **Kto decyduje:** wolontariusz sam, bez czekania na maintainera
- **Escalation:** GitHub Issue z labelka `volunteer-support`, w tresci: `STOP-QUOTA: API zwrocilo <kod> przy komorce <nazwa>`

### STOP-HANG: Notebook zawieszony

- **Sygnal:** komorka notebooka nie konczy sie po 15 minutach
- **Dzialanie:** Kernel -> Interrupt, zapisz co powstalo, nie restartuj na sile
- **Kto decyduje:** wolontariusz sam, bez czekania na maintainera
- **Escalation:** GitHub Issue z labelka `volunteer-support`, w tresci: `STOP-HANG: komorka <nazwa> nie zakonczyla sie po 15 min`

### STOP-DEPS: Blad zaleznosci albo wersji pakietu

- **Sygnal:** ImportError, ModuleNotFoundError, AttributeError, albo inny blad sugerujacy niezgodna wersje biblioteki
- **Dzialanie:** zapisz pelny traceback, przerwij notebook, zglos problem
- **Kto decyduje:** wolontariusz sam, bez czekania na maintainera
- **Escalation:** GitHub Issue z labelka `volunteer-support`, w tresci: `STOP-DEPS: <wyjatek> przy komorce <nazwa>`, dolacz pelny traceback

### STOP-SCOPE: GITHUB_PAT nie ma odpowiedniego scope

- **Sygnal:** blad 403 przy pushu do forka, albo blad autoryzacji GitHub
- **Dzialanie:** przerwij notebook, sprawdz scope tokenu na https://github.com/settings/tokens
- **Kto decyduje:** wolontariusz sam, bez czekania na maintainera
- **Escalation:** GitHub Issue z labelka `volunteer-support`, w tresci: `STOP-SCOPE: GITHUB_PAT nie pozwala na push do forka`

### STOP-UNCLEAR: Wolontariusz nie wie, co zrobic dalej

- **Sygnal:** wolontariusz nie rozumie instrukcji, nie wie, na jakim jest kroku, albo cos nie pasuje do opisu w runbooku
- **Dzialanie:** przerwij, zapisz stan rzeczy, nie kontynuuj na sile
- **Kto decyduje:** wolontariusz sam, bez czekania na maintainera
- **Escalation:** GitHub Issue z labelka `volunteer-support`, w tresci: `STOP-UNCLEAR: nie jasne na kroku <numer>`, opisz co jest niejasne

---

## Escalation points

| Poziom | Kto | Kiedy | Czas odpowiedzi |
|--------|-----|-------|-----------------|
| 1. Self-stop | Wolontariusz | Stop condition spelniony | Natychmiast |
| 2. Issue | Wolontariusz | Po przerwaniu runu | Cel 48h odpowiedzi |
| 3. Maintainer na zywo | Maintainer | Wolontariusz utknal i Issue nie daje odpowiedzi | Zalezy od kanalu ustalonego w C-5 |

**Wazne:** wolontariusz NIE musi czekac na odpowiedz maintainera, zeby przerwac run. Stop conditions daja mu pelne prawo do przerwania natychmiast.

---

## Kanaly komunikacji podczas canary

| Kanal | Kiedy | Odpowiedzialny |
|-------|-------|----------------|
| GitHub Issue z labelka `volunteer-support` | Po przerwaniu runu albo po otwarciu PR | Wolontariusz |
| Komentarz w PR | Po otwarciu PR, gdy cos nie pasuje w review | Wolontariusz albo Maintainer |
| Kanal na zywo (ustalony w C-5) | Podczas trwania runu, gdy utknelo | Maintainer |

---

## Co nie jest stop condition

- **Pusty wynik** — pusty wynik jest tez wynikiem. Otworz PR z opisem brakow.
- **Ostrzezenie pre-flight (WARN)** — nie blokuje uruchomienia, ale warto sprawdzic.
- **Czesciowy wynik** — nie wszystkie pliki musza powstac. Otworz PR z tym, co jest.

---

## Brak canary nie blokuje przygotowania

Ten packet jest przygotowaniem do canary, nie dowodem na to, ze canary sie odbyl. Nie udajemy, ze:

- retro juz zostalo przeprowadzone (retro template jest pusty do wypelnienia),
- wolontariusz juz przeszedl przez proces (sekwencja jest gotowa, ale nie wykonana),
- readiness jest domkniety (pozostaje DO POTWIERDZENIA tam, gdzie wymaga realnego runu).

Decyzje `go / no-go` przed otwarciem canary podejmuje maintainer na podstawie `CANARY_GO_LIVE_OPERATOR_PACKET.md` — packet spina blokery C-1..C-5 z evidence i statusami.

---

## Zrodla

- `PROJEKTY/13_baza_czesci_recykling/docs/PUBLIC_VOLUNTEER_RUN_READINESS.md`
- `PROJEKTY/13_baza_czesci_recykling/docs/PILOT_REVIEW_ASSIGNMENT_AND_APPROVAL_PATH.md`
- `PROJEKTY/13_baza_czesci_recykling/docs/VOLUNTEER_PREFLIGHT_CHECKLIST.md`
- `PROJEKTY/13_baza_czesci_recykling/docs/VOLUNTEER_FALLBACK_GUIDE.md`
- `PROJEKTY/13_baza_czesci_recykling/docs/VOLUNTEER_TERMS_OF_PARTICIPATION.md`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-kaggle-enrichment-01/RUNBOOK.md`
- `docs/WOLONTARIUSZE_GOTOWE_PRZYDZIALY.md`
- `PROJEKTY/13_baza_czesci_recykling/docs/CANARY_GO_LIVE_OPERATOR_PACKET.md`
