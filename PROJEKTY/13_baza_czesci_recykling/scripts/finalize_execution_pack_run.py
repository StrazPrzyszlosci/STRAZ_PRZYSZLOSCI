#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PACK_ID = "pack-project13-kaggle-enrichment-01"
TASK_ID = "task-project13-kaggle-enrichment-01"
PROJECT_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
BASE_DIR = PROJECT_DIR / "autonomous_test"
NOTEBOOK_PATH = PROJECT_DIR / "youtube-databaseparts.ipynb"
MANIFEST_PATH = PROJECT_DIR / "execution_packs" / PACK_ID / "manifest.json"
SUMMARY_OUTPUT = BASE_DIR / "reports" / "last_run_summary.md"
REBUILD_SCRIPT = PROJECT_DIR / "scripts" / "rebuild_autonomous_outputs.py"
SUMMARY_SCRIPT = PROJECT_DIR / "scripts" / "summarize_kaggle_run.py"
RECORDS_SCRIPT = PROJECT_DIR / "scripts" / "create_execution_records.py"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def count_jsonl(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open(encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())


def count_csv_rows(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.reader(handle))
    return max(len(rows) - 1, 0)


def relative_to_repo(path: Path) -> str:
    return str(path.resolve().relative_to(REPO_ROOT))


def run_json_command(command: list[str], *, cwd: Path) -> dict[str, Any]:
    result = subprocess.run(
        command,
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )
    stdout = result.stdout.strip().splitlines()
    if not stdout:
        return {}
    return json.loads(stdout[-1])


def load_manifest() -> dict[str, Any]:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def validate_manifest_outputs(manifest: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    output_info: list[dict[str, Any]] = []
    missing_outputs: list[str] = []

    for relative_output in manifest["output_paths"]:
        output_path = REPO_ROOT / relative_output
        count = None
        if output_path.exists() and output_path.suffix == ".jsonl":
            count = count_jsonl(output_path)
        elif output_path.exists() and output_path.suffix == ".csv":
            count = count_csv_rows(output_path)

        output_info.append(
            {
                "path": relative_output,
                "exists": output_path.exists(),
                "count": count,
            }
        )
        if not output_path.exists():
            missing_outputs.append(relative_output)

    return output_info, missing_outputs


def stage_paths(repo_dir: Path, relative_paths: list[str]) -> None:
    for relative_path in relative_paths:
        absolute_path = repo_dir / relative_path
        if absolute_path.exists():
            subprocess.run(["git", "-C", str(repo_dir), "add", "-f", relative_path], check=True)


def sanitize_branch_stamp(timestamp_slug: str) -> str:
    return timestamp_slug.replace("T", "-").removesuffix("Z")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Finalizuje realny run execution packa Project 13: rebuild, summary, Run record, git add/commit/push."
    )
    parser.add_argument("--fork-owner", required=True)
    parser.add_argument("--pack-id", default=PACK_ID)
    parser.add_argument("--task-id", default=TASK_ID)
    parser.add_argument("--repo-dir", type=Path, default=REPO_ROOT)
    parser.add_argument("--base-dir", type=Path, default=BASE_DIR)
    parser.add_argument("--summary-output", type=Path, default=SUMMARY_OUTPUT)
    parser.add_argument("--timestamp-slug", help="Kanoniczny znacznik czasu, np. 20260422T185605Z.")
    parser.add_argument("--branch-name")
    parser.add_argument("--run-ref")
    parser.add_argument("--operator-kind", default="hybrid_team")
    parser.add_argument("--environment-kind", default="kaggle")
    parser.add_argument("--run-status", default="needs_review")
    parser.add_argument("--artifact-storage-ref", help="Jesli PR juz istnieje, mozna od razu zapisac tez Artifact record.")
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
    parser.add_argument(
        "--git-mode",
        choices=["none", "stage", "commit", "push"],
        default="stage",
        help="Jak daleko doprowadzic zmiany gitowe po finalizacji runu.",
    )
    parser.add_argument("--commit-message")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_dir = args.repo_dir.resolve()
    base_dir = args.base_dir.resolve()
    summary_output = args.summary_output.resolve()
    started_at = utc_now().replace(microsecond=0).isoformat()

    timestamp_slug = args.timestamp_slug or utc_now().strftime("%Y%m%dT%H%M%SZ")
    branch_name = args.branch_name or f"pack-project13-kaggle-enrichment-{sanitize_branch_stamp(timestamp_slug)}"
    run_ref = args.run_ref or f"kaggle://project13/{timestamp_slug}"
    branch_ref = f"branch://{args.fork_owner}/{branch_name}"

    run_json_command(["python3", str(REBUILD_SCRIPT)], cwd=repo_dir)
    run_json_command(
        [
            "python3",
            str(SUMMARY_SCRIPT),
            "--base-dir",
            str(base_dir),
            "--output",
            str(summary_output),
            "--pack-id",
            args.pack_id,
            "--notebook-path",
            relative_to_repo(NOTEBOOK_PATH),
            "--fork-owner",
            args.fork_owner,
            "--branch-name",
            branch_name,
            "--run-ref",
            run_ref,
        ],
        cwd=repo_dir,
    )

    manifest = load_manifest()
    output_info, missing_outputs = validate_manifest_outputs(manifest)
    if missing_outputs:
        raise SystemExit(
            "Brakuje wymaganych outputow z manifestu: " + ", ".join(missing_outputs)
        )

    ended_at = utc_now().replace(microsecond=0).isoformat()
    records_command = [
        "python3",
        str(RECORDS_SCRIPT),
        "--pack-id",
        args.pack_id,
        "--task-id",
        args.task_id,
        "--fork-owner",
        args.fork_owner,
        "--run-ref",
        run_ref,
        "--summary-ref",
        relative_to_repo(summary_output),
        "--output-ref",
        branch_ref,
        "--operator-kind",
        args.operator_kind,
        "--environment-kind",
        args.environment_kind,
        "--run-status",
        args.run_status,
        "--started-at",
        started_at,
        "--ended-at",
        ended_at,
        "--timestamp-slug",
        timestamp_slug,
    ]
    if args.artifact_storage_ref:
        records_command.extend(
            [
                "--artifact-storage-ref",
                args.artifact_storage_ref,
                "--artifact-kind",
                args.artifact_kind,
                "--artifact-title",
                args.artifact_title,
                "--artifact-summary",
                args.artifact_summary,
                "--artifact-review-status",
                args.artifact_review_status,
            ]
        )

    records_result = run_json_command(records_command, cwd=repo_dir)
    run_record_path = Path(records_result["run_record"])
    artifact_record_path = Path(records_result["artifact_record"]) if records_result.get("artifact_record") else None
    run_record_payload = json.loads(run_record_path.read_text(encoding="utf-8"))
    run_id = run_record_payload["run_id"]

    staged_paths = list(manifest["output_paths"])
    staged_paths.append(relative_to_repo(run_record_path))
    if artifact_record_path is not None:
        staged_paths.append(relative_to_repo(artifact_record_path))

    committed = False
    pushed = False
    if args.git_mode != "none":
        subprocess.run(["git", "-C", str(repo_dir), "checkout", "-B", branch_name], check=True)
        stage_paths(repo_dir, staged_paths)
        staged_changes = subprocess.run(["git", "-C", str(repo_dir), "diff", "--cached", "--quiet"])

        if staged_changes.returncode != 0 and args.git_mode in {"commit", "push"}:
            commit_message = args.commit_message or f"Project13 Kaggle pack run {timestamp_slug}"
            subprocess.run(["git", "-C", str(repo_dir), "commit", "-m", commit_message], check=True)
            committed = True

        if committed and args.git_mode == "push":
            subprocess.run(["git", "-C", str(repo_dir), "push", "--set-upstream", "origin", branch_name], check=True)
            pushed = True

    artifact_follow_up_command = None
    if not args.artifact_storage_ref:
        artifact_follow_up_command = (
            "python3 PROJEKTY/13_baza_czesci_recykling/scripts/create_execution_records.py "
            f"--fork-owner {args.fork_owner} "
            f"--existing-run-id {run_id} "
            f"--timestamp-slug {timestamp_slug} "
            "--artifact-storage-ref https://github.com/StrazPrzyszlosci/STRAZ_PRZYSZLOSCI/pull/<numer>"
        )

    result = {
        "status": "ok",
        "pack_id": args.pack_id,
        "branch_name": branch_name,
        "branch_ref": branch_ref,
        "run_ref": run_ref,
        "run_id": run_id,
        "summary_ref": relative_to_repo(summary_output),
        "run_record_ref": relative_to_repo(run_record_path),
        "artifact_record_ref": relative_to_repo(artifact_record_path) if artifact_record_path else None,
        "git_mode": args.git_mode,
        "committed": committed,
        "pushed": pushed,
        "output_info": output_info,
        "artifact_follow_up_command": artifact_follow_up_command,
    }
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
