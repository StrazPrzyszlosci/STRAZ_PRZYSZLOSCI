#!/usr/bin/env python3
"""Validate AgriGrowPolicy (T26 — rolnictwo autonomiczne).

Polityka autopilota uprawy: czujniki, pasma bezpieczne/alarmowe, advisory
z klasami wykonania. Blokady:
- physical_actuation jest zabroniona jako actuation_class (brak sterowania
  pompa/dozowaniem/grzalka bez czlowieka; spójne z bramkami pack-phone-aquaponics-observer-01),
- edge_auto wymaga max_per_day oraz budzetu dziennego (autopilot_limits),
- kill switch i human control point są obowiązkowe,
- pasma muszą być matematycznie spójne (alarm poza pasmem bezpiecznym).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY = ROOT / "agri_autopilot" / "seed_policy.json"

ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{2,80}$")
SENSOR_RE = re.compile(r"^[a-z0-9_]+$")
TRIGGER_RE = re.compile(r"^([a-z0-9_]+)_(below_safe_min|above_safe_max)$")
ACTUATION_CLASSES = {
    "advisory_only",
    "edge_auto_within_safe_band",
    "requires_human_approval",
}
FORBIDDEN_ACTUATION_MARKERS = ("physical_actuation",)


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def validate_policy(record: dict) -> list[str]:
    errors: list[str] = []
    pid = record.get("id", "<unknown>")
    if not isinstance(pid, str) or not ID_RE.match(pid):
        errors.append(f"id must match {ID_RE.pattern}")
    if not isinstance(record.get("grow_cell_id"), str) or len(record.get("grow_cell_id", "")) < 3:
        errors.append("grow_cell_id required >=3 chars")
    if not isinstance(record.get("crop_profile"), str) or len(record.get("crop_profile", "")) < 3:
        errors.append("crop_profile required >=3 chars")

    sensors = record.get("sensors")
    if not isinstance(sensors, list) or not sensors:
        errors.append("sensors must be a non-empty list")
    else:
        for sensor in sensors:
            if not isinstance(sensor, str) or not SENSOR_RE.match(sensor):
                errors.append(f"sensor name invalid: {sensor!r}")

    bands = record.get("bands")
    if not isinstance(bands, dict) or not bands:
        errors.append("bands must be a non-empty object")
    else:
        for sensor in sensors or []:
            band = bands.get(sensor)
            if not isinstance(band, dict):
                errors.append(f"bands missing for sensor: {sensor}")
                continue
            values = {key: band.get(key) for key in ("safe_min", "safe_max", "alarm_below", "alarm_above")}
            if not all(_is_number(v) for v in values.values()):
                errors.append(f"bands[{sensor}] requires numeric safe_min/safe_max/alarm_below/alarm_above")
                continue
            if values["safe_min"] >= values["safe_max"]:
                errors.append(f"bands[{sensor}]: safe_min must be < safe_max")
            if values["alarm_below"] > values["safe_min"]:
                errors.append(f"bands[{sensor}]: alarm_below must be <= safe_min")
            if values["alarm_above"] < values["safe_max"]:
                errors.append(f"bands[{sensor}]: alarm_above must be >= safe_max")

    advisories = record.get("advisories")
    has_auto = False
    if not isinstance(advisories, list) or not advisories:
        errors.append("advisories must be a non-empty list")
    else:
        seen_actions: set[str] = set()
        declared_sensors = set(sensors or [])
        for adv in advisories:
            if not isinstance(adv, dict):
                errors.append("advisory must be an object")
                continue
            action_id = adv.get("action_id")
            if not isinstance(action_id, str) or not ID_RE.match(action_id):
                errors.append(f"advisory action_id invalid: {action_id!r}")
            elif action_id in seen_actions:
                errors.append(f"duplicate action_id: {action_id}")
            else:
                seen_actions.add(action_id)

            trigger = adv.get("trigger", "")
            match = TRIGGER_RE.match(str(trigger))
            if not match:
                errors.append(f"{action_id}: trigger must look like '<sensor>_below_safe_min|<sensor>_above_safe_max'")
            elif match.group(1) not in declared_sensors:
                errors.append(f"{action_id}: trigger sensor '{match.group(1)}' not declared in sensors")

            actuation_class = adv.get("actuation_class")
            if actuation_class not in ACTUATION_CLASSES:
                errors.append(
                    f"{action_id}: actuation_class must be one of {sorted(ACTUATION_CLASSES)}"
                )
            for marker in FORBIDDEN_ACTUATION_MARKERS:
                if marker in str(actuation_class):
                    errors.append(
                        f"{action_id}: {marker} is forbidden; autopilot never performs "
                        "pump/dosing/heater/valve actuation without human operator"
                    )
            if actuation_class == "edge_auto_within_safe_band":
                has_auto = True
                max_per_day = adv.get("max_per_day")
                if not isinstance(max_per_day, int) or isinstance(max_per_day, bool) or not 1 <= max_per_day <= 10:
                    errors.append(f"{action_id}: edge_auto_within_safe_band requires integer max_per_day in 1..10")

    if has_auto:
        limits = record.get("autopilot_limits")
        budget = limits.get("max_auto_actions_per_day") if isinstance(limits, dict) else None
        if not isinstance(budget, int) or isinstance(budget, bool) or not 1 <= budget <= 12:
            errors.append("autopilot_limits.max_auto_actions_per_day (1..12) required when any action is edge_auto_within_safe_band")

    if not isinstance(record.get("kill_switch_ref"), str) or len(record.get("kill_switch_ref", "")) < 5:
        errors.append("kill_switch_ref required >=5 chars")
    if not isinstance(record.get("human_control_point"), str) or len(record.get("human_control_point", "")) < 10:
        errors.append("human_control_point required >=10 chars")

    return errors


def validate_policies(payload: dict) -> list[str]:
    policies = payload.get("policies")
    if not isinstance(policies, list) or not policies:
        return ["policies must be a non-empty list"]
    errors: list[str] = []
    ids: set[str] = set()
    for index, record in enumerate(policies):
        if not isinstance(record, dict):
            errors.append(f"policies[{index}] must be an object")
            continue
        for error in validate_policy(record):
            errors.append(f"policies[{index}]::{record.get('id', '<unknown>')}: {error}")
        pid = record.get("id")
        if isinstance(pid, str):
            if pid in ids:
                errors.append(f"{pid}: duplicate policy id")
            ids.add(pid)
    return errors


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path, nargs="?", default=DEFAULT_POLICY)
    args = parser.parse_args(list(argv) if argv is not None else None)
    errors = validate_policies(json.loads(args.path.read_text(encoding="utf-8")))
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"OK: agri grow policies valid: {args.path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
