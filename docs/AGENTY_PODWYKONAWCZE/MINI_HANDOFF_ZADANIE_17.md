# Mini-Handoff Zadanie 17

## Co zostalo zrobione

Domkniety reviewer-ready packet dla disputed rekordow z verification. 30 disputed rekordow nie jest juz surowym logiem bez dalszego rozroznienia — kazdy ma jawna kategorie triage i zalecana akcje downstream.

### Nowa komenda `triage`

Dodano do `verify_candidates.py` komende `triage`, ktora klasyfikuje kazdy disputed rekord do jednej z 4 kategorii:

- `likely_confirmed` (14) — wysoka confidence MPN, niski disagreement; bezpieczny do auto-promote po review progow
- `ocr_needed` (7) — OCR frame check moglby rozstrzygnac; wymaga GEMINI_API_KEY
- `manual_review` (2) — human reviewer potrzebny; brak automatycznej sciezki
- `threshold_tuning` (7) — rekord powinien byc odrzucony/przekategoryzowany przez lepsze heurystyki MPN

### Triage indicators

Kazdy disputed rekord dostaje tez liste `triage_indicators`, np.:
- `full_model_string_not_mpn` — pelny napis z etykiety, nie sam MPN
- `date_code_in_part_number` — data kod w polu part_number
- `comma_separated_list` — lista designatorow z przecinkami
- `patent_number_in_part_number` — numer patentu w polu part_number
- `model_label_not_mpn` — napis "MODEL: ..."
- `board_model_number` — numer modelu plyty (BN44-...)
- `custom_wound_transformer_no_datasheet` — transformator bez datasheetu
- `enrichment_v2_with_video_source` — enrichment v2 z dostepnym video do OCR
- `video_source_available_for_ocr` — video dostepne, OCR mozliwy

### Pole `recommended_action`

Kazdy rekord triage dostaje `recommended_action`:
- `likely_confirmed` → `auto_promote: safe to promote to confirmed after threshold adjustment review`
- `ocr_needed` → `run_ocr_check` (gdy GEMINI_API_KEY dostepny) albo `await_ocr` (gdy nie)
- `manual_review` → `manual_review: human reviewer needed`
- `threshold_tuning` → `adjust_scoring_rules: record should be rejected or recategorized by improved MPN heuristics`

## Jakie pliki zmieniono

Zmienione:
- `PROJEKTY/13_baza_czesci_recykling/scripts/verify_candidates.py` — dodano: `classify_disputed_triage()`, `_recommended_action()`, `cmd_triage()`, zaktualizowano `cmd_report()` (sekcja triage), `cmd_run()` (krok triage w pipeline), `main()` (komenda triage)
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-kaggle-verification-01/RUNBOOK.md` — dodano: sekcja triage, opis kategorii, zaktualizowany przeplyw, output contract, blokery

Wygenerowane artefakty:
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/verification_triage.jsonl` — 30 disputed rekordow z triage
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/verification_report.md` — zaktualizowany z sekcja triage
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/verification_scored.jsonl` — zaktualizowany z polem `triage`
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/results/test_db_verified.jsonl` — zaktualizowany z polem `triage` dla disputed
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/verification_disagreements.jsonl` — zaktualizowany z polem `triage`

## Jakie komendy walidacyjne przeszly

- `python3 -m py_compile PROJEKTY/13_baza_czesci_recykling/scripts/verify_candidates.py` — OK
- `python3 PROJEKTY/13_baza_czesci_recykling/scripts/verify_candidates.py dry-run` — OK (82 kandydatow, 30 disputed z triage, 0 bledow)
- `python3 PROJEKTY/13_baza_czesci_recykling/scripts/verify_candidates.py run` (bez GEMINI_API_KEY) — OK, triage dziala, OCR skipowany
- `git diff --check` — OK

## Jak rozdzielono disputed przypadki

| Kategoria | Count | Przyklady |
|-----------|-------|-----------|
| likely_confirmed | 14 | M425R1GB4BB0-CWM0D, M51413ASP, BD82HM55 SLGZR, LDF-12V16W, V17081 |
| ocr_needed | 7 | 3336220400007, UE50MU6102KXXH, LF80537, TS8121K, BD243C, QHA001249, 1244-2 |
| manual_review | 2 | BN44-00213A (board model), QHAD01249 (custom transformer) |
| threshold_tuning | 7 | Lenovo NOK... (full model string), PATENT #..., 20-Sep-11 (date code), RV41,CV541... (designator list), MODEL: HK9 |

## Co wymaga OCR

7 rekordow `ocr_needed` czeka na OCR check przez GEMINI_API_KEY. Z nich:
- 4 maja enrichment v2 z `verification_raw` (LF80537, TS8121K, BD243C, QHA001249)
- 3 maja tylko video source bez enrichment v2 (3336220400007, UE50MU6102KXXH, 1244-2)

Gdy GEMINI_API_KEY bedzie dostepny:
```bash
GEMINI_API_KEY=... python3 scripts/verify_candidates.py ocr-check
```

## Czy potrzebny jest tuning progow

Tak. 7 rekordow `threshold_tuning` wskazuje na konkretne luki w heurystykach MPN:
1. `full_model_string_not_mpn` — rekord z calym napisem z etykiety zamiast samego MPN; trzeba odrzucac wieloczesciowe napisy z "NOK" i kodami kreskowymi
2. `date_code_in_part_number` — daty produkcji (np. "20-Sep-11 0756 BOM:01") powinny byc odrzucane przez pattern
3. `comma_separated_list` — listy designatorow z przecinkami (np. "RV41, CV541, CV611, R4082...") juz sa wychwytywane przez `MPN_REJECTION_PATTERNS` przy `"^[A-Z]\d{1,3}([,\s]+[A-Z]\d{1,3})+$"`, ale pattern nie lapie wariantow z wieloma kodami po przecinku
4. `patent_number_in_part_number` — napisy z "PATENT #" powinny byc odrzucane
5. `model_label_not_mpn` — "MODEL: HK9" to nie MPN

Rekomendacja: dodac do `MPN_REJECTION_PATTERNS` patterny dla date codes, patent numbers i model labels.

## Co nadal blokuje przejscie do curation

1. **14 rekordow `likely_confirmed`** — sa bezpieczne do promocji, ale wymagaja jawnej decyzji o zmianie progu `disputed -> confirmed` przed wejsciem do curation
2. **7 rekordow `ocr_needed`** — bez OCR check ich status pozostaje disputed; jesli curation ma przyjac tylko `confirmed`, te rekordy nie wejda
3. **2 rekordy `manual_review`** — BN44-00213A (board model) i QHAD01249 (custom transformer) wymagaja recznej decyzji czy board model i custom part number sa akceptowalne jako MPN
4. **7 rekordow `threshold_tuning`** — te powinny byc odrzucone przez poprawione heurystyki, a nie wchodzic do curation jako disputed

Najszybsza sciezka do odblokowania curation: promowac `likely_confirmed` do `confirmed` (potencjalnie 9+14=23 confirmed), odrzucic `threshold_tuning` do `rejected`, i zostawic `ocr_needed` + `manual_review` jako disputed w snapshotcie.

## Co powinien zrobic kolejny wykonawca

- Jesli GEMINI_API_KEY jest dostepny: uruchomic `python3 scripts/verify_candidates.py ocr-check` dla 7 rekordow `ocr_needed`
- Zdecydowac o promocji 14 `likely_confirmed` do confirmed (wymaga zmiany progu w `assign_verification_status` albo recznej akceptacji)
- Dodac patterny do `MPN_REJECTION_PATTERNS` dla date codes, patent numbers, model labels (zobacz `threshold_tuning` indicators)
- Uruchomic curation: `python3 scripts/curate_candidates.py review --snapshot autonomous_test/results/test_db_verified.jsonl`
