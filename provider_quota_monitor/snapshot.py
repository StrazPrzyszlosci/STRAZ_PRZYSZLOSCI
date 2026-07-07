#!/usr/bin/env python3
"""Provider quota monitor cell (T17, dawniej H2).

Czyta provider_matrix.json, tworzy snapshot limity (manual lub auto),
zglasza brak snapshotu jako blocker dla agent chain.

Bez zewnetrznych zaleznosci. Polityki:
- brak quota_snapshot.json => block_agent_chain() zwraca True (chain blokowany),
- NIM 40 RPM NIE jest gwarantowany (flaga guaranteed=false),
- Google AI Studio wymaga odniesienia do aktywnych limitow projektu.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MATRIX = ROOT / "agent_runtime_plans" / "hermes_pilot" / "provider_matrix.json"
DEFAULT_SNAPSHOT_OUT = ROOT / "agent_runtime_plans" / "hermes_pilot" / "quota_snapshot.json"

# Required fields per snapshot entry (manual lub auto).
REQ_SNAPSHOT_FIELDS = {"provider", "model", "source", "checked_at", "status"}
SNAPSHOT_STATUS_OK = "ok"
SNAPSHOT_STATUS_STALE = "stale"
SNAPSHOT_STATUS_MISSING = "missing"
NIM_KNOWN_BASELINE_RPM = 40


def _is_nonempty_str(v: Any) -> bool:
    return isinstance(v, str) and len(v) > 0


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def snapshot_from_matrix(matrix: dict, *, source: str = "manual") -> dict:
    """Zbuduj pusty/template snapshot z provider_matrix.

    W tej komorce NIE odpytujemy sieci - operator uzupelnia wartosci RPM/TPM/RPD.
    """
    entries = []
    for p in matrix.get("providers", []):
        pid = p.get("id", "unknown")
        # NIM baseline oznaczony jako nie-gwarantowany.
        guaranteed = False
        note = None
        if pid == "nvidia_nim_free":
            note = f"observed baseline {NIM_KNOWN_BASELINE_RPM} RPM not guaranteed; measure live"
        elif pid == "google_ai_studio_free":
            note = "inspect active project-level RPM/TPM/RPD limits in AI Studio"
        elif pid == "selfhost_recovered_node":
            note = "bounded by recovered hardware and energy/OZE ledger"
        entries.append({
            "provider": pid,
            "model": (p.get("candidate_models") or ["unknown"])[0],
            "source": source,
            "checked_at": _now_iso(),
            "status": SNAPSHOT_STATUS_STALE,
            "rpm": None,
            "tpm": None,
            "rpd": None,
            "guaranteed": guaranteed,
            "note": note,
        })
    return {
        "generated_at": _now_iso(),
        "source": source,
        "platform": "hermes_pilot",
        "entries": entries,
    }


def validate_snapshot(snapshot: dict) -> list[str]:
    errors: list[str] = []
    entries = snapshot.get("entries")
    if not isinstance(entries, list) or not entries:
        return ["snapshot.entries must be a non-empty list"]
    for i, e in enumerate(entries):
        if not isinstance(e, dict):
            errors.append(f"entries[{i}] must be object")
            continue
        missing = REQ_SNAPSHOT_FIELDS - set(e.keys())
        if missing:
            errors.append(f"entries[{i}] missing fields: {sorted(missing)}")
            continue
        for f in ("provider", "model", "source", "checked_at"):
            if not _is_nonempty_str(e.get(f)):
                errors.append(f"entries[{i}].{f} empty")
        if e.get("status") not in (SNAPSHOT_STATUS_OK, SNAPSHOT_STATUS_STALE, SNAPSHOT_STATUS_MISSING):
            errors.append(f"entries[{i}].status must be ok/stale/missing; got {e.get('status')!r}")
        # Specific: NIM cannot be declared guaranteed=true.
        if e.get("provider") == "nvidia_nim_free" and e.get("guaranteed") is True:
            errors.append(
                f"entries[{i}]: nvidia_nim_free guaranteed=true rejected - 40 RPM baseline is not guaranteed"
            )
        # Specific: google_ai_studio_free requires checked_at fresh + note referencing project limits.
        if e.get("provider") == "google_ai_studio_free":
            note = (e.get("note") or "").lower()
            if "ai studio" not in note and "project" not in note:
                errors.append(
                    f"entries[{i}]: google_ai_studio_free requires note referencing AI Studio / project-level limits"
                )
    return errors


def is_chain_blocked(snapshot: dict | None) -> bool:
    """Agent chain is blocked if there is no snapshot or any entry is missing/stale."""
    if not isinstance(snapshot, dict):
        return True
    entries = snapshot.get("entries")
    if not isinstance(entries, list) or not entries:
        return True
    if validate_snapshot(snapshot):
        return True
    for e in entries:
        if not isinstance(e, dict):
            return True
        if e.get("status") != SNAPSHOT_STATUS_OK:
            return True
    return False


def block_decision(snapshot: dict | None) -> dict:
    blocked = is_chain_blocked(snapshot)
    reason = "ok"
    if blocked:
        if snapshot is None or not isinstance(snapshot, dict) or not snapshot.get("entries"):
            reason = "missing_snapshot"
        elif validate_snapshot(snapshot):
            reason = "invalid_snapshot"
        else:
            reason = "stale_or_missing_quota"
    return {"blocked": blocked, "reason": reason}


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--matrix", type=Path, default=DEFAULT_MATRIX)
    parser.add_argument("--out", type=Path, default=DEFAULT_SNAPSHOT_OUT)
    parser.add_argument("--source", default="manual")
    parser.add_argument("--block-check", action="store_true",
                        help="Only print block decision JSON and exit")
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.block_check:
        snapshot = None
        if args.out.exists():
            try:
                snapshot = json.loads(args.out.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                snapshot = None
        decision = block_decision(snapshot)
        print(json.dumps(decision, indent=2, ensure_ascii=False))
        return 1 if decision["blocked"] else 0

    matrix = json.loads(args.matrix.read_text(encoding="utf-8"))
    snapshot = snapshot_from_matrix(matrix, source=args.source)
    args.out.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    errors = validate_snapshot(snapshot)
    if errors:
        for e in errors:
            print(f"ERROR: {e}")
        return 2
    blocked = is_chain_blocked(snapshot)
    status = "BLOCKED (stale entries need operator fill)" if blocked else "OK"
    print(f"OK snapshot written: {args.out} | chain decision: {status}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
