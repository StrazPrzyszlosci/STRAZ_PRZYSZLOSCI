# Curation Report

Generated: 2026-04-27T15:06:38Z
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
| confirmed | 23 | 0 | 0 |
| disputed | 0 | 9 | 0 |
| rejected | 0 | 0 | 50 |

## Key cases requiring review

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
| threshold_tuning | reject | 1 |
| ocr_needed | defer | 7 |
| manual_review | defer | 2 |
| no_triage | accept | 9 |
| no_triage | reject | 49 |

## Verified snapshot stability assessment

Verified snapshot is **structurally complete**: all three verification artifacts (snapshot, report, disagreement log) are present.

However, **9 candidates remain deferred** and block full pipeline completion:
- 7 deferred due to missing OCR (requires GEMINI_API_KEY)
- 2 deferred requiring manual human review

## Provenance

- Verification report: `/home/krzysiek/Dokumenty/INFO_GROUP/STRAZ_POLSKIEGO_Ai/PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/verification_report.md`
- Disagreement log: `/home/krzysiek/Dokumenty/INFO_GROUP/STRAZ_POLSKIEGO_Ai/PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/verification_disagreements.jsonl`
- Source snapshot: `/home/krzysiek/Dokumenty/INFO_GROUP/STRAZ_POLSKIEGO_Ai/PROJEKTY/13_baza_czesci_recykling/autonomous_test/results/test_db_verified.jsonl`
- Curation decisions: `/home/krzysiek/Dokumenty/INFO_GROUP/STRAZ_POLSKIEGO_Ai/PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/curation_decisions.jsonl`
- Review queue: `/home/krzysiek/Dokumenty/INFO_GROUP/STRAZ_POLSKIEGO_Ai/PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/curation_review_queue.jsonl`
- Export gate packet: `/home/krzysiek/Dokumenty/INFO_GROUP/STRAZ_POLSKIEGO_Ai/PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/export_gate_packet.json`

## Export gate status

**Gate: BLOCKED**

Export gate is **BLOCKED**. Do not run export until blockers are resolved:

- BLOCKER: 14 accepted candidates still pending human approval: M425R1GB4BB0-CWM0D, P28A41E, 230130, 2R2, 33 25V H33, K6100 1124 08.24, M51413ASP, MT1588AE 0311-ARS HF986, MINIJST E DC546134603 ST, JKB1, JKB2, INTEL 08 i7-628M, BD82HM55 SLGZR, 775i65G, RM 121, LDF-12V16W, V17081
- BLOCKER: No human review approval recorded for pending candidates
- warning: 9 deferred candidates not in export: 3336220400007, UE50MU6102KXXH, 1244-2, LF80537, TS8121K, BN44-00213A, QHAD01249, BD243C, QHA001249
- warning: 7 records still deferred by verification (ocr_needed)
- warning: 2 records still deferred by verification (manual_review)

To resolve:
1. Review pending_human_approval candidates using `record-review` command (see: docs/HUMAN_APPROVAL_LEDGER.md)
2. After all pending resolved: re-run `python3 scripts/curate_candidates.py export-gate`
3. If gate OPEN: follow the export-open readiness packet (docs/EXPORT_OPEN_READINESS_PACKET.md)
4. After export: fill and save receipt (autonomous_test/reports/export_release_receipt_TEMPLATE.json)

### Next steps (from gate packet)

- Resolve 2 blocker(s) before export:
- - 14 accepted candidates still pending human approval: M425R1GB4BB0-CWM0D, P28A41E, 230130, 2R2, 33 25V H33, K6100 1124 08.24, M51413ASP, MT1588AE 0311-ARS HF986, MINIJST E DC546134603 ST, JKB1, JKB2, INTEL 08 i7-628M, BD82HM55 SLGZR, 775i65G, RM 121, LDF-12V16W, V17081
- - No human review approval recorded for pending candidates
- To approve pending candidates, use record-review command (see: docs/HUMAN_APPROVAL_LEDGER.md)
- When gate OPEN: follow docs/EXPORT_OPEN_READINESS_PACKET.md for full execution sequence

## Deferred candidates detail

- 7 candidates deferred pending OCR (GEMINI_API_KEY not available)
- 2 candidates deferred pending manual human review
