"""When the decision core defers, scheduler must honor its safe final selection."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
from selfopt_chain.swarm import Demand, SwarmPlanner


class Core:
    def __init__(self, deferred):
        self.deferred = deferred

    def decide(self, *args, **kwargs):
        return {'final': 'first' if self.deferred else 'second', 'deferred': self.deferred,
                'confidence': 0.5 if self.deferred else 0.9,
                'probabilities': {'second': 0.51, 'first': 0.49}}


class DeferredSelectionContract(unittest.TestCase):
    def demands(self):
        return [Demand('first', 'first task', [], 'test', priority=2), Demand('second', 'second task', [], 'test', priority=1)]

    def test_deferred_uses_final_default_first(self):
        result = SwarmPlanner(Core(True)).decide_job_selection(self.demands(), 1)
        self.assertEqual(result['final'][0], 'first')

    def test_confident_choice_keeps_model_ranking(self):
        result = SwarmPlanner(Core(False)).decide_job_selection(self.demands(), 1)
        self.assertEqual(result['final'][0], 'second')

    def test_no_demands_is_empty(self):
        self.assertEqual(SwarmPlanner(Core(True)).decide_job_selection([], 1)['final'], [])


if __name__ == '__main__':
    unittest.main()
