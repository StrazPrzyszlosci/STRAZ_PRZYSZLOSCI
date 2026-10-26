"""T68: misje tła dla bezczynnych modeli + katalog OSS jako runtime-input."""
import json
import tempfile
import unittest
from pathlib import Path

from selfopt_chain.evolution_inputs import InputUnavailable, public_runtime
from selfopt_chain.evolver import EvolutionTask, EvolutionLoop, idle_mission_catalog


class FakeWorker:
    models = [{"model_id": "m/a", "quality_tier": 4, "routing_roles": ["reason"], "speed_class": "fast",
               "capabilities": ["text"], "context_tokens": 1000, "provider": "p", "role": "x",
               "privacy_class": "public_only", "cost_class": "free_quota"}]
    ledger = None
    executor_name = "hermes"

    def __init__(self, armed=True):
        self.armed = armed

    def enabled(self):
        return self.armed


class MissionCatalogTest(unittest.TestCase):
    def test_catalog_filters_missing_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("readme", encoding="utf-8")
            themes = idle_mission_catalog(root)
            self.assertEqual(themes, [])  # same README nie wystarcza — każdy temat ma twarde input_refs

    def test_catalog_on_real_repo_contains_core_themes(self):
        themes = idle_mission_catalog(Path("."))
        slugs = {t["slug"] for t in themes}
        self.assertGreaterEqual(len(slugs), 5)
        for expected in ("projekty_realizowalne_teraz", "openbot_sterownik", "selfopt_calibrate_review",
                          "repo_health", "lora_mesh_gotowosc"):
            self.assertIn(expected, slugs)


class IdleMissionTasksTest(unittest.TestCase):
    def _loop(self, worker):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            yield EvolutionLoop(root / "state", root / "docs", root, worker=worker, models=worker.models)

    def test_disabled_worker_gets_no_missions(self):
        loop = next(self._loop(FakeWorker(armed=False)))
        self.assertEqual(loop._idle_mission_tasks(3), [])

    def test_armed_worker_gets_capped_fresh_missions(self):
        loop = next(self._loop(FakeWorker(armed=True)))
        loop.repo_root = Path(".")
        missions = loop._idle_mission_tasks(3)
        self.assertEqual(len(missions), 3)
        for task in missions:
            self.assertTrue(task.task_id.startswith("mission_"))
            self.assertRegex(task.task_id, r"_\d{4}w\d+$")
            self.assertEqual(task.priority, -1)
            self.assertEqual(task.kind, "proposal")
            self.assertIn("suggest-only", task.constraints)
        ids = {t.task_id for t in missions}
        self.assertEqual(len(ids), 3)

    def test_runtime_ref_mission_skipped_when_catalog_missing(self):
        loop = next(self._loop(FakeWorker(armed=True)))
        loop.repo_root = Path(".")
        missions = loop._idle_mission_tasks(99)
        slugs = [t.source.split(":", 1)[1] for t in missions]
        self.assertNotIn("oss_adoption_scan", slugs)  # brak oss_catalog.json w state-dir

    def test_runtime_ref_mission_present_when_catalog_exists(self):
        loop = next(self._loop(FakeWorker(armed=True)))
        loop.repo_root = Path(".")
        loop.state_dir.mkdir(parents=True, exist_ok=True)
        (loop.state_dir / "oss_catalog.json").write_text(json.dumps(
            [{"name": "r", "url": "https://x", "readme_excerpt": "abc"}]), encoding="utf-8")
        missions = loop._idle_mission_tasks(99)
        slugs = [t.source.split(":", 1)[1] for t in missions]
        self.assertIn("oss_adoption_scan", slugs)


class OssRuntimeExportTest(unittest.TestCase):
    def test_oss_catalog_export_allowlist(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "oss_catalog.json"
            p.write_text(json.dumps([{"name": "repo", "url": "https://example/r",
                                       "readme_excerpt": "fragment", "secret": "drop-me"}]), encoding="utf-8")
            rows = public_runtime(p, "oss_catalog.json")
            self.assertEqual(rows[0]["name"], "repo")
            self.assertNotIn("secret", rows[0])

    def test_empty_catalog_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "oss_catalog.json"
            p.write_text(json.dumps([]), encoding="utf-8")
            with self.assertRaises(InputUnavailable):
                public_runtime(p, "oss_catalog.json")


if __name__ == "__main__":
    unittest.main()
