# Mini-Handoff Zadanie 11

## Co zostalo zrobione

- Stworzono realny execution surface verification: `scripts/verify_candidates.py`
- Pack `pack-project13-kaggle-verification-01` przeszedl ze statusu `draft` na `smoke_tested`
- Dry-run i pelny run na 82 kandydatach z `test_db.jsonl`: 9 confirmed, 30 disputed, 43 rejected
- Jawny input/output contract dodany do `manifest.json`
- RUNBOOK zaktualizowany o instrukcje uruchomienia, walidacje i handoff do curation
- CHAIN_MAP zaktualizowany: verification juz nie jest `draft`
- Readiness gate zmieniony na `passed`

## Jakie pliki zmieniono

Nowe:
- `PROJEKTY/13_baza_czesci_recykling/scripts/verify_candidates.py`

Zmienione:
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-kaggle-verification-01/manifest.json`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-kaggle-verification-01/RUNBOOK.md`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-kaggle-verification-01/readiness_gate.json`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-kaggle-verification-01/task.json`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-kaggle-verification-01/PR_TEMPLATE.md`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/CHAIN_MAP.md`

Wygenerowane artefakty verification:
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/results/test_db_verified.jsonl`
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/verification_report.md`
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/verification_disagreements.jsonl`
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/verification_scored.jsonl`

## Jakie komendy walidacyjne przeszly

- `python3 -m py_compile scripts/verify_candidates.py` — OK
- `python3 scripts/verify_candidates.py dry-run` — OK (82 kandydatow, 0 bledow)
- `python3 scripts/verify_candidates.py run` (bez GEMINI_API_KEY) — OK

## Co nadal blokuje pierwszy publiczny run

1. **OCR verification dla disputed** — wymaga GEMINI_API_KEY; obecny run pominol OCR check, co oznacza ze 30 disputed rekordow zostalo bez multimodalnego frame check
2. **Brak Kaggle notebooka** — execution surface jest lokalny (CLI), nie jako Kaggle notebook; migracja do Kaggle jest opcjonalna
3. **Brak obsady reviewerow** — disagreement log z 30 disputed wymaga manualnego review, ale nie ma jeszcze przydzielonych reviewerow
4. **Brak potwierdzenia scoringu** — rule-based scoring moze byc zbyt restrykcyjny (tylko 9/82 confirmed); moze wymagac tuningu progow

## Co powinien zrobic kolejny wykonawca

- Jesli GEMINI_API_KEY jest dostepny: uruchomic `python3 scripts/verify_candidates.py ocr-check` dla disputed rekordow
- Przejrzec `verification_disagreements.jsonl` i zdecydowac, ktore disputed mozna recznie promowac do confirmed
- Uruchomic curation: `python3 scripts/curate_candidates.py review --snapshot autonomous_test/results/test_db_verified.jsonl`
- Rozwazyc tuning progow disagreement w `verify_candidates.py` jesli 9 confirmed jest zbyt malo
