# Handoff po audycie izolowanego klona OpenClaw

Data: 2026-04-29  
Repo glowne: `/home/krzysiek/Dokumenty/INFO_GROUP/STRAZ_POLSKIEGO_Ai`  
Klon agenta: `/home/krzysiek/.openclaw/workspace/STRAZ_PRZYSZLOSCI`

## 1. Stan porownania

- Repo glowne bylo na `bdb6a2b` (`feat: sub-agent task portfolio 10 and canary go-live readiness baseline`).
- Klon agenta byl na starszym `a605de7` i mial niecommitowane zmiany.
- Glowne repo mialo dodatkowe nie sledzone dokumenty portfela `11` / zadan `41-46`; nie byly ruszane i nadal czekaja na wykonanie.
- Zmiany agenta byly wartosciowe, ale nie nadawaly sie do prostego skopiowania, bo kolidowaly z nowszym stanem `telegram_ai.js` i zawieraly bledy w notebooku oraz w sanitizacji tekstu Telegrama.

## 2. Co zostalo przyjete i poprawione

- Przyjeto centralny shield anti-prompt-injection jako `cloudflare/src/input_sanitizer.js`.
- Podpieto sanitizer do glownej rozmowy AI w `cloudflare/src/telegram_ai.js`.
- Podpieto sanitizer do finalnej analizy datasheet RAG w kanonicznym flow `telegram_ai.js`.
- Dodano ostrzezenia anti-injection do promptow vision dla zdjec czesci/urzadzen.
- Dodano lekka analize PDF pod katem ukrytego tekstu i audyt `pdf_hidden_content`.
- Dodano inline fallback schemy `datasheets` oraz kolumne `package` dla `recycled_parts` i `recycled_part_master`.
- Dodano migracje D1 `0013_datasheets_cache.sql`, `0014_injection_audit_and_package.sql`, `0015_olx_parts_market.sql`.
- Przyjeto notebooki:
  - `PROJEKTY/13_baza_czesci_recykling/datasheet-analyzer.ipynb`
  - `PROJEKTY/13_baza_czesci_recykling/olx-oddam-za-darmo-scraper.ipynb`
- Poprawiono notebook datasheet: usunieto `pip install hashlib`, zmieniono `parameters_json` na `parameters`, naprawiono generowanie SQL.
- Poprawiono notebook OLX: dodano bezpieczniejsze renderowanie literalu SQL zamiast `repr()`.
- Dodano testy sanitizera w `cloudflare/tests/input_sanitizer.test.mjs`.
- Przyjeto dokumenty audytu/API:
  - `PROJEKTY/00_knowledge_base/API_INVENTORY.md`
  - `docs/audit-schema-consistency-2026-04-29.md`
  - `cloudflare/raporty_zmian/2026-04-29-fix-datasheets-schema.md`

## 3. Co zostalo celowo odrzucone albo nieprzeniesione 1:1

- Nie przeniesiono zmiany agenta w `telegram_issues.js`, bo ustawiala `text` na caly obiekt `sanitizeUserInput(...)` zamiast `safeText`; to popsuloby routing wiadomosci.
- Nie przeniesiono calego starego rewrite'u `cloudflare/src/datasheet.js`, bo kanoniczny flow po nowszym commicie jest w `telegram_ai.js`.
- Nie uznano notebookow za wykonane produkcyjnie; zostaly tylko przygotowane i zwalidowane skladniowo.
- Nie otwarto export gate i nie zmieniono statusow zadan `41-46`; te zadania z aktualnego portfela nadal sa do wykonania.

## 4. Weryfikacja wykonana lokalnie

- `node --check cloudflare/src/telegram_ai.js`
- `node --check cloudflare/src/input_sanitizer.js`
- `node --check cloudflare/src/vision.js`
- `node --check cloudflare/src/datasheet.js`
- `node --test cloudflare/tests/input_sanitizer.test.mjs`
- `node --test cloudflare/tests/telegram_ai.test.mjs`
- `python3 -m unittest tests.test_cloudflare_ai_node_suite`
- `jq empty` dla obu notebookow
- `ast.parse` kodu Python z notebookow po pominieciu linii `!pip`
- `sqlite3 :memory:` z migracjami `0013`, `0014`, `0015`

`pytest` nie byl dostepny w srodowisku (`pytest: command not found`), wiec uzyto `unittest`.

## 5. Instrukcja harmonogramu notebookow

Najbezpieczniejszy model: Kaggle Scheduled Notebooks, a import do D1 dopiero po review plikow SQL.

1. W Kaggle utworz notebook z pliku `PROJEKTY/13_baza_czesci_recykling/olx-oddam-za-darmo-scraper.ipynb`.
2. Wlacz Internet w ustawieniach notebooka.
3. Ustaw schedule co `6-12h` dla OLX, bo to szybki scouting lokalnych okazji.
4. Outputy OLX beda w `/kaggle/working/olx_scraper/`: `olx_d1_import.sql`, `olx_offers_export.jsonl`, `scan_report.md`.
5. Utworz osobny notebook z `PROJEKTY/13_baza_czesci_recykling/datasheet-analyzer.ipynb`.
6. Dodaj sekrety Kaggle: `GEMINI_API_KEY`, opcjonalnie `GEMINI_API_KEY_2`.
7. Ustaw schedule nightly albo weekly dla datasheetow; na start zostaw `MAX_PARTS_PER_RUN = 50`.
8. Outputy datasheet beda w `/kaggle/working/STRAZ_PRZYSZLOSCI/datasheets/results/`.
9. Przed importem do D1 uruchom migracje:

```bash
cd cloudflare
npx wrangler d1 migrations apply fish-pond-v1 --remote
```

10. Po review SQL importuj wyniki:

```bash
npx wrangler d1 execute fish-pond-v1 --remote --file=/path/to/olx_d1_import.sql
npx wrangler d1 execute fish-pond-v1 --remote --file=/path/to/datasheets_d1_import.sql
```

Uwaga operacyjna: migracje `0013-0015` najlepiej zaaplikowac przed deployem Workera z inline fallbackiem. Jesli Worker najpierw sam doda kolumne `package`, migracja `0014` moze wymagac recznego pominiecia dwoch `ALTER TABLE ... ADD COLUMN package TEXT`.

## 6. Zadania i zalecenia dla izolowanego agenta

- Zrobic `pull/rebase` klona OpenClaw do `bdb6a2b` albo nowszego przed kolejna praca.
- Nie kopiowac calego worktree do main; przygotowywac male patche z opisem ryzyka.
- Dla kazdej zmiany JS uruchomic `node --check` i odpowiedni `node --test`.
- Nie oznaczac export gate jako open bez realnego human approval ledger i review decyzji.
- Wykonac nadal otwarte zadania z portfela `11`: `41-46`.
- Dopisac test integracyjny blokowania prompt injection w `generateChatReply`.
- Dopisac test datasheet RAG dla zablokowanego pytania i podejrzanego PDF.
- Uporzadkowac duplikacje `datasheet.js` vs kanoniczne `telegram_ai.js` albo oznaczyc stary modul jako legacy.
- Dla OLX przygotowac dopiero nastepny etap: query endpoint/bot command po tym, jak tabela `olx_*` bedzie miala realne dane.
- Aktualizowac `API_INVENTORY.md` tylko po rzeczywistym sprawdzeniu kluczy, modeli i endpointow.
- Nie zamykac zadan z poprzedniego handoffu dokumentacyjnie bez dowodu runu, raportu albo receiptu.
