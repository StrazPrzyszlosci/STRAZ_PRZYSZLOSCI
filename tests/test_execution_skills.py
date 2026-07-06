import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "execution_skills" / "seed_skills.json"

REQUIRED_SKILL_KEYS = {
    "id",
    "version",
    "status",
    "goal",
    "mission_alignment",
    "allowed_modes",
    "inputs",
    "outputs",
    "audit_trail",
    "review_gates",
    "safety_notes",
    "next_handoff",
}

HIGH_RISK_BLOCKS = {"pump_control", "heater_control", "relay_control", "dosing_control", "chemical_dosing"}


class ExecutionSkillRegistryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(REGISTRY.read_text(encoding="utf-8"))
        cls.skills = cls.data["skills"]

    def test_seed_registry_has_unique_skill_ids(self):
        ids = [skill["id"] for skill in self.skills]
        self.assertEqual(len(ids), len(set(ids)))
        for skill_id in ids:
            self.assertRegex(skill_id, r"^[a-z0-9][a-z0-9_-]{2,80}$")

    def test_each_skill_has_audit_contract(self):
        for skill in self.skills:
            self.assertTrue(REQUIRED_SKILL_KEYS.issubset(skill.keys()), skill.get("id"))
            self.assertTrue(skill["inputs"], skill["id"])
            self.assertTrue(skill["outputs"], skill["id"])
            self.assertTrue(skill["review_gates"], skill["id"])
            self.assertTrue(all(skill["audit_trail"].values()), skill["id"])
            self.assertIn("auditability", skill["mission_alignment"], skill["id"])

    def test_physical_or_food_skills_are_not_production_by_default(self):
        for skill in self.skills:
            if {"food", "water", "hardware_reuse"}.intersection(skill["mission_alignment"]):
                self.assertNotIn("production", skill["allowed_modes"], skill["id"])
                joined_blocks = {block for gate in skill["review_gates"] for block in gate["blocks"]}
                self.assertTrue(joined_blocks, skill["id"])

    def test_high_risk_actuation_is_blocked_by_review_gates(self):
        edge = next(skill for skill in self.skills if skill["id"] == "edge_onboarding")
        blocks = {block for gate in edge["review_gates"] for block in gate["blocks"]}
        self.assertTrue(HIGH_RISK_BLOCKS.intersection(blocks))

    def test_handoff_builder_prevents_false_green_status(self):
        handoff = next(skill for skill in self.skills if skill["id"] == "handoff_builder")
        gates = " ".join(gate["gate"] for gate in handoff["review_gates"])
        self.assertIn("no_false_green_status", gates)
        self.assertTrue(any("BLOCKED" in note for note in handoff["safety_notes"]))


if __name__ == "__main__":
    unittest.main()
