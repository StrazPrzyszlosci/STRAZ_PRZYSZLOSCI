# Curation Report

Generated: 2026-04-24T21:38:12Z
Pack: pack-project13-curation-01

## Counts

| Decision | Count |
|----------|-------|
| Accepted | 23 |
| Deferred | 9 |
| Rejected | 50 |
| **Total** | 82 |

### Breakdown by verification status

| Verification Status | Accepted | Deferred | Rejected |
|---------------------|----------|----------|----------|
| confirmed | 9 | 0 | 0 |
| disputed | 14 | 9 | 7 |
| rejected | 0 | 0 | 43 |

## Key cases requiring review

- **ACCEPTED (disputed, triage=likely_confirmed)**: candidate-0005 — Disputed in verification but triage=likely_confirmed (reasonable_mpn_confidence_very_low_disagreement). Auto-promoted to accept per triage recommendation.
- **ACCEPTED (disputed, triage=likely_confirmed)**: candidate-0006 — Disputed in verification but triage=likely_confirmed (reasonable_mpn_confidence_very_low_disagreement). Auto-promoted to accept per triage recommendation.
- **ACCEPTED (disputed, triage=likely_confirmed)**: candidate-0007 — Disputed in verification but triage=likely_confirmed (reasonable_mpn_confidence_very_low_disagreement). Auto-promoted to accept per triage recommendation.
- **ACCEPTED (disputed, triage=likely_confirmed)**: candidate-0015 — Disputed in verification but triage=likely_confirmed (reasonable_mpn_confidence_very_low_disagreement). Auto-promoted to accept per triage recommendation.
- **ACCEPTED (disputed, triage=likely_confirmed)**: candidate-0019 — Disputed in verification but triage=likely_confirmed (reasonable_mpn_confidence_very_low_disagreement). Auto-promoted to accept per triage recommendation.
- **ACCEPTED (disputed, triage=likely_confirmed)**: candidate-0020 — Disputed in verification but triage=likely_confirmed (reasonable_mpn_confidence_very_low_disagreement). Auto-promoted to accept per triage recommendation.
- **ACCEPTED (disputed, triage=likely_confirmed)**: candidate-0028 — Disputed in verification but triage=likely_confirmed (reasonable_mpn_confidence_very_low_disagreement). Auto-promoted to accept per triage recommendation.
- **ACCEPTED (disputed, triage=likely_confirmed)**: candidate-0032 — Disputed in verification but triage=likely_confirmed (reasonable_mpn_confidence_very_low_disagreement). Auto-promoted to accept per triage recommendation.
- **ACCEPTED (disputed, triage=likely_confirmed)**: candidate-0041 — Disputed in verification but triage=likely_confirmed (reasonable_mpn_confidence_very_low_disagreement). Auto-promoted to accept per triage recommendation.
- **ACCEPTED (disputed, triage=likely_confirmed)**: candidate-0042 — Disputed in verification but triage=likely_confirmed (reasonable_mpn_confidence_very_low_disagreement). Auto-promoted to accept per triage recommendation.
- **ACCEPTED (disputed, triage=likely_confirmed)**: candidate-0052 — Disputed in verification but triage=likely_confirmed (reasonable_mpn_confidence_very_low_disagreement). Auto-promoted to accept per triage recommendation.
- **ACCEPTED (disputed, triage=likely_confirmed)**: candidate-0054 — Disputed in verification but triage=likely_confirmed (reasonable_mpn_confidence_very_low_disagreement). Auto-promoted to accept per triage recommendation.
- **ACCEPTED (disputed, triage=likely_confirmed)**: candidate-0057 — Disputed in verification but triage=likely_confirmed (reasonable_mpn_confidence_very_low_disagreement). Auto-promoted to accept per triage recommendation.
- **ACCEPTED (disputed, triage=likely_confirmed)**: candidate-0062 — Disputed in verification but triage=likely_confirmed (reasonable_mpn_confidence_very_low_disagreement). Auto-promoted to accept per triage recommendation.
- **DEFERRED (triage=ocr_needed)**: candidate-0008 — Disputed in verification, triage=ocr_needed (video_source_available_for_ocr). Deferred: requires OCR frame check (GEMINI_API_KEY) to resolve.
- **DEFERRED (triage=ocr_needed)**: candidate-0012 — Disputed in verification, triage=ocr_needed (board_model_number, video_source_available_for_ocr). Deferred: requires OCR frame check (GEMINI_API_KEY) to resolve.
- **DEFERRED (triage=ocr_needed)**: candidate-0018 — Disputed in verification, triage=ocr_needed (video_source_available_for_ocr). Deferred: requires OCR frame check (GEMINI_API_KEY) to resolve.
- **DEFERRED (triage=ocr_needed)**: candidate-0073 — Disputed in verification, triage=ocr_needed (enrichment_v2_with_video_source). Deferred: requires OCR frame check (GEMINI_API_KEY) to resolve.
- **DEFERRED (triage=ocr_needed)**: candidate-0074 — Disputed in verification, triage=ocr_needed (enrichment_v2_with_video_source). Deferred: requires OCR frame check (GEMINI_API_KEY) to resolve.
- **DEFERRED (triage=manual_review)**: candidate-0076 — Disputed in verification, triage=manual_review (board_model_number). Deferred: human reviewer needed to assess part number validity.
- **DEFERRED (triage=manual_review)**: candidate-0077 — Disputed in verification, triage=manual_review (custom_wound_transformer_no_datasheet). Deferred: human reviewer needed to assess part number validity.
- **DEFERRED (triage=ocr_needed)**: candidate-0079 — Disputed in verification, triage=ocr_needed (enrichment_v2_with_video_source). Deferred: requires OCR frame check (GEMINI_API_KEY) to resolve.
- **DEFERRED (triage=ocr_needed)**: candidate-0080 — Disputed in verification, triage=ocr_needed (enrichment_v2_with_video_source). Deferred: requires OCR frame check (GEMINI_API_KEY) to resolve.

## Triage-informed curation breakdown

Disputed candidates were resolved using triage categories from verification:

| Triage Category | Curation Decision | Count |
|----------------|-------------------|-------|
| likely_confirmed | accept | 14 |
| threshold_tuning | reject | 7 |
| ocr_needed | defer | 7 |
| manual_review | defer | 2 |
| no_triage | accept | 9 |
| no_triage | reject | 43 |

## Verified snapshot stability assessment

Verified snapshot is **structurally complete**: all three verification artifacts (snapshot, report, disagreement log) are present.

However, **9 candidates remain deferred** and block full pipeline completion:
- 7 deferred due to missing OCR (requires GEMINI_API_KEY)
- 2 deferred requiring manual human review

**14 disputed candidates were auto-promoted to accept** based on triage=likely_confirmed. These should be reviewed by a human before export.

## Provenance

- Verification report: `/home/krzysiek/Dokumenty/INFO_GROUP/STRAZ_POLSKIEGO_Ai/PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/verification_report.md`
- Disagreement log: `/home/krzysiek/Dokumenty/INFO_GROUP/STRAZ_POLSKIEGO_Ai/PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/verification_disagreements.jsonl`
- Source snapshot: `/home/krzysiek/Dokumenty/INFO_GROUP/STRAZ_POLSKIEGO_Ai/PROJEKTY/13_baza_czesci_recykling/autonomous_test/results/test_db_verified.jsonl`
- Curation decisions: `/home/krzysiek/Dokumenty/INFO_GROUP/STRAZ_POLSKIEGO_Ai/PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/curation_decisions.jsonl`

## Handoff to export

After merge of this curation PR, the downstream export pack is safe to run:

```bash
python3 PROJEKTY/13_baza_czesci_recykling/scripts/build_catalog_artifacts.py export-all
python3 PROJEKTY/13_baza_czesci_recykling/scripts/build_catalog_artifacts.py validate
```

## What blocks export without additional review

- 7 candidates deferred pending OCR (GEMINI_API_KEY not available)
- 2 candidates deferred pending manual human review
- 14 disputed candidates auto-promoted to accept (need human confirmation before export)
