#!/usr/bin/env python3
"""Validate human needs intake records and block unsafe recommendations.

Bez zewnetrznych zaleznosci (spojne z reszta walidatorow: resource_scout,
potential_pipeline). Po co: rekomendacja automatyzacji nie moze wybierac
wykonania fizycznego bez human approval; prywatne dane sa blokowane bez
jawnego zakresu widocznosci.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RECORDS = ROOT / "human_needs" / "seed_needs.json"

ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{2,80}$")

REQUIRED_TOP = {
    "id", "submitted_by", "visibility_scope", "need_or_problem",
    "location_or_area", "cost_constraints", "energy_constraints",
    "origin", "expected_outcome",
}
ROLES = {"operator", "volunteer", "maintainer", "external_partner", "anonymous"}
VIS_LEVELS = {"public", "maintainer_only", "operator_only", "private_anonymized"}
COST_TIERS = {"free", "low_cost_under_50_pln", "low_cost_under_200_pln", "any_reasonable"}
ENERGY_CLASSES = {
    "external_provider", "low_power_or_oze_preferred",
    "high_energy_requires_oze_or_justification",
    "owned_hardware_low_cost", "unspecified",
}


def _is_nonempty_str(v: Any) -> bool:
    return isinstance(v, str) and len(v) > 0


def _is_bool(v: Any) -> bool:
    return isinstance(v, bool)


def validate_record(record: dict) -> list[str]:
    errors: list[str] = []
    rid = record.get("id", "<unknown>")

    if not _is_nonempty_str(rid) or not ID_RE.match(str(rid)):
        errors.append(f"id must match {ID_RE.pattern}")

    missing = REQUIRED_TOP - set(record.keys())
    if missing:
        errors.append(f"missing required fields: {sorted(missing)}")

    sb = record.get("submitted_by", {})
    if not isinstance(sb, dict):
        errors.append("submitted_by must be object")
    else:
        if sb.get("role") not in ROLES:
            errors.append(f"submitted_by.role must be one of {sorted(ROLES)}")
        if not _is_nonempty_str(sb.get("public_label")):
            errors.append("submitted_by.public_label required")
        if "contact_note" in sb and sb.get("contact_note") is not None and not isinstance(sb.get("contact_note"), str):
            errors.append("submitted_by.contact_note must be string if present")

    vs = record.get("visibility_scope", {})
    if not isinstance(vs, dict):
        errors.append("visibility_scope must be object")
    else:
        if vs.get("level") not in VIS_LEVELS:
            errors.append(f"visibility_scope.level must be one of {sorted(VIS_LEVELS)}")
        # Private data requires explicit visibility scope != public.
        # If private_anonymized is set, a contact_note in submitted_by is a private leak only
        # if visibility_scope.level == public.
        sb_level = vs.get("level")
        has_contact = _is_nonempty_str(record.get("submitted_by", {}).get("contact_note"))
        if sb_level == "public" and has_contact:
            errors.append(
                "private contact_note cannot be exposed under public visibility_scope"
            )

    if not _is_nonempty_str(record.get("need_or_problem")) or len(record.get("need_or_problem", "")) < 10:
        errors.append("need_or_problem must be >=10 chars")
    if not _is_nonempty_str(record.get("location_or_area")):
        errors.append("location_or_area required")

    mc = record.get("mission_classes", [])
    if not isinstance(mc, list) or not all(isinstance(x, str) for x in mc):
        errors.append("mission_classes must be a list of strings (optional but typed)")

    cc = record.get("cost_constraints", {})
    if not isinstance(cc, dict):
        errors.append("cost_constraints must be object")
    elif cc.get("max_pln_or_free") not in COST_TIERS:
        errors.append(f"cost_constraints.max_pln_or_free must be one of {sorted(COST_TIERS)}")

    ec = record.get("energy_constraints", {})
    if not isinstance(ec, dict):
        errors.append("energy_constraints must be object")
    elif ec.get("preferred_class") not in ENERGY_CLASSES:
        errors.append(f"energy_constraints.preferred_class must be one of {sorted(ENERGY_CLASSES)}")
    elif ec.get("preferred_class") == "high_energy_requires_oze_or_justification" and not ec.get("oze_required"):
        errors.append(
            "energy_constraints: high-energy class requires oze_required=true (no greenwash)"
        )

    origin = record.get("origin", {})
    if not isinstance(origin, dict):
        errors.append("origin must be object")
    else:
        if not _is_bool(origin.get("chosen_from_recommendation")):
            errors.append("origin.chosen_from_recommendation must be boolean")
        # Recommendation cannot auto-select physical execution.
        if origin.get("chosen_from_recommendation") is True:
            outcome = record.get("expected_outcome", "").lower()
            if any(bad in outcome for bad in ("install", "actuate", "deploy", "trigger_production")):
                errors.append(
                    "origin: recommendation cannot pre-select physical execution; "
                    "expected_outcome must not include install/actuate/deploy/trigger_production"
                )
        if not _is_nonempty_str(origin.get("provenance")):
            errors.append("origin.provenance required (>=3 chars)")
        rids = origin.get("recommended_dossier_ids", [])
        if not isinstance(rids, list) or not all(isinstance(x, str) for x in rids):
            errors.append("origin.recommended_dossier_ids must be a list of strings")

    if not _is_nonempty_str(record.get("expected_outcome")):
        errors.append("expected_outcome required (>=5 chars)")

    notes = record.get("safety_notes", [])
    if not isinstance(notes, list) or not all(isinstance(x, str) for x in notes):
        errors.append("safety_notes must be a list of strings (optional but typed)")

    return errors


def validate_records(payload: dict) -> list[str]:
    records = payload.get("records")
    if not isinstance(records, list) or not records:
        return ["records must be a non-empty list"]
    errors: list[str] = []
    ids: set[str] = set()
    for i, rec in enumerate(records):
        if not isinstance(rec, dict):
            errors.append(f"records[{i}] must be object")
            continue
        for e in validate_record(rec):
            errors.append(f"records[{i}]::{rec.get('id', '<unknown>')}: {e}")
        rid = rec.get("id")
        if isinstance(rid, str):
            if rid in ids:
                errors.append(f"{rid}: duplicate id")
            ids.add(rid)
    return errors


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path, nargs="?", default=DEFAULT_RECORDS)
    args = parser.parse_args(list(argv) if argv is not None else None)
    errors = validate_records(json.loads(args.path.read_text(encoding="utf-8")))
    if errors:
        for e in errors:
            print(f"ERROR: {e}")
        return 1
    print(f"OK: human needs intake records valid: {args.path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
