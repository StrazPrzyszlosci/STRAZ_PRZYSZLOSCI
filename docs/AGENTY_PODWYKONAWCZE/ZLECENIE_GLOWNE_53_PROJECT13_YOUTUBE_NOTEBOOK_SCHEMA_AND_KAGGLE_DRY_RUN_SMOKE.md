# Zlecenie Glowne 53 Project13 YouTube Notebook Schema And Kaggle Dry Run Smoke

## 1. Misja zadania

Sprawdzic, czy `youtube-databaseparts.ipynb` po poprawkach zapisuje rekordy zgodne z baza repo i `verify_candidates.py`, szczegolnie pola `verification`, `datasheet_url`, `footprint`, `pinout`, `yt_link`, `source_video`.

## 2. Read First

- `docs/AGENTY_PODWYKONAWCZE/ODBIOR_PORTFELA_12_ZADAN_46_50_2026-04-30.md`
- `PROJEKTY/13_baza_czesci_recykling/youtube-databaseparts.ipynb`
- `PROJEKTY/13_baza_czesci_recykling/scripts/verify_candidates.py`
- `PROJEKTY/13_baza_czesci_recykling/scripts/summarize_kaggle_run.py`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-kaggle-enrichment-01/manifest.json`

## 3. Write Scope

- `PROJEKTY/13_baza_czesci_recykling/youtube-databaseparts.ipynb`
- `tests/` dla lekkiego schema regression test, jesli potrzebny
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/youtube_notebook_schema_receipt_*.json`
- `docs/AGENTY_PODWYKONAWCZE/MINI_HANDOFF_ZADANIE_53.md`

## 4. Deliverables

- Fixture albo dry-run receipt potwierdzajacy, ze `save_result()` zapisuje `verification`, nie tylko `verification_raw`.
- Potwierdzenie, ze `datasheet_url` jest rzeczywistym PDF URL, gdy PDF pobrano, albo bezpiecznym fallback search URL.
- Potwierdzenie, ze stare outputy notebooka nie wrocily do commita.
- Mini-handoff.

## 5. Acceptance Criteria

- Test nie wymaga realnego `GEMINI_API_KEY`, jesli jest tylko schema fixture.
- Jesli robisz live Kaggle run, ogranicz do jednego filmu albo jednego fixture video.
- `test_db.jsonl` musi byc parsowalny JSONL i zgodny z `verify_candidates.py`.
- Nie wypychaj zmian bez forka wolontariusza i `finalize_execution_pack_run.py`.
- Nie zapisuj sekretow ani tokenow do notebook outputow.

## 6. Walidacja

- AST parse code cells notebooka
- `python3 PROJEKTY/13_baza_czesci_recykling/scripts/summarize_kaggle_run.py --base-dir PROJEKTY/13_baza_czesci_recykling/autonomous_test`
- JSONL parse dla nowych rekordow
- `git diff --check`

