import copy
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "hermes_work_queue" / "seed_queue.json"

import sys
sys.path.insert(0, str(ROOT / "hermes_work_queue"))
from validate_queue import validate_queue  # noqa: E402


def _ok_job(job_id: str = "repo_scout_daily") -> dict:
    return {
        "job_id": job_id,
        "purpose": "purpose string at least 10 chars",
        "inputs": ["docs/external_repos/registry.json"],
        "outputs": ["report.md"],
        "model_route": {"default_profile": "free_public_small_model"},
        "artifact_requirements": ["run_receipt.json", "handoff_or_pr.md"],
        "human_control_point": "maintainer reviews before merge",
        "next_disabled": True,
        "no_auto_merge": True,
        "no_direct_push": True
    }


def _ok_queue(jobs: list[dict] | None = None) -> dict:
    return {
        "queue_id": "hermes_test",
        "generated_at": "2026-07-06T00:00:00+00:00",
        "platform": "hermes_pilot",
        "jobs": jobs or [_ok_job()]
    }


class HermesWorkQueueTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = json.loads(SEED.read_text(encoding="utf-8"))

    def test_seed_validates(self):
        errors = validate_queue(self.payload)
        self.assertEqual(errors, [], f"seed must validate: {errors}")

    def test_seed_has_all_five_jobs(self):
        ids = {j["job_id"] for j in self.payload["jobs"]}
        self.assertEqual(ids, {
            "repo_scout_daily", "handoff_builder_after_commit",
            "resource_scout_triage", "execution_pack_draft_generator",
            "audit_reviewer_before_pr"
        })

    def test_blocks_empty_jobs(self):
        errors = validate_queue({"queue_id": "x", "platform": "y", "jobs": []})
        self.assertTrue(any("jobs must be a non-empty list" in e for e in errors))

    def test_blocks_unknown_job_id(self):
        q = _ok_queue([_ok_job("unknown_job")])
        errors = validate_queue(q)
        self.assertTrue(any("job_id" in e for e in errors))

    def test_blocks_duplicate_job_id(self):
        q = _ok_queue([_ok_job(), _ok_job()])
        errors = validate_queue(q)
        self.assertTrue(any("duplicate" in e for e in errors))

    def test_blocks_no_auto_merge_false(self):
        job = _ok_job()
        job["no_auto_merge"] = False
        q = _ok_queue([job])
        errors = validate_queue(q)
        self.assertTrue(any("no_auto_merge" in e for e in errors))

    def test_blocks_no_direct_push_false(self):
        job = _ok_job()
        job["no_direct_push"] = False
        q = _ok_queue([job])
        errors = validate_queue(q)
        self.assertTrue(any("no_direct_push" in e for e in errors))

    def test_blocks_next_disabled_false(self):
        job = _ok_job()
        job["next_disabled"] = False
        q = _ok_queue([job])
        errors = validate_queue(q)
        self.assertTrue(any("next_disabled" in e for e in errors))

    def test_blocks_unknown_artifact(self):
        job = _ok_job()
        job["artifact_requirements"] = ["rogue_file.json"]
        q = _ok_queue([job])
        errors = validate_queue(q)
        self.assertTrue(any("artifact_requirements" in e for e in errors))

    def test_blocks_missing_model_route(self):
        job = _ok_job()
        del job["model_route"]
        q = _ok_queue([job])
        errors = validate_queue(q)
        self.assertTrue(any("model_route" in e for e in errors))

    def test_blocks_short_purpose(self):
        job = _ok_job()
        job["purpose"] = "short"
        q = _ok_queue([job])
        errors = validate_queue(q)
        self.assertTrue(any("purpose" in e for e in errors))

    def test_blocks_short_human_control_point(self):
        job = _ok_job()
        job["human_control_point"] = "ok"
        q = _ok_queue([job])
        errors = validate_queue(q)
        self.assertTrue(any("human_control_point" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
