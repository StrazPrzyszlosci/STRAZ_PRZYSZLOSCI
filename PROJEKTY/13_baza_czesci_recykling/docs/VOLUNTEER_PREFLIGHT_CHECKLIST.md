# Volunteer Pre-Flight Checklist

## Cel

Ten dokument to jawny pre-flight dla wolontariusza. Przed odpaleniem notebooka Kaggle albo lokalnego dry-runu, wolontariusz i jego lokalny agent powinni przejsc te checkliste.

Pre-flight nie udaje, ze wszystko da sie sprawdzic automatycznie. Rozdziela to, co skrypt potwierdzi, od tego, co wolontariusz musi sprawdzic recznie.

---

## Szybki start: automatyczny pre-flight

Uruchom skrypt pre-flight z repo:

```bash
python3 PROJEKTY/13_baza_czesci_recykling/scripts/preflight_check.py
```

Skrypt sprawdzi:

- czy istnieje plik `.env` z sekretami,
- czy wymagane pliki projektu sa obecne,
- czy notebook parsuje sie jako prawidlowy JSON,
- czy notebook zawiera oczekiwane markery workflowu,
- czy format `GITHUB_PAT` wyglada prawidlowo.

Skrypt NIE sprawdzi (i nie moze):

- scope `GITHUB_PAT` — trzeba recznie na https://github.com/settings/tokens,
- quota YouTube API — trzeba recznie w Google Cloud Console,
- quota Gemini API — trzeba recznie na https://ai.google.dev/pricing,
- dostepnosci darmowego runtime Kaggle.

Wynik skryptu to raport z kategoriami: PASS, FAIL, WARN, MANUAL, SKIP. Punkty FAIL blokuja uruchomienie. Punkty MANUAL wymagaja recznego potwierdzenia.

---

## Checklist: sekcje reczne

### 1. Konto i fork

- [ ] Masz konto GitHub i fork repo `StrazPrzyszlosci/STRAZ_PRZYSZLOSCI`
- [ ] `git remote -v` pokazuje Twoj fork jako origin
- [ ] Nie pushujesz bezposrednio do upstream

### 2. `GITHUB_PAT` — scope i uprawnienia

- [ ] Token istnieje i jest ustawiony w `.env` oraz w Kaggle Secrets
- [ ] Token ma **Contents: Read and write** (fine-grained) albo scope **repo** (classic)
- [ ] Repository access w fine-grained tokenie ogranicza sie do Twojego forka
- [ ] Sprawdzono recznie na https://github.com/settings/tokens — skrypt nie moze potwierdzic scope

### 3. `YOUTUBE_API_KEY` — quota

- [ ] Klucz istnieje i jest ustawiony w `.env` oraz w Kaggle Secrets
- [ ] YouTube Data API v3 jest wlaczone w projekcie Google Cloud
- [ ] Sprawdzono quota: https://console.cloud.google.com/apis/api/youtube.googleapis.com/quotas
- [ ] Darmowa quota: ~10 000 jednostek/dobe; jeden search = 100 jednostek
- [ ] Nie ma wyczerpanej quota z innej czesci projektu albo innego narzedzia

### 4. `GEMINI_API_KEY` — quota

- [ ] Klucz istnieje i jest ustawiony w `.env` oraz w Kaggle Secrets
- [ ] Sprawdzono limity: https://ai.google.dev/pricing
- [ ] Darmowy tier: limity requests/min i tokens/min
- [ ] Nie ma wyczerpanej quota z innej czesci projektu albo innego narzedzia

### 5. Kaggle

- [ ] Masz aktywne konto Kaggle
- [ ] Darmowy runtime jest dostepny (nie zuzyty w innej sesji)
- [ ] Notebook zaimportowany z pliku `youtube-databaseparts.ipynb`
- [ ] Sekrety dodane w Kaggle Secrets (Add-ons > Secrets): `GITHUB_PAT`, `YOUTUBE_API_KEY`, `GEMINI_API_KEY`
- [ ] Komorka konfiguracyjna uzupelniona: `FORK_OWNER`, `GIT_USER_NAME`, `GIT_USER_EMAIL`

### 6. Zrozumienie

- [ ] Przeczytano `RUNBOOK.md` — 9 krokow
- [ ] Przeczytano `VOLUNTEER_TERMS_OF_PARTICIPATION.md` — 10 punktow
- [ ] Znany jest fallback: `VOLUNTEER_FALLBACK_GUIDE.md` — 4 sytuacje awaryjne
- [ ] Wolontariusz wie, ze moze przerwac w dowolnym momencie
- [ ] Wolontariusz wie, ze wynik moze zostac odrzucony w review

---

## Co zrobic, gdy pre-flight pokazuje FAIL

1. Popraw kazdy punkt FAIL — skrypt poda konkretna wskazowke.
2. Jesli brakuje `.env`, skopiuj z `.env.example` i uzupelnij wartosci.
3. Jesli brakuje sekretu, sledz instrukcje w `README.md` sekcja "Jak ustawic sekrety".
4. Jesli nie wiesz, jak poprawic punkt FAIL, zglos problem przez GitHub Issue z labelka `volunteer-support`.

## Co zrobic, gdy pre-flight pokazuje MANUAL

To nie sa bledy — to rzeczy, ktore skrypt nie moze sprawdzic za Ciebie:

1. Otworz linki podane w raporcie.
2. Potwierdz recznie, ze scope i quota sa w porzadku.
3. Jesli quota jest wyczerpana, odczekaj dobe albo stworz nowy projekt Google Cloud.
4. Zapisz wynik recznego sprawdzenia dla siebie — nie musisz go zgloszac.

## Co zrobic, gdy pre-flight pokazuje WARN

Ostrzezenia nie blokuja uruchomienia, ale wskazuja ryzyko:

1. Sprawdz, czy ostrzezenie jest istotne dla Twojego runu.
2. Jesli marker notebooka nie zostal znaleziony, notebook moze miec inna wersje niz oczekiwano.
3. Jesli format `GITHUB_PAT` nie wyglada typowo, upewnij sie, ze to wlasciwy token.

---

## Zrodla

- `PROJEKTY/13_baza_czesci_recykling/scripts/preflight_check.py` — automatyczny skrypt
- `PROJEKTY/13_baza_czesci_recykling/README.md` — sekcja "Jak ustawic sekrety"
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-kaggle-enrichment-01/RUNBOOK.md`
- `PROJEKTY/13_baza_czesci_recykling/docs/PUBLIC_VOLUNTEER_RUN_READINESS.md`
- `PROJEKTY/13_baza_czesci_recykling/docs/VOLUNTEER_FALLBACK_GUIDE.md`
- `PROJEKTY/13_baza_czesci_recykling/docs/VOLUNTEER_TERMS_OF_PARTICIPATION.md`
