import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from selfopt_chain.orchestrator import Orchestrator
from selfopt_chain.registry import load_registry
from selfopt_chain.swarm import (
    BasalDecisionCore,
    Demand,
    SwarmPlanner,
    SwarmResource,
    demand_from_need,
    exec_mode_scores,
    resources_from_models,
    resources_from_records,
    resource_score,
    softmax_confidence,
)

RECORDS = [
    ROOT / "resource_scout" / "examples" / "ewaste_phone_batch.json",
    ROOT / "resource_scout" / "examples" / "selfhost_compute_node.json",
]
NEEDS = ROOT / "human_needs" / "seed_needs.json"


def _records():
    out = []
    for p in RECORDS:
        out.extend(json.loads(p.read_text(encoding="utf-8"))["records"])
    return out


def _needs():
    return json.loads(NEEDS.read_text(encoding="utf-8"))["records"]


class SoftmaxConfidenceTest(unittest.TestCase):
    def test_higher_score_gets_higher_probability(self):
        probabilities, confidence = softmax_confidence({"a": 2.0, "b": 1.0})
        self.assertGreater(probabilities["a"], probabilities["b"])
        self.assertAlmostEqual(sum(probabilities.values()), 1.0, places=3)
        self.assertEqual(confidence, round(max(probabilities.values()), 4))

    def test_single_option_full_confidence(self):
        probabilities, confidence = softmax_confidence({"only": 0.3})
        self.assertEqual(confidence, 1.0)

    def test_option_count_buckets_do_not_crash(self):
        for n in (2, 10, 11, 25):
            scores = {f"o{i}": float(i) for i in range(n)}
            probabilities, _ = softmax_confidence(scores)
            self.assertAlmostEqual(sum(probabilities.values()), 1.0, places=2)


class BasalDecisionCoreTest(unittest.TestCase):
    def test_decision_format_and_log(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "decisions.jsonl"
            core = BasalDecisionCore(decision_log=log)
            decision = core.decide("choice", ["a", "b"], {"a": 3.0, "b": 0.5}, default_option="b", context={"cycle": 1})
            self.assertEqual(decision["group"], "swarm")
            self.assertEqual(decision["chosen"], "a")
            self.assertFalse(decision["deferred"])
            self.assertEqual(decision["final"], "a")
            self.assertEqual(decision["engine"], "builtin")
            entries = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len(entries), 1)
            for field in ("id", "question_type", "probabilities", "confidence", "confidence_floor", "deferred"):
                self.assertIn(field, entries[0])

    def test_low_confidence_defers_to_default(self):
        core = BasalDecisionCore(confidence_floor=0.99)
        decision = core.decide("choice", ["a", "b"], {"a": 1.1, "b": 1.0}, default_option="b")
        self.assertTrue(decision["deferred"])
        self.assertEqual(decision["final"], "b")
        self.assertEqual(decision["chosen"], "a")

    def test_missing_score_rejected(self):
        core = BasalDecisionCore()
        with self.assertRaises(ValueError):
            core.decide("choice", ["a", "b"], {"a": 1.0})

    def test_remote_engine_marker_via_env(self):
        with mock.patch.dict(os.environ, {"SELFOPT_BASAL_URL": "http://127.0.0.1:8000"}, clear=False):
            core = BasalDecisionCore()
            self.assertEqual(core.remote_url, "http://127.0.0.1:8000")
            decision = core.decide("choice", ["a"], {"a": 1.0})
            self.assertEqual(decision["engine"], "basal-serve")


class StrategyDecisionTest(unittest.TestCase):
    def _planner(self):
        return SwarmPlanner(BasalDecisionCore())

    def test_quota_pressure_favors_budget_strategies(self):
        plan_low = self._planner().decide_strategy({"quota_pressure": 0.0, "backlog": 2, "critical_jobs": 0, "oze_window": False})
        plan_high = self._planner().decide_strategy({"quota_pressure": 1.0, "backlog": 2, "critical_jobs": 0, "oze_window": False})
        self.assertIn(plan_low["chosen"], {"speed_first", "load_balance", "quota_preserve"})
        self.assertIn(plan_high["chosen"], {"load_balance", "quota_preserve"})

    def test_oze_window_favors_energy_oze(self):
        decision = self._planner().decide_strategy({"quota_pressure": 0.0, "backlog": 1, "critical_jobs": 0, "oze_window": True})
        self.assertEqual(decision["chosen"], "energy_oze")

    def test_critical_jobs_favor_quality_or_redundancy(self):
        decision = self._planner().decide_strategy({"quota_pressure": 0.0, "backlog": 1, "critical_jobs": 3, "oze_window": False})
        self.assertIn(decision["chosen"], {"quality_first", "redundancy"})

    def test_defer_falls_back_to_default_strategy(self):
        core = BasalDecisionCore(confidence_floor=0.999)
        planner = SwarmPlanner(core, default_strategy="speed_first")
        decision = planner.decide_strategy({"quota_pressure": 0.0, "backlog": 0, "critical_jobs": 0, "oze_window": False})
        self.assertTrue(decision["deferred"])
        self.assertEqual(decision["final"], "speed_first")


class ResourceScoringTest(unittest.TestCase):
    def _models(self):
        return resources_from_models(load_registry())

    def test_capability_mismatch_rejected(self):
        phone = SwarmResource("hardware:phone", "hardware", "telefon", ["vision", "sensing"])
        demand = Demand("d1", "mesh", ["mesh", "lora"], "test")
        self.assertLessEqual(resource_score(phone, demand, "speed_first", {}), -5.0)

    def test_exhausted_model_rejected(self):
        model = SwarmResource("model:x", "model", "x", ["text", "json"], rpd_budget=10, rpd_used=10)
        demand = Demand("d1", "procdev", ["text"], "test")
        self.assertLessEqual(resource_score(model, demand, "speed_first", {}), -5.0)

    def test_energy_oze_prefers_local(self):
        local = SwarmResource("hardware:selfhost", "hardware", "wezel", ["edge_compute"], energy_class="low_power_or_oze_preferred")
        remote = SwarmResource("model:cloud", "model", "cloud", ["edge_compute"], energy_class="external_provider")
        demand = Demand("d1", "obliczenia", ["edge_compute"], "test")
        s_local = resource_score(local, demand, "energy_oze", {})
        s_remote = resource_score(remote, demand, "energy_oze", {})
        self.assertGreater(s_local, s_remote)

    def test_load_balance_penalizes_reused_resource(self):
        model = SwarmResource("model:x", "model", "x", ["text"])
        demand = Demand("d1", "procdev", ["text"], "test")
        fresh = resource_score(model, demand, "load_balance", {})
        reused = resource_score(model, demand, "load_balance", {"model:x": 3})
        self.assertGreater(fresh, reused)


class DemandFromNeedTest(unittest.TestCase):
    def test_aquaponics_need_requires_vision_sensing(self):
        demand = demand_from_need(_needs()[0])
        self.assertEqual(demand.source, "human_needs")
        self.assertIn("vision", demand.required)
        self.assertIn("sensing", demand.required)

    def test_oze_required_raises_priority(self):
        demand = demand_from_need(_needs()[0])
        self.assertEqual(demand.priority, 2)

    def test_offline_knowledge_need_maps_to_local_inference(self):
        demand = demand_from_need(_needs()[1])
        self.assertIn("local_inference", demand.required)


class ExecModeTest(unittest.TestCase):
    def test_phone_sensing_prefers_device_profile(self):
        phone = SwarmResource("hardware:phone", "hardware", "telefon", ["vision", "sensing"])
        demand = Demand("d1", "obserwacja", ["vision", "sensing"], "test")
        decision = BasalDecisionCore().decide("choice", ["device_profile", "on_device_model", "cloud_chain"], exec_mode_scores(demand, phone), default_option="cloud_chain")
        self.assertEqual(decision["chosen"], "device_profile")

    def test_selfhost_prefers_on_device_model(self):
        node = SwarmResource("hardware:selfhost", "hardware", "wezel", ["local_inference", "edge_compute"])
        demand = Demand("d1", "offline", ["local_inference"], "test")
        decision = BasalDecisionCore().decide("choice", ["device_profile", "on_device_model", "cloud_chain"], exec_mode_scores(demand, node), default_option="cloud_chain")
        self.assertEqual(decision["chosen"], "on_device_model")

    def test_model_resource_prefers_cloud_chain(self):
        model = SwarmResource("model:x", "model", "model", ["text", "json"])
        demand = Demand("d1", "draft", ["text"], "test")
        decision = BasalDecisionCore().decide("choice", ["device_profile", "on_device_model", "cloud_chain"], exec_mode_scores(demand, model), default_option="cloud_chain")
        self.assertEqual(decision["chosen"], "cloud_chain")


class PlanCycleTest(unittest.TestCase):
    """Przykład operatora: telefon + selfhost w zasobach -> basal przydziela sprzęt do zapotrzebowań."""

    def test_phone_allocated_to_aquaponics_need(self):
        hardware = resources_from_records(_records())
        models = resources_from_models(load_registry())
        mission = [demand_from_need(r) for r in _needs()]
        procdev = [Demand("procdev_x", "procdev", ["text", "json"], "resource_scout")]
        planner = SwarmPlanner(BasalDecisionCore())
        plan = planner.plan_cycle(mission, procdev, hardware + models, {"backlog": 1, "quota_pressure": 0.0, "critical_jobs": 1, "oze_window": False}, max_jobs=3)
        aq = next(a for a in plan["mission_allocations"] if "aquaponics" in a["demand_id"])
        self.assertIsNotNone(aq["resource"], "basal musi przydzielić zasób do zapotrzebowania akwaponiki")
        self.assertIn("phone", aq["resource"]["resource_id"])
        self.assertEqual(aq["exec_mode"], "device_profile")
        self.assertIn("procdev_x", plan["execution_order"])
        self.assertFalse(plan["auto_applied"])

    def test_many_decisions_per_cycle(self):
        hardware = resources_from_records(_records())
        models = resources_from_models(load_registry())
        mission = [demand_from_need(r) for r in _needs()]
        procdev = [Demand(f"procdev_{i}", "procdev", ["text"], "resource_scout") for i in range(3)]
        core = BasalDecisionCore()
        planner = SwarmPlanner(core)
        plan = planner.plan_cycle(mission, procdev, hardware + models, {"backlog": 3, "quota_pressure": 0.0, "critical_jobs": 0, "oze_window": False}, max_jobs=2)
        self.assertEqual(plan["strategy_decision"]["chosen"] is not None, True)
        self.assertEqual(len(plan["mission_allocations"]), len(mission))
        self.assertEqual(len(plan["execution_order"]), 2)
        self.assertGreaterEqual(plan["decisions_count"], 1 + len(mission) * 2 + 1)

    def test_no_capable_resource_recorded_not_faked(self):
        models = resources_from_models(load_registry())
        mission = [Demand("need_mesh", "lacznosc mesh", ["mesh", "lora"], "human_needs")]
        core = BasalDecisionCore()
        plan = SwarmPlanner(core).plan_cycle(mission, [], models, {"backlog": 0, "quota_pressure": 0.0, "critical_jobs": 0, "oze_window": False})
        alloc = plan["mission_allocations"][0]
        self.assertIsNone(alloc["resource"])
        self.assertEqual(alloc["reason"], "no_capable_resource")


class OrchestratorSwarmIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)

    def _config(self):
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
            "inbox_dir": None,
            "quota_snapshot_path": None,
            "confidence_floor": 0.55,
            "oze_window": False,
        }

    def test_cycle_contains_swarm_plan_and_allocations(self):
        orch = Orchestrator(self._config())
        receipt = orch.run_cycle()
        self.assertIn("swarm", receipt)
        swarm = receipt["swarm"]
        self.assertIn(swarm["strategy"], set(["speed_first", "quality_first", "load_balance", "quota_preserve", "energy_oze", "redundancy", "queue_when_busy"]))
        self.assertGreaterEqual(swarm["mission_allocations"], 1)
        self.assertGreaterEqual(swarm["decisions_count"], 3)
        plan_path = self.base / "state" / "swarm_plans" / "cycle_1.json"
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        self.assertFalse(plan["auto_applied"])
        aq = next(a for a in plan["mission_allocations"] if "aquaponics" in a["demand_id"])
        self.assertIn("phone", aq["resource"]["resource_id"])
        alloc_md = (self.base / "state" / "swarm_plans" / "cycle_1_allocations.md").read_text(encoding="utf-8")
        self.assertIn("suggest-only", alloc_md)
        self.assertIn("PROPOZYCJĄ", alloc_md)
        self.assertEqual(len(receipt["jobs_run"]), 2)
        log = (self.base / "state" / "decisions.jsonl").read_text(encoding="utf-8").strip().splitlines()
        self.assertGreaterEqual(len(log), 5)
        entry = json.loads(log[0])
        self.assertEqual(entry["group"], "swarm")

    def test_jobs_still_execute_in_swarm_order(self):
        orch = Orchestrator(self._config())
        receipt = orch.run_cycle()
        planned_order = receipt["swarm"]["execution_order"]
        executed_ids = [j["job_id"] for j in receipt["jobs_run"]]
        self.assertEqual(sorted(executed_ids), sorted(planned_order))


if __name__ == "__main__":
    unittest.main()
