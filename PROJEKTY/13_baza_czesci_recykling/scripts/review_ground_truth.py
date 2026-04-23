#!/usr/bin/env python3
"""Review and finalize ground-truth labels for benchmark_sample.jsonl.

Applies the ground-truth criteria:
- is_valid_part=true: Real, specific electronic component with valid or plausible MPN
- is_valid_part=false: Board model, designator list, OCR artifact, date code, generic label,
  programmer/tool, enclosure, null/None, custom transformer without standard MPN,
  or text that does not identify a specific reusable component.

Also handles mislabeled records where part_name doesn't match part_number.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

BENCHMARK_DIR = Path(__file__).resolve().parents[1] / "autonomous_test" / "benchmarks"
SAMPLE_PATH = BENCHMARK_DIR / "benchmark_sample.jsonl"

REVIEW_OVERRIDES: dict[str, dict[str, Any]] = {
    "bench-v1-0000": {
        "is_valid_part": False,
        "reviewer_notes": "1500µF is a capacitance value, not an MPN. Generic capacitor specification without manufacturer part number.",
    },
    "bench-v1-0006": {
        "is_valid_part": False,
        "reviewer_notes": "P28A41E is likely a date/lot code, not a recognized MPN for SMD capacitors.",
    },
    "bench-v1-0007": {
        "is_valid_part": False,
        "reviewer_notes": "230130, 2R2, 33 25V H33 are value designators and date codes, not MPNs.",
    },
    "bench-v1-0012": {
        "is_valid_part": False,
        "reviewer_notes": "UE50MU6102KXXH is a Samsung TV model number, not an electronic component MPN.",
    },
    "bench-v1-0015": {
        "is_valid_part": False,
        "reviewer_notes": "K6100 1124 08.24 appears to be a date code (Aug 2024) and lot number, not a valid eMMC MPN (Samsung eMMC would start with KLMAG2...).",
    },
    "bench-v1-0018": {
        "is_valid_part": False,
        "reviewer_notes": "1244-2 is a generic speaker identifier, not a recognized component MPN.",
    },
    "bench-v1-0025": {
        "is_valid_part": False,
        "reviewer_notes": "part_number BCM2837B01FSBG is SoC MPN (duplicated from bench-v1-0024), but part_name says Micro USB Power Input — mismatch. The power input jack itself has no MPN.",
    },
    "bench-v1-0028": {
        "is_valid_part": False,
        "reviewer_notes": "MINIJST E DC546134603 ST looks like a connector type + PCB serial, not a standard component MPN.",
    },
    "bench-v1-0031": {
        "is_valid_part": False,
        "reviewer_notes": "20-Sep-11 0756 BOM:01 is a date code and BOM reference, not a relay MPN.",
    },
    "bench-v1-0032": {
        "is_valid_part": False,
        "reviewer_notes": "JKB1, JKB2 are PCB test point designators, not component MPNs.",
    },
    "bench-v1-0033": {
        "is_valid_part": False,
        "reviewer_notes": "RK214 is a PCB reference designator (resistor), not an MPN.",
    },
    "bench-v1-0034": {
        "is_valid_part": False,
        "reviewer_notes": "PQB18 is a PCB reference designator, not an MPN.",
    },
    "bench-v1-0035": {
        "is_valid_part": False,
        "reviewer_notes": "PQB18 is a PCB reference designator (same as bench-v1-0034), not an MPN.",
    },
    "bench-v1-0036": {
        "is_valid_part": False,
        "reviewer_notes": "RV41, CV541... are all PCB reference designators, not MPNs.",
    },
    "bench-v1-0054": {
        "is_valid_part": False,
        "reviewer_notes": "RM 121 is a radio model identifier (Unitra RM 121), not a component MPN.",
    },
    "bench-v1-0059": {
        "is_valid_part": False,
        "reviewer_notes": "UL E141940 V-0 130 C... is a safety certification mark and production date, not an MOV MPN.",
    },
    "bench-v1-0077": {
        "is_valid_part": True,
        "reviewer_notes": "QHAD01249 is a Samsung-internal transformer part number. Custom but valid for reuse as a board-level replacement part.",
    },
}

MISLABEL_CORRECTIONS: dict[str, dict[str, Any]] = {
    "bench-v1-0003": {
        "is_valid_part": True,
        "reviewer_notes": "TPS65994 is a real TI USB-C PD controller MPN. observed_text=BRAK means OCR failed but part_number is correct. Verified: true MPN.",
    },
    "bench-v1-0009": {
        "is_valid_part": True,
        "reviewer_notes": "N15P-Q3-A1 is a real NVIDIA GPU MPN (GK107). observed_text=BRAK but MPN is valid. Verified: true MPN.",
    },
    "bench-v1-0050": {
        "is_valid_part": True,
        "reviewer_notes": "MX25L25673G is a real Macronix SPI Flash MPN. observed_text shows OCR failed but MPN is valid.",
    },
    "bench-v1-0061": {
        "is_valid_part": True,
        "reviewer_notes": "ITE IT8628E is a real ITE Super I/O MPN. The part_name says VRAM but the actual IC is a valid component.",
    },
    "bench-v1-0070": {
        "is_valid_part": True,
        "reviewer_notes": "JMicron JMS578 is a real SATA-to-USB bridge controller MPN. Valid component regardless of part_name mismatch.",
    },
    "bench-v1-0072": {
        "is_valid_part": True,
        "reviewer_notes": "ITE IT8512E is a real ITE Embedded Controller MPN. part_name=Cooling Fan is wrong — the IC is a valid component.",
    },
    "bench-v1-0075": {
        "is_valid_part": True,
        "reviewer_notes": "ITE IT8512E is a real ITE Embedded Controller MPN. part_name=CMOS Battery is wrong — duplicate IC, valid component.",
    },
    "bench-v1-0078": {
        "is_valid_part": True,
        "reviewer_notes": "2SD526 is a real NPN power transistor MPN (Darlington). Valid component with TO-220 package.",
    },
    "bench-v1-0079": {
        "is_valid_part": True,
        "reviewer_notes": "BD243C is a real NPN power transistor MPN. Valid component with TO-220 package.",
    },
}


def main() -> int:
    if not SAMPLE_PATH.exists():
        print(f"Sample not found: {SAMPLE_PATH}")
        return 1

    records: list[dict[str, Any]] = []
    for raw_line in SAMPLE_PATH.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        records.append(json.loads(line))

    all_overrides = {**REVIEW_OVERRIDES, **MISLABEL_CORRECTIONS}
    changed = 0

    for rec in records:
        sid = rec.get("sample_id", "")
        if sid in all_overrides:
            override = all_overrides[sid]
            old_val = rec["ground_truth"]["is_valid_part"]
            new_val = override["is_valid_part"]
            rec["ground_truth"]["is_valid_part"] = new_val
            rec["ground_truth"]["label_pending_review"] = False
            rec["ground_truth"]["reviewer_notes"] = override["reviewer_notes"]
            if old_val != new_val:
                changed += 1
            continue

        rec["ground_truth"]["label_pending_review"] = False
        if not rec["ground_truth"]["reviewer_notes"]:
            rec["ground_truth"]["reviewer_notes"] = (
                "Heuristic label confirmed by review: matches ground-truth criteria."
            )

    SAMPLE_PATH.write_text(
        "\n".join(
            json.dumps(rec, ensure_ascii=False, separators=(",", ":"))
            for rec in records
        )
        + "\n",
        encoding="utf-8",
    )

    valid = sum(1 for r in records if r["ground_truth"]["is_valid_part"])
    invalid = len(records) - valid
    pending = sum(
        1 for r in records if r["ground_truth"].get("label_pending_review", True)
    )

    print(f"Reviewed {len(records)} records.")
    print(f"  Changes applied: {changed}")
    print(f"  is_valid_part=true:  {valid}")
    print(f"  is_valid_part=false: {invalid}")
    print(f"  label_pending_review=true: {pending}")
    print(f"  Sample saved to: {SAMPLE_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
