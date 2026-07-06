import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "potential_pipeline" / "seed_dossiers.json"
SCRIPT = ROOT / "potential_pipeline" / "generate_execution_plan.py"
EXPECTED_STAGES = ["analiza_potencjalu", "zamysl", "projekt", "wykonanie", "optymalizacja"]


class PotentialPipelineTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(SEED.read_text(encoding="utf-8"))
        cls.dossier = cls.data["dossiers"][0]

    def test_seed_dossier_encodes_potential_to_optimization_loop(self):
        stages = [step["stage"] for step in self.dossier["workflow"]]
        self.assertEqual(stages, EXPECTED_STAGES)
        self.assertTrue(self.dossier["free_or_low_cost"])
        self.assertGreater(self.dossier["potential_score"], self.dossier["risk_score"])

    def test_ewaste_potential_targets_food_and_hardware_reuse(self):
        needs = set(self.dossier["mission_need"])
        self.assertIn("food", needs)
        self.assertIn("waste", needs)
        self.assertIn("hardware_reuse", needs)
        products = {product["product"] for product in self.dossier["intended_products"]}
        self.assertIn("phone-aquaponics-observer", products)
        self.assertIn("recycled-sensor-gateway", products)

    def test_physical_products_require_approval_and_artifacts(self):
        for product in self.dossier["intended_products"]:
            self.assertTrue(product["required_artifacts"], product["product"])
            if product["product"] in {"phone-aquaponics-observer", "recycled-sensor-gateway"}:
                self.assertTrue(product["approval_required"], product["product"])
        self.assertIn("human_approval_before_physical_actuation", self.dossier["review_gates"])

    def test_generator_validate_only_passes(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--validate-only"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("OK: ewaste_to_food_edge_devices", result.stdout)

    def test_generator_writes_deterministic_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "plan.md"
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--output", str(output)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            plan = output.read_text(encoding="utf-8")
        self.assertIn("# Execution plan: ewaste_to_food_edge_devices", plan)
        self.assertIn("phone-aquaponics-observer", plan)
        self.assertIn("human_approval_before_physical_actuation", plan)
        self.assertIn("suggest-only", plan)


if __name__ == "__main__":
    unittest.main()
