# Verification Report

Generated: 2026-04-29T22:50:40Z
Pack: pack-project13-kaggle-verification-01
Execution surface: scripts/verify_candidates.py

## Input

- Source snapshot: `/home/krzysiek/Dokumenty/INFO_GROUP/STRAZ_POLSKIEGO_Ai/PROJEKTY/13_baza_czesci_recykling/autonomous_test/results/test_db.jsonl`
- Records loaded: 82
- Unique devices: 26

## Results

| Status | Count |
|--------|-------|
| Confirmed | 26 |
| Disputed | 0 |
| Rejected | 56 |
| **Total** | 82 |

## Disagreement summary

- Disputed records: 0
- Disagreement log: `/home/krzysiek/Dokumenty/INFO_GROUP/STRAZ_POLSKIEGO_Ai/PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/verification_disagreements.jsonl`

## Disputed triage summary

- No disputed triage records remain.
- Triage report: `/home/krzysiek/Dokumenty/INFO_GROUP/STRAZ_POLSKIEGO_Ai/PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/verification_triage.jsonl`

## Status resolution summary

| Status | Before | After | Delta |
|--------|--------|-------|-------|
| confirmed | 25 | 26 | +1 |
| disputed | 1 | 0 | -1 |
| rejected | 56 | 56 | 0 |

- Resolutions applied: 1
- Still deferred (ocr_needed): 0
- Still deferred (manual_review): 0
- Blocked for clean verified snapshot: 0
- Resolution packet: `/home/krzysiek/Dokumenty/INFO_GROUP/STRAZ_POLSKIEGO_Ai/PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/status_resolution_packet.json`
- Policy version: v2

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
- Status resolution packet: `/home/krzysiek/Dokumenty/INFO_GROUP/STRAZ_POLSKIEGO_Ai/PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/status_resolution_packet.json`

## Limitations

- OCR-based verification requires GEMINI_API_KEY and was skipped if not available
- Rule-based validation may produce false positives for short or ambiguous MPNs
- threshold_tuning records are now rejected by improved MPN heuristics (status resolution policy v2)
- likely_confirmed records are now promoted to confirmed by status resolution policy v2
- No ocr_needed records remain deferred in the current status resolution packet
- No manual_review records remain deferred in the current status resolution packet
- Verification is separate from curation and export (no downstream promotion)
- Verification pack does NOT handle export gate; that is curation's responsibility

## Handoff to curation

After review of this report and disagreement log, run:

```bash
python3 scripts/curate_candidates.py review --snapshot /home/krzysiek/Dokumenty/INFO_GROUP/STRAZ_POLSKIEGO_Ai/PROJEKTY/13_baza_czesci_recykling/autonomous_test/results/test_db_verified.jsonl
python3 scripts/curate_candidates.py dry-run --fallback-test-db
```
