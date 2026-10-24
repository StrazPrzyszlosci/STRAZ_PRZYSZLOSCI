#!/usr/bin/env python3
"""Orkiestrator łańcucha procesów samooptymalizujących (selfopt_chain, T48).

CLI: uruchamia łańcuch zadań (definicja JSON), routuje każde zadanie do
darmowego modelu o odpowiedniej jakości (szybkość przy zachowaniu jakości),
zbiera ślady wykonania, emituje run_receipt.json + optimization_proposals.md,
a finalne advisory potrafi spakować do kopert LoRa (spool store-and-forward).

Tryb domyślny = MockEngine (offline, deterministyczny, zero sieci).
FreeApiEngine tylko z SELFOPT_NETWORK=1. Wszystko suggest-only.
"""
from __future__ import annotations

import argparse
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from selfopt_chain.adapters import engines_summary, get_graph_engine
from selfopt_chain.engine import FreeApiEngine, MockEngine
from selfopt_chain.omniroute import OmniRouteEngine
from selfopt_chain.graph import GraphError
from selfopt_chain.optimizers import GepaPromptOptimizer, MapElitesOptimizer
from selfopt_chain.registry import DEFAULT_REGISTRY, load_registry
from selfopt_chain.router import QuotaLedger, QuotaExceeded, route_task
from selfopt_chain.tracer import TraceRecorder, extract_insights, summarize_traces
from selfopt_chain.transport import (
    LoraEnvelope,
    LoraSpool,
    format_advisory_for_edge,
    sanitize_for_radio,
)

VALID_KINDS = {
    "format", "classify", "route", "summarize", "extract", "translate", "triage",
    "draft", "review", "code_draft", "reason", "multimodal_reason",
    "vision_extract", "large_batch_extraction",
}
NODE_TYPES = VALID_KINDS | {"dispatch"}


def validate_chain(chain: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    nodes = chain.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        return ["chain.nodes must be a non-empty array"]
    ids = [n.get("id") for n in nodes]
    if len(ids) != len(set(ids)):
        errors.append("chain.nodes: zduplikowane id wezlow")
    for i, n in enumerate(nodes):
        if not isinstance(n, dict):
            errors.append(f"nodes[{i}] must be object")
            continue
        nid = n.get("id", f"nodes[{i}]")
        if not nid:
            errors.append(f"nodes[{i}].id missing")
        node_type = n.get("type") or n.get("kind")
        if node_type not in NODE_TYPES:
            errors.append(f"{nid}: nieznany typ wezla {node_type!r}; dozwolone: {sorted(NODE_TYPES)}")
        if node_type == "dispatch":
            if n.get("destination") not in ("MESHTASTIC", "MESHCORE"):
                errors.append(f"{nid}: dispatch wymaga destination MESHTASTIC lub MESHCORE")
        else:
            if n.get("privacy") not in ("public", "private"):
                errors.append(f"{nid}: privacy must be public|private")
            if n.get("complexity") not in ("light", "medium", "heavy"):
                errors.append(f"{nid}: complexity must be light|medium|heavy")
    pipeline = chain.get("pipeline")
    if pipeline is not None:
        if not isinstance(pipeline, list) or not pipeline:
            errors.append("chain.pipeline must be non-empty array of node ids")
        else:
            unknown = [p for p in pipeline if p not in ids]
            if unknown:
                errors.append(f"chain.pipeline: nieznane wezly {unknown}")
    else:
        entry = chain.get("entry")
        if entry not in ids:
            errors.append(f"chain.entry {entry!r} nie wskazuje na zaden wezel")
        for n in nodes:
            nid = n.get("id")
            nexts = [n.get("next")] if n.get("next") else []
            for cond in n.get("conditional", []) or []:
                nexts.append(cond.get("next"))
            for nxt in nexts:
                if nxt not in ids and nxt != "__end__":
                    errors.append(f"{nid}: next/conditional wskazuje nieznany wezel {nxt!r}")
    return errors


def build_chain_graph(chain: dict[str, Any], runner: "ChainRunner") -> Any:
    engine_info = get_graph_engine()
    graph_cls = engine_info["StateGraph"]
    graph_start = engine_info["START"]
    graph_end = engine_info["END"]
    builder = graph_cls(dict)
    nodes = {n["id"]: n for n in chain["nodes"]}
    pipeline = chain.get("pipeline")
    if pipeline:
        order = list(pipeline)
    else:
        order = list(nodes)
    for nid in order:
        node = nodes[nid]
        builder.add_node(nid, runner.make_node_fn(node))
    if pipeline:
        builder.add_edge(graph_start, pipeline[0])
        for a, b in zip(pipeline, pipeline[1:]):
            builder.add_edge(a, b)
        builder.add_edge(pipeline[-1], graph_end)
    else:
        builder.set_entry_point(chain["entry"])
        for nid in order:
            node = nodes[nid]
            if node.get("conditional"):
                mapping = {c["when_output"]: graph_end if c["next"] == "__end__" else c["next"] for c in node["conditional"]}
                builder.add_conditional_edges(
                    nid,
                    lambda state, _nid=nid: (state.get("outputs", {}).get(_nid, {}).get("output") or "OK"),
                    mapping,
                )
            else:
                nxt = node.get("next", "__end__")
                builder.add_edge(nid, graph_end if nxt == "__end__" else nxt)
    return builder.compile()


class ChainRunner:
    def __init__(self, models: list[dict], engine_name: str, quota_snapshot: dict[str, Any] | None, tracer: TraceRecorder, spool: LoraSpool | None = None, decision_core: Any | None = None, ledger=None, should_stop=None, max_attempts: int = 2) -> None:
        self.models = models
        self.engine_name = engine_name
        self.decision_core = decision_core
        self.ledger = ledger if ledger is not None else QuotaLedger(models)
        self.should_stop = should_stop or (lambda: False)
        self.max_attempts = max_attempts
        self.usage: dict[str, int] = {}
        self.quota_snapshot = quota_snapshot
        self.tracer = tracer
        self.spool = spool
        self.routing: list[dict[str, Any]] = []
        self.dispatched: list[dict[str, Any]] = []
        self.blocked: list[dict[str, Any]] = []
        if engine_name == "free-api":
            self.engine = FreeApiEngine(models)
        elif engine_name == "omniroute":
            self.engine = OmniRouteEngine(models)
        else:
            self.engine = MockEngine(models)

    def make_node_fn(self, node: dict[str, Any]):
        def fn(state: dict[str, Any]) -> dict[str, Any]:
            node_type = node.get("type") or node.get("kind")
            previous = state.get("last_node")
            if self.should_stop() or (previous and not state.get("outputs", {}).get(previous, {}).get("ok")):
                result = {"ok": False, "output": "", "error_class": "stopped" if self.should_stop() else "dependency_failed"}
                return {"outputs": {**state.get("outputs", {}), node["id"]: result}, "last_node": node["id"], "route": "SKIP"}
            if node_type == "dispatch":
                return self._dispatch_node(node, state)
            task = {
                "task_id": node["id"],
                "kind": node_type,
                "privacy": node.get("privacy", "public"),
                "complexity": node.get("complexity", "light"),
                "requires": node.get("requires", []),
            }
            context = {"payload": state.get("payload", {}), "previous_outputs": state.get("outputs", {})}
            prompt = node.get("prompt", "") + "\n" + json.dumps(context, ensure_ascii=False)
            if len(prompt.encode()) > 65536:
                result = {"ok": False, "output": "", "error_class": "context_limit_exceeded"}
                return {"outputs": {**state.get("outputs", {}), node["id"]: result}, "last_node": node["id"]}
            result = {"ok": False, "output": "", "error": "not attempted", "error_class": "routing_blocked"}
            attempted = set()
            for attempt in range(self.max_attempts):
                if self.should_stop():
                    result = {"ok": False, "output": "", "error": "operator stop", "error_class": "stopped"}
                    break
                eligible = [m for m in self.models if m["model_id"] not in attempted]
                decision = route_task(task, eligible, self.ledger, self.quota_snapshot)
                self.tracer.routed(decision, node["id"])
                if decision["blocked"]:
                    self.blocked.append({"node": node["id"], "reason": decision["blocked_reason"]})
                    result = {"ok": False, "output": "", "error": decision["blocked_reason"], "error_class": "routing_blocked"}
                    break
                model_id = self.decision_core.select_model(decision, node_type) if self.decision_core else decision["chosen"]["model_id"]
                candidates = {decision["chosen"]["model_id"], *[m["model_id"] for m in decision["alternatives"]]}
                if model_id not in candidates:
                    result = {"ok": False, "output": "", "error": "model outside candidates", "error_class": "routing_blocked"}
                    break
                attempted.add(model_id)
                try:
                    self.ledger.record(model_id)
                except QuotaExceeded:
                    continue
                self.usage[model_id] = self.usage.get(model_id, 0) + 1
                result = self.engine.complete(task, model_id, prompt)
                self.tracer.node_result(node["id"], result)
                self.routing.append({**decision, "node": node["id"], "ok": result["ok"], "model_selected_by_basal": model_id, "attempt": attempt + 1})
                if result["ok"] or result.get("error_class") not in {"http_error", "connection_error"}:
                    break
            outputs = {**state.get("outputs", {}), node["id"]: result}
            return {"outputs": outputs, "last_node": node["id"], "route": result.get("output", "")}

        return fn

    def _dispatch_node(self, node: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
        if self.spool is None:
            self.tracer.error(node["id"], "dispatch bez spool-dir")
            result = {"ok": False, "output": "", "error": "no spool configured", "error_class": "no_spool"}
            return {"outputs": {**state.get("outputs", {}), node["id"]: result}, "last_node": node["id"], "route": "SKIP"}
        last = state.get("last_node")
        text = sanitize_for_radio(str((state.get("outputs", {}).get(last, {}) or {}).get("output", "")))
        payload = format_advisory_for_edge(text)
        envelope = LoraEnvelope(payload, destination_network=node.get("destination", "MESHTASTIC"), destination_channel=int(node.get("channel", 0)), ttl_minutes=int(node.get("ttl_minutes", 30)))
        receipt = self.spool.enqueue(envelope)
        self.tracer.event("lora_dispatch", node=node["id"], envelope_id=envelope.id, enqueued=receipt["enqueued"], reason=receipt["reason"], priority=envelope.priority)
        self.dispatched.append({"node": node["id"], "envelope_id": envelope.id, "priority": envelope.priority, "enqueued": receipt["enqueued"], "reason": receipt["reason"]})
        result = {"ok": bool(receipt["enqueued"]), "output": json.dumps(receipt, ensure_ascii=False)}
        return {"outputs": {**state.get("outputs", {}), node["id"]: result}, "last_node": node["id"], "route": "DISPATCH" if receipt["enqueued"] else "SKIP"}


def render_proposals_md(run_id: str, insights: list[dict[str, Any]], gepa: dict[str, Any], map_elites: dict[str, Any], summary: dict[str, Any], engines: dict[str, Any]) -> str:
    lines = [
        "# Propozycje optymalizacji łańcucha (suggest-only)",
        "",
        f"- run_id: `{run_id}`",
        f"- silniki: graph={engines['graph']}, gepa={engines['gepa']}, openevolve={engines['openevolve']}",
        "- status: **nic nie zostało auto-zaaplikowane**; każdą propozycję review'uje człowiek (konwencja T38).",
        "",
        "## 1. Routing i wąskie gardła (Abstral-inspired)",
        "",
    ]
    if not insights:
        lines.append("Brak wąskich gardeł powyżej progów w tym runie.")
    for ins in insights:
        lines.append(f"### {ins['insight_id']} (confidence={ins['confidence']})")
        lines.append(f"- evidence: `{json.dumps(ins['evidence'], ensure_ascii=False)}`")
        lines.append(f"- propozycja: {ins['suggested_skill_patch']}")
        lines.append("")
    lines.append("## 2. Kandydaci promptów (GEPA-Pareto)")
    lines.append(f"- front Pareto: `{gepa.get('pareto_front')}`")
    lines.append(f"- wybór: `{gepa.get('chosen_id')}`; {gepa.get('rationale')}")
    lines.append("")
    lines.append("## 3. Archiwum programów (OpenEvolve MAP-Elites)")
    lines.append(f"- nisze: {map_elites.get('niches')}")
    for row in map_elites.get("archive", []):
        lines.append(f"- kind={row['kind']} complexity={row['complexity']}: `{row['program_id']}` fitness={row['fitness']}")
    lines.append("")
    lines.append("## 4. Statystyki modeli tego runu")
    for model_id, stats in sorted(summary.get("models", {}).items()):
        lines.append(f"- {model_id}: ok_rate={stats['ok_rate']}, avg_latency_ms={stats['avg_latency_ms']}, runs={stats['count']}")
    lines.append("")
    return "\n".join(lines)


def run_chain(chain_path: Path, out_dir: Path, engine_name: str, registry_path: Path, quota_snapshot_path: Path | None, spool_dir: Path | None, decision_core: Any | None = None, ledger=None, should_stop=None) -> int:
    chain = json.loads(chain_path.read_text(encoding="utf-8"))
    errors = validate_chain(chain)
    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        return 2

    out_dir.mkdir(parents=True, exist_ok=True)
    effective_spool_dir = spool_dir or (out_dir / "lora_spool")
    run_id = uuid.uuid4().hex[:12]
    tracer = TraceRecorder(run_id, out_path=out_dir / "traces.jsonl")
    models = load_registry(registry_path)

    quota_snapshot: dict[str, Any] | None = None
    if quota_snapshot_path is not None:
        quota_snapshot = json.loads(quota_snapshot_path.read_text(encoding="utf-8"))

    has_dispatch = any((n.get("type") or n.get("kind")) == "dispatch" for n in chain["nodes"])
    spool = LoraSpool(effective_spool_dir) if has_dispatch else None
    runner = ChainRunner(models, engine_name, quota_snapshot, tracer, spool, decision_core=decision_core, ledger=ledger, should_stop=should_stop)
    tracer.run_start(chain.get("chain_id", chain_path.stem), engine_name)

    started = datetime.now(timezone.utc).isoformat(timespec="seconds")
    status = "ok"
    final_outputs: dict[str, Any] = {}
    try:
        graph = build_chain_graph(chain, runner)
        state: dict[str, Any] = {"payload": chain.get("payload", {})}
        final = graph.invoke(state)
        nodes_run = len(final.get("outputs", {}))
        final_outputs = final.get("outputs", {})
    except GraphError as exc:
        status = f"failed: {exc}"
        nodes_run = 0
        tracer.error("graph", str(exc))
    failures = [nid for nid, result in final_outputs.items() if not result.get("ok")]
    if failures or nodes_run == 0:
        status = "failed" if not any(r.get("ok") for r in final_outputs.values()) else "degraded"
    tracer.run_end(status, nodes_run)
    (out_dir / "final_outputs.json").write_text(json.dumps(final_outputs, ensure_ascii=False, indent=2), encoding="utf-8")
    finished = datetime.now(timezone.utc).isoformat(timespec="seconds")

    insights = extract_insights(tracer.dump())
    gepa = GepaPromptOptimizer().optimize(chain.get("prompt_candidates", []))
    map_elites = MapElitesOptimizer()
    map_elites.step(chain.get("program_candidates", []))
    me_proposal = map_elites.proposal()
    me_proposal["archive"] = [
        {"kind": row["kind"], "complexity": row["complexity"], "program_id": row["program_id"], "fitness": row["fitness"]}
        for row in me_proposal["archive"]
    ]
    summary = summarize_traces(tracer.dump())

    receipt = {
        "run_id": run_id,
        "chain_id": chain.get("chain_id", chain_path.stem),
        "started": started,
        "finished": finished,
        "status": status,
        "engine": engine_name,
        "engines_detected": engines_summary(),
        "models_registry": str(registry_path),
        "nodes_run": nodes_run,
        "routed": len(runner.routing),
        "blocked": runner.blocked,
        "lora_dispatched": runner.dispatched,
        "quota_usage": {"rpm_used": runner.usage, "rpd_used": runner.usage},
        "insights_count": len(insights),
        "policy": "suggest-only",
        "auto_applied": False,
        "artifacts": ["traces.jsonl", "run_receipt.json", "optimization_proposals.md", "final_outputs.json"],
        "spool_dir": str(effective_spool_dir) if spool else None,
    }
    (out_dir / "run_receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    proposals_md = render_proposals_md(run_id, insights, gepa, me_proposal, summary, engines_summary())
    (out_dir / "optimization_proposals.md").write_text(proposals_md, encoding="utf-8")

    print(json.dumps({"run_id": run_id, "status": status, "nodes_run": nodes_run, "routed": len(runner.routing), "insights": len(insights), "out_dir": str(out_dir)}, ensure_ascii=False))
    return 0 if status == "ok" else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Orkiestrator łańcucha samooptymalizującego (darmowe modele AI)")
    parser.add_argument("--chain", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=None, help="katalog wyjsciowy (default: scratch/selfopt/<chain>_<ts>)")
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--engine", choices=["mock", "free-api", "omniroute"], default="mock")
    parser.add_argument("--quota-snapshot", type=Path, default=None)
    parser.add_argument("--spool-dir", type=Path, default=None)
    args = parser.parse_args(argv if argv is not None else None)

    out_dir = args.out
    if out_dir is None:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out_dir = Path("scratch/selfopt") / f"{args.chain.stem}_{ts}"
    return run_chain(args.chain, out_dir, args.engine, args.registry, args.quota_snapshot, args.spool_dir)


if __name__ == "__main__":
    sys.exit(main())
