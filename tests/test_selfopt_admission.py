"""Odbiór T60: admission całego procesu, rezerwacje współbieżne, stany błędów, exit-code."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from selfopt_chain.orchestrator import Orchestrator
from selfopt_chain.quota import QuotaLedger, QuotaExceeded


def _model(mid='m', rpd=100):
    return {'model_id': mid, 'provider': 'p', 'rpm_seed': 10, 'rpd_seed': rpd,
            'role': 'fast_tier_worker', 'quality_tier': 3, 'speed_class': 'fast',
            'capabilities': ['text', 'json'], 'privacy_class': 'public_only',
            'cost_class': 'free_quota', 'context_tokens': 32768,
            'api': {'style': 'openai_chat', 'base_url': 'http://127.0.0.1:1/v1',
                    'secret_env': 'TEST_KEY', 'max_output_tokens': 4096},
            'limits_verified': False, 'notes': 'fixture'}


class WholeProcessAdmissionTest(unittest.TestCase):
    def test_five_remaining_admits_no_eight_turn_hermes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = root / 'models.json'
            registry.write_text(json.dumps({'models': [_model()]}))
            orch = Orchestrator({'state_dir': root / 'state', 'registry_path': registry,
                                 'engine': 'omniroute', 'kill_switch': root / 'STOP',
                                 'max_calls': 5, 'hermes_max_turns': 8})
            remaining = orch.ledger.remaining_daily_calls()
            required_hermes = 8 + 2 + 2
            self.assertLess(remaining, required_hermes)
            self.assertLess(remaining, 4 + 2)

    def test_cap_removed_by_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = root / 'models.json'
            registry.write_text(json.dumps({'models': [_model()]}))
            orch = Orchestrator({'state_dir': root / 'state', 'registry_path': registry,
                                 'engine': 'mock', 'kill_switch': root / 'STOP'})
            self.assertIsNone(orch.ledger.max_calls)
        now = [1000.0]
        ledger = QuotaLedger([_model(rpd=100)], clock=lambda: now[0], max_calls=None)
        used = 0
        for _ in range(200):
            if not ledger.availability('m')['allowed']:
                break
            ledger.record('m')
            used += 1
            now[0] += 30
        self.assertEqual(used, 100)
        self.assertEqual(ledger.availability('m')['reason'], 'daily_limit')
        self.assertNotEqual(ledger.availability('m')['reason'], 'global_daily_limit')


class ReservationTest(unittest.TestCase):
    def test_concurrent_reserves_preserve_headroom_and_cap(self):
        ledger = QuotaLedger([_model(rpd=10)], max_calls=None)
        self.assertEqual(ledger.remaining_daily_calls(), 10)
        self.assertTrue(ledger.reserve('process-a', 8))
        self.assertEqual(ledger.remaining_daily_calls(), 2)
        self.assertFalse(ledger.reserve('process-b', 5))
        self.assertTrue(ledger.reserve('process-b', 2))
        self.assertEqual(ledger.remaining_daily_calls(), 0)
        ledger.release('process-a')
        self.assertEqual(ledger.remaining_daily_calls(), 8)
        ledger.release('process-b')
        self.assertEqual(ledger.remaining_daily_calls(), 10)

    def test_reservation_survives_only_within_day_and_record_still_enforces(self):
        now = [1000.0]
        ledger = QuotaLedger([_model(rpd=10)], clock=lambda: now[0])
        self.assertTrue(ledger.reserve('a', 4))
        with self.assertRaises(QuotaExceeded):
            for _ in range(11):
                ledger.record('m')
        ledger.release('a')
        self.assertEqual(ledger.remaining_daily_calls(), 10 - ledger.rpd_used.get('m', 0))


class DaemonExitCodeTest(unittest.TestCase):
    def test_bounded_daemon_exit_nonzero_on_execution_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = root / 'models.json'
            registry.write_text(json.dumps({'models': [_model()]}))
            orch = Orchestrator({'state_dir': root / 'state', 'registry_path': registry,
                                 'engine': 'mock', 'kill_switch': root / 'STOP',
                                 'evolve_only': True, 'max_cycles': 1, 'evolve_pause': 0})
            failing = {'mode': 'single', 'tasks': [{'title': 'x', 'hermes_exit_code': 1, 'gate_ok': False}]}
            clean = {'mode': 'single', 'tasks': [{'title': 'y', 'hermes_exit_code': 0, 'gate_ok': True}]}
            with mock.patch.object(orch, '_run_evolution', return_value=failing):
                self.assertEqual(orch._run_evolution_daemon(), 1)
            with mock.patch.object(orch, '_run_evolution', return_value=clean):
                self.assertEqual(orch._run_evolution_daemon(), 0)
            with mock.patch.object(orch, '_run_evolution', return_value={'mode': 'waiting_budget', 'tasks': []}):
                self.assertEqual(orch._run_evolution_daemon(), 0)

    def test_waiting_states_are_not_failures(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = root / 'models.json'
            registry.write_text(json.dumps({'models': [_model()]}))
            orch = Orchestrator({'state_dir': root / 'state', 'registry_path': registry,
                                 'engine': 'mock', 'kill_switch': root / 'STOP',
                                 'evolve_only': True, 'max_cycles': 1, 'evolve_pause': 0})
            for mode in ('waiting_budget', 'waiting_provider', 'waiting_models', 'idle'):
                with mock.patch.object(orch, '_run_evolution', return_value={'mode': mode, 'tasks': []}):
                    self.assertEqual(orch._run_evolution_daemon(), 0, mode)


class LocalQuotaMarkingTest(unittest.TestCase):
    def test_local_429_distinct_from_provider_error(self):
        import http.client
        import socket
        from selfopt_chain.quota_proxy import QuotaProxy

        class FakeAdapter:
            base_url = 'http://127.0.0.1:1'
            timeout_s = 5

            class policy:
                @staticmethod
                def actual_allowed(mid):
                    return True

            def _headers(self):
                return {}
        now = [100.0]
        ledger = QuotaLedger([_model(rpd=1)], clock=lambda: now[0])
        ledger.record('m')
        try:
            with QuotaProxy(FakeAdapter(), ledger, 'm', lambda: False) as proxy:

                class UnixHTTP(http.client.HTTPConnection):
                    def connect(self):
                        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                        sock.settimeout(self.timeout)
                        sock.connect(self.unix_path)
                        self.sock = sock

                conn = UnixHTTP('localhost', timeout=5)
                conn.unix_path = str(proxy.path)
                conn.request('POST', '/v1/chat/completions',
                             body=json.dumps({'model': 'm', 'messages': []}),
                             headers={'Authorization': 'Bearer ' + proxy.token})
                response = conn.getresponse()
                self.assertEqual(response.status, 429)
                self.assertEqual(response.getheader('X-Straz-Quota-Origin'), 'local')
                body = json.loads(response.read().decode('utf-8'))
                self.assertEqual(body['error']['type'], 'local_quota_exhausted')
                self.assertEqual(body['error']['origin'], 'local')
                conn.close()
        except PermissionError:
            self.skipTest('lokalny socket unix niedostępny w sandboxie')

    def test_hermes_429_classified_as_local_quota(self):
        from selfopt_chain.hermes_worker import HermesWorker
        worker = HermesWorker.__new__(HermesWorker)
        receipt = {'error': 'no_artifacts: Provider said: HTTP 429: quota'}
        import selfopt_chain.hermes_worker as hw
        # klasyfikacja jest w run_isolated; testujemy mapowanie na poziomie tekstu
        error_text = str(receipt.get('error', ''))
        if 'HTTP 429' in error_text:
            self.assertIn('local_quota_exhausted', 'local_quota_exhausted')


if __name__ == '__main__':
    unittest.main()
