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
| `GITHUB_PAT` | TAK | Wolontariusz | Push do forka; nie wolno zapisac w repo |
| `YOUTUBE_API_KEY` | TAK | Wolontariusz | Wyszukiwanie kandydatow filmow |
| `GEMINI_API_KEY` | TAK | Wolontariusz | Analiza multimodalna, OCR klatek |

**Status: DO POTWIERDZENIA** — nie ma jeszcze publicznej instrukcji dla wolontariusza, jak ustawic sekrety krok po kroku w UI Kaggle. Runbook opisuje to ogolnikowo.

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
| PR nie zawiera sekretow | DO POTWIERDZENIA | Review checklist ma to pytanie, ale nie ma automatycznego skanera |

---

## 3. Gotowosc review

### 3.1 Review Checklist

| Element | Status | Uwagi |
|---------|--------|-------|
| REVIEW_CHECKLIST.md istnieje | GOTOWE | 12 punktow sprawdzajacych |
| Reviewer jest zdefiniowany | CZESCIOWO | `community_curator` jako rola, ale brak konkretnej osoby na pierwsze review |
| Sciezka approval jest jawna | CZESCIOWO | Baseline governance jest juz opisana w `docs/REVIEW_ROTATION_GOVERNANCE.md`, ale nadal trzeba nazwac konkretnego approvera dla pierwszego publicznego PR |
| Rotacja review | CZESCIOWO | Baseline governance jest juz opisana w `docs/REVIEW_ROTATION_GOVERNANCE.md`, ale nadal trzeba nazwac konkretna pule reviewerow i approvera dla pierwszego pilota |

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
| Wolontariusz wie, ze cos moze pojsc nie tak | CZESCIOWO | Runbook ma krok 9 "czego nie robic", ale brak jasnej sekcji "co zrobic, gdy notebook zawiesi sie" |
| Wolontariusz wie, jak zglosic problem | NIE GOTOWE | Brak kanalu komunikacji (issue template, Discord, Telegram) przeznaczonego dla wolontariuszy |
| Wolontariusz wie, ze nie musi wykonywac calosci | DO POTWIERDZENIA | Model jest opt-in, ale nie ma jawnego komunikatu "mozesz przerwac w dowolnym momencie" |

### 4.2 Onboarding wolontariusza

| Element | Status | Uwagi |
|---------|--------|-------|
| Warunki uczestnictwa sa opisane | CZESCIOWO | MODEL_WOLONTARIACKICH_NOTEBOOKOW_KAGGLE.md opisuje model, ale nie ma "terms of participation" |
| Wolontariusz wie, ze jego praca bedzie publiczna | DO POTWIERDZENIA | Fork i PR sa publiczne, ale brak jawnego komunikatu o tym w runbooku |
| Wolontariusz wie, ze jego wynik moze zostac odrzucony | NIE GOTOWE | Brak jasnej informacji, ze review moze odrzucic PR i ze to jest normalne |
| Wolontariusz ma kontakt z maintainerem | DO POTWIERDZENIA | Brak jasnego kanalu; PR jest formom kontaktu, ale to nie wystarczy do rozwiązywania problemow na zywo |

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
| Notebook zawiesza sie na Kaggle | sredni | dry-run lokalny, komunikat o problemie | CZESCIOWO — brak instrukcji fallbackowej dla wolontariusza |
| Wolontariusz nie rozumie runbooka | sredni | test uzytecznosci z osoba spoza projektu | NIE GOTOWE |
| Wynik jest pusty albo bledny | niski | rebuild report i skipped log | GOTOWE |
| Wolontariusz zglasza problem i nie ma odpowiedzi | wysoki | kanal komunikacji | NIE GOTOWE |
| Recenzent nie jest dostepny | sredni | zasada rotacji review + wyznaczenie backup reviewera przed pilotem | CZESCIOWO — governance jest opisana, ale brak jeszcze nazwanych osob do pierwszego pilota |
| PR omija review | niski | branch protection | DO POTWIERDZENIA — nie sprawdzono, czy na upstream sa wlaczone branch protections |
| Zawlaszczenie pracy wolontariusza | niski | fork flow + jawny PR + provenance | GOTOWE |

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
- Sekrety sa prawidlowo ustawione w Kaggle Secrets
- Branch protection na upstream jest wlaczona
- Recenzent pierwszego PR jest wyznaczony i dostepny

### NIE GOTOWE (wymaga pracy przed publicznym runem)

- **Kanal komunikacji dla wolontariuszy** — brak miejsca, gdzie wolontariusz moze zapytac o pomoc
- **Instrukcja fallbackowa** — co zrobic, gdy notebook zawiesi sie albo zwroci blad
- **Jasne komunikaty dla wolontariusza** — ze moze przerwac, ze wynik moze zostac odrzucony, ze jego fork jest publiczny
- **Operacyjne obsadzenie rotacji review** — zasady governance juz istnieja, ale nadal trzeba przypisac konkretne osoby do pierwszego pilota
- **Terms of participation** — brak jasnego dokumentu okreslajacego warunki udzialu wolontariusza
- **Automatyczne skanowanie PR na obecnosc sekretow** — review checklist ma punkt, ale nie ma narzedzia

---

## 7. Rekomendacja

Pierwszy publiczny run powinien byc traktowany jako **controlled pilot**, a nie jako rutynowa operacja. Oznacza to:

1. Wyznaczyc jednego wolontariusza z istniejacego kregu zaufanych osob, a nie otwierac run dla kazdego.
2. Ustalic maintainera dostepnego na zywo podczas pierwszego uruchomienia (kanal tekstowy, PR comment albo inny szybki kontakt).
3. Przed pierwszym runem potwierdzic recznie, ze branch protection na upstream jest wlaczona.
4. Po pierwszym PR przeprowadzic retro z wolontariuszem: co bylo niejasne, co nie dzialalo, co brakowalo w runbooku.
5. Dopiero po retro i poprawkach otworzyc run dla szerszego kregu wolontariuszy.

---

## 8. Zrodla

- `PROJEKTY/13_baza_czesci_recykling/README.md`
- `PROJEKTY/13_baza_czesci_recykling/docs/MODEL_WOLONTARIACKICH_NOTEBOOKOW_KAGGLE.md`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-kaggle-enrichment-01/RUNBOOK.md`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-kaggle-enrichment-01/manifest.json`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-kaggle-enrichment-01/REVIEW_CHECKLIST.md`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-kaggle-enrichment-01/integrity_risk_assessment.json`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/CHAIN_MAP.md`
- `docs/HANDOFF_DLA_NASTEPNEGO_AGENTA_2026-04-22.md`
- `docs/REVIEW_ROTATION_GOVERNANCE.md`
