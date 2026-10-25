"""T66: ensemble ról modeli — pula producentów, ranking wyników, porównanie."""
import tempfile
import unittest
from pathlib import Path

from selfopt_chain.evolver import EvolutionLoop, EvolutionTask, ensemble_pool, rank_ensemble_candidates


def _model(mid, tier=4, roles=("reason", "draft")):
    return {"model_id": mid, "quality_tier": tier, "routing_roles": list(roles), "speed_class": "medium",
            "capabilities": ["text", "json"], "context_tokens": 100000, "provider": "p", "role": "x",
            "privacy_class": "public_only", "cost_class": "free_quota"}


def _models():
    return {m["model_id"]: m for m in [
        _model("primary/x:free", 4), _model("second/y:free", 5), _model("third/z:free", 4), _model("weak/w:free", 2),
    ]}


class EnsemblePoolTest(unittest.TestCase):
    def test_k1_returns_primary_only(self):
        pool = ensemble_pool(_models(), ["primary/x:free", "second/y:free"], "proposal", "primary/x:free", 1)
        self.assertEqual(pool, ["primary/x:free"])

    def test_pool_distinct_capped_and_primary_first(self):
        pool = ensemble_pool(_models(), ["primary/x:free", "second/y:free", "third/z:free", "weak/w:free"],
                             "proposal", "primary/x:free", 3)
        self.assertEqual(pool[0], "primary/x:free")
        self.assertEqual(len(pool), 3)
        self.assertEqual(len(set(pool)), 3)

    def test_pool_fallback_when_no_others(self):
        pool = ensemble_pool(_models(), ["primary/x:free"], "proposal", "primary/x:free", 3)
        self.assertEqual(pool, ["primary/x:free"])

    def test_pool_empty_primary(self):
        self.assertEqual(ensemble_pool(_models(), [], "proposal", "", 3), [])

    def test_pool_k_larger_than_candidates(self):
        pool = ensemble_pool(_models(), ["primary/x:free", "second/y:free"], "proposal", "primary/x:free", 5)
        self.assertEqual(set(pool), {"primary/x:free", "second/y:free"})


class RankEnsembleTest(unittest.TestCase):
    def _receipt(self, alias, gate=False, review="unreviewed", valid=False, executed=False):
        return {"model_alias": alias, "gate_ok": gate, "review": {"verdict": review},
                "validation_ok": valid, "execution_ok": executed}

    def test_gate_beats_review_only(self):
        ranked = rank_ensemble_candidates([
            self._receipt("a", review="pass", valid=True, executed=True),
            self._receipt("b", gate=True, review="pass", valid=True, executed=True),
        ])
        self.assertEqual(ranked[0]["model_alias"], "b")

    def test_review_breaks_tie_between_valid(self):
        ranked = rank_ensemble_candidates([
            self._receipt("a", valid=True, executed=True),
            self._receipt("b", review="pass", valid=True, executed=True),
        ])
        self.assertEqual(ranked[0]["model_alias"], "b")

    def test_all_bad_still_deterministic(self):
        rows = [self._receipt("x"), self._receipt("a"), self._receipt("m")]
        self.assertEqual([r["model_alias"] for r in rank_ensemble_candidates(rows)],
                         [r["model_alias"] for r in rank_ensemble_candidates(list(reversed(rows)))])

    def test_validation_beats_execution_only(self):
        ranked = rank_ensemble_candidates([
            self._receipt("a", executed=True),
            self._receipt("b", valid=True),
        ])
        self.assertEqual(ranked[0]["model_alias"], "b")


class EnsembleLoopInitTest(unittest.TestCase):
    def test_default_and_explicit_ensemble_candidates(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            loop = EvolutionLoop(root / "state", root / "docs", root)
            self.assertEqual(loop.ensemble_candidates, 1)
            loop2 = EvolutionLoop(root / "state2", root / "docs", root, ensemble_candidates=2)
            self.assertEqual(loop2.ensemble_candidates, 2)

    def test_invalid_ensemble_falls_back_to_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            loop = EvolutionLoop(root / "state3", root / "docs", root, ensemble_candidates=0)
            self.assertEqual(loop.ensemble_candidates, 1)


if __name__ == "__main__":
    unittest.main()
