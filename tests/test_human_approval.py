import copy
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "human_approval" / "seed_approvals.json"

import sys
sys.path.insert(0, str(ROOT / "human_approval"))
from validate_record import validate_record, validate_records  # noqa: E402


def _ok_approval() -> dict:
    return {
        "id": "approval_test_ok",
        "approved_by": {"role": "maintainer", "label": "m1"},
        "approved_scope": "dry_run_only",
        "artifacts_or_target": ["test.txt"],
        "granted_at": "2026-07-06T00:00:00+00:00",
        "expires_at": "2026-12-31T00:00:00+00:00",
        "risks": ["test risk"],
        "rollback_command": "rm",
        "human_control_point": "maintainer signs off",
        "revoked": False,
        "reason": "test approval reason at least 10 chars"
    }


class HumanApprovalRecordTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = json.loads(SEED.read_text(encoding="utf-8"))
        cls.records = cls.payload["records"]

    def test_seed_validates(self):
        errors = validate_records(self.payload)
        self.assertEqual(errors, [], f"seed must validate: {errors}")

    def test_blocks_expired_approval(self):
        rec = _ok_approval()
        rec["expires_at"] = "2020-01-01T00:00:00+00:00"
        errors = validate_record(rec)
        self.assertTrue(any("expired" in e for e in errors), errors)

    def test_blocks_revoked(self):
        rec = _ok_approval()
        rec["revoked"] = True
        errors = validate_record(rec)
        self.assertTrue(any("revoked" in e for e in errors), errors)

    def test_blocks_code_review_covering_physical(self):
        rec = _ok_approval()
        rec["approved_scope"] = "code_review"
        rec["artifacts_or_target"] = ["edge_flasher physical install"]
        errors = validate_record(rec)
        self.assertTrue(any("code_review" in e and "physical" in e for e in errors) or any("physical" in e for e in errors), errors)

    def test_blocks_provider_cost_without_ledger(self):
        rec = _ok_approval()
        rec["approved_scope"] = "provider_cost_increase"
        rec["artifacts_or_target"] = ["nvidia_nim"]
        errors = validate_record(rec)
        self.assertTrue(any("cost_ledger_ref" in e for e in errors), errors)

    def test_allows_provider_cost_with_ledger(self):
        rec = _ok_approval()
        rec["approved_scope"] = "provider_cost_increase"
        rec["cost_ledger_ref"] = "ledger_entry_42"
        errors = validate_record(rec)
        self.assertFalse(any("cost_ledger_ref" in e for e in errors), errors)

    def test_blocks_unknown_scope(self):
        rec = _ok_approval()
        rec["approved_scope"] = "launch_missiles"
        errors = validate_record(rec)
        self.assertTrue(any("approved_scope" in e for e in errors), errors)

    def test_blocks_missing_rollback(self):
        rec = _ok_approval()
        rec["rollback_command"] = ""
        errors = validate_record(rec)
        self.assertTrue(any("rollback_command" in e for e in errors), errors)

    def test_blocks_duplicate_id(self):
        a = _ok_approval()
        b = _ok_approval()
        errors = validate_records({"records": [a, b]})
        self.assertTrue(any("duplicate" in e for e in errors), errors)

    def test_blocks_short_reason(self):
        rec = _ok_approval()
        rec["reason"] = "ok"
        errors = validate_record(rec)
        self.assertTrue(any("reason" in e for e in errors), errors)


if __name__ == "__main__":
    unittest.main()