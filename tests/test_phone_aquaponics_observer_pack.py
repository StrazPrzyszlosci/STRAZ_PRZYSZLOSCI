import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "PROJEKTY" / "13_baza_czesci_recykling" / "execution_packs" / "pack-phone-aquaponics-observer-01"


class PhoneAquaponicsObserverPackTest(unittest.TestCase):
    def test_pack_has_required_files_and_edge_inputs(self):
        for filename in ["manifest.json", "RUNBOOK.md", "REVIEW_CHECKLIST.md"]:
            self.assertTrue((PACK / filename).exists(), filename)
        manifest = json.loads((PACK / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["profile_id"], "phone-aquaponics-observer")
        self.assertIn("edge_flasher device_profile.json", manifest["required_inputs"])
        self.assertIn("edge_flasher install_receipt.json", manifest["required_inputs"])

    def test_execution_steps_do_not_include_forbidden_action_tokens(self):
        runbook = (PACK / "RUNBOOK.md").read_text(encoding="utf-8")
        execution_section = runbook.split("## Execution steps", 1)[1].split("## Out of scope", 1)[0]
        forbidden = ["control_pump", "dose_nutrients", "control_heater", "feed_fish"]
        for token in forbidden:
            self.assertNotIn(token, execution_section)
        self.assertIn("observation", execution_section)
        self.assertIn("human", execution_section)


if __name__ == "__main__":
    unittest.main()
