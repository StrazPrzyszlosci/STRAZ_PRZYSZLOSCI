#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
PROJECT_DIR = Path(__file__).resolve().parents[1]
PACK_ID = "pack-project13-kaggle-enrichment-01"
PACK_DIR = PROJECT_DIR / "execution_packs" / PACK_ID
DRY_RUN_DIR = PACK_DIR / "dry_runs"
SUMMARY_SCRIPT = PROJECT_DIR / "scripts" / "summarize_kaggle_run.py"
RECORDS_SCRIPT = PROJECT_DIR / "scripts" / "create_execution_records.py"
REBUILD_SCRIPT = PROJECT_DIR / "scripts" / "rebuild_autonomous_outputs.py"
BASE_DIR = PROJECT_DIR / "autonomous_test"
NOTEBOOK_PATH = PROJECT_DIR / "youtube-databaseparts.ipynb"
MANIFEST_PATH = PACK_DIR / "manifest.json"
RUNBOOK_PATH = PACK_DIR / "RUNBOOK.md"
PR_TEMPLATE_PATH = PACK_DIR / "PR_TEMPLATE.md"
REVIEW_CHECKLIST_PATH = PACK_DIR / "REVIEW_CHECKLIST.md"


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
    rows = path.read_text(encoding="utf-8").splitlines()
    return max(len(rows) - 1, 0)


def add_check(checks: list[dict], name: str, status: str, details: str) -> None:
    checks.append({"name": name, "status": status, "details": details})


def build_pr_preview(template_text: str, run_stamp: str, summary_path: Path) -> str:
    preview = template_text
    replacements = {
        "run_id": f"run-project13-kaggle-enrichment-dry-run-local-{run_stamp}",
        "fork_owner": "dry-run-local",
        "branch_name": f"dry-run-pack-project13-{run_stamp}",
        "kaggle_run_timestamp_utc": utc_now().replace(microsecond=0).isoformat(),
        "kaggle_notebook_url_or_id": f"dry-run://project13/local/{run_stamp}",
        "liczba nowych rekordow": "0 w dry-run local validation",
        "liczba przetworzonych filmow": "na podstawie istniejacego snapshotu artifactow",
        "nowe lub istotne modele urzadzen": "zobacz dry-run report i summary",
        "nowe lub istotne part numbers": "zobacz dry-run report i summary",
    }

    for key, value in replacements.items():
        preview = preview.replace(f"- `{key}`:", f"- `{key}`: {value}")

    preview += (
        "\n## Dry Run Notes\n\n"
        f"- summary_report: `{summary_path.relative_to(REPO_ROOT)}`\n"
        "- Ten plik jest tylko szkicem PR do lokalnego testu execution packa.\n"
    )
    return preview


def render_report(
    checks: list[dict],
    *,
    run_stamp: str,
    summary_path: Path,
    pr_preview_path: Path,
    manifest: dict,
) -> str:
    failures = [item for item in checks if item["status"] == "fail"]
    warnings = [item for item in checks if item["status"] == "warn"]
    overall = "pass"
    if failures:
        overall = "needs_changes"
    elif warnings:
        overall = "conditional"

    lines = [
        "# Dry Run Report Dla Pack Project13 Kaggle Enrichment 01",
        "",
        f"- executed_at_utc: {utc_now().replace(microsecond=0).isoformat()}",
        f"- run_mode: local_dry_run",
        f"- overall_status: {overall}",
        f"- pack_id: {manifest['pack_id']}",
        f"- scope: {manifest['scope']}",
        f"- summary_report: {summary_path.relative_to(REPO_ROOT)}",
        f"- pr_preview: {pr_preview_path.relative_to(REPO_ROOT)}",
        "",
        "## Checks",
        "",
    ]

    for item in checks:
        lines.append(f"- [{item['status']}] {item['name']}: {item['details']}")

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- Status `pass` oznacza, ze lokalny kontrakt packa jest spiety i snapshot ma komplet wymaganych artefaktow review-ready.",
            "- Dry-run weryfikuje lokalnie kontrakt packa, provenance, artefakty i gotowosc dokumentacyjna bez uruchamiania prawdziwego Kaggle runu ani prawdziwego PR.",
            "- Status `conditional` oznacza, ze pack jest logicznie spiety, ale nadal sa luki przed publicznym przebiegiem.",
            "- Status `needs_changes` oznacza, ze przed publicznym dry-runem wolontariusza trzeba poprawic przynajmniej jeden blokujacy element.",
        ]
    )

    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Wykonuje lokalny dry-run execution packa Project 13.")
    parser.add_argument("--base-dir", type=Path, default=BASE_DIR)
    parser.add_argument("--fork-owner", default="dry-run-local")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_stamp = utc_now().strftime("%Y%m%dT%H%M%SZ")
    branch_name = f"dry-run-pack-project13-{run_stamp}"
    run_ref = f"dry-run://project13/local/{run_stamp}"

    DRY_RUN_DIR.mkdir(parents=True, exist_ok=True)
    summary_path = DRY_RUN_DIR / f"summary_{run_stamp}.md"
    pr_preview_path = DRY_RUN_DIR / f"pr_preview_{run_stamp}.md"
    report_path = DRY_RUN_DIR / f"dry_run_report_{run_stamp}.md"

    subprocess.run(
        ["python3", str(REBUILD_SCRIPT)],
        check=True,
        cwd=REPO_ROOT,
    )

    subprocess.run(
        [
            "python3",
            str(SUMMARY_SCRIPT),
            "--base-dir",
            str(args.base_dir),
            "--output",
            str(summary_path),
            "--pack-id",
            PACK_ID,
            "--notebook-path",
            str(NOTEBOOK_PATH.relative_to(REPO_ROOT)),
            "--fork-owner",
            args.fork_owner,
            "--branch-name",
            branch_name,
            "--run-ref",
            run_ref,
        ],
        check=True,
        cwd=REPO_ROOT,
    )

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    template_text = PR_TEMPLATE_PATH.read_text(encoding="utf-8")
    pr_preview_path.write_text(build_pr_preview(template_text, run_stamp, summary_path), encoding="utf-8")

    checks: list[dict] = []
    add_check(checks, "manifest_json", "pass", "Manifest istnieje i parsuje sie poprawnie.")
    for label, path in [
        ("runbook", RUNBOOK_PATH),
        ("pr_template", PR_TEMPLATE_PATH),
        ("review_checklist", REVIEW_CHECKLIST_PATH),
        ("notebook", NOTEBOOK_PATH),
    ]:
        add_check(
            checks,
            f"required_file::{label}",
            "pass" if path.exists() else "fail",
            f"{path.relative_to(REPO_ROOT)}",
        )

    notebook_text = NOTEBOOK_PATH.read_text(encoding="utf-8")
    notebook_markers = {
        "fork_owner_placeholder": "FORK_OWNER = \\\"TWOJ_LOGIN_GITHUB\\\"" in notebook_text,
        "noreply_identity": "@users.noreply.github.com" in notebook_text,
        "finalizer_script": "finalize_execution_pack_run.py" in notebook_text,
        "finalizer_push_mode": "--git-mode" in notebook_text and "\\\"push\\\"" in notebook_text,
        "finalizer_run_metadata": "run_record_ref" in notebook_text and "run_id" in notebook_text,
        "inventree_bootstrap": "INVENTREE_FILE.touch(exist_ok=True)" in notebook_text,
    }
    for marker_name, marker_ok in notebook_markers.items():
        add_check(
            checks,
            f"notebook::{marker_name}",
            "pass" if marker_ok else "fail",
            "Statyczna kontrola notebooka pod workflow packa.",
        )

    for relative_output in manifest["output_paths"]:
        output_path = REPO_ROOT / relative_output
        exists = output_path.exists()
        status = "pass" if exists else "fail"
        details = f"{relative_output}"
        count = None
        if exists and output_path.suffix == ".jsonl":
            count = count_jsonl(output_path)
            details += f" | records={count}"
        elif exists and output_path.suffix == ".csv":
            count = count_csv_rows(output_path)
            details += f" | rows={count}"

        if not exists and output_path.name == "inventree_import.jsonl" and notebook_markers["inventree_bootstrap"]:
            status = "warn"
            details += " | brak w obecnym snapshotcie, ale notebook bootstrapuje pusty plik przy nowym runie"
        elif (
            exists
            and count == 0
            and output_path.suffix in {".jsonl", ".csv"}
            and output_path.name != "rebuild_autonomous_outputs_skipped.jsonl"
        ):
            status = "warn"
            details += " | plik istnieje, ale jest pusty po obecnym snapshotcie"

        add_check(checks, f"output::{output_path.name}", status, details)

    summary_text = summary_path.read_text(encoding="utf-8")
    provenance_ok = all(
        token in summary_text
        for token in [
            f"pack_id: {PACK_ID}",
            f"notebook_path: {NOTEBOOK_PATH.relative_to(REPO_ROOT)}",
            f"branch_name: {branch_name}",
            f"run_ref: {run_ref}",
        ]
    )
    add_check(
        checks,
        "summary::provenance",
        "pass" if provenance_ok else "fail",
        f"{summary_path.relative_to(REPO_ROOT)}",
    )

    template_sections_ok = all(
        token in pr_preview_path.read_text(encoding="utf-8")
        for token in ["## Run Provenance", "## Known Issues", "## Integrity Notes", "## Dry Run Notes"]
    )
    add_check(
        checks,
        "pr_preview::sections",
        "pass" if template_sections_ok else "fail",
        f"{pr_preview_path.relative_to(REPO_ROOT)}",
    )

    report_text = render_report(
        checks,
        run_stamp=run_stamp,
        summary_path=summary_path,
        pr_preview_path=pr_preview_path,
        manifest=manifest,
    )
    report_path.write_text(report_text, encoding="utf-8")

    failures = [item for item in checks if item["status"] == "fail"]
    warnings = [item for item in checks if item["status"] == "warn"]
    run_status = "succeeded"
    if failures:
        run_status = "failed"
    elif warnings:
        run_status = "needs_review"

    records_command = [
        "python3",
        str(RECORDS_SCRIPT),
        "--fork-owner",
        args.fork_owner,
        "--run-ref",
        run_ref,
        "--summary-ref",
        str(report_path.relative_to(REPO_ROOT)),
        "--output-ref",
        str(pr_preview_path.relative_to(REPO_ROOT)),
        "--operator-kind",
        "local_agent",
        "--environment-kind",
        "local",
        "--run-status",
        run_status,
        "--timestamp-slug",
        run_stamp,
        "--artifact-storage-ref",
        str(report_path.relative_to(REPO_ROOT)),
        "--artifact-kind",
        "report",
        "--artifact-title",
        "Dry-run report dla execution packa Project 13",
        "--artifact-summary",
        f"Lokalny dry-run packa {PACK_ID} zakonczyl sie statusem {run_status}.",
        "--artifact-review-status",
        "draft",
    ]
    subprocess.run(records_command, check=True, cwd=REPO_ROOT)

    print(
        json.dumps(
            {
                "status": "ok",
                "dry_run_report": str(report_path),
                "summary_report": str(summary_path),
                "pr_preview": str(pr_preview_path),
                "run_status": run_status,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
