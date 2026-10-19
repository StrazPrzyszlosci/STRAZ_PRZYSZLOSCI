#!/usr/bin/env python3
"""Ślady wykonania łańcucha + ekstrakcja insightów (selfopt_chain, T48).

Inspiracja ABSTRAL (Abstracting and Extracting Structural Information):
zbieramy pelne metadane wykonania (wezel, zadanie, model, latencja, ok/fail),
porownujemy przebiegi sukcesow i porazek per rodzaj zadania i wyciagamy
wniki strukturalne (waske gardlo, niedopasowanie modelu) wraz z propozycja
patcha skilla. Wszystko suggest-only - nic nie jest autozaaplikowane.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class TraceRecorder:
    def __init__(self, run_id: str, out_path: Path | None = None) -> None:
        self.run_id = run_id
        self.out_path = out_path
        self.events: list[dict[str, Any]] = []
        if out_path is not None:
            out_path.parent.mkdir(parents=True, exist_ok=True)

    def event(self, event_type: str, **fields: Any) -> None:
        record = {"ts": _now_iso(), "run_id": self.run_id, "type": event_type}
        record.update(fields)
        self.events.append(record)
        if self.out_path is not None:
            with self.out_path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(record, ensure_ascii=False) + "\n")

    def run_start(self, chain_id: str, engine: str) -> None:
        self.event("run_started", chain_id=chain_id, engine=engine)

    def run_end(self, status: str, nodes_run: int) -> None:
        self.event("run_finished", status=status, nodes_run=nodes_run)

    def routed(self, decision: dict[str, Any], node: str) -> None:
        self.event(
            "routed",
            node=node,
            task_id=decision.get("task_id"),
            kind=decision.get("kind"),
            required_tier=decision.get("required_tier"),
            chosen=decision.get("chosen"),
            blocked=decision.get("blocked"),
            blocked_reason=decision.get("blocked_reason"),
        )

    def node_result(self, node: str, result: dict[str, Any]) -> None:
        self.event(
            "node_result",
            node=node,
            ok=result.get("ok"),
            model_id=result.get("model_id"),
            provider=result.get("provider"),
            latency_ms=result.get("latency_ms"),
            tokens_est=result.get("tokens_est"),
            error=result.get("error"),
            error_class=result.get("error_class"),
        )

    def error(self, where: str, error: str) -> None:
        self.event("error", where=where, error=error)

    def dump(self) -> list[dict[str, Any]]:
        return list(self.events)


def summarize_traces(events: list[dict[str, Any]]) -> dict[str, Any]:
    """Agregacja śladów per kind i per model."""
    kinds: dict[str, dict[str, Any]] = {}
    models: dict[str, dict[str, Any]] = {}
    for ev in events:
        if ev.get("type") != "node_result":
            continue
        kind = None
        for r in events:
            if r.get("type") == "routed" and r.get("node") == ev.get("node"):
                kind = r.get("kind")
                break
        ok = bool(ev.get("ok"))
        latency = ev.get("latency_ms") or 0
        for bucket, key in ((kinds, kind), (models, ev.get("model_id"))):
            if key is None:
                continue
            entry = bucket.setdefault(key, {"count": 0, "ok": 0, "latency_sum": 0})
            entry["count"] += 1
            entry["ok"] += 1 if ok else 0
            entry["latency_sum"] += latency
    for bucket in (kinds, models):
        for entry in bucket.values():
            entry["ok_rate"] = round(entry["ok"] / entry["count"], 3)
            entry["avg_latency_ms"] = round(entry["latency_sum"] / entry["count"], 1)
            del entry["ok"], entry["latency_sum"]
    return {"kinds": kinds, "models": models}


def extract_insights(events: list[dict[str, Any]], max_latency_share: float = 0.4, min_runs: int = 2) -> list[dict[str, Any]]:
    """Insights strukturalne na styl Abstral: waskie gardla i niedopasowania modeli."""
    summary = summarize_traces(events)
    insights: list[dict[str, Any]] = []

    routed_by_node = {ev["node"]: ev for ev in events if ev.get("type") == "routed"}
    node_latencies = [
        (ev.get("node"), ev.get("latency_ms") or 0)
        for ev in events
        if ev.get("type") == "node_result"
    ]
    total_latency = sum(lat for _, lat in node_latencies) or 1
    for node, latency in node_latencies:
        share = latency / total_latency
        if share >= max_latency_share and len(node_latencies) >= min_runs:
            kind = routed_by_node.get(node, {}).get("kind")
            insights.append({
                "insight_id": f"bottleneck:{node}",
                "kind": "bottleneck",
                "target": node,
                "evidence": {"latency_share": round(share, 3), "latency_ms": latency, "task_kind": kind},
                "suggested_skill_patch": (
                    f"Wezel {node} (kind={kind}) generuje {round(share * 100)}% latencji lancucha. "
                    "Rozważ przeniesienie na szybszy model o tym samym tierze (router: speed_class=fast) "
                    "lub podzial zadania na dwa lzejsze wezly."
                ),
                "confidence": round(share, 3),
            })

    for model_id, stats in summary["models"].items():
        if stats["count"] >= min_runs and stats["ok_rate"] < 0.5:
            kinds_hit = [
                r.get("kind") for r in events
                if r.get("type") == "routed" and (r.get("chosen") or {}).get("model_id") == model_id
            ]
            insights.append({
                "insight_id": f"quality_gap:{model_id}",
                "kind": "quality_gap",
                "target": model_id,
                "evidence": {"ok_rate": stats["ok_rate"], "runs": stats["count"], "task_kinds": sorted(set(k for k in kinds_hit if k))},
                "suggested_skill_patch": (
                    f"Model {model_id} ma ok_rate {stats['ok_rate']} na {stats['count']} uruchomieniach. "
                    "Rozważ podniesienie tieru w rejestrze, obnizenie budzetu RPM w runach "
                    "lub wylaczenie providera w quota_snapshot (status=stale)."
                ),
                "confidence": round(1 - stats["ok_rate"], 3),
            })

    for kind, stats in summary["kinds"].items():
        if stats["count"] >= min_runs and stats["avg_latency_ms"] >= 1500:
            insights.append({
                "insight_id": f"slow_kind:{kind}",
                "kind": "slow_kind",
                "target": kind,
                "evidence": {"avg_latency_ms": stats["avg_latency_ms"], "runs": stats["count"]},
                "suggested_skill_patch": (
                    f"Rodzaj zadania {kind} srednio trwa {stats['avg_latency_ms']} ms. "
                    "Rozważ dodanie wariantu skilla z mniejszym kontekstem albo routing do modelu fast."
                ),
                "confidence": round(min(stats["avg_latency_ms"] / 3000, 1.0), 3),
            })

    return insights
