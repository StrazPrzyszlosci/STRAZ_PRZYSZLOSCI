import json
import subprocess
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

from selfopt_chain.evolution_store import EvolutionStore
from selfopt_chain.evolver import EvolutionLoop, EvolutionTask


class SimulationPromotionTests(unittest.TestCase):
    def test_mock_then_armed_after_restart_runs_once_and_retains_ready(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / 'repo'
            repo.mkdir()
            subprocess.run(['git', 'init', '--quiet', str(repo)], check=True)
            docs = repo / 'docs'
            docs.mkdir()
            state = root / 'state'
            task = EvolutionTask('promotion', 'Concrete proposal for regression', 'test')

            class Worker:
                models = []
                ledger = None
                executor_name = 'controlled_test'
                armed = False
                calls = 0

                def enabled(self):
                    return self.armed

                def run_isolated(self, query, **kwargs):
                    self.calls += 1
                    output = root / ('production-' + str(self.calls))
                    output.mkdir()
                    (output / 'PROPOSAL.md').write_text('Concrete proposal with explicit regression checks.')
                    return {'executed': True, 'exit_code': 0, 'quarantine_dir': str(output),
                            'security_gate': {'ok': True}, 'validation': {'ok': True}}

            class Review:
                def complete(self, task, model_id, prompt):
                    return {'ok': True, 'model_id': 'controlled_test',
                            'output': '{"verdict":"pass","notes":"unit-test review oracle"}' if task['kind'] == 'review' else '{}'}

            worker = Worker()
            with patch('selfopt_chain.evolver.collect_evolution_tasks', return_value=[task]):
                first = EvolutionLoop(state, docs, repo, worker=worker, strategy_engine=Review())
                simulated = first.run(1)[0]
                self.assertEqual(simulated['status'], 'simulated')
                self.assertEqual(first.run(1), [])
                self.assertEqual(worker.calls, 0)

                worker.armed = True
                resumed = EvolutionLoop(state, docs, repo, worker=worker, strategy_engine=Review())
                promoted = resumed.run(1)
                self.assertEqual(len(promoted), 1, 'a mock receipt must not consume a real run')
                self.assertEqual(promoted[0]['status'], 'ready')
                self.assertEqual(promoted[0]['input_hash'], simulated['input_hash'])
                self.assertEqual(worker.calls, 1)
                self.assertEqual(resumed.run(1), [])
                row = resumed.store.snapshot()[resumed.fingerprint(task)]
                self.assertEqual(row['attempts'], 1)
                self.assertEqual(row['simulation_history'][0]['run_id'], simulated['run_id'])
                self.assertTrue(Path(simulated['receipt_path']).is_file())

    def test_promotion_does_not_reopen_real_terminal_states(self):
        for status in ['ready', 'published', 'accepted', 'rejected']:
            with self.subTest(status=status), tempfile.TemporaryDirectory() as tmp:
                store = EvolutionStore(tmp)
                lease = store.acquire('key', 'task', 'version')
                store.finish('key', lease, {'status': status, 'run_id': 'retained'})
                self.assertFalse(store.eligible('key', 'version', promote_simulated=True))
                self.assertIsNone(store.acquire('key', 'task', 'version', promote_simulated=True))

    def test_concurrent_promotion_has_exactly_one_owner(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = EvolutionStore(tmp)
            original = store.acquire('key', 'task', 'version')
            store.finish('key', original, {'status': 'simulated', 'run_id': 'simulation'})
            self.assertFalse(store.eligible('key', 'version'))
            with ThreadPoolExecutor(max_workers=8) as pool:
                leases = list(pool.map(lambda _: EvolutionStore(tmp).acquire(
                    'key', 'task', 'version', promote_simulated=True), range(8)))
            self.assertEqual(sum(lease is not None for lease in leases), 1)
            self.assertFalse(store.finish('key', original, {'status': 'ready'}))

    def test_legacy_simulated_row_promotes_without_resetting_real_failures(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'evolution_index.json').write_text(json.dumps({'key': {
                'status': 'simulated', 'task_id': 'task', 'input_hash': 'version',
                'attempts': 9, 'content_attempts': 0, 'run_id': 'legacy-mock'}}))
            now = [100.0]
            store = EvolutionStore(root, clock=lambda: now[0], max_attempts=1)
            self.assertTrue(store.eligible('key', 'version', promote_simulated=True))
            lease = store.acquire('key', 'task', 'version', promote_simulated=True)
            self.assertIsNotNone(lease)
            store.finish('key', lease, {'status': 'needs_fixes', 'executor': 'controlled_test'})
            now[0] += 901
            self.assertFalse(store.eligible('key', 'version', promote_simulated=True))
            self.assertIsNone(store.acquire('key', 'task', 'version', promote_simulated=True))
            row = store.snapshot()['key']
            self.assertEqual(row['content_attempts'], 1)
            self.assertEqual(row['simulation_history'][0]['run_id'], 'legacy-mock')


if __name__ == '__main__':
    unittest.main()
