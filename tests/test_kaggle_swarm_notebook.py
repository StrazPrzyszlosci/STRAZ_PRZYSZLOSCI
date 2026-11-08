"""Static checks for the standalone Kaggle swarm notebook (no Kaggle runtime required)."""
import ast
import json
import unittest
from pathlib import Path

NOTEBOOK = Path(__file__).resolve().parents[1] / "notebooks" / "kaggle_selfopt_swarm.ipynb"


class KaggleSwarmNotebookTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))

    def test_notebook_structure(self):
        self.assertEqual(self.notebook["nbformat"], 4)
        self.assertGreaterEqual(len(self.notebook["cells"]), 6)
        self.assertTrue(any(cell["cell_type"] == "markdown" for cell in self.notebook["cells"]))

    def test_python_source_parses(self):
        for index, cell in enumerate(self.notebook["cells"]):
            if cell["cell_type"] == "code":
                with self.subTest(index=index):
                    ast.parse("".join(cell["source"]), filename=f"cell_{index}")

    def test_no_saved_execution_or_credentials(self):
        sources = []
        for cell in self.notebook["cells"]:
            if cell["cell_type"] == "code":
                self.assertIsNone(cell["execution_count"])
                self.assertEqual(cell["outputs"], [])
                sources.append("".join(cell["source"]))
        content = "\n".join(sources)
        self.assertIn('MODE = "demo"', content)
        self.assertIn('HERMES_MODE = "off"', content)
        self.assertIn('SELFOPT_HERMES', content)
        self.assertIn('STRICT_ZERO_COST', content)
        self.assertIn('MAX_CALLS_PER_DAY', content)
        self.assertIn('kaggle_secret("OMNIROUTE_ENDPOINT_KEY")', content)
        self.assertNotIn("ghp_", content)
        self.assertNotIn("sk-proj-", content)

    def test_no_unbounded_default(self):
        source = "\n".join("".join(c["source"]) for c in self.notebook["cells"] if c["cell_type"] == "code")
        self.assertIn('RUN_SECONDS = 600', source)
        self.assertIn('RUN_CYCLES = 2', source)
        self.assertIn('--max-seconds', source)
        self.assertIn('--max-calls', source)
        self.assertIn('swarm_state.zip', source)
        self.assertIn('manual_review_required', source)


if __name__ == "__main__":
    unittest.main()
