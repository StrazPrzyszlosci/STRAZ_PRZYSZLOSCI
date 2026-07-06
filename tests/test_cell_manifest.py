import copy
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFESTS = ROOT / "agentic_cells" / "seed_cell_manifests.json"

import sys
sys.path.insert(0, str(ROOT / "agentic_cells"))
from validate_cell_manifest import (  # noqa: E402
    validate_manifest,
    validate_manifests,
)


EXPECTED_CELL_IDS = {
    "edge_flasher",
    "resource_scout",
    "model_resource_selector",
    "potential_pipeline",
    "aquaponics_observer_pack",
}


def _load() -> dict:
    return json.loads(MANIFESTS.read_text(encoding="utf-8"))


class AgenticCellManifestTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = _load()
        cls.cells = cls.payload["cells"]

    def test_seed_describes_all_five_expected_cells(self):
        ids = {cell["cell_id"] for cell in self.cells}
        self.assertEqual(ids, EXPECTED_CELL_IDS)

    def test_cell_ids_are_unique(self):
        ids = [cell["cell_id"] for cell in self.cells]
        self.assertEqual(len(ids), len(set(ids)))

    def test_validator_accepts_seed(self):
        errors = validate_manifests(self.payload)
        self.assertEqual(errors, [], f"seed must validate: {errors}")

    def test_schema_required_fields_are_present_in_each_cell(self):
        for cell in self.cells:
            for field in ("cell_id", "version", "status", "purpose",
                          "allowed_modes", "input_contract", "output_artifacts",
                          "model_resource_policy", "energy_policy",
                          "human_control_points", "audit_trail", "rollback_plan",
                          "review_gates"):
                self.assertIn(field, cell, f"{cell['cell_id']} missing {field}")

    def test_each_cell_has_audit_trail_all_true(self):
        for cell in self.cells:
            audit = cell["audit_trail"]
            for flag in ("must_record_inputs", "must_record_tool_versions",
                         "must_record_decisions", "must_record_artifacts"):
                self.assertTrue(audit[flag], f"{cell['cell_id']}.{flag}")

    def test_each_cell_blocks_public_model_private_data(self):
        for cell in self.cells:
            pol = cell["model_resource_policy"]
            self.assertFalse(
                pol["may_use_private_data_on_public_model"],
                f"{cell['cell_id']} must not send private data to public model by default",
            )

    def test_high_risk_cells_reference_actuation_in_control_points(self):
        for cell in self.cells:
            if "hardware-lab" in cell["allowed_modes"] or "production" in cell["allowed_modes"]:
                blob = " ".join(
                    p.get("point", "") for p in cell["human_control_points"]
                ).lower() + " " + " ".join(
                    g.get("gate", "") for g in cell["review_gates"]
                ).lower()
                self.assertIn("actuation", blob, f"{cell['cell_id']} high-risk cell needs actuation gate")

    def test_block_rejects_missing_human_control_points(self):
        cell = copy.deepcopy(self.cells[0])
        cell["human_control_points"] = []
        errors = validate_manifest(cell)
        self.assertTrue(any("human_control_points" in e for e in errors))

    def test_block_rejects_missing_audit_trail(self):
        cell = copy.deepcopy(self.cells[0])
        cell["audit_trail"] = {"must_record_inputs": True}
        errors = validate_manifest(cell)
        self.assertTrue(any("audit_trail" in e for e in errors))

    def test_block_rejects_production_without_explicit_production_gate(self):
        cell = copy.deepcopy(self.cells[0])
        cell["allowed_modes"] = ["read-only", "production"]
        errors = validate_manifest(cell)
        self.assertTrue(any("production" in e for e in errors), errors)

    def test_block_rejects_private_data_on_public_model_flag_true(self):
        cell = copy.deepcopy(self.cells[0])
        cell["model_resource_policy"]["may_use_private_data_on_public_model"] = True
        errors = validate_manifest(cell)
        self.assertTrue(any("private data" in e for e in errors), errors)

    def test_block_rejects_duplicate_cell_id(self):
        payload = {"cells": [self.cells[0], copy.deepcopy(self.cells[0])]}
        errors = validate_manifests(payload)
        self.assertTrue(any("duplicate cell_id" in e for e in errors))

    def test_block_rejects_missing_rollback_strategy(self):
        cell = copy.deepcopy(self.cells[0])
        cell["rollback_plan"]["strategy"] = "ab"
        errors = validate_manifest(cell)
        self.assertTrue(any("rollback_plan.strategy" in e for e in errors))

    def test_block_rejects_unknown_input_kind(self):
        cell = copy.deepcopy(self.cells[0])
        cell["input_contract"][0]["kind"] = "secret_root"
        errors = validate_manifest(cell)
        self.assertTrue(any("kind" in e for e in errors))

    def test_each_cell_has_implementation_ref(self):
        for cell in self.cells:
            impl = cell.get("implementation_ref", {})
            self.assertTrue(impl.get("directory"), f"{cell['cell_id']} missing implementation_ref.directory")
            self.assertTrue(impl.get("entry_artifact"), f"{cell['cell_id']} missing implementation_ref.entry_artifact")


if __name__ == "__main__":
    unittest.main()
