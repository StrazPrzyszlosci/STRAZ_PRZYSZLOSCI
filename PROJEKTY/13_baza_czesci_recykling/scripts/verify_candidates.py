#!/usr/bin/env python3
"""Execution surface for pack-project13-kaggle-verification-01.

Verify candidate parts from enrichment through rule-based MPN validation,
OCR cross-check, disagreement scoring, and reviewer-ready output.

This script does NOT require GEMINI_API_KEY for the core rule-based flow.
OCR-based verification (multimodal frame check) requires the API key and
falls back to rule-based-only mode when absent.

Commands:
load — Load candidate snapshot and report stats
validate — Rule-based MPN validation + enrichment field cross-check
ocr-check — Attempt OCR-based frame verification (requires GEMINI_API_KEY)
ocr-selector — List/select individual OCR-deferred cases for surgical execution (--case CANDIDATE_ID or --group VIDEO_URL)
score — Compute disagreement scores and assign verification_status
triage — Classify disputed records into triage categories (ocr_needed, manual_review, threshold_tuning, likely_confirmed)
resolve-status — Apply status resolution policy: promote likely_confirmed, reject threshold_tuning, defer ocr_needed/manual_review
deferred-workpack — Generate operator-ready workpack for deferred OCR and manual review cases
snapshot — Write verified snapshot (test_db_verified.jsonl)
report — Generate verification_report.md (includes triage summary when available)
run — Execute full pipeline: load + validate + score + triage + resolve-status + snapshot + report
dry-run — Same as run but writes to a separate dry-run output directory
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RESULTS_DIR = PROJECT_ROOT / "autonomous_test" / "results"
REPORTS_DIR = PROJECT_ROOT / "autonomous_test" / "reports"

CANDIDATE_SNAPSHOT_PATH = RESULTS_DIR / "test_db.jsonl"
VERIFIED_SNAPSHOT_PATH = RESULTS_DIR / "test_db_verified.jsonl"
VERIFICATION_REPORT_PATH = REPORTS_DIR / "verification_report.md"
DISAGREEMENT_LOG_PATH = REPORTS_DIR / "verification_disagreements.jsonl"
TRIAGE_REPORT_PATH = REPORTS_DIR / "verification_triage.jsonl"

DRY_RUN_SUFFIX = ".dry-run"

DESIGNATOR_PATTERN = re.compile(r"^[A-Z]\d{1,3}([,\s]+[A-Z]\d{1,3})+$")
DATE_CODE_PATTERN = re.compile(
    r"\b\d{2}[\/\-](?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b|\b\d{2}[\/\-]\d{2}[\/\-]\d{2}\b|\b20\d{2}[\/\-]\d{2}",
    re.IGNORECASE,
)
MODEL_LABEL_PATTERN = re.compile(r"^MODEL:\s+", re.IGNORECASE)
PATENT_PATTERN = re.compile(r"PATENT\s*#", re.IGNORECASE)
FULL_MODEL_STRING_PATTERN = re.compile(r"^[A-Z][a-z]+\s+NOK\s+", re.IGNORECASE)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        records.append(json.loads(line))
    return records


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            json.dumps(row, ensure_ascii=False, separators=(",", ":")) for row in rows
        )
        + "\n",
        encoding="utf-8",
    )


def write_json(path: Path, data: dict[str, Any] | list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


MPN_REJECTION_PATTERNS: list[tuple[str, str]] = [
    (r"^[A-Z]\d{1,3}([,\s]+[A-Z]\d{1,3})+$", "designator_list"),
    (r"^BRAK$", "empty_verification"),
    (r"^\s*$", "empty_field"),
    (r"^[A-ZĄĆĘŁŃÓŚŹŻa-ząćęłńóśźż\s]{4,}$", "plain_text_phrase"),
    (r"^\d+[µu]?[FfHh]$", "value_not_mpn"),
    (r"^\d+[KkMm]?[ΩΩ]$", "value_not_mpn"),
    (r"^[0-9]{1,4}$", "short_number"),
    (r"BLĄD\s", "ocr_error"),
    (r"PATENT\s*#", "patent_number"),
    (r"^MODEL:\s+", "model_label_not_mpn"),
    (r"^[A-Z][a-z]+\s+NOK\s+", "full_model_string_not_mpn"),
    (r"\d{2}[\/\-](?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[\/\-]\d{2,4}", "date_code_in_part_number"),
    (r"\bBOM\s*:", "bom_label_in_part_number"),
    (r"\b(?:FSB|Rev\.?|REV\.?)\b", "spec_annotation_not_mpn"),
]

MPN_REJECTION_BROAD_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"^[A-Z][a-z]+\s+NOK\s+", re.IGNORECASE), "full_model_string_not_mpn"),
    (re.compile(r"PATENT\s*#", re.IGNORECASE), "patent_number"),
    (re.compile(r"^MODEL:\s+", re.IGNORECASE), "model_label_not_mpn"),
    (re.compile(r"\d{2}[\/\-](?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[\/\-]\d{2,4}", re.IGNORECASE), "date_code_in_part_number"),
    (re.compile(r"\bBOM\s*:", re.IGNORECASE), "bom_label_in_part_number"),
    (re.compile(r"\b(?:FSB|Rev\.?|REV\.?)\b", re.IGNORECASE), "spec_annotation_not_mpn"),
]

PART_NUMBER_IC_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"^[A-Z]{2,5}\d{2,6}[A-Z]{0,4}$",
        r"^[A-Z]{2,5}\d{2,6}[A-Z]{0,4}-[A-Z0-9]{1,6}$",
        r"^[A-Z]{2,4}\d{3,5}[A-Z]{1,3}\d{0,2}$",
        r"^[A-Z]{2}\d{4}[A-Z]{1,3}$",
        r"^\d{4}[A-Z]{2,3}$",
        r"^[A-Z]{2,5}-\d{3,5}$",
        r"^[A-Z]{3}\d{4}",
    ]
]

CONNECTOR_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"^\d{6,10}$",
        r"^\d{3}-\d{3,4}-\d{2,3}$",
        r"^[A-Z]{2,3}\d{4,6}[A-Z]?$",
    ]
]

RESISTOR_CAP_PATTERN: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"^[A-Z]{2,3}\d{4,5}[A-Z]{0,3}$",
    ]
]

STATUS_RESOLUTION_POLICY: dict[str, dict[str, Any]] = {
    "likely_confirmed": {
        "resolution": "promote_to_confirmed",
        "condition": "mpn_valid AND confidence>=0.6 AND disagreement<=0.15 AND no_threshold_indicators",
        "new_status": "confirmed",
        "audit_note": "Auto-promoted from disputed (triage=likely_confirmed) per status resolution policy v2",
    },
    "threshold_tuning": {
        "resolution": "reject_by_heuristics",
        "condition": "mpn_invalid_due_to_rejection_pattern OR comma_separated_list",
        "new_status": "rejected",
        "audit_note": "Rejected by improved MPN heuristics (triage=threshold_tuning) per status resolution policy v2",
    },
    "ocr_needed": {
        "resolution": "defer_pending_ocr",
        "condition": "ocr_actionable AND no GEMINI_API_KEY",
        "new_status": "disputed",
        "audit_note": "Deferred: OCR check required but GEMINI_API_KEY not available",
    },
    "manual_review": {
        "resolution": "defer_pending_human",
        "condition": "board_model OR custom_transformer",
        "new_status": "disputed",
        "audit_note": "Deferred: requires human reviewer decision",
    },
}

STATUS_RESOLUTION_PACKET_PATH = REPORTS_DIR / "status_resolution_packet.json"


def classify_mpn_quality(part_number: str) -> dict[str, Any]:
    if not part_number or not part_number.strip():
        return {"valid": False, "reason": "empty_field", "confidence": 0.1}

    pn = part_number.strip()

    for pattern, reason in MPN_REJECTION_PATTERNS:
        if re.match(pattern, pn):
            return {"valid": False, "reason": reason, "confidence": 0.1}

    for pattern, reason in MPN_REJECTION_BROAD_PATTERNS:
        if pattern.search(pn):
            return {"valid": False, "reason": reason, "confidence": 0.1}

    comma_count = pn.count(",")
    if comma_count >= 3:
        return {"valid": False, "reason": "comma_separated_list", "confidence": 0.1}

    if len(pn) < 2:
        return {"valid": False, "reason": "too_short", "confidence": 0.1}

    has_alnum = any(c.isalnum() for c in pn)
    if not has_alnum:
        return {"valid": False, "reason": "no_alphanumeric", "confidence": 0.0}

    if len(pn) >= 5:
        for pat in PART_NUMBER_IC_PATTERNS:
            if pat.match(pn):
                return {"valid": True, "reason": "ic_mpn_pattern", "confidence": 0.9}

    if len(pn) >= 6:
        for pat in CONNECTOR_PATTERNS:
            if pat.match(pn):
                return {
                    "valid": True,
                    "reason": "connector_mpn_pattern",
                    "confidence": 0.8,
                }

    if len(pn) >= 5:
        for pat in RESISTOR_CAP_PATTERN:
            if pat.match(pn):
                return {
                    "valid": True,
                    "reason": "passive_mpn_pattern",
                    "confidence": 0.8,
                }

    has_digits = any(c.isdigit() for c in pn)
    has_letters = any(c.isalpha() for c in pn)
    if has_digits and has_letters and len(pn) >= 4:
        return {"valid": True, "reason": "mixed_alnum_mpn", "confidence": 0.6}

    if len(pn) >= 3 and has_digits:
        return {"valid": True, "reason": "short_numeric_id", "confidence": 0.4}

    return {"valid": False, "reason": "unrecognized_format", "confidence": 0.2}


def cross_check_enrichment(record: dict[str, Any]) -> dict[str, Any]:
    issues: list[str] = []
    confidence = record.get("confidence", 0.0)
    verification = record.get("verification", {})
    verified = verification.get("verified", None)
    observed_text = verification.get("observed_text", "")
    part_number = record.get("part_number", "")
    part_name = record.get("part_name", "")

    if verified is None:
        issues.append("no_verification_flag")

    if observed_text == "BRAK":
        issues.append("observed_text_brak")
    elif observed_text == "Błąd wycinania klatki":
        issues.append("frame_extraction_error")

    if part_number and observed_text and part_number != observed_text:
        if observed_text != "BRAK" and "Błąd" not in observed_text:
            issues.append("mpn_observed_mismatch")

    if confidence < 0.5:
        issues.append("low_confidence")

    if not part_name or not part_name.strip():
        issues.append("missing_part_name")

    if not part_number or not part_number.strip():
        issues.append("missing_part_number")

    return {
        "issues": issues,
        "issue_count": len(issues),
        "passed": len(issues) == 0,
    }


def compute_disagreement_score(
    mpn_result: dict[str, Any],
    cross_check: dict[str, Any],
    record: dict[str, Any],
) -> float:
    score = 0.0

    if not mpn_result["valid"]:
        score += 0.5
    else:
        score += max(0.0, 0.3 - mpn_result["confidence"] * 0.3)

    score += cross_check["issue_count"] * 0.15

    verification = record.get("verification", {})
    verified = verification.get("verified")
    observed_text = verification.get("observed_text", "")

    if verified is False:
        score += 0.3
    elif verified is None:
        score += 0.2

    if observed_text == "BRAK":
        score += 0.3
    elif "Błąd" in observed_text:
        score += 0.4

    return min(1.0, round(score, 3))


def assign_verification_status(
    mpn_result: dict[str, Any],
    cross_check: dict[str, Any],
    disagreement_score: float,
    record: dict[str, Any],
) -> str:
    verification = record.get("verification", {})
    verified = verification.get("verified")
    observed_text = verification.get("observed_text", "")

    if observed_text == "BRAK":
        return "rejected"

    if "Błąd" in observed_text:
        return "rejected"

    if not mpn_result["valid"]:
        return "rejected"

    if verified is False:
        if disagreement_score < 0.3 and mpn_result["confidence"] >= 0.8:
            return "disputed"
        return "rejected"

    if (
        disagreement_score <= 0.15
        and cross_check["passed"]
        and mpn_result["confidence"] >= 0.7
    ):
        return "confirmed"

    if disagreement_score <= 0.4:
        return "disputed"

    return "rejected"


def classify_disputed_triage(record: dict[str, Any]) -> dict[str, Any]:
    part_number = record.get("part_number", "")
    part_name = record.get("part_name", "")
    observed_text = record.get("verification", {}).get("observed_text", "")
    verification_raw = record.get("verification_raw", {})
    verification = record.get("verification", {})
    verified = verification.get("verified")
    mpn_result = record.get("_mpn_result", {})
    cross_check = record.get("_cross_check", {})
    disagreement_score = record.get("disagreement_score", 0.0)
    confidence = record.get("confidence", 0.0)

    indicators: list[str] = []
    triage_category = "manual_review"
    ocr_actionable = False

    has_yt_link = bool(record.get("yt_link", record.get("source_video", "")))
    has_frame_error = (
        "Błąd" in observed_text
        or cross_check.get("issues", [])
        and "frame_extraction_error" in cross_check.get("issues", [])
    )

    pn = part_number.strip()

    if DESIGNATOR_PATTERN.match(pn):
        indicators.append("designator_list_not_mpn")
        triage_category = "threshold_tuning"

    if DATE_CODE_PATTERN.search(pn):
        indicators.append("date_code_in_part_number")
        triage_category = "threshold_tuning"

    if MODEL_LABEL_PATTERN.match(pn):
        indicators.append("model_label_not_mpn")
        triage_category = "threshold_tuning"

    if PATENT_PATTERN.search(pn):
        indicators.append("patent_number_in_part_number")
        triage_category = "threshold_tuning"

    if FULL_MODEL_STRING_PATTERN.match(pn):
        indicators.append("full_model_string_not_mpn")
        triage_category = "threshold_tuning"

    comma_count = pn.count(",")
    if comma_count >= 3:
        indicators.append("comma_separated_list")
        triage_category = "threshold_tuning"

    is_board_model = any(
        kw in part_name.lower()
        for kw in ["board", "płyta", "mainboard", "power supply", "psu"]
    ) and any(kw in pn.lower() for kw in ["bn44", "bn44-", "ue50", "ue32"])
    if is_board_model:
        indicators.append("board_model_number")
        triage_category = "manual_review"

    is_transformer_custom = any(
        kw in part_name.lower() for kw in ["transformer", "trafo"]
    ) and any(kw in pn.lower() for kw in ["qha", "qhad"])
    if is_transformer_custom:
        indicators.append("custom_wound_transformer_no_datasheet")
        triage_category = "manual_review"

    if (
        mpn_result.get("valid")
        and mpn_result.get("confidence", 0) >= 0.8
        and disagreement_score <= 0.2
        and verified is True
        and not indicators
    ):
        triage_category = "likely_confirmed"
        indicators.append("high_mpn_confidence_low_disagreement_verified_true")

    if (
        mpn_result.get("valid")
        and mpn_result.get("confidence", 0) >= 0.6
        and disagreement_score <= 0.15
        and not indicators
    ):
        triage_category = "likely_confirmed"
        indicators.append("reasonable_mpn_confidence_very_low_disagreement")

    if verification_raw and has_yt_link and not indicators:
        indicators.append("enrichment_v2_with_video_source")
        ocr_actionable = True
        if triage_category == "manual_review":
            triage_category = "ocr_needed"

    if (
        has_yt_link
        and not verification_raw
        and not has_frame_error
        and triage_category == "manual_review"
    ):
        ocr_actionable = True
        indicators.append("video_source_available_for_ocr")
        if triage_category == "manual_review":
            triage_category = "ocr_needed"

    if has_frame_error:
        indicators.append("frame_extraction_error_blocker")

    if not has_yt_link:
        indicators.append("no_video_source_ocr_not_actionable")
        ocr_actionable = False

    gemini_available = bool(os.environ.get("GEMINI_API_KEY"))

    return {
        "triage_category": triage_category,
        "triage_indicators": indicators,
        "ocr_actionable": ocr_actionable,
        "gemini_available": gemini_available,
        "recommended_action": _recommended_action(
            triage_category, ocr_actionable, gemini_available
        ),
    }


def _recommended_action(
    category: str, ocr_actionable: bool, gemini_available: bool
) -> str:
    if category == "threshold_tuning":
        return "adjust_scoring_rules: record should be rejected or recategorized by improved MPN heuristics"
    if category == "likely_confirmed":
        return "auto_promote: safe to promote to confirmed after threshold adjustment review"
    if category == "ocr_needed":
        if gemini_available:
            return "run_ocr_check: GEMINI_API_KEY available, run verify_candidates.py ocr-check"
        return "await_ocr: GEMINI_API_KEY not available, defer to next run with OCR enabled"
    return "manual_review: human reviewer needed to assess part number validity"


def try_ocr_check(
    records: list[dict[str, Any]],
    api_key: str | None = None,
) -> list[dict[str, Any]]:
    key = api_key or os.environ.get("GEMINI_API_KEY")
    if not key:
        return records

    try:
        from google import genai
        from google.genai import types as genai_types
    except ImportError:
        return records

    client = genai.Client(api_key=key)
    model = "gemma-4-31b-it"
    updated = []

    for rec in records:
        vs = rec.get("verification_status", "unknown")
        if vs != "disputed":
            updated.append(rec)
            continue

        yt_link = rec.get("yt_link", rec.get("source_video", ""))
        part_number = rec.get("part_number", "")
        part_name = rec.get("part_name", "")

        prompt = (
            f"You are verifying an electronic part identification from a teardown video.\n"
            f"Part name: {part_name}\n"
            f"Claimed part number: {part_number}\n"
            f"Video URL: {yt_link}\n\n"
            f"Is '{part_number}' a valid manufacturer part number for '{part_name}'? "
            f"Answer YES or NO with a brief reason."
        )

        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
            )
            answer = (response.text or "").strip().upper()
            if answer.startswith("YES"):
                rec["verification_status"] = "confirmed"
                rec["ocr_check"] = {"result": "confirmed", "raw": response.text}
            elif answer.startswith("NO"):
                rec["verification_status"] = "rejected"
                rec["ocr_check"] = {"result": "rejected", "raw": response.text}
            else:
                rec["ocr_check"] = {"result": "inconclusive", "raw": response.text}
        except Exception as e:
            rec["ocr_check"] = {"result": "error", "error": str(e)}

        updated.append(rec)

    return updated


def cmd_load(args: argparse.Namespace) -> dict[str, Any]:
    print("=== Verification Load: Reading candidate snapshot ===\n")

    snapshot_path = Path(args.input) if args.input else CANDIDATE_SNAPSHOT_PATH
    candidates = read_jsonl(snapshot_path)

    if not candidates:
        print(f" No candidates found at: {snapshot_path}")
        print(f" Ensure enrichment output exists before running verification.")
        return {"loaded": 0}

    print(f" Snapshot: {snapshot_path}")
    print(f" Records: {len(candidates)}")

    if candidates:
        sample = candidates[0]
        print(f" Fields: {list(sample.keys())}")

    devices = set()
    for c in candidates:
        d = c.get("device", "unknown")
        devices.add(d)
    print(f" Unique devices: {len(devices)}")

    verified_true = sum(
        1 for c in candidates if c.get("verification", {}).get("verified") is True
    )
    verified_false = sum(
        1 for c in candidates if c.get("verification", {}).get("verified") is False
    )
    verified_none = sum(
        1 for c in candidates if c.get("verification", {}).get("verified") is None
    )
    print(f" Enrichment verified=true: {verified_true}")
    print(f" Enrichment verified=false: {verified_false}")
    print(f" Enrichment verified=null: {verified_none}")

    print(f"\n=== Load complete ===")
    return {"loaded": len(candidates)}


def cmd_validate(args: argparse.Namespace) -> dict[str, Any]:
    print("=== Verification Validate: Rule-based MPN validation ===\n")

    snapshot_path = Path(args.input) if args.input else CANDIDATE_SNAPSHOT_PATH
    candidates = read_jsonl(snapshot_path)

    if not candidates:
        print(" No candidates to validate. Run 'load' first or provide --input.")
        return {"validated": 0}

    valid_count = 0
    invalid_count = 0
    reasons: dict[str, int] = {}

    for rec in candidates:
        pn = rec.get("part_number", "")
        result = classify_mpn_quality(pn)
        rec["_mpn_result"] = result
        if result["valid"]:
            valid_count += 1
        else:
            invalid_count += 1
        r = result["reason"]
        reasons[r] = reasons.get(r, 0) + 1

    print(f" Total: {len(candidates)}")
    print(f" Valid MPN: {valid_count}")
    print(f" Invalid MPN: {invalid_count}")
    print(f"\n Rejection reasons:")
    for reason, count in sorted(reasons.items(), key=lambda x: -x[1]):
        print(f"   {reason}: {count}")

    print(f"\n=== Validate complete ===")
    return {
        "validated": len(candidates),
        "valid": valid_count,
        "invalid": invalid_count,
    }


def cmd_ocr_check(args: argparse.Namespace) -> dict[str, Any]:
    print("=== Verification OCR Check: Multimodal frame verification ===\n")

    api_key = args.api_key or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print(" GEMINI_API_KEY not found. OCR check skipped.")
        print(" Set env var GEMINI_API_KEY or pass --api-key to enable.")
        print(" Verification can still proceed with rule-based scoring only.")
        return {"ocr_checked": 0, "fallback": "rule_based_only"}

    snapshot_path = Path(args.input) if args.input else CANDIDATE_SNAPSHOT_PATH
    candidates = read_jsonl(snapshot_path)

    pre_scored = REPORTS_DIR / "verification_scored.jsonl"
    if pre_scored.exists():
        candidates = read_jsonl(pre_scored)

    disputed_count = sum(
        1 for c in candidates if c.get("verification_status") == "disputed"
    )
    print(f" Disputed records to OCR-check: {disputed_count}")
    print(f" Starting OCR verification (model: gemma-4-31b-it)...")

    updated = try_ocr_check(candidates, api_key)

    ocr_results = {}
    for rec in updated:
        ocr = rec.get("ocr_check", {})
        r = ocr.get("result", "skipped")
        ocr_results[r] = ocr_results.get(r, 0) + 1

    print(f"\n OCR results:")
    for result, count in sorted(ocr_results.items()):
        print(f"   {result}: {count}")

    scored_path = REPORTS_DIR / "verification_scored.jsonl"
    write_jsonl(scored_path, updated)
    print(f"\n Scored records (with OCR) saved to: {scored_path}")

    print(f"\n=== OCR Check complete ===")
    return {"ocr_checked": disputed_count, "results": ocr_results}


def cmd_score(args: argparse.Namespace) -> dict[str, Any]:
    print("=== Verification Score: Computing disagreement scores ===\n")

    snapshot_path = Path(args.input) if args.input else CANDIDATE_SNAPSHOT_PATH
    candidates = read_jsonl(snapshot_path)

    if not candidates:
        print(" No candidates to score. Provide --input with candidate snapshot.")
        return {"scored": 0}

    for rec in candidates:
        mpn_result = rec.get("_mpn_result")
        if not mpn_result:
            pn = rec.get("part_number", "")
            mpn_result = classify_mpn_quality(pn)
            rec["_mpn_result"] = mpn_result

        cross_check = cross_check_enrichment(rec)
        rec["_cross_check"] = cross_check

        disagreement = compute_disagreement_score(mpn_result, cross_check, rec)
        rec["disagreement_score"] = disagreement

        status = assign_verification_status(mpn_result, cross_check, disagreement, rec)
        rec["verification_status"] = status

    status_counts: dict[str, int] = {}
    for rec in candidates:
        s = rec["verification_status"]
        status_counts[s] = status_counts.get(s, 0) + 1

    print(f" Total scored: {len(candidates)}")
    for status in ["confirmed", "disputed", "rejected"]:
        print(f"   {status}: {status_counts.get(status, 0)}")

    avg_disagreement = sum(rec["disagreement_score"] for rec in candidates) / max(
        len(candidates), 1
    )
    print(f" Avg disagreement score: {avg_disagreement:.3f}")

    scored_path = REPORTS_DIR / "verification_scored.jsonl"
    write_jsonl(scored_path, candidates)
    print(f"\n Scored records saved to: {scored_path}")

    print(f"\n=== Score complete ===")
    return {"scored": len(candidates), "status_counts": status_counts}


def cmd_triage(args: argparse.Namespace) -> dict[str, Any]:
    print("=== Verification Triage: Classifying disputed records ===\n")

    scored_path = REPORTS_DIR / "verification_scored.jsonl"
    if not scored_path.exists():
        print(" No scored records found. Run 'score' first.")
        return {"triaged": 0}

    candidates = read_jsonl(scored_path)
    disputed = [
        rec for rec in candidates if rec.get("verification_status") == "disputed"
    ]

    if not disputed:
        print(" No disputed records to triage.")
        return {"triaged": 0}

    print(f" Disputed records to triage: {len(disputed)}\n")

    triage_counts: dict[str, int] = {}
    triaged_records: list[dict[str, Any]] = []
    all_indicators: dict[str, int] = {}

    for rec in disputed:
        triage = classify_disputed_triage(rec)
        rec["triage"] = triage
        cat = triage["triage_category"]
        triage_counts[cat] = triage_counts.get(cat, 0) + 1
        for ind in triage.get("triage_indicators", []):
            all_indicators[ind] = all_indicators.get(ind, 0) + 1

        triaged_records.append(
            {
                "part_number": rec.get("part_number", ""),
                "part_name": rec.get("part_name", ""),
                "device": rec.get("device", ""),
                "disagreement_score": rec.get("disagreement_score", 0.0),
                "confidence": rec.get("confidence", 0.0),
                "verification_status": rec.get("verification_status", ""),
                "triage_category": cat,
                "triage_indicators": triage["triage_indicators"],
                "ocr_actionable": triage["ocr_actionable"],
                "recommended_action": triage["recommended_action"],
            }
        )

    gemini_available = bool(os.environ.get("GEMINI_API_KEY"))

    print(" Triage categories:")
    for cat in ["likely_confirmed", "ocr_needed", "manual_review", "threshold_tuning"]:
        count = triage_counts.get(cat, 0)
        print(f"   {cat}: {count}")
    print()
    print(" Triage indicators:")
    for ind, count in sorted(all_indicators.items(), key=lambda x: -x[1]):
        print(f"   {ind}: {count}")
    print()
    print(f" GEMINI_API_KEY available: {gemini_available}")
    print(
        f" OCR-actionable records: {sum(1 for r in triaged_records if r['ocr_actionable'])}"
    )
    print()

    dry_run = getattr(args, "dry_run", False)
    triage_path = TRIAGE_REPORT_PATH
    if dry_run:
        triage_path = TRIAGE_REPORT_PATH.parent / (
            TRIAGE_REPORT_PATH.name + DRY_RUN_SUFFIX
        )

    write_jsonl(triage_path, triaged_records)
    print(f" Triage report written: {triage_path}")

    write_jsonl(scored_path, candidates)
    print(f" Scored records updated with triage: {scored_path}")

    print(f"\n=== Triage complete ===")
    return {
        "triaged": len(disputed),
        "triage_counts": triage_counts,
        "gemini_available": gemini_available,
    }


def cmd_resolve_status(args: argparse.Namespace) -> dict[str, Any]:
    print("=== Verification Resolve Status: Applying status resolution policy ===\n")

    scored_path = REPORTS_DIR / "verification_scored.jsonl"
    if not scored_path.exists():
        print(" No scored records found. Run 'score' and 'triage' first.")
        return {"resolved": 0}

    candidates = read_jsonl(scored_path)

    status_before: dict[str, int] = {}
    for rec in candidates:
        s = rec.get("verification_status", "unknown")
        status_before[s] = status_before.get(s, 0) + 1

    resolution_log: list[dict[str, Any]] = []
    ocr_needed_remaining: list[dict[str, Any]] = []
    manual_review_remaining: list[dict[str, Any]] = []

    for rec in candidates:
        if rec.get("verification_status") != "disputed":
            continue

        triage = rec.get("triage", {})
        if not triage:
            triage = classify_disputed_triage(rec)
            rec["triage"] = triage

        cat = triage.get("triage_category", "manual_review")
        policy = STATUS_RESOLUTION_POLICY.get(cat, STATUS_RESOLUTION_POLICY["manual_review"])

        old_status = rec["verification_status"]

        if cat == "likely_confirmed":
            mpn_result = rec.get("_mpn_result") or classify_mpn_quality(rec.get("part_number", ""))
            rec["_mpn_result"] = mpn_result
            indicators = triage.get("triage_indicators", [])
            has_threshold_indicator = any(
                ind in indicators
                for ind in [
                    "designator_list_not_mpn",
                    "date_code_in_part_number",
                    "model_label_not_mpn",
                    "patent_number_in_part_number",
                    "full_model_string_not_mpn",
                    "comma_separated_list",
                ]
            )
            if mpn_result.get("valid") and not has_threshold_indicator:
                rec["verification_status"] = "confirmed"
                rec["status_resolution"] = {
                    "policy": "likely_confirmed_promote_v2",
                    "from": old_status,
                    "to": "confirmed",
                    "triage_category": cat,
                    "audit_note": policy["audit_note"],
                    "resolved_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                }
                resolution_log.append({
                    "part_number": rec.get("part_number", ""),
                    "part_name": rec.get("part_name", ""),
                    "triage_category": cat,
                    "from": old_status,
                    "to": "confirmed",
                    "audit_note": policy["audit_note"],
                })
            else:
                rec["verification_status"] = "rejected"
                rec["status_resolution"] = {
                    "policy": "likely_confirmed_blocked_by_threshold_v2",
                    "from": old_status,
                    "to": "rejected",
                    "triage_category": cat,
                    "audit_note": "Likely_confirmed blocked by threshold indicators; rejected per policy v2",
                    "resolved_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                }
                resolution_log.append({
                    "part_number": rec.get("part_number", ""),
                    "part_name": rec.get("part_name", ""),
                    "triage_category": cat,
                    "from": old_status,
                    "to": "rejected",
                    "audit_note": "likely_confirmed blocked by threshold indicators",
                })

        elif cat == "threshold_tuning":
            mpn_result = rec.get("_mpn_result") or classify_mpn_quality(rec.get("part_number", ""))
            rec["_mpn_result"] = mpn_result
            if not mpn_result.get("valid"):
                rec["verification_status"] = "rejected"
            else:
                rec["verification_status"] = "rejected"
            rec["status_resolution"] = {
                "policy": "threshold_tuning_reject_v2",
                "from": old_status,
                "to": "rejected",
                "triage_category": cat,
                "audit_note": policy["audit_note"],
                "resolved_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
            resolution_log.append({
                "part_number": rec.get("part_number", ""),
                "part_name": rec.get("part_name", ""),
                "triage_category": cat,
                "from": old_status,
                "to": "rejected",
                "audit_note": policy["audit_note"],
            })

        elif cat == "ocr_needed":
            ocr_needed_remaining.append({
                "part_number": rec.get("part_number", ""),
                "part_name": rec.get("part_name", ""),
                "device": rec.get("device", ""),
                "triage_category": cat,
                "ocr_actionable": triage.get("ocr_actionable", False),
                "audit_note": policy["audit_note"],
            })
            rec["status_resolution"] = {
                "policy": "ocr_needed_defer_v2",
                "from": old_status,
                "to": "disputed",
                "triage_category": cat,
                "audit_note": policy["audit_note"],
                "resolved_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            }

        elif cat == "manual_review":
            manual_review_remaining.append({
                "part_number": rec.get("part_number", ""),
                "part_name": rec.get("part_name", ""),
                "device": rec.get("device", ""),
                "triage_category": cat,
                "triage_indicators": triage.get("triage_indicators", []),
                "audit_note": policy["audit_note"],
            })
            rec["status_resolution"] = {
                "policy": "manual_review_defer_v2",
                "from": old_status,
                "to": "disputed",
                "triage_category": cat,
                "audit_note": policy["audit_note"],
                "resolved_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            }

    status_after: dict[str, int] = {}
    for rec in candidates:
        s = rec.get("verification_status", "unknown")
        status_after[s] = status_after.get(s, 0) + 1

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    packet: dict[str, Any] = {
        "generated_at": now,
        "policy_version": "v2",
        "status_before": status_before,
        "status_after": status_after,
        "resolution_log": resolution_log,
        "ocr_needed_remaining": ocr_needed_remaining,
        "manual_review_remaining": manual_review_remaining,
        "blocked_for_clean_snapshot": [],
    }

    if ocr_needed_remaining:
        packet["blocked_for_clean_snapshot"].extend(
            [f"ocr_needed: {r['part_number']}" for r in ocr_needed_remaining]
        )
    if manual_review_remaining:
        packet["blocked_for_clean_snapshot"].extend(
            [f"manual_review: {r['part_number']}" for r in manual_review_remaining]
        )

    dry_run = getattr(args, "dry_run", False)
    packet_path = STATUS_RESOLUTION_PACKET_PATH
    if dry_run:
        packet_path = STATUS_RESOLUTION_PACKET_PATH.parent / (
            STATUS_RESOLUTION_PACKET_PATH.name + DRY_RUN_SUFFIX
        )

    write_json(packet_path, packet)

    print(" Status resolution policy applied:")
    for status in ["confirmed", "disputed", "rejected"]:
        before = status_before.get(status, 0)
        after = status_after.get(status, 0)
        delta = after - before
        sign = "+" if delta > 0 else ""
        print(f"  {status}: {before} -> {after} ({sign}{delta})")

    print(f"\n Resolutions applied: {len(resolution_log)}")
    print(f" Still deferred (ocr_needed): {len(ocr_needed_remaining)}")
    print(f" Still deferred (manual_review): {len(manual_review_remaining)}")
    print(f" Blocked for clean snapshot: {len(packet['blocked_for_clean_snapshot'])}")
    print(f"\n Status resolution packet: {packet_path}")

    write_jsonl(scored_path, candidates)
    print(f" Scored records updated with resolution: {scored_path}")

    print(f"\n=== Resolve Status complete ===")
    return {
        "resolved": len(resolution_log),
        "status_before": status_before,
        "status_after": status_after,
        "ocr_needed_remaining": len(ocr_needed_remaining),
        "manual_review_remaining": len(manual_review_remaining),
    }


DEFERRED_WORKPACK_JSON_PATH = REPORTS_DIR / "deferred_resolution_workpack.json"
DEFERRED_WORKPACK_MD_PATH = REPORTS_DIR / "deferred_resolution_workpack.md"
OCR_DEFERRED_CASE_PACKET_PATH = REPORTS_DIR / "ocr_deferred_case_packet.json"


def cmd_deferred_workpack(args: argparse.Namespace) -> dict[str, Any]:
    print("=== Verification Deferred Workpack: Generating operator-ready packet for deferred cases ===\n")

    resolution_path = STATUS_RESOLUTION_PACKET_PATH
    if getattr(args, "dry_run", False):
        alt = STATUS_RESOLUTION_PACKET_PATH.parent / (STATUS_RESOLUTION_PACKET_PATH.name + DRY_RUN_SUFFIX)
        if alt.exists():
            resolution_path = alt

    if not resolution_path.exists():
        print(" No status resolution packet found. Run 'resolve-status' first.")
        return {"workpack": False}

    with open(resolution_path, "r", encoding="utf-8") as f:
        resolution_packet = json.load(f)

    ocr_needed = resolution_packet.get("ocr_needed_remaining", [])
    manual_review = resolution_packet.get("manual_review_remaining", [])

    if not ocr_needed and not manual_review:
        print(" No deferred cases remaining. Workpack not needed.")
        return {"workpack": False, "ocr_needed": 0, "manual_review": 0}

    verified_path = VERIFIED_SNAPSHOT_PATH
    if getattr(args, "dry_run", False):
        alt = VERIFIED_SNAPSHOT_PATH.parent / (VERIFIED_SNAPSHOT_PATH.name + DRY_RUN_SUFFIX)
        if alt.exists():
            verified_path = alt

    verified_records = read_jsonl(verified_path)
    verified_by_pn: dict[str, dict[str, Any]] = {}
    for rec in verified_records:
        pn = rec.get("part_number", "")
        if pn:
            verified_by_pn[pn] = rec

    review_queue_path = REPORTS_DIR / "curation_review_queue.jsonl"
    review_queue = read_jsonl(review_queue_path) if review_queue_path.exists() else []
    candidate_id_by_pn: dict[str, str] = {}
    for entry in review_queue:
        pn = entry.get("part_number", "")
        cid = entry.get("candidate_id", "")
        if pn and cid:
            candidate_id_by_pn[pn] = cid

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    ocr_entries: list[dict[str, Any]] = []
    for case in ocr_needed:
        pn = case.get("part_number", "")
        rec = verified_by_pn.get(pn, {})
        verification_raw = rec.get("verification_raw", {})
        entry: dict[str, Any] = {
            "candidate_id": candidate_id_by_pn.get(pn, ""),
            "part_number": pn,
            "part_name": case.get("part_name", ""),
            "device": case.get("device", ""),
            "disagreement_score": rec.get("disagreement_score", 0.0),
            "confidence": rec.get("confidence", 0.0),
            "triage_indicators": case.get("triage_indicators", rec.get("triage", {}).get("triage_indicators", [])),
            "evidence_url": rec.get("yt_link", ""),
            "source_video": rec.get("source_video", ""),
            "verification_observed_text": rec.get("verification", {}).get("observed_text", ""),
            "verification_verified": rec.get("verification", {}).get("verified"),
            "datasheet_url": rec.get("datasheet_url"),
            "footprint": rec.get("footprint"),
            "ocr_actionable": case.get("ocr_actionable", True),
            "next_action": "run_ocr_check",
            "next_action_detail": f"GEMINI_API_KEY required. Run: GEMINI_API_KEY=... python3 scripts/verify_candidates.py ocr-check. Verify '{pn}' against video frame for {case.get('part_name', '')} on {case.get('device', '')}.",
            "resolution_if_ocr_confirms": "promote to confirmed -> re-run curation pipeline",
            "resolution_if_ocr_rejects": "reject -> update status_resolution -> re-run curation",
            "resolution_if_ocr_inconclusive": "escalate to manual_review",
        }
        if verification_raw:
            entry["verification_raw_verified"] = verification_raw.get("verified")
            entry["verification_raw_observed_text"] = verification_raw.get("observed_text", "")
        ocr_entries.append(entry)

    manual_entries: list[dict[str, Any]] = []
    for case in manual_review:
        pn = case.get("part_number", "")
        rec = verified_by_pn.get(pn, {})
        verification_raw = rec.get("verification_raw", {})
        m_entry: dict[str, Any] = {
            "candidate_id": candidate_id_by_pn.get(pn, ""),
            "part_number": pn,
            "part_name": case.get("part_name", ""),
            "device": case.get("device", ""),
            "disagreement_score": rec.get("disagreement_score", 0.0),
            "confidence": rec.get("confidence", 0.0),
            "triage_indicators": case.get("triage_indicators", rec.get("triage", {}).get("triage_indicators", [])),
            "evidence_url": rec.get("yt_link", ""),
            "source_video": rec.get("source_video", ""),
            "verification_observed_text": rec.get("verification", {}).get("observed_text", ""),
            "verification_verified": rec.get("verification", {}).get("verified"),
            "datasheet_url": rec.get("datasheet_url"),
            "footprint": rec.get("footprint"),
            "ocr_actionable": False,
            "next_action": "human_review_decision",
            "next_action_detail": f"Human reviewer must decide: Is '{pn}' a valid catalog entry for {case.get('part_name', '')}?",
            "decision_options": ["accept", "reject", "defer"],
        }
        if verification_raw:
            m_entry["verification_raw_verified"] = verification_raw.get("verified")
            m_entry["verification_raw_observed_text"] = verification_raw.get("observed_text", "")
        manual_entries.append(m_entry)

    workpack_json: dict[str, Any] = {
        "generated_at": now,
        "pack": "pack-project13-kaggle-verification-01",
        "description": "Operator-ready workpack for deferred verification cases. Each case has evidence, next action, and resolution path.",
        "total_cases": len(ocr_entries) + len(manual_entries),
        "ocr_needed_cases": len(ocr_entries),
        "manual_review_cases": len(manual_entries),
        "ocr_needed": ocr_entries,
        "manual_review": manual_entries,
        "procedure_when_gemini_available": [
            "1. Set GEMINI_API_KEY environment variable",
            "2. Run: GEMINI_API_KEY=... python3 scripts/verify_candidates.py ocr-check",
            "3. Review OCR results in verification_scored.jsonl for ocr_needed cases",
            "4. Re-run full pipeline: python3 scripts/verify_candidates.py run",
            "5. Then re-run curation: python3 scripts/curate_candidates.py dry-run --fallback-test-db",
            "6. Then re-check export gate: python3 scripts/curate_candidates.py export-gate",
        ],
        "procedure_for_human_review": [
            "1. Read reviewer_context for each manual_review case",
            "2. Choose one of the decision_options",
            "3. Update curation_review_queue.jsonl: set reviewed_by, reviewed_at, and review_status",
            "4. Re-run: python3 scripts/curate_candidates.py export-gate",
        ],
        "dependencies": {
            "ocr_needed": "GEMINI_API_KEY (not currently available)",
            "manual_review": "Human reviewer decision (no automated resolution possible)",
        },
        "provenance": {
            "status_resolution_packet": str(resolution_path),
            "verification_report": str(VERIFICATION_REPORT_PATH),
            "verification_triage": str(TRIAGE_REPORT_PATH),
            "verification_disagreements": str(DISAGREEMENT_LOG_PATH),
            "curation_review_queue": str(review_queue_path) if review_queue_path.exists() else "not yet generated",
            "export_gate_packet": str(REPORTS_DIR / "export_gate_packet.json"),
            "verified_snapshot": str(verified_path),
        },
    }

    dry_run = getattr(args, "dry_run", False)
    workpack_json_path = DEFERRED_WORKPACK_JSON_PATH
    workpack_md_path = DEFERRED_WORKPACK_MD_PATH
    if dry_run:
        workpack_json_path = DEFERRED_WORKPACK_JSON_PATH.parent / (DEFERRED_WORKPACK_JSON_PATH.name + DRY_RUN_SUFFIX)
        workpack_md_path = DEFERRED_WORKPACK_MD_PATH.parent / (DEFERRED_WORKPACK_MD_PATH.name + DRY_RUN_SUFFIX)

    write_json(workpack_json_path, workpack_json)

    md_lines = [
        "# Deferred Resolution Workpack",
        "",
        f"Generated: {now}",
        "Pack: pack-project13-kaggle-verification-01",
        "",
        "## Summary",
        "",
        f"{len(ocr_entries) + len(manual_entries)} deferred verification cases need resolution.",
        "",
        "| Track | Count | Requirement |",
        "|-------|-------|-------------|",
        f"| ocr_needed | {len(ocr_entries)} | GEMINI_API_KEY |",
        f"| manual_review | {len(manual_entries)} | Human reviewer decision |",
        "",
    ]

    if ocr_entries:
        md_lines.append("## OCR-Needed Cases")
        md_lines.append("")
        for i, entry in enumerate(ocr_entries, 1):
            md_lines.append(f"### {i}. {entry['part_number']} — {entry['part_name']} ({entry['device']})")
            md_lines.append("")
            md_lines.append(f"- **candidate_id**: {entry.get('candidate_id', 'unknown')}")
            md_lines.append(f"- **disagreement**: {entry.get('disagreement_score', 0)}, **confidence**: {entry.get('confidence', 0)}")
            md_lines.append(f"- **evidence_url**: {entry.get('evidence_url', 'N/A')}")
            md_lines.append(f"- **observed_text**: {entry.get('verification_observed_text', 'N/A')}")
            if entry.get("footprint"):
                md_lines.append(f"- **footprint**: {entry['footprint']}")
            md_lines.append(f"- **next_action**: {entry.get('next_action', '')}")
            md_lines.append(f"- **next_action_detail**: {entry.get('next_action_detail', '')}")
            md_lines.append(f"- **if confirmed**: {entry.get('resolution_if_ocr_confirms', '')}")
            md_lines.append(f"- **if rejected**: {entry.get('resolution_if_ocr_rejects', '')}")
            md_lines.append(f"- **if inconclusive**: {entry.get('resolution_if_ocr_inconclusive', '')}")
            md_lines.append("")

    if manual_entries:
        md_lines.append("## Manual Review Cases")
        md_lines.append("")
        for i, entry in enumerate(manual_entries, 1):
            md_lines.append(f"### {i}. {entry['part_number']} — {entry['part_name']} ({entry['device']})")
            md_lines.append("")
            md_lines.append(f"- **candidate_id**: {entry.get('candidate_id', 'unknown')}")
            md_lines.append(f"- **disagreement**: {entry.get('disagreement_score', 0)}, **confidence**: {entry.get('confidence', 0)}")
            md_lines.append(f"- **evidence_url**: {entry.get('evidence_url', 'N/A')}")
            md_lines.append(f"- **observed_text**: {entry.get('verification_observed_text', 'N/A')}")
            if entry.get("footprint"):
                md_lines.append(f"- **footprint**: {entry['footprint']}")
            md_lines.append(f"- **next_action**: {entry.get('next_action', '')}")
            md_lines.append(f"- **decision_options**: {', '.join(entry.get('decision_options', []))}")
            md_lines.append("")

    md_lines.extend([
        "## Procedures",
        "",
        "### When GEMINI_API_KEY becomes available",
        "",
        "```bash",
        "GEMINI_API_KEY=... python3 scripts/verify_candidates.py ocr-check",
        "python3 scripts/verify_candidates.py run",
        "python3 scripts/curate_candidates.py dry-run --fallback-test-db",
        "python3 scripts/curate_candidates.py export-gate",
        "```",
        "",
        "### For human reviewer decisions",
        "",
        "1. Read case details above",
        "2. Choose one of the decision_options",
        "3. Update `curation_review_queue.jsonl`: set `reviewed_by`, `reviewed_at`, `review_status`",
        "4. Re-run: `python3 scripts/curate_candidates.py export-gate`",
        "",
        f"JSON workpack: `{workpack_json_path}`",
        "",
    ])

    workpack_md_path.parent.mkdir(parents=True, exist_ok=True)
    workpack_md_path.write_text("\n".join(md_lines), encoding="utf-8")

    print(f" OCR-needed cases: {len(ocr_entries)}")
    print(f" Manual review cases: {len(manual_entries)}")
    print(f" Total deferred cases: {len(ocr_entries) + len(manual_entries)}")
    print(f"\n JSON workpack: {workpack_json_path}")
    print(f" Markdown workpack: {workpack_md_path}")
    print(f"\n=== Deferred Workpack complete ===")

    return {
        "workpack": True,
        "ocr_needed": len(ocr_entries),
        "manual_review": len(manual_entries),
        "json_path": str(workpack_json_path),
        "md_path": str(workpack_md_path),
    }


def build_ocr_case_map() -> list[dict[str, Any]]:
    workpack_path = DEFERRED_WORKPACK_JSON_PATH
    if not workpack_path.exists():
        return []
    with open(workpack_path, "r", encoding="utf-8") as f:
        workpack = json.load(f)
    ocr_cases = workpack.get("ocr_needed", [])
    case_map: list[dict[str, Any]] = []
    for case in ocr_cases:
        candidate_id = case.get("candidate_id", "")
        part_number = case.get("part_number", "")
        evidence_url = case.get("evidence_url", "")
        source_video = case.get("source_video", "")
        observed_text = case.get("verification_observed_text", "") or case.get("verification_raw_observed_text", "")
        part_name = case.get("part_name", "")
        device = case.get("device", "")
        disagreement_score = case.get("disagreement_score", 0.0)
        confidence = case.get("confidence", 0.0)
        footprint = case.get("footprint")
        datasheet_url = case.get("datasheet_url")
        cmd = f"GEMINI_API_KEY=... python3 scripts/verify_candidates.py ocr-selector --case {candidate_id}"
        case_map.append({
            "candidate_id": candidate_id,
            "part_number": part_number,
            "part_name": part_name,
            "device": device,
            "evidence_url": evidence_url,
            "source_video": source_video,
            "expected_text": observed_text,
            "disagreement_score": disagreement_score,
            "confidence": confidence,
            "footprint": footprint,
            "datasheet_url": datasheet_url,
            "next_command": cmd,
            "next_action": case.get("next_action", "run_ocr_check"),
            "resolution_if_ocr_confirms": case.get("resolution_if_ocr_confirms", ""),
            "resolution_if_ocr_rejects": case.get("resolution_if_ocr_rejects", ""),
            "resolution_if_ocr_inconclusive": case.get("resolution_if_ocr_inconclusive", ""),
        })
    return case_map


def cmd_ocr_selector(args: argparse.Namespace) -> dict[str, Any]:
    print("=== Verification OCR Selector: Surgical case-level OCR execution surface ===\n")

    case_map = build_ocr_case_map()
    if not case_map:
        print(" No OCR-deferred cases found. Run 'deferred-workpack' first.")
        return {"selector": False, "cases": 0}

    case_filter = getattr(args, "case", None)
    group_filter = getattr(args, "group", None)

    if case_filter:
        selected = [c for c in case_map if c["candidate_id"] == case_filter]
        if not selected:
            print(f" Case '{case_filter}' not found. Available:")
            for c in case_map:
                print(f"  {c['candidate_id']}: {c['part_number']} ({c['part_name']})")
            return {"selector": False, "cases": 0, "reason": "case_not_found"}
        print(f" Selected single case: {case_filter}")
        selected_map = selected
    elif group_filter:
        video_groups: dict[str, list[dict[str, Any]]] = {}
        for c in case_map:
            vid = c.get("source_video", "unknown")
            video_groups.setdefault(vid, []).append(c)
        if group_filter not in video_groups:
            print(f" Group '{group_filter}' not found. Available video sources:")
            for vid, cases in video_groups.items():
                ids = [c["candidate_id"] for c in cases]
                print(f"  {vid}: {ids}")
            return {"selector": False, "cases": 0, "reason": "group_not_found"}
        selected_map = video_groups[group_filter]
        print(f" Selected group: {len(selected_map)} cases from same video")
    else:
        selected_map = case_map

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    packet: dict[str, Any] = {
        "generated_at": now,
        "pack": "pack-project13-kaggle-verification-01",
        "description": "OCR deferred case selector and prompt packet. Each case is independently actionable with GEMINI_API_KEY.",
        "total_ocr_cases": len(case_map),
        "selected_cases": len(selected_map),
        "selection_filter": case_filter or group_filter or "all",
        "ocr_cases": selected_map,
        "video_source_groups": {},
        "operator_instructions": {
            "step_1_set_key": "export GEMINI_API_KEY=your_key_here",
            "step_2_single_case": "python3 scripts/verify_candidates.py ocr-selector --case candidate-XXXX",
            "step_2_group": "python3 scripts/verify_candidates.py ocr-selector --group <video_url>",
            "step_2_all": "python3 scripts/verify_candidates.py ocr-selector",
            "step_3_run_ocr": "python3 scripts/verify_candidates.py ocr-check",
            "step_4_review": "Check verification_scored.jsonl for ocr_check results per candidate_id",
            "step_5_rerun_pipeline": "python3 scripts/verify_candidates.py run",
            "step_6_rerun_curation": "python3 scripts/curate_candidates.py dry-run --fallback-test-db",
            "step_7_check_gate": "python3 scripts/curate_candidates.py export-gate",
            "important": "Do NOT mark any OCR case as resolved without a real OCR run and result review.",
        },
    }

    video_groups: dict[str, list[str]] = {}
    for c in case_map:
        vid = c.get("source_video", "unknown")
        video_groups.setdefault(vid, []).append(c["candidate_id"])
    packet["video_source_groups"] = video_groups

    dry_run = getattr(args, "dry_run", False)
    out_path = OCR_DEFERRED_CASE_PACKET_PATH
    if dry_run:
        out_path = OCR_DEFERRED_CASE_PACKET_PATH.parent / (
            OCR_DEFERRED_CASE_PACKET_PATH.name + DRY_RUN_SUFFIX
        )

    write_json(out_path, packet)

    print(f"\n OCR deferred case map ({len(selected_map)} case(s)):")
    print(f" {'candidate_id':<18} {'part_number':<20} {'expected_text':<20} {'evidence_url'}")
    print(f" {'-'*18} {'-'*20} {'-'*20} {'-'*40}")
    for c in selected_map:
        ev_short = c["evidence_url"][:60] + "..." if len(c["evidence_url"]) > 60 else c["evidence_url"]
        print(f" {c['candidate_id']:<18} {c['part_number']:<20} {c['expected_text']:<20} {ev_short}")

    print(f"\n Video source grouping (cases runnable in single OCR pass):")
    for vid, cids in video_groups.items():
        print(f"  {vid[:60]}...")
        for cid in cids:
            c = next(x for x in case_map if x["candidate_id"] == cid)
            print(f"    {cid}: {c['part_number']} -> expected: '{c['expected_text']}'")

    print(f"\n Operator instructions when GEMINI_API_KEY available:")
    print(f"  1. export GEMINI_API_KEY=your_key_here")
    print(f"  2. Single case: python3 scripts/verify_candidates.py ocr-selector --case candidate-XXXX")
    print(f"  3. Or run OCR directly: GEMINI_API_KEY=... python3 scripts/verify_candidates.py ocr-check")
    print(f"  4. Review: verification_scored.jsonl -> ocr_check field per candidate_id")
    print(f"  5. Re-run pipeline: python3 scripts/verify_candidates.py run")
    print(f"  6. Re-run curation: python3 scripts/curate_candidates.py dry-run --fallback-test-db")
    print(f"  7. Check export gate: python3 scripts/curate_candidates.py export-gate")

    print(f"\n OCR case packet written: {out_path}")
    print(f"\n=== OCR Selector complete ===")
    return {
        "selector": True,
        "total_ocr_cases": len(case_map),
        "selected_cases": len(selected_map),
        "video_groups": len(video_groups),
        "packet_path": str(out_path),
    }


def cmd_snapshot(args: argparse.Namespace) -> dict[str, Any]:
    print("=== Verification Snapshot: Writing verified snapshot ===\n")

    scored_path = REPORTS_DIR / "verification_scored.jsonl"
    if not scored_path.exists():
        print(" No scored records found. Run 'score' first.")
        return {"written": 0}

    candidates = read_jsonl(scored_path)

    dry_run = getattr(args, "dry_run", False)
    output_path = VERIFIED_SNAPSHOT_PATH
    if dry_run:
        output_path = VERIFIED_SNAPSHOT_PATH.parent / (
            VERIFIED_SNAPSHOT_PATH.name + DRY_RUN_SUFFIX
        )

    clean_records = []
    for rec in candidates:
        clean = {k: v for k, v in rec.items() if not k.startswith("_")}
        clean_records.append(clean)

    write_jsonl(output_path, clean_records)

    status_counts: dict[str, int] = {}
    for rec in clean_records:
        s = rec.get("verification_status", "unknown")
        status_counts[s] = status_counts.get(s, 0) + 1

    print(f" Records written: {len(clean_records)}")
    for status in ["confirmed", "disputed", "rejected"]:
        print(f"   {status}: {status_counts.get(status, 0)}")
    print(f" Output: {output_path}")

    disagreements = [
        rec for rec in clean_records if rec.get("verification_status") == "disputed"
    ]

    disagreement_path = DISAGREEMENT_LOG_PATH
    if dry_run:
        disagreement_path = DISAGREEMENT_LOG_PATH.parent / (
            DISAGREEMENT_LOG_PATH.name + DRY_RUN_SUFFIX
        )

    write_jsonl(disagreement_path, disagreements)
    print(f" Disagreements written: {len(disagreements)}")
    print(f" Disagreement log: {disagreement_path}")

    print(f"\n=== Snapshot complete ===")
    return {
        "written": len(clean_records),
        "disagreements": len(disagreements),
        "output_path": str(output_path),
    }


def cmd_report(args: argparse.Namespace) -> dict[str, Any]:
    print("=== Verification Report: Generating verification_report.md ===\n")

    dry_run = getattr(args, "dry_run", False)

    verified_path = VERIFIED_SNAPSHOT_PATH
    if dry_run:
        alt = VERIFIED_SNAPSHOT_PATH.parent / (
            VERIFIED_SNAPSHOT_PATH.name + DRY_RUN_SUFFIX
        )
        if alt.exists():
            verified_path = alt

    disagreement_path = DISAGREEMENT_LOG_PATH
    if dry_run:
        alt = DISAGREEMENT_LOG_PATH.parent / (
            DISAGREEMENT_LOG_PATH.name + DRY_RUN_SUFFIX
        )
        if alt.exists():
            disagreement_path = alt

    candidates = read_jsonl(verified_path)
    disagreements = read_jsonl(disagreement_path)

    triage_path = TRIAGE_REPORT_PATH
    if dry_run:
        alt_t = TRIAGE_REPORT_PATH.parent / (TRIAGE_REPORT_PATH.name + DRY_RUN_SUFFIX)
        if alt_t.exists():
            triage_path = alt_t
    triage_records = read_jsonl(triage_path) if triage_path.exists() else []

    resolution_packet_path = STATUS_RESOLUTION_PACKET_PATH
    if dry_run:
        alt_r = STATUS_RESOLUTION_PACKET_PATH.parent / (STATUS_RESOLUTION_PACKET_PATH.name + DRY_RUN_SUFFIX)
        if alt_r.exists():
            resolution_packet_path = alt_r
    resolution_packet = {}
    if resolution_packet_path.exists():
        with open(resolution_packet_path, "r", encoding="utf-8") as f:
            resolution_packet = json.load(f)

    if not candidates:
        print(" No verified records found. Run 'score' and 'snapshot' first.")
        return {"report": False}

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    input_ref = str(Path(args.input) if args.input else CANDIDATE_SNAPSHOT_PATH)

    status_counts: dict[str, int] = {"confirmed": 0, "disputed": 0, "rejected": 0}
    for rec in candidates:
        s = rec.get("verification_status", "unknown")
        status_counts[s] = status_counts.get(s, 0) + 1

    devices: set[str] = set()
    for rec in candidates:
        devices.add(rec.get("device", "unknown"))

    key_disputed = disagreements[:10]

    lines = [
        "# Verification Report",
        "",
        f"Generated: {now}",
        f"Pack: pack-project13-kaggle-verification-01",
        f"Execution surface: scripts/verify_candidates.py",
        "",
        "## Input",
        "",
        f"- Source snapshot: `{input_ref}`",
        f"- Records loaded: {len(candidates)}",
        f"- Unique devices: {len(devices)}",
        "",
        "## Results",
        "",
        "| Status | Count |",
        "|--------|-------|",
        f"| Confirmed | {status_counts['confirmed']} |",
        f"| Disputed | {status_counts['disputed']} |",
        f"| Rejected | {status_counts['rejected']} |",
        f"| **Total** | {len(candidates)} |",
        "",
        "## Disagreement summary",
        "",
        f"- Disputed records: {len(disagreements)}",
        f"- Disagreement log: `{disagreement_path}`",
        "",
    ]

    if key_disputed:
        lines.append("### Key disputed cases")
        lines.append("")
        for d in key_disputed:
            pn = d.get("part_number", "?")
            device = d.get("device", "?")
            ds = d.get("disagreement_score", 0.0)
            triage = d.get("triage", {})
            cat = triage.get("triage_category", "unknown")
            indicators = triage.get("triage_indicators", [])
            ind_str = ", ".join(indicators) if indicators else "none"
            lines.append(
                f"- **{pn}** (device: {device}) — disagreement: {ds}, triage: {cat}, indicators: {ind_str}"
            )
        lines.append("")

    if triage_records:
        triage_counts_rpt: dict[str, int] = {}
        for tr in triage_records:
            cat = tr.get("triage_category", "unknown")
            triage_counts_rpt[cat] = triage_counts_rpt.get(cat, 0) + 1

        lines.append("## Disputed triage summary")
        lines.append("")
        lines.append("| Triage category | Count | Description |")
        lines.append("|----------------|-------|-------------|")
        lines.append(
            "| likely_confirmed | {} | High MPN confidence, low disagreement; safe to auto-promote after review |".format(
                triage_counts_rpt.get("likely_confirmed", 0)
            )
        )
        lines.append(
            "| ocr_needed | {} | OCR frame check could resolve; requires GEMINI_API_KEY |".format(
                triage_counts_rpt.get("ocr_needed", 0)
            )
        )
        lines.append(
            "| manual_review | {} | Human reviewer needed; no automated resolution path |".format(
                triage_counts_rpt.get("manual_review", 0)
            )
        )
        lines.append(
            "| threshold_tuning | {} | Record should be rejected or recategorized by improved MPN heuristics |".format(
                triage_counts_rpt.get("threshold_tuning", 0)
            )
        )
        lines.append("")
        lines.append(f"- Triage report: `{triage_path}`")
        lines.append(
            f"- GEMINI_API_KEY available: {bool(os.environ.get('GEMINI_API_KEY'))}"
        )
        ocr_actionable_count = sum(
            1 for tr in triage_records if tr.get("ocr_actionable")
        )
    lines.append(f"- OCR-actionable records: {ocr_actionable_count}")
    lines.append("")

    if resolution_packet:
        lines.append("## Status resolution summary")
        lines.append("")
        before = resolution_packet.get("status_before", {})
        after = resolution_packet.get("status_after", {})
        lines.append("| Status | Before | After | Delta |")
        lines.append("|--------|--------|-------|-------|")
        for status in ["confirmed", "disputed", "rejected"]:
            b = before.get(status, 0)
            a = after.get(status, 0)
            delta = a - b
            sign = "+" if delta > 0 else ""
            lines.append(f"| {status} | {b} | {a} | {sign}{delta} |")
        lines.append("")
        lines.append(f"- Resolutions applied: {len(resolution_packet.get('resolution_log', []))}")
        lines.append(f"- Still deferred (ocr_needed): {len(resolution_packet.get('ocr_needed_remaining', []))}")
        lines.append(f"- Still deferred (manual_review): {len(resolution_packet.get('manual_review_remaining', []))}")
        lines.append(f"- Blocked for clean verified snapshot: {len(resolution_packet.get('blocked_for_clean_snapshot', []))}")
        lines.append(f"- Resolution packet: `{resolution_packet_path}`")
        lines.append(f"- Policy version: {resolution_packet.get('policy_version', 'unknown')}")
        lines.append("")

    lines.extend(
        [
            "## Verification method",
            "",
            "1. Rule-based MPN validation (pattern matching, rejection heuristics)",
            "2. Enrichment field cross-check (verification flag, observed text, confidence)",
            "3. Disagreement score computation (0.0 = full agreement, 1.0 = maximum disagreement)",
            "4. Status assignment: confirmed / disputed / rejected",
            "5. OCR frame check (optional, requires GEMINI_API_KEY — disputed records only)",
            "6. Disputed triage (classify disputed into: likely_confirmed, ocr_needed, manual_review, threshold_tuning)",
            "",
    "## Output contract",
    "",
    f"- Verified snapshot: `{verified_path}`",
    f"- This report: `{VERIFICATION_REPORT_PATH}`",
    f"- Disagreement log: `{disagreement_path}`",
    f"- Triage report: `{triage_path}`",
    f"- Status resolution packet: `{resolution_packet_path}`",
    "",
    "## Limitations",
    "",
    "- OCR-based verification requires GEMINI_API_KEY and was skipped if not available",
    "- Rule-based validation may produce false positives for short or ambiguous MPNs",
    "- threshold_tuning records are now rejected by improved MPN heuristics (status resolution policy v2)",
    "- likely_confirmed records are now promoted to confirmed by status resolution policy v2",
    "- ocr_needed records remain deferred until GEMINI_API_KEY is available",
    "- manual_review records remain deferred until human reviewer decides",
    "- Verification is separate from curation and export (no downstream promotion)",
    "- Verification pack does NOT handle export gate; that is curation's responsibility",
    "",
            "## Handoff to curation",
            "",
            "After review of this report and disagreement log, run:",
            "",
            "```bash",
            "python3 scripts/curate_candidates.py review --snapshot "
            + str(verified_path),
            "python3 scripts/curate_candidates.py dry-run --fallback-test-db",
            "```",
            "",
        ]
    )

    report_path = VERIFICATION_REPORT_PATH
    if dry_run:
        report_path = VERIFICATION_REPORT_PATH.parent / (
            VERIFICATION_REPORT_PATH.name + DRY_RUN_SUFFIX
        )

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")

    print(f" Report written: {report_path}")
    print(f" Confirmed: {status_counts['confirmed']}")
    print(f" Disputed: {status_counts['disputed']}")
    print(f" Rejected: {status_counts['rejected']}")

    print(f"\n=== Report complete ===")
    return {"report": True, "path": str(report_path)}


def cmd_run(args: argparse.Namespace, dry_run: bool = False) -> dict[str, Any]:
    mode_label = "DRY-RUN" if dry_run else "RUN"
    print(f"=== Verification {mode_label}: Full pipeline ===\n")

    if dry_run:
        args.dry_run = True

    load_result = cmd_load(args)
    loaded = load_result.get("loaded", 0)
    if loaded == 0:
        print(f"\n No candidates loaded. Pipeline stopped.")
        return {"pipeline": "stopped", "reason": "no_candidates"}

    validate_result = cmd_validate(args)
    score_result = cmd_score(args)
    triage_result = cmd_triage(args)
    resolve_result = cmd_resolve_status(args)

    if not dry_run:
        api_key = getattr(args, "api_key", None) or os.environ.get("GEMINI_API_KEY")
        if api_key:
            cmd_ocr_check(args)

    snapshot_result = cmd_snapshot(args)
    report_result = cmd_report(args)

    print(f"\n=== {mode_label} pipeline complete ===")
    print(f" Loaded: {loaded}")
    print(f" Validated: {validate_result.get('validated', 0)}")
    print(f" Scored: {score_result.get('scored', 0)}")
    print(f" Triaged: {triage_result.get('triaged', 0)} disputed")
    print(f" Resolved: {resolve_result.get('resolved', 0)} status changes")
    print(f" Snapshot: {snapshot_result.get('written', 0)} records")
    print(f" Report: {'written' if report_result.get('report') else 'skipped'}")

    if dry_run:
        print(
            f"\n NOTE: Outputs written with .dry-run suffix. Canonical files NOT modified."
        )
        print(f" To apply, run: verify_candidates.py run")

    return {
        "loaded": loaded,
        "validated": validate_result.get("validated", 0),
        "scored": score_result.get("scored", 0),
        "triaged": triage_result.get("triaged", 0),
        "resolved": resolve_result.get("resolved", 0),
        "snapshot": snapshot_result.get("written", 0),
        "report": report_result.get("report", False),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verification execution surface for pack-project13-kaggle-verification-01",
    )
    sub = parser.add_subparsers(dest="command", help="Available commands")

    common_args = [
        ("--input", "Path to candidate snapshot (default: test_db.jsonl)"),
        ("--api-key", "GEMINI_API_KEY for OCR verification (or set env var)"),
    ]

    for name, help_text in [
        ("load", "Load candidate snapshot and report stats"),
        ("validate", "Rule-based MPN validation + cross-check"),
        ("ocr-check", "OCR-based frame verification (requires GEMINI_API_KEY)"),
        ("ocr-selector", "List/select individual OCR-deferred cases for surgical execution"),
        ("score", "Compute disagreement scores and assign verification status"),
        ("triage", "Classify disputed records into triage categories"),
        ("resolve-status", "Apply status resolution policy to disputed records"),
        ("deferred-workpack", "Generate operator-ready workpack for deferred OCR and manual review cases"),
        ("snapshot", "Write verified snapshot and disagreement log"),
        ("report", "Generate verification_report.md"),
        (
            "run",
            "Execute full pipeline: load + validate + score + triage + snapshot + report",
        ),
        ("dry-run", "Same as run but outputs to .dry-run suffixed files"),
    ]:
        sp = sub.add_parser(name, help=help_text)
        for flag, desc in common_args:
            sp.add_argument(flag, default=None, help=desc)
        if name == "ocr-selector":
            sp.add_argument("--case", default=None, help="Select single case by candidate_id (e.g. candidate-0008)")
            sp.add_argument("--group", default=None, help="Select cases grouped by video source URL")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    commands = {
        "load": cmd_load,
        "validate": cmd_validate,
        "ocr-check": cmd_ocr_check,
        "ocr-selector": cmd_ocr_selector,
        "score": cmd_score,
        "triage": cmd_triage,
        "resolve-status": cmd_resolve_status,
        "deferred-workpack": cmd_deferred_workpack,
        "snapshot": cmd_snapshot,
        "report": cmd_report,
        "run": lambda a: cmd_run(a, dry_run=False),
        "dry-run": lambda a: cmd_run(a, dry_run=True),
    }

    commands[args.command](args)


if __name__ == "__main__":
    main()
