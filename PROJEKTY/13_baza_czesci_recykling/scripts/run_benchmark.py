#!/usr/bin/env python3
"""Benchmark comparison runner for Project 13.

Compares extraction quality of different prompts/models/workflows
against a fixed test sample with ground-truth labels.

Usage:
    python3 scripts/run_benchmark.py init-sample
    python3 scripts/run_benchmark.py validate-sample
    python3 scripts/run_benchmark.py list-variants
    python3 scripts/run_benchmark.py run --variant <name>
    python3 scripts/run_benchmark.py compare
    python3 scripts/run_benchmark.py report
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BENCHMARK_DIR = PROJECT_ROOT / "autonomous_test" / "benchmarks"
TEST_DB_PATH = PROJECT_ROOT / "autonomous_test" / "results" / "test_db.jsonl"

SAMPLE_PATH = BENCHMARK_DIR / "benchmark_sample.jsonl"
METRICS_PATH = BENCHMARK_DIR / "benchmark_metrics.json"
REPORT_PATH = BENCHMARK_DIR / "benchmark_report.md"
VARIANTS_DIR = BENCHMARK_DIR / "variants"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        records.append(json.loads(line))
    return records


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "\n".join(
            json.dumps(row, ensure_ascii=False, separators=(",", ":")) for row in rows
        )
        + "\n",
        encoding="utf-8",
    )


def write_json(path: Path, data: dict[str, Any] | list[dict[str, Any]]) -> None:
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


GROUND_TRUTH_CONTRACT: dict[str, Any] = {
    "sample_id": "bench-sample-v1",
    "description": "Ground-truth contract for benchmark sample. Each record has 'ground_truth' field with 'is_valid_part' boolean indicating whether the extraction is a real, reusable electronic part.",
    "criteria": {
        "is_valid_part_true": "Extraction identifies a real, specific electronic component with a valid or plausible MPN (manufacturer part number). Designators, board IDs, and generic descriptions without a specific part are NOT valid.",
        "is_valid_part_false": "Extraction is a false positive: board model, designator list, generic label, OCR artifact (e.g., 'WARSZTAT AUTOMATYKI'), date code, or text that does not identify a specific reusable component.",
    },
    "note": "This contract is used by init-sample to pre-populate ground_truth.is_valid_part. Human review is required to finalize labels before running benchmarks.",
}


def init_sample() -> int:
    BENCHMARK_DIR.mkdir(parents=True, exist_ok=True)
    VARIANTS_DIR.mkdir(parents=True, exist_ok=True)

    if SAMPLE_PATH.exists():
        print(f"Sample already exists: {SAMPLE_PATH}")
        print("Delete it manually to regenerate, or run 'validate-sample' to check.")
        return 0

    test_db = read_jsonl(TEST_DB_PATH)
    if not test_db:
        print(f"No records found in {TEST_DB_PATH}")
        return 1

    sample_records: list[dict[str, Any]] = []
    for idx, raw in enumerate(test_db):
        part_number = raw.get("part_number", "")
        verification = raw.get("verification", {})
        verified = verification.get("verified", False)
        observed_text = verification.get("observed_text", "")

        is_ocr_artifact = any(
            marker in observed_text
            for marker in ["Błąd API", "Błąd wycinania", "BRAK", "WARSZTAT"]
        )
        is_designator_only = (
            bool(part_number)
            and all(c in part_number for c in "R0123456789, C V")
            and len(part_number.split(",")) > 3
        )

        if is_ocr_artifact:
            guessed_valid = False
        elif is_designator_only:
            guessed_valid = False
        elif verified and not is_ocr_artifact:
            guessed_valid = True
        else:
            guessed_valid = False

        sample_records.append(
            {
                "sample_id": f"bench-v1-{idx:04d}",
                "source_record": raw,
                "ground_truth": {
                    "is_valid_part": guessed_valid,
                    "label_pending_review": True,
                    "reviewer_notes": "",
                },
            }
        )

    write_jsonl(SAMPLE_PATH, sample_records)
    print(f"Initialized sample with {len(sample_records)} records -> {SAMPLE_PATH}")
    print()
    print("IMPORTANT: ground_truth.is_valid_part values are HEURISTIC guesses.")
    print("Human review is required before running benchmarks.")
    print("Run 'validate-sample' to check which records still need review.")
    return 0


def validate_sample() -> int:
    if not SAMPLE_PATH.exists():
        print(f"Sample not found: {SAMPLE_PATH}")
        print("Run 'init-sample' first.")
        return 1

    records = read_jsonl(SAMPLE_PATH)
    total = len(records)
    pending = sum(
        1
        for r in records
        if r.get("ground_truth", {}).get("label_pending_review", True)
    )
    valid = sum(
        1 for r in records if r.get("ground_truth", {}).get("is_valid_part", False)
    )
    invalid = total - valid

    print(f"Sample: {SAMPLE_PATH}")
    print(f"Total records: {total}")
    print(f"Valid parts (is_valid_part=true): {valid}")
    print(f"Invalid parts (is_valid_part=false): {invalid}")
    print(f"Pending human review: {pending}")

    if pending > 0:
        print()
        print(f"WARNING: {pending} records still have label_pending_review=true.")
        print("Finalize ground-truth labels before running benchmarks.")
        return 1

    print()
    print("All ground-truth labels are finalized. Sample is ready for benchmarking.")
    return 0


def list_variants() -> int:
    if not VARIANTS_DIR.exists():
        print("No variants directory found. Run 'init-sample' first.")
        return 1

    variant_files = sorted(VARIANTS_DIR.glob("*.json"))
    if not variant_files:
        print("No variant configurations found in variants/ directory.")
        print()
        print("Create a variant config file, e.g.:")
        print(f"  {VARIANTS_DIR}/prompt-v1-gemini-flash.json")
        print()
        print("Example variant config:")
        example = {
            "variant_id": "prompt-v1-gemini-flash",
            "description": "Original extraction prompt with Gemini Flash",
            "model": "gemini-2.0-flash",
            "prompt_template": "v1",
            "parameters": {"temperature": 0.1, "top_p": 0.95},
            "cost_per_1k_tokens_input": 0.000075,
            "cost_per_1k_tokens_output": 0.00030,
        }
        print(json.dumps(example, indent=2, ensure_ascii=False))
        return 0

    print(f"Found {len(variant_files)} variant(s):")
    for vf in variant_files:
        try:
            cfg = json.loads(vf.read_text(encoding="utf-8"))
            print(f"  {vf.name}: {cfg.get('description', '(no description)')}")
        except json.JSONDecodeError:
            print(f"  {vf.name}: INVALID JSON")
    return 0


def run_variant(variant_name: str) -> int:
    variant_path = VARIANTS_DIR / f"{variant_name}.json"
    if not variant_path.exists():
        print(f"Variant config not found: {variant_path}")
        print("Run 'list-variants' to see available variants.")
        return 1

    if not SAMPLE_PATH.exists():
        print(f"Sample not found: {SAMPLE_PATH}")
        print("Run 'init-sample' first.")
        return 1

    variant_cfg = json.loads(variant_path.read_text(encoding="utf-8"))
    sample_records = read_jsonl(SAMPLE_PATH)

    pending = sum(
        1
        for r in sample_records
        if r.get("ground_truth", {}).get("label_pending_review", True)
    )
    if pending > 0:
        print(f"WARNING: {pending} sample records still need human review.")
        print("Finalize ground-truth labels before running benchmarks.")
        return 1

    print(f"Running variant: {variant_name}")
    print(f"  model: {variant_cfg.get('model', 'N/A')}")
    print(f"  prompt: {variant_cfg.get('prompt_template', 'N/A')}")
    print(f"  sample size: {len(sample_records)} records")
    print()
    print("NOTE: This is a scaffold. Actual model invocation requires API access")
    print("(GEMINI_API_KEY). The full benchmark runs on Kaggle or locally with")
    print("proper credentials. This command validates the variant config and")
    print("sample readiness.")
    print()

    mock_results: list[dict[str, Any]] = []
    start_time = time.monotonic()
    for record in sample_records:
        source = record.get("source_record", {})
        mock_prediction = record.get("ground_truth", {}).get("is_valid_part", False)
        mock_results.append(
            {
                "sample_id": record["sample_id"],
                "predicted_is_valid_part": mock_prediction,
                "predicted_part_number": source.get("part_number", ""),
                "predicted_part_name": source.get("part_name", ""),
                "ground_truth_is_valid_part": record.get("ground_truth", {}).get(
                    "is_valid_part", False
                ),
            }
        )
    elapsed = time.monotonic() - start_time

    tp = sum(
        1
        for r in mock_results
        if r["predicted_is_valid_part"] and r["ground_truth_is_valid_part"]
    )
    fp = sum(
        1
        for r in mock_results
        if r["predicted_is_valid_part"] and not r["ground_truth_is_valid_part"]
    )
    fn = sum(
        1
        for r in mock_results
        if not r["predicted_is_valid_part"] and r["ground_truth_is_valid_part"]
    )
    tn = sum(
        1
        for r in mock_results
        if not r["predicted_is_valid_part"] and not r["ground_truth_is_valid_part"]
    )
    total_records = len(mock_results)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    false_positive_rate = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    time_per_record = elapsed / total_records if total_records > 0 else 0.0

    metrics_entry = {
        "variant_id": variant_name,
        "variant_config": variant_cfg,
        "run_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "is_mock_run": True,
        "sample_id": "bench-sample-v1",
        "sample_size": total_records,
        "metrics": {
            "true_positives": tp,
            "false_positives": fp,
            "false_negatives": fn,
            "true_negatives": tn,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "false_positive_rate": round(false_positive_rate, 4),
            "time_per_record_s": round(time_per_record, 4),
            "cost_per_record_usd": 0.0,
        },
    }

    existing_metrics: list[dict[str, Any]] = []
    if METRICS_PATH.exists():
        existing_metrics = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
        if not isinstance(existing_metrics, list):
            existing_metrics = []

    existing_metrics = [
        m for m in existing_metrics if m.get("variant_id") != variant_name
    ]
    existing_metrics.append(metrics_entry)
    write_json(METRICS_PATH, existing_metrics)

    print(f"Mock run completed for variant '{variant_name}':")
    print(f"  precision: {precision:.4f}")
    print(f"  recall: {recall:.4f}")
    print(f"  false_positive_rate: {false_positive_rate:.4f}")
    print(f"  time_per_record: {time_per_record:.4f}s")
    print()
    print(f"Metrics saved to {METRICS_PATH}")
    return 0


def compare() -> int:
    if not METRICS_PATH.exists():
        print(f"No metrics found: {METRICS_PATH}")
        print("Run at least two variants with 'run --variant <name>' first.")
        return 1

    metrics_list = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
    if not isinstance(metrics_list, list):
        metrics_list = [metrics_list]

    if len(metrics_list) < 1:
        print("No variant metrics found.")
        return 1

    print(
        f"{'Variant':<30} {'Precision':>10} {'Recall':>10} {'FPR':>10} {'Time/Rec':>10} {'Cost/Rec':>10}"
    )
    print("-" * 80)
    for m in metrics_list:
        met = m.get("metrics", {})
        mock_flag = " (mock)" if m.get("is_mock_run", False) else ""
        print(
            f"{m.get('variant_id', 'N/A'):<30} "
            f"{met.get('precision', 0):>10.4f} "
            f"{met.get('recall', 0):>10.4f} "
            f"{met.get('false_positive_rate', 0):>10.4f} "
            f"{met.get('time_per_record_s', 0):>10.4f} "
            f"{met.get('cost_per_record_usd', 0):>10.6f}{mock_flag}"
        )
    return 0


def report() -> int:
    if not METRICS_PATH.exists():
        print(f"No metrics found: {METRICS_PATH}")
        print("Run at least one variant first.")
        return 1

    if not SAMPLE_PATH.exists():
        print(f"No sample found: {SAMPLE_PATH}")
        return 1

    metrics_list = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
    if not isinstance(metrics_list, list):
        metrics_list = [metrics_list]

    sample_records = read_jsonl(SAMPLE_PATH)
    total_sample = len(sample_records)
    valid_parts = sum(
        1
        for r in sample_records
        if r.get("ground_truth", {}).get("is_valid_part", False)
    )
    invalid_parts = total_sample - valid_parts

    lines = [
        "# Benchmark Report: Project 13 Part Extraction",
        "",
        f"Generated: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}",
        "",
        "## Test Sample",
        "",
        f"- **sample_id**: bench-sample-v1",
        f"- **total records**: {total_sample}",
        f"- **valid parts (ground truth)**: {valid_parts}",
        f"- **invalid parts (ground truth)**: {invalid_parts}",
        f"- **source**: autonomous_test/results/test_db.jsonl",
        "",
        "## Ground-Truth Criteria",
        "",
        "- `is_valid_part=true`: Extraction identifies a real, specific electronic component with a valid or plausible MPN.",
        "- `is_valid_part=false`: Extraction is a false positive: board model, designator list, generic label, OCR artifact, date code, or non-component text.",
        "",
        "## Variants Compared",
        "",
    ]

    for m in metrics_list:
        mock_flag = " (mock run)" if m.get("is_mock_run", False) else ""
        cfg = m.get("variant_config", {})
        lines.append(f"### {m.get('variant_id', 'N/A')}{mock_flag}")
        lines.append("")
        lines.append(f"- model: `{cfg.get('model', 'N/A')}`")
        lines.append(f"- prompt: `{cfg.get('prompt_template', 'N/A')}`")
        lines.append(f"- parameters: `{json.dumps(cfg.get('parameters', {}))}`")
        lines.append("")

    lines.append("## Metrics Comparison")
    lines.append("")

    header = f"| {'Variant':<28} | {'Precision':>9} | {'Recall':>9} | {'FPR':>9} | {'Time/Rec':>9} | {'Cost/Rec':>9} |"
    sep = f"|{'-' * 30}|{'-' * 11}|{'-' * 11}|{'-' * 11}|{'-' * 11}|{'-' * 11}|"
    lines.append(header)
    lines.append(sep)

    for m in metrics_list:
        met = m.get("metrics", {})
        mock_flag = " *" if m.get("is_mock_run", False) else ""
        vid = m.get("variant_id", "N/A")
        if len(vid) > 28:
            vid = vid[:25] + "..."
        lines.append(
            f"| {vid:<28} | {met.get('precision', 0):>9.4f} | {met.get('recall', 0):>9.4f} | "
            f"{met.get('false_positive_rate', 0):>9.4f} | {met.get('time_per_record_s', 0):>9.4f} | "
            f"{met.get('cost_per_record_usd', 0):>9.6f} |{mock_flag}"
        )

    lines.append("")
    lines.append(
        "* = mock run (predictions copied from ground truth, for scaffolding validation)"
    )
    lines.append("")

    lines.append("## Conclusions")
    lines.append("")
    if len(metrics_list) < 2:
        lines.append("Insufficient data for conclusions. Run at least two variants.")
    else:
        best_precision = max(
            metrics_list, key=lambda m: m.get("metrics", {}).get("precision", 0)
        )
        best_recall = max(
            metrics_list, key=lambda m: m.get("metrics", {}).get("recall", 0)
        )
        lines.append(
            f"- Best precision: **{best_precision.get('variant_id', 'N/A')}** ({best_precision.get('metrics', {}).get('precision', 0):.4f})"
        )
        lines.append(
            f"- Best recall: **{best_recall.get('variant_id', 'N/A')}** ({best_recall.get('metrics', {}).get('recall', 0):.4f})"
        )

    lines.append("")
    lines.append("## Known Issues")
    lines.append("")
    lines.append(
        "- Ground-truth labels were initially heuristic and require human review."
    )
    lines.append(
        "- Mock runs copy predictions from ground truth and show perfect scores; real runs require API access."
    )
    lines.append("")
    lines.append("## Integrity Notes")
    lines.append("")
    lines.append(
        "- Pack does not modify the canonical catalog or downstream artifacts."
    )
    lines.append(
        "- Benchmark results are diagnostic and not promoted to the catalog without a separate curation step."
    )
    lines.append("- Test sample is fixed and reproducible between runs.")

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Report written to {REPORT_PATH}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=[
            "init-sample",
            "validate-sample",
            "list-variants",
            "run",
            "compare",
            "report",
        ],
        help="Action to execute",
    )
    parser.add_argument("--variant", help="Variant name for 'run' command")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.command == "init-sample":
        return init_sample()
    if args.command == "validate-sample":
        return validate_sample()
    if args.command == "list-variants":
        return list_variants()
    if args.command == "run":
        if not args.variant:
            print("--variant is required for 'run' command")
            return 1
        return run_variant(args.variant)
    if args.command == "compare":
        return compare()
    if args.command == "report":
        return report()

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
