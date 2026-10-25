"""T67: zwiadowca całościowy — PR-y/sprzęt/baza części jako wejścia; dyrektor/asystent."""
import json
import tempfile
import unittest
from pathlib import Path

from selfopt_chain.evolution_inputs import InputUnavailable, prepare_inputs, public_runtime
from selfopt_chain.evolver import EvolutionTask, _parse_targets, generate_llm_strategy


class ScoutRuntimeExportTest(unittest.TestCase):
    def test_public_runtime_allows_scout_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "open_prs.json").write_text(json.dumps(
                [{"number": 34, "title": "T65", "is_draft": True, "mergeable": True, "head": "a", "base": "main",
                  "updated_at": "2026-10-25", "secret_field": "x"}]), encoding="utf-8")
            rows = public_runtime(root / "open_prs.json", "open_prs.json")
            self.assertEqual(rows[0]["number"], 34)
            self.assertNotIn("secret_field", rows[0])
            (root / "hardware_changes.json").write_text(json.dumps(
                [{"changed_at": "t", "field": "cpu.effective_cores", "before": 4, "after": 8}]), encoding="utf-8")
            self.assertEqual(public_runtime(root / "hardware_changes.json", "hardware_changes.json")[0]["after"], 8)
            (root / "parts_db_changes.json").write_text(json.dumps(
                [{"changed_at": "t", "rows_before": 10, "rows_after": 12, "delta": 2}]), encoding="utf-8")
            self.assertEqual(public_runtime(root / "parts_db_changes.json", "parts_db_changes.json")[0]["delta"], 2)

    def test_public_runtime_rejects_unknown_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "whatever.json"
            p.write_text(json.dumps([{"a": 1}]), encoding="utf-8")
            with self.assertRaises(InputUnavailable):
                public_runtime(p, "whatever.json")

    def test_empty_scout_file_blocks_task(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "open_prs.json"
            p.write_text(json.dumps([]), encoding="utf-8")
            with self.assertRaises(InputUnavailable):
                public_runtime(p, "open_prs.json")


class ScoutTargetsTest(unittest.TestCase):
    def test_scout_targets_declared_with_cadence(self):
        targets = {t.task_id: t for t in _parse_targets()}
        for task_id, cadence in (("target_open_prs_triage", 3), ("target_hardware_adaptation", 7),
                                 ("target_parts_db_refresh", 7), ("target_external_oss_adoption", 7),
                                 ("target_actuation_readiness_scan", 14)):
            self.assertIn(task_id, targets)
            self.assertEqual(targets[task_id].reset_after_days, cadence)
        self.assertIn("open_prs.json", targets["target_open_prs_triage"].runtime_refs)
        self.assertIn("AGENTS.md", targets["target_open_prs_triage"].input_refs)


class DirectorAssistantTest(unittest.TestCase):
    class Engine:
        def __init__(self):
            self.prompts = []

        def complete(self, task, alias, prompt):
            self.prompts.append(prompt)
            return {"ok": True, "model_id": "director/test", "output": json.dumps({
                "brief": "kolejnosc wg priorytetow", "priorities": ["t1"],
                "model_hints": {"t1": "smart"}, "assistant_feedback": "preferuj mocne modele do review",
                "subtasks": []})}

    def test_assistant_report_flows_to_director_and_feedback_returns(self):
        engine = self.Engine()
        tasks = [EvolutionTask(task_id="t1", title="T", source="test")]
        report = {"recent_decisions": [{"id": "d1", "question_type": "model_selection", "final": "m/a"}],
                  "labels_total": 3, "labels_accepted": 1, "labels_rejected": 2}
        strategy, subtasks = generate_llm_strategy(tasks, engine, {"architecture": "x86_64"}, assistant_report=report)
        self.assertIn("RAPORT ASYSTENTA", engine.prompts[0])
        self.assertIn("model_selection", engine.prompts[0])
        self.assertEqual(strategy["assistant_feedback"], "preferuj mocne modele do review")
        self.assertEqual(strategy["model_hints"], {"t1": "smart"})

    def test_fallback_strategy_has_assistant_feedback(self):
        tasks = [EvolutionTask(task_id="t1", title="T", source="test")]
        strategy, _ = generate_llm_strategy(tasks, None)
        self.assertEqual(strategy["assistant_feedback"], "")


if __name__ == "__main__":
    unittest.main()
