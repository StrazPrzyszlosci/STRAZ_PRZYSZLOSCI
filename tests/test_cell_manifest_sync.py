import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFESTS = ROOT / "agentic_cells" / "seed_cell_manifests.json"

EXPECTED_DIRS = {
    "edge_flasher": "edge_flasher",
    "resource_scout": "resource_scout",
    "model_resource_selector": "model_resource_selector",
    "potential_pipeline": "potential_pipeline",
    "aquaponics_observer_pack": "PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-phone-aquaponics-observer-01",
    "human_needs_intake": "human_needs",
    "provider_quota_monitor": "provider_quota_monitor",
    "hermes_work_queue": "hermes_work_queue",
    "human_approval": "human_approval",
    "agri_autopilot": "agri_autopilot",
    "agri_edge_agent": "agri_grow_agent",
}


class CellManifestSyncTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(MANIFESTS.read_text(encoding="utf-8"))
        cls.cells = cls.data["cells"]

    def test_every_cell_has_implementation_ref_directory(self):
        for cell in self.cells:
            cid = cell["cell_id"]
            impl = cell.get("implementation_ref", {})
            self.assertTrue(impl.get("directory"), f"{cid}: missing implementation_ref.directory")

    def test_implementation_directories_exist_on_disk(self):
        for cell in self.cells:
            cid = cell["cell_id"]
            directory = cell.get("implementation_ref", {}).get("directory", "")
            self.assertTrue(directory, f"{cid}: no directory to verify")
            path = ROOT / directory
            self.assertTrue(path.is_dir(), f"{cid}: implementation_ref.directory {directory} does not exist on disk")

    def test_implementation_entry_artifacts_exist_on_disk(self):
        for cell in self.cells:
            cid = cell["cell_id"]
            entry = cell.get("implementation_ref", {}).get("entry_artifact", "")
            self.assertTrue(entry, f"{cid}: missing implementation_ref.entry_artifact")
            path = ROOT / entry
            self.assertTrue(path.is_file(), f"{cid}: entry_artifact {entry} does not exist on disk")

    def test_expected_directories_map_matches(self):
        actual = {cell["cell_id"]: cell.get("implementation_ref", {}).get("directory", "") for cell in self.cells}
        self.assertEqual(actual, EXPECTED_DIRS, "cell_id -> directory mismatch; update EXPECTED_DIRS in test or fix manifest")


if __name__ == "__main__":
    unittest.main()