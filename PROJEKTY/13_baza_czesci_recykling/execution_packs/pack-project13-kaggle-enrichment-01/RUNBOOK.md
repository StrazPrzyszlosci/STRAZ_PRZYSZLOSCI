# Runbook Wolontariusza Dla Pack Project13 Kaggle Enrichment 01

## Cel

Ten runbook prowadzi wolontariusza i jego lokalnego agenta przez pierwszy realny loop `KaggleNotebookPack` dla `Project 13`.

Docelowy przeplyw:

```text
fork -> Kaggle notebook -> branch na forku -> PR -> review -> merge
```

## Co trzeba miec przed startem

- konto `GitHub`
- wlasny fork repo `StrazPrzyszlosci/STRAZ_PRZYSZLOSCI`
- konto `Kaggle`
- notebook `PROJEKTY/13_baza_czesci_recykling/youtube-databaseparts.ipynb`
- sekrety ustawione w `Kaggle Secrets`

## Wymagane sekrety

Pack wymaga trzech sekretow. Szczegolowa instrukcja, skad wziasc kazdy klucz, znajduje sie w `PROJEKTY/13_baza_czesci_recykling/README.md` sekcja "Jak ustawic sekrety". Plik `.env.example` w katalogu projektu zawiera gotowy szablon.

### `GITHUB_PAT` — token pushu do Twojego forka

1. Wejdz na https://github.com/settings/tokens?type=beta (Fine-grained tokens).
2. Kliknij **Generate new token**.
3. Nadaj nazwe, np. `kaggle-pack-push`.
4. W **Repository access** wybierz **Only select repositories** i wskaz swoj fork.
5. W **Permissions > Repository permissions** ustaw **Contents: Read and write**.
6. Wygeneruj token i skopiuj wartosc.

Alternatywa (legacy): https://github.com/settings/tokens ze scope `repo`.

### `YOUTUBE_API_KEY` — klucz do YouTube Data API v3

1. Wejdz na https://console.cloud.google.com/.
2. Utworz projekt (lub wybierz istniejacy).
3. Przejdz do **APIs & Services > Library** i wlacz **YouTube Data API v3**.
4. Przejdz do **APIs & Services > Credentials** i kliknij **Create Credentials > API key**.
5. Skopiuj klucz. Opcjonalnie ogranicz go do YouTube Data API v3 (**Restrict key**).

Darmowa quota: ok. 10 000 jednostek/dobe; jeden search = 100 jednostek.

### `GEMINI_API_KEY` — klucz do Gemini API (analiza multimodalna, OCR klatek)

1. Wejdz na https://aistudio.google.com/apikey.
2. Zaloguj sie kontem Google.
3. Kliknij **Create API key** albo **Get API key**.
4. Wybierz projekt Google Cloud (lub utworz nowy).
5. Skopiuj klucz.

Darmowy tier: limity requests/min i tokens/min — patrz https://ai.google.dev/pricing.

### Lokalny plik `.env`

Skopiuj szablon i uzupelnij wartosci:

```bash
cp PROJEKTY/13_baza_czesci_recykling/.env.example PROJEKTY/13_baza_czesci_recykling/.env
```

Nigdy nie commituj pliku `.env` do repozytorium — jest w `.gitignore`.

### Przeniesienie do Kaggle Secrets

Te same wartosci z `.env` musisz dodac w UI Kaggle:

1. W otwartym notebooku kliknij w pasku bocznym ikone klucza (**Add-ons > Secrets**).
2. Kliknij **+ Add Secret**.
3. Dodaj sekret o nazwie `GITHUB_PAT` z wartoscia z Twojego `.env`.
4. Powtorz dla `YOUTUBE_API_KEY` i `GEMINI_API_KEY`.
5. Nazwy w Kaggle Secrets musza byc dokladnie takie same jak wyzej — notebook odczyta je przez `kaggle_secrets.UserSecretClient()`.

Nie zapisuj tych sekretow w repozytorium ani w tresci PR.

## Krok 0. Pre-flight check

Zanim zaczniesz cokolwiek ustawiac, uruchom pre-flight check:

```bash
python3 PROJEKTY/13_baza_czesci_recykling/scripts/preflight_check.py
```

Skrypt sprawdzi:

- czy istnieje plik `.env` z sekretami,
- czy wymagane pliki projektu sa obecne,
- czy notebook parsuje sie poprawnie,
- czy format `GITHUB_PAT` wyglada prawidlowo.

Skrypt NIE sprawdzi (i nie moze):

- scope `GITHUB_PAT` — sprawd recznie na https://github.com/settings/tokens,
- quota YouTube API — sprawd w Google Cloud Console,
- quota Gemini API — sprawd na https://ai.google.dev/pricing,
- dostepnosci darmowego runtime Kaggle.

Jesli pre-flight pokazuje FAIL, popraw te punkty przed kontynuowaniem. Szczegolowa checklist reczna: `PROJEKTY/13_baza_czesci_recykling/docs/VOLUNTEER_PREFLIGHT_CHECKLIST.md`.

## Krok 1. Przygotuj fork

1. Otworz repo upstream `StrazPrzyszlosci/STRAZ_PRZYSZLOSCI`.
2. Utworz albo odswiez swoj fork.
3. Upewnij sie, ze mozesz pushowac do swojego forka przez PAT.

## Wariant lokalny: dry-run przed prawdziwym Kaggle runem

Zanim wolontariusz odpali prawdziwy notebook na `Kaggle`, maintainer albo lokalny agent moze wykonac suchy przebieg kontraktu packa:

```bash
python3 PROJEKTY/13_baza_czesci_recykling/scripts/dry_run_execution_pack.py
```

Ten dry-run:

- nie zuzywa sekretow wolontariusza ani zasobow `Kaggle`,
- buduje lokalny raport walidacyjny packa,
- generuje szkic PR oraz rekord `Run` i `Artifact` dla suchego przebiegu,
- pokazuje, czy kontrakt artefaktow i provenance jest juz gotowy do publicznego uruchomienia.

## Krok 2. Importuj notebook do Kaggle

1. Otworz `Kaggle`.
2. Utworz nowy notebook przez import pliku `youtube-databaseparts.ipynb`.
3. Przed uruchomieniem uzupelnij w komorce konfiguracyjnej:
   - `FORK_OWNER`
   - `GIT_USER_NAME`
   - `GIT_USER_EMAIL`
4. Nie zostawiaj placeholderow ani danych innej osoby.

## Krok 3. Ustaw sekrety

Dodaj w `Kaggle Secrets`:

- `GITHUB_PAT`
- `YOUTUBE_API_KEY`
- `GEMINI_API_KEY`

Notebook powinien uzyc tylko tych sekretow i tylko do deklarowanego celu packa.

## Krok 4. Uruchom notebook

1. Uruchom komorki po kolei.
2. Poczekaj na wygenerowanie plikow w `autonomous_test/`.
3. Sprawdz, czy notebook wygenerowal:
   - `processed_videos.json`
   - `results/test_db.jsonl`
   - `results/inventree_import.jsonl`
   - `results/ecoEDA_inventory.csv`
   - `reports/last_run_summary.md`
   - `reports/rebuild_autonomous_outputs_report.md`
   - `reports/rebuild_autonomous_outputs_skipped.jsonl`
4. Na koncu notebook powinien wypisac:
   - `run_id`
   - `run_ref`
   - `run_record_ref`

Jesli ktorys plik nie powstal, zatrzymaj sie i opisz to w raporcie runu oraz PR.

## Krok 5. Zweryfikuj wynik przed pushem

Przed pushem sprawdz:

- czy branch jest nowy i nalezy do Twojego forka
- czy commit author wskazuje Ciebie albo adres `noreply`
- czy raport runu opisuje zakres danych i known issues
- czy raport rebuild wyjasnia, jakie rekordy weszly do `inventree_import.jsonl` i `ecoEDA_inventory.csv`
- czy log skipped records jest spojny z raportem rebuild i nie ukrywa masowego odrzucania danych
- czy w artefaktach nie ma sekretow, plikow tymczasowych ani pobranych filmow

## Krok 6. Push do forka

Notebook powinien:

- wywolac `scripts/finalize_execution_pack_run.py`,
- zapisac kanoniczny rekord `Run` w `execution_packs/.../records/`,
- utworzyc branch o nazwie podobnej do `pack-project13-kaggle-enrichment-<timestamp>`
- dodac tylko artefakty review-ready
- wypchnac branch do `origin`, czyli do Twojego forka

Upstream nie powinien byc celem pushu z poziomu notebooka.

## Krok 7. Otworz PR

1. Na GitHubie otworz PR z brancha forka do `StrazPrzyszlosci/STRAZ_PRZYSZLOSCI`.
2. Skopiuj tresc z `PR_TEMPLATE.md`.
3. Wklej `run_id`, `run_ref` i link do notebooka Kaggle lub identyfikator runu.
4. Dolacz ograniczenia i znane problemy.

## Krok 8. Dopnij `Artifact` record po otwarciu PR

Notebook powinien juz automatycznie zapisac `Run record` oraz trwaly `run context` w pliku `last_pack_run_context.json`. Ten plik zawiera wszystkie metadane potrzebne do dopiecia `Artifact` bez recznego rekonstruowania provenance z logow.

Najprostszy sposob dopiecia `Artifact` - z uzyciem domyslnego run context:

```bash
python3 PROJEKTY/13_baza_czesci_recykling/scripts/attach_pr_artifact_record.py \
  --pr-url https://github.com/StrazPrzyszlosci/STRAZ_PRZYSZLOSCI/pull/<numer>
```

Helper automatycznie uzyje `last_pack_run_context.json` z domyslnej sciezki.

Jesli chcesz wskazac inny plik run context:

```bash
python3 PROJEKTY/13_baza_czesci_recykling/scripts/attach_pr_artifact_record.py \
  --run-context PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/last_pack_run_context.json \
  --pr-url https://github.com/StrazPrzyszlosci/STRAZ_PRZYSZLOSCI/pull/<numer>
```

Alternatywnie, z jawnym `run_id`:

```bash
python3 PROJEKTY/13_baza_czesci_recykling/scripts/attach_pr_artifact_record.py \
  --run-id <run-id-z-logu-notebooka> \
  --pr-url https://github.com/StrazPrzyszlosci/STRAZ_PRZYSZLOSCI/pull/<numer>
```

Lub przez autodiscovery po fork owner:

```bash
python3 PROJEKTY/13_baza_czesci_recykling/scripts/attach_pr_artifact_record.py \
  --fork-owner <twoj-login-github> \
  --pr-url https://github.com/StrazPrzyszlosci/STRAZ_PRZYSZLOSCI/pull/<numer>
```

Helper zapisze rekord `Artifact` w katalogu:

- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-kaggle-enrichment-01/records/`

## Krok 9. Czego nie robic

- nie pushuj bezposrednio do upstream
- nie commituj sekretow ani pelnych URL-i z tokenem
- nie podmieniaj autora commita na maintainera lub inna osobe
- nie promuj wynikow bez raportu runu i jawnego PR

## Krok 10. Co zrobic, gdy cos pojdzie nie tak

Jesli notebook zawiesi sie, zwroci blad albo wynik bedzie pusty:

1. Przeczytaj `PROJEKTY/13_baza_czesci_recykling/docs/VOLUNTEER_FALLBACK_GUIDE.md`.
2. Jesli nie wiesz, co zrobic, przerwij i zglos problem przez GitHub Issue z labelka `volunteer-support`.
3. Mozesz przerwac w dowolnym momencie — to jest dobrowolna praca.

Warunki udzialu sa opisane w `PROJEKTY/13_baza_czesci_recykling/docs/VOLUNTEER_TERMS_OF_PARTICIPATION.md`. Uruchomienie notebooka oznacza, ze znasz i akceptujesz te warunki.

## Minimalne kryterium sukcesu

Pack jest wykonany poprawnie, gdy:

- notebook przechodzi end-to-end na koncie wolontariusza
- wynik laduje na branchu w jego forku
- powstaje raport runu
- PR daje sie zreviewowac bez recznego odtwarzania calego przebiegu
