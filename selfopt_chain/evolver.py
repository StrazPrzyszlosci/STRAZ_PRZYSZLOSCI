#!/usr/bin/env python3
"""Pętla samoewolucji repo (selfopt_chain, T52).

Realizacja dyrektywy operatora (2026-10-22): „repo ma samo ewoluować, a nie
być rozbudowywane jednym modelem w Kilo Code". Rój cyklicznie:
1. ZBIERA zadania ewolucyjne z własnych artefaktów i stanu repo:
   - handoffy: sekcje „Następne zadania (propozycje T*)" (deterministyczny parser),
   - propozycje optymalizacji z cykli (optimization_proposals.md: insights/GEPA/MAP-Elites),
   - celowniki operatora: evolution_targets.json.
2. basal DECYDUJE tryb równoległości (single|wide|deep):
   wide = N zadań równolegle na różne modele; deep = szybki słaby model pisze,
   duży model sprawdza (dyrektywa operatora), single = oszczędnie.
3. WYKONUJE: mock-lane (offline, szablon propozycji) lub HermesWorker
   headless (uzbrojony tryb: OmniRoute → darmowe LLM, sandbox, kwarantanna).
4. BRAMKA: SecurityGate skanuje każdą produkcję; naruszenie = kwarantanna
   trzyma („zły kod nie wchodzi do roju"), licencje copyleft → review.
5. Artefakty: scratch/selfopt/evolution_queue/<id>/PROPOSAL.md (gotowy
   szkic PR) + gate_report.json; wszystko suggest-only — merge tylko człowiek.

Deterministycznie testowalne offline; realne LLM po uzbrojeniu
(SELFOPT_NETWORK=1 + OmniRoute + SELFOPT_HERMES=1).
"""
from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from selfopt_chain.hermes_worker import HermesWorker, SecurityGate
from selfopt_chain.swarm import BasalDecisionCore

TARGETS_PATH = Path(__file__).with_name("evolution_targets.json")
NEXT_TASKS_RE = re.compile(r"^\d+\.\s*\*\*(T\d+[^*]*)\*\*[:\s]+(.*)$", re.MULTILINE)


@dataclass
class EvolutionTask:
    task_id: str
    title: str
    source: str
    context: str = ""
    constraints: str = "suggest-only; testy obowiązkowe; merge tylko przez PR człowieka"
    lane_role: str = "work"


def _parse_handoff_tasks(docs_dir: Path, limit: int = 5) -> list[EvolutionTask]:
    """Deterministyczny parser sekcji 'Następne zadania' z handoffów."""
    tasks: list[EvolutionTask] = []
    handoffs = sorted(docs_dir.glob("HANDOFF_DLA_NASTEPNEGO_AGENTA_*.md"), reverse=True)
    for handoff in handoffs[:2]:
        text = handoff.read_text(encoding="utf-8")
        section = re.split(r"Następne zadania|Nastepne zadania", text, maxsplit=1)
        if len(section) < 2:
            continue
        for match in NEXT_TASKS_RE.finditer(section[1]):
            title = f"{match.group(1).strip()}: {match.group(2).strip()[:120]}"
            tasks.append(EvolutionTask(
                task_id=f"handoff_{handoff.stem[-30:]}_{len(tasks)}",
                title=title,
                source=f"handoff:{handoff.name}",
                context=match.group(0),
            ))
            if len(tasks) >= limit:
                return tasks
    return tasks


def _parse_proposal_tasks(state_dir: Path, limit: int = 5) -> list[EvolutionTask]:
    """Insighty i propozycje z artifacts cykli → zadania ewolucyjne."""
    tasks: list[EvolutionTask] = []
    proposals = sorted(state_dir.rglob("optimization_proposals.md"))
    for proposal in proposals[:3]:
        text = proposal.read_text(encoding="utf-8")
        for header in re.findall(r"^### (bottleneck:[^\n]+|quality_gap:[^\n]+|slow_kind:[^\n]+)$", text, re.MULTILINE)[:limit]:
            tasks.append(EvolutionTask(
                task_id=f"proposal_{proposal.parent.name}_{len(tasks)}",
                title=f"Popraw wskazówkę z artefaktu: {header}",
                source=f"proposal:{proposal}",
                context=header,
            ))
            if len(tasks) >= limit:
                return tasks
    return tasks


def _parse_targets(path: Path = TARGETS_PATH) -> list[EvolutionTask]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return [
        EvolutionTask(
            task_id=f"target_{t['target_id']}",
            title=t["title"],
            source=f"evolution_targets:{t['target_id']}",
            context=t.get("source_hint", ""),
            constraints=t.get("constraints", "suggest-only"),
        )
        for t in data.get("targets", [])
    ]


def collect_evolution_tasks(state_dir: Path, docs_dir: Path, max_tasks: int = 6) -> list[EvolutionTask]:
    """Zbiór zadań: handoffy + proposals + celowniki; deterministycznie."""
    tasks = _parse_handoff_tasks(docs_dir) + _parse_proposal_tasks(state_dir) + _parse_targets()
    seen: set[str] = set()
    unique: list[EvolutionTask] = []
    for task in tasks:
        if task.task_id in seen:
            continue
        seen.add(task.task_id)
        unique.append(task)
    return unique[:max_tasks]


def decide_parallel_mode(core: BasalDecisionCore, backlog: int, critical: int) -> str:
    """basal decyduje: single | wide | deep (równoległość subagentów)."""
    scores = {
        "single": 1.0,
        "wide": 0.4 + 0.25 * min(backlog, 6),
        "deep": 0.3 + 0.6 * critical,
    }
    decision = core.decide("choice", list(scores), scores, default_option="single", context={"backlog": backlog, "critical": critical})
    return decision["final"]


def build_task_query(task: EvolutionTask, repo_root: Path) -> str:
    return "\n".join([
        "# Zadanie ewolucji repo (rój Straży Przyszłości)",
        f"- Tytuł: {task.title}",
        f"- Źródło: {task.source}",
        f"- Kontekst: {task.context or 'brak'}",
        f"- Ograniczenia: {task.constraints}",
        "",
        "Zasady nienegocjowalne:",
        "- suggest-only: proponujesz zmiany jako patch/PR-draft, nie wykonujesz push do main;",
        "- kod offline-testowalny, deterministyczne testy w stylu repo (python3 -m unittest);",
        "- zakaz sekretów, destrukcji, physical_actuation, exfiltracji env;",
        "- repo:", str(repo_root),
        "",
        "Wykonaj: przeanalizuj wskazany kontekst, przygotuj minimalny patch/propozycję",
        "i listę testów do uruchomienia. Wynik zapisz jako PLIKI w katalogu bieżącym",
        "(PROPOSAL.md + opcjonalne fragmenty kodu w plikach).",
    ])


def render_mock_proposal(task: EvolutionTask, parallel_mode: str, gate_report: dict[str, Any]) -> str:
    return "\n".join([
        f"# Propozycja ewolucji repo — {task.title} (suggest-only)",
        "",
        f"- task_id: `{task.task_id}`",
        f"- źródło: {task.source}",
        f"- tryb równoległości basal: **{parallel_mode}**",
        "- wykonawca: mock-lane (offline); realny Hermes+OmniRoute po uzbrojeniu",
        "",
        "## Kontekst",
        task.context or "(uzepełnij po analizie)",
        "",
        "## Proponowane kroki",
        "1. Analiza kontekstu i dotkniętych plików (własny obszar claimu!).",
        "2. Minimalny patch + testy (offline, deterministyczne).",
        "3. Pełna suita: `python3 -m unittest discover -s tests -p 'test_*.py'`.",
        "4. PR draft po review bramki; merge wyłącznie człowiek (no_auto_merge).",
        "",
        "## Ograniczenia",
        f"- {task.constraints}",
        "",
        f"## Bramka bezpieczeństwa",
        f"- ok: {gate_report.get('ok')}; violations: {len(gate_report.get('violations', []))}; licencje do review: {len(gate_report.get('licenses_review', []))}",
        "- status: **auto_applied: false** — artefakt czeka na review człowieka.",
        "",
    ])


class EvolutionLoop:
    """Jeden przebieg ewolucji repo: zadania → (mock|hermes) → bramka → kolejka."""

    def __init__(self, state_dir: Path, docs_dir: Path, repo_root: Path, worker: HermesWorker | None = None) -> None:
        self.state_dir = state_dir
        self.docs_dir = docs_dir
        self.repo_root = repo_root
        self.worker = worker
        self.gate = SecurityGate()
        self.queue_dir = state_dir / "evolution_queue"

    def run(self, max_tasks: int = 4, parallel_mode: str = "single") -> list[dict[str, Any]]:
        tasks = collect_evolution_tasks(self.state_dir, self.docs_dir, max_tasks=max_tasks)
        results: list[dict[str, Any]] = []
        for task in tasks:
            run_id = f"{task.task_id}_{uuid.uuid4().hex[:6]}"
            out_dir = self.queue_dir / run_id
            out_dir.mkdir(parents=True, exist_ok=True)
            receipt: dict[str, Any] = {
                "run_id": run_id,
                "task_id": task.task_id,
                "title": task.title,
                "source": task.source,
                "parallel_mode": parallel_mode,
                "executor": "mock",
                "gate_ok": None,
                "quarantined": False,
                "proposal_path": None,
            }
            if self.worker is not None and HermesWorker.enabled():
                receipt["executor"] = "hermes"
                query = build_task_query(task, self.repo_root)
                hermes_receipt = self.worker.run_isolated(query)
                receipt["hermes_run_id"] = hermes_receipt.get("run_id")
                receipt["hermes_executed"] = hermes_receipt.get("executed")
                report = hermes_receipt.get("security_gate") or {"ok": False, "violations": [{"rule": "hermes_not_executed"}], "licenses_review": []}
                (out_dir / "hermes_receipt.json").write_text(json.dumps(hermes_receipt, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
            else:
                proposal = render_mock_proposal(task, parallel_mode, {"ok": True, "violations": [], "licenses_review": []})
                proposal_path = out_dir / "PROPOSAL.md"
                proposal_path.write_text(proposal, encoding="utf-8")
                report = self.gate.inspect_code(proposal)
                receipt["proposal_path"] = str(proposal_path)
            (out_dir / "gate_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
            receipt["gate_ok"] = report.get("ok")
            receipt["quarantined"] = bool(report.get("quarantine_required"))
            receipt["auto_applied"] = False
            results.append(receipt)
        return results
