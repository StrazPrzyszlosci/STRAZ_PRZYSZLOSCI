#!/usr/bin/env python3
"""Dry-run importer for CERN KiCad Library metadata.

This script intentionally does not write to D1/SQLite. It scans a local KiCad
library checkout (or a small fixture in tests), extracts lightweight component
metadata from .kicad_sym and .kicad_mod files, and writes staging preview files
plus a Markdown quality report.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

DEFAULT_SOURCE_SLUG = "cern-kicad-libs"
DEFAULT_SOURCE_URL = "https://gitlab.com/ohwr/cern-kicad-libs"
DEFAULT_LICENSE_SPDX = "CERN-OHL-P-2.0"
DEFAULT_KICAD_VERSION_FAMILY = "9.x"
REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "PROJEKTY" / "13_baza_czesci_recykling" / "cern_kicad_import_preview"

PROPERTY_PATTERN = re.compile(r'\(property\s+"([^"]+)"\s+"((?:\\"|[^"])*)"', re.MULTILINE)
FOOTPRINT_HEADER_PATTERN = re.compile(r'\(footprint\s+"([^"]+)"')


@dataclass
class KicadComponent:
    source_slug: str
    source_url: str
    license_spdx: str
    upstream_commit: str
    kicad_version_family: str
    artifact_type: str
    library_name: str
    symbol_name: str
    footprint_name: str
    reference_prefix: str
    description: str
    keywords: str
    manufacturer: str
    mpn: str
    datasheet_url: str
    package: str
    normalized_part_number: str
    raw_symbol_path: str
    raw_footprint_path: str
    raw_metadata_json: str


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def normalize_part_number(value: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", (value or "").upper())


def decode_kicad_string(value: str) -> str:
    return value.replace('\\"', '"').strip()


def get_git_commit(path: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except Exception:
        return "unknown"
    return result.stdout.strip() or "unknown"


def relative_to_root(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def extract_top_level_symbol_forms(text: str) -> list[str]:
    forms: list[str] = []
    depth = 0
    i = 0
    capture_start: int | None = None
    capture_depth: int | None = None
    in_string = False
    escape = False

    while i < len(text):
        char = text[i]
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            i += 1
            continue

        if char == '"':
            in_string = True
            i += 1
            continue

        if char == "(":
            token_match = re.match(r"\(\s*([A-Za-z_][A-Za-z0-9_\-]*)", text[i:])
            depth += 1
            if token_match and token_match.group(1) == "symbol" and depth == 2 and capture_start is None:
                capture_start = i
                capture_depth = depth
            i += 1
            continue

        if char == ")":
            if capture_start is not None and capture_depth == depth:
                forms.append(text[capture_start : i + 1])
                capture_start = None
                capture_depth = None
            depth = max(0, depth - 1)
        i += 1
    return forms


def extract_symbol_name(symbol_form: str) -> str:
    match = re.match(r'\(symbol\s+"([^"]+)"', symbol_form.strip())
    return decode_kicad_string(match.group(1)) if match else ""


def extract_properties(symbol_form: str) -> dict[str, str]:
    return {decode_kicad_string(k): decode_kicad_string(v) for k, v in PROPERTY_PATTERN.findall(symbol_form)}


def component_from_symbol(
    symbol_path: Path,
    symbol_form: str,
    source_root: Path,
    source_slug: str,
    source_url: str,
    license_spdx: str,
    upstream_commit: str,
    kicad_version_family: str,
) -> KicadComponent:
    props = extract_properties(symbol_form)
    symbol_name = extract_symbol_name(symbol_form)
    value = props.get("Value") or symbol_name
    mpn = props.get("MPN") or props.get("Manufacturer Part Number") or ""
    description = props.get("Description") or props.get("ki_description") or ""
    keywords = props.get("ki_keywords") or props.get("Keywords") or ""
    footprint = props.get("Footprint") or ""
    manufacturer = props.get("Manufacturer") or props.get("MFR") or ""
    package = props.get("Package") or props.get("ki_fp_filters") or ""
    datasheet = props.get("Datasheet") or ""
    part_number = mpn or value or symbol_name

    return KicadComponent(
        source_slug=source_slug,
        source_url=source_url,
        license_spdx=license_spdx,
        upstream_commit=upstream_commit,
        kicad_version_family=kicad_version_family,
        artifact_type="symbol",
        library_name=symbol_path.stem,
        symbol_name=symbol_name,
        footprint_name=footprint,
        reference_prefix=props.get("Reference", ""),
        description=description,
        keywords=keywords,
        manufacturer=manufacturer,
        mpn=mpn,
        datasheet_url=datasheet,
        package=package,
        normalized_part_number=normalize_part_number(part_number),
        raw_symbol_path=relative_to_root(symbol_path, source_root),
        raw_footprint_path="",
        raw_metadata_json=json.dumps({"properties": props}, ensure_ascii=False, sort_keys=True),
    )


def parse_symbol_file(path: Path, source_root: Path, source_meta: dict[str, str]) -> list[KicadComponent]:
    text = path.read_text(encoding="utf-8", errors="replace")
    return [
        component_from_symbol(path, form, source_root, **source_meta)
        for form in extract_top_level_symbol_forms(text)
    ]


def parse_footprint_file(path: Path, source_root: Path, source_meta: dict[str, str]) -> KicadComponent | None:
    text = path.read_text(encoding="utf-8", errors="replace")
    match = FOOTPRINT_HEADER_PATTERN.search(text)
    if not match:
        return None
    footprint_name = decode_kicad_string(match.group(1))
    library_name = path.parent.name.removesuffix(".pretty")
    return KicadComponent(
        source_slug=source_meta["source_slug"],
        source_url=source_meta["source_url"],
        license_spdx=source_meta["license_spdx"],
        upstream_commit=source_meta["upstream_commit"],
        kicad_version_family=source_meta["kicad_version_family"],
        artifact_type="footprint",
        library_name=library_name,
        symbol_name="",
        footprint_name=f"{library_name}:{footprint_name}" if library_name else footprint_name,
        reference_prefix="",
        description="",
        keywords="",
        manufacturer="",
        mpn="",
        datasheet_url="",
        package=footprint_name,
        normalized_part_number=normalize_part_number(footprint_name),
        raw_symbol_path="",
        raw_footprint_path=relative_to_root(path, source_root),
        raw_metadata_json=json.dumps({"footprint": footprint_name}, ensure_ascii=False, sort_keys=True),
    )


def iter_components(source_root: Path, source_meta: dict[str, str], sample_limit: int | None = None) -> list[KicadComponent]:
    components: list[KicadComponent] = []
    for symbol_path in sorted(source_root.rglob("*.kicad_sym")):
        components.extend(parse_symbol_file(symbol_path, source_root, source_meta))
        if sample_limit and len(components) >= sample_limit:
            return components[:sample_limit]
    for footprint_path in sorted(source_root.rglob("*.kicad_mod")):
        component = parse_footprint_file(footprint_path, source_root, source_meta)
        if component:
            components.append(component)
        if sample_limit and len(components) >= sample_limit:
            return components[:sample_limit]
    return components


def write_jsonl(path: Path, rows: Iterable[KicadComponent]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(asdict(row), ensure_ascii=False, sort_keys=True) + "\n")


def write_csv(path: Path, rows: list[KicadComponent]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(asdict(rows[0]).keys()) if rows else [field.name for field in KicadComponent.__dataclass_fields__.values()]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def build_report(rows: list[KicadComponent], source_root: Path, source_meta: dict[str, str], jsonl_path: Path, csv_path: Path) -> str:
    with_symbol = sum(1 for row in rows if row.symbol_name)
    with_footprint = sum(1 for row in rows if row.footprint_name)
    with_mpn = sum(1 for row in rows if row.mpn)
    with_datasheet = sum(1 for row in rows if row.datasheet_url)
    missing_metadata = len(rows) - with_mpn
    sample_rows = rows[:10]
    sample_lines = [
        f"- `{row.artifact_type}` `{row.symbol_name or row.footprint_name}` | footprint=`{row.footprint_name}` | mpn=`{row.mpn}` | source=`{row.raw_symbol_path or row.raw_footprint_path}`"
        for row in sample_rows
    ] or ["- Brak komponentów w próbce."]

    return "\n".join([
        "# CERN KiCad Library dry-run import report",
        "",
        f"Generated at: {datetime.now(timezone.utc).isoformat()}",
        f"Source root: `{source_root}`",
        f"Source slug: `{source_meta['source_slug']}`",
        f"Source URL: `{source_meta['source_url']}`",
        f"Upstream commit: `{source_meta['upstream_commit']}`",
        f"License SPDX: `{source_meta['license_spdx']}`",
        f"KiCad version family: `{source_meta['kicad_version_family']}`",
        "",
        "## Summary",
        "",
        f"- Components in preview: {len(rows)}",
        f"- Rows with symbol name: {with_symbol}",
        f"- Rows with footprint: {with_footprint}",
        f"- Rows with MPN: {with_mpn}",
        f"- Rows with datasheet URL: {with_datasheet}",
        f"- Rows missing explicit MPN: {missing_metadata}",
        "",
        "## Outputs",
        "",
        f"- JSONL: `{jsonl_path}`",
        f"- CSV: `{csv_path}`",
        "",
        "## Sample candidates",
        "",
        *sample_lines,
        "",
        "## Import decision",
        "",
        "Do not convert the full CERN KiCad library before ingest. This dry-run keeps source paths, commit, license and KiCad version family as provenance. Use KiCad conversion later only for project export or compatibility checks.",
        "",
    ])


def run_import(args: argparse.Namespace) -> dict[str, Path | int]:
    source_root = Path(args.source).resolve()
    if not source_root.exists():
        raise FileNotFoundError(f"Source path does not exist: {source_root}")

    source_meta = {
        "source_slug": args.source_slug,
        "source_url": args.source_url,
        "license_spdx": args.license_spdx,
        "upstream_commit": args.upstream_commit or get_git_commit(source_root),
        "kicad_version_family": args.kicad_version_family,
    }
    rows = iter_components(source_root, source_meta, args.sample_limit)
    stamp = args.output_stamp or utc_stamp()
    output_root = Path(args.output_root).resolve()
    results_dir = output_root / "results"
    reports_dir = output_root / "reports"
    jsonl_path = results_dir / f"cern_kicad_components_sample_{stamp}.jsonl"
    csv_path = results_dir / f"cern_kicad_components_sample_{stamp}.csv"
    report_path = reports_dir / f"cern_kicad_import_preview_{stamp}.md"

    write_jsonl(jsonl_path, rows)
    write_csv(csv_path, rows)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(build_report(rows, source_root, source_meta, jsonl_path, csv_path), encoding="utf-8")

    return {"count": len(rows), "jsonl": jsonl_path, "csv": csv_path, "report": report_path}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Dry-run CERN KiCad Library importer for NSIP staging previews.")
    parser.add_argument("--source", required=True, help="Local CERN KiCad checkout or fixture directory.")
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT), help="Directory for reports/ and results/ preview outputs.")
    parser.add_argument("--sample-limit", type=int, default=200, help="Maximum number of components to include in preview; 0 means no limit.")
    parser.add_argument("--source-slug", default=DEFAULT_SOURCE_SLUG)
    parser.add_argument("--source-url", default=DEFAULT_SOURCE_URL)
    parser.add_argument("--license-spdx", default=DEFAULT_LICENSE_SPDX)
    parser.add_argument("--kicad-version-family", default=DEFAULT_KICAD_VERSION_FAMILY)
    parser.add_argument("--upstream-commit", default="", help="Override source commit; defaults to git rev-parse when available.")
    parser.add_argument("--output-stamp", default="", help="Deterministic suffix for tests/reproducible dry-runs.")
    args = parser.parse_args(argv)
    if args.sample_limit is not None and args.sample_limit <= 0:
        args.sample_limit = None
    return args


def main(argv: list[str] | None = None) -> int:
    result = run_import(parse_args(argv))
    print(json.dumps({key: str(value) for key, value in result.items()}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
