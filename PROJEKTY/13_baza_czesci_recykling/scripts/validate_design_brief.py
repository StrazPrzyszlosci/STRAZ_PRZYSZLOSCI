#!/usr/bin/env python3
"""Design brief validator dla packa pack-project13-blueprint-design-01.

Waliduje wypelniony design brief (markdown) wzgledem required fields zdefiniowanych
w DESIGN_BRIEF_TEMPLATE.md i design_brief.schema.json.

Obsluguje dwa formaty wejscia:
  - plik markdown (parsuje tabele markdown i wyciaga pola/wartosci)
  - plik JSON (bezposrednio waliduje wzgledem JSON schema)

Uzycie:
  python3 validate_design_brief.py <brief_file>
  python3 validate_design_brief.py <brief_file> --json
  python3 validate_design_brief.py <brief_file> --schema <schema_path>
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

SCHEMA_PATH = PROJECT_ROOT / "schemas" / "design_brief.schema.json"
BRIEF_TEMPLATE_PATH = PROJECT_ROOT / "docs" / "DESIGN_BRIEF_TEMPLATE.md"

REQUIRED_FIELDS = [
    "brief_id",
    "device_name",
    "device_purpose",
    "primary_function",
    "inputs",
    "outputs",
    "communication_interfaces",
    "power_source",
    "voltage_levels",
    "max_current_draw",
    "operating_environment",
    "temperature_range",
    "max_bom_cost",
    "reuse_priority",
    "assumptions",
    "constraints",
]

VALID_ENVIRONMENTS = [
    "indoor",
    "outdoor_sheltered",
    "outdoor_exposed",
    "industrial",
    "wet_area",
]

VALID_REUSE_PRIORITIES = [
    "reuse_first",
    "cost_first",
]

SECTION_HEADERS = {
    "1": "Identyfikacja urzadzenia",
    "2": "Funkcja urzadzenia",
    "3": "Zasilanie",
    "4": "Srodowisko pracy",
    "5": "Ograniczenia kosztowe",
    "6": "Reuse parts",
    "7": "Zalozenia i ograniczenia projektowe",
    "8": "Donor board profile",
}


def parse_markdown_tables(text: str) -> dict[str, str]:
    """Parse markdown tables from a design brief and extract field-value pairs.

    Returns a dict of {field_name: field_value} for all found fields.
    """
    fields: dict[str, str] = {}
    lines = text.split("\n")

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        if line.startswith("|") and "Pole" in line:
            header_cells = [c.strip() for c in line.split("|")[1:-1]]

            is_value_table = False
            if len(header_cells) >= 2:
                second_col = header_cells[1].lower()
                if "wartosc" in second_col or "wartość" in second_col or "value" in second_col:
                    is_value_table = True

            if not is_value_table:
                i += 1
                continue

            i += 1
            while i < len(lines) and lines[i].strip().startswith("|") and set(lines[i].strip().replace("|", "").replace("-", "").replace(":", "").strip()) <= {" "}:
                i += 1

            while i < len(lines):
                row = lines[i].strip()
                if not row.startswith("|"):
                    break
                cells = [c.strip() for c in row.split("|")[1:-1]]
                if len(cells) >= 2:
                    key = cells[0].strip().strip("`")
                    value = cells[1].strip()
                    if key and key != "Pole" and not key.startswith("---"):
                        fields[key] = value
                i += 1
            continue

        i += 1

    return fields


def validate_fields(fields: dict[str, str]) -> list[str]:
    """Validate extracted fields against required fields and enum constraints.

    Returns a list of error messages. Empty list means valid.
    """
    errors: list[str] = []

    for field_name in REQUIRED_FIELDS:
        value = fields.get(field_name)
        if value is None:
            errors.append(f"BRAK WYMAGANEGO POLA: '{field_name}'")
        elif not value.strip() or value.strip().lower() in ("__do_uzupelnienia__", "tbd", "todo"):
            errors.append(f"WYMAGANE POLE PUSTE LUB NIEWYPELNIONE: '{field_name}' = '{value}'")

    env = fields.get("operating_environment", "").strip().lower()
    if env and env not in VALID_ENVIRONMENTS:
        errors.append(
            f"operating_environment='{env}' nie jest w dozwolonych wartosciach: {VALID_ENVIRONMENTS}"
        )

    rp = fields.get("reuse_priority", "").strip().lower()
    if rp and rp not in VALID_REUSE_PRIORITIES:
        errors.append(
            f"reuse_priority='{rp}' nie jest w dozwolonych wartosciach: {VALID_REUSE_PRIORITIES}"
        )

    return errors


def validate_json_against_schema(data: dict, schema: dict) -> list[str]:
    """Validate a JSON dict against a JSON schema.

    Uses jsonschema if available, otherwise falls back to manual required-fields check.
    Returns a list of error messages. Empty list means valid.
    """
    try:
        import jsonschema
        validator_cls = jsonschema.Draft202012Validator
        validator = validator_cls(schema)
        errors = []
        for error in sorted(validator.iter_errors(data), key=lambda e: list(e.path)):
            path = ".".join(str(p) for p in error.path) if error.path else "(root)"
            errors.append(f"JSON schema violation at {path}: {error.message}")
        return errors
    except ImportError:
        errors = []
        for field_name in schema.get("required", []):
            if field_name not in data or not str(data[field_name]).strip():
                errors.append(f"BRAK WYMAGANEGO POLA: '{field_name}'")

        props = schema.get("properties", {})
        if "operating_environment" in data:
            env = data["operating_environment"]
            env_schema = props.get("operating_environment", {})
            if "enum" in env_schema and env not in env_schema["enum"]:
                errors.append(
                    f"operating_environment='{env}' nie jest w dozwolonych wartosciach: {env_schema['enum']}"
                )
        if "reuse_priority" in data:
            rp = data["reuse_priority"]
            rp_schema = props.get("reuse_priority", {})
            if "enum" in rp_schema and rp not in rp_schema["enum"]:
                errors.append(
                    f"reuse_priority='{rp}' nie jest w dozwolonych wartosciach: {rp_schema['enum']}"
                )

        return errors


def validate_brief(brief_path: Path, schema_path: Path | None = None, is_json: bool = False) -> bool:
    """Main validation function. Returns True if brief is valid, False otherwise."""
    if schema_path is None:
        schema_path = SCHEMA_PATH

    if not brief_path.exists():
        print(f"BLAD: Plik briefu nie istnieje: {brief_path}")
        return False

    text = brief_path.read_text(encoding="utf-8")
    all_errors: list[str] = []

    if is_json:
        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            print(f"BLAD: Nie mozna sparsowac JSON: {e}")
            return False

        if schema_path.exists():
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            all_errors.extend(validate_json_against_schema(data, schema))
        else:
            all_errors.append(f"Schema nie istnieje: {schema_path}")
    else:
        fields = parse_markdown_tables(text)

        if not fields:
            print("BLAD: Nie udalo sie wyciagnac zadnych pol z markdown. Czy plik ma tabele z kolumna 'Wartosc'?")
            return False

        print(f"Znaleziono {len(fields)} pol w briefie markdown:")
        for k, v in fields.items():
            req_marker = "[WYMAGANE]" if k in REQUIRED_FIELDS else "[opcja]"
            print(f"  {req_marker} {k}: {v[:80]}{'...' if len(v) > 80 else ''}")

        md_errors = validate_fields(fields)
        all_errors.extend(md_errors)

        if schema_path.exists():
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            schema_fields = set(schema.get("properties", {}).keys())
            extracted_keys = set(fields.keys())
            missing_in_schema = extracted_keys - schema_fields
            if missing_in_schema:
                print(f"\nUWAGA: Pola w briefie nieobecne w schema (nie blokuja walidacji): {missing_in_schema}")

    print(f"\n{'='*60}")
    print(f"Walidacja: {brief_path.name}")
    print(f"Schema:    {schema_path}")
    print(f"{'='*60}")

    if all_errors:
        print(f"\nBLEDY WALIDACJI ({len(all_errors)}):")
        for err in all_errors:
            print(f"  - {err}")
        print(f"\nWERDYKT: FAIL — brief nie przechodzi walidacji")
        return False
    else:
        print("\nWERDYKT: PASS — brief spelnia wymagania schema baseline")
        return True


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Walidator design brief dla pack-project13-blueprint-design-01"
    )
    parser.add_argument(
        "brief_file",
        type=Path,
        help="Sciezka do pliku briefu (markdown albo JSON)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="is_json",
        help="Traktuj wejscie jako JSON zamiast markdown",
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=None,
        help="Sciezka do pliku schema JSON (domyslnie: schemas/design_brief.schema.json)",
    )

    args = parser.parse_args()
    valid = validate_brief(args.brief_file, args.schema, args.is_json)
    sys.exit(0 if valid else 1)


if __name__ == "__main__":
    main()
