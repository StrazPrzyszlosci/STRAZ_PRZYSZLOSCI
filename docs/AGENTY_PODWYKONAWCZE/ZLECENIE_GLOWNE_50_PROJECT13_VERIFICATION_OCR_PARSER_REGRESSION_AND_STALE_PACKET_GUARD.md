# Zlecenie Glowne 50 Project13 Verification OCR Parser Regression And Stale Packet Guard

## 1. Misja zadania

Dodaj regresyjna ochrone dla bledu z audytu: markdownowe `**YES**` / `**NO**` nie moze ponownie tworzyc falszywego `inconclusive`, a stare workpacki OCR nie moga pokazywac cases, gdy `status_resolution_packet.json` ma `0` deferred.

## 2. Wyzszy cel organizacji

Zadanie `42` zostalo domkniete po korekcie, ale bez testu regresyjnego ten sam blad moze wrocic przy nastepnej zmianie verification pipeline.

## 3. Read First

- `docs/AGENTY_PODWYKONAWCZE/ODBIOR_PORTFELA_11_ZADAN_41_45_2026-04-30.md`
- `docs/AGENTY_PODWYKONAWCZE/MINI_HANDOFF_ZADANIE_42.md`
- `PROJEKTY/13_baza_czesci_recykling/scripts/verify_candidates.py`
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/status_resolution_packet.json`
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/ocr_deferred_case_packet.json`

## 4. Write Scope

- `PROJEKTY/13_baza_czesci_recykling/scripts/verify_candidates.py`
- `tests/` albo nowy lekki test w odpowiednim miejscu repo
- `docs/AGENTY_PODWYKONAWCZE/MINI_HANDOFF_ZADANIE_50.md`

## 5. Deliverables

- test parsera OCR dla `YES`, `NO`, `**YES**`, `**NO**`, `Answer: YES`
- test albo smoke check dla pustego `status_resolution_packet.json`: `ocr-selector` zapisuje pusty packet zamiast starej listy
- mini-handoff z komendami testowymi

## 6. Acceptance Criteria

- test nie wymaga `GEMINI_API_KEY`
- test nie wykonuje zadnego network call
- test rozroznia `inconclusive` od markdownowego YES/NO
- `ocr_deferred_case_packet.json` po stanie `0 deferred` ma `total_ocr_cases: 0`

## 7. Walidacja

- `python3 -m py_compile PROJEKTY/13_baza_czesci_recykling/scripts/verify_candidates.py`
- nowy test regresyjny
- `python3 PROJEKTY/13_baza_czesci_recykling/scripts/verify_candidates.py deferred-workpack`
- `python3 PROJEKTY/13_baza_czesci_recykling/scripts/verify_candidates.py ocr-selector`
- `git diff --check`

## 8. Blokery

Brak frameworka testowego nie blokuje zadania. Wtedy dodaj prosty test `unittest` albo smoke script, bez zaleznosci sieciowych.

## 9. Mini-handoff

Zapisz:

- jakie przypadki parsera pokryto,
- gdzie jest test,
- jaki jest wynik `ocr-selector` przy `0 deferred`,
- czy trzeba jeszcze refaktorowac verification pipeline.
