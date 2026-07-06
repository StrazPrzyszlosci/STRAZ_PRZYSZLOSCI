#!/usr/bin/env python3
"""Select the cheapest safe model/resource profile for a small automation cell."""
import argparse
import json
from pathlib import Path

PROFILES = Path(__file__).with_name("profiles.json")


def select_profile(task: dict, profiles: list[dict]) -> dict:
    privacy = task.get("privacy", "public")
    needs_local = task.get("requires_offline") or privacy == "private"
    needs_heavy = task.get("workload") in {"vision", "batch_extraction", "large_reasoning"}
    public_consent = task.get("human_consent_for_public_model", False)
    energy_justification = task.get("energy_justification")

    if privacy == "private" and public_consent:
        raise ValueError("private tasks must not use public models merely because consent was toggled; prefer local/selfhost profile")
    if needs_heavy:
        if not energy_justification:
            raise ValueError("high-cost local/GPU workload requires energy_justification")
        return next(p for p in profiles if p["id"] == "selfhost_gpu_high_cost_node")
    if needs_local:
        return next(p for p in profiles if p["id"] == "selfhost_recovered_low_power_node")
    return next(p for p in profiles if p["id"] == "free_public_small_model")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", type=Path, required=True)
    args = parser.parse_args()
    profiles = json.loads(PROFILES.read_text(encoding="utf-8"))["profiles"]
    task = json.loads(args.task.read_text(encoding="utf-8"))
    try:
        selected = select_profile(task, profiles)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 1
    print(json.dumps({"selected_profile_id": selected["id"], "provider_type": selected["provider_type"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
