# Public Volunteer Run Readiness

## Cel dokumentu

Ten dokument jest checklista gotowosci do pierwszego publicznego wolontariackiego runu `Project 13`. Nie ogranicza sie tylko do stanu technicznego notebooka — obejmuje rowniez fork flow, review, provenance i komunikacje z wolontariuszem.

Rozdziela jasno to, co jest gotowe lokalnie, od tego, co musi byc potwierdzone przed publicznym uruchomieniem.

---

## 1. Gotowosc techniczna

### 1.1 Notebook

| Element | Status lokalny | Status publiczny | Uwagi |
|---------|---------------|-----------------|-------|
| Notebook `youtube-databaseparts.ipynb` istnieje i dziala lokalnie | GOTOWE | DO POTWIERDZENIA | Lokalne dry-runy przeszly, ale prawdziwy Kaggle runtime moze zachowac sie inaczej (limity, timeouty, wersje bibliotek) |
| Finalizer `finalize_execution_pack_run.py` zapisuje Run record | GOTOWE | DO POTWIERDZENIA | Sprawdzone lokalnie z git_mode=push i git_mode=none; na Kaggle trzeba potwierdzic, ze git push dziala z forka |
| Rebuild outputow review-ready (`rebuild_autonomous_outputs.py`) | GOTOWE | GOTOWE | Dziala deterministycznie; ostatni rebuild: 82 total, 77 accepted, 5 skipped |
| Helper dopiecia Artifact (`attach_pr_artifact_record.py`) | GOTOWE | GOTOWE | Wspiera run_id, fork-owner i autodiscovery |
| Dry-run skrypt (`dry_run_execution_pack.py`) | GOTOWE | GOTOWE | Uzywalny lokalnie przed publicznym runem |
| Raport runu (`last_run_summary.md`) | GOTOWE | DO POTWIERDZENIA | Szablon dziala; tresc zalezy od prawdziwych danych z Kaggle |

### 1.2 Sekrety

| Sekret | Potrzebny? | Kto ustawia? | Uwagi |
|--------|-----------|-------------|-------|
| `GITHUB_PAT` | TAK | Wolontariusz | Push do forka; nie wolno zapisac w repo; instrukcja: `README.md` sekcja "Jak ustawic sekrety"; scope: Fine-grained Contents=R+W albo classic repo |
| `YOUTUBE_API_KEY` | TAK | Wolontariusz | Wyszukiwanie kandydatow filmow; instrukcja: `README.md` sekcja "Jak ustawic sekrety"; quota: ~10 000 jednostek/dobe |
| `GEMINI_API_KEY` | TAK | Wolontariusz | Analiza multimodalna, OCR klatek; instrukcja: `README.md` sekcja "Jak ustawic sekrety"; limity RPM/TPM na darmowym tierze |

**Status: GOTOWE** — publiczna instrukcja setupu sekretow znajduje sie w `PROJEKTY/13_baza_czesci_recykling/README.md` sekcja "Jak ustawic sekrety". Plik `.env.example` zawiera szablon z krok po kroku opisem pozyskania kazdego klucza i przeniesienia do Kaggle Secrets. RUNBOOK.md krok 3 odsyla do tej instrukcji.

### 1.2a Pre-flight check

| Element | Status | Uwagi |
|---------|--------|-------|
| Skrypt pre-flight `preflight_check.py` | GOTOWE | Sprawdza: `.env`, obecnosc sekretow, pliki projektu, smoke notebooka, format GITHUB_PAT |
| Jawna checklist reczna (scope, quota, Kaggle) | GOTOWE | `VOLUNTEER_PREFLIGHT_CHECKLIST.md` — scope GITHUB_PAT, quota YouTube/Gemini, runtime Kaggle |
| Weryfikacja scope GITHUB_PAT | RECZNA | Skrypt sprawdza format tokenu, ale scope trzeba potwierdzic recznie na https://github.com/settings/tokens |
| Pre-flight check quota YouTube/Gemini | RECZNA | Quota nie da sie sprawdzic offline; wolontariusz musi potwierdzic recznie w konsoli Google Cloud i na https://ai.google.dev/pricing |

### 1.2b Canary pilot packet

| Element | Status | Uwagi |
|---------|--------|-------|
| Canary pilot packet | GOTOWE | `CANARY_PILOT_PACKET.md` — sekwencja przed/w trakcie/po sesji, stop conditions, escalation points |
| Retro template po pierwszej sesji | GOTOWE | `CANARY_RETRO_TEMPLATE.md` — template do wypelnienia po pierwszym canary runie; nie udaje, ze retro juz wykonano |
| Stop conditions (STOP-QUOTA, STOP-HANG, STOP-DEPS, STOP-SCOPE, STOP-UNCLEAR) | GOTOWE | Definicja w `CANARY_PILOT_PACKET.md`; wolontariusz ma prawo przerwac bez czekania na maintainera |
| Escalation points | GOTOWE | 3-poziomowa eskalacja: self-stop -> Issue -> maintainer na zywo; w `CANARY_PILOT_PACKET.md` |
| Go-live operator packet | GOTOWE | `CANARY_GO_LIVE_OPERATOR_PACKET.md` — decyzja go/no-go z blocker ledger C-1..C-5; obecnie NO-GO |

### 1.3 Zaleznosci runtime

| Zaleznosc | Status | Uwagi |
|-----------|--------|-------|
| Darmowy runtime Kaggle dostepny | DO POTWIERDZENIA | Wolontariusz musi miec aktywne konto Kaggle z niewykorzystanym limitem |
| Wersje pakietow Python na Kaggle | DO POTWIERDZENIA | Notebook moze zalezec od pakietow, ktore na Kaggle sa w innej wersji niz lokalnie |
| Dostep do YouTube Data API | DO POTWIERDZENIA | Limit zapytan API jest ograniczony; wolontariusz musi miec wlasny klucz z włączona quota |
| Dostep do Gemini API | DO POTWIERDZENIA | Analogicznie — wolontariusz musi miec wlasny klucz i quota |

---

## 2. Gotowosc fork flow

### 2.1 Fork i branch

| Element | Status | Uwagi |
|---------|--------|-------|
| Instrukcja tworzenia forka | GOTOWE | Opisana w RUNBOOK.md krok 1 |
| Model branch per run | GOTOWE | Finalizer tworzy branch o nazwie `pack-project13-kaggle-enrichment-<timestamp>` |
| Push do forka, nie do upstream | GOTOWE | Notebook i finalizer ustawiaja remote na fork wolontariusza |
| Brak bezposredniego pushu do upstream | GOTOWE | Zabezpieczone w kontrakcie packa i integrity assessment |

### 2.2 Pull Request

| Element | Status | Uwagi |
|---------|--------|-------|
| PR_TEMPLATE.md istnieje | GOTOWE | `execution_packs/pack-project13-kaggle-enrichment-01/PR_TEMPLATE.md` |
| PR wymaga pack_id, run_id, branch, notebook | GOTOWE | Wymagane w szablonie i review checklist |
| PR opisuje ograniczenia i known issues | DO POTWIERDZENIA | Szablon ma pole, ale tresc zalezy od wolontariusza — trzeba sprawdzac recznie |
| PR nie zawiera sekretow | GOTOWE | Automatyczny scan: workflow `pr_secret_scan.yml` (GitHub Actions) + lokalny skrypt `scripts/scan_pr_secrets.py`; review checklist zaktualizowany |

---

## 3. Gotowosc review

### 3.1 Review Checklist i Review Enforcement

| Element | Status | Uwagi |
|---------|--------|-------|
| REVIEW_CHECKLIST.md istnieje | GOTOWE | 12 punktow sprawdzajacych |
| Reviewer jest zdefiniowany | CZESCIOWO | `community_curator` jako rola, ale brak konkretnej osoby na pierwsze review |
| Sciezka approval jest jawna | CZESCIOWO | Baseline governance jest juz opisana w `docs/REVIEW_ROTATION_GOVERNANCE.md`, ale nadal trzeba nazwac konkretnego approvera dla pierwszego publicznego PR |
| Rotacja review | CZESCIOWO | Baseline governance jest juz opisana w `docs/REVIEW_ROTATION_GOVERNANCE.md`, ale nadal trzeba nazwac konkretna pule reviewerow i approvera dla pierwszego pilota |
| `.github/CODEOWNERS` istnieje | GOTOWE | Baseline z mapowaniem sciezek na role review; loginy `DO_UZUPELNIENIA` — maintainer musi uzupelnic |
| CODEOWNERS loginy uzupelnione | DO POTWIERDZENIA | Maintainer musi zamienic `@DO_UZUPELNIENIA_*` na loginy GitHub; patrz `REVIEW_ENFORCEMENT_BASELINE.md` krok 1 |
| `require_code_owner_reviews` wlaczone | DO POTWIERDZENIA | Wymaga: (1) uzupelnienia CODEOWNERS, (2) wlaczenia opcji w branch protection; patrz `BRANCH_PROTECTION_OPERATOR_PACKET.md` |
| Dokument review enforcement | GOTOWE | `REVIEW_ENFORCEMENT_BASELINE.md` opisuje, jak CODEOWNERS, secret scan i branch protection sie uzupelniaja |

### 3.2 Provenance

| Element | Status | Uwagi |
|---------|--------|-------|
| Kanoniczny Run record powstaje automatycznie | GOTOWE | Finalizer zapisuje go w `execution_packs/.../records/` |
| Artifact da sie dopiac po PR | GOTOWE | Helper `attach_pr_artifact_record.py` dziala lokalnie |
| Audit trail odrzuconych rekordow | GOTOWE | `rebuild_autonomous_outputs_skipped.jsonl` |
| Raport rebuild z accepted/skipped counts | GOTOWE | `rebuild_autonomous_outputs_report.md` |

---

## 4. Gotowosc komunikacyjna

### 4.1 Komunikacja z wolontariuszem

| Element | Status | Uwagi |
|---------|--------|-------|
| Runbook prowadzi wolontariusza krok po kroku | GOTOWE | `RUNBOOK.md` — 9 krokow |
| Wolontariusz rozumie, co robi i po co | DO POTWIERDZENIA | Brak testu uzytecznosci runbooka z osoba spoza projektu |
| Wolontariusz wie, ze cos moze pojsc nie tak | GOTOWE | `VOLUNTEER_FALLBACK_GUIDE.md` opisuje 4 sytuacje awaryjne + instrukcje przerwania |
| Wolontariusz wie, jak zglosic problem | GOTOWE | Issue template `volunteer_problem_report.md` + labelka `volunteer-support`; rekomendowany czas odpowiedzi: 48h |
| Wolontariusz wie, ze nie musi wykonywac calosci | GOTOWE | Jawny komunikat w `VOLUNTEER_FALLBACK_GUIDE.md` sekcja "Mozesz przerwac w dowolnym momencie" + `VOLUNTEER_TERMS_OF_PARTICIPATION.md` punkt 1 |

### 4.2 Onboarding wolontariusza

| Element | Status | Uwagi |
|---------|--------|-------|
| Warunki uczestnictwa sa opisane | GOTOWE | `VOLUNTEER_TERMS_OF_PARTICIPATION.md` — 10 punktow, w tym dobrowolnosc, publicznosc, odrzucenie wyniku, sekrety, brak zawlaszczenia |
| Wolontariusz wie, ze jego praca bedzie publiczna | GOTOWE | Jawny komunikat w `VOLUNTEER_TERMS_OF_PARTICIPATION.md` punkt 2; rekomendacja konta anonimowego |
| Wolontariusz wie, ze jego wynik moze zostac odrzucony | GOTOWE | Jawny komunikat w `VOLUNTEER_TERMS_OF_PARTICIPATION.md` punkt 3; odrzucenie PR nie jest ocena wolontariusza |
| Wolontariusz ma kontakt z maintainerem | CZESCIOWO | GitHub Issue z labelka `volunteer-support`; cel 48h odpowiedzi; brak jeszcze kanalu na zywo (Discord/Telegram: do_potwierdzenia) |

---

## 5. Gotowosc organizacyjna

### 5.1 Governance

| Element | Status | Uwagi |
|---------|--------|-------|
| IntegrityRiskAssessment packa | GOTOWE | `integrity-pack-project13-kaggle-enrichment-01`, status: pass, risk_level: low |
| ReadinessGate packa | GOTOWE | `gate-pack-ready-project13-kaggle-enrichment-01`, status: pass |
| Zasada fork-first | GOTOWE | Wymuszona w notebooku i kontrakcie packa |
| Zasada review-before-merge | GOTOWE | Wymuszona w modelu PR |
| Zasada niepromowania bez provenance | GOTOWE | W acceptance criteria packa |

### 5.2 Ryzyka specyficzne dla pierwszego publicznego runu

| Ryzyko | Poziom | Mitygacja | Status mitygacji |
|--------|--------|-----------|-----------------|
| Notebook zawiesza sie na Kaggle | sredni | dry-run lokalny, komunikat o problemie, stop condition STOP-HANG | GOTOWE — `VOLUNTEER_FALLBACK_GUIDE.md` Sytuacja 1 + `CANARY_PILOT_PACKET.md` STOP-HANG |
| Wolontariusz nie rozumie runbooka | sredni | test uzytecznosci z osoba spoza projektu, stop condition STOP-UNCLEAR | CZESCIOWO — canary packet opisuje sekwencje i stop condition, ale test z realnym wolontariuszem nadal czeka |
| Wynik jest pusty albo bledny | niski | rebuild report i skipped log | GOTOWE |
| Wolontariusz zglasza problem i nie ma odpowiedzi | wysoki | kanal komunikacji, escalation points | CZESCIOWO — Issue template istnieje, canary packet definiuje escalation, ale brak kanalu na zywo; cel 48h odpowiedzi |
| Recenzent nie jest dostepny | sredni | zasada rotacji review + wyznaczenie backup reviewera przed pilotem | CZESCIOWO — governance jest opisana, ale brak jeszcze nazwanych osob do pierwszego pilota |
| PR omija review | niski | branch protection + CODEOWNERS | CZESCIOWO — operator packet istnieje (`BRANCH_PROTECTION_OPERATOR_PACKET.md`), CODEOWNERS istnieje (`.github/CODEOWNERS`), ale maintainer musi jeszcze wykonac weryfikacje branch protection i uzupelnic loginy w CODEOWNERS |
| Zawlaszczenie pracy wolontariusza | niski | fork flow + jawny PR + provenance | GOTOWE |
| Wyczerpanie quota API podczas runu | sredni | stop condition STOP-QUOTA, jawna instrukcja w pre-flighcie | GOTOWE — `CANARY_PILOT_PACKET.md` STOP-QUOTA + `VOLUNTEER_PREFLIGHT_CHECKLIST.md` |
| Blad zaleznosci / wersji pakietu na Kaggle | sredni | stop condition STOP-DEPS | GOTOWE — `CANARY_PILOT_PACKET.md` STOP-DEPS |

---

## 6. Podsumowanie: gotowe lokalnie vs gotowe publicznie

### GOTOWE LOKALNIE (nie wymaga dodatkowej pracy)

- Notebook i finalizer dzialaja lokalnie
- Rebuild outputow review-ready jest deterministyczny
- Helper dopiecia Artifact dziala
- Run record powstaje automatycznie
- Audit trail odrzuconych rekordow
- Fork flow (fork -> branch -> PR) jest zabezpieczony w kontrakcie
- Review checklist istnieje
- IntegrityRiskAssessment i ReadinessGate sa pass
- PR_TEMPLATE.md i RUNBOOK.md istnieja

### DO POTWIERDZENIA PRZED PUBLICZNYM RUNEM

- Notebook dziala na prawdziwym runtime Kaggle bez bledow wersji pakietow
- Wolontariusz potrafi przejsc przez runbook bez pomocy maintainera
- Sekrety sa prawidlowo ustawione w Kaggle Secrets (instrukcja dostepna w README.md i .env.example; pozostaje do potwierdzenia realne wykonanie przez wolontariusza)
- Scope `GITHUB_PAT` jest prawidlowy (pre-flight skrypt sprawdza format; scope trzeba potwierdzic recznie — patrz `VOLUNTEER_PREFLIGHT_CHECKLIST.md` sekcja 2)
- Quota YouTube i Gemini jest wystarczajaca (nie da sie sprawdzic offline — patrz `VOLUNTEER_PREFLIGHT_CHECKLIST.md` sekcje 3 i 4)
- Branch protection na upstream jest wlaczona (operator packet: `BRANCH_PROTECTION_OPERATOR_PACKET.md`; maintainer musi wykonac weryfikacje)
- CODEOWNERS loginy sa uzupelnione (`.github/CODEOWNERS` istnieje z `@DO_UZUPELNIENIA_*`; maintainer musi zamienic na loginy GitHub — patrz `REVIEW_ENFORCEMENT_BASELINE.md` krok 1)
- Recenzent pierwszego PR jest wyznaczony i dostepny

### NIE GOTOWE (wymaga pracy przed publicznym runem)

- **Test uzytecznosci runbooka** — brak testu z osoba spoza projektu; wolontariusz moze nie zrozumiec instrukcji bez pomocy
- **Automatyczne skanowanie PR na obecnosc sekretow** — ~~brak narzedzia~~ GOTOWE: workflow `pr_secret_scan.yml` + lokalny skrypt `scripts/scan_pr_secrets.py`
- **Kanal komunikacji na zywo** — Issue template jest gotowy, ale brak Discord/Telegram/do_potwierdzenia; GitHub Issues sa rekomendowane jako baseline
- **Branch protection na upstream** — ~~nie sprawdzono~~ CZESCIOWO: operator packet `BRANCH_PROTECTION_OPERATOR_PACKET.md` istnieje; maintainer musi wykonac weryfikacje

### DOMKNIETE W TEJ ITERACJI (byly NIE GOTOWE)

- ~~**Kanal komunikacji dla wolontariuszy**~~ — GOTOWE: Issue template `volunteer_problem_report.md` + labelka `volunteer-support`
- ~~**Instrukcja fallbackowa**~~ — GOTOWE: `VOLUNTEER_FALLBACK_GUIDE.md` opisuje 4 sytuacje awaryjne
- ~~**Jasne komunikaty dla wolontariusza**~~ — GOTOWE: fallback guide + terms of participation
- ~~**Terms of participation**~~ — GOTOWE: `VOLUNTEER_TERMS_OF_PARTICIPATION.md` — 10 punktow
- ~~**Operacyjne obsadzenie rotacji review**~~ — CZESCIOWO→CZESCIOWO: governance opisana, ale nadal brak nazwanych osob (nie zmienilo sie)
- ~~**Instrukcja setupu sekretow dla wolontariusza**~~ — GOTOWE: `README.md` sekcja "Jak ustawic sekrety" + `.env.example` + RUNBOOK.md krok 3 z detalami Kaggle Secrets
- ~~**Automatyczne skanowanie PR na obecnosc sekretow**~~ — GOTOWE: workflow `pr_secret_scan.yml` (GitHub Actions) + lokalny skrypt `scripts/scan_pr_secrets.py`; REVIEW_CHECKLIST.md zaktualizowany
- ~~**Operator packet dla branch protection**~~ — GOTOWE: `BRANCH_PROTECTION_OPERATOR_PACKET.md` z krok po kroku instrukcja weryfikacji i wlaczenia protection na `main`
- ~~**Pre-flight check dla wolontariusza**~~ — GOTOWE: skrypt `scripts/preflight_check.py` + `VOLUNTEER_PREFLIGHT_CHECKLIST.md` z reczna checklist scope i quota
- ~~**Weryfikacja scope GITHUB_PAT**~~ — CZESCIOWO→RECZNA: skrypt pre-flight sprawdza format tokenu, ale scope trzeba potwierdzic recznie; instrukcja w `VOLUNTEER_PREFLIGHT_CHECKLIST.md` sekcja 2
- ~~**Pre-flight check quota YouTube/Gemini**~~ — NIE GOTOWE→RECZNA: quota nie da sie sprawdzic offline; wolontariusz dostaje jawna instrukcje w `VOLUNTEER_PREFLIGHT_CHECKLIST.md` sekcje 3 i 4
- ~~**CODEOWNERS**~~ — NIE ISTNIAL→GOTOWE: `.github/CODEOWNERS` z baseline mapowaniem sciezek na role review; loginy `DO_UZUPELNIENIA`
- ~~**Review enforcement baseline**~~ — NIE ISTNIAL→GOTOWE: `REVIEW_ENFORCEMENT_BASELINE.md` opisuje, jak CODEOWNERS, secret scan i branch protection sie uzupelniaja; instrukcja aktywacji dla maintainera
- ~~**Brak kontrolowanego packetu pierwszego pilota wolontariackiego**~~ — NIE ISTNIAL→GOTOWE: `CANARY_PILOT_PACKET.md` spina sekwencje przed/w trakcie/po sesji, stop conditions i escalation points
- ~~**Retro template po pierwszym canary runie**~~ — NIE ISTNIAL→GOTOWE: `CANARY_RETRO_TEMPLATE.md` — template do wypelnienia po pierwszej sesji; nie udaje, ze retro juz wykonano
- ~~**Stop conditions dla wolontariusza**~~ — NIE ISTNIAL→GOTOWE: 5 stop conditions (STOP-QUOTA, STOP-HANG, STOP-DEPS, STOP-SCOPE, STOP-UNCLEAR) w `CANARY_PILOT_PACKET.md`

---

## 7. Rekomendacja

Pierwszy publiczny run powinien byc traktowany jako **controlled canary pilot**, a nie jako rutynowa operacja. Oznacza to:

1. Wyznaczyc jednego wolontariusza z istniejacego kregu zaufanych osob, a nie otwierac run dla kazdego.
2. Ustalic maintainera dostepnego na zywo podczas pierwszego uruchomienia (kanal tekstowy, PR comment albo inny szybki kontakt).
3. Przed pierwszym runem potwierdzic recznie, ze branch protection na upstream jest wlaczona.
4. Podczas runu obowiazuja stop conditions z `CANARY_PILOT_PACKET.md` — wolontariusz ma prawo przerwac bez czekania na maintainera.
5. Po pierwszym PR przeprowadzic retro z wolontariuszem wg `CANARY_RETRO_TEMPLATE.md`.
6. Dopiero po retro i poprawkach otworzyc run dla szerszego kregu wolontariuszy.

Sekwencja canary (przed, w trakcie, po) jest opisana w `CANARY_PILOT_PACKET.md`. Decyzje `go / no-go` podejmuje maintainer na podstawie `CANARY_GO_LIVE_OPERATOR_PACKET.md` — packet spina blokery C-1..C-5 z evidence i statusami.

---

## 8. Zrodla

- `PROJEKTY/13_baza_czesci_recykling/README.md`
- `PROJEKTY/13_baza_czesci_recykling/docs/MODEL_WOLONTARIACKICH_NOTEBOOKOW_KAGGLE.md`
- `PROJEKTY/13_baza_czesci_recykling/docs/VOLUNTEER_PREFLIGHT_CHECKLIST.md`
- `PROJEKTY/13_baza_czesci_recykling/scripts/preflight_check.py`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-kaggle-enrichment-01/RUNBOOK.md`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-kaggle-enrichment-01/manifest.json`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-kaggle-enrichment-01/REVIEW_CHECKLIST.md`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-kaggle-enrichment-01/integrity_risk_assessment.json`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/CHAIN_MAP.md`
- `docs/HANDOFF_DLA_NASTEPNEGO_AGENTA_2026-04-22.md`
- `PROJEKTY/13_baza_czesci_recykling/docs/REVIEW_ENFORCEMENT_BASELINE.md`
- `PROJEKTY/13_baza_czesci_recykling/docs/BRANCH_PROTECTION_OPERATOR_PACKET.md`
- `PROJEKTY/13_baza_czesci_recykling/docs/PILOT_REVIEW_ASSIGNMENT_AND_APPROVAL_PATH.md`
- `.github/CODEOWNERS`
- `.github/workflows/pr_secret_scan.yml`
- `docs/REVIEW_ROTATION_GOVERNANCE.md`
- `PROJEKTY/13_baza_czesci_recykling/docs/CANARY_PILOT_PACKET.md`
- `PROJEKTY/13_baza_czesci_recykling/docs/CANARY_RETRO_TEMPLATE.md`
- `PROJEKTY/13_baza_czesci_recykling/docs/CANARY_GO_LIVE_OPERATOR_PACKET.md`
