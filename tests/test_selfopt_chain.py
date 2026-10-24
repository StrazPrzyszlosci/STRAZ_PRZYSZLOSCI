import io
import json
import os
import sys
import tempfile
import unittest
import urllib.request
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from selfopt_chain.engine import FreeApiEngine, MockEngine
from selfopt_chain.graph import END, GraphError, StateGraph
from selfopt_chain.optimizers import GepaPromptOptimizer, MapElitesOptimizer, default_fitness
from selfopt_chain.registry import DEFAULT_REGISTRY, load_registry, validate_registry
from selfopt_chain.router import QuotaLedger, required_tier_for_kind, route_task
from selfopt_chain.tracer import TraceRecorder, extract_insights, summarize_traces
from selfopt_chain import run_loop

EXAMPLES = ROOT / "selfopt_chain" / "examples"


def _task(kind, **kw):
    return {"task_id": kw.pop("task_id", "t1"), "kind": kind, "privacy": kw.pop("privacy", "public"), "requires": kw.pop("requires", []), **kw}


class RegistryTest(unittest.TestCase):
    def test_seed_registry_valid(self):
        models = load_registry()
        self.assertGreaterEqual(len(models), 10)

    def test_duplicate_model_id_rejected(self):
        models = load_registry()
        payload = {"models": models + [dict(models[0])]}
        self.assertTrue(validate_registry(payload))

    def test_paid_cost_class_rejected(self):
        models = load_registry()
        paid = dict(models[0])
        paid["model_id"] = "paid-model"
        paid["cost_class"] = "paid"
        self.assertTrue(validate_registry({"models": models + [paid]}))

    def test_hosted_model_cannot_be_local_private(self):
        models = load_registry()
        wrong = dict(models[0])
        wrong["model_id"] = "wrong-privacy"
        wrong["privacy_class"] = "local_private"
        self.assertTrue(validate_registry({"models": models + [wrong]}))

    def test_secret_value_in_api_rejected(self):
        models = load_registry()
        leak = json.loads(json.dumps(models[0]))
        leak["model_id"] = "leaky"
        leak["api"]["secret_env"] = "sk-live-token"
        errors = validate_registry({"models": models + [leak]})
        self.assertTrue(errors)


class RouterTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.models = load_registry()

    def test_classify_picks_fast_hosted_min_excess(self):
        ledger = QuotaLedger(self.models)
        decision = route_task(_task("classify"), self.models, ledger)
        chosen = decision["chosen"]
        self.assertEqual(chosen["quality_tier"], 2)
        self.assertEqual(chosen["speed_class"], "fast")
        self.assertNotEqual(chosen["provider"], "selfhost_recovered_node")
        self.assertFalse(decision["blocked"])

    def test_vision_extract_requires_tier5(self):
        ledger = QuotaLedger(self.models)
        decision = route_task(_task("vision_extract", requires=["vision"]), self.models, ledger)
        self.assertEqual(decision["chosen"]["model_id"], "gemini-2.5-pro")
        self.assertEqual(decision["required_tier"], 5)

    def test_private_task_routed_to_local_only(self):
        ledger = QuotaLedger(self.models)
        decision = route_task(_task("summarize", privacy="private"), self.models, ledger)
        self.assertEqual(decision["chosen"]["provider"], "selfhost_recovered_node")

    def test_quota_exhaustion_falls_back_deterministically(self):
        ledger = QuotaLedger(self.models)
        fast8b = "llama-3.1-8b-instant"
        for _ in range(30):
            ledger.record(fast8b)
        decision = route_task(_task("classify"), self.models, ledger)
        self.assertNotEqual(decision["chosen"]["model_id"], fast8b)
        self.assertIn(fast8b, decision["rejected"]["quota"])

    def test_all_quota_exhausted_blocks(self):
        ledger = QuotaLedger(self.models)
        for m in self.models:
            while ledger.can_use(m["model_id"]):
                ledger.record(m["model_id"])
        decision = route_task(_task("classify"), self.models, ledger)
        self.assertTrue(decision["blocked"])
        self.assertEqual(decision["blocked_reason"], "quota_exhausted")

    def test_unknown_kind_defaults_to_tier3(self):
        self.assertEqual(required_tier_for_kind("nieznany"), 3)

    def test_missing_capability_blocks(self):
        ledger = QuotaLedger(self.models)
        decision = route_task(_task("classify", privacy="private", requires=["vision"]), self.models, ledger)
        self.assertTrue(decision["blocked"])
        self.assertEqual(decision["blocked_reason"], "no_capability_match")

    def test_tier_unreachable_blocks(self):
        ledger = QuotaLedger(self.models)
        decision = route_task(_task("vision_extract", privacy="private", requires=["vision"]), self.models, ledger)
        self.assertTrue(decision["blocked"])

    def test_stale_snapshot_blocks_provider(self):
        ledger = QuotaLedger(self.models)
        snapshot = {"entries": [{"provider": "groq_free", "status": "stale"}]}
        decision = route_task(_task("classify"), self.models, ledger, quota_snapshot=snapshot)
        self.assertNotIn("groq_free", [decision["chosen"]["provider"]] + [a["provider"] for a in decision["alternatives"]])

    def test_heavier_kind_prefers_higher_tier_than_light_kind(self):
        ledger = QuotaLedger(self.models)
        light = route_task(_task("classify"), self.models, ledger)["chosen"]["quality_tier"]
        heavy = route_task(_task("reason", requires=["reasoning"]), self.models, ledger)["chosen"]["quality_tier"]
        self.assertGreaterEqual(heavy, 4)
        self.assertLessEqual(light, 2)


class GraphTest(unittest.TestCase):
    def test_linear_pipeline_from_start_edge(self):
        g = StateGraph(dict)
        g.add_node("a", lambda s: {"x": s.get("x", 0) + 1})
        g.add_node("b", lambda s: {"x": s["x"] * 2})
        g.add_edge(START := "__start__", "a")
        g.add_edge("a", "b")
        g.add_edge("b", END)
        out = g.compile().invoke({"x": 3})
        self.assertEqual(out["x"], 8)

    def test_conditional_edges_route_by_state(self):
        g = StateGraph(dict)
        g.add_node("gate", lambda s: {"label": "alarm"})
        g.add_node("hot", lambda s: {"path": "escalate"})
        g.add_node("cold", lambda s: {"path": "ignore"})
        g.set_entry_point("gate")
        g.add_conditional_edges("gate", lambda s: s["label"], {"alarm": "hot", "ok": "cold"})
        g.add_edge("hot", END)
        g.add_edge("cold", END)
        out = g.compile().invoke({})
        self.assertEqual(out["path"], "escalate")

    def test_step_limit_guards_loop(self):
        g = StateGraph(dict)
        g.add_node("loop", lambda s: {"i": s.get("i", 0) + 1})
        g.set_entry_point("loop")
        g.add_edge("loop", "loop")
        with self.assertRaises(GraphError):
            g.compile().invoke({}, max_steps=5)

    def test_unknown_edge_endpoint_rejected(self):
        g = StateGraph(dict)
        g.add_node("a", lambda s: {})
        with self.assertRaises(GraphError):
            g.add_edge("a", "nieznany")

    def test_compile_without_entry_rejected(self):
        g = StateGraph(dict)
        g.add_node("a", lambda s: {})
        with self.assertRaises(GraphError):
            g.compile()


class EngineTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.models = load_registry()

    def test_mock_classify_detects_alarm_keyword(self):
        engine = MockEngine(self.models)
        alarm = engine.complete(_task("classify"), "llama-3.1-8b-instant", "telemetria: ALARM czujnik B")
        self.assertEqual(alarm["output"], "ALARM")
        ok = engine.complete(_task("classify"), "llama-3.1-8b-instant", "telemetria: wszystko w normie")
        self.assertEqual(ok["output"], "OK")

    def test_mock_failure_simulation(self):
        engine = MockEngine(self.models, fail_kinds={"extract"})
        res = engine.complete(_task("extract"), "llama-3.1-8b-instant", "x")
        self.assertFalse(res["ok"])
        self.assertEqual(res["error_class"], "mock_failure")

    def test_mock_latency_follows_speed_class(self):
        engine = MockEngine(self.models)
        fast = engine.complete(_task("summarize"), "llama-3.1-8b-instant", "x")
        slow = engine.complete(_task("summarize"), "meta/llama-3.1-405b-instruct", "x")
        self.assertLess(fast["latency_ms"], slow["latency_ms"])

    def test_free_api_refuses_without_env_flag(self):
        env = {"SELFOPT_NETWORK": "", "GROQ_API_KEY": "test-token"}
        with mock.patch.dict(os.environ, env, clear=False):
            engine = FreeApiEngine(self.models)
            res = engine.complete(_task("summarize"), "llama-3.1-8b-instant", "x")
        self.assertFalse(res["ok"])
        self.assertEqual(res["error_class"], "network_disabled")

    def test_free_api_refuses_private_task_even_with_flag(self):
        env = {"SELFOPT_NETWORK": "1", "GROQ_API_KEY": "test-token"}
        with mock.patch.dict(os.environ, env, clear=False):
            engine = FreeApiEngine(self.models)
            res = engine.complete(_task("summarize", privacy="private"), "llama-3.1-8b-instant", "x")
        self.assertFalse(res["ok"])
        self.assertEqual(res["error_class"], "privacy_violation")

    def test_free_api_missing_secret(self):
        env = {"SELFOPT_NETWORK": "1"}
        env.pop("GROQ_API_KEY", None)
        with mock.patch.dict(os.environ, env, clear=False):
            engine = FreeApiEngine(self.models)
            res = engine.complete(_task("summarize"), "llama-3.1-8b-instant", "x")
        self.assertFalse(res["ok"])
        self.assertEqual(res["error_class"], "missing_secret")

    def test_free_api_openai_chat_happy_path_offline(self):
        env = {"SELFOPT_NETWORK": "1", "GROQ_API_KEY": "test-token"}
        fake_payload = {"choices": [{"message": {"content": "odpowiedz modelu"}}]}
        fake_resp = io.BytesIO(json.dumps(fake_payload).encode("utf-8"))
        with mock.patch.dict(os.environ, env, clear=False), \
                mock.patch.object(urllib.request, "urlopen", return_value=fake_resp) as urlopen:
            engine = FreeApiEngine(self.models)
            res = engine.complete(_task("summarize"), "llama-3.1-8b-instant", "prompt")
        self.assertTrue(res["ok"])
        self.assertEqual(res["output"], "odpowiedz modelu")
        req = urlopen.call_args[0][0]
        self.assertIn("api.groq.com", req.full_url)
        self.assertNotIn("test-token", req.full_url)


class OptimizersTest(unittest.TestCase):
    def _cands(self):
        return [
            {"id": "a", "prompt": "pA", "scores": {"quality": 0.9, "latency_ms": 100, "cost": 0}, "feedback": "A byloby lepsze z lista krokow"},
            {"id": "b", "prompt": "pB", "scores": {"quality": 0.8, "latency_ms": 200, "cost": 0}, "feedback": "B gubi kontekst"},
            {"id": "c", "prompt": "pC", "scores": {"quality": 0.7, "latency_ms": 50, "cost": 0}, "feedback": ""},
        ]

    def test_pareto_front_excludes_dominated(self):
        front = GepaPromptOptimizer().pareto_front(self._cands())
        self.assertIn("a", front)
        self.assertIn("c", front)
        self.assertNotIn("b", front)

    def test_chosen_max_quality_with_auto_apply_false(self):
        out = GepaPromptOptimizer().optimize(self._cands())
        self.assertEqual(out["chosen_id"], "a")
        self.assertFalse(out["auto_apply"])
        self.assertTrue(out["rationale"])

    def test_reflection_merges_feedback_and_insights(self):
        out = GepaPromptOptimizer().propose_reflection(self._cands(), [{"suggested_skill_patch": "wyzel X na model fast"}])
        self.assertIn("lista krokow", out["prompt_patch_proposal"])
        self.assertIn("wyzel X", out["prompt_patch_proposal"])
        self.assertFalse(out["auto_apply"])

    def test_map_elites_replaces_only_on_better_fitness(self):
        me = MapElitesOptimizer()
        prog = {"id": "p1", "kind": "summarize", "complexity": "light", "scores": {"quality": 0.6, "latency_ms": 200}}
        accepted = me.step([prog])
        self.assertEqual(len(accepted), 1)
        worse = {"id": "p2", "kind": "summarize", "complexity": "light", "scores": {"quality": 0.5, "latency_ms": 900}}
        accepted = me.step([worse])
        self.assertEqual(accepted, [])
        better = {"id": "p3", "kind": "summarize", "complexity": "light", "scores": {"quality": 0.9, "latency_ms": 100}}
        accepted = me.step([better])
        self.assertEqual(accepted[0]["replaced"], "p1")

    def test_map_elites_separate_niches(self):
        me = MapElitesOptimizer()
        me.step([{"id": "x", "kind": "classify", "complexity": "light", "scores": {"quality": 0.5, "latency_ms": 100}}])
        me.step([{"id": "y", "kind": "draft", "complexity": "heavy", "scores": {"quality": 0.5, "latency_ms": 100}}])
        self.assertEqual(me.proposal()["niches"], 2)

    def test_default_fitness_penalizes_latency(self):
        self.assertGreater(default_fitness({"quality": 0.5, "latency_ms": 0}), default_fitness({"quality": 0.5, "latency_ms": 3000}))


class TracerTest(unittest.TestCase):
    def test_insights_flag_slow_model_and_bottleneck(self):
        tracer = TraceRecorder("run-x")
        tracer.run_start("demo", "mock")
        for node, lat in (("a", 300), ("b", 2400)):
            tracer.routed({"task_id": node, "kind": "extract", "required_tier": 2, "chosen": {"model_id": "slow-model", "provider": "p", "quality_tier": 4, "speed_class": "slow"}, "blocked": False, "blocked_reason": None}, node)
            tracer.node_result(node, {"ok": False, "model_id": "slow-model", "provider": "p", "latency_ms": lat, "tokens_est": 10, "error": "mock failure", "error_class": "mock_failure"})
        tracer.run_end("ok", 2)
        insights = extract_insights(tracer.dump())
        ids = [i["insight_id"] for i in insights]
        self.assertTrue(any(i.startswith("quality_gap:slow-model") for i in ids))
        self.assertTrue(any(i.startswith("bottleneck:b") for i in ids))
        summary = summarize_traces(tracer.dump())
        self.assertEqual(summary["models"]["slow-model"]["ok_rate"], 0.0)


class ValidateChainTest(unittest.TestCase):
    def test_example_chains_validate(self):
        for name in ("chain_resource_triage.json", "chain_edge_advisory_lora.json"):
            chain = json.loads((EXAMPLES / name).read_text(encoding="utf-8"))
            self.assertEqual(run_loop.validate_chain(chain), [], name)

    def test_unknown_next_rejected(self):
        bad = {"nodes": [{"id": "a", "kind": "classify", "privacy": "public", "complexity": "light", "next": "nikt"}], "entry": "a"}
        self.assertTrue(run_loop.validate_chain(bad))

    def test_dispatch_requires_destination(self):
        bad = {"nodes": [{"id": "d", "type": "dispatch", "destination": "GDANSK"}], "entry": "d"}
        self.assertTrue(run_loop.validate_chain(bad))


class RunLoopEndToEndTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.out = Path(self.tmp.name)

    def test_resource_triage_run_emits_artifacts(self):
        rc = run_loop.main([
            "--chain", str(EXAMPLES / "chain_resource_triage.json"),
            "--out", str(self.out / "run"),
        ])
        self.assertEqual(rc, 0)
        receipt = json.loads((self.out / "run" / "run_receipt.json").read_text(encoding="utf-8"))
        self.assertEqual(receipt["status"], "ok")
        self.assertEqual(receipt["nodes_run"], 4)
        self.assertEqual(receipt["routed"], 4)
        self.assertFalse(receipt["auto_applied"])
        self.assertEqual(receipt["policy"], "suggest-only")
        self.assertTrue((self.out / "run" / "traces.jsonl").exists())
        proposals = (self.out / "run" / "optimization_proposals.md").read_text(encoding="utf-8")
        self.assertIn("suggest-only", proposals)

    def test_lora_advisory_dispatch_enqueues_envelope(self):
        rc = run_loop.main([
            "--chain", str(EXAMPLES / "chain_edge_advisory_lora.json"),
            "--out", str(self.out / "run2"),
        ])
        self.assertEqual(rc, 0)
        receipt = json.loads((self.out / "run2" / "run_receipt.json").read_text(encoding="utf-8"))
        self.assertEqual(len(receipt["lora_dispatched"]), 1)
        self.assertTrue(receipt["lora_dispatched"][0]["enqueued"])
        queue = (self.out / "run2" / "lora_spool" / "queue.jsonl").read_text(encoding="utf-8").strip().splitlines()
        envelope = json.loads(queue[0])
        self.assertEqual(envelope["priority"], 1)
        self.assertIn("ALARM", envelope["payload_text"])

    def test_free_api_engine_reports_network_disabled(self):
        env = {"SELFOPT_NETWORK": ""}
        with mock.patch.dict(os.environ, env, clear=False):
            rc = run_loop.main([
                "--chain", str(EXAMPLES / "chain_resource_triage.json"),
                "--out", str(self.out / "run3"),
                "--engine", "free-api",
            ])
        self.assertEqual(rc, 1)
        receipt = json.loads((self.out / "run3" / "run_receipt.json").read_text(encoding="utf-8"))
        self.assertNotEqual(receipt["status"], "ok")
        proposals = (self.out / "run3" / "optimization_proposals.md").read_text(encoding="utf-8")
        self.assertIn("GEPA-Pareto", proposals)


if __name__ == "__main__":
    unittest.main()
