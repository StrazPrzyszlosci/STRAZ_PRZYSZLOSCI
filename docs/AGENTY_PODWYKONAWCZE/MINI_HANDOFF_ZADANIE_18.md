# Mini-Handoff Zadanie 18

## Co zostalo zrobione

- Curation zostala uruchomiona na realnym wejsciu z verification (`test_db_verified.jsonl`), bez fallbacku na `test_db.jsonl`
- Skrypt `curate_candidates.py` zostal rozszerzony o triage-informed decisions dla disputed candidates:
  - `likely_confirmed` (14 rekordow) -> auto-promote do `accept`
  - `threshold_tuning` (7 rekordow) -> `reject` (part_number nie jest waznym MPN)
  - `ocr_needed` (7 rekordow) -> `defer` (wymaga GEMINI_API_KEY do OCR frame check)
  - `manual_review` (2 rekordow) -> `defer` (wymaga ludzkiego review)
- Raport `curation_report.md` zostal rozszerzony o:
  - triage-informed curation breakdown table
  - verified snapshot stability assessment
  - jawny opis co blokuje export bez dodatkowego review
- CHAIN_MAP zaktualizowany: curation-01 status zmieniony z `smoke_tested` na `real_verified_tested`

## Jakie pliki zmieniono

Zmienione:
- `PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/CHAIN_MAP.md`

Wygenerowane artefakty curation (dry-run):
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/curation_aligned.jsonl`
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/curation_decisions.jsonl`
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/curation_report.md`

## Jakie komendy walidacyjne przeszly

- `python3 -m py_compile scripts/curate_candidates.py` — OK
- `python3 scripts/curate_candidates.py review` — OK (82 kandydatow, 0 limitations)
- `python3 scripts/curate_candidates.py dry-run` — OK (bez --fallback-test-db, na realnym verified snapshot)

## Counts decyzyjne (dry-run na test_db_verified.jsonl, 82 kandydatow)

| Decyzja | Count | Sklad |
|---------|-------|-------|
| accept | 23 | 9 confirmed + 14 disputed(triage=likely_confirmed) |
| defer | 9 | 7 ocr_needed + 2 manual_review |
| reject | 50 | 43 rejected + 7 disputed(triage=threshold_tuning) |

## Czy verified snapshot wystarczyl jako input

Tak, verified snapshot jest **strukturalnie kompletny**: wszystkie 3 artefakty verification (snapshot, report, disagreement log) istnieja i zostaly wczytane. Handoff `verification -> curation` jest **praktycznie stabilny** z nastepujacymi zastrzezeniami:

1. 14 disputed candidates zostalo auto-promotowanych do accept na podstawie triage — wymaga to ludzkiego potwierdzenia przed exportem
2. 9 candidates pozostaje deferred i nie da sie ich rozstrzygnac automatycznie
3. Brak GEMINI_API_KEY blokuje 7 ocr_needed candidates

## Co blokuje przejscie do exportu bez dodatkowego review

1. **7 candidates deferred pending OCR** — bez GEMINI_API_KEY nie da sie wykonac OCR frame check; te rekordy moga byc potencjalnie waznymi czesciami
2. **2 candidates deferred pending manual review** — custom transformer + board model number wymagaja ludzkiej oceny
3. **14 disputed auto-promoted do accept** — triage=likely_confirmed nie jest rownoznaczny z confirmed; przed exportem nalezy przeprowadzic human review tych rekordow

## Co powinien zrobic kolejny wykonawca

- Jesli GEMINI_API_KEY jest dostepny: uruchomic `python3 scripts/verify_candidates.py ocr-check` dla ocr_needed rekordow, a nastepnie ponownie uruchomic curation dry-run
- Przejrzec 14 auto-promotowanych disputed candidates i potwierdzic lub odrzucic ich accept status
- Po review: uruchomic `python3 scripts/curate_candidates.py apply` aby zapisac zaakceptowanych kandydatow do kanonicznego katalogu
- Nastepnie uruchomic export: `python3 scripts/build_catalog_artifacts.py export-all`
