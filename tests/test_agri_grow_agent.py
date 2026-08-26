import json
import tempfile
import unittest
from pathlib import Path
from urllib import request as urlrequest

import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "agri_grow_agent"))

from agent import build_request, load_cursor, render_event, run_once, save_cursor, should_run  # noqa: E402


def fake_fetch_factory(responses):
    calls = []

    def fetch(req: urlrequest.Request):
        calls.append(req)
        item = responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item

    return fetch, calls


class GrowAgentStateTest(unittest.TestCase):
    def test_cursor_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "cursor.json"
            self.assertEqual(load_cursor(state), 0)
            save_cursor(state, 42)
            self.assertEqual(load_cursor(state), 42)

    def test_load_cursor_tolerates_corrupt_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "cursor.json"
            state.write_text("not-json", encoding="utf-8")
            self.assertEqual(load_cursor(state), 0)


class GrowAgentRenderTest(unittest.TestCase):
    def test_renders_alarm_with_kill_switch_and_manual_hint(self):
        line = render_event({
            "kind": "alarm",
            "severity": "critical",
            "payload": {
                "sensor": "ph",
                "value": 5.3,
                "direction": "below_alarm",
                "suggested_action": "buffer_dose_ph_up",
                "execution_hint": "manual_by_operator",
                "kill_switch_ref": "gniazdo R1",
            },
        })
        self.assertIn("[ALARM]", line)
        self.assertIn("ph=5.3", line)
        self.assertIn("WYŁĄCZNIE RĘCZNIE", line)
        self.assertIn("gniazdo R1", line)

    def test_renders_recommendation_modes(self):
        auto = render_event({"kind": "recommendation", "payload": {
            "sensor": "ph", "value": 5.7, "direction": "below_safe_min",
            "suggested_action": "buffer_dose_ph_up", "autopilot_eligible": True,
            "human_control_point": "operator przegląda zdarzenia",
        }})
        manual = render_event({"kind": "recommendation", "payload": {
            "sensor": "light_ppfd", "value": 500.0, "direction": "above_safe_max",
            "suggested_action": "shade_cloth_deploy", "execution_hint": "requires_human_approval",
        }})
        exhausted = render_event({"kind": "recommendation", "payload": {
            "sensor": "ph", "value": 5.7, "reason": "daily_autopilot_budget_exhausted",
        }})
        self.assertTrue(auto.startswith("[AUTO-W-PASMIE]"))
        self.assertIn("requires_human_approval", manual)
        self.assertIn("daily_autopilot_budget_exhausted", exhausted)

    def test_unknown_kind_returns_none(self):
        self.assertIsNone(render_event({"kind": "mystery", "payload": {}}))


class GrowAgentRunOnceTest(unittest.TestCase):
    def _cfg(self, tmp: str) -> dict:
        return {
            "api_base": "https://worker.example.invalid",
            "provider_id": "phone-aquaponics-observer-01",
            "provider_token": "secret-token",
            "limit": 50,
            "state_file": str(Path(tmp) / ".state" / "cursor.json"),
            "kill_switch_file": str(Path(tmp) / "no-switch"),
            "since_id": 0,
        }

    def test_poll_renders_events_and_advances_cursor(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = self._cfg(tmp)
            payload = {
                "events": [
                    {"id": 3, "kind": "status", "severity": "info", "payload": {"sensor": "ph", "value": 6.2}},
                    {"id": 7, "kind": "alarm", "severity": "critical", "payload": {"sensor": "ph", "value": 5.2}},
                ],
                "next_cursor": 7,
            }
            fetch, calls = fake_fetch_factory([payload])
            lines = run_once(cfg, fetch)
            self.assertEqual(len(calls), 1)
            self.assertEqual(calls[0].get_header("X-provider-token"), "secret-token")
            self.assertIn("/v1/ws/events?provider_id=phone-aquaponics-observer-01&since_id=0&limit=50", calls[0].full_url)
            self.assertEqual(load_cursor(Path(cfg["state_file"])), 7)
            self.assertTrue(any("[ALARM]" in line for line in lines))

    def test_empty_feed_keeps_cursor_and_reports_ok(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = self._cfg(tmp)
            save_cursor(Path(cfg["state_file"]), 11)
            cfg["since_id"] = 11
            fetch, _ = fake_fetch_factory([{"events": [], "next_cursor": 11}])
            lines = run_once(cfg, fetch)
            self.assertIn("kursor=11", lines[0])

    def test_http_error_does_not_leak_token(self):
        from urllib import error as urlerror

        with tempfile.TemporaryDirectory() as tmp:
            cfg = self._cfg(tmp)
            fetch, _ = fake_fetch_factory([urlerror.HTTPError(cfg["api_base"], 401, "Unauthorized", None, None)])
            lines = run_once(cfg, fetch)
            self.assertIn("HTTP 401", lines[0])
            self.assertNotIn("secret-token", "\n".join(lines))

    def test_kill_switch_blocks_polling(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = self._cfg(tmp)
            switch = Path(tmp) / "agri_kill_switch"
            switch.write_text("stop", encoding="utf-8")
            cfg["kill_switch_file"] = str(switch)
            fetch, calls = fake_fetch_factory([])
            lines = run_once(cfg, fetch)
            self.assertEqual(calls, [])
            self.assertIn("[KILL-SWITCH]", lines[0])

    def test_should_run_semantics(self):
        with tempfile.TemporaryDirectory() as tmp:
            absent = Path(tmp) / "missing"
            self.assertTrue(should_run(absent))
            present = Path(tmp) / "present"
            present.write_text("x", encoding="utf-8")
            self.assertFalse(should_run(present))


if __name__ == "__main__":
    unittest.main()
