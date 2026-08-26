import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "human_approval" / "seed_approvals.json"

sys.path.insert(0, str(ROOT / "human_approval"))
from expiry_report import build_report, days_until, format_lines, main  # noqa: E402

NOW = datetime(2026, 8, 26, 12, 0, 0, tzinfo=timezone.utc)


def record(rid: str, days_to_expiry: int, revoked: bool = False) -> dict:
    from datetime import timedelta

    return {
        "id": rid,
        "revoked": revoked,
        "expires_at": (NOW + timedelta(days=days_to_expiry)).isoformat(),
    }


class ExpiryReportTest(unittest.TestCase):
    def test_days_until_counts_full_days_negative_when_past(self):
        self.assertEqual(days_until("2026-09-05T00:00:00+00:00", NOW), 9)
        # -6d12h floored to -7 pełnych dni (datetime.days zaokrągla w dół).
        self.assertEqual(days_until("2026-08-20T00:00:00+00:00", NOW), -7)
        self.assertIsNone(days_until("not-a-date", NOW))

    def test_seed_records_are_ok_today(self):
        payload = json.loads(SEED.read_text(encoding="utf-8"))
        report = build_report(payload, now=NOW)
        self.assertEqual(report["expired"], [])
        self.assertEqual(report["expiring_soon"], [])
        self.assertEqual(len(report["ok"]), 2)

    def test_classifies_expiring_soon_expired_and_revoked(self):
        payload = {
            "records": [
                record("ok_record", 90),
                record("soon_record", 10),
                record("boundary_record", 30),
                record("old_record", -3),
                record("dead_record", 5, revoked=True),
                {"id": "bad_date_record", "expires_at": "yesterday"},
            ]
        }
        report = build_report(payload, now=NOW)
        ids_expired = [entry["id"] for entry in report["expired"]]
        ids_soon = [entry["id"] for entry in report["expiring_soon"]]
        self.assertEqual(ids_expired, ["old_record"])
        self.assertEqual(sorted(ids_soon), ["boundary_record", "soon_record"])
        self.assertEqual([entry["id"] for entry in report["invalid"]], ["dead_record", "bad_date_record"])

    def test_format_lines_warn_and_error(self):
        report = build_report({"records": [record("soon_record", 7), record("old_record", -1)]}, now=NOW)
        lines = format_lines(report)
        self.assertTrue(any(line.startswith("ERROR: old_record") and "renew or archive" in line for line in lines))
        self.assertTrue(any(line.startswith("WARNING: soon_record") and "schedule renewal" in line for line in lines))

    def test_main_exit_codes(self):
        with tempfile.TemporaryDirectory() as tmp:
            ok_path = Path(tmp) / "ok.json"
            ok_path.write_text(json.dumps({"records": [record("ok_record", 120)]}), encoding="utf-8")
            self.assertEqual(main([str(ok_path), "--warn-days", "30"]), 0)

            expired_path = Path(tmp) / "expired.json"
            expired_path.write_text(json.dumps({"records": [record("old_record", -2)]}), encoding="utf-8")
            self.assertEqual(main([str(expired_path)]), 1)

            warn_only_path = Path(tmp) / "warn.json"
            warn_only_path.write_text(json.dumps({"records": [record("soon_record", 20)]}), encoding="utf-8")
            # Ostrzeżenie nie wywala exit code — dopóki nic nie wygasło.
            self.assertEqual(main([str(warn_only_path), "--warn-days", "30"]), 0)


if __name__ == "__main__":
    unittest.main()
