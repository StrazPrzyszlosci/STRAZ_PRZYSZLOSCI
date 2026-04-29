#!/usr/bin/env python3
"""Smoke-test baseline dla execution surface pack-project13-blueprint-design-01.

Uruchamia 3 testy:
1. VALID_BRIEF: dry_run_blueprint_design.py na poprawnym sample briefie — oczekiwany PASS
2. INVALID_BRIEF: dry_run_blueprint_design.py na blednym briefie — oczekiwany FAIL
3. VALIDATOR_ONLY: validate_design_brief.py na blednym briefie — oczekiwany FAIL

Uzycie:
    python3 smoke_test_blueprint_design.py
    python3 smoke_test_blueprint_design.py --verbose
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
VALID_BRIEF = PROJECT_ROOT / "docs" / "SAMPLE_DESIGN_BRIEF_WIFI_TEMP_SENSOR.md"
INVALID_BRIEF = PROJECT_ROOT / "docs" / "INVALID_DESIGN_BRIEF_BAD_ROWS.md"
DRY_RUN_SCRIPT = SCRIPTS_DIR / "dry_run_blueprint_design.py"
VALIDATOR_SCRIPT = SCRIPTS_DIR / "validate_design_brief.py"


def run_command(cmd: list[str], label: str, expect_pass: bool, verbose: bool) -> tuple[bool, str]:
    result = subprocess.run(cmd, capture_output=True, text=True)
    actual_pass = result.returncode == 0
    match = actual_pass == expect_pass
    status = "PASS" if match else "FAIL"
    detail = f"{label}: oczekiwano {'PASS' if expect_pass else 'FAIL'}, otrzymano {'PASS' if actual_pass else 'FAIL'} — {status}"
    if verbose or not match:
        detail += f"\n  stdout: {result.stdout[:500]}"
        if result.stderr:
            detail += f"\n  stderr: {result.stderr[:500]}"
    return match, detail


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-test baseline dla blueprint-design-01")
    parser.add_argument("--verbose", action="store_true", help="Pokaz pelny output komend")
    args = parser.parse_args()

    results: list[tuple[bool, str]] = []

    if not DRY_RUN_SCRIPT.exists():
        print(f"BLAD: {DRY_RUN_SCRIPT} nie istnieje", file=sys.stderr)
        return 1

    if not VALID_BRIEF.exists():
        print(f"BLAD: {VALID_BRIEF} nie istnieje", file=sys.stderr)
        return 1

    if not INVALID_BRIEF.exists():
        print(f"UWAGA: {INVALID_BRIEF} nie istnieje — pomijam test negatywny")
        print("  Aby uruchomic test negatywny, utworz INVALID_DESIGN_BRIEF_BAD_ROWS.md")
    else:
        m, d = run_command(
            ["python3", str(DRY_RUN_SCRIPT), "--brief", str(INVALID_BRIEF)],
            "INVALID_BRIEF (dry-run)",
            expect_pass=False,
            verbose=args.verbose,
        )
        results.append((m, d))

        m2, d2 = run_command(
            ["python3", str(VALIDATOR_SCRIPT), str(INVALID_BRIEF)],
            "INVALID_BRIEF (validator)",
            expect_pass=False,
            verbose=args.verbose,
        )
        results.append((m2, d2))

    m3, d3 = run_command(
        ["python3", str(DRY_RUN_SCRIPT), "--brief", str(VALID_BRIEF)],
        "VALID_BRIEF (dry-run)",
        expect_pass=True,
        verbose=args.verbose,
    )
    results.append((m3, d3))

    m4, d4 = run_command(
        ["python3", str(VALIDATOR_SCRIPT), str(VALID_BRIEF)],
        "VALID_BRIEF (validator)",
        expect_pass=True,
        verbose=args.verbose,
    )
    results.append((m4, d4))

    print("=" * 60)
    print("SMOKE TEST BASELINE: pack-project13-blueprint-design-01")
    print("=" * 60)
    for match, detail in results:
        print(f"  {'[PASS]' if match else '[FAIL]'} {detail}")

    all_pass = all(m for m, _ in results)
    total = len(results)
    passed = sum(1 for m, _ in results if m)
    print(f"\nWerdykt: {passed}/{total} testow przeszlo")
    print("OVERALL:", "PASS" if all_pass else "FAIL")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
