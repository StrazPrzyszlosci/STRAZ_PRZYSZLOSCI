import io
import json
import os
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from selfopt_chain import run_loop
from selfopt_chain.engine import MockEngine
from selfopt_chain.evolver import EvolutionLoop
from selfopt_chain.hermes_worker import HermesWorker, SecurityGate
from selfopt_chain.orchestrator import Orchestrator, Job, build_chain_def, quota_gate
from selfopt_chain.quota import QuotaLedger, QuotaExceeded
from selfopt_chain.registry import DEFAULT_REGISTRY, load_registry
from selfopt_chain.swarm import Demand, charter_check, load_charter
from selfopt_chain.tracer import TraceRecorder

ROOT = Path(__file__).resolve().parents[1]


class QuotaRegressionTests(unittest.TestCase):
    def test_atomic_limit_across_instances_and_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'ledger.json'
            models = [{'model_id': 'm', 'rpm_seed': 100, 'rpd_seed': 8}]
            def reserve(_):
                try:
                    QuotaLedger(models, path).record('m')
                    return True
                except QuotaExceeded:
                    return False
            with ThreadPoolExecutor(max_workers=8) as pool:
                self.assertEqual(sum(pool.map(reserve, range(30))), 8)
            self.assertEqual(QuotaLedger(models, path).rpd_used, {'m': 8})

    def test_rolling_minute_and_midnight_without_restart(self):
        now = [1700000000.0]
        ledger = QuotaLedger([{'model_id': 'm', 'rpm_seed': 1, 'rpd_seed': 2}], clock=lambda: now[0])
        ledger.record('m')
        self.assertFalse(ledger.can_use('m'))
        now[0] += 61
        ledger.record('m')
        now[0] += 61
        self.assertFalse(ledger.can_use('m'))
        now[0] += 86400
        self.assertTrue(ledger.can_use('m'))

    def test_all_real_engines_require_snapshot(self):
        for name in ['free-api', 'omniroute']:
            self.assertFalse(quota_gate(name, None)['allowed'])


class ExecutionRegressionTests(unittest.TestCase):
    def test_draft_and_review_receive_dependencies(self):
        chain = build_chain_def(Job('probe', 'resource_scout', {'id': 'probe'}))
        runner = run_loop.ChainRunner(load_registry(), 'mock', None, TraceRecorder('probe'))
        prompts = {}
        class Capture:
            def complete(self, task, model_id, prompt):
                prompts[task['task_id']] = prompt
                return {'ok': True, 'output': 'marker_' + task['task_id'], 'model_id': model_id}
        runner.engine = Capture()
        run_loop.build_chain_graph(chain, runner).invoke({'payload': chain['payload']})
        self.assertIn('marker_extract', prompts['draft'])
        self.assertIn('marker_draft', prompts['review'])

    def test_failed_job_is_retryable_and_eight_calls_are_eight(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            config = {'engine': 'mock', 'state_dir': base, 'registry_path': DEFAULT_REGISTRY,
                      'records_paths': [ROOT / 'resource_scout/examples/ewaste_phone_batch.json'],
                      'max_jobs': 1, 'kill_switch': base / 'STOP', 'inbox_dir': None}
            original = MockEngine
            with patch.object(run_loop, 'MockEngine', side_effect=lambda m: original(m, fail_kinds={'review'})), redirect_stdout(io.StringIO()):
                orch = Orchestrator(config)
                failed = orch.run_cycle()
            self.assertNotEqual(failed['jobs_status'], 'ok')
            self.assertFalse(orch.state.data['processed'])
            with redirect_stdout(io.StringIO()):
                success = orch.run_cycle()
            self.assertEqual(success['jobs_run'][0]['rc'], 0)
            self.assertEqual(sum(orch.ledger.rpd_used.values()), 8)

    def test_private_input_is_never_reclassified_public(self):
        chain = build_chain_def(Job('private', 'lora_inbox', {'privacy': 'private', 'payload_text': 'PRIVATE_MARKER'}))
        self.assertTrue(all(n['privacy'] == 'private' for n in chain['nodes']))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'chain.json'
            path.write_text(json.dumps(chain))
            with patch.object(run_loop.FreeApiEngine, '_call') as network, redirect_stdout(io.StringIO()):
                rc = run_loop.run_chain(path, Path(tmp) / 'run', 'free-api', DEFAULT_REGISTRY, None, None)
            self.assertNotEqual(rc, 0)
            network.assert_not_called()

    def test_failed_dependency_prevents_review_call(self):
        chain = build_chain_def(Job('probe', 'audit', {}))
        runner = run_loop.ChainRunner(load_registry(), 'mock', None, TraceRecorder('probe'))
        runner.engine = MockEngine(load_registry(), fail_kinds={'draft'})
        output = run_loop.build_chain_graph(chain, runner).invoke({'payload': {}})['outputs']
        self.assertEqual(output['review']['error_class'], 'dependency_failed')
        self.assertEqual(len(runner.routing), 3)


class ArtifactRegressionTests(unittest.TestCase):
    def test_empty_and_symlink_artifacts_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            self.assertFalse(SecurityGate().inspect_tree(p)['ok'])
            (p / 'escape.py').symlink_to('/etc/passwd')
            self.assertFalse(SecurityGate().inspect_tree(p)['ok'])

    def test_key_not_present_in_command_or_disabled_receipt(self):
        worker = HermesWorker(api_key=('DUMMY_' + 'TEST_SECRET'))
        with tempfile.TemporaryDirectory() as tmp:
            command = worker.build_command(Path(tmp) / 'task.md', Path(tmp))
            self.assertNotIn('DUMMY_TEST_SECRET', json.dumps(command))

    def test_evolution_dedup_survives_new_instance(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp)
            with patch.dict(os.environ, {'SELFOPT_HERMES': '0'}):
                first = EvolutionLoop(state, ROOT / 'docs', ROOT).run(max_tasks=2)
                second = EvolutionLoop(state, ROOT / 'docs', ROOT).run(max_tasks=2)
            self.assertFalse({x['fingerprint'] for x in first} & {x['fingerprint'] for x in second})
            self.assertTrue(all(not x['ready_for_human_review'] for x in first))

    def test_charter_boundaries(self):
        for text, allowed in [('wytwarzanie części', True), ('bronowanie pola', True), ('broń', False), ('inwigilacja', False)]:
            result = charter_check([Demand('d', text, [], 'test')], load_charter())
            self.assertEqual(result['ok'], allowed, text)
