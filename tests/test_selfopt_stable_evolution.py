import json
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

from selfopt_chain.evolution_store import EvolutionStore
from selfopt_chain.evolution_inputs import prepare_inputs, task_prompt, InputUnavailable
from selfopt_chain.evolver import EvolutionLoop, EvolutionTask, _parse_handoff_tasks
from selfopt_chain.swarm import BasalDecisionCore

ROOT = Path(__file__).resolve().parents[1]


class LeaseTests(unittest.TestCase):
    def test_only_one_owner_and_stale_owner_cannot_finish(self):
        with tempfile.TemporaryDirectory() as tmp:
            now = [100.0]
            def store():
                return EvolutionStore(tmp, clock=lambda: now[0], lease_seconds=10)
            with ThreadPoolExecutor(max_workers=8) as pool:
                leases = list(pool.map(lambda _: store().acquire('key', 'task', 'input-v1'), range(8)))
            lease = next(x for x in leases if x)
            self.assertEqual(sum(x is not None for x in leases), 1)
            now[0] += 11
            replacement = store().acquire('key', 'task', 'input-v1')
            self.assertIsNotNone(replacement)
            self.assertFalse(store().finish('key', lease, {'status': 'ready'}))
            self.assertTrue(store().finish('key', replacement, {'status': 'ready', 'run_id': 'new'}))
            self.assertFalse(store().eligible('key', 'input-v1'))
            self.assertTrue(store().eligible('key', 'input-v2'))

    def test_retry_retains_feedback_and_bounds_repeated_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            now = [100.0]
            store = EvolutionStore(tmp, clock=lambda: now[0], max_attempts=2, retry_seconds=10)
            lease = store.acquire('k', 't', 'v1')
            store.finish('k', lease, {'status': 'needs_fixes', 'error': 'missing test'})
            self.assertFalse(store.eligible('k', 'v1'))
            now[0] += 11
            resumed = EvolutionStore(tmp, clock=lambda: now[0], max_attempts=2, retry_seconds=10)
            self.assertEqual(resumed.feedback('k')['error'], 'missing test')
            lease = resumed.acquire('k', 't', 'v1')
            self.assertIsNotNone(lease)
            resumed.finish('k', lease, {'status': 'needs_fixes'})
            now[0] += 100
            self.assertFalse(resumed.eligible('k', 'v1'))
            self.assertTrue(resumed.eligible('k', 'v2'))

    def test_missing_inputs_do_not_consume_attempts(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = EvolutionStore(tmp)
            store.block('key', 'missing labels')
            self.assertEqual(store.snapshot()['key'].get('attempts', 0), 0)
            self.assertTrue(store.eligible('key', 'new-inputs'))


class TaskInputTests(unittest.TestCase):
    def test_latest_handoff_plain_numbered_items_and_continuations(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            (p / 'HANDOFF_DLA_NASTEPNEGO_AGENTA_2026-01-01.md').write_text('## Następne zadania\n1. **T1 stary**: stary opis\n')
            (p / 'HANDOFF_DLA_NASTEPNEGO_AGENTA_2026-01-02.md').write_text('## Otwarte etapy\n1. Nowe konkretne zadanie\n   z dalszym opisem i plikiem.\n2. Drugie zadanie.\n\n## Ryzyka\ninne\n')
            tasks = _parse_handoff_tasks(p)
            self.assertEqual(len(tasks), 2)
            self.assertIn('dalszym opisem', tasks[0].context)
            self.assertTrue(all('2026-01-02' in t.source for t in tasks))

    def test_feedback_is_in_next_prompt_but_not_input_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = EvolutionTask('t', 'napraw', 'test', input_refs=['selfopt_chain/swarm.py'])
            first = prepare_inputs(task, ROOT, Path(tmp))
            second = prepare_inputs(task, ROOT, Path(tmp), {'error': 'acceptance failed at case 2'})
            self.assertEqual(first['input_hash'], second['input_hash'])
            self.assertIn('acceptance failed at case 2', task_prompt(second))
            self.assertIn('/repo/selfopt_chain/swarm.py', task_prompt(second))

    def test_runtime_data_is_required_and_sanitized(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp)
            task = EvolutionTask('t', 'kalibracja', 'test', runtime_refs=['decisions.jsonl'])
            with self.assertRaises(InputUnavailable):
                prepare_inputs(task, ROOT, state)
            (state / 'decisions.jsonl').write_text(json.dumps({'id': 'd1', 'question_type': 'strategy', 'confidence': 0.5,
                    'context': {'private': 'DO_NOT_EXPORT'}, 'api_key': 'DO_NOT_EXPORT'}) + '\n')
            bundle = prepare_inputs(task, ROOT, state)
            self.assertNotIn('DO_NOT_EXPORT', json.dumps(bundle))

    def test_missing_data_blocks_before_strategy_or_worker(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = EvolutionTask('t', 'kalibracja', 'test', runtime_refs=['labels.jsonl'])
            class NeverEngine:
                def complete(self, *args):
                    raise AssertionError('unready task consumed a model request')
            with patch('selfopt_chain.evolver.collect_evolution_tasks', return_value=[task]):
                loop = EvolutionLoop(Path(tmp), ROOT / 'docs', ROOT, strategy_engine=NeverEngine())
                self.assertEqual(loop.run(), [])
                self.assertEqual(len(loop.blocked), 1)

    def test_model_selection_uses_characteristics_not_model_name(self):
        models = [{'model_id': 'named-fast-but-slow', 'quality_tier': 3, 'speed_class': 'slow'},
                  {'model_id': 'ordinary', 'quality_tier': 4, 'speed_class': 'fast'}]
        with tempfile.TemporaryDirectory() as tmp, patch.dict('os.environ', {'SELFOPT_BASAL_URL': ''}):
            loop = EvolutionLoop(Path(tmp), ROOT / 'docs', ROOT, models=models,
                                 lane_models=[m['model_id'] for m in models], decision_core=BasalDecisionCore())
            loop.strategy = {'model_hints': {'task': 'fast'}}
            self.assertEqual(loop._lane_model(0, EvolutionTask('task', 'work', 'test')), 'ordinary')


class CompleteRetryTests(unittest.TestCase):
    def test_worker_failure_feedback_retry_and_ready_retention(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict('os.environ', {'SELFOPT_HERMES': '1'}):
            now = [100.0]
            root = Path(tmp)
            task = EvolutionTask('t', 'opis konkretnej zmiany', 'test')
            prompts = []
            class Worker:
                models = []
                ledger = None
                def run_isolated(self, query, **kwargs):
                    prompts.append(query)
                    output = root / ('output' + str(len(prompts)))
                    output.mkdir()
                    if len(prompts) == 1:
                        return {'executed': True, 'exit_code': 1, 'quarantine_dir': str(output),
                                'error': 'no_artifacts', 'security_gate': {'ok': False}, 'validation': {'ok': False}}
                    (output / 'PROPOSAL.md').write_text('Konkretna propozycja z testem i uzasadnieniem.')
                    return {'executed': True, 'exit_code': 0, 'quarantine_dir': str(output),
                            'security_gate': {'ok': True}, 'validation': {'ok': True}}
            class Review:
                def complete(self, task, model_id, prompt):
                    return {'ok': True, 'model_id': 'review', 'output': '{"verdict":"pass","notes":"complete"}' if task['kind'] == 'review' else '{}'}
            with patch('selfopt_chain.evolver.collect_evolution_tasks', return_value=[task]):
                loop = EvolutionLoop(root, ROOT / 'docs', ROOT, worker=Worker(), strategy_engine=Review(),
                                     clock=lambda: now[0], retry_seconds=10)
                self.assertEqual(loop.run(1)[0]['status'], 'needs_fixes')
                self.assertEqual(loop.run(1), [])
                now[0] += 11
                receipt = loop.run(1)[0]
                self.assertEqual(receipt['status'], 'ready')
                self.assertIn('no_artifacts', prompts[-1])
                self.assertTrue(Path(receipt['archive_path']).is_dir())
                self.assertEqual(loop.run(1), [])
