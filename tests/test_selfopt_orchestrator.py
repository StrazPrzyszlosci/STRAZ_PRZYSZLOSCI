import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from selfopt_chain.orchestrator import (
    BOOTSTRAP_RECORD,
    Orchestrator,
    OrchestratorState,
    collect_jobs,
    fingerprint,
    load_capability_map,
    match_capability,
    quota_gate,
)
from selfopt_chain.registry import load_registry

RECORDS = [
    ROOT / "resource_scout" / "examples" / "ewaste_phone_batch.json",
    ROOT / "resource_scout" / "examples" / "selfhost_compute_node.json",
]


def _config(tmp: Path, engine: str = "mock", **kw) -> dict:
    return {
        "engine": engine,
        "interval_s": 0,
        "max_cycles": 1,
        "max_jobs": 3,
        "state_dir": tmp / "state",
        "kill_switch": tmp / "KILL_SWITCH",
        "registry_path": ROOT / "selfopt_chain" / "free_models.json",
        "records_paths": [RECORDS[0], RECORDS[1]],
        "inbox_dir": None,
        "quota_snapshot_path": None,
        **kw,
    }


class CapabilityMapTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.map_data = load_capability_map()

    def test_default_entry_exists(self):
        self.assertIn("default", self.map_data["classes"])

    def test_all_repo_refs_exist_on_disk(self):
        for cls, entry in self.map_data["classes"].items():
            for ref in entry["repo_refs"]:
                self.assertTrue((ROOT / ref).exists(), f"{cls}: brak na dysku {ref}")

    def test_scout_example_classes_are_covered(self):
        for path in RECORDS:
            data = json.loads(path.read_text(encoding="utf-8"))
            for record in data["records"]:
                matched = match_capability(record["resource_class"], self.map_data)
                self.assertIn("capability", matched)
                self.assertTrue(matched["repo_refs"])

    def test_unknown_class_falls_back_to_default(self):
        matched = match_capability("nieznany_sprzet", self.map_data)
        self.assertEqual(matched["capability"], "unknown_resource_triage")


class QuotaGateTest(unittest.TestCase):
    def test_mock_engine_bypasses_gate(self):
        decision = quota_gate("mock", None)
        self.assertTrue(decision["allowed"])

    def test_free_api_blocked_without_snapshot(self):
        decision = quota_gate("free-api", ROOT / "nie_istnieje.json")
        self.assertFalse(decision["allowed"])
        self.assertIn("missing_snapshot", decision["reason"])

    def test_free_api_blocked_when_snapshot_stale(self):
        with tempfile.TemporaryDirectory() as tmp:
            snapshot_path = Path(tmp) / "quota_snapshot.json"
            snapshot_path.write_text(json.dumps({
                "entries": [{"provider": "groq_free", "model": "x", "source": "manual",
                             "checked_at": "2026-10-20T00:00:00+00:00", "status": "stale"}]
            }), encoding="utf-8")
            decision = quota_gate("free-api", snapshot_path)
        self.assertFalse(decision["allowed"])
        self.assertIn("quota_snapshot_blocked", decision["reason"])

    def test_free_api_allowed_with_ok_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            snapshot_path = Path(tmp) / "quota_snapshot.json"
            entries = [
                {"provider": pid, "model": "m", "source": "manual",
                 "checked_at": "2026-10-20T00:00:00+00:00", "status": "ok",
                 "rpm": 30, "tpm": None, "rpd": 1000, "guaranteed": False,
                 "note": "" if pid != "google_ai_studio_free" else "verified in AI Studio project limits"}
                for pid in ("groq_free", "google_ai_studio_free")
            ]
            snapshot_path.write_text(json.dumps({"entries": entries}), encoding="utf-8")
            decision = quota_gate("free-api", snapshot_path)
        self.assertTrue(decision["allowed"], decision)


class StateAndBudgetTest(unittest.TestCase):
    def test_budgeted_models_drop_exhausted(self):
        state = OrchestratorState(Path(tempfile.mkdtemp()))
        models = load_registry()
        target = models[0]["model_id"]
        state.data["daily_calls"][target] = models[0]["rpd_seed"]
        view = state.budgeted_models(models)
        self.assertNotIn(target, [m["model_id"] for m in view])
        other = [m for m in models if m["model_id"] != target][0]
        state.data["daily_calls"][other["model_id"]] = 10
        view = state.budgeted_models(models)
        view_other = next(m for m in view if m["model_id"] == other["model_id"])
        self.assertEqual(view_other["rpd_seed"], other["rpd_seed"] - 10)

    def test_date_rollover_resets_daily_calls(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = OrchestratorState(Path(tmp))
            state.data["date"] = "2020-01-01"
            state.data["daily_calls"]["model-x"] = 100
            state.save()
            fresh = OrchestratorState(Path(tmp))
            fresh.load()
            self.assertEqual(fresh.data["daily_calls"], {})

    def test_dedup_by_fingerprint(self):
        state = OrchestratorState(Path(tempfile.mkdtemp()))
        fp = fingerprint(BOOTSTRAP_RECORD)
        self.assertFalse(state.already_processed(fp))
        state.mark_processed(fp, BOOTSTRAP_RECORD["id"])
        self.assertTrue(state.already_processed(fp))


class CollectJobsTest(unittest.TestCase):
    def test_collects_records_from_scout_examples(self):
        jobs = collect_jobs(RECORDS, None)
        self.assertEqual(len(jobs), 2)
        sources = {j.source for j in jobs}
        self.assertEqual(sources, {"resource_scout"})

    def test_collects_inbox_messages(self):
        with tempfile.TemporaryDirectory() as tmp:
            inbox = Path(tmp)
            (inbox / "msg_001.json").write_text(json.dumps({
                "origin_network": "MESHTASTIC",
                "payload_text": "[EDGE→HUB] temp poza pasmem przez 3h"
            }), encoding="utf-8")
            jobs = collect_jobs([], inbox)
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].source, "lora_inbox")
        self.assertEqual(jobs[0].record["resource_class"], "field_feedback")


class OrchestratorCycleTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)

    def test_once_cycle_processes_records_and_writes_drafts(self):
        orch = Orchestrator(_config(self.base))
        receipt = orch.run_cycle()
        self.assertEqual(receipt["quota_gate"]["allowed"], True)
        self.assertEqual(receipt["jobs_status"], "ok")
        self.assertEqual(len(receipt["jobs_run"]), 2)
        drafts = sorted((self.base / "state" / "procdev_queue").glob("*.md"))
        self.assertEqual(len(drafts), 2)
        phone_draft = (self.base / "state" / "procdev_queue" / "ewaste_phone_batch_local_001.md").read_text(encoding="utf-8")
        self.assertIn("edge_sensing_and_control", phone_draft)
        self.assertIn("PROJEKTY/06_smartfony_jako_sterowniki.md", phone_draft)
        self.assertIn("auto_applied: false", phone_draft)
        self.assertIn("phone-aquaponics-observer", phone_draft)
        compute_draft = (self.base / "state" / "procdev_queue" / "selfhost_compute_node_recovered_001.md").read_text(encoding="utf-8")
        self.assertIn("sovereign_local_inference", compute_draft)
        for job in receipt["jobs_run"]:
            self.assertTrue(Path(job["procdev_draft"]).exists())
            self.assertEqual(job["rc"], 0)

    def test_second_cycle_dedups_processed_jobs(self):
        orch = Orchestrator(_config(self.base))
        first = orch.run_cycle()
        self.assertEqual(len(first["jobs_run"]), 2)
        second = orch.run_cycle()
        self.assertEqual(second["jobs_status"], "no_new_jobs")
        self.assertEqual(second["jobs_run"], [])
        self.assertEqual(second["jobs_skipped_processed"], 2)

    def test_free_api_cycle_blocked_by_quota_gate(self):
        config = _config(self.base, engine="free-api", quota_snapshot_path=self.base / "brak.json")
        orch = Orchestrator(config)
        receipt = orch.run_cycle()
        self.assertFalse(receipt["quota_gate"]["allowed"])
        self.assertEqual(receipt["jobs_status"], "skipped_quota_gate")
        self.assertEqual(receipt["jobs_run"], [])

    def test_daily_budget_exhausted_skips_jobs(self):
        state_dir = self.base / "state"
        state_dir.mkdir(parents=True)
        models = load_registry()
        state = OrchestratorState(state_dir)
        for m in models:
            state.data["daily_calls"][m["model_id"]] = m["rpd_seed"]
        state.save()
        orch = Orchestrator(_config(self.base))
        receipt = orch.run_cycle()
        self.assertEqual(receipt["jobs_status"], "daily_budget_exhausted")
        self.assertEqual(receipt["jobs_run"], [])

    def test_empty_sources_run_bootstrap_demo(self):
        config = _config(self.base)
        config["records_paths"] = [self.base / "nie_ma.json"]
        receipt = Orchestrator(config).run_cycle()
        self.assertEqual(receipt["jobs_status"], "bootstrap_demo")
        self.assertEqual(len(receipt["jobs_run"]), 1)
        draft = (self.base / "state" / "procdev_queue" / "selfopt_bootstrap_001.md").read_text(encoding="utf-8")
        self.assertIn("bootstrap_demo", draft)

    def test_kill_switch_stops_daemon_before_first_cycle(self):
        kill = self.base / "KILL_SWITCH"
        kill.write_text("stop", encoding="utf-8")
        config = _config(self.base)
        config["max_cycles"] = 5
        orch = Orchestrator(config)
        rc = orch.run()
        self.assertEqual(rc, 0)
        stopped = json.loads((self.base / "state" / "stopped.json").read_text(encoding="utf-8"))
        self.assertEqual(stopped["reason"], "kill_switch")
        self.assertEqual(stopped["cycles_done"], 0)

    def test_bounded_daemon_runs_two_cycles(self):
        config = _config(self.base)
        config["max_cycles"] = 2
        config["interval_s"] = 0
        orch = Orchestrator(config)
        rc = orch.run()
        self.assertEqual(rc, 0)
        cycles = sorted((self.base / "state" / "cycles").glob("cycle_*.json"))
        self.assertEqual(len(cycles), 2)
        second = json.loads((self.base / "state" / "cycles" / "cycle_2.json").read_text(encoding="utf-8"))
        self.assertEqual(second["jobs_status"], "no_new_jobs")

    def test_cycle_receipts_are_suggest_only(self):
        receipt = Orchestrator(_config(self.base)).run_cycle()
        self.assertFalse(receipt["auto_applied"])
        self.assertEqual(receipt["policy"], "suggest-only")
        run_receipt = json.loads((self.base / "state" / "runs" / "cycle_1_ewaste_phone_batch_local_001" / "run_receipt.json").read_text(encoding="utf-8"))
        self.assertFalse(run_receipt["auto_applied"])
        self.assertTrue((self.base / "state" / "runs" / "cycle_1_ewaste_phone_batch_local_001" / "final_outputs.json").exists())


if __name__ == "__main__":
    unittest.main()
