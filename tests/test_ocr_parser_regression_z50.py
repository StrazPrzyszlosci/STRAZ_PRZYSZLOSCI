import importlib.util
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = (
    REPO_ROOT
    / "PROJEKTY"
    / "13_baza_czesci_recykling"
    / "scripts"
    / "verify_candidates.py"
)
REPORTS_DIR = (
    REPO_ROOT
    / "PROJEKTY"
    / "13_baza_czesci_recykling"
    / "autonomous_test"
    / "reports"
)


def _load_verify_module():
    spec = importlib.util.spec_from_file_location("verify_candidates", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class TestOCRParserRegression(unittest.TestCase):
    """Regression tests for OCR decision parser (zadanie 50).

    The audit in zadanie 42 found that markdown-wrapped **YES** / **NO**
    was misclassified as inconclusive.  These tests guarantee that
    parse_ocr_decision() strips markdown formatting and returns the
    correct verification status.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_verify_module()

    def test_plain_yes(self) -> None:
        self.assertEqual(self.module.parse_ocr_decision("YES"), "confirmed")

    def test_plain_no(self) -> None:
        self.assertEqual(self.module.parse_ocr_decision("NO"), "rejected")

    def test_bold_yes(self) -> None:
        self.assertEqual(self.module.parse_ocr_decision("**YES**"), "confirmed")

    def test_bold_no(self) -> None:
        self.assertEqual(self.module.parse_ocr_decision("**NO**"), "rejected")

    def test_answer_prefix_yes(self) -> None:
        self.assertEqual(self.module.parse_ocr_decision("Answer: YES"), "confirmed")

    def test_answer_prefix_no(self) -> None:
        self.assertEqual(self.module.parse_ocr_decision("Answer: NO"), "rejected")

    def test_italic_bold_yes(self) -> None:
        self.assertEqual(self.module.parse_ocr_decision("***YES***"), "confirmed")

    def test_backtick_yes(self) -> None:
        self.assertEqual(self.module.parse_ocr_decision("`YES`"), "confirmed")

    def test_heading_yes(self) -> None:
        self.assertEqual(self.module.parse_ocr_decision("# YES"), "confirmed")

    def test_leading_whitespace_yes(self) -> None:
        self.assertEqual(self.module.parse_ocr_decision("  YES"), "confirmed")

    def test_no_with_reason(self) -> None:
        self.assertEqual(self.module.parse_ocr_decision("NO. The part is not valid."), "rejected")

    def test_bold_yes_with_reason(self) -> None:
        self.assertEqual(self.module.parse_ocr_decision("**YES** - valid MPN"), "confirmed")

    def test_garbage_input_returns_none(self) -> None:
        self.assertIsNone(self.module.parse_ocr_decision("MAYBE"))

    def test_empty_input_returns_none(self) -> None:
        self.assertIsNone(self.module.parse_ocr_decision(""))

    def test_none_input_returns_none(self) -> None:
        self.assertIsNone(self.module.parse_ocr_decision(None))

    def test_case_insensitive(self) -> None:
        self.assertEqual(self.module.parse_ocr_decision("**yes**"), "confirmed")
        self.assertEqual(self.module.parse_ocr_decision("**no**"), "rejected")


class TestStalePacketGuard(unittest.TestCase):
    """Stale packet guard tests (zadanie 50).

    When status_resolution_packet.json has 0 deferred cases,
    ocr-selector must write total_ocr_cases: 0 instead of
    retaining stale case lists from prior runs.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_verify_module()

    def test_ocr_deferred_packet_zero_cases_when_no_deferred(self) -> None:
        packet_path = REPORTS_DIR / "ocr_deferred_case_packet.json"
        if not packet_path.exists():
            self.skipTest("ocr_deferred_case_packet.json not yet generated")
        with open(packet_path, "r", encoding="utf-8") as f:
            packet = json.load(f)
        self.assertEqual(packet.get("total_ocr_cases", -1), 0,
                         "ocr_deferred_case_packet.json should have total_ocr_cases=0 when no deferred cases remain")

    def test_status_resolution_zero_deferred_implies_empty_ocr_cases(self) -> None:
        resolution_path = REPORTS_DIR / "status_resolution_packet.json"
        if not resolution_path.exists():
            self.skipTest("status_resolution_packet.json not yet generated")
        with open(resolution_path, "r", encoding="utf-8") as f:
            resolution = json.load(f)
        ocr_remaining = resolution.get("ocr_needed_remaining", [])
        manual_remaining = resolution.get("manual_review_remaining", [])
        if len(ocr_remaining) == 0 and len(manual_remaining) == 0:
            packet_path = REPORTS_DIR / "ocr_deferred_case_packet.json"
            if packet_path.exists():
                with open(packet_path, "r", encoding="utf-8") as f:
                    packet = json.load(f)
                self.assertEqual(packet.get("total_ocr_cases", -1), 0,
                                 "0 deferred in status_resolution but ocr packet still lists cases")

    def test_empty_deferred_workpack_when_zero_deferred(self) -> None:
        workpack_path = REPORTS_DIR / "deferred_resolution_workpack.json"
        if not workpack_path.exists():
            self.skipTest("deferred_resolution_workpack.json not yet generated")
        with open(workpack_path, "r", encoding="utf-8") as f:
            workpack = json.load(f)
        resolution_path = REPORTS_DIR / "status_resolution_packet.json"
        if not resolution_path.exists():
            self.skipTest("status_resolution_packet.json not yet generated")
        with open(resolution_path, "r", encoding="utf-8") as f:
            resolution = json.load(f)
        ocr_remaining = resolution.get("ocr_needed_remaining", [])
        manual_remaining = resolution.get("manual_review_remaining", [])
        if len(ocr_remaining) == 0 and len(manual_remaining) == 0:
            self.assertEqual(workpack.get("total_cases", -1), 0,
                             "0 deferred in status_resolution but workpack still has cases")

    def test_ocr_selector_writes_empty_packet_in_isolation(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            fake_resolution = {
                "generated_at": "2026-01-01T00:00:00Z",
                "policy_version": "v2",
                "status_before": {"confirmed": 1, "disputed": 0, "rejected": 0},
                "status_after": {"confirmed": 1, "disputed": 0, "rejected": 0},
                "resolution_log": [],
                "ocr_needed_remaining": [],
                "manual_review_remaining": [],
                "blocked_for_clean_snapshot": [],
            }
            resolution_file = tmp_path / "status_resolution_packet.json"
            resolution_file.write_text(json.dumps(fake_resolution), encoding="utf-8")
            workpack_file = tmp_path / "deferred_resolution_workpack.json"
            workpack_file.write_text(json.dumps({
                "generated_at": "2026-01-01T00:00:00Z",
                "total_cases": 0,
                "ocr_needed": [],
                "manual_review": [],
            }), encoding="utf-8")
            ocr_packet_file = tmp_path / "ocr_deferred_case_packet.json"
            self.module.build_ocr_case_map()
            self.assertEqual(self.module.build_ocr_case_map(), [])


if __name__ == "__main__":
    unittest.main()
