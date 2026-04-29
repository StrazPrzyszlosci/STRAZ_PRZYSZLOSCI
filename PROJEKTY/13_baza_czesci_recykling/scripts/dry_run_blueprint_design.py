#!/usr/bin/env python3
"""Minimal dry-run execution surface dla packa pack-project13-blueprint-design-01.

Przyjmuje wypelniony design brief (markdown), waliduje go wzgledem schema baseline,
dopasowuje reuse parts z kanonicznego katalogu, generuje review-ready artefakty
(design_dossier, BOM, assembly_instructions, design_risks, missing_parts) i zapisuje
dry-run report.

Nie generuje CAD/BOM z zewnetrznych narzedzi — to jest kontrolowany dry-run
powtarzajacy to, co pack powinien zrobic na minimalnym, uczciwym execution surface.

Uzycie:
    python3 dry_run_blueprint_design.py --brief <brief_file>
    python3 dry_run_blueprint_design.py --brief <brief_file> --catalog <catalog_path>
    python3 dry_run_blueprint_design.py --brief <brief_file> --output-dir <dir>
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
PACK_ID = "pack-project13-blueprint-design-01"
PACK_DIR = PROJECT_ROOT / "execution_packs" / PACK_ID
DEFAULT_CATALOG = PROJECT_ROOT / "data" / "parts_master.jsonl"
VALIDATOR_SCRIPT = PROJECT_ROOT / "scripts" / "validate_design_brief.py"
MANIFEST_PATH = PACK_DIR / "manifest.json"
RUNBOOK_PATH = PACK_DIR / "RUNBOOK.md"
REVIEW_CHECKLIST_PATH = PACK_DIR / "REVIEW_CHECKLIST.md"
PR_TEMPLATE_PATH = PACK_DIR / "PR_TEMPLATE.md"

PLACEHOLDER_VALUES = {"__do_uzupelnienia__", "tbd", "todo", "__do_uzupełnienia__"}
VALID_QUANTITY_PATTERN = re.compile(r"^[1-9]\d*\s*(x|szt|pcs)?\.?$", re.IGNORECASE)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def load_catalog(catalog_path: Path) -> dict[str, dict]:
    if not catalog_path.exists():
        return {}
    parts: dict[str, dict] = {}
    with catalog_path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            slug = record.get("part_slug", "")
            if slug:
                parts[slug] = record
    return parts


def validate_brief_external(brief_path: Path) -> bool:
    if not VALIDATOR_SCRIPT.exists():
        print(f"UWAGA: Walidator nie istnieje: {VALIDATOR_SCRIPT}", file=sys.stderr)
        return False
    result = subprocess.run(
        ["python3", str(VALIDATOR_SCRIPT), str(brief_path)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print("Walidacja briefu NIE PRZESZLA:", file=sys.stderr)
        print(result.stdout, file=sys.stderr)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
    return result.returncode == 0


def parse_markdown_tables_local(text: str) -> dict[str, str]:
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
                if "wartosc" in second_col or "warto\u015b\u0107" in second_col or "value" in second_col:
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
            continue
        i += 1
    return fields


def parse_reuse_sections(text: str) -> tuple[list[dict], list[dict]]:
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
                })

        if in_missing_section and line.startswith("|"):
            cells = [c.strip() for c in line.split("|")[1:-1]]
            if len(cells) >= 3 and cells[0] not in ("Funkcja", "---", "") and not cells[0].startswith("-"):
                missing_parts.append({
                    "function": cells[0],
                    "required_param": cells[1] if len(cells) > 1 else "",
                    "donor_available": cells[2] if len(cells) > 2 else "",
                    "notes": cells[3] if len(cells) > 3 else "",
                })

        i += 1

    return catalog_parts, missing_parts


def validate_row_level(catalog_parts: list[dict], missing_parts: list[dict], fields: dict[str, str]) -> list[str]:
    errors: list[str] = []

    for cp in catalog_parts:
        slug = cp.get("part_slug", "")
        qty = cp.get("quantity", "1")
        if slug.lower().strip("`") in PLACEHOLDER_VALUES or not slug.strip():
            errors.append(f"SEKCJA 6.1: part_slug jest placeholderem albo pusty: '{slug}'")
        if qty.lower() in PLACEHOLDER_VALUES or not qty.strip():
            errors.append(f"SEKCJA 6.1: quantity jest placeholderem albo pusty dla part_slug='{slug}': '{qty}'")
        elif not VALID_QUANTITY_PATTERN.match(qty.strip()):
            errors.append(f"SEKCJA 6.1: quantity='{qty}' dla part_slug='{slug}' nie jest prawidlowa liczba")
        if not re.match(r"^[a-z0-9][a-z0-9_-]*[a-z0-9]$", slug.strip().lower()) and slug.strip():
            errors.append(f"SEKCJA 6.1: part_slug='{slug}' nie pasuje do formatu slug")

    for mp in missing_parts:
        func = mp.get("function", "")
        req_param = mp.get("required_param", "")
        donor = mp.get("donor_available", "")
        if func.lower() in PLACEHOLDER_VALUES or not func.strip():
            errors.append(f"SEKCJA 6.2: Funkcja jest placeholderem albo pusta: '{func}'")
        if req_param.lower() in PLACEHOLDER_VALUES or not req_param.strip():
            errors.append(f"SEKCJA 6.2: Wymagany parametr jest placeholderem albo pusty dla Funkcja='{func}': '{req_param}'")
        donor_upper = donor.upper().strip()
        if donor_upper not in ("TAK", "NIE", "SPRAWDZIC", "") and not donor_upper.startswith("TAK") and not donor_upper.startswith("NIE") and not donor_upper.startswith("SPRAWDZIC"):
            errors.append(f"SEKCJA 6.2: Czy da sie pozyskac='{donor}' dla Funkcja='{func}' — oczekiwano TAK/NIE/SPRAWDZIC (opcjonalnie z wyjasnieniem po mysliniku)")

    assumptions = fields.get("assumptions", "").strip()
    if assumptions and assumptions.lower() not in PLACEHOLDER_VALUES:
        numbered_pattern = re.compile(r"^\d+\s*[.):]\s*")
        raw_segments = [s.strip().rstrip(",") for s in assumptions.split(".") if s.strip().rstrip(",")]
        merged: list[str] = []
        for seg in raw_segments:
            if re.match(r"^\d+$", seg.strip()):
                merged.append(seg.strip() + ".")
            elif merged and re.match(r"^\d+\.$", merged[-1].strip()):
                merged[-1] = merged[-1].rstrip(".") + ". " + seg
            else:
                merged.append(seg)
        segments = [numbered_pattern.sub("", seg).strip() for seg in merged if numbered_pattern.sub("", seg).strip()]
        if len(segments) < 2:
            errors.append(f"assumptions ma tylko {len(segments)} punkt — wymagane min 2 konkretna zalozenia")

    constraints = fields.get("constraints", "").strip()
    if constraints and constraints.lower() not in PLACEHOLDER_VALUES:
        numbered_pattern = re.compile(r"^\d+\s*[.):]\s*")
        raw_segments = [s.strip().rstrip(",") for s in constraints.split(".") if s.strip().rstrip(",")]
        merged: list[str] = []
        for seg in raw_segments:
            if re.match(r"^\d+$", seg.strip()):
                merged.append(seg.strip() + ".")
            elif merged and re.match(r"^\d+\.$", merged[-1].strip()):
                merged[-1] = merged[-1].rstrip(".") + ". " + seg
            else:
                merged.append(seg)
        segments = [numbered_pattern.sub("", seg).strip() for seg in merged if numbered_pattern.sub("", seg).strip()]
        if len(segments) < 2:
            errors.append(f"constraints ma tylko {len(segments)} punkt — wymagane min 2 konkretna ograniczenia")

    return errors


def build_bill_of_materials(
    fields: dict[str, str],
    catalog_parts: list[dict],
    missing_parts: list[dict],
    catalog: dict[str, dict],
) -> dict:
    bom_items: list[dict] = []

    for cp in catalog_parts:
        slug = cp["part_slug"]
        catalog_entry = catalog.get(slug)
        bom_item = {
            "part_slug": slug,
            "quantity": cp["quantity"],
            "source": "reuse_catalog" if catalog_entry else "missing_from_catalog",
            "part_name": catalog_entry.get("part_name", cp.get("notes", "")) if catalog_entry else cp.get("notes", slug),
            "species": catalog_entry.get("species", "") if catalog_entry else "",
            "genus": catalog_entry.get("genus", "") if catalog_entry else "",
        }
        bom_items.append(bom_item)

    for mp in missing_parts:
        safe_slug = mp["function"].lower().replace(" ", "-").replace("(", "").replace(")", "")
        bom_item = {
            "part_slug": f"missing-{safe_slug}",
            "quantity": "1",
            "source": "missing",
            "part_name": mp["function"],
            "species": "",
            "genus": "",
            "required_param": mp["required_param"],
            "donor_available": mp["donor_available"],
            "notes": mp.get("notes", ""),
        }
        bom_items.append(bom_item)

    reuse_count = sum(1 for item in bom_items if item["source"] == "reuse_catalog")
    missing_from_catalog_count = sum(1 for item in bom_items if item["source"] == "missing_from_catalog")
    missing_count = sum(1 for item in bom_items if item["source"] == "missing")

    return {
        "brief_id": fields.get("brief_id", ""),
        "device_name": fields.get("device_name", ""),
        "items": bom_items,
        "summary": {
            "total_items": len(bom_items),
            "reuse_catalog": reuse_count,
            "missing_from_catalog": missing_from_catalog_count,
            "missing": missing_count,
        },
        "dry_run": True,
        "generated_at": utc_now().replace(microsecond=0).isoformat(),
    }


def build_design_dossier(
    fields: dict[str, str],
    catalog_parts: list[dict],
    missing_parts: list[dict],
    catalog: dict[str, dict],
    bom: dict,
) -> str:
    brief_id = fields.get("brief_id", "unknown")
    device_name = fields.get("device_name", "unknown")
    primary_function = fields.get("primary_function", "")
    power_source = fields.get("power_source", "")
    voltage_levels = fields.get("voltage_levels", "")
    communication = fields.get("communication_interfaces", "")
    env = fields.get("operating_environment", "")
    reuse_priority = fields.get("reuse_priority", "")

    reuse_lines: list[str] = []
    for cp in catalog_parts:
        slug = cp["part_slug"]
        entry = catalog.get(slug)
        if entry:
            reuse_lines.append(
                f"- **{entry.get('part_name', slug)}** (`{slug}`): {entry.get('description', '')} "
                f" \u2014 {cp['quantity']}x z katalogu reuse"
            )
        else:
            reuse_lines.append(
                f"- **{slug}** \u2014 {cp['quantity']}x, UWAGA: nie znaleziono w kanonicznym katalogu"
            )

    missing_lines: list[str] = []
    for mp in missing_parts:
        donor = "TAK" if "TAK" in mp.get("donor_available", "").upper() else "NIE/Sprawdzic"
        missing_lines.append(
            f"- **{mp['function']}** ({mp['required_param']}): donor={donor} \u2014 {mp.get('notes', '')}"
        )

    lines = [
        f"# Design Dossier: {device_name}",
        "",
        f"- brief_id: `{brief_id}`",
        f"- dry_run: True",
        f"- generated_at: {utc_now().replace(microsecond=0).isoformat()}",
        "",
        "## 1. Uzasadnienie wyboru czesci",
        "",
        f"Reuse priority: **{reuse_priority}**",
        "",
        "### Czesci z kanonicznego katalogu",
        "",
    ]
    lines.extend(reuse_lines)
    lines.extend([
        "",
        "### Czesci brakujace (missing parts)",
        "",
    ])
    lines.extend(missing_lines)
    lines.extend([
        "",
        "## 2. Schemat logiczny (dry-run)",
        "",
        f"- Funkcja glowna: {primary_function}",
        f"- Zasilanie: {power_source} ({voltage_levels})",
        f"- Komunikacja: {communication}",
        f"- Srodowisko: {env}",
        "",
        "> Uwaga: To jest dry-run dossier. Schemat logiczny jest opisowy, nie CAD.",
        "> Nie udaje gotowosci hardware bez bench review.",
        "",
        "## 3. Przeplyw danych",
        "",
        f"- {fields.get('data_flow', 'Nie okreslono w briefie')}",
        "",
        "## 4. Zalozenia i ograniczenia",
        "",
        f"- Zalozenia: {fields.get('assumptions', '')}",
        f"- Ograniczenia: {fields.get('constraints', '')}",
        f"- Ryzyka: {fields.get('known_risks', 'Nie okreslono')}",
        "",
        "## 5. BOM summary",
        "",
        f"- Total items: {bom['summary']['total_items']}",
        f"- Reuse z katalogu: {bom['summary']['reuse_catalog']}",
        f"- Nie znalezione w katalogu: {bom['summary']['missing_from_catalog']}",
        f"- Missing (spoza katalogu): {bom['summary']['missing']}",
        "",
    ])
    return "\n".join(lines) + "\n"


def build_assembly_instructions(fields: dict[str, str], bom: dict) -> str:
    device_name = fields.get("device_name", "unknown")
    power_source = fields.get("power_source", "")
    flash_method = fields.get("flash_method", "Nie okreslono")

    steps: list[str] = [
        f"# Instrukcja Montazu: {device_name}",
        "",
        f"- dry_run: True",
        f"- generated_at: {utc_now().replace(microsecond=0).isoformat()}",
        "",
        "## Wymagane czesci",
        "",
    ]

    for item in bom["items"]:
        source_tag = "[REUSE]" if item["source"] == "reuse_catalog" else "[MISSING]"
        if item["source"] == "missing_from_catalog":
            source_tag = "[NOT_IN_CATALOG]"
        steps.append(f"- {source_tag} {item['quantity']}x {item['part_name']}")

    steps.extend([
        "",
        "## Krok 1: Przygotowanie zasilania",
        "",
        f"Zrodlo zasilania: {power_source}",
        "",
        "## Krok 2: Podlaczenie czesci reuse",
        "",
        "> Szczegolowe schematy podlaczenia sa poza zakresem tego dry-run.",
        "> Nie lutowac BGA/QFN bez odpowiedniego sprzetu i doswiadczenia.",
        "",
        "## Krok 3: Flashowanie firmware",
        "",
        f"Metoda flashowania: {flash_method}",
        "",
        "## Krok 4: Test podstawowy",
        "",
        "> Urzadzenie musi przejsc IntegrityRiskAssessment i ReadinessGate(integrity_ready)",
        "> przed jakimkolwiek flashowaniem na realnym hardware.",
        "",
    ])
    return "\n".join(steps) + "\n"


def build_design_risks(fields: dict[str, str]) -> dict:
    risks: list[dict] = []

    known = fields.get("known_risks", "")
    if known:
        risk_idx = 0
        for segment in known.split("."):
            segment = segment.strip()
            if not segment:
                continue
            risk_idx += 1
            risks.append({
                "id": f"R{risk_idx:03d}",
                "description": segment,
                "severity": "medium",
                "mitigation": "Wymagane reczne review przed promocja do runtime",
                "dry_run_flag": True,
            })

    adc_mentioned = "adc" in fields.get("inputs", "").lower() or "adc" in known.lower()
    if adc_mentioned and "esp8266" in fields.get("communication_interfaces", "").lower():
        risks.append({
            "id": "R099",
            "description": "ADC ESP8266 ma tylko 1 kanal i zakres 0-1V \u2014 wymaga dzielnika napiecia",
            "severity": "high",
            "mitigation": "Dodac dzielnik napiecia w assembly instructions; zweryfikowac zakres sensora",
            "dry_run_flag": True,
        })

    if not risks:
        risks.append({
            "id": "R001",
            "description": "Brak zidentyfikowanych ryzyk w briefie \u2014 reczna weryfikacja wymagana",
            "severity": "unknown",
            "mitigation": "Review brief i BOM pod katem ryzyk projektowych",
            "dry_run_flag": True,
        })

    return {
        "brief_id": fields.get("brief_id", ""),
        "risks": risks,
        "dry_run": True,
        "generated_at": utc_now().replace(microsecond=0).isoformat(),
    }


def build_missing_parts_or_assumptions(
    fields: dict[str, str],
    missing_parts: list[dict],
    catalog_parts_not_found: list[str],
) -> dict:
    missing_entries: list[dict] = []

    for mp in missing_parts:
        missing_entries.append({
            "kind": "missing_part",
            "description": mp["function"],
            "required_param": mp["required_param"],
            "donor_available": mp["donor_available"],
            "assumption": "",
        })

    for slug in catalog_parts_not_found:
        missing_entries.append({
            "kind": "not_in_catalog",
            "description": slug,
            "required_param": "",
            "donor_available": "",
            "assumption": "Part slug z briefu nie znaleziony w kanonicznym katalogu",
        })

    assumptions_text = fields.get("assumptions", "")
    if assumptions_text:
        for segment in assumptions_text.split("."):
            segment = segment.strip()
            if segment:
                missing_entries.append({
                    "kind": "assumption",
                    "description": segment,
                    "required_param": "",
                    "donor_available": "",
                    "assumption": segment,
                })

    return {
        "brief_id": fields.get("brief_id", ""),
        "entries": missing_entries,
        "dry_run": True,
        "generated_at": utc_now().replace(microsecond=0).isoformat(),
    }


def build_dry_run_report(
    brief_path: Path,
    output_dir: Path,
    checks: list[dict],
    fields: dict[str, str],
    bom: dict,
    run_stamp: str,
) -> str:
    failures = [c for c in checks if c["status"] == "fail"]
    warnings = [c for c in checks if c["status"] == "warn"]
    overall = "pass"
    if failures:
        overall = "needs_changes"
    elif warnings:
        overall = "conditional"

    lines = [
        f"# Dry Run Report: {PACK_ID}",
        "",
        f"- executed_at_utc: {utc_now().replace(microsecond=0).isoformat()}",
        f"- run_mode: local_dry_run",
        f"- overall_status: {overall}",
        f"- pack_id: {PACK_ID}",
        f"- brief_file: {brief_path}",
        f"- brief_id: {fields.get('brief_id', 'unknown')}",
        f"- device_name: {fields.get('device_name', 'unknown')}",
        f"- bom_summary: total={bom['summary']['total_items']}, reuse={bom['summary']['reuse_catalog']}, missing={bom['summary']['missing']}",
        f"- output_dir: {output_dir}",
        f"- run_stamp: {run_stamp}",
        "",
        "## Checks",
        "",
    ]

    for c in checks:
        lines.append(f"- [{c['status']}] {c['name']}: {c['details']}")

    lines.extend([
        "",
        "## Interpretation",
        "",
        "- `pass`: lokalny dry-run zakonczony sukcesem, artefakty sa review-ready.",
        "- `conditional`: pack dziala, ale sa otwarte pytania do recznego review.",
        "- `needs_changes`: przynajmniej jeden check nie przeszedl \u2014 fix wymagany.",
        "",
        "## Artefakty",
        "",
        "- `design_dossier.md` \u2014 uzasadnienie wyboru czesci i opis logiczny",
        "- `bill_of_materials.json` \u2014 BOM z odniesieniami do katalogu lub oznaczeniem missing",
        "- `assembly_instructions.md` \u2014 instrukcja montazu (dry-run, opisowa)",
        "- `design_risks.json` \u2014 zidentyfikowane ryzyka projektowe",
        "- `missing_parts_or_assumptions.json` \u2014 czesci brakujace i zalozenia",
        "- `dry_run_report.md` \u2014 ten raport",
        "",
        "> Uwaga: To jest dry-run surface. Nie generuje CAD, nie udaje gotowosci hardware.",
        "> Artefakty sa reviewowalne jako dokument, nie jako gotowy schematic.",
    ])

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Minimal dry-run execution surface dla pack-project13-blueprint-design-01"
    )
    parser.add_argument(
        "--brief", type=Path, required=True,
        help="Sciezka do pliku design brief (markdown)",
    )
    parser.add_argument(
        "--catalog", type=Path, default=DEFAULT_CATALOG,
        help="Sciezka do kanonicznego katalogu parts_master.jsonl",
    )
    parser.add_argument(
        "--output-dir", type=Path, default=None,
        help="Katalog wyjsciowy (domyslnie: pack_dir/output/)",
    )
    args = parser.parse_args()

    run_stamp = utc_now().strftime("%Y%m%dT%H%M%SZ")
    output_dir = args.output_dir or (PACK_DIR / "output")
    output_dir.mkdir(parents=True, exist_ok=True)

    checks: list[dict] = []

    if not args.brief.exists():
        print(f"BLAD: Brief nie istnieje: {args.brief}", file=sys.stderr)
        return 1

    brief_valid = validate_brief_external(args.brief)
    checks.append({
        "name": "brief_validation",
        "status": "pass" if brief_valid else "fail",
        "details": f"{args.brief} \u2014 {'PASS' if brief_valid else 'FAIL'}",
    })

    if not brief_valid:
        print("BLAD: Brief nie przeszedl walidacji. Dry-run przerwany.", file=sys.stderr)
        report = build_dry_run_report(
            args.brief, output_dir, checks, {},
            {"summary": {"total_items": 0, "reuse_catalog": 0, "missing_from_catalog": 0, "missing": 0}},
            run_stamp,
        )
        report_path = output_dir / "dry_run_report.md"
        report_path.write_text(report, encoding="utf-8")
        return 1

    text = args.brief.read_text(encoding="utf-8")
    fields = parse_markdown_tables_local(text)
    checks.append({
        "name": "brief_fields_extracted",
        "status": "pass" if len(fields) >= 10 else "warn",
        "details": f"{len(fields)} pol wyciagnietych z markdown",
    })

    catalog = load_catalog(args.catalog)
    checks.append({
        "name": "catalog_loaded",
        "status": "pass" if len(catalog) > 0 else "warn",
        "details": f"{args.catalog} \u2014 {len(catalog)} rekordow",
    })

    manifest_exists = MANIFEST_PATH.exists()
    checks.append({
        "name": "manifest_exists",
        "status": "pass" if manifest_exists else "fail",
        "details": str(MANIFEST_PATH),
    })

    runbook_exists = RUNBOOK_PATH.exists()
    checks.append({
        "name": "runbook_exists",
        "status": "pass" if runbook_exists else "warn",
        "details": str(RUNBOOK_PATH),
    })

    review_checklist_exists = REVIEW_CHECKLIST_PATH.exists()
    checks.append({
        "name": "review_checklist_exists",
        "status": "pass" if review_checklist_exists else "warn",
        "details": str(REVIEW_CHECKLIST_PATH),
    })

    catalog_parts, missing_parts = parse_reuse_sections(text)
    checks.append({
        "name": "reuse_parts_parsed",
        "status": "pass" if catalog_parts or missing_parts else "warn",
        "details": f"catalog_parts={len(catalog_parts)}, missing_parts={len(missing_parts)}",
    })

    row_errors = validate_row_level(catalog_parts, missing_parts, fields)
    if row_errors:
        checks.append({
            "name": "brief_row_validation",
            "status": "fail",
            "details": f"{len(row_errors)} bledow w wierszach sekcji 6/7: {'; '.join(row_errors[:3])}{'...' if len(row_errors) > 3 else ''}",
        })
        print("BLEDY WALIDACJI WIERSZY BRIEFU:", file=sys.stderr)
        for re_err in row_errors:
            print(f"  - {re_err}", file=sys.stderr)
        report = build_dry_run_report(
            args.brief, output_dir, checks, fields,
            {"summary": {"total_items": 0, "reuse_catalog": 0, "missing_from_catalog": 0, "missing": 0}},
            run_stamp,
        )
        report_path = output_dir / "dry_run_report.md"
        report_path.write_text(report, encoding="utf-8")
        return 1
    else:
        checks.append({
            "name": "brief_row_validation",
            "status": "pass",
            "details": "Wszystkie wiersze sekcji 6.1, 6.2 i sekcji 7 przeszly walidacje",
        })

    catalog_parts_not_found: list[str] = []
    for cp in catalog_parts:
        slug = cp["part_slug"]
        if slug not in catalog:
            catalog_parts_not_found.append(slug)

    if catalog_parts_not_found:
        checks.append({
            "name": "catalog_part_coverage",
            "status": "warn",
            "details": f"Nie znalezione w katalogu: {catalog_parts_not_found}",
        })
    else:
        checks.append({
            "name": "catalog_part_coverage",
            "status": "pass",
            "details": "Wszystkie catalog_parts znalezione w kanonicznym katalogu",
        })

    bom = build_bill_of_materials(fields, catalog_parts, missing_parts, catalog)
    bom_path = output_dir / "bill_of_materials.json"
    bom_path.write_text(json.dumps(bom, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    checks.append({
        "name": "artifact::bill_of_materials",
        "status": "pass",
        "details": str(bom_path),
    })

    dossier = build_design_dossier(fields, catalog_parts, missing_parts, catalog, bom)
    dossier_path = output_dir / "design_dossier.md"
    dossier_path.write_text(dossier, encoding="utf-8")
    checks.append({
        "name": "artifact::design_dossier",
        "status": "pass",
        "details": str(dossier_path),
    })

    instructions = build_assembly_instructions(fields, bom)
    instructions_path = output_dir / "assembly_instructions.md"
    instructions_path.write_text(instructions, encoding="utf-8")
    checks.append({
        "name": "artifact::assembly_instructions",
        "status": "pass",
        "details": str(instructions_path),
    })

    risks = build_design_risks(fields)
    risks_path = output_dir / "design_risks.json"
    risks_path.write_text(json.dumps(risks, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    checks.append({
        "name": "artifact::design_risks",
        "status": "pass",
        "details": str(risks_path),
    })

    missing_or_assumptions = build_missing_parts_or_assumptions(fields, missing_parts, catalog_parts_not_found)
    missing_path = output_dir / "missing_parts_or_assumptions.json"
    missing_path.write_text(
        json.dumps(missing_or_assumptions, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    checks.append({
        "name": "artifact::missing_parts_or_assumptions",
        "status": "pass",
        "details": str(missing_path),
    })

    report = build_dry_run_report(args.brief, output_dir, checks, fields, bom, run_stamp)
    report_path = output_dir / "dry_run_report.md"
    report_path.write_text(report, encoding="utf-8")
    checks.append({
        "name": "artifact::dry_run_report",
        "status": "pass",
        "details": str(report_path),
    })

    failures = [c for c in checks if c["status"] == "fail"]
    warnings = [c for c in checks if c["status"] == "warn"]
    overall = "pass"
    if failures:
        overall = "needs_changes"
    elif warnings:
        overall = "conditional"

    result = {
        "status": "ok",
        "overall": overall,
        "pack_id": PACK_ID,
        "brief_id": fields.get("brief_id", "unknown"),
        "device_name": fields.get("device_name", "unknown"),
        "output_dir": str(output_dir),
        "artifacts": [
            str(dossier_path),
            str(bom_path),
            str(instructions_path),
            str(risks_path),
            str(missing_path),
            str(report_path),
        ],
        "bom_summary": bom["summary"],
        "checks_total": len(checks),
        "checks_pass": sum(1 for c in checks if c["status"] == "pass"),
        "checks_warn": len(warnings),
        "checks_fail": len(failures),
        "run_stamp": run_stamp,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

    return 0 if overall != "needs_changes" else 1


if __name__ == "__main__":
    raise SystemExit(main())
