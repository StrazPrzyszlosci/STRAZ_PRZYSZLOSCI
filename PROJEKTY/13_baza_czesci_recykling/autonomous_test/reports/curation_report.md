# Curation Report

Generated: 2026-04-29T22:45:32Z
Pack: pack-project13-curation-01

## Counts

| Decision | Count |
|----------|-------|
| Accepted | 26 |
| Deferred | 0 |
| Rejected | 56 |
| **Total** | 82 |

### Breakdown by verification status

| Verification Status | Accepted | Deferred | Rejected |
|---------------------|----------|----------|----------|
| confirmed | 26 | 0 | 0 |
| disputed | 0 | 0 | 0 |
| rejected | 0 | 0 | 56 |

## Key cases requiring review

No special cases — all accepted candidates were confirmed in verification.

## Triage-informed curation breakdown

Disputed candidates were resolved using triage categories from verification:

| Triage Category | Curation Decision | Count |
|----------------|-------------------|-------|
| likely_confirmed | accept | 14 |
| threshold_tuning | reject | 1 |
| ocr_needed | accept | 2 |
| ocr_needed | reject | 5 |
| manual_review | accept | 1 |
| manual_review | reject | 1 |
| no_triage | accept | 9 |
| no_triage | reject | 49 |

## Verified snapshot stability assessment

Verified snapshot is **structurally complete**: all three verification artifacts (snapshot, report, disagreement log) are present.


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

To resolve:
1. Review pending_human_approval candidates in curation_review_queue.jsonl
2. Set reviewed_by and reviewed_at for approved entries
3. Re-run: python3 scripts/curate_candidates.py export-gate

### Next steps (from gate packet)

- Resolve 2 blocker(s) before export:
-   - 14 accepted candidates still pending human approval: M425R1GB4BB0-CWM0D, P28A41E, 230130, 2R2, 33 25V H33, K6100 1124 08.24, M51413ASP, MT1588AE 0311-ARS HF986, MINIJST E DC546134603 ST, JKB1, JKB2, INTEL 08 i7-628M, BD82HM55 SLGZR, 775i65G, RM 121, LDF-12V16W, V17081
-   - No human review approval recorded for pending candidates
- To approve pending candidates, use record-review command:
-   python3 scripts/curate_candidates.py record-review --candidate-id candidate-0005 --decision approved --reviewed-by <REVIEWER_NAME>
-   python3 scripts/curate_candidates.py record-review --candidate-id candidate-0006 --decision approved --reviewed-by <REVIEWER_NAME>
-   python3 scripts/curate_candidates.py record-review --candidate-id candidate-0007 --decision approved --reviewed-by <REVIEWER_NAME>
-   python3 scripts/curate_candidates.py record-review --candidate-id candidate-0015 --decision approved --reviewed-by <REVIEWER_NAME>
-   python3 scripts/curate_candidates.py record-review --candidate-id candidate-0019 --decision approved --reviewed-by <REVIEWER_NAME>
-   ... and 9 more pending candidates
- Then re-run: python3 scripts/curate_candidates.py export-gate
