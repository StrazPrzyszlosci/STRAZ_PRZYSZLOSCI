# Zlecenie Glowne 19 Project13 Volunteer Secrets Setup Guide And Env Example

## 1. Misja zadania

Uprosc onboarding wolontariusza przez publiczna instrukcje: skad wziasc `GITHUB_PAT`, `YOUTUBE_API_KEY`, `GEMINI_API_KEY`, jak wpisac je do `.env`, i jak przeniesc te same wartosci do `Kaggle Secrets`.

## 2. Wyzszy cel organizacji

To zadanie usuwa jedno z najwiekszych tarc wolontariatu: nowa osoba ma nie szukac po internecie i po repo, tylko dostac gotowa instrukcje setupu.

## 3. Read First

- `docs/HANDOFF_DLA_NASTEPNEGO_AGENTA_2026-04-24.md`
- `docs/WOLONTARIUSZE_GOTOWE_PRZYDZIALY.md`
- `PROJEKTY/13_baza_czesci_recykling/docs/PUBLIC_VOLUNTEER_RUN_READINESS.md`
- `PROJEKTY/13_baza_czesci_recykling/README.md`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-kaggle-enrichment-01/RUNBOOK.md`

## 4. Write Scope

- `PROJEKTY/13_baza_czesci_recykling/README.md`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-kaggle-enrichment-01/RUNBOOK.md`
- `docs/WOLONTARIUSZE_GOTOWE_PRZYDZIALY.md`
- ewentualnie `README.md`
- nowy plik `PROJEKTY/13_baza_czesci_recykling/.env.example`

## 5. Deliverables

- publiczna instrukcja skad wziasc kazdy klucz
- `.env.example` z poprawnymi nazwami zmiennych
- instrukcja: `.env` lokalnie -> `Kaggle Secrets` w notebooku
- aktualizacja readiness po zmianach

## 6. Acceptance Criteria

- wolontariusz wie skad wziasc `GITHUB_PAT`, `YOUTUBE_API_KEY`, `GEMINI_API_KEY`
- wolontariusz dostaje jawny format `.env`
- README albo RUNBOOK mowi, ze te same wartosci trzeba ustawic tez w `Kaggle Secrets`
- sekcja sekretow w readiness jest co najmniej lepiej domknieta niz obecne `DO POTWIERDZENIA`

## 7. Walidacja

- kontrola spojnosci miedzy `.env.example`, README i RUNBOOK.md
- `git diff --check`

## 8. Blokery

Nie linkuj wolontariusza do niejasnych, prywatnych albo niejawnych instrukcji. Jesli jakis klucz wymaga jeszcze decyzji operatora, nazwij to wprost.

## 9. Mini-handoff

Zapisz:

- gdzie dodano instrukcje setupu sekretow,
- jakie zmienne sa w `.env.example`,
- ktore pozycje readiness to domknelo,
- co nadal zostaje do potwierdzenia.
