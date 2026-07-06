#!/usr/bin/env python3
"""Generate a deterministic execution plan from a PotentialDossier seed.

This script intentionally produces a Markdown plan only. It does not control hardware,
modify canonical catalogs, or deploy automation.
"""
import argparse
import json
from pathlib import Path

STAGES = ["analiza_potencjalu", "zamysl", "projekt", "wykonanie", "optymalizacja"]


def load_dossier(path: Path, dossier_id: str) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    for dossier in data.get("dossiers", []):
        if dossier.get("id") == dossier_id:
            return dossier
    raise SystemExit(f"Dossier not found: {dossier_id}")


def validate_dossier(dossier: dict) -> list[str]:
    errors: list[str] = []
    stages = [step.get("stage") for step in dossier.get("workflow", [])]
    if stages != STAGES:
        errors.append(f"workflow stages must be exactly {STAGES}, got {stages}")
    if not dossier.get("free_or_low_cost"):
        errors.append("dossier must focus on free_or_low_cost potential")
    if dossier.get("potential_score", 0) <= dossier.get("risk_score", 100):
        errors.append("potential_score should be greater than risk_score for a seed execution candidate")
    physical_products = [p for p in dossier.get("intended_products", []) if "observer" in p.get("product", "") or "gateway" in p.get("product", "")]
    for product in physical_products:
        if not product.get("approval_required"):
            errors.append(f"physical/edge product requires approval: {product.get('product')}")
    gates = set(dossier.get("review_gates", []))
    if "human_approval_before_physical_actuation" not in gates:
        errors.append("missing human_approval_before_physical_actuation gate")
    return errors


def build_plan(dossier: dict) -> str:
    lines = [
        f"# Execution plan: {dossier['id']}",
        "",
        f"Source potential: {dossier['source']}",
        f"Potential score: {dossier['potential_score']} / Risk score: {dossier['risk_score']}",
        "",
        "## Mission needs",
        "",
        *[f"- {need}" for need in dossier["mission_need"]],
        "",
        "## Products to design from potential",
        "",
    ]
    for product in dossier["intended_products"]:
        lines.extend([
            f"### {product['product']}",
            f"- Target use: {product['target_use']}",
            f"- Approval required: {str(product['approval_required']).lower()}",
            "- Required artifacts:",
            *[f"  - {artifact}" for artifact in product["required_artifacts"]],
            "",
        ])
    lines.extend(["## Stage plan", ""])
    for step in dossier["workflow"]:
        lines.extend([
            f"### {step['stage']}",
            f"- Question: {step['question']}",
            f"- Output: {step['output']}",
            f"- Default mode: {step['default_mode']}",
            "",
        ])
    lines.extend([
        "## Review gates",
        "",
        *[f"- {gate}" for gate in dossier["review_gates"]],
        "",
        "## Optimization metrics",
        "",
        *[f"- {metric}" for metric in dossier["optimization_metrics"]],
        "",
        "## Safety stance",
        "",
        "This plan is suggest-only until human approval records explicitly unlock a physical execution pack.",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dossier-id", default="ewaste_to_food_edge_devices")
    parser.add_argument("--input", type=Path, default=Path(__file__).with_name("seed_dossiers.json"))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()

    dossier = load_dossier(args.input, args.dossier_id)
    errors = validate_dossier(dossier)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    if args.validate_only:
        print(f"OK: {args.dossier_id}")
        return 0
    plan = build_plan(dossier)
    if args.output:
        args.output.write_text(plan, encoding="utf-8")
        print(f"Wrote {args.output}")
    else:
        print(plan, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
