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

VALID_QUANTITY_PATTERN = re.compile(r"^[1-9]\d*\s*(x|szt|pcs)?\.?$", re.IGNORECASE)

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

PLACEHOLDER_VALUES = {"__do_uzupelnienia__", "tbd", "todo", "__do_uzupełnienia__"}


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


def parse_reuse_sections(text: str) -> tuple[list[dict], list[dict]]:
    """Parse section 6.1 and 6.2 from design brief markdown.

    Returns (catalog_parts, missing_parts) as lists of dicts.
    """
    catalog_parts: list[dict] = []
    missing_parts: list[dict] = []

    lines = text.split("\n")
    i = 0
    in_catalog_section = False
    in_missing_section = False

    while i < len(lines):
        line = lines[i].strip()

        if "6.1" in line and ("kanoniczn" in line.lower() or "katalog" in line.lower()):
            in_catalog_section = True
            in_missing_section = False
            i += 1
            continue
        elif "6.2" in line and ("spoza" in line.lower() or "missing" in line.lower()):
            in_missing_section = True
            in_catalog_section = False
            i += 1
            continue
        elif line.startswith("## ") and "6" not in line:
            in_catalog_section = False
            in_missing_section = False

        if in_catalog_section and line.startswith("|"):
            cells = [c.strip() for c in line.split("|")[1:-1]]
            if len(cells) >= 3 and cells[0] not in ("part_slug", "---", "") and not cells[0].startswith("-"):
                catalog_parts.append({
                    "part_slug": cells[0],
                    "quantity": cells[1] if len(cells) > 1 else "1",
                    "notes": cells[2] if len(cells) > 2 else "",
                    "line_number": i + 1,
                })

        if in_missing_section and line.startswith("|"):
            cells = [c.strip() for c in line.split("|")[1:-1]]
            if len(cells) >= 3 and cells[0] not in ("Funkcja", "---", "") and not cells[0].startswith("-"):
                missing_parts.append({
                    "function": cells[0],
                    "required_param": cells[1] if len(cells) > 1 else "",
                    "donor_available": cells[2] if len(cells) > 2 else "",
                    "notes": cells[3] if len(cells) > 3 else "",
                    "line_number": i + 1,
                })

        i += 1

    return catalog_parts, missing_parts


def validate_reuse_section_rows(catalog_parts: list[dict], missing_parts: list[dict]) -> list[str]:
    """Validate individual rows in section 6.1 and 6.2 of the brief.

    Returns a list of error messages.
    """
    errors: list[str] = []

    for cp in catalog_parts:
        slug = cp["part_slug"]
        qty = cp["quantity"]
        ln = cp.get("line_number", "?")

        if slug.lower().strip("`") in PLACEHOLDER_VALUES or not slug.strip():
            errors.append(
                f"SEKCJA 6.1 wiersz linia {ln}: part_slug jest placeholderem albo pusty: '{slug}'"
            )

        if qty.lower() in PLACEHOLDER_VALUES or not qty.strip():
            errors.append(
                f"SEKCJA 6.1 wiersz linia {ln}: quantity jest placeholderem albo pusty dla part_slug='{slug}': '{qty}'"
            )
        elif not VALID_QUANTITY_PATTERN.match(qty.strip()):
            errors.append(
                f"SEKCJA 6.1 wiersz linia {ln}: quantity='{qty}' dla part_slug='{slug}' nie jest prawidlowa liczba (np. 1, 2x, 3szt)"
            )

        if not re.match(r"^[a-z0-9][a-z0-9_-]*[a-z0-9]$", slug.strip().lower()):
            errors.append(
                f"SEKCJA 6.1 wiersz linia {ln}: part_slug='{slug}' nie pasuje do formatu slug (male litery, cyfry, mysliniki, podkreslenia)"
            )

    for mp in missing_parts:
        func = mp["function"]
        req_param = mp["required_param"]
        donor = mp["donor_available"]
        ln = mp.get("line_number", "?")

        if func.lower() in PLACEHOLDER_VALUES or not func.strip():
            errors.append(
                f"SEKCJA 6.2 wiersz linia {ln}: Funkcja jest placeholderem albo pusta: '{func}'"
            )

        if req_param.lower() in PLACEHOLDER_VALUES or not req_param.strip():
            errors.append(
                f"SEKCJA 6.2 wiersz linia {ln}: Wymagany parametr jest placeholderem albo pusty dla Funkcja='{func}': '{req_param}'"
            )

    donor_upper = donor.upper().strip()
    if donor_upper not in ("TAK", "NIE", "SPRAWDZIC", "") and not donor_upper.startswith("TAK") and not donor_upper.startswith("NIE") and not donor_upper.startswith("SPRAWDZIC"):
        errors.append(
            f"SEKCJA 6.2 wiersz linia {ln}: Czy da sie pozyskac='{donor}' dla Funkcja='{func}' — oczekiwano TAK/NIE/SPRAWDZIC (opcjonalnie z wyjasnieniem po mysliniku)"
        )

    return errors


def validate_assumptions_constraints_rows(fields: dict[str, str]) -> list[str]:
    """Validate assumptions and constraints fields for placeholder-only content
    and minimal structural quality.

    Returns a list of error messages.
    """
    errors: list[str] = []

    assumptions = fields.get("assumptions", "").strip()
    if assumptions.lower() in PLACEHOLDER_VALUES:
        errors.append("assumptions zawiera tylko placeholder — wymagane sa konkretne zalozenia")
    elif not assumptions:
        errors.append("assumptions jest puste — wymagane sa konkretne zalozenia")

    constraints = fields.get("constraints", "").strip()
    if constraints.lower() in PLACEHOLDER_VALUES:
        errors.append("constraints zawiera tylko placeholder — wymagane sa konkretne ograniczenia")
    elif not constraints:
        errors.append("constraints jest puste — wymagane sa konkretne ograniczenia")

    NUMBERED_SEGMENT_PATTERN = re.compile(r"^\d+\s*[.):]\s*")

    if assumptions and assumptions.lower() not in PLACEHOLDER_VALUES:
        raw_segments = [s.strip().rstrip(",") for s in assumptions.split(".") if s.strip().rstrip(",")]
        merged: list[str] = []
        for seg in raw_segments:
            if re.match(r"^\d+$", seg.strip()):
                merged.append(seg.strip() + ".")
            elif merged and re.match(r"^\d+\.$", merged[-1].strip()):
                merged[-1] = merged[-1].rstrip(".") + ". " + seg
            else:
                merged.append(seg)
        segments = []
        for seg in merged:
            cleaned = NUMBERED_SEGMENT_PATTERN.sub("", seg).strip()
            if cleaned:
                segments.append(cleaned)
        if len(segments) < 2:
            errors.append(
                f"assumptions ma tylko {len(segments)} punkt — wymagane min 2 konkretne zalozenia (oddzielone kropkami)"
            )
        for idx, seg in enumerate(segments, 1):
            if len(seg) < 5:
                errors.append(
                    f"assumptions punkt {idx} jest zbyt krotki ('{seg}') — zalozenie musi byc konkretnym zdaniem"
                )
            if seg.lower() in PLACEHOLDER_VALUES:
                errors.append(
                    f"assumptions punkt {idx} jest placeholderem ('{seg}') — wymagane konkretne zalozenie"
                )

    if constraints and constraints.lower() not in PLACEHOLDER_VALUES:
        raw_segments = [s.strip().rstrip(",") for s in constraints.split(".") if s.strip().rstrip(",")]
        merged: list[str] = []
        for seg in raw_segments:
            if re.match(r"^\d+$", seg.strip()):
                merged.append(seg.strip() + ".")
            elif merged and re.match(r"^\d+\.$", merged[-1].strip()):
                merged[-1] = merged[-1].rstrip(".") + ". " + seg
            else:
                merged.append(seg)
        segments = []
        for seg in merged:
            cleaned = NUMBERED_SEGMENT_PATTERN.sub("", seg).strip()
            if cleaned:
                segments.append(cleaned)
        if len(segments) < 2:
            errors.append(
                f"constraints ma tylko {len(segments)} punkt — wymagane min 2 konkretne ograniczenia (oddzielone kropkami)"
            )
        for idx, seg in enumerate(segments, 1):
            if len(seg) < 5:
                errors.append(
                    f"constraints punkt {idx} jest zbyt krotki ('{seg}') — ograniczenie musi byc konkretnym zdaniem"
                )
        if seg.lower() in PLACEHOLDER_VALUES:
            errors.append(
                f"constraints punkt {idx} jest placeholderem ('{seg}') — wymagane konkretne ograniczenie"
            )

    return errors


def validate_internal_consistency(fields: dict[str, str]) -> list[str]:
    """Validate internal consistency between fields in the brief.

    Returns a list of error messages.
    """
    errors: list[str] = []

    voltage = fields.get("voltage_levels", "").lower()
    power_source = fields.get("power_source", "").lower()
    if "3.3v" in voltage and "5v" not in voltage and "usb" in power_source and "regulator" not in power_source:
        if "regulator" not in fields.get("assumptions", "").lower() and "lm7805" not in fields.get("assumptions", "").lower() and "stab" not in fields.get("assumptions", "").lower():
            errors.append(
                "WYSTEPNA SPOJNOSC: voltage_levels wymaga 3.3V, power_source=USB 5V, ale assumptions nie wspomina o regulatorze napiecia — brakuje wytlumaczenia konwersji 5V->3.3V"
            )

    env = fields.get("operating_environment", "").lower()
    temp_range = fields.get("temperature_range", "").lower()
    if env == "outdoor_exposed" and ("0c" in temp_range or "-40" not in temp_range):
        if "outdoor" not in fields.get("assumptions", "").lower() and "obudow" not in fields.get("constraints", "").lower():
            errors.append(
                "WYSTEPNA SPOJNOSC: operating_environment=outdoor_exposed, ale temperature_range i constraints nie odnosia sie do ochrony przed warunkami zewnetrznymi"
            )

    max_bom = fields.get("max_bom_cost", "").strip()
    if max_bom:
        cost_match = re.search(r"(\d+)", max_bom)
        reuse_priority = fields.get("reuse_priority", "").strip().lower()
        if cost_match and int(cost_match.group(1)) == 0 and reuse_priority != "cost_first":
            errors.append(
                "WYSTEPNA SPOJNOSC: max_bom_cost=0 ale reuse_priority nie jest cost_first — sprzecnosc pomiedzy budzetem a priorytetem"
            )

    inputs = fields.get("inputs", "").lower()
    comms = fields.get("communication_interfaces", "").lower()
    if "i2c" in inputs and "i2c" not in comms:
        errors.append(
            "WYSTEPNA SPOJNOSC: inputs wymienia I2C, ale communication_interfaces nie zawiera I2C"
        )
    if "spi" in inputs and "spi" not in comms:
        errors.append(
            "WYSTEPNA SPOJNOSC: inputs wymienia SPI, ale communication_interfaces nie zawiera SPI"
        )
    if "uart" in inputs and "uart" not in comms and "serial" not in comms:
        errors.append(
            "WYSTEPNA SPOJNOSC: inputs wymienia UART, ale communication_interfaces nie zawiera UART ani Serial"
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

    row_errors = validate_assumptions_constraints_rows(fields)
    all_errors.extend(row_errors)

    consistency_errors = validate_internal_consistency(fields)
    all_errors.extend(consistency_errors)

    catalog_parts, missing_parts = parse_reuse_sections(text)
    if catalog_parts or missing_parts:
        reuse_row_errors = validate_reuse_section_rows(catalog_parts, missing_parts)
        all_errors.extend(reuse_row_errors)
    elif "reuse" in text.lower() or "6.1" in text or "6.2" in text:
        all_errors.append("SEKCJA 6 istnieje, ale nie znaleziono zadnych wierszy czesci — sekcja 6.1 i/lub 6.2 jest pusta albo zle sformatowana")

    if schema_path.exists():
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        schema_fields = set(schema.get("properties", {}).keys())
        extracted_keys = set(fields.keys())
        missing_in_schema = extracted_keys - schema_fields
        if missing_in_schema:
            print(f"\nUWAGA: Pola w briefie nieobecne w schema (nie blokuja walidacji): {missing_in_schema}")

    print(f"\n{'='*60}")
    print(f"Walidacja: {brief_path.name}")
    print(f"Schema: {schema_path}")
    print(f"{'='*60}")

    if all_errors:
        print(f"\nBLEDY WALIDACJI ({len(all_errors)}):")
        for err in all_errors:
            print(f" - {err}")
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
