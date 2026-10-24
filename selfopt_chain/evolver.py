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
import hashlib
import fcntl
import time
from contextlib import contextmanager
from itertools import zip_longest
import os
import re
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from selfopt_chain.hermes_worker import HermesWorker, SecurityGate
from selfopt_chain.swarm import BasalDecisionCore

TARGETS_PATH = Path(__file__).with_name("evolution_targets.json")
NEXT_TASKS_RE = re.compile(r"^\d+\.\s*\*\*(T\d+[^*]*)\*\*[:\s]+(.*)$", re.MULTILINE)
DEFAULT_DRAFT_ALIAS = os.environ.get("SELFOPT_EVOLVE_DRAFT_MODEL", "auto/best-fast")
DEFAULT_REVIEW_ALIAS = os.environ.get("SELFOPT_EVOLVE_REVIEW_MODEL", "auto/best-reasoning")


def review_by_strong_model(task: EvolutionTask, produced_text: str, review_engine: Any | None, review_alias: str = DEFAULT_REVIEW_ALIAS) -> dict[str, Any]:
    """DYREKTYWA: mocny model sprawdza to, co zrobił słaby model.

    Review semantyczny (oprócz SecurityGate wzorców): czy produkcja spełnia
    zadanie, co poprawić, verdict pass | needs_fixes | fail.
    Offline (brak engine): verdict 'unreviewed' — artefakt NIE przechodzi
    review i czeka na człowieka (bramka wzorców nadal obowiązuje).
    """
    if review_engine is None or not produced_text.strip():
        return {"reviewer": "none", "verdict": "unreviewed", "notes": "brak engine review — czeka na review człowieka"}
    prompt = "\n".join([
        "# Review produkcji słabego modelu (rój Straży Przyszłości)",
        f"Zadanie: {task.title}",
        f"Kontekst: {(task.context or '')[:300]}",
        "",
        "Produkcja do sprawdzenia:",
        produced_text[:6000],
        "",
        "Oceń: (1) czy produkcja spełnia zadanie, (2) błędy/braki, (3) co poprawić.",
        'Odpowiedz WYŁĄCZNIE JSON: {"verdict": "pass"|"needs_fixes"|"fail", "notes": "2-4 zdania"}',
    ])
    result = review_engine.complete({"kind": "review", "privacy": "public", "task_id": f"review_{task.task_id}"}, review_alias, prompt)
    if not result.get("ok"):
        return {"reviewer": "none", "verdict": "unreviewed", "notes": f"review engine niedostepny: {result.get('error_class', '?')}"}
    raw = str(result.get("output", "")).strip()
    try:
        start, end = raw.find("{"), raw.rfind("}")
        parsed = json.loads(raw[start:end + 1])
        verdict = parsed.get("verdict") if parsed.get("verdict") in {"pass", "needs_fixes", "fail"} else "unreviewed"
        return {"reviewer": result.get("model_id", review_alias), "verdict": verdict, "notes": str(parsed.get("notes", ""))[:400]}
    except (ValueError, TypeError, AttributeError):
        return {"reviewer": result.get("model_id", review_alias), "verdict": "unreviewed", "notes": "review: nieparsowalna odpowiedź"}


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
    sources = [_parse_handoff_tasks(docs_dir), _parse_proposal_tasks(state_dir), _parse_targets()]
    tasks = [task for row in zip_longest(*sources) for task in row if task is not None]
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
    decision = core.decide("parallel_mode", list(scores), scores, default_option="single", context={"backlog": backlog, "critical": critical})
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


def generate_llm_strategy(tasks: list[EvolutionTask], strategy_engine: Any | None) -> tuple[dict[str, Any], list[EvolutionTask]]:
    """KROK 1 (dyrektywa operatora): STRATEGIE tworzy LLM na darmowych modelach.

    LLM dostaje surowe zadania z backlogu i produkuje 'strategy brief':
    priorytety, podejście, hinty klas modeli ORAZ DEKOMPOZYCJĘ najważniejszych
    zadań na konkretne PODZADANIA (atomizacja — świeży materiał co rundę,
    żeby ewolucja non-stop nie kręciła kółka na tych samych wpisach).
    Offline (brak engine): strategia deterministyczna, bez podzadań.
    """
    known_ids = {t.task_id for t in tasks}
    fallback_strategy = {
        "source": "deterministic_fallback",
        "brief": "Kolejnosc wejsciowa zadan; brak rankingu LLM (offline).",
        "priorities": [t.task_id for t in tasks],
        "model_hints": {t.task_id: "auto" for t in tasks},
    }
    if strategy_engine is None or not tasks:
        return fallback_strategy, []
    listing = "\n".join(f"- [{t.task_id}] {t.title} (źródło: {t.source})" for t in tasks)
    prompt = "\n".join([
        "# Zadanie: strategia ewolucji repo dla roju Straży Przyszłości (suggest-only)",
        "Poniżej surowe zadania z backlogu roju. Utwórz 'strategy brief' WYŁĄCZNIE jako JSON:",
        '{"brief": str, "priorities": [task_id...], "model_hints": {task_id: "fast"|"smart"},',
        ' "subtasks": [{"task_id": "unikalne-id-podzadania", "title": "konkretne podzadanie", "context": "jak wykonać", "parent": "task_id"}]}',
        "Priorytety = kolejność realizacji. Podzadania = dekompozycja najważniejszych zadań",
        "na 2-4 konkretne, wykonalne kawałki (atomizacja procesów). Maks. 6 podzadań.",
        "",
        "Zadania:",
        listing,
    ])
    result = strategy_engine.complete({"kind": "reason", "privacy": "public", "task_id": "evolution_strategy"}, "auto", prompt)
    if not result.get("ok"):
        fallback_strategy["source"] = f"llm_unavailable:{result.get('error_class', 'unknown')}"
        return fallback_strategy, []
    raw = str(result.get("output", "")).strip()
    try:
        start, end = raw.find("{"), raw.rfind("}")
        parsed = json.loads(raw[start:end + 1])
        strategy = {
            "source": f"llm:{result.get('model_id', 'auto')}",
            "brief": str(parsed.get("brief", ""))[:600],
            "priorities": [p for p in parsed.get("priorities", []) if p in known_ids],
            "model_hints": {k: v for k, v in parsed.get("model_hints", {}).items() if k in known_ids},
        }
        subtasks: list[EvolutionTask] = []
        seen_ids: set[str] = set()
        for sub in parsed.get("subtasks", [])[:6]:
            if not isinstance(sub, dict):
                continue
            sub_id = str(sub.get("task_id", "")).strip()
            title = str(sub.get("title", "")).strip()
            if not sub_id or sub_id in known_ids or sub_id in seen_ids or not title:
                continue
            seen_ids.add(sub_id)
            subtasks.append(EvolutionTask(
                task_id=sub_id,
                title=title[:160],
                source=f"llm_strategy:subtask_of:{sub.get('parent', '?')}",
                context=str(sub.get("context", ""))[:400],
            ))
        return strategy, subtasks
    except (ValueError, TypeError, AttributeError):
        fallback_strategy["source"] = "llm_bad_json"
        return fallback_strategy, []


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
    """Jeden przebieg ewolucji repo: zadania → (mock|Hermes) → bramka → kolejka.

    Tryb wide: zadania wykonują się RÓWNOLEGLE, każde pasmo na INNYM modelu
    (round-robin po darmowym katalogu OmniRoute — limity RPM rozkładają się
    per model, np. NIM 40 RPM osobno na model). Limit pasm: max_lanes
    (konfigurowalne, domyślnie 6).
    """

    def __init__(self, state_dir: Path, docs_dir: Path, repo_root: Path, worker: HermesWorker | None = None, lane_models: list[str] | None = None, decision_core=None, strategy_engine: Any | None = None, max_lanes: int = 6, should_stop=None) -> None:
        self.state_dir = state_dir
        self.docs_dir = docs_dir
        self.repo_root = repo_root
        self.worker = worker
        self.lane_models = lane_models or []
        self.decision_core = decision_core
        self.strategy_engine = strategy_engine
        self.max_lanes = max_lanes
        self.should_stop = should_stop or (lambda: False)
        self.gate = SecurityGate()
        self.queue_dir = state_dir / "evolution_queue"
        self.strategy: dict[str, Any] = {}

    @staticmethod
    def fingerprint(task):
        content = {"title": " ".join(task.title.split()), "context": task.context, "constraints": task.constraints}
        return hashlib.sha256(json.dumps(content, sort_keys=True, ensure_ascii=False).encode()).hexdigest()

    @contextmanager
    def index(self):
        self.state_dir.mkdir(parents=True, exist_ok=True)
        path = self.state_dir / "evolution_index.json"
        with (self.state_dir / "evolution_index.lock").open("a+") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            data = json.loads(path.read_text()) if path.exists() else {}
            yield data
            temp = path.with_suffix(".tmp")
            temp.write_text(json.dumps(data, indent=2) + "\n")
            os.replace(temp, path)


    def run(self, max_tasks: int = 4, parallel_mode: str = "single") -> list[dict[str, Any]]:
        if self.should_stop():
            return []
        tasks = collect_evolution_tasks(self.state_dir, self.docs_dir, max_tasks=100)
        with self.index() as index:
            tasks = [t for t in tasks if self.fingerprint(t) not in index]
        from selfopt_chain.swarm import Demand, charter_check, load_charter
        tasks = [t for t in tasks if charter_check([Demand(t.task_id, t.title + " " + (t.context or ""), [], t.source)], load_charter())["ok"]]
        if not tasks:
            return []
        self.strategy, subtasks = generate_llm_strategy(tasks, self.strategy_engine)
        order = {task_id: i for i, task_id in enumerate(self.strategy.get("priorities", []))}
        tasks.sort(key=lambda t: order.get(t.task_id, len(order)))
        # Occupied numbered tasks remain with their owner, even if mentioned
        # in an old handoff. Check all local worktrees when available.
        try:
            from tools.agent_claims import collect
            active_tasks = {c["task"] for c in collect(self.repo_root, True).values()}
            tasks = [t for t in tasks if not any(re.match(rf"{task}(?![0-9])", t.title) for task in active_tasks)]
        except (OSError, ValueError, __import__("subprocess").CalledProcessError):
            pass
        tasks = tasks[:max_tasks]
        if subtasks:
            tasks = (tasks[:1] + [s for s in subtasks if s.task_id not in {t.task_id for t in tasks}])[:max_tasks]
        armed = self.worker is not None and HermesWorker.enabled()
        if armed and parallel_mode == "wide" and len(tasks) > 1:
            from concurrent.futures import ThreadPoolExecutor

            lanes = min(self.max_lanes, len(tasks))
            with ThreadPoolExecutor(max_workers=lanes) as pool:
                futures = [
                    pool.submit(self._run_task, task, parallel_mode, self._lane_model(i, task))
                    for i, task in enumerate(tasks)
                ]
                return [future.result() for future in futures]
        return [self._run_task(task, parallel_mode, self._lane_model(i, task)) for i, task in enumerate(tasks) if not self.should_stop()]

    def _lane_model(self, lane_index: int, task: EvolutionTask | None = None) -> str:
        """Model pasma: basal wybiera odpowiedni LLM; bez rdzenia/strategy — round-robin."""
        if self.decision_core is not None and task is not None and self.lane_models:
            hint = (self.strategy.get("model_hints", {}) or {}).get(task.task_id, "")
            scores = {m: (1.5 if (hint == "fast" and "fast" in m) or (hint == "smart" and "smart" in m) else 0.5) for m in self.lane_models}
            decision = self.decision_core.decide("model_selection", list(self.lane_models), scores, default_option=self.lane_models[lane_index % len(self.lane_models)], context={"task_id": task.task_id, "strategy_hint": hint})
            return decision["final"]
        if not self.lane_models:
            return "auto"
        return self.lane_models[lane_index % len(self.lane_models)]

    def _run_task(self, task: EvolutionTask, parallel_mode: str, model_alias: str | None) -> dict[str, Any]:
        fp = self.fingerprint(task)
        with self.index() as index:
            if fp in index or self.should_stop():
                return {"task_id": task.task_id, "status": "duplicate_or_stopped", "auto_applied": False}
            index[fp] = {"status": "running", "task_id": task.task_id, "started": time.time()}
        run_id = f"task_{fp[:16]}_{uuid.uuid4().hex[:6]}"
        out_dir = self.queue_dir / run_id
        out_dir.mkdir(parents=True, exist_ok=True)
        receipt: dict[str, Any] = {
            "run_id": run_id,
            "task_id": task.task_id,
            "title": task.title,
            "source": task.source,
            "parallel_mode": parallel_mode,
            "model_alias": model_alias,
            "executor": "mock",
            "gate_ok": None,
            "quarantined": False,
            "proposal_path": None,
        }
        if self.worker is not None and HermesWorker.enabled():
            receipt["executor"] = "hermes"
            query = build_task_query(task, self.repo_root)
            hermes_receipt = self.worker.run_isolated(query, model_alias=model_alias)
            receipt["hermes_run_id"] = hermes_receipt.get("run_id")
            receipt["hermes_executed"] = hermes_receipt.get("executed")
            receipt["hermes_exit_code"] = hermes_receipt.get("exit_code")
            report = hermes_receipt.get("security_gate") or {"ok": False, "violations": [{"rule": "hermes_not_executed"}], "licenses_review": []}
            (out_dir / "hermes_receipt.json").write_text(json.dumps(hermes_receipt, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
            quarantine = Path(hermes_receipt.get("quarantine_dir", out_dir))
            pieces = []
            total = 0
            for produced in sorted(quarantine.rglob("*")):
                if produced.is_file() and not produced.is_symlink() and produced.name not in {"output.json", "task.md", "hermes_receipt.json"}:
                    content = produced.read_text(encoding="utf-8", errors="replace")
                    total += len(content)
                    pieces.append(f"# {produced.relative_to(quarantine)}\n{content}")
            produced_text = "\n".join(pieces) if total <= 5500 else ""
            review = review_by_strong_model(task, produced_text, self.strategy_engine)
            receipt["review"] = review
            (out_dir / "review.json").write_text(json.dumps(review, ensure_ascii=False, indent=2), encoding="utf-8")
        else:
            proposal = render_mock_proposal(task, parallel_mode, {"ok": True, "violations": [], "licenses_review": []})
            proposal_path = out_dir / "PROPOSAL.md"
            proposal_path.write_text(proposal, encoding="utf-8")
            report = self.gate.inspect_code(proposal)
            receipt["proposal_path"] = str(proposal_path)
            receipt["review"] = {"reviewer": "none", "verdict": "unreviewed", "notes": "mock-lane: czeka na review człowieka"}
        (out_dir / "gate_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        receipt["security_ok"] = bool(report.get("ok"))
        receipt["execution_ok"] = receipt.get("executor") == "hermes" and receipt.get("hermes_exit_code") == 0
        receipt["review_ok"] = (receipt.get("review") or {}).get("verdict") == "pass"
        receipt["validation_ok"] = bool((hermes_receipt.get("validation") or {}).get("ok")) if receipt["executor"] == "hermes" else False
        receipt["gate_ok"] = receipt["security_ok"] and receipt["execution_ok"] and receipt["review_ok"] and receipt["validation_ok"]
        receipt["ready_for_human_review"] = receipt["gate_ok"]
        receipt["status"] = "ready" if receipt["gate_ok"] else "simulated" if receipt["executor"] == "mock" else "needs_fixes"
        receipt["quarantined"] = bool(report.get("quarantine_required"))
        receipt["auto_applied"] = False
        receipt["fingerprint"] = fp
        (out_dir / "evolution_receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
        with self.index() as index:
            index[fp] = {"status": receipt["status"], "run_id": run_id, "task_id": task.task_id}
        return receipt
