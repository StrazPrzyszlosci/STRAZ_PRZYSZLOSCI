#!/usr/bin/env python3
"""Generate suggest-only edge flasher wizard artifacts.

The wizard scaffolds reviewable files only. It never flashes firmware, opens network
ports, controls hardware, or marks a physical install as approved.
"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROFILES = ROOT / "profiles.json"


def load_profile(profile_id: str, path: Path = PROFILES) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    for profile in data.get("profiles", []):
        if profile.get("id") == profile_id:
            return profile
    raise SystemExit(f"Unknown profile: {profile_id}")


def assert_safe_profile(profile: dict) -> None:
    if not profile.get("blocked_high_risk_actions"):
        raise SystemExit("Profile must block high-risk actions")
    if not profile.get("required_human_approval_before"):
        raise SystemExit("Profile must define human approval gates")
    forbidden_allowed = set(profile.get("allowed_actions", [])) & set(profile.get("blocked_high_risk_actions", []))
    if forbidden_allowed:
        raise SystemExit(f"Action cannot be both allowed and blocked: {sorted(forbidden_allowed)}")


def build_device_profile(profile: dict) -> dict:
    return {
        "profile_id": profile["id"],
        "device_class": profile["device_class"],
        "purpose": profile["purpose"],
        "mode": "suggest_only_observation_or_cataloging",
        "allowed_actions": profile["allowed_actions"],
        "blocked_high_risk_actions": profile["blocked_high_risk_actions"],
        "required_human_approval_before": profile["required_human_approval_before"],
        "safety_status": "blocked_until_human_approval_for_physical_or_high_risk_actions",
    }


def build_install_receipt(profile: dict) -> dict:
    return {
        "profile_id": profile["id"],
        "generated_at": datetime(2026, 7, 6, tzinfo=timezone.utc).isoformat(),
        "install_status": "NOT_INSTALLED",
        "approval_status": "MISSING_HUMAN_APPROVAL",
        "performed_actions": [],
        "blocked_actions": profile["blocked_high_risk_actions"],
        "operator_note_required": True,
    }


def bench_report(profile: dict) -> str:
    lines = [f"# Bench test report: {profile['id']}", "", "Status: BLOCKED_PENDING_REAL_BENCH_AND_HUMAN_APPROVAL", "", "## Required bench checks", ""]
    lines.extend(f"- [ ] {check}" for check in profile["bench_checks"])
    lines.extend(["", "## Explicitly blocked high-risk actions", ""])
    lines.extend(f"- {action}" for action in profile["blocked_high_risk_actions"])
    lines.extend(["", "No physical deployment, firmware flashing, actuator control, or public publishing is authorized by this scaffold.", ""])
    return "\n".join(lines)


def rollback_doc(profile: dict) -> str:
    return "\n".join([
        f"# Rollback plan: {profile['id']}",
        "",
        "1. Stop the local wizard run; do not retry high-risk actions automatically.",
        "2. Disconnect the reused device from any test network if a human operator connected it.",
        "3. Preserve generated receipts and logs for review.",
        "4. Revert only files produced by this artifact generation run if review rejects the profile.",
        "5. Require a new human approval record before any physical installation or actuation attempt.",
        "",
    ])


def write_artifacts(profile: dict, output_dir: Path) -> None:
    assert_safe_profile(profile)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "device_profile.json").write_text(json.dumps(build_device_profile(profile), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (output_dir / "install_receipt.json").write_text(json.dumps(build_install_receipt(profile), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (output_dir / "bench_test_report.md").write_text(bench_report(profile), encoding="utf-8")
    (output_dir / "rollback.md").write_text(rollback_doc(profile), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    profile = load_profile(args.profile)
    write_artifacts(profile, args.output_dir)
    print(f"Wrote edge flasher scaffold for {args.profile} to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
