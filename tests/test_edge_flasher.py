import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILES = ROOT / "edge_flasher" / "profiles.json"
SCRIPT = ROOT / "edge_flasher" / "generate_artifacts.py"


class EdgeFlasherTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profiles = json.loads(PROFILES.read_text(encoding="utf-8"))["profiles"]

    def test_required_profiles_exist_and_block_high_risk_actions(self):
        profile_ids = {profile["id"] for profile in self.profiles}
        self.assertEqual(profile_ids, {"phone-aquaponics-observer", "recycle-bench-catalog-station", "phone-sensor-gateway"})
        for profile in self.profiles:
            self.assertTrue(profile["allowed_actions"], profile["id"])
            self.assertTrue(profile["blocked_high_risk_actions"], profile["id"])
            self.assertTrue(profile["required_human_approval_before"], profile["id"])
            self.assertFalse(set(profile["allowed_actions"]) & set(profile["blocked_high_risk_actions"]), profile["id"])

    def test_generator_writes_safe_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--profile", "phone-aquaponics-observer", "--output-dir", tmp],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            out = Path(tmp)
            device = json.loads((out / "device_profile.json").read_text(encoding="utf-8"))
            receipt = json.loads((out / "install_receipt.json").read_text(encoding="utf-8"))
            report = (out / "bench_test_report.md").read_text(encoding="utf-8")
            rollback = (out / "rollback.md").read_text(encoding="utf-8")
        self.assertEqual(device["safety_status"], "blocked_until_human_approval_for_physical_or_high_risk_actions")
        self.assertEqual(receipt["install_status"], "NOT_INSTALLED")
        self.assertEqual(receipt["approval_status"], "MISSING_HUMAN_APPROVAL")
        self.assertIn("control_pump", device["blocked_high_risk_actions"])
        self.assertIn("BLOCKED_PENDING_REAL_BENCH_AND_HUMAN_APPROVAL", report)
        self.assertIn("Require a new human approval", rollback)


if __name__ == "__main__":
    unittest.main()
