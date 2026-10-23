import io
import json
import os
import sys
import tempfile
import unittest
import urllib.request
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from selfopt_chain.evolver import (
    EvolutionLoop,
    collect_evolution_tasks,
    decide_parallel_mode,
    _parse_handoff_tasks,
    _parse_targets,
)
from selfopt_chain.hermes_worker import HermesWorker, SecurityGate, parse_stream_json_output
from selfopt_chain.omniroute import FreeOnlyPolicy, OmniRouteAdapter, OmniRouteEngine
from selfopt_chain.engine import FreeApiEngine
from selfopt_chain.registry import load_registry
from selfopt_chain.swarm import BasalDecisionCore, resources_from_records, load_charter
from selfopt_chain.orchestrator import load_capability_map, collect_jobs



class AuditFixesTest(unittest.TestCase):
    """Testy napraw z audytu T48–T52 (P0/P1)."""

    def test_chain_passes_context_review_sees_draft(self):
        import selfopt_chain.run_loop as rl
        from selfopt_chain.swarm import BasalDecisionCore
        from pathlib import Path as P
        captured = {}

        class RecordingEngine:
            def __init__(self, models):
                self.calls = []
            def complete(self, task, model_id, prompt):
                captured[task.get("task_id")] = prompt
                return {"ok": True, "output": f"out:{task.get('task_id')}", "model_id": model_id, "provider": "p", "latency_ms": 1, "tokens_est": 1}

        chain = json.loads((ROOT / "selfopt_chain" / "examples" / "chain_resource_triage.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            chain_path = P(tmp) / "chain.json"
            chain_path.write_text(json.dumps(chain), encoding="utf-8")
            rl.ChainRunner  # sanity
            import unittest as _u
            original = rl.ChainRunner
            class PatchedRunner(original):
                def __init__(self, models, engine_name, quota_snapshot, tracer, spool=None, decision_core=None, **runner_options):
                    super().__init__(models, engine_name, quota_snapshot, tracer, spool, decision_core, **runner_options)
                    self.engine = RecordingEngine(models)
            with _u.mock.patch.object(rl, "ChainRunner", PatchedRunner):
                rc = rl.run_chain(chain_path, P(tmp) / "out", "mock", ROOT / "selfopt_chain" / "free_models.json", None, None)
        self.assertEqual(rc, 0)
        self.assertIn("out:classify", captured["extract"], "extract ma widzieć wynik classify")
        self.assertIn("out:draft", captured["review"], "review ma widzieć draft")

    def test_degraded_status_on_partial_failure(self):
        import selfopt_chain.run_loop as rl
        from pathlib import Path as P
        chain = json.loads((ROOT / "selfopt_chain" / "examples" / "chain_resource_triage.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            chain_path = P(tmp) / "chain.json"
            chain_path.write_text(json.dumps(chain), encoding="utf-8")
            import unittest as _u
            original = rl.ChainRunner
            class FailingEngineRunner(original):
                def __init__(self, models, engine_name, quota_snapshot, tracer, spool=None, decision_core=None, **runner_options):
                    super().__init__(models, engine_name, quota_snapshot, tracer, spool, decision_core, **runner_options)
                    from selfopt_chain.engine import MockEngine
                    self.engine = MockEngine(models, fail_kinds={"extract"})
            with _u.mock.patch.object(rl, "ChainRunner", FailingEngineRunner):
                rc = rl.run_chain(chain_path, P(tmp) / "out", "mock", ROOT / "selfopt_chain" / "free_models.json", None, None)
            receipt = json.loads((P(tmp) / "out" / "run_receipt.json").read_text(encoding="utf-8"))
        self.assertEqual(rc, 1)
        self.assertIn("degraded", receipt["status"])

    def test_record_calls_counts_calls_not_models(self):
        from selfopt_chain.orchestrator import OrchestratorState
        state = OrchestratorState(Path(tempfile.mkdtemp()))
        state.record_calls({"model-a": 5, "model-b": 0})
        state.record_calls({"model-a": 3})
        self.assertEqual(state.data["daily_calls"]["model-a"], 8)
        self.assertEqual(state.data["daily_calls"].get("model-b", 0), 0)

    def test_charter_word_boundaries_no_false_positives(self):
        charter = load_charter()
        ok_text = "Wytwarzanie obudow z odzysku oraz bronowanie sali warsztatowej dla spolecznosci"
        bad = SecurityGate()
        from selfopt_chain.swarm import Demand as D, charter_check
        good = D("n1", ok_text, ["assembly"], "human_needs", payload={"mission_classes": ["production", "food"]})
        self.assertTrue(charter_check([good], charter)["ok"], "wytwarzanie/bronowanie NIE moga byc blokowane")
        weapon = D("n2", "potrzebna broń i amunicja do testow", [], "human_needs", payload={"mission_classes": ["safety"]})
        self.assertFalse(charter_check([weapon], charter)["ok"], "broń musi byc zablokowana")
        face = D("n3", "system rozpoznawania twarzy na osiedlu", ["vision"], "human_needs", payload={"mission_classes": ["sensing"]})
        self.assertFalse(charter_check([face], charter)["ok"])

    def test_private_inbox_job_privacy_end_to_end(self):
        with tempfile.TemporaryDirectory() as tmp:
            inbox = Path(tmp)
            (inbox / "m1.json").write_text(json.dumps({"origin_network": "MESHTASTIC", "payload_text": "[EDGE→HUB] temp 27C"}), encoding="utf-8")
            jobs = collect_jobs([], inbox)
        from selfopt_chain.orchestrator import build_chain_def
        self.assertEqual([node["privacy"] for node in build_chain_def(jobs[0])["nodes"]], ["private"] * 4)

    def test_engine_local_style_uses_env_base(self):
        fake = {"choices": [{"message": {"content": "lokalna odpowiedz"}}]}
        with mock.patch.dict(os.environ, {"SELFOPT_NETWORK": "1", "SELFHOST_AI_BASE_URL": "http://127.0.0.1:9999"}, clear=False), \
                mock.patch.object(urllib.request, "urlopen", return_value=io.BytesIO(json.dumps(fake).encode("utf-8"))) as urlopen:
            engine = FreeApiEngine(load_registry())
            result = engine.complete({"privacy": "private"}, "small-instruct", "prompt")
        self.assertTrue(result["ok"])
        self.assertIn("127.0.0.1:9999", urlopen.call_args[0][0].full_url)
        self.assertNotIn("Authorization", urlopen.call_args[0][0].headers)

    def test_engine_local_style_fail_closed_without_env(self):
        env = {"SELFOPT_NETWORK": "1"}
        with mock.patch.dict(os.environ, env, clear=False), \
                mock.patch.dict("os.environ", {"SELFHOST_AI_BASE_URL": ""}, clear=False):
            engine = FreeApiEngine(load_registry())
            result = engine.complete({"privacy": "private"}, "small-instruct", "prompt")
        self.assertFalse(result["ok"])
        self.assertIn(result["error_class"], {"missing_secret", "connection_error"})

    def test_gate_fail_closed_on_zero_artifacts(self):
        gate = SecurityGate()
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "output.json").write_text("{}", encoding="utf-8")
            report = gate.inspect_tree(Path(tmp), skip={"output.json"})
        self.assertFalse(report["ok"])
        self.assertTrue(report["blocked"])
        self.assertEqual(report["scanned_files"], 0)

    def test_hermes_command_key_redacted_in_receipt(self):
        worker = HermesWorker(api_key="sk-SECRET-123")
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "run"
            run_dir.mkdir()
            task = worker.write_task_file("r", "task.md", "# t")
            receipt = worker.run_isolated("# t")
        serialized = json.dumps(receipt, default=str)
        self.assertNotIn("sk-SECRET-123", serialized)
        self.assertNotIn("--api-key", serialized)
        self.assertFalse(receipt["executed"])

    def test_calibration_repeated_evidence_is_idempotent(self):
        from selfopt_chain.calibrate import fit_temperatures
        decisions = [{"id": "d1", "question_type": "strategy", "deferred": False, "confidence": 0.6, "chosen": "x", "final": "x"}]
        labels = [{"decision_id": "d1", "accepted": False}]
        first = fit_temperatures(decisions, labels)
        second = fit_temperatures(decisions, labels)
        self.assertEqual(second["temperature_per_prim"], first["temperature_per_prim"])
        self.assertEqual(second["n_labels"], 1)

    def test_evolution_dedup_across_cycles(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "state"
            loop = EvolutionLoop(state, ROOT / "docs", ROOT, worker=None)
            first = loop.run(max_tasks=2, parallel_mode="single")
            second = loop.run(max_tasks=2, parallel_mode="single")
            self.assertTrue(first)
            first_ids = {t["task_id"] for t in first}
            second_ids = {t["task_id"] for t in second}
            self.assertFalse(first_ids & second_ids, "zadnia z pierwszej tury nie moze powtorzyc sie w drugiej")
