#!/usr/bin/env python3
"""Expiry report dla HumanApprovalRecord (T31).

Ryzyko z handoffu PO_T21_T26: seedy approvals wygasają dyskretnie (test
test_seed_validates pada dopiero PO dacie). Ten raport ostrzega WCZEŚNIEJ:
- WARNING: rekord wygasa w ciągu --warn-days (domyślnie 30),
- ERROR + exit 1: rekord już wygasł (do naprawy renewalem lub archiwizacją).

Użycie w cron/CI:
    python3 human_approval/expiry_report.py [--warn-days 30] [path]
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RECORDS = ROOT / "human_approval" / "seed_approvals.json"
DEFAULT_WARN_DAYS = 30


def _parse_iso(value: Any) -> datetime | None:
    try:
        return datetime.fromisoformat(str(value))
    except (ValueError, TypeError):
        return None


def days_until(expires_at: str, now: datetime | None = None) -> int | None:
    """Pełne dni do wygaśnięcia; wartość ujemna = już wygasłe."""
    expiry = _parse_iso(expires_at)
    if expiry is None:
        return None
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    return (expiry - current).days


def build_report(payload: dict, now: datetime | None = None, warn_days: int = DEFAULT_WARN_DAYS) -> dict:
    records = payload.get("records")
    if not isinstance(records, list):
        return {"error": "records must be a list"}
    report = {
        "expired": [],
        "expiring_soon": [],
        "ok": [],
        "invalid": [],
        "warn_days": int(warn_days),
    }
    for record in records:
        if not isinstance(record, dict):
            continue
        rid = record.get("id", "<unknown>")
        if record.get("revoked") is True:
            report["invalid"].append({"id": rid, "reason": "revoked=true"})
            continue
        days_left = days_until(record.get("expires_at", ""), now)
        if days_left is None:
            report["invalid"].append({"id": rid, "reason": "expires_at_not_iso"})
        elif days_left < 0:
            report["expired"].append({"id": rid, "expires_at": record.get("expires_at"), "days_left": days_left})
        elif days_left <= warn_days:
            report["expiring_soon"].append({"id": rid, "expires_at": record.get("expires_at"), "days_left": days_left})
        else:
            report["ok"].append({"id": rid, "expires_at": record.get("expires_at"), "days_left": days_left})
    return report


def format_lines(report: dict) -> list[str]:
    lines: list[str] = []
    for entry in report.get("invalid", []):
        lines.append(f"WARNING: {entry['id']}: {entry['reason']}")
    for entry in report.get("expired", []):
        lines.append(f"ERROR: {entry['id']}: approval expired at {entry['expires_at']} ({entry['days_left']} days ago); renew or archive")
    for entry in report.get("expiring_soon", []):
        lines.append(f"WARNING: {entry['id']}: expires at {entry['expires_at']} in {entry['days_left']} days; schedule renewal")
    return lines


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Human approval expiry report")
    parser.add_argument("path", type=Path, nargs="?", default=DEFAULT_RECORDS)
    parser.add_argument("--warn-days", type=int, default=DEFAULT_WARN_DAYS)
    args = parser.parse_args(list(argv) if argv is not None else None)

    payload = json.loads(args.path.read_text(encoding="utf-8"))
    report = build_report(payload, warn_days=args.warn_days)
    if "error" in report:
        print(f"ERROR: {report['error']}")
        return 1

    lines = format_lines(report)
    summary = (
        f"ok={len(report['ok'])} expiring_soon={len(report['expiring_soon'])} "
        f"expired={len(report['expired'])} invalid={len(report['invalid'])}"
    )
    for line in lines:
        print(line)
    print(f"SUMMARY: {summary}")

    if report["expired"] or report["invalid"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
