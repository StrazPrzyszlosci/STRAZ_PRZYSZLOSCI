#!/usr/bin/env python3
"""Pętla samodoskonalenia decyzji roju (selfopt_chain, T51).

Wzorzec pętli danych basala (HYC, router.py + basal-calibrate) przeniesiony
na decyzje ROJU (nie tylko routing LLM):

    decisions.jsonl  ──(annotate / feedback z LoRa inbox)──►  labels.jsonl
    ──►  fit_temperatures()  ──►  CALIBRATION.selfopt.json
    ──►  BasalDecisionCore używa dopasowanych temperatur
    ──►  mniej stratnych deferów, wyższa jakość confidence
    ──►  decisions.jsonl (nowe decyzje z lepszym confidence)

Ewolucja strategii (GEPA-style, suggest-only): statystyki wybranych strategii
i akceptacji przydziałów → propozycja korekt stałych scorów w MD do review
człowieka. Nic nie jest auto-zaaplikowane do kodu.

Fit v1 (deterministyczny, ograniczony do [0.3, 3.0]):
- decyzja DOBRA (accepted=true), ale zdeferowana  →  temperature była za WYSOKA
  (scores zbyt spłaszczone) → obniż (wyostrz),
- decyzja ZŁA (accepted=false), ale niezdeferowana →  temperature była za NISKA
  (nadmierna pewność) → podnieś (spłaszcz).
Kierunek = znak(bad_undeferred - good_deferred); krok = 0.15 * |kierunek| / n.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from selfopt_chain.swarm import TEMPERATURE_SEEDS

TEMP_MIN = 0.3
TEMP_MAX = 3.0
FIT_STEP = 0.15
DEFAULT_STRATEGY_HINTS = {
    "speed_first": 1.0,
    "quality_first": 0.3,
    "load_balance": 0.5,
    "quota_preserve": 0.4,
    "energy_oze": 0.3,
    "redundancy": 0.1,
    "queue_when_busy": 0.1,
}


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    entries = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            entries.append(json.loads(line))
    return entries


def load_decisions(state_dir: Path) -> list[dict[str, Any]]:
    return _read_jsonl(state_dir / "decisions.jsonl")


def load_labels(state_dir: Path) -> list[dict[str, Any]]:
    return _read_jsonl(state_dir / "labels.jsonl")


def append_label(state_dir: Path, decision_id: str, accepted: bool, note: str = "", source: str = "operator") -> dict[str, Any]:
    """Etykieta decyzji (wzór router.py annotate z basala; źródło: operator/field)."""
    label = {
        "decision_id": decision_id,
        "accepted": bool(accepted),
        "note": note,
        "source": source,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    labels_path = state_dir / "labels.jsonl"
    labels_path.parent.mkdir(parents=True, exist_ok=True)
    with labels_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(label, ensure_ascii=False) + "\n")
    return label


def _seed_temperature(question_type: str) -> float:
    temps = TEMPERATURE_SEEDS.get(question_type, TEMPERATURE_SEEDS["choice"])
    return temps.get("default", 0.771)


def fit_temperatures(decisions: list[dict[str, Any]], labels: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Dopasowanie temperatur per typ pytania wg etykiet; None gdy brak etykiet."""
    by_id = {d["id"]: d for d in decisions}
    labeled = [(label, by_id[label["decision_id"]]) for label in labels if label["decision_id"] in by_id]
    if not labeled:
        return None
    per_type: dict[str, dict[str, int]] = {}
    for label, decision in labeled:
        stats = per_type.setdefault(decision["question_type"], {"good_deferred": 0, "bad_undeferred": 0, "n": 0})
        good = bool(label.get("accepted"))
        deferred = bool(decision.get("deferred"))
        if good and deferred:
            stats["good_deferred"] += 1
        if (not good) and (not deferred):
            stats["bad_undeferred"] += 1
        stats["n"] += 1
    temperature_per_prim: dict[str, float] = {}
    for question_type, stats in per_type.items():
        seed = _seed_temperature(question_type)
        direction = stats["bad_undeferred"] - stats["good_deferred"]
        step = FIT_STEP * abs(direction) / max(1, stats["n"])
        fitted = min(TEMP_MAX, max(TEMP_MIN, seed + (step if direction > 0 else -step if direction < 0 else 0.0)))
        temperature_per_prim[question_type] = round(fitted, 4)
    return {
        "temperature_per_prim": temperature_per_prim,
        "temperature_source": {
            qtype: f"fitted on {stats['n']} labeled decisions (good_deferred={stats['good_deferred']}, bad_undeferred={stats['bad_undeferred']})"
            for qtype, stats in per_type.items()
        },
        "n_labels": len(labeled),
        "bounds": [TEMP_MIN, TEMP_MAX],
        "note": "kalibracja roju (wzór basal-calibrate); nadpisuje seedy temperatur decyzji",
    }


def write_calibration(state_dir: Path, calibration: dict[str, Any]) -> Path:
    path = state_dir / "CALIBRATION.selfopt.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(calibration, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def load_calibration(state_dir: Path) -> dict[str, Any] | None:
    path = state_dir / "CALIBRATION.selfopt.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def render_strategy_proposal(decisions: list[dict[str, Any]], labels: list[dict[str, Any]], cycle_hint: int | None = None) -> str:
    """Propozycja ewolucji strategii (GEPA-style, suggest-only)."""
    by_id = {d["id"]: d for d in decisions}
    strategy_decisions = [d for d in decisions if "strategy" in json.dumps(d.get("context", {}))]
    strategy_events = []
    for d in decisions:
        ctx = d.get("context", {}) or {}
        if "strategy" in ctx:
            strategy_events.append((ctx.get("strategy"), d))
    strategy_stats: dict[str, dict[str, Any]] = {}
    for strategy, decision in strategy_events:
        stats = strategy_stats.setdefault(strategy, {"allocations": 0, "conf_sum": 0.0, "deferred": 0})
        stats["allocations"] += 1
        stats["conf_sum"] += decision.get("confidence", 0.0)
        stats["deferred"] += 1 if decision.get("deferred") else 0
    label_by_decision = {label["decision_id"]: label for label in labels}
    accepted_by_strategy: dict[str, Counter] = {}
    for decision in decisions:
        ctx = decision.get("context", {}) or {}
        strategy = ctx.get("strategy")
        label = label_by_decision.get(decision["id"])
        if strategy and label:
            bucket = accepted_by_strategy.setdefault(strategy, Counter())
            bucket["accepted" if label.get("accepted") else "rejected"] += 1
    lines = [
        "# Propozycja ewolucji strategii roju (GEPA-style, suggest-only)",
        "",
        f"- decyzji w logu: {len(decisions)}; etykiet: {len(labels)}" + (f"; cykl: {cycle_hint}" if cycle_hint else ""),
        "- status: **nic nie zostało auto-zaaplikowane**; korekty stałych scorów to propozycje do review człowieka.",
        "",
    ]
    if not strategy_events:
        lines.append("Brak decyzji z kontekstem strategii — zbierz więcej cykli.")
        return "\n".join(lines)
    lines.append("| strategia | przydziały | avg conf | defer-rate | accepted | rejected | sugestia |")
    lines.append("|---|---|---|---|---|---|---|")
    for strategy in sorted(set(s for s, _ in strategy_events)):
        stats = strategy_stats.get(strategy, {"allocations": 0, "conf_sum": 0.0, "deferred": 0})
        n = max(1, stats["allocations"])
        avg_conf = round(stats["conf_sum"] / n, 3)
        defer_rate = round(stats["deferred"] / n, 3)
        acc = accepted_by_strategy.get(strategy, Counter())
        accepted, rejected = acc.get("accepted", 0), acc.get("rejected", 0)
        hint_seed = DEFAULT_STRATEGY_HINTS.get(strategy, 0.5)
        if rejected > accepted:
            suggestion = f"obniz stale scorów (seed {hint_seed} → {round(hint_seed * 0.8, 2)})"
        elif accepted > 0 and defer_rate > 0.5:
            suggestion = "wyostrz roznice stalych (mniej deferów): +0.1 do dominujacego sygnalu"
        elif accepted > rejected:
            suggestion = "utrzymaj; zwieksz udzial o +0.1 w sygnalach, gdzie wygrywa"
        else:
            suggestion = "brak danych — zbierz etykiety (calibrate.py annotate / feedback z pola)"
        lines.append(f"| {strategy} | {stats['allocations']} | {avg_conf} | {defer_rate} | {accepted} | {rejected} | {suggestion} |")
    lines += [
        "",
        "## Jak zaaplikować (człowiek)",
        "1. Przejrzyj tabelę; zaakceptowane sugestie przenieś do stałych w `selfopt_chain/swarm.py` (STRATEGY_WEIGHTS / sygnały decide_strategy).",
        "2. Zmiana przez PR (no_auto_merge); po merge uruchom cykle i porównaj defer-rate oraz accepted-rate.",
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Samokalibracja decyzji roju (decisions.jsonl + labels.jsonl → CALIBRATION.selfopt.json)")
    parser.add_argument("--state-dir", type=Path, default=Path("scratch/selfopt"))
    sub = parser.add_subparsers(dest="cmd", required=True)

    fit = sub.add_parser("fit", help="dopasuj temperatury z etykiet i zapisz kalibrację")
    annotate = sub.add_parser("annotate", help="oznacz decyzję (wzór router.py annotate)")
    annotate.add_argument("--decision-id", required=True)
    annotate.add_argument("--accepted", required=True, choices=["yes", "no"])
    annotate.add_argument("--note", default="")
    annotate.add_argument("--source", default="operator", help="operator | field | outcome")
    propose = sub.add_parser("propose", help="propozycja ewolucji strategii (MD, suggest-only)")

    args = parser.parse_args(argv if argv is not None else None)
    state_dir: Path = args.state_dir

    if args.cmd == "annotate":
        label = append_label(state_dir, args.decision_id, args.accepted == "yes", args.note, args.source)
        print(json.dumps(label, ensure_ascii=False))
        return 0
    if args.cmd == "fit":
        calibration = fit_temperatures(load_decisions(state_dir), load_labels(state_dir))
        if calibration is None:
            print("BRAK: brak etykiet do fitu — oznacz decyzje (annotate) lub zaczekaj na feedback z pola")
            return 2
        path = write_calibration(state_dir, calibration)
        print(f"OK: kalibracja zapisana: {path} | n_labels={calibration['n_labels']}")
        print(json.dumps(calibration["temperature_per_prim"], ensure_ascii=False))
        return 0
    if args.cmd == "propose":
        proposal = render_strategy_proposal(load_decisions(state_dir), load_labels(state_dir))
        out = state_dir / "strategy_evolution_proposal.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(proposal, encoding="utf-8")
        print(f"OK: propozycja zapisana: {out} (suggest-only)")
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
