import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import subprocess
from tools.agent_claims import reserve, conflicts, collect


class ClaimTests(unittest.TestCase):
    def test_atomic_competing_reservations(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(['git', 'init', '-q', tmp], check=True)
            def attempt(owner):
                try:
                    reserve(root, 'T99', owner, ['module.py'])
                    return True
                except (ValueError, FileExistsError):
                    return False
            with ThreadPoolExecutor(max_workers=2) as pool:
                self.assertEqual(sum(pool.map(attempt, ['one', 'two'])), 1)
            owner = next((root / 'docs/AGENT_CLAIMS').glob('T99-*.md'))
            old = owner.parent / 'T99-old.md'
            old.write_text('- Status: in_progress\n')
            owner.write_text(owner.read_text().replace('in_progress', 'done') + '\n- Decyzja operatora: transfer\n- Supersedes claims: T99-old.md\n')
            self.assertEqual(collect(root), {})

    def test_file_overlap_across_different_tasks(self):
        claims = {'a': {'task': 'T1', 'writes': ['src/*.py']},
                  'b': {'task': 'T2', 'writes': ['src/worker.py']}}
        self.assertEqual(len(conflicts(claims)), 1)
