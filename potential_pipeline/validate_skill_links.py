#!/usr/bin/env python3
"""Validate that PotentialDossier products are mapped to execution skills."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DOSSIERS = ROOT / "potential_pipeline" / "seed_dossiers.json"
DEFAULT_SKILLS = ROOT / "execution_skills" / "seed_skills.json"


def validate_links(dossiers: dict, skills: dict) -> list[str]:
    skill_ids = {skill["id"] for skill in skills.get("skills", [])}
    errors: list[str] = []
    for dossier in dossiers.get("dossiers", []):
        for product in dossier.get("intended_products", []):
            name = product.get("product", "<unknown>")
            skill_id = product.get("execution_skill_id")
            missing = product.get("missing_skill_to_create")
            if bool(skill_id) == bool(missing):
                errors.append(f"{dossier.get('id')}::{name} must define exactly one of execution_skill_id or missing_skill_to_create")
                continue
            if skill_id and skill_id not in skill_ids:
                errors.append(f"{dossier.get('id')}::{name} references unknown execution_skill_id: {skill_id}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dossiers", type=Path, default=DEFAULT_DOSSIERS)
    parser.add_argument("--skills", type=Path, default=DEFAULT_SKILLS)
    args = parser.parse_args()
    errors = validate_links(
        json.loads(args.dossiers.read_text(encoding="utf-8")),
        json.loads(args.skills.read_text(encoding="utf-8")),
    )
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("OK: all PotentialDossier products are linked to execution skills or declared missing skills")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
