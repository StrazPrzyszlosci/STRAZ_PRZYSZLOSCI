import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "agri_autopilot" / "seed_policy.json"
SCHEMA = ROOT / "agri_autopilot" / "schema.json"

sys.path.insert(0, str(ROOT / "agri_autopilot"))
from evaluate_readings import evaluate_readings  # noqa: E402
from validate_policy import validate_policies, validate_policy  # noqa: E402


class AgriAutopilotPolicyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = json.loads(SEED.read_text(encoding="utf-8"))
        cls.policies = cls.payload["policies"]
        cls.aquaponics = next(p for p in cls.policies if p["id"] == "grow_policy_aquaponics_greens_01")

    def test_seed_validates(self):
        self.assertEqual(validate_policies(self.payload), [])

    def test_schema_contract_matches_seed_fields(self):
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        required = set(schema["properties"]["policies"]["items"]["required"])
        for policy in self.policies:
            missing = required - set(policy)
            self.assertEqual(missing, set(), f"{policy['id']} missing: {missing}")

    def _ok_policy(self) -> dict:
        return copy.deepcopy(self.aquaponics)

    def test_blocks_physical_actuation_class(self):
        policy = self._ok_policy()
        policy["advisories"][0]["actuation_class"] = "physical_actuation"
        errors = validate_policy(policy)
        self.assertTrue(any("forbidden" in e for e in errors), errors)

    def test_blocks_trigger_for_undeclared_sensor(self):
        policy = self._ok_policy()
        policy["advisories"][0]["trigger"] = "nitrate_ppm_below_safe_min"
        errors = validate_policy(policy)
        self.assertTrue(any("not declared in sensors" in e for e in errors), errors)

    def test_blocks_band_missing_and_inconsistent_ranges(self):
        policy = self._ok_policy()
        del policy["bands"]["ph"]
        self.assertTrue(any("bands missing" in e for e in validate_policy(policy)))

        policy = self._ok_policy()
        policy["bands"]["ph"] = {"safe_min": 7.0, "safe_max": 6.0, "alarm_below": 7.5, "alarm_above": 5.0}
        errors = validate_policy(policy)
        self.assertTrue(any("safe_min must be < safe_max" in e for e in errors))
        self.assertTrue(any("alarm_below must be <= safe_min" in e for e in errors))
        self.assertTrue(any("alarm_above must be >= safe_max" in e for e in errors))

    def test_blocks_auto_action_without_daily_budget(self):
        policy = self._ok_policy()
        del policy["autopilot_limits"]
        errors = validate_policy(policy)
        self.assertTrue(any("max_auto_actions_per_day" in e for e in errors), errors)

    def test_blocks_auto_action_without_max_per_day(self):
        policy = self._ok_policy()
        del policy["advisories"][0]["max_per_day"]
        errors = validate_policy(policy)
        self.assertTrue(any("max_per_day" in e for e in errors), errors)

    def test_blocks_missing_kill_switch_or_control_point(self):
        policy = self._ok_policy()
        policy["kill_switch_ref"] = ""
        policy["human_control_point"] = "short"
        errors = validate_policy(policy)
        self.assertTrue(any("kill_switch_ref" in e for e in errors))
        self.assertTrue(any("human_control_point" in e for e in errors))

    def test_blocks_duplicate_policy_ids(self):
        payload = copy.deepcopy(self.payload)
        payload["policies"].append(copy.deepcopy(payload["policies"][0]))
        errors = validate_policies(payload)
        self.assertTrue(any("duplicate policy id" in e for e in errors))


class AgriAutopilotEvaluatorTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        payload = json.loads(SEED.read_text(encoding="utf-8"))
        cls.policy = next(p for p in payload["policies"] if p["id"] == "grow_policy_aquaponics_greens_01")

    def test_alarm_event_on_critical_ph(self):
        result = evaluate_readings(self.policy, {"ph": 5.3})
        self.assertEqual(len(result["events"]), 1)
        event = result["events"][0]
        self.assertEqual(event["kind"], "alarm")
        self.assertEqual(event["severity"], "critical")
        self.assertEqual(event["provider_id"], "phone-aquaponics-observer-01")
        self.assertEqual(event["payload"]["suggested_action"], "buffer_dose_ph_up")
        self.assertEqual(event["payload"]["execution_hint"], "manual_by_operator")

    def test_warning_recommendation_outside_safe_band(self):
        result = evaluate_readings(self.policy, {"air_temp_c": 27.5})
        self.assertEqual(result["events"][0]["kind"], "recommendation")
        self.assertEqual(result["events"][0]["severity"], "warning")
        self.assertEqual(result["events"][0]["payload"]["execution_hint"], "manual_by_operator")
        self.assertEqual(result["summary"]["alarms"], 0)

    def test_auto_suggestion_respects_daily_budget(self):
        within_budget = evaluate_readings(self.policy, {"ph": 5.7}, auto_actions_used_today=4)
        self.assertEqual(within_budget["summary"]["auto_suggested"], 1)
        self.assertTrue(within_budget["events"][0]["payload"]["autopilot_eligible"])

        exhausted = evaluate_readings(self.policy, {"ph": 5.7}, auto_actions_used_today=6)
        self.assertEqual(exhausted["summary"]["auto_suggested"], 0)
        payload = exhausted["events"][0]["payload"]
        self.assertFalse(payload["autopilot_eligible"])
        self.assertEqual(payload["reason"], "daily_autopilot_budget_exhausted")

    def test_human_approval_hint_for_shade_cloth(self):
        # 500 ppfd: powyżej safe_max (400) ale poniżej alarm_above (600) -> warning z bramką człowieka.
        result = evaluate_readings(self.policy, {"light_ppfd": 500.0})
        payload = result["events"][0]["payload"]
        self.assertEqual(payload["suggested_action"], "shade_cloth_deploy")
        self.assertEqual(payload["execution_hint"], "requires_human_approval")

    def test_light_above_alarm_threshold_is_critical_alarm(self):
        result = evaluate_readings(self.policy, {"light_ppfd": 650.0})
        event = result["events"][0]
        self.assertEqual(event["kind"], "alarm")
        self.assertEqual(event["severity"], "critical")

    def test_within_safe_band_is_silent_unless_requested(self):
        silent = evaluate_readings(self.policy, {"ph": 6.2, "air_temp_c": 21.0})
        self.assertEqual(silent["events"], [])
        self.assertEqual(silent["summary"]["ok"], 2)

        with_status = evaluate_readings(self.policy, {"ph": 6.2}, include_ok_status=True)
        self.assertEqual(with_status["events"][0]["kind"], "status")
        self.assertEqual(with_status["events"][0]["severity"], "info")

    def test_unknown_sensor_is_skipped(self):
        result = evaluate_readings(self.policy, {"nitrate_ppm": 42, "ph": "not-a-number"})
        self.assertEqual(result["events"], [])
        self.assertEqual(result["summary"]["ok"], 0)


if __name__ == "__main__":
    unittest.main()
