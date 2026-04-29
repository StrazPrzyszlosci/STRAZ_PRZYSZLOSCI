# Mini Handoff Zadanie 36

## Co zostalo zrobione

1. Dodano komende `ocr-selector` do `scripts/verify_candidates.py` — chirurgiczny execution surface dla 7 OCR-deferred cases
2. Wygenerowano `ocr_deferred_case_packet.json` — stabilny artefakt z mapa `candidate_id -> evidence_url -> expected_text -> next_command`
3. Napisano `OCR_DEFERRED_CASE_SELECTOR_AND_PROMPT_PACKET.md` — instrukcja operatorska dla ruchu z `GEMINI_API_KEY`
4. Komenda `ocr-selector` wspiera 3 tryby: all / --case candidate-XXXX / --group VIDEO_URL

## Jakie pliki dotknieto

- `PROJEKTY/13_baza_czesci_recykling/scripts/verify_candidates.py` — dodano `build_ocr_case_map()`, `cmd_ocr_selector()`, flagi `--case` i `--group`, rejestracja komendy
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/ocr_deferred_case_packet.json` — nowy artefakt (wygenerowany przez `ocr-selector`)
- `PROJEKTY/13_baza_czesci_recykling/docs/OCR_DEFERRED_CASE_SELECTOR_AND_PROMPT_PACKET.md` — nowy dokument operatorski

## Co zweryfikowano

- `python3 -m py_compile` — PASS
- `ocr-selector` bez filtra — wyswietla 7 cases z poprawnym mapowaniem
- `ocr-selector --case candidate-0073` — poprawnie filtruje pojedynczy case
- `ocr-selector --group "https://www.youtube.com/watch?v=WRKu1dDCVEw"` — poprawnie grupuje 2 cases z tego samego wideo
- Counts: 7 ocr_needed vs `deferred_resolution_workpack.json` — ZGODNE
- candidate_id, part_number, evidence_url — ZGODNE z packetem zadania 30

## Co zostalo otwarte

- Zadny OCR case nie zostal oznaczony jako rozwiazany — prawidlowo, brak GEMINI_API_KEY
- 2 cases manual_review (candidate-0076, candidate-0077) nie sa w scope tego packetu — sa w `deferred_resolution_workpack.json` pod `manual_review`
- Po pojawieniu sie GEMINI_API_KEY: uruchomic `ocr-check`, przejrzec wyniki, re-run pipeline
- Wyniki OCR inconclusive beda eskalowane do manual_review — wtedy lacza sie z torami candidate-0076/0077
