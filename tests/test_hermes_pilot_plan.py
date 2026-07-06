import json
import subprocess
import sys
import unittest
from pathlib import Path

from agent_runtime_plans.hermes_pilot.validate_pilot import validate_pilot, validate_provider_matrix

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "agent_runtime_plans" / "hermes_pilot" / "validate_pilot.py"
PROVIDER_MATRIX = ROOT / "agent_runtime_plans" / "hermes_pilot" / "provider_matrix.json"
PILOT_PLAN = ROOT / "agent_runtime_plans" / "hermes_pilot" / "pilot_plan.json"


class HermesPilotPlanTest(unittest.TestCase):
    def test_pilot_plan_cli_passes(self):
        result = subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("OK: Hermes pilot plan", result.stdout)

    def test_providers_block_physical_actuation(self):
        data = json.loads(PROVIDER_MATRIX.read_text(encoding="utf-8"))
        errors = validate_provider_matrix(data)
        self.assertEqual(errors, [])
        for provider in data["providers"]:
            self.assertIn("physical_actuation", provider["blocked_modes"])
            self.assertTrue(provider["quota_policy"])

    def test_pilot_requires_audit_artifacts_and_review_blocks(self):
        data = json.loads(PILOT_PLAN.read_text(encoding="utf-8"))
        errors = validate_pilot(data)
        self.assertEqual(errors, [])
        self.assertIn("run_receipt.json", data["required_artifacts_per_run"])
        self.assertIn("quota_snapshot.json", data["required_artifacts_per_run"])
        self.assertIn("physical actuation", data["blocked_until_review"])

    def test_missing_review_status_is_rejected(self):
        data = json.loads(PILOT_PLAN.read_text(encoding="utf-8"))
        data["status"] = "ready_to_deploy"
        errors = validate_pilot(data)
        self.assertTrue(any("draft_review_required" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
