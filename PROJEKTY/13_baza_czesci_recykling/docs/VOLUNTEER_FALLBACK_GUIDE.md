# Fallback Guide Dla Wolontariusza

## Cel

Ten dokument mowi Ci, co zrobic, gdy cos pojdzie nie tak podczas uruchamiania notebooka Kaggle dla `Project 13`.

Nie musisz znac calego projektu. Wystarczy, ze wiesz, gdzie sie zatrzymac i jak zglosic problem.

---

## Sytuacja 1: Notebook zawiesil sie albo dziala zbyt dlugo

**Co sie dzieje:** Komorka notebooka nie konczy sie po rozsadnym czasie (np. wiecej niz 15 minut na pojedyncza komorke).

**Co zrobic:**

1. **Nie restartuj na sile.** Zapisz, co juz powstalo.
2. Sprawdz, czy to problem z limitem Kaggle: `Kernel -> Interrupt`, potem `Kernel -> Restart & Clear Output`.
3. Jesli restart pomogl, sproboj uruchomic ponownie od przerwanej komorki.
4. Jesli nie pomogl, przejdz do [Sytuacji 4](#sytuacja-4-nie-wiesz-co-zrobic-dalej).

**Wazne:** Twoj czas i limity Kaggle sa wazniejsze niz wykonanie packa do konca. Czesciowy wynik jest lepszy niz zaden.

---

## Sytuacja 2: Blad w komorce — czerwony output albo wyjatek

**Co sie dzieje:** Komorka rzuca wyjatek, czerwony tekst albo niespodziewany blad.

**Co zrobic:**

1. Przeczytaj tresc bledu. Czesto zawiera wskazowke (brak sekretu, zly format, brak dostepu do API).
2. Sprawdz, czy wszystkie sekrety sa ustawione: `GITHUB_PAT`, `YOUTUBE_API_KEY`, `GEMINI_API_KEY`.
3. Sprawdz, czy `FORK_OWNER`, `GIT_USER_NAME` i `GIT_USER_EMAIL` w komorce konfiguracyjnej sa poprawne.
4. Jesli blad dotyczy API (quota, 403, 429): to nie Twoj blad. Zapisz output, zatrzymaj notebook i zglos problem.
5. Jesli blad dotyczy wersji pakietu: zapisz pelny traceback i zglos problem.

**Wazne:** Nie musisz sam naprawiac bledow technicznych. Twoim zadaniem jest zreportowac je, a nie debugowac srodowisko Kaggle.

---

## Sytuacja 3: Brak artefaktow albo pusty wynik

**Co sie dzieje:** Notebook zakonczyl sie bez bledu, ale brakuje oczekiwanych plikow albo sa puste.

**Co zrobic:**

1. Sprawdz, ktore pliki powstaly, a ktore nie. Lista oczekiwanych artefaktow jest w runbooku (krok 4).
2. Jesli powstal `reports/last_run_summary.md`, przejrz go — moze zawierac wyjasnienie.
3. Jesli `processed_videos.json` jest pusty: prawdopodobnie problem z `YOUTUBE_API_KEY` albo quota.
4. Nie probuj recznie dopisywac danych do artefaktow.
5. Otworz PR z tym, co jest, i opisz braki w sekcji `Known Issues`.

**Wazne:** Pusty wynik jest tez wynikiem. Pokazuje, ze cos blokuje pipeline, i to jest cenna informacja.

---

## Sytuacja 4: Nie wiesz, co zrobic dalej

**Co zrobic:**

1. **Przerwij.** Nie kontynuuj na sile.
2. Zapisz stan rzeczy: screenshot, output komorek, tresc bledu — cokolwiek, co masz.
3. Zglos problem (patrz nizej).
4. Nie martw sie, ze cos "zepsules". Repo jest zabezpieczone: Twoj fork jest Twoja przestrzenia, a upstream nie dostaje zmian bez review.

---

## Jak zglosic problem

### Opcja A: Issue na GitHub (rekomendowana)

1. Przejdz do `https://github.com/StrazPrzyszlosci/STRAZ_PRZYSZLOSCI/issues`.
2. Kliknij `New Issue`.
3. Wybierz szablon `Volunteer Problem Report`.
4. Wypelnij pola: krok runbooka, opis problemu, co juz zrobiles, output/blad (bez sekretow).

### Opcja B: Komentarz w PR

Jesli juz otworzyles PR, dodaj komentarz z opisem problemu. Reviewer zobaczy to podczas review.

### Opcja C: Kontakt bezposredni (do_potwierdzenia)

Jesli maintainer udostepni kanal kontaktowy (Discord, Telegram, albo inny), bedzie on wskazany tutaj:

- **Kanal eskalacji:** `do_potwierdzenia` — obecnie rekomendacja to GitHub Issue z labelka `volunteer-support`
- **Czas odpowiedzi:** cel to 48h roboczych, ale na obecnym etapie moze byc dluzszy

---

## Mozesz przerwac w dowolnym momencie

To jest dobrowolna praca. Masz prawo:

- przerwac uruchomienie w dowolnym momencie,
- nie otwierac PR, jesli nie jestes zadowolony z wyniku,
- zglosic problem i czekac na pomoc,
- odmowic dalszej pracy bez podawania powodu.

Twoj fork jest Twoja przestrzenia. Nic nie trafia do upstream bez Twojego PR i bez review.

---

## Zrodla

- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-kaggle-enrichment-01/RUNBOOK.md`
- `PROJEKTY/13_baza_czesci_recykling/docs/PUBLIC_VOLUNTEER_RUN_READINESS.md`
- `PROJEKTY/13_baza_czesci_recykling/docs/VOLUNTEER_TERMS_OF_PARTICIPATION.md`
