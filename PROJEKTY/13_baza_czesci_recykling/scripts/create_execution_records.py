#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_PACK_ID = "pack-project13-kaggle-enrichment-01"
DEFAULT_TASK_ID = "task-project13-kaggle-enrichment-01"
DEFAULT_OUTPUT_DIR = (
    Path(__file__).resolve().parents[1]
    / "execution_packs"
    / DEFAULT_PACK_ID
    / "records"
)


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_run_record(args: argparse.Namespace, timestamp_slug: str) -> tuple[str, dict]:
    run_id = f"run-project13-kaggle-enrichment-{slugify(args.fork_owner)}-{timestamp_slug}"
    output_refs = [args.summary_ref]
    if args.output_ref:
        output_refs.append(args.output_ref)

    payload = {
        "schema_version": "v1",
        "run_id": run_id,
        "task_id": args.task_id,
        "pack_id": args.pack_id,
        "operator_kind": args.operator_kind,
        "environment_kind": args.environment_kind,
        "status": args.run_status,
        "logs_ref": args.run_ref,
        "output_refs": output_refs,
        "started_at": args.started_at or utc_now(),
        "ended_at": args.ended_at or utc_now(),
    }
    return run_id, payload


def build_artifact_record(args: argparse.Namespace, run_id: str, timestamp_slug: str) -> tuple[str, dict]:
    artifact_id = f"artifact-project13-kaggle-enrichment-{slugify(args.fork_owner)}-{timestamp_slug}"
    payload = {
        "schema_version": "v1",
        "artifact_id": artifact_id,
        "run_id": run_id,
        "artifact_kind": args.artifact_kind,
        "title": args.artifact_title,
        "summary": args.artifact_summary,
        "storage_ref": args.artifact_storage_ref,
        "review_status": args.artifact_review_status,
        "provenance": [
            {
                "entity_kind": "execution_pack",
                "entity_id": args.pack_id,
            },
            {
                "entity_kind": "run",
                "entity_id": run_id,
            },
        ],
        "created_at": utc_now(),
        "updated_at": utc_now(),
    }
    return artifact_id, payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Tworzy kanoniczne rekordy Run oraz opcjonalnie Artifact dla execution packa Project 13."
    )
    parser.add_argument("--pack-id", default=DEFAULT_PACK_ID)
    parser.add_argument("--task-id", default=DEFAULT_TASK_ID)
    parser.add_argument("--fork-owner", required=True)
    parser.add_argument("--existing-run-id", help="Jesli podane, skrypt nie tworzy nowego Run i dopina tylko Artifact do istniejacego run_id.")
    parser.add_argument("--run-ref", help="Identyfikator albo URL runu Kaggle.")
    parser.add_argument("--summary-ref", help="Sciezka albo URL do raportu runu.")
    parser.add_argument("--output-ref", help="Dodatkowy output, np. branch lub katalog artefaktow.")
    parser.add_argument("--operator-kind", default="hybrid_team")
    parser.add_argument("--environment-kind", default="kaggle")
    parser.add_argument("--run-status", default="needs_review")
    parser.add_argument("--started-at")
    parser.add_argument("--ended-at")
    parser.add_argument("--timestamp-slug", help="Wymusza wspolny znacznik czasu dla nazw rekordow, np. 20260422T185605Z.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--artifact-storage-ref", help="URL do PR albo innego artefaktu.")
    parser.add_argument("--artifact-kind", default="pull_request")
    parser.add_argument(
        "--artifact-title",
        default="PR z artefaktami Project 13 po uruchomieniu KaggleNotebookPack",
    )
    parser.add_argument(
        "--artifact-summary",
        default="Artefakt zawiera provenance do packa, runu i raportu przebiegu.",
    )
    parser.add_argument("--artifact-review-status", default="review_ready")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    timestamp_slug = args.timestamp_slug or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    result = {
        "status": "ok",
    }
    run_id = args.existing_run_id

    if not run_id:
        if not args.run_ref or not args.summary_ref:
            raise SystemExit("--run-ref i --summary-ref sa wymagane, jesli nie podano --existing-run-id.")

        run_id, run_payload = build_run_record(args, timestamp_slug)
        run_path = args.output_dir / f"{run_id}.json"
        write_json(run_path, run_payload)
        result["run_record"] = str(run_path)
    elif not args.artifact_storage_ref:
        raise SystemExit("--artifact-storage-ref jest wymagane, jesli uzywasz --existing-run-id bez tworzenia nowego Run.")

    if args.artifact_storage_ref:
        artifact_id, artifact_payload = build_artifact_record(args, run_id, timestamp_slug)
        artifact_path = args.output_dir / f"{artifact_id}.json"
        write_json(artifact_path, artifact_payload)
        result["artifact_record"] = str(artifact_path)

    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
