import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from selfopt_chain.omniroute import FreeOnlyPolicy, OmniRouteAdapter, response_diagnostic
from selfopt_chain.orchestrator import Orchestrator
from selfopt_chain.quota import QuotaLedger
from selfopt_chain.registry import load_registry
from selfopt_chain.evolver import EvolutionLoop, EvolutionTask
from selfopt_chain.swarm import BasalDecisionCore


class ProviderDiagnosticTests(unittest.TestCase):
    def test_empty_response_preserves_time_and_counts_without_reasoning_text(self):
        model = load_registry()[0]
        adapter = OmniRouteAdapter(FreeOnlyPolicy([model]), api_key='test-only')
        payload = {'model': model['model_id'], 'choices': [{'finish_reason': 'length',
                   'message': {'content': '', 'reasoning_content': 'DO_NOT_RECORD_REASONING'}}],
                   'usage': {'completion_tokens': 4096, 'completion_tokens_details': {'reasoning_tokens': 4096}}}
        with mock.patch.dict('os.environ', {'SELFOPT_NETWORK': '1'}), \
             mock.patch('urllib.request.urlopen', return_value=io.BytesIO(json.dumps(payload).encode())), \
             mock.patch('selfopt_chain.omniroute.time.monotonic', side_effect=[100.0, 100.125]):
            result = adapter.complete({'privacy': 'public'}, 'public fixture', model['model_id'])
        self.assertFalse(result['ok'])
        self.assertEqual(result['error_class'], 'bad_response')
        self.assertEqual(result['latency_ms'], 125)
        self.assertEqual(result['response_diagnostic']['finish_reason'], 'length')
        self.assertEqual(result['response_diagnostic']['usage']['reasoning_tokens'], 4096)
        self.assertNotIn('DO_NOT_RECORD_REASONING', json.dumps(result))

    def test_non_json_and_non_object_fail_closed(self):
        model = load_registry()[0]
        for body in [b'not json', b'[]']:
            with self.subTest(body=body), mock.patch.dict('os.environ', {'SELFOPT_NETWORK': '1'}), \
                 mock.patch('urllib.request.urlopen', return_value=io.BytesIO(body)):
                result = OmniRouteAdapter(FreeOnlyPolicy([model])).complete({'privacy': 'public'}, 'fixture', model['model_id'])
                self.assertEqual(result['error_class'], 'bad_response')

    def test_diagnostic_never_copies_unknown_fields_or_finish_text(self):
        payload = {'choices': [{'finish_reason': {'secret': 'DO_NOT_COPY'},
                   'message': {'api_key': 'DO_NOT_COPY', 'content': None}}],
                   'usage': {'secret': 'DO_NOT_COPY', 'total_tokens': 15}}
        diagnostic = response_diagnostic(payload)
        self.assertEqual(diagnostic['finish_reason'], 'other')
        self.assertEqual(diagnostic['usage'], {'total_tokens': 15})
        self.assertNotIn('DO_NOT_COPY', json.dumps(diagnostic))

    def test_cooldown_and_budget_have_distinct_reasons(self):
        now = [100.0]
        models = [{'model_id': 'one', 'provider': 'p', 'rpm_seed': 10, 'rpd_seed': 100}]
        ledger = QuotaLedger(models, max_calls=10, clock=lambda: now[0])
        ledger.record('one')
        ledger.record_outcome('one', {'ok': False, 'error_class': 'connection_error'})
        self.assertEqual(ledger.availability('one')['reason'], 'provider_cooldown')
        self.assertEqual(ledger.rpd_used['one'], 1)
        ledger.max_calls = 1
        self.assertEqual(ledger.availability('one')['reason'], 'global_daily_limit')
        ledger.max_calls = 10
        now[0] += 121
        self.assertTrue(ledger.availability('one')['allowed'])

    def test_daemon_reports_provider_wait_without_spending_more_calls(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            model = load_registry()[0]
            registry = root / 'models.json'
            registry.write_text(json.dumps({'models': [model]}))
            orchestrator = Orchestrator({'state_dir': root / 'state', 'registry_path': registry,
                'engine': 'omniroute', 'kill_switch': root / 'STOP', 'max_calls': 100})
            orchestrator.ledger.record(model['model_id'])
            orchestrator.ledger.record_outcome(model['model_id'], {'ok': False, 'error_class': 'connection_error'})
            with mock.patch('selfopt_chain.orchestrator.quota_gate', return_value={'allowed': True}):
                result = orchestrator._run_evolution()
            self.assertEqual(result['mode'], 'waiting_provider')
            self.assertEqual(result['resource_status'][model['model_id']]['reason'], 'provider_cooldown')
            self.assertEqual(orchestrator.ledger.rpd_used[model['model_id']], 1)

    def test_model_selection_sees_measured_transport_history(self):
        models = [{'model_id': name, 'provider': 'p', 'rpm_seed': 10, 'rpd_seed': 100,
                   'quality_tier': 4, 'speed_class': 'fast', 'cost_class': 'free_quota',
                   'privacy_class': 'public_only', 'capabilities': ['text'], 'context_tokens':32768}
                  for name in ['first-failing', 'working']]
        now = [100.0]
        ledger = QuotaLedger(models, clock=lambda: now[0])
        for _ in range(2):
            ledger.record_outcome('first-failing', {'ok': False, 'error_class': 'connection_error'})
            ledger.record_outcome('working', {'ok': True, 'latency_ms': 200})
        now[0] += 1000
        with tempfile.TemporaryDirectory() as tmp, mock.patch.dict('os.environ', {'SELFOPT_BASAL_URL': ''}):
            core = BasalDecisionCore()
            worker = mock.Mock(models=models, ledger=ledger)
            loop = EvolutionLoop(Path(tmp), Path(tmp), Path(tmp), worker=worker, models=models,
                                 lane_models=[m['model_id'] for m in models], decision_core=core)
            selected = loop._lane_model(0, EvolutionTask('test', 'work', 'test'))
            self.assertEqual(selected, 'working')
            observations = core.decisions[-1]['context']['model_characteristics']['first-failing']['observed_transport']
            self.assertEqual(observations['failures'], 2)

    def test_invalid_basal_probabilities_fall_back_instead_of_crashing(self):
        cases = [({'a': 'invalid', 'b': 1}, 1), ({'a': True, 'b': False}, 1),
                 ({'a': 1}, 1), ({'a': 0, 'b': 0}, 0),
                 ({'a': 0.8, 'b': 0.8}, 0.8), ({'a': 0.7, 'b': 0.3}, 1),
                 ({'a': float('nan'), 'b': 0.5}, 0.5)]
        for probabilities, confidence in cases:
            payload = {'answers': {'decision': {'probabilities': probabilities, 'confidence': confidence}}}
            with self.subTest(probabilities=probabilities), \
                 mock.patch('urllib.request.urlopen', return_value=io.BytesIO(json.dumps(payload).encode())):
                core = BasalDecisionCore()
                core.remote_url = 'http://127.0.0.1:8000'
                decision = core.decide('model_selection', ['a', 'b'], {'a': 2.0, 'b': 1.0}, default_option='a')
                self.assertEqual(decision['engine'], 'builtin')
                self.assertEqual(decision['final'], 'a')

    def test_valid_basal_choice_remains_authoritative(self):
        payload = {'answers': {'decision': {'probabilities': {'a': 0.2, 'b': 0.8}, 'confidence': 0.8}}}
        with mock.patch('urllib.request.urlopen', return_value=io.BytesIO(json.dumps(payload).encode())):
            core = BasalDecisionCore()
            core.remote_url = 'http://127.0.0.1:8000'
            result = core.decide('model_selection', ['a', 'b'], {'a': 2.0, 'b': 1.0}, default_option='a')
            self.assertEqual(result['engine'], 'basal-serve')
            self.assertEqual(result['final'], 'b')


if __name__ == '__main__':
    unittest.main()
