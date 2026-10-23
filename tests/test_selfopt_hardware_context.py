import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from selfopt_chain.hardware_context import collect_hardware_context
from selfopt_chain.swarm import BasalDecisionCore
from selfopt_chain.evolver import EvolutionLoop, EvolutionTask, generate_llm_strategy
from selfopt_chain.evolution_inputs import task_prompt
from selfopt_chain.model_selection import shortlist_models


class HardwareContextTests(unittest.TestCase):
    def test_ancestor_process_limits_override_host_capacity_without_identifiers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            files = {'proc/meminfo': 'MemTotal: 32768 kB\nMemAvailable: 16384 kB\n',
                     'proc/cpuinfo': 'model name : Example CPU\nSerial : NEVER_EXPORT_THIS\n',
                     'proc/self/cgroup': '0::/user/worker\n',
                     'sys/fs/cgroup/user/cpu.max': '200000 100000',
                     'sys/fs/cgroup/user/memory.max': str(12 * 1024 * 1024),
                     'sys/fs/cgroup/user/memory.current': str(5 * 1024 * 1024),
                     'sys/fs/cgroup/user/worker/cpu.max': 'max 100000',
                     'sys/class/drm/card0/device/vendor': '0x10de',
                     'sys/class/drm/card0/device/device': '0x1234'}
            for name, value in files.items():
                p = root / name
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(value)
            with patch('os.cpu_count', return_value=16), patch('os.sched_getaffinity', return_value=set(range(8))):
                context = collect_hardware_context(root, proc_root=root / 'proc', sys_root=root / 'sys')
            self.assertEqual(context['cpu']['effective_cores'], 2)
            self.assertEqual(context['memory']['effective_available_bytes'], 7 * 1024 * 1024)
            self.assertEqual(context['gpus'][0]['vendor_id'], '0x10de')
            self.assertFalse(context['gpus'][0]['inference_backend_verified'])
            self.assertNotIn('NEVER_EXPORT_THIS', json.dumps(context))
            self.assertNotIn(str(root), json.dumps(context))

    def test_missing_hardware_measurement_is_unknown_not_zero_or_free_total(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'meminfo').write_text('MemTotal: 32768 kB\n')
            with patch('shutil.disk_usage', side_effect=OSError('not observable')):
                context = collect_hardware_context(root, proc_root=root, sys_root=root / 'missing')
            self.assertIsNone(context['memory']['effective_available_bytes'])
            self.assertIsNone(context['workspace_storage']['free_bytes'])

    def test_current_hardware_reaches_local_basal_without_mutating_caller_context(self):
        hardware = {'scope': 'orchestrator_host', 'cpu': {'effective_cores': 2}}
        caller = {'task_id': 'task'}
        reply = {'answers': {'decision': {'probabilities': {'a': .2, 'b': .8}, 'confidence': .8}}}
        core = BasalDecisionCore(hardware_context=hardware)
        core.remote_url = 'http://127.0.0.1:8000'
        with patch('urllib.request.urlopen', return_value=io.BytesIO(json.dumps(reply).encode())) as request:
            result = core.decide('model_selection', ['a', 'b'], {'a': 2, 'b': 1}, context=caller)
        state = json.loads(json.loads(request.call_args.args[0].data)['state'])
        self.assertEqual(state['kontekst_roju']['hardware_context'], hardware)
        self.assertEqual(result['engine'], 'basal-serve')
        self.assertEqual(caller, {'task_id': 'task'})

    def test_hardware_is_available_to_strategy_and_worker_without_reversioning_task(self):
        hardware = {'cpu': {'effective_cores': 2}, 'memory': {'effective_available_bytes': 1024}}
        task = EvolutionTask('t', 'public proposal', 'test')
        strategy = Mock()
        strategy.complete.return_value = {'ok': False, 'error_class': 'offline'}
        generate_llm_strategy([task], strategy, hardware)
        self.assertIn(json.dumps(hardware), strategy.complete.call_args.args[2])
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            core = BasalDecisionCore(hardware_context=hardware)
            loop = EvolutionLoop(root, root, root, decision_core=core)
            with patch('selfopt_chain.evolver.collect_evolution_tasks', return_value=[task]):
                self.assertEqual(len(loop.pending()), 1)
                original_hash = next(iter(loop.inputs.values()))['input_hash']
                receipt = loop.run(1)[0]
                manifest = json.loads((Path(receipt['receipt_path']).parent / 'input_manifest.json').read_text())
                self.assertEqual(manifest['hardware_context'], hardware)
                self.assertEqual(manifest['input_hash'], original_hash)
                self.assertIn(json.dumps(hardware), task_prompt(manifest))

    def test_remote_model_size_is_not_constrained_by_host_hardware(self):
        models = [{'model_id': 'cloud-large', 'quality_tier': 5, 'speed_class': 'slow',
                   'privacy_class': 'public_only', 'cost_class': 'free_quota',
                   'capabilities': ['text', 'code', 'json'], 'context_tokens': 1000000}]
        result = shortlist_models(models, kind='code_draft')
        self.assertEqual(result['candidates'], ['cloud-large'])
        self.assertEqual(result['details']['cloud-large']['execution_location'], 'remote_api')
        self.assertFalse(result['details']['cloud-large']['host_hardware_limits_model_size'])


if __name__ == '__main__':
    unittest.main()
