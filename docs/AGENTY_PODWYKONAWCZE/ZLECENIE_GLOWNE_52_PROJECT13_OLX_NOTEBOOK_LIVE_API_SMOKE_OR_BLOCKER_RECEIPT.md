# Zlecenie Glowne 52 Project13 OLX Notebook Live API Smoke Or Blocker Receipt

## 1. Misja zadania

Sprawdzic, czy `olx-oddam-za-darmo-scraper.ipynb` po poprawkach preflight/warmup/retry potrafi pobrac jedna strone OLX API. Jesli OLX blokuje IP albo Kaggle nie ma internetu, zapisac blocker receipt.

## 2. Read First

- `docs/AGENTY_PODWYKONAWCZE/ODBIOR_PORTFELA_12_ZADAN_46_50_2026-04-30.md`
- `PROJEKTY/13_baza_czesci_recykling/olx-oddam-za-darmo-scraper.ipynb`
- `cloudflare/migrations/0015_olx_parts_market.sql`

## 3. Write Scope

- `PROJEKTY/13_baza_czesci_recykling/olx-oddam-za-darmo-scraper.ipynb`
- `PROJEKTY/13_baza_czesci_recykling/olx_data/` albo Kaggle output path, jesli run testowy eksportuje fixture
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/olx_notebook_smoke_receipt_*.json`
- `docs/AGENTY_PODWYKONAWCZE/MINI_HANDOFF_ZADANIE_52.md`

## 4. Deliverables

- Smoke receipt z wynikiem `olx_preflight_host`, `warmup_olx_session`, statusem HTTP pierwszej strony i liczba ofert.
- Jesli pobrano dane: maly SQLite/JSONL/SQL smoke output i raport zgodnosci z migracja D1.
- Jesli 403/429/no internet: blocker receipt z kodem i bez dalszego scrapowania.
- Mini-handoff.

## 5. Acceptance Criteria

- Nie uruchamiaj pelnego scrapingu, dopoki one-page smoke nie przejdzie.
- Nie obchodz blokad OLX agresywnym proxy ani wysokim rate limit.
- `Accept` dla API pozostaje JSON-compatible.
- Non-JSON odpowiedz ma byc jawnie raportowana, nie parsowana jako pusta lista.
- SQL export musi byc zgodny z tabela z migracji `0015_olx_parts_market.sql`.

## 6. Walidacja

- AST parse code cells notebooka
- `python3 -m json.tool <smoke_receipt>.json`
- jesli powstal SQL: kontrola cudzyslowow i `INSERT` bez sekretow
- `git diff --check`

