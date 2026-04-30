# Zlecenie Glowne 51 Project13 Datasheet Notebook Real PDF Smoke And D1 Export Sanity

## 1. Misja zadania

Uruchom kontrolowany smoke test `datasheet-analyzer.ipynb` po poprawkach pobierania PDF. Celem jest potwierdzenie, ze notebook pobiera prawdziwe pliki PDF, a nie HTML/redirect/error page.

## 2. Read First

- `docs/AGENTY_PODWYKONAWCZE/ODBIOR_PORTFELA_12_ZADAN_46_50_2026-04-30.md`
- `PROJEKTY/13_baza_czesci_recykling/datasheet-analyzer.ipynb`
- `cloudflare/migrations/0013_datasheets_cache.sql`

## 3. Write Scope

- `PROJEKTY/13_baza_czesci_recykling/datasheet-analyzer.ipynb`
- `PROJEKTY/13_baza_czesci_recykling/datasheets/` albo Kaggle output path, jesli run jest lokalny testowy
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/datasheet_notebook_smoke_receipt_*.json`
- `docs/AGENTY_PODWYKONAWCZE/MINI_HANDOFF_ZADANIE_51.md`

## 4. Deliverables

- Smoke receipt z lista testowanych part numbers, URL, source, size, SHA-256 i wynikiem walidacji `%PDF`.
- Jesli Gemini key jest dostepny: co najmniej 1 analizowany datasheet i eksport JSONL/SQL.
- Jesli Gemini key nie jest dostepny: PDF-only smoke receipt, bez udawania AI analysis.
- Mini-handoff.

## 5. Acceptance Criteria

- Test obejmuje minimum 5 seed parts, w tym `NE555`, `LM7805`, `ATmega328P`, `ESP8266` albo jawny blocker sieciowy.
- Kazdy zaliczony plik zaczyna sie od `%PDF` albo ma wiarygodny `Content-Type` PDF.
- DuckDuckGo query nie wraca do starego buga `?q=q=...`.
- Nie zapisuj HTML jako `.pdf`.
- Sekrety Gemini nie trafiaja do repo.

## 6. Walidacja

- `python3 -m json.tool <smoke_receipt>.json`
- AST parse code cells notebooka
- kontrola rozmiarow i hashy PDF w receipt
- `git diff --check`

