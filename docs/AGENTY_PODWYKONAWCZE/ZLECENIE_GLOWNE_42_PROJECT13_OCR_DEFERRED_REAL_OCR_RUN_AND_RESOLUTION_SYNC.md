# Zlecenie Glowne 42 Project13 OCR Deferred Real OCR Run And Resolution Sync

## 1. Misja zadania

Wykonaj realny OCR run dla `7` cases `ocr_needed`, korzystajac z `ocr-selector` i `OCR_DEFERRED_CASE_SELECTOR_AND_PROMPT_PACKET.md`.

To zadanie wymaga prawdziwego `GEMINI_API_KEY`. Bez klucza nie wolno oznaczac zadnego case jako rozstrzygnietego.

## 2. Wyzszy cel organizacji

Po `36` kazdy OCR case jest juz chirurgicznie opisany.
Teraz trzeba zamienic selector w realny wynik weryfikacji albo jawny blocker receipt.

## 3. Read First

- `docs/HANDOFF_DLA_NASTEPNEGO_AGENTA_2026-04-29.md`
- `docs/AGENTY_PODWYKONAWCZE/MINI_HANDOFF_ZADANIE_36.md`
- `PROJEKTY/13_baza_czesci_recykling/docs/OCR_DEFERRED_CASE_SELECTOR_AND_PROMPT_PACKET.md`
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/ocr_deferred_case_packet.json`
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/deferred_resolution_workpack.json`
- `PROJEKTY/13_baza_czesci_recykling/scripts/verify_candidates.py`

## 4. Write Scope

- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/`
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/results/`
- `docs/AGENTY_PODWYKONAWCZE/MINI_HANDOFF_ZADANIE_42.md`

## 5. Deliverables

- realny OCR run dla pojedynczego case, grupy cases albo wszystkich `7` OCR cases
- `ocr_run_receipt_YYYY-MM-DD.json` z wybranymi candidate_id, timestampem, wynikiem komend i lista wynikow
- odswiezone artefakty verification/status resolution, jesli pipeline je generuje
- jesli brak `GEMINI_API_KEY`: blocker receipt bez zmiany statusow
- mini-handoff z wynikiem per candidate_id

## 6. Acceptance Criteria

- zadne OCR case nie jest oznaczone jako resolved bez realnego przebiegu OCR
- `candidate_id`, `part_number` i `evidence_url` zgadzaja sie z `ocr_deferred_case_packet.json`
- wyniki `confirmed`, `rejected` i `inconclusive` sa rozdzielone
- `inconclusive` trafia do manual-review/sciezki defer, nie jest przepychane automatycznie
- po OCR uruchomiono odpowiednia walidacje pipeline albo zapisano, dlaczego nie mozna jej uruchomic

## 7. Walidacja

- `python3 PROJEKTY/13_baza_czesci_recykling/scripts/verify_candidates.py ocr-selector`
- dla wybranej grupy: `python3 PROJEKTY/13_baza_czesci_recykling/scripts/verify_candidates.py ocr-selector --group <VIDEO_URL>`
- z kluczem: `GEMINI_API_KEY=... python3 PROJEKTY/13_baza_czesci_recykling/scripts/verify_candidates.py ocr-check`
- po realnym runie: `python3 PROJEKTY/13_baza_czesci_recykling/scripts/verify_candidates.py run`
- `git diff --check`

## 8. Blokery

Brak `GEMINI_API_KEY`, quota albo dostepu do materialu zrodlowego blokuje realny OCR.
Nie obchodz tego heurystyka i nie wpisuj sztucznego `confirmed`.

## 9. Mini-handoff

Zapisz:

- ktore OCR cases uruchomiono,
- jaki byl wynik per candidate_id,
- ktore cases pozostaja `ocr_needed`,
- ktore cases wymagaja manual review,
- czy `export-gate` nadal jest blokowany przez deferred.
