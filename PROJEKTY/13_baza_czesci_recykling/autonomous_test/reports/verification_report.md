# Verification Report

Generated: 2026-04-24T10:39:52Z
Pack: pack-project13-kaggle-verification-01
Execution surface: scripts/verify_candidates.py

## Input

- Source snapshot: `/home/krzysiek/Dokumenty/INFO_GROUP/STRAZ_POLSKIEGO_Ai/PROJEKTY/13_baza_czesci_recykling/autonomous_test/results/test_db.jsonl`
- Records loaded: 82
- Unique devices: 26

## Results

| Status | Count |
|--------|-------|
| Confirmed | 9 |
| Disputed | 30 |
| Rejected | 43 |
| **Total** | 82 |

## Disagreement summary

- Disputed records: 30
- Disagreement log: `/home/krzysiek/Dokumenty/INFO_GROUP/STRAZ_POLSKIEGO_Ai/PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/verification_disagreements.jsonl`

### Key disputed cases

- **Lenovo NOK ILG5081008 308C1K835W000Y 43398 7628365100030** (device: Lenovo Laptop) — disagreement: 0.12, triage: threshold_tuning, indicators: full_model_string_not_mpn
- **M425R1GB4BB0-CWM0D** (device: Lenovo Laptop) — disagreement: 0.12, triage: likely_confirmed, indicators: reasonable_mpn_confidence_very_low_disagreement
- **P28A41E** (device: Lenovo Laptop) — disagreement: 0.12, triage: likely_confirmed, indicators: reasonable_mpn_confidence_very_low_disagreement
- **230130, 2R2, 33 25V H33** (device: Lenovo Laptop) — disagreement: 0.12, triage: likely_confirmed, indicators: reasonable_mpn_confidence_very_low_disagreement
- **3336220400007** (device: Dell Precision M4800) — disagreement: 0.18, triage: ocr_needed, indicators: video_source_available_for_ocr
- **UE50MU6102KXXH** (device: Samsung UE50MU6102K) — disagreement: 0.12, triage: ocr_needed, indicators: board_model_number, video_source_available_for_ocr
- **K6100 1124 08.24** (device: Samsung UE50MU6102K) — disagreement: 0.12, triage: likely_confirmed, indicators: reasonable_mpn_confidence_very_low_disagreement
- **1244-2** (device: Samsung UE32EH4000) — disagreement: 0.18, triage: ocr_needed, indicators: video_source_available_for_ocr
- **M51413ASP** (device: Unknown Electronic Waste) — disagreement: 0.12, triage: likely_confirmed, indicators: reasonable_mpn_confidence_very_low_disagreement
- **MT1588AE 0311-ARS HF986** (device: Unknown Electronic Waste) — disagreement: 0.12, triage: likely_confirmed, indicators: reasonable_mpn_confidence_very_low_disagreement

## Disputed triage summary

| Triage category | Count | Description |
|----------------|-------|-------------|
| likely_confirmed | 14 | High MPN confidence, low disagreement; safe to auto-promote after review |
| ocr_needed | 7 | OCR frame check could resolve; requires GEMINI_API_KEY |
| manual_review | 2 | Human reviewer needed; no automated resolution path |
| threshold_tuning | 7 | Record should be rejected or recategorized by improved MPN heuristics |

- Triage report: `/home/krzysiek/Dokumenty/INFO_GROUP/STRAZ_POLSKIEGO_Ai/PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/verification_triage.jsonl`
- GEMINI_API_KEY available: False
- OCR-actionable records: 7

## Verification method

1. Rule-based MPN validation (pattern matching, rejection heuristics)
2. Enrichment field cross-check (verification flag, observed text, confidence)
3. Disagreement score computation (0.0 = full agreement, 1.0 = maximum disagreement)
4. Status assignment: confirmed / disputed / rejected
5. OCR frame check (optional, requires GEMINI_API_KEY — disputed records only)
6. Disputed triage (classify disputed into: likely_confirmed, ocr_needed, manual_review, threshold_tuning)

## Output contract

- Verified snapshot: `/home/krzysiek/Dokumenty/INFO_GROUP/STRAZ_POLSKIEGO_Ai/PROJEKTY/13_baza_czesci_recykling/autonomous_test/results/test_db_verified.jsonl`
- This report: `/home/krzysiek/Dokumenty/INFO_GROUP/STRAZ_POLSKIEGO_Ai/PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/verification_report.md`
- Disagreement log: `/home/krzysiek/Dokumenty/INFO_GROUP/STRAZ_POLSKIEGO_Ai/PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/verification_disagreements.jsonl`
- Triage report: `/home/krzysiek/Dokumenty/INFO_GROUP/STRAZ_POLSKIEGO_Ai/PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/verification_triage.jsonl`

## Limitations

- OCR-based verification requires GEMINI_API_KEY and was skipped if not available
- Rule-based validation may produce false positives for short or ambiguous MPNs
- Disputed records now have triage categories; threshold_tuning records should improve scoring rules
- ocr_needed records remain deferred until GEMINI_API_KEY is available
- Verification is separate from curation and export (no downstream promotion)

## Handoff to curation

After review of this report and disagreement log, run:

```bash
python3 scripts/curate_candidates.py review --snapshot /home/krzysiek/Dokumenty/INFO_GROUP/STRAZ_POLSKIEGO_Ai/PROJEKTY/13_baza_czesci_recykling/autonomous_test/results/test_db_verified.jsonl
python3 scripts/curate_candidates.py dry-run --fallback-test-db
```
