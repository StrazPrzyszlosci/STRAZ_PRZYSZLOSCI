#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROJECT_DIR = Path(__file__).resolve().parents[1]
BASE_DIR = PROJECT_DIR / "autonomous_test"
RESULTS_DIR = BASE_DIR / "results"
REPORTS_DIR = BASE_DIR / "reports"
TEST_DB_PATH = RESULTS_DIR / "test_db.jsonl"
INVENTREE_PATH = RESULTS_DIR / "inventree_import.jsonl"
ECOEDA_PATH = RESULTS_DIR / "ecoEDA_inventory.csv"
REPORT_PATH = REPORTS_DIR / "rebuild_autonomous_outputs_report.md"
SKIPPED_PATH = REPORTS_DIR / "rebuild_autonomous_outputs_skipped.jsonl"

ECOEDA_HEADERS = ["Reference", "Value", "Footprint", "Datasheet", "Description"]

INVALID_EXACT_VALUES = {
    "",
    "none",
    "null",
    "brak",
    "unknown",
    "unknown part",
    "requires_hq_check",
}


@dataclass
class ClassifiedRecord:
    record: dict[str, Any]
    normalized_part_number: str
    category: str
    reference: str


def normalize_space(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def normalize_part_number(value: Any) -> str:
    return re.sub(r"[^A-Z0-9._+\-/]", "", normalize_space(value).upper())


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        parsed = json.loads(line)
        if isinstance(parsed, dict):
            rows.append(parsed)
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) for row in rows) + "\n",
        encoding="utf-8",
    )


def choose_best_record(records: list[ClassifiedRecord]) -> ClassifiedRecord:
    def score(item: ClassifiedRecord) -> tuple[float, int, int]:
        record = item.record
        verification = record.get("verification_raw") or record.get("verification") or {}
        verified = 1 if verification.get("verified") is True else 0
        confidence = float(record.get("confidence") or 0.0)
        has_datasheet = 1 if normalize_space(record.get("datasheet_url")) else 0
        return (
            verified + confidence + has_datasheet,
            len(item.normalized_part_number),
            len(normalize_space(record.get("part_name"))),
        )

    return sorted(records, key=score, reverse=True)[0]


def infer_reference(part_name: str, footprint: str) -> str:
    combined = f"{part_name} {footprint}".lower()
    if any(token in combined for token in ["capacitor", "kondensator"]):
        return "C?"
    if any(token in combined for token in ["resistor", "rezystor"]):
        return "R?"
    if any(token in combined for token in ["inductor", "coil", "cewka"]):
        return "L?"
    if any(token in combined for token in ["diode", "dioda"]):
        return "D?"
    if any(token in combined for token in ["transistor", "mosfet"]):
        return "Q?"
    if any(token in combined for token in ["connector", "usb", "gniazdo"]):
        return "J?"
    if "pcb" in combined or "board" in combined or "plyta" in combined:
        return "PCB?"
    return "U?"


def infer_category(record: dict[str, Any]) -> str:
    verification = record.get("verification_raw") or record.get("verification") or {}
    category = normalize_space(verification.get("category"))
    if category:
        return category

    part_name = normalize_space(record.get("part_name")).lower()
    footprint = normalize_space(record.get("footprint")).lower()
    combined = f"{part_name} {footprint}"
    if any(token in combined for token in ["capacitor", "kondensator"]):
        return "Capacitors"
    if any(token in combined for token in ["resistor", "rezystor"]):
        return "Resistors"
    if any(token in combined for token in ["inductor", "coil", "cewka"]):
        return "Inductors"
    if any(token in combined for token in ["diode", "dioda"]):
        return "Diodes"
    if any(token in combined for token in ["transistor", "mosfet"]):
        return "Transistors"
    if any(token in combined for token in ["memory", "ram", "nand", "flash"]):
        return "Memory"
    if any(token in combined for token in ["cpu", "processor", "controller", "kbc", "chip", "układ", "ic", "programmer"]):
        return "Integrated Circuits"
    if any(token in combined for token in ["board", "pcb", "motherboard", "plyta"]):
        return "Boards"
    return "Recovered Components"


def classify_record(record: dict[str, Any]) -> tuple[ClassifiedRecord | None, str | None]:
    raw_part_number = normalize_space(record.get("part_number"))
    lowered = raw_part_number.casefold()
    if lowered in INVALID_EXACT_VALUES:
        return None, "empty_or_placeholder_part_number"
    if lowered.startswith("błąd") or lowered.startswith("blad") or lowered.startswith("error"):
        return None, "error_marker_in_part_number"
    if re.fullmatch(r"[A-Z]?\d+(?:,\s*[A-Z]?\d+)+", raw_part_number, flags=re.IGNORECASE):
        return None, "looks_like_designator_list"
    if re.fullmatch(r"[A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż ]{8,}", raw_part_number):
        return None, "looks_like_plain_text_phrase"

    normalized_part = normalize_part_number(raw_part_number)
    if not normalized_part:
        return None, "normalized_part_number_empty"
    if len(re.findall(r"[A-Z0-9]", normalized_part)) < 3:
        return None, "too_short_after_normalization"

    part_name = normalize_space(record.get("part_name"))
    footprint = normalize_space(record.get("footprint"))
    category = infer_category(record)
    reference = infer_reference(part_name, footprint)
    return (
        ClassifiedRecord(
            record=record,
            normalized_part_number=normalized_part,
            category=category,
            reference=reference,
        ),
        None,
    )


def build_inventree_rows(records: list[ClassifiedRecord]) -> list[dict[str, Any]]:
    grouped: dict[str, list[ClassifiedRecord]] = {}
    for item in records:
        grouped.setdefault(item.normalized_part_number, []).append(item)

    rows: list[dict[str, Any]] = []
    for _, grouped_records in sorted(grouped.items()):
        best = choose_best_record(grouped_records)
        record = best.record
        rows.append(
            {
                "name": normalize_space(record.get("part_number")),
                "description": normalize_space(record.get("part_name")),
                "category": best.category,
                "IPN": best.normalized_part_number,
                "parameters": {
                    "Footprint": normalize_space(record.get("footprint")) or "Unknown",
                    "SourceDevice": normalize_space(record.get("device")) or "Unknown",
                    "PinoutSummary": normalize_space((record.get("pinout") or {}).get("summary")),
                },
                "link": normalize_space(record.get("yt_link")),
                "stock_location": normalize_space(record.get("device")) or "Unknown Device",
            }
        )
    return rows


def build_ecoeda_rows(records: list[ClassifiedRecord]) -> list[dict[str, str]]:
    grouped: dict[tuple[str, str], list[ClassifiedRecord]] = {}
    for item in records:
        key = (
            normalize_space(item.record.get("device")),
            item.normalized_part_number,
        )
        grouped.setdefault(key, []).append(item)

    rows: list[dict[str, str]] = []
    for _, grouped_records in sorted(grouped.items()):
        best = choose_best_record(grouped_records)
        record = best.record
        rows.append(
            {
                "Reference": best.reference,
                "Value": normalize_space(record.get("part_number")),
                "Footprint": normalize_space(record.get("footprint")) or "Unknown",
                "Datasheet": normalize_space(record.get("datasheet_url")) or normalize_space(record.get("source_video")),
                "Description": f"{normalize_space(record.get('part_name'))} | donor: {normalize_space(record.get('device'))}",
            }
        )
    return rows


def write_ecoeda_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=ECOEDA_HEADERS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_report(
    total_records: int,
    accepted: list[ClassifiedRecord],
    skipped: list[dict[str, Any]],
    inventree_rows: list[dict[str, Any]],
    ecoeda_rows: list[dict[str, str]],
    report_path: Path,
) -> None:
    reasons = Counter(item["reason"] for item in skipped)
    lines = [
        "# Rebuild Autonomous Outputs Report",
        "",
        f"- source: {TEST_DB_PATH.relative_to(PROJECT_DIR)}",
        f"- total_records: {total_records}",
        f"- accepted_records: {len(accepted)}",
        f"- skipped_records: {len(skipped)}",
        f"- inventree_rows: {len(inventree_rows)}",
        f"- ecoeda_rows: {len(ecoeda_rows)}",
        "",
        "## Outputs",
        "",
        f"- {INVENTREE_PATH.relative_to(PROJECT_DIR)}",
        f"- {ECOEDA_PATH.relative_to(PROJECT_DIR)}",
        f"- {SKIPPED_PATH.relative_to(PROJECT_DIR)}",
        "",
        "## Skip Reasons",
        "",
    ]
    if reasons:
        for reason, count in sorted(reasons.items()):
            lines.append(f"- {reason}: {count}")
    else:
        lines.append("- none")

    lines.extend(["", "## Sample Accepted Parts", ""])
    if accepted:
        for item in accepted[:10]:
            lines.append(
                f"- {normalize_space(item.record.get('part_number'))} | {normalize_space(item.record.get('part_name'))} | {normalize_space(item.record.get('device'))}"
            )
    else:
        lines.append("- none")

    lines.extend(["", "## Sample Skipped Records", ""])
    if skipped:
        for item in skipped[:10]:
            lines.append(
                f"- {item['reason']} | part_number={item['part_number']} | part_name={item['part_name']} | device={item['device']}"
            )
    else:
        lines.append("- none")

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Odbudowuje review-ready artefakty autonomous_test z test_db.jsonl dla Project 13."
    )
    parser.add_argument("--test-db", type=Path, default=TEST_DB_PATH)
    parser.add_argument("--inventree-output", type=Path, default=INVENTREE_PATH)
    parser.add_argument("--ecoeda-output", type=Path, default=ECOEDA_PATH)
    parser.add_argument("--report-output", type=Path, default=REPORT_PATH)
    parser.add_argument("--skipped-output", type=Path, default=SKIPPED_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    records = load_jsonl(args.test_db.resolve())

    accepted: list[ClassifiedRecord] = []
    skipped: list[dict[str, Any]] = []
    for record in records:
        classified, reason = classify_record(record)
        if classified is not None:
            accepted.append(classified)
            continue
        skipped.append(
            {
                "reason": reason,
                "part_number": normalize_space(record.get("part_number")),
                "part_name": normalize_space(record.get("part_name")),
                "device": normalize_space(record.get("device")),
                "source_video": normalize_space(record.get("source_video")),
            }
        )

    inventree_rows = build_inventree_rows(accepted)
    ecoeda_rows = build_ecoeda_rows(accepted)
    write_jsonl(args.inventree_output.resolve(), inventree_rows)
    write_ecoeda_csv(args.ecoeda_output.resolve(), ecoeda_rows)
    write_jsonl(args.skipped_output.resolve(), skipped)
    write_report(
        total_records=len(records),
        accepted=accepted,
        skipped=skipped,
        inventree_rows=inventree_rows,
        ecoeda_rows=ecoeda_rows,
        report_path=args.report_output.resolve(),
    )

    print(
        json.dumps(
            {
                "status": "ok",
                "accepted_records": len(accepted),
                "skipped_records": len(skipped),
                "inventree_rows": len(inventree_rows),
                "ecoeda_rows": len(ecoeda_rows),
                "inventree_output": str(args.inventree_output.resolve()),
                "ecoeda_output": str(args.ecoeda_output.resolve()),
                "report_output": str(args.report_output.resolve()),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
