# Wolontariusze Gotowe Przydzialy

## Cel dokumentu

To jest kanoniczny punkt wejscia dla nowego wolontariusza i jego lokalnego agenta.

Nowy wolontariusz nie powinien zaczynac od pustej kartki, od przegladania calego repo ani od katalogu `docs/AGENTY_PODWYKONAWCZE/`.

Lokalny agent ma wejsc tutaj, wybrac pierwszy pasujacy przydzial i poprowadzic wolontariusza dalej.

## Zasada nadrzedna

- wolontariusz ma dostac gotowy przydzial, a nie sam wymyslac sobie zadanie
- lokalny agent ma przeczytac repo i przejac ciezar interpretacji instrukcji
- wolontariusz nie musi pisac od zera promptu, briefu ani planu pracy
- `docs/AGENTY_PODWYKONAWCZE/` nie jest onboardingiem dla wolontariuszy

## Rozdzial dwoch torow

- `docs/WOLONTARIUSZE_GOTOWE_PRZYDZIALY.md`: publiczna sciezka wejscia dla wolontariuszy z agentami
- `docs/AGENTY_PODWYKONAWCZE/`: wewnetrzne zlecenia dla agentow operatora repo, wykorzystywane wtedy, gdy brakuje realnych wolontariuszy

## Regula przypisania dla lokalnego agenta

1. Sprawdz, jakie zasoby ma wolontariusz.
2. Wybierz pierwszy przydzial z tej listy, ktorego wymagania sa spelnione.
3. Poprowadz wolontariusza krok po kroku przez materialy i czynnosci wykonawcze.
4. To agent przygotowuje `Issue`, `PR` albo krotki handoff z wykonania. Wolontariusz ma glownie decydowac, czy chce uruchomic dany krok i zuzyc swoje zasoby.

## Gotowe przydzialy

### `VOL-P13-01` Realny run `Project 13` na `Kaggle`

- Kiedy przydzielac:
- gdy wolontariusz ma konto `GitHub`, konto `Kaggle`, lokalnego agenta i gotowosc do ustawienia wlasnych sekretow
- Minimalne zasoby:
- fork repo
- `Kaggle`
- `GITHUB_PAT`
- `YOUTUBE_API_KEY`
- `GEMINI_API_KEY`
- Czytaj najpierw:
- `PROJEKTY/13_baza_czesci_recykling/docs/CANARY_PILOT_PACKET.md`
- `PROJEKTY/13_baza_czesci_recykling/docs/VOLUNTEER_PREFLIGHT_CHECKLIST.md`
- `PROJEKTY/13_baza_czesci_recykling/README.md` (sekcja "Jak ustawic sekrety")
- `PROJEKTY/13_baza_czesci_recykling/.env.example`
- `PROJEKTY/13_baza_czesci_recykling/docs/MODEL_WOLONTARIACKICH_NOTEBOOKOW_KAGGLE.md`
- `PROJEKTY/13_baza_czesci_recykling/docs/VOLUNTEER_TERMS_OF_PARTICIPATION.md`
- `PROJEKTY/13_baza_czesci_recykling/docs/VOLUNTEER_FALLBACK_GUIDE.md`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-kaggle-enrichment-01/RUNBOOK.md`
- Wynik koncowy:
- branch i `PR` z forka wolontariusza do upstream dla packa `pack-project13-kaggle-enrichment-01`
- Rola lokalnego agenta:
- uruchomic pre-flight check: `python3 PROJEKTY/13_baza_czesci_recykling/scripts/preflight_check.py`
- przeprowadzic setup sekretow (instrukcja w `PROJEKTY/13_baza_czesci_recykling/README.md` sekcja "Jak ustawic sekrety")
- pilnowac bezpieczenstwa sekretow
- przygotowac opis `PR` i dopiecie `Artifact`
- pilnowac stop conditions z `CANARY_PILOT_PACKET.md` — wolontariusz ma prawo przerwac w dowolnym momencie

### `VOL-P13-02` Lokalny dry-run i audyt tarcia `Project 13`

- Kiedy przydzielac:
- gdy wolontariusz ma laptop, lokalnego agenta i srodowisko `Python`, ale nie ma jeszcze `Kaggle` albo kluczy API
- Minimalne zasoby:
- lokalny shell
- `python3`
- fork repo albo lokalna kopia
- Czytaj najpierw:
- `PROJEKTY/13_baza_czesci_recykling/docs/CANARY_PILOT_PACKET.md`
- `PROJEKTY/13_baza_czesci_recykling/docs/VOLUNTEER_PREFLIGHT_CHECKLIST.md`
- `PROJEKTY/13_baza_czesci_recykling/README.md`
  - `PROJEKTY/13_baza_czesci_recykling/docs/PUBLIC_VOLUNTEER_RUN_READINESS.md`
  - `PROJEKTY/13_baza_czesci_recykling/docs/VOLUNTEER_FALLBACK_GUIDE.md`
  - `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-kaggle-enrichment-01/RUNBOOK.md`
- Wynik koncowy:
  - `Issue` albo `PR` z tarciem onboardingowym, niejasnymi krokami i wynikiem lokalnego dry-runu
- Rola lokalnego agenta:
  - uruchomic `dry_run_execution_pack.py`
  - przejsc z wolontariuszem runbook linia po linii
  - przygotowac raport tarcia bez wymagania, by wolontariusz pisal go recznie

### `VOL-P13-03` Smoke test wejscia przez onboarding i Telegram

- Kiedy przydzielac:
  - gdy wolontariusz nie ma jeszcze gotowosci do runu technicznego, ale chce pomoc w uproszczeniu wejscia do inicjatywy
- Minimalne zasoby:
  - lokalny agent
  - dostep do repo
  - opcjonalnie `Telegram`
- Czytaj najpierw:
  - `README.md`
  - `docs/ARCHITEKTURA_ONBOARDINGU.md`
  - `data/onboarding/straznik_rekomendator_v1.json`
- Wynik koncowy:
  - `Issue` albo `PR` z punktami tarcia w onboardingu, rekomendowanym uproszczeniem komunikatow i ocena, czy przydzial byl natychmiast jasny
- Rola lokalnego agenta:
  - zasymulowac wejscie nowej osoby
  - wskazac, czy bot i repo prowadza do konkretnego przydzialu bez dodatkowego tlumaczenia

## Domyslny wybor dla lokalnego agenta

- jesli wolontariusz ma `Kaggle` i klucze API, zacznij od `VOL-P13-01`
- jesli nie ma jeszcze `Kaggle` albo sekretow, ale ma lokalne `Python`, zacznij od `VOL-P13-02`
- jesli ma glownie czas na wejscie, czytanie i test uproszczonego onboardingu, zacznij od `VOL-P13-03`

## Czego nie robic

- nie kieruj wolontariusza do `docs/AGENTY_PODWYKONAWCZE/`
- nie pros wolontariusza, zeby sam od zera wymyslil zadanie
- nie pros o push do upstream
- nie pros o ustawianie sekretow poza jego wlasnym kontem
- nie traktuj braku `Kaggle` jako braku sensownego wkladu
