"""Controller-owned acceptance: a bounded failed evolution run must report failure."""
import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT))
from selfopt_chain.orchestrator import Orchestrator


class DaemonExitContract(unittest.TestCase):
    def run_case(self, tasks):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp)
            config = {'engine': 'mock', 'state_dir': state, 'kill_switch': state / 'STOP',
                      'registry_path': ROOT / 'selfopt_chain/free_models.json', 'records_paths': [],
                      'max_jobs': 1, 'max_cycles': 1, 'evolve_only': True, 'evolve_pause': 0}
            runner = Orchestrator(config)
            with patch.object(runner, '_run_evolution', return_value={'mode': 'single', 'tasks': tasks}), contextlib.redirect_stdout(io.StringIO()):
                return runner.run()

    def test_unresolved_worker_failure_is_nonzero(self):
        self.assertNotEqual(self.run_case([{'status': 'needs_fixes', 'executor': 'hermes', 'hermes_exit_code': 1}]), 0)

    def test_ready_result_is_success(self):
        self.assertEqual(self.run_case([{'status': 'ready', 'executor': 'hermes', 'hermes_exit_code': 0, 'gate_ok': True}]), 0)

    def test_ready_direct_patch_is_success(self):
        self.assertEqual(self.run_case([{'status': 'ready', 'executor': 'direct_patch', 'worker_exit_code': 0, 'hermes_exit_code': None, 'gate_ok': True}]), 0)

    def test_failed_direct_patch_is_nonzero(self):
        self.assertNotEqual(self.run_case([{'status': 'needs_fixes', 'executor': 'direct_patch', 'worker_exit_code': 1, 'hermes_exit_code': None, 'gate_ok': False}]), 0)

    def test_empty_queue_is_not_a_failure(self):
        self.assertEqual(self.run_case([]), 0)


if __name__ == '__main__':
    unittest.main()
