#!/usr/bin/env python3
"""Deterministyczny ewaluator odczytów dla AgriGrowPolicy (T26).

Wejście: polityka (rekord z seed_policy.json) + odczyty czujników.
Wyjście: zdarzenia zgodne z formatem edge_event_stream (T22):
  {provider_id (= grow_cell_id), kind, severity, payload}
kind/severity pokrywają się z cloudflare/src/edge_events_stream.js:
  kind in {recommendation, alarm, status, notice},
  severity in {info, warning, critical}.

Bezpieczeństwo:
- akcje autopilota (edge_auto_within_safe_band) są sugerowane tylko w budżecie
  dziennym; po wyczerpaniu budżetu wracają jako instrukcja manualna,
- akcje requires_human_approval nigdy nie są auto-wykonywane,
- evaluator tylko sugeruje; nie wykonuje żadnej fizycznej akcji.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY = ROOT / "agri_autopilot" / "seed_policy.json"


def _advisory_index(policy: dict) -> dict[str, dict]:
    index: dict[str, dict] = {}
    for advisory in policy.get("advisories", []):
        trigger = str(advisory.get("trigger", ""))
        if trigger:
            index[trigger] = advisory
    return index


def evaluate_readings(
    policy: dict,
    readings: dict[str, Any],
    auto_actions_used_today: int = 0,
    include_ok_status: bool = False,
) -> dict:
    events: list[dict] = []
    advisories = _advisory_index(policy)
    limits = policy.get("autopilot_limits") or {}
    budget = int(limits.get("max_auto_actions_per_day", 0))
    budget_left = max(budget - int(auto_actions_used_today), 0)
    summary = {"alarms": 0, "warnings": 0, "auto_suggested": 0, "ok": 0}

    bands = policy.get("bands", {})
    for sensor, value in readings.items():
        band = bands.get(sensor)
        if band is None or not isinstance(value, (int, float)) or isinstance(value, bool):
            continue
        grow_cell_id = policy.get("grow_cell_id", "unknown-grow-cell")
        base_payload = {"sensor": sensor, "value": value, "policy_id": policy.get("id")}
        below_alarm = value < band["alarm_below"]
        above_alarm = value > band["alarm_above"]
        below_safe = value < band["safe_min"]
        above_safe = value > band["safe_max"]

        if below_alarm or above_alarm:
            summary["alarms"] += 1
            direction = "below_alarm" if below_alarm else "above_alarm"
            trigger = f"{sensor}_below_safe_min" if below_alarm else f"{sensor}_above_safe_max"
            advisory = advisories.get(trigger)
            events.append({
                "provider_id": grow_cell_id,
                "kind": "alarm",
                "severity": "critical",
                "payload": {
                    **base_payload,
                    "direction": direction,
                    "suggested_action": advisory.get("action_id") if advisory else None,
                    "execution_hint": "manual_by_operator",
                    "kill_switch_ref": policy.get("kill_switch_ref"),
                },
            })
            continue

        if not below_safe and not above_safe:
            summary["ok"] += 1
            if include_ok_status:
                events.append({
                    "provider_id": grow_cell_id,
                    "kind": "status",
                    "severity": "info",
                    "payload": {**base_payload, "state": "within_safe_band"},
                })
            continue

        trigger = f"{sensor}_below_safe_min" if below_safe else f"{sensor}_above_safe_max"
        advisory = advisories.get(trigger)
        action_id = advisory.get("action_id") if advisory else None
        actuation_class = advisory.get("actuation_class") if advisory else "advisory_only"
        payload = {**base_payload, "direction": "below_safe_min" if below_safe else "above_safe_max",
                   "suggested_action": action_id}

        if actuation_class == "edge_auto_within_safe_band":
            if action_id and budget_left > 0:
                budget_left -= 1
                summary["auto_suggested"] += 1
                summary["warnings"] += 1
                events.append({
                    "provider_id": grow_cell_id,
                    "kind": "recommendation",
                    "severity": "warning",
                    "payload": {
                        **payload,
                        "autopilot_eligible": True,
                        "max_per_day": advisory.get("max_per_day"),
                        "human_control_point": policy.get("human_control_point"),
                    },
                })
            else:
                summary["warnings"] += 1
                events.append({
                    "provider_id": grow_cell_id,
                    "kind": "recommendation",
                    "severity": "warning",
                    "payload": {
                        **payload,
                        "autopilot_eligible": False,
                        "reason": "daily_autopilot_budget_exhausted",
                        "execution_hint": "manual_by_operator",
                    },
                })
            continue

        summary["warnings"] += 1
        hint = (
            "requires_human_approval"
            if actuation_class == "requires_human_approval"
            else "manual_by_operator"
        )
        events.append({
            "provider_id": grow_cell_id,
            "kind": "recommendation",
            "severity": "warning",
            "payload": {
                **payload,
                "actuation_class": actuation_class,
                "execution_hint": hint,
                "human_control_point": policy.get("human_control_point"),
            },
        })

    return {"events": events, "summary": summary}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--policy-id", required=True, help="id rekordu polityki z pliku")
    parser.add_argument("--readings", required=True, help='JSON obiekt {"sensor": value, ...}')
    parser.add_argument("--used-today", type=int, default=0, help="wykonane dziś akcje autopilota")
    args = parser.parse_args(argv)

    payload = json.loads(args.policy.read_text(encoding="utf-8"))
    policy = next((p for p in payload.get("policies", []) if p.get("id") == args.policy_id), None)
    if policy is None:
        print(f"ERROR: policy not found: {args.policy_id}")
        return 1
    result = evaluate_readings(policy, json.loads(args.readings), args.used_today)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
