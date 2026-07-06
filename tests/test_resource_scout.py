import json
import subprocess
import sys
import unittest
from pathlib import Path

from resource_scout.validate_records import validate_records

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "resource_scout" / "validate_records.py"
EXAMPLES = [
    ROOT / "resource_scout" / "examples" / "ewaste_phone_batch.json",
    ROOT / "resource_scout" / "examples" / "selfhost_compute_node.json",
]


class ResourceScoutTest(unittest.TestCase):
    def test_examples_are_valid(self):
        for example in EXAMPLES:
            result = subprocess.run([sys.executable, str(SCRIPT), str(example)], cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertIn("OK: resource scout records valid", result.stdout)

    def test_missing_cost_location_or_risks_is_blocked(self):
        record = json.loads(EXAMPLES[0].read_text(encoding="utf-8"))
        bad = record["records"][0]
        bad.pop("location")
        bad.pop("cost")
        bad["risks"] = []
        errors = validate_records(record)
        self.assertTrue(any("location" in error for error in errors))
        self.assertTrue(any("cost" in error for error in errors))
        self.assertTrue(any("risk" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
