#!/usr/bin/env python3
"""Validate the Hermes pilot plan before any always-on agent is deployed."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def validate_provider_matrix(data: dict) -> list[str]:
    errors: list[str] = []
    providers = data.get("providers", [])
    if not providers:
        return ["providers must not be empty"]
    for provider in providers:
        prefix = provider.get("id", "<unknown>")
        for field in ["secret_name", "quota_policy", "privacy_note", "allowed_cell_modes", "blocked_modes"]:
            if not provider.get(field):
                errors.append(f"{prefix}: missing {field}")
        if "physical_actuation" not in provider.get("blocked_modes", []):
            errors.append(f"{prefix}: physical_actuation must be blocked")
    return errors


def validate_pilot(data: dict) -> list[str]:
    errors: list[str] = []
    if data.get("status") != "draft_review_required":
        errors.append("pilot status must remain draft_review_required")
    for field in ["runtime_targets", "initial_cells", "required_secrets", "required_artifacts_per_run", "human_control_points", "blocked_until_review"]:
        if not data.get(field):
            errors.append(f"missing {field}")
    blocked = set(data.get("blocked_until_review", []))
    for required in ["direct push to main", "physical actuation", "secret printing", "auto-merge", "unbounded spend"]:
        if required not in blocked:
            errors.append(f"blocked_until_review must include: {required}")
    artifacts = set(data.get("required_artifacts_per_run", []))
    for required in ["run_receipt.json", "model_route.json", "quota_snapshot.json"]:
        if required not in artifacts:
            errors.append(f"required_artifacts_per_run must include: {required}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider-matrix", type=Path, default=ROOT / "provider_matrix.json")
    parser.add_argument("--pilot-plan", type=Path, default=ROOT / "pilot_plan.json")
    args = parser.parse_args()
    errors = []
    errors.extend(validate_provider_matrix(json.loads(args.provider_matrix.read_text(encoding="utf-8"))))
    errors.extend(validate_pilot(json.loads(args.pilot_plan.read_text(encoding="utf-8"))))
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("OK: Hermes pilot plan is review-gated and provider-aware")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
