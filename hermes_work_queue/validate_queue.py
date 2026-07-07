#!/usr/bin/env python3
"""Validate Hermes first work queue (T18, dawniej H3).

Kazdy job ma input, output, model_route, artifact_requirements i human_control_point.
Zaden job nie moze auto-merge ani direct push. Brak ktoregokolwiek blokuje.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_QUEUE = ROOT / "hermes_work_queue" / "seed_queue.json"

JOB_IDS = {
    "repo_scout_daily",
    "handoff_builder_after_commit",
    "resource_scout_triage",
    "execution_pack_draft_generator",
    "audit_reviewer_before_pr",
}
ARTIFACT_PROTO = {
    "run_receipt.json", "model_route.json", "quota_snapshot.json",
    "git_diff.patch", "handoff_or_pr.md",
}


def _is_nonempty_str(v: Any) -> bool:
    return isinstance(v, str) and len(v) > 0


def _is_nonempty_list(v: Any) -> bool:
    return isinstance(v, list) and len(v) > 0


def validate_queue(payload: dict) -> list[str]:
    errors: list[str] = []
    jobs = payload.get("jobs")
    if not _is_nonempty_list(jobs):
        return ["jobs must be a non-empty list"]
    if not _is_nonempty_str(payload.get("queue_id")):
        errors.append("queue_id required")
    if not _is_nonempty_str(payload.get("platform")):
        errors.append("platform required")
    seen_ids: set[str] = set()
    for i, job in enumerate(jobs):
        if not isinstance(job, dict):
            errors.append(f"jobs[{i}] must be object")
            continue
        job_id = job.get("job_id", "<unknown>")
        if job_id not in JOB_IDS:
            errors.append(f"jobs[{i}].job_id must be one of {sorted(JOB_IDS)}; got {job_id!r}")
        if job_id in seen_ids:
            errors.append(f"jobs[{i}]: duplicate job_id {job_id}")
        seen_ids.add(job_id)
        if not _is_nonempty_str(job.get("purpose")) or len(job.get("purpose", "")) < 10:
            errors.append(f"jobs[{i}].purpose must be >=10 chars")
        if not _is_nonempty_list(job.get("inputs")):
            errors.append(f"jobs[{i}].inputs must be non-empty list")
        if not _is_nonempty_list(job.get("outputs")):
            errors.append(f"jobs[{i}].outputs must be non-empty list")
        mr = job.get("model_route", {})
        if not isinstance(mr, dict) or not _is_nonempty_str(mr.get("default_profile")):
            errors.append(f"jobs[{i}].model_route.default_profile required")
        arts = job.get("artifact_requirements", [])
        if not _is_nonempty_list(arts):
            errors.append(f"jobs[{i}].artifact_requirements must be non-empty list")
        elif not set(arts).issubset(ARTIFACT_PROTO):
            errors.append(
                f"jobs[{i}].artifact_requirements must be subset of {sorted(ARTIFACT_PROTO)}"
            )
        if not _is_nonempty_str(job.get("human_control_point")) or len(job.get("human_control_point", "")) < 5:
            errors.append(f"jobs[{i}].human_control_point must be >=5 chars")
        if job.get("no_auto_merge") is not True:
            errors.append(f"jobs[{i}].no_auto_merge must be true (Hermes cannot auto-merge)")
        if job.get("no_direct_push") is not True:
            errors.append(f"jobs[{i}].no_direct_push must be true (Hermes cannot direct push main)")
        if job.get("next_disabled") is False:
            errors.append(
                f"jobs[{i}].next_disabled must be true (Hermes jobs are staged, not auto-chained)"
            )
    return errors


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path, nargs="?", default=DEFAULT_QUEUE)
    args = parser.parse_args(list(argv) if argv is not None else None)
    errors = validate_queue(json.loads(args.path.read_text(encoding="utf-8")))
    if errors:
        for e in errors:
            print(f"ERROR: {e}")
        return 1
    print(f"OK: hermes work queue valid: {args.path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
