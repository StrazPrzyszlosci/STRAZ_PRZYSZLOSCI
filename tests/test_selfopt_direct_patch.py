import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from selfopt_chain.direct_patch_worker import DirectPatchWorker


class ExactEditTests(unittest.TestCase):
    def run_response(self, response):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp);source = root / 'source';source.mkdir()
            (source / 'sample.py').write_text('def answer():\n    return 1\n')
            worker = DirectPatchWorker([], None, source, root / 'state')
            worker.engine.complete = lambda *args: {'ok': True, 'output': json.dumps(response), 'model_id': 'model'}
            bundle = {'kind': 'patch', 'task_id': 't', 'allowed_paths': ['sample.py'],
                      'input_files': {'sample.py': (source / 'sample.py').read_text()}, 'acceptance': 'contract'}
            with patch('selfopt_chain.direct_patch_worker.repository_snapshot', return_value=(source, 'a' * 40)), \
                 patch('selfopt_chain.direct_patch_worker.validate_patch', return_value={'ok': True}):
                result = worker.run_isolated('input', model_alias='model', input_bundle=bundle)
            result['patch_text'] = (Path(result['quarantine_dir']) / 'changes.patch').read_text() if (Path(result['quarantine_dir']) / 'changes.patch').exists() else ''
            return result

    def test_exact_edit_builds_a_patch(self):
        result = self.run_response({'proposal': 'Fix answer', 'edits': [{'path': 'sample.py', 'old': '    return 1\n', 'new': '    return 2\n'}]})
        self.assertEqual(result['exit_code'], 0)
        self.assertIn('+    return 2', result['patch_text'])

    def test_no_fuzzy_edits_or_scope_escape(self):
        bad = self.run_response({'proposal': 'Fix', 'edits': [{'path': 'sample.py', 'old': 'missing', 'new': 'value'}]})
        self.assertEqual(bad['exit_code'], 1)
        self.assertIn('old_fragment_not_unique', bad['error'])
        bad = self.run_response({'proposal': 'Fix', 'edits': [{'path': '../escape.py', 'old': 'x', 'new': 'y'}]})
        self.assertEqual(bad['exit_code'], 1)
