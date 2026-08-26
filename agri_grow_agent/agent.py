#!/usr/bin/env python3
"""Grow-agent dla węzła edge (Termux/proot) — T28.

Polluje `GET /v1/ws/events` (T22) z kursorem i renderuje zdarzenia
advisory-only po polsku. Agent NIE wykonuje żadnych akcji fizycznych:
pompa/dozowanie/grzałka/zawory pozostają wyłącznie ręczne (bramki
pack-phone-aquaponics-observer-01 i agri_autopilot).

Kill switch: jeśli plik kill-switch istnieje, agent kończy pracę bez polla.
Token providera nigdy nie jest logowany ani zapisywany w state.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Callable
from urllib import error as urlerror
from urllib import request as urlrequest

DEFAULT_STATE_DIR = Path(__file__).resolve().parent / ".state"
DEFAULT_KILL_SWITCH = Path.home() / "agri_kill_switch"
FETCH_TIMEOUT_SECONDS = 20


def load_cursor(state_file: Path) -> int:
    try:
        return int(json.loads(state_file.read_text(encoding="utf-8")).get("since_id", 0))
    except (OSError, ValueError, AttributeError):
        return 0


def save_cursor(state_file: Path, since_id: int) -> None:
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(json.dumps({"since_id": int(since_id)}, sort_keys=True), encoding="utf-8")


def should_run(kill_switch_file: Path) -> bool:
    return not kill_switch_file.exists()


def render_event(event: dict[str, Any]) -> str | None:
    kind = event.get("kind")
    payload = event.get("payload") or {}
    sensor = payload.get("sensor", "?")
    value = payload.get("value", "?")
    direction = payload.get("direction", "")
    action = payload.get("suggested_action")

    if kind == "alarm":
        line = f"[ALARM] {sensor}={value} ({direction})"
        if action:
            line += f" | sugerowana akcja: {action} — WYŁĄCZNIE RĘCZNIE"
        kill = payload.get("kill_switch_ref")
        if kill:
            line += f" | kill switch: {kill}"
        return line

    if kind == "recommendation":
        hint = payload.get("execution_hint", "manual_by_operator")
        eligible = payload.get("autopilot_eligible")
        prefix = "[AUTO-W-PASMIE]" if eligible else "[SUGESTIA]"
        line = f"{prefix} {sensor}={value} ({direction}) | akcja: {action or 'brak'} | tryb: {hint}"
        reason = payload.get("reason")
        if reason:
            line += f" | powód: {reason}"
        return line

    if kind in ("status", "notice"):
        return f"[INFO] {payload}"

    return None


def build_request(cfg: dict[str, Any]) -> urlrequest.Request:
    url = (
        f"{cfg['api_base'].rstrip('/')}/v1/ws/events"
        f"?provider_id={cfg['provider_id']}&since_id={cfg['since_id']}&limit={cfg['limit']}"
    )
    req = urlrequest.Request(url, method="GET")
    req.add_header("X-Provider-Token", cfg["provider_token"])
    req.add_header("User-Agent", "agri-grow-agent/1.0 (advisory-only)")
    return req


def default_fetch(req: urlrequest.Request) -> dict[str, Any]:
    with urlrequest.urlopen(req, timeout=FETCH_TIMEOUT_SECONDS) as resp:
        return json.loads(resp.read().decode("utf-8"))


def run_once(cfg: dict[str, Any], fetch_impl: Callable[[urlrequest.Request], dict] | None = None) -> list[str]:
    """Jeden cykl polla. Zwraca wyrenderowane linie; aktualizuje kursor w state."""
    fetch = fetch_impl or default_fetch
    if not should_run(Path(cfg["kill_switch_file"])):
        return ["[KILL-SWITCH] plik obecny — agent wstrzymany"]

    try:
        payload = fetch(build_request(cfg))
    except urlerror.HTTPError as exc:
        # Bez wycieku tokenu: tylko kod błędu.
        return [f"[BLAD] HTTP {exc.code} przy pollu zdarzeń"]
    except (urlerror.URLError, OSError, ValueError) as exc:
        return [f"[BLAD] poll nieudany: {type(exc).__name__}"]

    events = payload.get("events") or []
    lines: list[str] = []
    for event in events:
        rendered = render_event(event)
        if rendered:
            lines.append(rendered)

    next_cursor = payload.get("next_cursor")
    if next_cursor is None:
        next_cursor = events[-1]["id"] if events else cfg["since_id"]
    save_cursor(Path(cfg["state_file"]), int(next_cursor))
    if not lines:
        lines.append(f"[OK] brak nowych zdarzeń (kursor={next_cursor})")
    return lines


def build_config(argv: list[str] | None = None) -> dict[str, Any]:
    parser = argparse.ArgumentParser(description="Agri grow-agent (advisory-only poller)")
    parser.add_argument("--api-base", default=os.environ.get("AGRI_API_BASE", "http://127.0.0.1:8787"))
    parser.add_argument("--provider-id", required=os.environ.get("AGRI_PROVIDER_ID") is None)
    parser.add_argument("--provider-token", default=os.environ.get("AGRI_PROVIDER_TOKEN", ""))
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--state-dir", type=Path, default=DEFAULT_STATE_DIR)
    parser.add_argument("--kill-switch-file", type=Path, default=DEFAULT_KILL_SWITCH)
    parser.add_argument("--interval-seconds", type=int, default=0, help="0 = jeden cykl (--once)")
    parser.add_argument("--cycles", type=int, default=1, help="ile cykli wykonać (dla interval > 0)")
    args = parser.parse_args(argv)

    provider_id = args.provider_id or os.environ.get("AGRI_PROVIDER_ID", "")
    provider_token = args.provider_token or os.environ.get("AGRI_PROVIDER_TOKEN", "")
    if not provider_id:
        raise SystemExit("Brak provider_id (arg --provider-id lub env AGRI_PROVIDER_ID).")
    if not provider_token:
        raise SystemExit("Brak provider_token (env AGRI_PROVIDER_TOKEN zalecane — nie wpisuj w CLI historii).")

    return {
        "api_base": args.api_base,
        "provider_id": provider_id,
        "provider_token": provider_token,
        "limit": max(1, min(args.limit, 500)),
        "state_file": str(args.state_dir / "cursor.json"),
        "kill_switch_file": str(args.kill_switch_file),
        "interval_seconds": max(0, args.interval_seconds),
        "cycles": max(1, args.cycles),
        "since_id": load_cursor(args.state_dir / "cursor.json"),
    }


def main(argv: list[str] | None = None) -> int:
    cfg = build_config(argv)
    cycle = 0
    while True:
        cycle += 1
        for line in run_once(cfg):
            print(line, flush=True)
        cfg["since_id"] = load_cursor(Path(cfg["state_file"]))
        if cfg["interval_seconds"] <= 0 or cycle >= cfg["cycles"]:
            break
        time.sleep(cfg["interval_seconds"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
