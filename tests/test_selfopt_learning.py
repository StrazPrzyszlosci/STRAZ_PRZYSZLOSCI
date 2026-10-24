"""Odbiór T63: domknięcie uczenia z wyników i metryki skuteczności."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from selfopt_chain.calibrate import (
    append_label,
    fit_temperatures,
    load_calibration,
    write_calibration,
)
from selfopt_chain.metrics import measure
from selfopt_chain.swarm import BasalDecisionCore


def _decision(did, qtype, deferred, chosen):
    return {"id": did, "question_type": qtype, "deferred": deferred,
            "confidence": 0.6, "chosen": chosen, "final": chosen, "options": [chosen]}


class LearningLoopTest(unittest.TestCase):
    def test_label_changes_its_decision_type_calibration_only(self):
        decisions = [
            _decision("d-alloc", "allocation", False, "phone"),
            _decision("d-sel", "model_selection", False, "nvidia"),
        ]
        calibration = fit_temperatures(decisions, [{"decision_id": "d-alloc", "accepted": True}])
        self.assertIn("allocation", calibration["temperature_per_prim"])
        self.assertNotIn("model_selection", calibration["temperature_per_prim"], "etykieta alloc nie może kalibrować model_selection")

    def test_label_drives_next_decision_defer_threshold(self):
        decisions = [_decision("d-sel", "model_selection", True, "nvidia")]
        labels = [{"decision_id": "d-sel", "accepted": True}]
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp)
            calibration = fit_temperatures(decisions, labels)
            path = write_calibration(state, calibration)
            self.assertTrue(path.exists())
            loaded = load_calibration(state)
            self.assertEqual(loaded["temperature_per_prim"], calibration["temperature_per_prim"], "restart zachowuje kalibrację")
            core = BasalDecisionCore(temperatures=loaded["temperature_per_prim"])
            decision = core.decide("model_selection", ["a", "b"], {"a": 1.0, "b": 0.5}, default_option="a")
            self.assertGreaterEqual(decision["confidence"], 0.55)
            self.assertEqual(decision["final"], "a", "wyostrozona kalibracja czyni decyzje pewna")

    def test_reprocessing_same_labels_is_idempotent(self):
        decisions = [_decision("d-x", "strategy", False, "speed_first")]
        labels = [{"decision_id": "d-x", "accepted": False}]
        first = fit_temperatures(decisions, labels)
        second = fit_temperatures(decisions, labels)
        self.assertEqual(first["temperature_per_prim"], second["temperature_per_prim"],
                         "ponowne przetworzenie tych samych etykiet nie może dodawać pozornego uczenia")

    def test_missing_labels_returns_none_explicitly(self):
        self.assertIsNone(fit_temperatures([_decision("d-y", "strategy", False, "x")], []))

    def test_label_provenance_recorded(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp)
            (state / "decisions.jsonl").write_text(json.dumps(_decision("dec-1", "strategy", False, "x")) + "\n")
            label = append_label(state, "dec-1", True, "dobry wybór", source="operator")
            stored = json.loads((state / "labels.jsonl").read_text().splitlines()[0])
            self.assertEqual(stored["decision_id"], "dec-1")
            self.assertEqual(stored["source"], "operator")
            self.assertIn("ts", stored)


class EffectivenessMetricsTest(unittest.TestCase):
    def _state(self, root: Path):
        state = root / "state"
        (state / "runs").mkdir(parents=True)
        (state / "runs" / "r1").mkdir()
        (state / "runs" / "r1" / "run_receipt.json").write_text(json.dumps({"status": "ok", "human_accepted": True, "blocked": []}))
        queue = state / "evolution_queue" / "task_1"
        queue.mkdir(parents=True)
        (queue / "evolution_receipt.json").write_text(json.dumps({
            "executor": "direct_patch", "validation_ok": True, "security_ok": True,
            "execution_ok": True, "gate_ok": True, "latency_ms": 42000,
            "review": {"verdict": "pass"}}))
        (state / "evolution_index.json").write_text(json.dumps({"t1": {"attempts": 3}}))
        (state / "quota_ledger.json").write_text(json.dumps({"daily": {"m": 10}}))
        (state / "decisions.jsonl").write_text(json.dumps({"id": "d1"}) + "\n")
        (state / "labels.jsonl").write_text(json.dumps({"decision_id": "d1", "accepted": True}) + "\n")
        return state

    def test_report_discloses_evolution_effectiveness_and_missing_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = self._state(Path(tmp))
            report = measure(state)
            evo = report["evolution"]
            self.assertEqual(evo["receipts"], 1)
            self.assertEqual(evo["validated_artifacts"], 1)
            self.assertEqual(evo["validated_per_100_producer_calls"], 100.0)
            self.assertEqual(evo["positive_review_share"], 1.0)
            self.assertEqual(evo["duplicate_attempt_targets"], 1)
            self.assertEqual(evo["producer_calls"], 1)
            self.assertEqual(evo["avg_producer_latency_ms"], 42000)
            self.assertEqual(evo["published_proposals"], 0)
            self.assertIn("published", evo["missing_data"], "brak publikacji ma być jawny")
            self.assertEqual(report["useful_artifacts_per_100_attempts"], 10.0)
            self.assertEqual(report["feedback_coverage"], 1.0)
            self.assertEqual(report["human_acceptance_rate"], 1.0)

    def test_empty_state_reports_nulls_not_zeros(self):
        with tempfile.TemporaryDirectory() as tmp:
            empty = Path(tmp) / "empty"
            empty.mkdir()
            report = measure(empty)
            self.assertIsNone(report["human_acceptance_rate"])
            self.assertIsNone(report["useful_artifacts_per_100_attempts"])
            self.assertIsNone(report["evolution"]["positive_review_share"])
            self.assertEqual(report["evolution"]["receipts"], 0)


if __name__ == "__main__":
    unittest.main()
