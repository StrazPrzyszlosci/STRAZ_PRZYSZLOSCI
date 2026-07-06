import json
import unittest
from pathlib import Path

from model_resource_selector.select_model import select_profile

ROOT = Path(__file__).resolve().parents[1]
PROFILES = json.loads((ROOT / "model_resource_selector" / "profiles.json").read_text(encoding="utf-8"))["profiles"]


class ModelResourceSelectorTest(unittest.TestCase):
    def test_public_low_risk_task_uses_free_public_profile(self):
        selected = select_profile({"privacy": "public", "workload": "summary"}, PROFILES)
        self.assertEqual(selected["id"], "free_public_small_model")

    def test_private_task_prefers_selfhost_low_power_profile(self):
        selected = select_profile({"privacy": "private", "workload": "routing"}, PROFILES)
        self.assertEqual(selected["id"], "selfhost_recovered_low_power_node")

    def test_private_task_cannot_be_forced_to_public_by_consent_flag(self):
        with self.assertRaises(ValueError):
            select_profile({"privacy": "private", "human_consent_for_public_model": True}, PROFILES)

    def test_high_cost_workload_requires_energy_justification(self):
        with self.assertRaises(ValueError):
            select_profile({"privacy": "private", "workload": "vision"}, PROFILES)
        selected = select_profile({"privacy": "private", "workload": "vision", "energy_justification": "OZE surplus window"}, PROFILES)
        self.assertEqual(selected["id"], "selfhost_gpu_high_cost_node")


if __name__ == "__main__":
    unittest.main()
