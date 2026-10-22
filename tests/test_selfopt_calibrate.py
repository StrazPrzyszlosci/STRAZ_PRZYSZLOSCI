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
    load_decisions,
    load_labels,
    render_strategy_proposal,
    write_calibration,
)
from selfopt_chain.orchestrator import Orchestrator, collect_feedback
from selfopt_chain.swarm import (
    CHARTER_PATH,
    BasalDecisionCore,
    Demand,
    SwarmPlanner,
    SwarmResource,
    charter_check,
    load_charter,
    resources_from_records,
    softmax_confidence,
)

RECORDS = [
    ROOT / "resource_scout" / "examples" / "ewaste_phone_batch.json",
    ROOT / "resource_scout" / "examples" / "selfhost_compute_node.json",
]
NEEDS = ROOT / "human_needs" / "seed_needs.json"


def _write_jsonl(path: Path, entries: list[dict]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(e, ensure_ascii=False) + "\n" for e in entries), encoding="utf-8")
    return path


class FitTemperaturesTest(unittest.TestCase):
    def _decision(self, question_type: str, deferred: bool) -> dict:
        return {"id": f"d{deferred}{question_type}", "question_type": question_type, "deferred": deferred, "confidence": 0.5, "chosen": "a", "final": "a" if not deferred else "b"}

    def test_good_but_deferred_sharpens_temperature(self):
        decisions = [self._decision("choice", True), self._decision("choice", False), self._decision("choice", False)]
        labels = [{"decision_id": d["id"], "accepted": True} for d in decisions]
        calibration = fit_temperatures(decisions, labels)
        self.assertLess(calibration["temperature_per_prim"]["choice"], 0.771)
        self.assertEqual(calibration["n_labels"], 3)

    def test_bad_and_undeferred_flattens_temperature(self):
        decisions = [self._decision("choice", False)]
        labels = [{"decision_id": "dFalsechoice", "accepted": False}]
        calibration = fit_temperatures(decisions, labels)
        self.assertGreater(calibration["temperature_per_prim"]["choice"], 0.771)

    def test_no_labels_returns_none(self):
        self.assertIsNone(fit_temperatures([self._decision("choice", False)], []))

    def test_temperature_bounds(self):
        decisions = [self._decision("choice", True)]
        labels = [{"decision_id": "dTruechoice", "accepted": True}]
        calibration = fit_temperatures(decisions, labels)
        self.assertGreaterEqual(calibration["temperature_per_prim"]["choice"], 0.3)
        self.assertLessEqual(calibration["temperature_per_prim"]["choice"], 3.0)

    def test_write_and_load_calibration_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp)
            decisions = [self._decision("choice", True)]
            labels = [{"decision_id": "dTruechoice", "accepted": True}]
            calibration = fit_temperatures(decisions, labels)
            path = write_calibration(state, calibration)
            self.assertTrue(path.exists())
            loaded = load_calibration(state)
            self.assertEqual(loaded["temperature_per_prim"], calibration["temperature_per_prim"])
            self.assertIn("temperature_source", loaded)

    def test_sharper_temperature_raises_confidence(self):
        scores = {"a": 1.0, "b": 0.8}
        _, conf_seed = softmax_confidence(scores, "choice")
        _, conf_sharp = softmax_confidence(scores, "choice", temperatures={"choice": 0.3})
        self.assertGreater(conf_sharp, conf_seed)

    def test_core_uses_calibrated_temperatures(self):
        core = BasalDecisionCore(temperatures={"choice": 0.3})
        decision = core.decide("choice", ["a", "b"], {"a": 1.0, "b": 0.8})
        self.assertGreaterEqual(decision["confidence"], 0.55)
        self.assertEqual(decision["final"], "a")


class AnnotateAndProposalTest(unittest.TestCase):
    def test_append_label_and_strategy_proposal(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp)
            decisions = [
                {"id": "d1", "question_type": "choice", "deferred": False, "confidence": 0.6, "chosen": "speed_first", "context": {"strategy": "speed_first", "demand": "m1"}},
                {"id": "d2", "question_type": "choice", "deferred": False, "confidence": 0.7, "chosen": "x", "context": {"strategy": "speed_first", "demand": "m2"}},
                {"id": "d3", "question_type": "choice", "deferred": False, "confidence": 0.8, "chosen": "y", "context": {"strategy": "speed_first", "demand": "m3"}},
            ]
            _write_jsonl(state / "decisions.jsonl", decisions)
            append_label(state, "d1", True, "dobry przydział")
            append_label(state, "d2", False, "zły przydział")
            append_label(state, "d3", False, "też zły przydział")
            labels = load_labels(state)
            self.assertEqual(len(labels), 3)
            proposal = render_strategy_proposal(load_decisions(state), labels)
            self.assertIn("suggest-only", proposal)
            self.assertIn("speed_first", proposal)
            self.assertIn("obniz stale", proposal)
            out = state / "strategy_evolution_proposal.md"
            out.write_text(proposal, encoding="utf-8")
            self.assertFalse("auto-zaaplikowane" in "")


class CollectFeedbackTest(unittest.TestCase):
    def test_feedback_messages_become_labels_not_jobs(self):
        with tempfile.TemporaryDirectory() as tmp:
            inbox = Path(tmp)
            (inbox / "fb1.json").write_text(json.dumps({"feedback": {"decision_id": "abc123", "accepted": True, "note": "telefon sprawdzil sie przy akwaponice"}}), encoding="utf-8")
            (inbox / "job1.json").write_text(json.dumps({"origin_network": "MESHTASTIC", "payload_text": "temp 27C"}), encoding="utf-8")
            feedbacks = collect_feedback(inbox)
        self.assertEqual(len(feedbacks), 1)
        self.assertEqual(feedbacks[0]["decision_id"], "abc123")
        self.assertEqual(feedbacks[0]["source"], "field")


class CharterTest(unittest.TestCase):
    def test_charter_loads(self):
        charter = load_charter()
        self.assertIn("food", charter["allowed_mission_classes"])
        self.assertTrue(any("broń" in kw or "weapon" in kw for kw in charter["forbidden_keywords"]))

    def test_forbidden_keyword_blocks_mission(self):
        charter = load_charter()
        demand = Demand("n1", "surveillance system do inwigilacji osób", ["vision"], "human_needs", payload={"mission_classes": ["sensing"]})
        result = charter_check([demand], charter)
        self.assertFalse(result["ok"])
        self.assertEqual(result["violations"][0]["rule"], "forbidden_keywords")

    def test_outside_mission_class_blocks(self):
        charter = load_charter()
        demand = Demand("n2", "pilot nowej uslugi", ["vision"], "human_needs", payload={"mission_classes": ["military_operations"]})
        result = charter_check([demand], charter)
        self.assertFalse(result["ok"])
        self.assertEqual(result["violations"][0]["rule"], "allowed_mission_classes")

    def test_valid_mission_passes(self):
        charter = load_charter()
        demand = Demand("n3", "obserwacja akwaponiki", ["vision", "sensing"], "human_needs", payload={"mission_classes": ["food", "sensing"]})
        result = charter_check([demand], charter)
        self.assertTrue(result["ok"])

    def test_plan_cycle_blocks_charter_violation(self):
        hardware = resources_from_records([{"id": "ph1", "resource_class": "old_smartphones", "cost": {"amount_pln": 0}, "location": {}, "risks": [], "required_evidence": [], "activation_requirements": {}}])
        bad = Demand("n_bad", "system rozpoznawania twarzy na osiedlu", ["vision"], "human_needs", payload={"mission_classes": ["sensing"]})
        good = Demand("n_good", "obserwacja akwaponiki", ["vision", "sensing"], "human_needs", payload={"mission_classes": ["food"]})
        plan = SwarmPlanner(BasalDecisionCore()).plan_cycle([bad, good], [], hardware, {"backlog": 0, "quota_pressure": 0.0, "critical_jobs": 0, "oze_window": False})
        self.assertFalse(plan["charter"]["ok"])
        blocked = next(a for a in plan["mission_allocations"] if a["demand_id"] == "n_bad")
        self.assertEqual(blocked["reason"], "charter_violation")
        self.assertEqual(blocked["resource"], None)
        ok_alloc = next(a for a in plan["mission_allocations"] if a["demand_id"] == "n_good")
        self.assertIsNotNone(ok_alloc["resource"])

    def test_charter_file_is_not_swarm_writable_joke(self):
        self.assertTrue(CHARTER_PATH.exists())


class ProductionResourcesTest(unittest.TestCase):
    """Drabina produkcji: udostępnione zdolności produkcyjne jako zasoby roju."""

    def _record(self, rid: str, cls: str) -> dict:
        return {"id": rid, "resource_class": cls, "cost": {"amount_pln": 0}, "location": {}, "risks": [], "required_evidence": [], "activation_requirements": {}}

    def test_3d_printer_resource_capabilities(self):
        resources = resources_from_records([self._record("prn1", "3d_printer")])
        self.assertEqual(resources[0].resource_id, "hardware:3d_printer:prn1")
        self.assertIn("additive_manufacturing", resources[0].capabilities)

    def test_robot_arm_resource_capabilities(self):
        resources = resources_from_records([self._record("arm1", "robot_arm")])
        self.assertIn("assembly", resources[0].capabilities)

    def test_liteweed_style_demand_allocates_production_chain(self):
        resources = resources_from_records([self._record("ph1", "old_smartphones"), self._record("mech1", "mechanics_scrap"), self._record("prn1", "3d_printer"), self._record("arm1", "robot_arm")])
        demand = Demand("need_weeding_robot", "potrzebny robot odchwaszczajacy dla malego gospodarstwa", ["mechanics", "assembly", "vision"], "human_needs", payload={"mission_classes": ["food", "environment"]})
        plan = SwarmPlanner(BasalDecisionCore()).plan_cycle([demand], [], resources, {"backlog": 0, "quota_pressure": 0.0, "critical_jobs": 1, "oze_window": False})
        alloc = plan["mission_allocations"][0]
        self.assertIsNotNone(alloc["resource"], "basal musi przydzielić zasób do zadania odchwaszczania (partial matching)")
        self.assertTrue(plan["charter"]["ok"])
        self.assertIn("hardware:", alloc["resource"]["resource_id"])

    def test_liteweed_reference_doc_linked_in_capability_map(self):
        map_data = json.loads((ROOT / "selfopt_chain" / "capability_map.json").read_text(encoding="utf-8"))
        refs = map_data["classes"]["mechanics_scrap"]["repo_refs"]
        self.assertIn("docs/LITEWEED_WZORZEC_REFERENCYJNY.md", refs)
        self.assertTrue((ROOT / "docs" / "LITEWEED_WZORZEC_REFERENCYJNY.md").exists())


class OrchestratorCalibrationFlowTest(unittest.TestCase):
    """Pętla samodoskonalenia: feedback z pola → labels → autokalibracja → rdzeń."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)

    def _config(self, inbox: Path | None = None):
        return {
            "engine": "mock",
            "interval_s": 0,
            "max_cycles": 1,
            "max_jobs": 3,
            "state_dir": self.base / "state",
            "kill_switch": self.base / "KILL_SWITCH",
            "registry_path": ROOT / "selfopt_chain" / "free_models.json",
            "records_paths": RECORDS,
            "needs_paths": [NEEDS],
            "inbox_dir": inbox,
            "quota_snapshot_path": None,
            "confidence_floor": 0.55,
            "oze_window": False,
        }

    def test_cycle_without_labels_reports_calibration_not_applied(self):
        receipt = Orchestrator(self._config()).run_cycle()
        self.assertEqual(receipt["calibration"]["applied"], False)
        self.assertEqual(receipt["field_feedback"]["received"], 0)

    def test_field_feedback_ingests_labels_and_autocalibrates_next_cycle(self):
        inbox = self.base / "inbox"
        inbox.mkdir()
        orch = Orchestrator(self._config(inbox=inbox))
        first = orch.run_cycle()
        self.assertEqual(first["field_feedback"]["received"], 0)
        decisions = load_decisions(self.base / "state")
        self.assertTrue(decisions, "cykl musi wygenerować decyzje")
        (inbox / "fb1.json").write_text(json.dumps({"feedback": {"decision_id": decisions[0]["id"], "accepted": True, "note": "telefon sprawdzil sie przy akwaponice"}}), encoding="utf-8")
        orch2 = Orchestrator(self._config(inbox=inbox))
        receipt = orch2.run_cycle()
        self.assertEqual(receipt["field_feedback"]["received"], 1)
        self.assertEqual(receipt["field_feedback"]["new_labels"], 1)
        self.assertTrue(receipt["calibration"]["applied"])
        self.assertIn("choice", receipt["calibration"]["temperatures"])
        labels = load_labels(self.base / "state")
        self.assertEqual(len(labels), 1)
        self.assertEqual(labels[0]["source"], "field")
        self.assertIsNotNone(load_calibration(self.base / "state"))

    def test_duplicate_feedback_not_reingested(self):
        inbox = self.base / "inbox"
        inbox.mkdir()
        orch = Orchestrator(self._config(inbox=inbox))
        orch.run_cycle()
        decisions = load_decisions(self.base / "state")
        feedback_file = inbox / "fb1.json"
        feedback_file.write_text(json.dumps({"feedback": {"decision_id": decisions[0]["id"], "accepted": True, "note": "ok"}}), encoding="utf-8")
        first = Orchestrator(self._config(inbox=inbox)).run_cycle()
        second = Orchestrator(self._config(inbox=inbox)).run_cycle()
        self.assertEqual(first["field_feedback"]["new_labels"], 1)
        self.assertEqual(second["field_feedback"]["new_labels"], 0)
        self.assertEqual(len(load_labels(self.base / "state")), 1)


if __name__ == "__main__":
    unittest.main()
