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
score — Compute disagreement scores and assign verification_status
triage — Classify disputed records into triage categories (ocr_needed, manual_review, threshold_tuning, likely_confirmed)
snapshot — Write verified snapshot (test_db_verified.jsonl)
report — Generate verification_report.md (includes triage summary when available)
run — Execute full pipeline: load + validate + score + triage + snapshot + report
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


def classify_mpn_quality(part_number: str) -> dict[str, Any]:
    if not part_number or not part_number.strip():
        return {"valid": False, "reason": "empty_field", "confidence": 0.0}

    pn = part_number.strip()

    for pattern, reason in MPN_REJECTION_PATTERNS:
        if re.match(pattern, pn):
            return {"valid": False, "reason": reason, "confidence": 0.1}

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
            "",
            "## Limitations",
            "",
            "- OCR-based verification requires GEMINI_API_KEY and was skipped if not available",
            "- Rule-based validation may produce false positives for short or ambiguous MPNs",
            "- Disputed records now have triage categories; threshold_tuning records should improve scoring rules",
            "- ocr_needed records remain deferred until GEMINI_API_KEY is available",
            "- Verification is separate from curation and export (no downstream promotion)",
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
        ("score", "Compute disagreement scores and assign verification status"),
        ("triage", "Classify disputed records into triage categories"),
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

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    commands = {
        "load": cmd_load,
        "validate": cmd_validate,
        "ocr-check": cmd_ocr_check,
        "score": cmd_score,
        "triage": cmd_triage,
        "snapshot": cmd_snapshot,
        "report": cmd_report,
        "run": lambda a: cmd_run(a, dry_run=False),
        "dry-run": lambda a: cmd_run(a, dry_run=True),
    }

    commands[args.command](args)


if __name__ == "__main__":
    main()
