#!/usr/bin/env python3
"""Validate resource scouting records for auditable agentic cells."""
import argparse
import json
from pathlib import Path

REQUIRED_FIELDS = [
    "id",
    "source",
    "location",
    "cost",
    "resource_class",
    "possible_products",
    "risks",
    "required_evidence",
    "activation_requirements",
]


def validate_record(record: dict) -> list[str]:
    errors: list[str] = []
    for field in REQUIRED_FIELDS:
        if field not in record or record[field] in (None, "", [], {}):
            errors.append(f"missing required field: {field}")
    if record.get("cost", {}).get("amount_pln") is None:
        errors.append("cost.amount_pln is required, use 0 for free resources")
    if record.get("cost", {}).get("amount_pln", 0) < 0:
        errors.append("cost.amount_pln cannot be negative")
    if not record.get("risks"):
        errors.append("at least one risk must be listed")
    if not record.get("required_evidence"):
        errors.append("at least one required evidence item must be listed")
    activation = record.get("activation_requirements", {})
    if "energy" not in activation or "logistics" not in activation:
        errors.append("activation_requirements must include energy and logistics")
    if record.get("activation_fit") == "oze_or_free_energy" and not activation.get("energy"):
        errors.append("OZE/free-energy activation fit requires energy note")
    return errors


def validate_records(data: dict) -> list[str]:
    records = data.get("records")
    if not isinstance(records, list) or not records:
        return ["records must be a non-empty list"]
    errors: list[str] = []
    for index, record in enumerate(records):
        for error in validate_record(record):
            errors.append(f"records[{index}]::{record.get('id', '<unknown>')}: {error}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    errors = validate_records(json.loads(args.path.read_text(encoding="utf-8")))
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"OK: resource scout records valid: {args.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
