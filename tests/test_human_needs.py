import copy
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "human_needs" / "seed_needs.json"

import sys
sys.path.insert(0, str(ROOT / "human_needs"))
from validate_records import validate_record, validate_records  # noqa: E402


def _ok_record() -> dict:
    return {
        "id": "need_test_ok",
        "submitted_by": {"role": "volunteer", "public_label": "v1"},
        "visibility_scope": {"level": "maintainer_only"},
        "need_or_problem": "Test need description at least 10 chars",
        "location_or_area": "PL local",
        "cost_constraints": {"max_pln_or_free": "free"},
        "energy_constraints": {"preferred_class": "low_power_or_oze_preferred"},
        "origin": {"chosen_from_recommendation": False, "provenance": "test"},
        "expected_outcome": "just a test outcome"
    }


class HumanNeedsIntakeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = json.loads(SEED.read_text(encoding="utf-8"))
        cls.records = cls.payload["records"]

    def test_seed_validates(self):
        errors = validate_records(self.payload)
        self.assertEqual(errors, [], f"seed must validate: {errors}")

    def test_ids_unique(self):
        ids = [r["id"] for r in self.records]
        self.assertEqual(len(ids), len(set(ids)))

    def test_blocks_private_contact_note_under_public_visibility(self):
        rec = _ok_record()
        rec["submitted_by"]["contact_note"] = "private phone"
        rec["visibility_scope"]["level"] = "public"
        errors = validate_record(rec)
        self.assertTrue(any("contact_note" in e for e in errors), errors)

    def test_blocks_high_energy_without_oze_required(self):
        rec = _ok_record()
        rec["energy_constraints"] = {"preferred_class": "high_energy_requires_oze_or_justification", "oze_required": False}
        errors = validate_record(rec)
        self.assertTrue(any("oze_required" in e for e in errors), errors)

    def test_allows_high_energy_with_oze_required(self):
        rec = _ok_record()
        rec["energy_constraints"] = {"preferred_class": "high_energy_requires_oze_or_justification", "oze_required": True}
        errors = validate_record(rec)
        self.assertFalse(any("oze_required" in e for e in errors), errors)

    def test_blocks_recommendation_preselecting_physical_execution(self):
        rec = _ok_record()
        rec["origin"]["chosen_from_recommendation"] = True
        rec["expected_outcome"] = "install pump and actuate"
        errors = validate_record(rec)
        self.assertTrue(any("physical execution" in e for e in errors), errors)

    def test_allows_own_description_without_recommendation(self):
        rec = _ok_record()
        rec["origin"]["chosen_from_recommendation"] = False
        rec["origin"]["own_description_provided"] = True
        rec["expected_outcome"] = "manual install by operator"
        errors = validate_record(rec)
        self.assertFalse(any("physical execution" in e for e in errors), errors)

    def test_blocks_missing_visibility_scope(self):
        rec = _ok_record()
        del rec["visibility_scope"]
        errors = validate_record(rec)
        self.assertTrue(any("visibility_scope" in e for e in errors + ["missing required fields: ['visibility_scope']"]) or any("missing required fields" in e for e in errors))

    def test_blocks_bad_id(self):
        rec = _ok_record()
        rec["id"] = "Bad ID!"
        errors = validate_record(rec)
        self.assertTrue(any("id must match" in e for e in errors))

    def test_blocks_duplicate_id(self):
        a = _ok_record()
        b = _ok_record()
        errors = validate_records({"records": [a, b]})
        self.assertTrue(any("duplicate id" in e for e in errors))

    def test_blocks_unknown_role(self):
        rec = _ok_record()
        rec["submitted_by"]["role"] = "root"
        errors = validate_record(rec)
        self.assertTrue(any("role" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
