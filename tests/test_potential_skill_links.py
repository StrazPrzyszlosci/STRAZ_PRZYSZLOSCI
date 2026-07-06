import json
import subprocess
import sys
import unittest
from pathlib import Path

from potential_pipeline.validate_skill_links import validate_links

ROOT = Path(__file__).resolve().parents[1]
DOSSIERS = ROOT / "potential_pipeline" / "seed_dossiers.json"
SKILLS = ROOT / "execution_skills" / "seed_skills.json"
SCRIPT = ROOT / "potential_pipeline" / "validate_skill_links.py"


class PotentialSkillLinksTest(unittest.TestCase):
    def test_seed_products_link_to_existing_skills(self):
        result = subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("OK: all PotentialDossier products", result.stdout)

    def test_missing_skill_link_is_rejected(self):
        dossiers = json.loads(DOSSIERS.read_text(encoding="utf-8"))
        skills = json.loads(SKILLS.read_text(encoding="utf-8"))
        dossiers["dossiers"][0]["intended_products"][0].pop("execution_skill_id", None)
        errors = validate_links(dossiers, skills)
        self.assertTrue(errors)
        self.assertIn("must define exactly one", errors[0])


if __name__ == "__main__":
    unittest.main()
