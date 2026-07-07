import copy
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "agent_runtime_plans" / "hermes_pilot" / "provider_matrix.json"

import sys
sys.path.insert(0, str(ROOT / "provider_quota_monitor"))
from snapshot import (  # noqa: E402
    NIM_KNOWN_BASELINE_RPM,
    SNAPSHOT_STATUS_OK,
    SNAPSHOT_STATUS_STALE,
    block_decision,
    is_chain_blocked,
    snapshot_from_matrix,
    validate_snapshot,
)


def _filled_snapshot_ok() -> dict:
    snap = snapshot_from_matrix(json.loads(MATRIX.read_text(encoding="utf-8")), source="manual")
    for e in snap["entries"]:
        e["status"] = SNAPSHOT_STATUS_OK
        e["rpm"] = 30
        if e["provider"] == "google_ai_studio_free":
            e["note"] = "AI Studio project-level RPM inspected"
        elif e["provider"] == "nvidia_nim_free":
            e["note"] = "measured live; 40 RPM baseline not guaranteed"
            e["guaranteed"] = False
        elif e["provider"] == "selfhost_recovered_node":
            e["note"] = "bounded by recovered hardware"
    return snap


class ProviderQuotaMonitorTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matrix = json.loads(MATRIX.read_text(encoding="utf-8"))

    def test_snapshot_template_validates(self):
        snap = snapshot_from_matrix(self.matrix)
        # Validation passes structurally (status=stale allowed).
        self.assertEqual(validate_snapshot(snap), [])

    def test_snapshot_entries_for_all_three_providers(self):
        snap = snapshot_from_matrix(self.matrix)
        ids = {e["provider"] for e in snap["entries"]}
        self.assertEqual(ids, {"google_ai_studio_free", "nvidia_nim_free", "selfhost_recovered_node"})

    def test_chain_blocked_when_missing_snapshot(self):
        self.assertTrue(is_chain_blocked(None))
        self.assertTrue(is_chain_blocked({}))
        self.assertTrue(is_chain_blocked({"entries": []}))

    def test_chain_blocked_when_stale_entries(self):
        snap = snapshot_from_matrix(self.matrix)
        self.assertTrue(is_chain_blocked(snap))

    def test_chain_unblocked_when_all_ok(self):
        snap = _filled_snapshot_ok()
        self.assertFalse(is_chain_blocked(snap))

    def test_block_decision_missing_snapshot_reports_missing(self):
        decision = block_decision(None)
        self.assertTrue(decision["blocked"])
        self.assertEqual(decision["reason"], "missing_snapshot")

    def test_block_decision_stale_reports_stale(self):
        snap = snapshot_from_matrix(self.matrix)
        decision = block_decision(snap)
        self.assertTrue(decision["blocked"])
        self.assertEqual(decision["reason"], "stale_or_missing_quota")

    def test_block_decision_ok_reports_not_blocked(self):
        snap = _filled_snapshot_ok()
        decision = block_decision(snap)
        self.assertFalse(decision["blocked"])
        self.assertEqual(decision["reason"], "ok")

    def test_nim_guaranteed_true_rejected(self):
        snap = _filled_snapshot_ok()
        nim = next(e for e in snap["entries"] if e["provider"] == "nvidia_nim_free")
        nim["guaranteed"] = True
        errors = validate_snapshot(snap)
        self.assertTrue(any("guaranteed" in e for e in errors), errors)

    def test_google_without_ai_studio_note_rejected(self):
        snap = _filled_snapshot_ok()
        g = next(e for e in snap["entries"] if e["provider"] == "google_ai_studio_free")
        g["note"] = "measured by hand without platform reference"
        errors = validate_snapshot(snap)
        self.assertTrue(any("AI Studio" in e or "project" in e for e in errors), errors)

    def test_invalid_status_rejected(self):
        snap = _filled_snapshot_ok()
        snap["entries"][0]["status"] = "purple"
        errors = validate_snapshot(snap)
        self.assertTrue(any("status must be" in e for e in errors), errors)

    def test_missing_required_field_rejected(self):
        snap = _filled_snapshot_ok()
        del snap["entries"][0]["checked_at"]
        errors = validate_snapshot(snap)
        self.assertTrue(any("missing fields" in e for e in errors), errors)

    def test_nim_baseline_constant(self):
        self.assertEqual(NIM_KNOWN_BASELINE_RPM, 40)


if __name__ == "__main__":
    unittest.main()
