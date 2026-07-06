#!/usr/bin/env python3
"""Validate AgenticCellManifest records against the cell manifest schema.

Bez zewnetrznych zaleznosci: walidujemy recznie wymagane pola, typy, enumy i
wzorce, tak jak wspieraj dotychczasowe walidatory (potential_pipeline,
resource_scout). Manifest opisuje istniejaca komorke i jej NIE zastepuje.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA = ROOT / "agentic_cells" / "cell_manifest_schema.json"
DEFAULT_MANIFESTS = ROOT / "agentic_cells" / "seed_cell_manifests.json"

CELL_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{2,80}$")
VERSION_RE = re.compile(r"^v[0-9]+$")

ALLOWED_MODES = {
    "read-only", "suggest-only", "dry-run", "staging-write",
    "human-approved", "hardware-lab", "production",
}
STATUS_VALUES = {"draft", "ready_for_review", "active", "deprecated"}
INPUT_KINDS = {
    "repo_file", "external_repo", "sensor_data", "photo", "operator_note",
    "catalog", "api", "handoff", "execution_pack",
}
ENERGY_CLASSES = {
    "external_provider", "low_power_or_oze_preferred",
    "high_energy_requires_oze_or_justification", "owned_hardware_low_cost",
}

# Tryby dajace realne ryzyko fizyczne lub produkcyjne. staging-write dotyczy
# zapisu draftow/D1 i NIE jest high-risk loszenia blokady actuation.
HIGH_RISK_MODES = {"hardware-lab", "production"}


def _is_bool(value: Any) -> bool:
    return isinstance(value, bool)


def _is_nonempty_str(value: Any) -> bool:
    return isinstance(value, str) and len(value) > 0


def _is_nonempty_list(value: Any) -> bool:
    return isinstance(value, list) and len(value) > 0


def _is_strings_list(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(x, str) for x in value)


def _validate_audited_block(cell: dict, errors: list[str], cell_id: str) -> None:
    audit = cell.get("audit_trail")
    if not isinstance(audit, dict):
        errors.append(f"{cell_id}: audit_trail must be an object")
        return
    for key in ("must_record_inputs", "must_record_tool_versions",
                "must_record_decisions", "must_record_artifacts"):
        if not _is_bool(audit.get(key)):
            errors.append(f"{cell_id}: audit_trail.{key} must be boolean")


def _validate_human_control_points(cell: dict, errors: list[str], cell_id: str) -> None:
    points = cell.get("human_control_points")
    if not _is_nonempty_list(points):
        errors.append(f"{cell_id}: human_control_points must be a non-empty array")
        return
    for i, p in enumerate(points):
        if not isinstance(p, dict):
            errors.append(f"{cell_id}: human_control_points[{i}] must be object")
            continue
        if not _is_nonempty_str(p.get("point")):
            errors.append(f"{cell_id}: human_control_points[{i}].point missing")
        if not _is_nonempty_str(p.get("reviewer_role")):
            errors.append(f"{cell_id}: human_control_points[{i}].reviewer_role missing")
        if not _is_nonempty_list(p.get("blocks")):
            errors.append(f"{cell_id}: human_control_points[{i}].blocks must be non-empty list of strings")
        elif not _is_strings_list(p.get("blocks")):
            errors.append(f"{cell_id}: human_control_points[{i}].blocks must be list of strings")


def _validate_review_gates(cell: dict, errors: list[str], cell_id: str) -> None:
    gates = cell.get("review_gates")
    if not _is_nonempty_list(gates):
        errors.append(f"{cell_id}: review_gates must be a non-empty array")
        return
    for i, g in enumerate(gates):
        if not isinstance(g, dict):
            errors.append(f"{cell_id}: review_gates[{i}] must be object")
            continue
        if not _is_nonempty_str(g.get("gate")):
            errors.append(f"{cell_id}: review_gates[{i}].gate missing")
        if not _is_nonempty_str(g.get("reviewer_role")):
            errors.append(f"{cell_id}: review_gates[{i}].reviewer_role missing")
        if not _is_nonempty_list(g.get("blocks")):
            errors.append(f"{cell_id}: review_gates[{i}].blocks must be non-empty list of strings")


def _validate_model_resource_policy(cell: dict, errors: list[str], cell_id: str) -> None:
    pol = cell.get("model_resource_policy")
    if not isinstance(pol, dict):
        errors.append(f"{cell_id}: model_resource_policy must be an object")
        return
    if not _is_nonempty_str(pol.get("default_profile")):
        errors.append(f"{cell_id}: model_resource_policy.default_profile missing")
    if not _is_bool(pol.get("may_use_paid")):
        errors.append(f"{cell_id}: model_resource_policy.may_use_paid must be boolean")
    if not _is_bool(pol.get("may_use_private_data_on_public_model")):
        errors.append(
            f"{cell_id}: model_resource_policy.may_use_private_data_on_public_model must be boolean"
        )
    # Prywatne dane na publicznym modelu trzeba wylaczyc przez wpisz false.
    if pol.get("may_use_private_data_on_public_model") is True:
        errors.append(
            f"{cell_id}: private data must NOT be sent to public model by default "
            "(may_use_private_data_on_public_model must be false in seed)"
        )


def _validate_energy_policy(cell: dict, errors: list[str], cell_id: str) -> None:
    pol = cell.get("energy_policy")
    if not isinstance(pol, dict):
        errors.append(f"{cell_id}: energy_policy must be an object")
        return
    if pol.get("default_class") not in ENERGY_CLASSES:
        errors.append(
            f"{cell_id}: energy_policy.default_class must be one of {sorted(ENERGY_CLASSES)}"
        )
    if not _is_bool(pol.get("low_power_first")):
        errors.append(f"{cell_id}: energy_policy.low_power_first must be boolean")


def _validate_rollback_plan(cell: dict, errors: list[str], cell_id: str) -> None:
    rb = cell.get("rollback_plan")
    if not isinstance(rb, dict):
        errors.append(f"{cell_id}: rollback_plan must be an object")
        return
    if not isinstance(rb.get("strategy"), str) or len(rb.get("strategy", "")) < 5:
        errors.append(f"{cell_id}: rollback_plan.strategy must be >=5 chars")
    if not _is_nonempty_str(rb.get("rollback_artifact")):
        errors.append(f"{cell_id}: rollback_plan.rollback_artifact missing")


def _validate_no_high_risk_without_human_block(cell: dict, errors: list[str], cell_id: str) -> None:
    """Komórka w trybie high-risk musi miec human_control_points blokujace actuation."""
    modes = set(cell.get("allowed_modes", []))
    high_risk = modes & HIGH_RISK_MODES
    if not high_risk:
        return
    points = cell.get("human_control_points", [])
    joined = " ".join(p.get("point", "") for p in points if isinstance(p, dict)).lower()
    gates_joined = " ".join(g.get("gate", "") for g in cell.get("review_gates", []) if isinstance(g, dict)).lower()
    blob = f"{joined} {gates_joined}"
    if "actuation" not in blob and "physical" not in blob and "production" not in blob:
        errors.append(
            f"{cell_id}: high-risk modes {sorted(high_risk)} require human control point or "
            "review gate referencing actuation/physical/production"
        )
    if "production" in modes and "production" not in blob:
        errors.append(
            f"{cell_id}: production mode requires explicit human gate referencing 'production'"
        )


def validate_manifest(cell: dict) -> list[str]:
    errors: list[str] = []
    cell_id = cell.get("cell_id", "<unknown>")

    if not isinstance(cell_id, str) or not CELL_ID_RE.match(str(cell_id)):
        errors.append(f"{cell_id}: cell_id must match {CELL_ID_RE.pattern}")
    if not VERSION_RE.match(str(cell.get("version", ""))):
        errors.append(f"{cell_id}: version must match {VERSION_RE.pattern}")
    if cell.get("status") not in STATUS_VALUES:
        errors.append(f"{cell_id}: status must be one of {sorted(STATUS_VALUES)}")
    if not isinstance(cell.get("purpose"), str) or len(cell.get("purpose", "")) < 10:
        errors.append(f"{cell_id}: purpose must be >=10 chars")
    modes = cell.get("allowed_modes")
    if not _is_nonempty_list(modes) or not set(modes).issubset(ALLOWED_MODES):
        errors.append(f"{cell_id}: allowed_modes must be non-empty subset of {sorted(ALLOWED_MODES)}")

    inputs = cell.get("input_contract")
    if not _is_nonempty_list(inputs):
        errors.append(f"{cell_id}: input_contract must be a non-empty array")
    else:
        for i, item in enumerate(inputs):
            if not isinstance(item, dict):
                errors.append(f"{cell_id}: input_contract[{i}] must be object")
                continue
            if not _is_nonempty_str(item.get("name")):
                errors.append(f"{cell_id}: input_contract[{i}].name missing")
            if item.get("kind") not in INPUT_KINDS:
                errors.append(f"{cell_id}: input_contract[{i}].kind must be one of {sorted(INPUT_KINDS)}")
            if not _is_bool(item.get("required")):
                errors.append(f"{cell_id}: input_contract[{i}].required must be boolean")

    outputs = cell.get("output_artifacts")
    if not _is_nonempty_list(outputs):
        errors.append(f"{cell_id}: output_artifacts must be a non-empty array")
    else:
        for i, item in enumerate(outputs):
            if not isinstance(item, dict):
                errors.append(f"{cell_id}: output_artifacts[{i}] must be object")
                continue
            if not _is_nonempty_str(item.get("path_or_type")):
                errors.append(f"{cell_id}: output_artifacts[{i}].path_or_type missing")
            if not _is_nonempty_str(item.get("description")):
                errors.append(f"{cell_id}: output_artifacts[{i}].description missing")
            if not _is_bool(item.get("review_required")):
                errors.append(f"{cell_id}: output_artifacts[{i}].review_required must be boolean")

    _validate_model_resource_policy(cell, errors, cell_id)
    _validate_energy_policy(cell, errors, cell_id)
    _validate_human_control_points(cell, errors, cell_id)
    _validate_audited_block(cell, errors, cell_id)
    _validate_rollback_plan(cell, errors, cell_id)
    _validate_review_gates(cell, errors, cell_id)
    _validate_no_high_risk_without_human_block(cell, errors, cell_id)

    notes = cell.get("safety_notes", [])
    if not isinstance(notes, list) or not all(isinstance(x, str) for x in notes):
        errors.append(f"{cell_id}: safety_notes must be a list of strings (optional but typed)")
    return errors


def validate_manifests(payload: dict) -> list[str]:
    cells = payload.get("cells")
    if not _is_nonempty_list(cells):
        return ["cells must be a non-empty array"]
    errors: list[str] = []
    ids: set[str] = set()
    for cell in cells:
        if not isinstance(cell, dict):
            errors.append("each cell must be an object")
            continue
        errors.extend(validate_manifest(cell))
        cid = cell.get("cell_id")
        if isinstance(cid, str):
            if cid in ids:
                errors.append(f"{cid}: duplicate cell_id")
            ids.add(cid)
    return errors


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifests", type=Path, default=DEFAULT_MANIFESTS)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    args = parser.parse_args(list(argv) if argv is not None else None)

    schema = json.loads(args.schema.read_text(encoding="utf-8"))
    required = set(schema.get("required", []))
    payload = json.loads(args.manifests.read_text(encoding="utf-8"))

    errors: list[str] = []
    for cell in payload.get("cells", []):
        if isinstance(cell, dict):
            missing = required - set(cell.keys())
            if missing:
                errors.append(f"{cell.get('cell_id')}: missing required fields {sorted(missing)}")
    errors.extend(validate_manifests(payload))

    if errors:
        for err in errors:
            print(f"ERROR: {err}")
        return 1
    print(f"OK: {len(payload.get('cells', []))} agentic cell manifest(s) valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
