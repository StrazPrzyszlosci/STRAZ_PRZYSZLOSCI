#!/usr/bin/env python3
"""Validate HumanApprovalRecord (T19, dawniej H4).

Rekord zatwierdzenia przez czlowieka: kto/co/zakres/czas/ryzyka/expiry/rollback.
Blokady:
- Approval wygasa; timestamp expiry meets jest bardziej na poziomie platyny (walidator weryfikuje, czy not still valid).
- Approval dla kodu nie zatwierdza fizycznego dzialania.
- Approval dla providerow nie zatwierdza zwiekszania kosztow bez ledgeru.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RECORDS = ROOT / "human_approval" / "seed_approvals.json"

ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{2,80}$")
SCOPE_VALUES = {
    "code_review", "physical_installation", "provider_cost_increase",
    "production_deploy", "dry_run_only",
}
ROLES = {"operator", "maintainer", "volunteer"}


def _is_nonempty_str(v: Any) -> bool:
    return isinstance(v, str) and len(v) > 0


def _has_expired(expires_at: str) -> bool:
    try:
        dt = datetime.fromisoformat(expires_at)
        return dt < datetime.now(timezone.utc)
    except (ValueError, TypeError):
        return True


def validate_record(record: dict) -> list[str]:
    errors: list[str] = []
    rid = record.get("id", "<unknown>")
    if not _is_nonempty_str(rid) or not ID_RE.match(str(rid)):
        errors.append(f"id must match {ID_RE.pattern}")
    if record.get("revoked") is not True and not isinstance(record.get("revoked"), bool):
        errors.append("revoked must be boolean")
    if record.get("revoked") is True:
        errors.append("revoked=true — approval is cancelled; record should be archived/overwritten")
    if not _is_nonempty_str(record.get("reason")) or len(record.get("reason", "")) < 10:
        errors.append("reason must be >=10 chars")

    ab = record.get("approved_by", {})
    if not isinstance(ab, dict):
        errors.append("approved_by must be object")
    else:
        if ab.get("role") not in ROLES:
            errors.append(f"approved_by.role must be one of {sorted(ROLES)}")
        if not _is_nonempty_str(ab.get("label")):
            errors.append("approved_by.label required")

    scope = record.get("approved_scope")
    if scope not in SCOPE_VALUES:
        errors.append(f"approved_scope must be one of {sorted(SCOPE_VALUES)}")
    else:
        # Scope-specific hard rules:
        # code_review cannot ok physical install.
        # provider_cost_increase requires cost_ledger_ref.
        if scope == "code_review":
            targets = " ".join(str(x) for x in record.get("artifacts_or_target", []))
            if any(w in targets.lower() for w in ("install", "actuate", "deploy_prod", "trigger_physical")):
                errors.append(
                    "code_review approval cannot cover physical installation or "
                    "production deployment scopes"
                )
        if scope == "provider_cost_increase":
            if not _is_nonempty_str(record.get("cost_ledger_ref")):
                errors.append(
                    "provider_cost_increase approval requires cost_ledger_ref "
                    "(links to the specific cost/energy ledger entry)"
                )

    if not _is_nonempty_str(record.get("expires_at")):
        errors.append("expires_at required")
    elif _has_expired(record.get("expires_at", "")):
        errors.append(
            f"approval expired at {record.get('expires_at')}; "
            "renewed or archive record required"
        )

    if not _is_nonempty_str(record.get("granted_at")):
        errors.append("granted_at required")

    if not isinstance(record.get("risks"), list) or not record.get("risks"):
        errors.append("risks must be a non-empty list of strings")
    elif not all(isinstance(r, str) for r in record.get("risks")):
        errors.append("risks must be list of strings")

    if not _is_nonempty_str(record.get("rollback_command")) or len(record.get("rollback_command", "")) < 2:
        errors.append("rollback_command required >=2 chars")

    if not _is_nonempty_str(record.get("human_control_point")) or len(record.get("human_control_point", "")) < 5:
        errors.append("human_control_point required >=5 chars")

    return errors


def validate_records(payload: dict) -> list[str]:
    records = payload.get("records")
    if not isinstance(records, list) or not records:
        return ["records must be a non-empty list"]
    errors: list[str] = []
    ids: set[str] = set()
    for i, rec in enumerate(records):
        if not isinstance(rec, dict):
            errors.append(f"records[{i}] must be object")
            continue
        for e in validate_record(rec):
            errors.append(f"records[{i}]::{rec.get('id', '<unknown>')}: {e}")
        rid = rec.get("id")
        if isinstance(rid, str):
            if rid in ids:
                errors.append(f"{rid}: duplicate id")
            ids.add(rid)
    return errors


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path, nargs="?", default=DEFAULT_RECORDS)
    args = parser.parse_args(list(argv) if argv is not None else None)
    errors = validate_records(json.loads(args.path.read_text(encoding="utf-8")))
    if errors:
        for e in errors:
            print(f"ERROR: {e}")
        return 1
    print(f"OK: human approval records valid: {args.path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())