#!/usr/bin/env python3
"""Rezydentny agent-orkiestrator (selfopt_chain, T49).

Wizja operatora: po uruchomieniu chodzi agent, który AUTOMATYCZNIE używa
darmowych zasobów API AI i rozwija procesy w kierunku fizycznych możliwości
rozbudowy i produkcji opisanych w repo (README „Etap 1": resource scouting,
w tym elektrośmieci) - rozbudowując zdolności systemu do służenia ludziom.

Cykl orkiestratora:
1. Kill switch (plik) -> stop z receiptem; SIGTERM/SIGINT -> gracefully.
2. Bramka quota: tryb free-api wymaga quota_snapshot z provider_quota_monitor
   (status ok dla wszystkich) - inaczej cykl pominięty (human control point
   „no_agent_chain_without_ok_snapshot"). Tryb mock biega offline bez bramki.
3. Zbiór zadań: rekordy resource_scout (JSON), inbox LoRa (EDGE->HUB),
   bootstrap demo gdy pusto. Dedup po odcisku rekordu (stan w state-dir).
4. Zadanie -> łańcuch AI (classify -> extract -> draft -> review) na modelach
   wybranych przez router; wyniki + capability_map -> draft rozbudowy
   zdolności w procdev_queue (SUGGEST-ONLY: auto_applied=false).
5. Budżety: dobowe limity per model z rejestru, stan persystowany, reset
   przy zmianie daty; widok rejestru z odjętym zużyciem trafia do routera.

Zero aktuation, zero auto-merge; wszystkie artefakty czekają na review.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import signal
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from selfopt_chain.registry import DEFAULT_REGISTRY, load_registry
from selfopt_chain.run_loop import run_chain

DEFAULT_STATE_DIR = ROOT / "scratch" / "selfopt"
DEFAULT_KILL_SWITCH = DEFAULT_STATE_DIR / "KILL_SWITCH"
DEFAULT_INTERVAL_S = 300
DEFAULT_MAX_JOBS = 3
CAPABILITY_MAP_PATH = Path(__file__).with_name("capability_map.json")
BOOTSTRAP_RECORD = {
    "id": "selfopt_bootstrap_001",
    "source": {"type": "bootstrap_demo", "url_or_note": "Wbudowana probka: smartfony z lokalnej grupy (demonstracja petli orkiestratora)"},
    "location": {"country": "PL", "region": "local", "pickup_radius_km": 15},
    "cost": {"amount_pln": 0, "currency": "PLN", "condition": "free_pickup"},
    "resource_class": "old_smartphones",
    "possible_products": ["phone-aquaponics-observer"],
    "risks": ["bootstrap_demo_no_real_offer"],
    "required_evidence": ["front_back_photos"],
    "activation_requirements": {"energy": "charge from OZE surplus", "logistics": "one human pickup"},
    "activation_fit": "oze_or_free_energy",
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def fingerprint(record: dict[str, Any]) -> str:
    return hashlib.sha1(json.dumps(record, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:16]


def load_capability_map(path: Path = CAPABILITY_MAP_PATH) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if "default" not in data.get("classes", {}):
        raise ValueError("capability_map: brak wpisu 'default'")
    return data


def match_capability(resource_class: str, capability_map: dict[str, Any]) -> dict[str, Any]:
    return capability_map["classes"].get(resource_class, capability_map["classes"]["default"])


def quota_gate(engine_name: str, snapshot_path: Path | None) -> dict[str, Any]:
    """Bramka „no_agent_chain_without_ok_snapshot" dla realnych wywołań API."""
    if engine_name != "free-api":
        return {"allowed": True, "reason": "mock_engine_bez_bramki_quota"}
    if snapshot_path is None or not snapshot_path.exists():
        return {"allowed": False, "reason": "quota_snapshot_blocked:missing_snapshot"}
    from provider_quota_monitor.snapshot import block_decision

    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    decision = block_decision(snapshot)
    if decision["blocked"]:
        return {"allowed": False, "reason": f"quota_snapshot_blocked:{decision['reason']}"}
    return {"allowed": True, "reason": "quota_snapshot_ok"}


class OrchestratorState:
    """Stan persystowany: licznik cykli, odciski przetworzonych zadań, budżety dobowe."""

    def __init__(self, state_dir: Path) -> None:
        self.path = state_dir / "orchestrator_state.json"
        self.data: dict[str, Any] = {"date": _today(), "cycle": 0, "processed": {}, "daily_calls": {}}

    def load(self) -> None:
        if self.path.exists():
            loaded = json.loads(self.path.read_text(encoding="utf-8"))
            if loaded.get("date") != _today():
                loaded["date"] = _today()
                loaded["daily_calls"] = {}
            self.data = loaded

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")

    def already_processed(self, fp: str) -> bool:
        return fp in self.data["processed"]

    def mark_processed(self, fp: str, job_id: str) -> None:
        self.data["processed"][fp] = {"job_id": job_id, "ts": _now_iso()}

    def record_calls(self, models_used: list[str]) -> None:
        for mid in models_used:
            self.data["daily_calls"][mid] = self.data["daily_calls"].get(mid, 0) + 1

    def budgeted_models(self, models: list[dict]) -> list[dict]:
        """Widok rejestru z odjętym dobowym zużyciem; modele z wyczerpanym
        budżetem są usuwane (walidator rejestru wymaga limitów > 0, a router
        ma wybrać alternatywę zamiast dostawać martwego kandydata)."""
        view = []
        for m in models:
            remaining = m.get("rpd_seed", 0) - self.data["daily_calls"].get(m["model_id"], 0)
            if remaining > 0:
                m2 = dict(m)
                m2["rpd_seed"] = remaining
                view.append(m2)
        return view


class Job:
    def __init__(self, job_id: str, source: str, record: dict[str, Any]) -> None:
        self.job_id = job_id
        self.source = source
        self.record = record
        self.fingerprint = fingerprint(record)


def collect_jobs(records_paths: list[Path], inbox_dir: Path | None) -> list[Job]:
    jobs: list[Job] = []
    for path in records_paths:
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        for record in data.get("records", []):
            jobs.append(Job(str(record.get("id", uuid.uuid4().hex[:8])), "resource_scout", record))
    if inbox_dir is not None and inbox_dir.exists():
        for msg_path in sorted(inbox_dir.glob("*.json")):
            msg = json.loads(msg_path.read_text(encoding="utf-8"))
            record = {
                "id": f"inbox_{msg_path.stem}",
                "source": {"type": "lora_inbox", "url_or_note": msg.get("payload_text", "")},
                "location": {"country": "PL", "region": "field", "pickup_radius_km": 0},
                "cost": {"amount_pln": 0, "currency": "PLN", "condition": "n/a"},
                "resource_class": "field_feedback",
                "possible_products": ["skill-patch-proposal"],
                "risks": ["field_data_unverified"],
                "required_evidence": ["operator_ack"],
                "activation_requirements": {"energy": "n/a", "logistics": "n/a"},
                "payload_text": msg.get("payload_text", ""),
            }
            jobs.append(Job(record["id"], "lora_inbox", record))
    return jobs


def build_chain_def(job: Job) -> dict[str, Any]:
    prompt_context = json.dumps(job.record, ensure_ascii=False)
    return {
        "chain_id": f"procdev_{job.job_id}",
        "nodes": [
            {"id": "classify", "kind": "classify", "privacy": "public", "complexity": "light", "requires": ["text"],
             "prompt": f"Ocen klase zasobu i pilnosci dla misji Strazy Przyszlosci. Rekord:\n{prompt_context}"},
            {"id": "extract", "kind": "extract", "privacy": "public", "complexity": "medium", "requires": ["text", "json"],
             "prompt": f"Wyciagnij kluczowe parametry zasobu (klasa, lokalizacja, koszt, ryzyka, evidence, energia/logistyka):\n{prompt_context}"},
            {"id": "draft", "kind": "draft", "privacy": "public", "complexity": "medium", "requires": ["text", "json"],
             "prompt": f"Zredaguj krotki draft dossier potencjalu: co z tego zasobu moze sluzyc ludziom, jaki produkt, dla kogo:\n{prompt_context}"},
            {"id": "review", "kind": "review", "privacy": "public", "complexity": "light", "requires": ["text"],
             "prompt": f"Zweryfikuj draft wzgledem ryzyk i brakujacej evidencji; co musi potwierdzic czlowiek:\n{prompt_context}"},
        ],
        "pipeline": ["classify", "extract", "draft", "review"],
        "payload": job.record,
    }


def render_procdev_draft(job: Job, capability: dict[str, Any], outputs: dict[str, Any], models_used: list[str], quota_usage: dict[str, Any]) -> str:
    record = job.record
    repo_refs = "\n".join(f"- {ref}" for ref in capability["repo_refs"])
    products = ", ".join(capability["products"]) or "-"
    cells = ", ".join(capability["cells"]) or "-"
    serves = ", ".join(capability["serves"]) or "-"
    ai_lines = []
    for node in ("classify", "extract", "draft", "review"):
        out = outputs.get(node, {})
        ai_lines.append(f"- {node}: `{out.get('output', '')}` (model: {out.get('model_id', 'n/a')}, ok={out.get('ok')})")
    lines = [
        f"# Propozycja rozbudowy zdolności — {job.job_id} (suggest-only)",
        "",
        f"- źródło zadania: **{job.source}**",
        f"- zasób: `{record.get('id')}`, klasa: `{record.get('resource_class')}`, koszt: {record.get('cost', {}).get('amount_pln')} PLN",
        f"- lokalizacja: {record.get('location', {})}",
        f"- ryzyka: {record.get('risks')}",
        "",
        "## Dopasowanie zdolności (capability_map)",
        f"- zdolność: **{capability['capability']}** (służy: {serves})",
        f"- produkty: {products}",
        f"- istniejące komórki: {cells}",
        f"- następny proces: {capability['next_process']}",
        " Referencje repo:",
        repo_refs,
        "",
        "## Wyniki łańcucha AI (darmowe modele, routing wg jakości)",
        *ai_lines,
        "",
        "## Proponowane kroki (każdy pod bramką człowieka)",
        "1. Komplet evidencji: " + ", ".join(record.get("required_evidence", [])) + ".",
        f"2. Logistyka: {record.get('activation_requirements', {}).get('logistics', 'n/a')}.",
        f"3. Energia: {record.get('activation_requirements', {}).get('energy', 'n/a')}.",
        "4. Bench na recovered hardware (edge_flasher, suggest-only) -> artefakty do review.",
        "5. Pack draft -> PR (no_auto_merge, merge wyłącznie po review człowieka).",
        "",
        "## Zasady",
        "- status: **auto_applied: false** — nic nie zostało zaaplikowane;",
        "  artefakt czeka na review człowieka (konwencja suggest-only T38).",
        "- physical_actuation zabroniona; instalacja/aktuation tylko przez operatora.",
        f"- zużycie budżetu runu: {json.dumps(quota_usage, ensure_ascii=False)}",
        f"- modele użyte: {', '.join(sorted(set(models_used))) or 'brak (routing zablokowany)'}",
        "",
    ]
    return "\n".join(lines)


class Orchestrator:
    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.state_dir = Path(config["state_dir"])
        self.state = OrchestratorState(self.state_dir)
        self.state.load()
        self.capability_map = load_capability_map(Path(config.get("capability_map_path", CAPABILITY_MAP_PATH)))
        self.registry_path = Path(config.get("registry_path", DEFAULT_REGISTRY))
        self.stop_requested = False

    def request_stop(self, *_args: Any) -> None:
        self.stop_requested = True

    def kill_switch_active(self) -> bool:
        return Path(self.config["kill_switch"]).exists()

    def run_cycle(self) -> dict[str, Any]:
        cycle_no = self.state.data["cycle"] + 1
        receipt: dict[str, Any] = {
            "cycle": cycle_no,
            "started": _now_iso(),
            "engine": self.config["engine"],
            "kill_switch": False,
            "quota_gate": quota_gate(self.config["engine"], self.config.get("quota_snapshot_path")),
            "jobs_run": [],
            "jobs_skipped_processed": 0,
            "jobs_status": "ok",
            "auto_applied": False,
            "policy": "suggest-only",
        }
        if not receipt["quota_gate"]["allowed"]:
            receipt["finished"] = _now_iso()
            receipt["jobs_status"] = "skipped_quota_gate"
            return receipt

        jobs = collect_jobs(self.config["records_paths"], self.config.get("inbox_dir"))
        pending = [j for j in jobs if not self.state.already_processed(j.fingerprint)]
        receipt["jobs_skipped_processed"] = len(jobs) - len(pending)
        if not pending:
            if not jobs:
                pending = [Job(BOOTSTRAP_RECORD["id"], "bootstrap_demo", BOOTSTRAP_RECORD)]
                receipt["jobs_status"] = "bootstrap_demo"
            else:
                receipt["jobs_status"] = "no_new_jobs"
                receipt["finished"] = _now_iso()
                return receipt

        budgeted = self.state.budgeted_models(load_registry(self.registry_path))
        if not budgeted:
            receipt["jobs_status"] = "daily_budget_exhausted"
            receipt["finished"] = _now_iso()
            return receipt
        budget_registry_path = self.state_dir / f"registry_view_cycle_{cycle_no}.json"
        budget_registry_path.parent.mkdir(parents=True, exist_ok=True)
        budget_registry_path.write_text(json.dumps({"models": budgeted}, ensure_ascii=False, indent=2), encoding="utf-8")

        procdev_dir = self.state_dir / "procdev_queue"
        for job in pending[: self.config["max_jobs"]]:
            run_dir = self.state_dir / "runs" / f"cycle_{cycle_no}_{job.job_id}"
            chain_path = run_dir / "chain.json"
            chain_path.parent.mkdir(parents=True, exist_ok=True)
            chain_path.write_text(json.dumps(build_chain_def(job), ensure_ascii=False, indent=2), encoding="utf-8")
            rc = run_chain(
                chain_path=chain_path,
                out_dir=run_dir,
                engine_name=self.config["engine"],
                registry_path=budget_registry_path,
                quota_snapshot_path=self.config.get("quota_snapshot_path"),
                spool_dir=None,
            )
            models_used: list[str] = []
            outputs: dict[str, Any] = {}
            quota_usage: dict[str, Any] = {}
            run_receipt_path = run_dir / "run_receipt.json"
            if run_receipt_path.exists():
                run_receipt = json.loads(run_receipt_path.read_text(encoding="utf-8"))
                quota_usage = run_receipt.get("quota_usage", {}).get("rpd_used", {})
                models_used = sorted(quota_usage.keys())
            final_outputs_path = run_dir / "final_outputs.json"
            if final_outputs_path.exists():
                outputs = json.loads(final_outputs_path.read_text(encoding="utf-8"))
            capability = match_capability(job.record.get("resource_class", ""), self.capability_map)
            draft = render_procdev_draft(job, capability, outputs, models_used, quota_usage)
            procdev_dir.mkdir(parents=True, exist_ok=True)
            draft_path = procdev_dir / f"{job.job_id}.md"
            draft_path.write_text(draft, encoding="utf-8")
            self.state.record_calls(models_used)
            self.state.mark_processed(job.fingerprint, job.job_id)
            receipt["jobs_run"].append({
                "job_id": job.job_id,
                "source": job.source,
                "rc": rc,
                "run_dir": str(run_dir),
                "procdev_draft": str(draft_path),
                "capability": capability["capability"],
            })
        receipt["finished"] = _now_iso()
        return receipt

    def run(self) -> int:
        signal.signal(signal.SIGTERM, self.request_stop)
        signal.signal(signal.SIGINT, self.request_stop)
        max_cycles = self.config.get("max_cycles")
        while not self.stop_requested:
            if self.kill_switch_active():
                self.state_dir.mkdir(parents=True, exist_ok=True)
                stopped = {"stopped": True, "reason": "kill_switch", "ts": _now_iso(), "cycles_done": self.state.data["cycle"]}
                (self.state_dir / "stopped.json").write_text(json.dumps(stopped, ensure_ascii=False, indent=2), encoding="utf-8")
                print(json.dumps(stopped, ensure_ascii=False))
                return 0
            receipt = self.run_cycle()
            self.state.data["cycle"] = receipt["cycle"]
            self.state.save()
            cycles_dir = self.state_dir / "cycles"
            cycles_dir.mkdir(parents=True, exist_ok=True)
            (cycles_dir / f"cycle_{receipt['cycle']}.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
            print(json.dumps({k: receipt[k] for k in ("cycle", "jobs_status", "jobs_run", "quota_gate") if k in receipt}, ensure_ascii=False), flush=True)
            if max_cycles is not None and self.state.data["cycle"] >= max_cycles:
                return 0
            if self.stop_requested:
                break
            time.sleep(self.config.get("interval_s", DEFAULT_INTERVAL_S))
        self.state_dir.mkdir(parents=True, exist_ok=True)
        stopped = {"stopped": True, "reason": "signal", "ts": _now_iso(), "cycles_done": self.state.data["cycle"]}
        (self.state_dir / "stopped.json").write_text(json.dumps(stopped, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(stopped, ensure_ascii=False))
        return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Rezydentny agent-orkiestrator: darmowe modele AI rozwijają procesy repo (suggest-only)")
    parser.add_argument("--engine", choices=["mock", "free-api"], default="mock")
    parser.add_argument("--interval", type=int, default=DEFAULT_INTERVAL_S, help="sekundy między cyklami")
    parser.add_argument("--max-cycles", type=int, default=None, help="limit cykli (brak = daemon)")
    parser.add_argument("--once", action="store_true", help="jeden cykl i wyjście")
    parser.add_argument("--max-jobs", type=int, default=DEFAULT_MAX_JOBS)
    parser.add_argument("--state-dir", type=Path, default=DEFAULT_STATE_DIR)
    parser.add_argument("--kill-switch", type=Path, default=DEFAULT_KILL_SWITCH)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--records", type=Path, nargs="*", default=[ROOT / "resource_scout" / "examples" / "ewaste_phone_batch.json", ROOT / "resource_scout" / "examples" / "selfhost_compute_node.json"])
    parser.add_argument("--inbox-dir", type=Path, default=None, help="katalog wiadomości EDGE->HUB (JSON) do domknięcia pętli terenowej")
    parser.add_argument("--quota-snapshot", type=Path, default=ROOT / "agent_runtime_plans" / "hermes_pilot" / "quota_snapshot.json")
    args = parser.parse_args(argv if argv is not None else None)

    config: dict[str, Any] = {
        "engine": args.engine,
        "interval_s": 0 if args.once else args.interval,
        "max_cycles": 1 if args.once else args.max_cycles,
        "max_jobs": args.max_jobs,
        "state_dir": args.state_dir,
        "kill_switch": args.kill_switch,
        "registry_path": args.registry,
        "records_paths": [Path(p) for p in args.records],
        "inbox_dir": args.inbox_dir,
        "quota_snapshot_path": args.quota_snapshot if args.engine == "free-api" else None,
    }
    return Orchestrator(config).run()


if __name__ == "__main__":
    sys.exit(main())
