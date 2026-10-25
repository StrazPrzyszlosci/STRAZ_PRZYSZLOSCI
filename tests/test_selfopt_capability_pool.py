"""T65: pula kandydatów basala — podłoga kompetencji recenzenta, profile NIM, auto-etykiety, kadencja celów."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from selfopt_chain import evolution_inputs as ei
from selfopt_chain.evolver import EvolutionTask, _parse_targets, auto_label_outcome, reviewer_floor, review_by_strong_model, run_budget_for
from selfopt_chain.hermes_worker import write_runtime_inputs
from selfopt_chain.router import DEFAULT_REQUIRED_TIER, required_tier_for_kind


def _registry(*rows):
    return [dict(model_id=mid, quality_tier=tier, routing_roles=roles, cost_class='free_quota',
                 privacy_class='public_only', capabilities=['text', 'json'], speed_class='medium',
                 context_tokens=100000, provider='p', role='x') for mid, tier, roles in rows]


class FakeEngine:
    def __init__(self, ok=True, model_id='reviewer'):
        self.ok, self.model_id, self.calls = ok, model_id, []

    def complete(self, task, alias, prompt):
        self.calls.append(alias)
        return {'ok': self.ok, 'output': '{"verdict": "pass", "notes": "ok"}', 'model_id': self.model_id}


class ReviewerFloorTest(unittest.TestCase):
    def test_review_kind_requires_strong_tier(self):
        self.assertGreaterEqual(required_tier_for_kind('review'), 4)

    def test_reviewer_floor_requires_producer_tier(self):
        reg = _registry(('weak/producer', 2, ['code_draft']), ('r4', 4, ['review']), ('r5', 5, ['review']))
        required, best = reviewer_floor('weak/producer', reg)
        self.assertEqual(required, 4)
        self.assertEqual(best, 'r5')

    def test_reviewer_floor_never_below_strong_producer(self):
        reg = _registry(('strong/producer', 5, ['code_draft']), ('r4', 4, ['review']), ('r5', 5, ['review']))
        required, best = reviewer_floor('strong/producer', reg)
        self.assertEqual(required, 5)
        self.assertEqual(best, 'r5')

    def test_reviewer_floor_fail_closed_without_qualified_reviewer(self):
        reg = _registry(('p', 2, ['code_draft']), ('r2', 2, ['review']))
        required, best = reviewer_floor('p', reg)
        self.assertGreaterEqual(required, 4)
        self.assertIsNone(best)
        task = EvolutionTask(task_id='t', title='T', source='test')
        out = review_by_strong_model(task, 'produkcja', FakeEngine(), producer_alias='p', registry=reg)
        self.assertEqual(out['verdict'], 'unreviewed')
        self.assertIn('no_reviewer_at_required_tier', out['notes'])

    def test_review_picks_strongest_qualified_reviewer(self):
        reg = _registry(('p', 2, ['code_draft']), ('r4', 4, ['review']), ('r5', 5, ['review']))
        engine = FakeEngine()
        task = EvolutionTask(task_id='t', title='T', source='test')
        out = review_by_strong_model(task, 'produkcja', engine, producer_alias='p', registry=reg)
        self.assertEqual(engine.calls[-1], 'r5')
        self.assertEqual(out['verdict'], 'pass')


class ProfilesTest(unittest.TestCase):
    def test_profiles_shape_and_nim_presence(self):
        data = json.loads(Path('selfopt_chain/runtime_model_profiles.json').read_text(encoding='utf-8'))
        profiles = data['profiles']
        self.assertGreaterEqual(len(profiles), 10)
        self.assertIn('nvidia/z-ai/glm-5.3', profiles)
        for mid, p in profiles.items():
            self.assertIsInstance(p['quality_tier'], int)
            self.assertTrue(1 <= p['quality_tier'] <= 5, mid)
            self.assertTrue(p['routing_roles'], mid)
            for role in p['routing_roles']:
                self.assertIn(role, DEFAULT_REQUIRED_TIER, f'{mid}: nieznana rola {role}')
            self.assertTrue(p['basis'], mid)
        for mid in ('nvidia/z-ai/glm-5.3', 'nvidia/nvidia/nemotron-3-ultra-550b-a55b',
                    'nvidia/nvidia/llama-3.1-nemotron-70b-instruct', 'kilocode/nvidia/nemotron-3-ultra-550b-a55b:free'):
            self.assertIn(mid, profiles)

    def test_periodic_target_declares_cadence(self):
        targets = {t.task_id: t for t in _parse_targets()}
        self.assertEqual(targets['target_free_models_registry_refresh'].reset_after_days, 14)

    def test_periodic_input_hash_rotates_with_time_bucket(self):
        task = EvolutionTask(task_id='target_x', title='X', source='test',
                            input_refs=['selfopt_chain/README.md'], reset_after_days=14)
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(ei.time, 'time', return_value=0.0):
                h1 = ei.prepare_inputs(task, '.', tmp)['input_hash']
            with mock.patch.object(ei.time, 'time', return_value=14 * 86400 + 1.0):
                h2 = ei.prepare_inputs(task, '.', tmp)['input_hash']
            with mock.patch.object(ei.time, 'time', return_value=13 * 86400):
                h3 = ei.prepare_inputs(task, '.', tmp)['input_hash']
        self.assertNotEqual(h1, h2)
        self.assertEqual(h1, h3)


class AutoLabelTest(unittest.TestCase):
    def test_auto_label_from_mechanical_outcome_and_dedup(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp)
            (state / 'decisions.jsonl').write_text(json.dumps({'id': 'd1', 'question_type': 'model_selection',
                'chosen': 'm/a', 'final': 'm/a', 'confidence': 1.0, 'engine': 'basal'}) + '\n', encoding='utf-8')
            first = auto_label_outcome(state, 'm/a', False, 'task_x: needs_fixes (auto, T65)')
            self.assertEqual(first, 'd1')
            rows = [json.loads(line) for line in (state / 'labels.jsonl').read_text(encoding='utf-8').splitlines()]
            self.assertEqual(rows[-1]['decision_id'], 'd1')
            self.assertFalse(rows[-1]['accepted'])
            self.assertEqual(rows[-1]['source'], 'auto_outcome')
            self.assertIsNone(auto_label_outcome(state, 'm/a', True, 'task_y: ready (auto, T65)'))

    def test_auto_label_silent_when_no_matching_decision(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp)
            (state / 'decisions.jsonl').write_text(json.dumps({'id': 'd2', 'question_type': 'model_selection',
                'chosen': 'm/b', 'final': 'm/b', 'confidence': 1.0, 'engine': 'basal'}) + '\n', encoding='utf-8')
            self.assertIsNone(auto_label_outcome(state, 'm/missing', True, 'x'))
            self.assertFalse((state / 'labels.jsonl').exists())


    def test_run_budget_scales_with_model_speed(self):
        self.assertEqual(run_budget_for({'speed_class': 'slow'}), 900)
        self.assertEqual(run_budget_for({'speed_class': 'medium'}), 540)
        self.assertEqual(run_budget_for({'speed_class': 'fast'}), 360)
        self.assertEqual(run_budget_for({}), 360)
        self.assertEqual(run_budget_for(None), 360)


class RuntimeInputsTest(unittest.TestCase):
    def test_write_runtime_inputs_materializes_jsonl_and_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            inputs = Path(tmp)
            bundle = {'runtime_metadata': {
                'decisions.jsonl': [{'id': 'd1', 'final': 'm/a'}, {'id': 'd2', 'final': 'm/b'}],
                'labels.jsonl': [{'decision_id': 'd1', 'accepted': True, 'source': 'auto_outcome'}],
                'extra.json': {'k': 'v'},
            }}
            written = write_runtime_inputs(inputs, bundle)
            self.assertEqual(len(written), 3)
            rows = [json.loads(line) for line in (inputs / 'decisions.jsonl').read_text(encoding='utf-8').splitlines()]
            self.assertEqual([r['id'] for r in rows], ['d1', 'd2'])
            labels = [json.loads(line) for line in (inputs / 'labels.jsonl').read_text(encoding='utf-8').splitlines()]
            self.assertEqual(labels[0]['decision_id'], 'd1')
            self.assertEqual(json.loads((inputs / 'extra.json').read_text(encoding='utf-8')), {'k': 'v'})

    def test_task_prompt_points_to_runtime_files(self):
        manifest = {'task_id': 't', 'title': 'T', 'context': '', 'constraints': '', 'kind': 'proposal',
                    'allowed_paths': [], 'expected_outputs': ['output/PROPOSAL.md'],
                    'input_files': {}, 'runtime_metadata': {'decisions.jsonl': [], 'labels.jsonl': []},
                    'previous_feedback': {}}
        prompt = ei.task_prompt(manifest)
        self.assertIn('/input/decisions.jsonl', prompt)
        self.assertIn('/input/labels.jsonl', prompt)
        self.assertIn('Nie szukaj', prompt)

    def test_task_prompt_without_runtime_has_no_dead_hint(self):
        manifest = {'task_id': 't', 'title': 'T', 'context': '', 'constraints': '', 'kind': 'proposal',
                    'allowed_paths': [], 'expected_outputs': ['output/PROPOSAL.md'],
                    'input_files': {}, 'runtime_metadata': {}, 'previous_feedback': {}}
        prompt = ei.task_prompt(manifest)
        self.assertNotIn('Dane runtime', prompt)


if __name__ == '__main__':
    unittest.main()
