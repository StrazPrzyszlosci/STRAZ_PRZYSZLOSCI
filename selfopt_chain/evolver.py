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
        f"Kontekst: {(task.context or '')[:2000]}",
        "",
        "Produkcja do sprawdzenia:",
        produced_text,
        "",
        "Oceń: (1) czy produkcja spełnia zadanie, (2) błędy/braki, (3) co poprawić.",
        'Odpowiedz WYŁĄCZNIE JSON: {"verdict": "pass"|"needs_fixes"|"fail", "notes": "2-4 zdania"}',
    ])
    result = review_engine.complete({"kind": "review", "privacy": "public", "task_id": f"review_{task.task_id}",
        "max_tokens": 8192, "response_format": {"type": "json_object"},
        "system_prompt": "Return only a JSON object with verdict and notes. No tools are available; review the supplied material."}, review_alias, prompt)
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
    input_refs: list[str] = field(default_factory=list)
    runtime_refs: list[str] = field(default_factory=list)
    allowed_paths: list[str] = field(default_factory=list)
    acceptance_ref: str | None = None
    kind: str = "proposal"
    priority: int = 0
    focus_symbols: dict[str, list[str]] = field(default_factory=dict)


def _parse_handoff_tasks(docs_dir: Path, limit: int = 5) -> list[EvolutionTask]:
    """Read the newest actionable handoff, including continued numbered items."""
    handoffs = sorted(docs_dir.glob("HANDOFF_DLA_NASTEPNEGO_AGENTA_*.md"), reverse=True)
    for handoff in handoffs:
        text = handoff.read_text(encoding="utf-8")
        section = re.search(r"^##[^\n]*(?:Następne zadania|Nastepne zadania|Otwarte etapy|Następne kroki)[^\n]*\n(.*?)(?=^## |\Z)", text, re.M | re.S)
        if not section:
            continue
        matches = list(re.finditer(r"^\d+\.\s+(.*?)(?=^\d+\.\s|\Z)", section[1], re.M | re.S))
        tasks = []
        for i, match in enumerate(matches[:limit]):
            full = " ".join(match[1].replace("**", "").split())
            tasks.append(EvolutionTask(task_id=f"handoff_{handoff.stem}_{i}", title=full[:240],
                        source=f"handoff:{handoff.name}", context=full,
                        input_refs=["selfopt_chain/README.md"]))
        if tasks:
            return tasks
    return []


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
            input_refs=t.get("input_refs", []), runtime_refs=t.get("runtime_refs", []),
            allowed_paths=t.get("allowed_paths", []), acceptance_ref=t.get("acceptance_ref"),
            kind=t.get("kind", "proposal"), priority=int(t.get("priority", 0)), focus_symbols=t.get("focus_symbols", {}),
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


def generate_llm_strategy(tasks: list[EvolutionTask], strategy_engine: Any | None, hardware_context=None) -> tuple[dict[str, Any], list[EvolutionTask]]:
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
    listing = "\n".join(f"- [{t.task_id}] {t.title} (źródło: {t.source}; priorytet: {t.priority}; typ: {t.kind})" for t in tasks)
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
        'Aktualny sprzęt i ograniczenia hosta: ' + json.dumps(hardware_context or {}, ensure_ascii=False),
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
    """Prepare inputs, lease a task, produce, independently validate and retain a candidate."""

    def __init__(self, state_dir, docs_dir, repo_root, worker=None, lane_models=None,
                 decision_core=None, strategy_engine=None, max_lanes=6, should_stop=None,
                 models=None, retry_seconds=60, max_attempts=3, clock=time.time):
        from selfopt_chain.evolution_store import EvolutionStore
        self.state_dir, self.docs_dir, self.repo_root = Path(state_dir), Path(docs_dir), Path(repo_root)
        self.worker, self.lane_models = worker, lane_models or []
        self.decision_core, self.strategy_engine = decision_core, strategy_engine
        self.max_lanes, self.should_stop = max_lanes, should_stop or (lambda: False)
        self.models = {m["model_id"]: m for m in (models or getattr(worker, "models", None) or [])}
        self.gate, self.queue_dir = SecurityGate(), self.state_dir / "evolution_queue"
        self.store = EvolutionStore(self.state_dir, clock=clock, retry_seconds=retry_seconds, max_attempts=max_attempts)
        self.strategy, self.inputs, self.blocked = {}, {}, []

    @staticmethod
    def fingerprint(task):
        content = {"title": " ".join(task.title.split()), "context": task.context, "constraints": task.constraints}
        return hashlib.sha256(json.dumps(content, sort_keys=True, ensure_ascii=False).encode()).hexdigest()

    def index(self):
        return self.store.transaction()

    def _worker_enabled(self):
        return self.worker is not None and getattr(self.worker, "enabled", HermesWorker.enabled)()

    def _acceptance_passes(self, task) -> bool:
        """Uruchamia niezależny kontrakt odbioru na obecnym drzewie (bez network).

        Cel z przechodzącym akceptatorem jest już spełniony — nie jest kolejkowany
        (T62: nie produkuj gotowej wersji ponownie). Błąd uruchomienia = brak
        przesłanki do pominięcia (cel zostaje w kolejce).
        """
        import subprocess
        import sys
        script = self.repo_root / task.acceptance_ref
        if not script.is_file():
            return False
        env = {k: v for k, v in os.environ.items()
               if k not in {"SELFOPT_NETWORK", "SELFOPT_HERMES", "SELFOPT_BASAL_URL"}}
        env.update({"SELFOPT_NETWORK": "0", "SELFOPT_HERMES": "0", "SELFOPT_BASAL_URL": ""})
        try:
            completed = subprocess.run([sys.executable, str(script)], cwd=self.repo_root,
                                       env=env, capture_output=True, text=True, timeout=120)
        except (OSError, subprocess.TimeoutExpired):
            return False
        return completed.returncode == 0

    def pending(self):
        from selfopt_chain.evolution_inputs import prepare_inputs, InputUnavailable
        from selfopt_chain.swarm import Demand, charter_check, load_charter
        self.blocked, result = [], []
        try:
            from tools.agent_claims import collect
            active = {c["task"] for c in collect(self.repo_root, True).values()}
        except (OSError, ValueError, __import__("subprocess").CalledProcessError):
            active = set()
        for task in collect_evolution_tasks(self.state_dir, self.docs_dir, 100):
            fp = self.fingerprint(task)
            if any(re.match(rf"{number}(?![0-9])", task.title) for number in active):
                continue
            if not charter_check([Demand(task.task_id, task.title + " " + task.context, [], task.source)], load_charter())["ok"]:
                continue
            try:
                bundle = prepare_inputs(task, self.repo_root, self.state_dir, self.store.feedback(fp))
            except (InputUnavailable, ValueError, OSError) as error:
                self.store.block(fp, str(error))
                self.blocked.append({"task_id": task.task_id, "reason": str(error)})
                continue
            # T62: akceptator sprawdzany PRZED kolejkowaniem — cel, którego kontrakt
            # JUŻ przechodzi na obecnym drzewie, jest gotowy (nie produkuj ponownie).
            if task.acceptance_ref and self._acceptance_passes(task):
                self.blocked.append({"task_id": task.task_id, "reason": "acceptance_already_passing",
                                     "kind": "ready"})
                continue
            if self._worker_enabled() and self.models and self.lane_models:
                from selfopt_chain.model_selection import shortlist_models
                selection = shortlist_models([self.models[mid] for mid in self.lane_models if mid in self.models],
                    kind='code_draft' if task.kind == 'patch' else 'reason',
                    ledger=getattr(self.worker, 'ledger', None), requires_tools=task.kind != 'patch')
                if not selection['candidates']:
                    self.blocked.append({'task_id': task.task_id, 'reason': 'no_eligible_profile', 'kind': 'models'})
                    continue
            if self.store.eligible(fp, bundle["input_hash"], promote_simulated=self._worker_enabled()):
                self.inputs[fp] = bundle
                result.append(task)
        return result

    def run(self, max_tasks=4, parallel_mode="single", tasks=None):
        if self.should_stop():
            return []
        tasks = self.pending() if tasks is None else tasks
        if not tasks:
            return []
        self.strategy, subtasks = generate_llm_strategy(tasks, self.strategy_engine,
                                                       getattr(self.decision_core, 'hardware_context', {}))
        # A decomposition is a proposal; only a complete task contract may execute.
        self.strategy["proposed_subtasks"] = [{"title": t.title, "parent_source": t.source} for t in subtasks]
        order = {task_id: i for i, task_id in enumerate(self.strategy.get("priorities", []))}
        tasks = sorted(tasks, key=lambda t: (-t.priority, order.get(t.task_id, len(order))))[:max_tasks]
        self.state_dir.mkdir(parents=True, exist_ok=True)
        (self.state_dir / "last_evolution_plan.json").write_text(json.dumps({"strategy": self.strategy,
             "selected": [t.task_id for t in tasks], "blocked": self.blocked}, ensure_ascii=False, indent=2))
        armed = self._worker_enabled()
        if armed and parallel_mode == "wide" and len(tasks) > 1:
            from concurrent.futures import ThreadPoolExecutor
            # Patches with overlapping declared scope must stay sequential.
            scopes = [set(t.allowed_paths) for t in tasks]
            from tools.agent_claims import overlap
            disjoint = all(not any(overlap(x, y) for x in a for y in b) for i, a in enumerate(scopes) for b in scopes[i + 1:])
            if disjoint:
                with ThreadPoolExecutor(max_workers=min(self.max_lanes, len(tasks))) as pool:
                    futures = [pool.submit(self._run_task, task, parallel_mode, self._lane_model(i, task)) for i, task in enumerate(tasks)]
                    return [f.result() for f in futures]
        return [self._run_task(task, parallel_mode, self._lane_model(i, task)) for i, task in enumerate(tasks) if not self.should_stop()]

    def _lane_model(self, lane_index, task=None):
        if not self.lane_models:
            return None
        from selfopt_chain.model_selection import shortlist_models
        hint = (self.strategy.get("model_hints") or {}).get(task.task_id, "") if task else ""
        ledger = getattr(self.worker, 'ledger', None)
        bundle = self.inputs.get(self.fingerprint(task), {}) if task else {}
        sources = bundle.get('source_excerpts') or bundle.get('input_files', {})
        estimated_context = (sum(len(v.encode()) for v in sources.values()) + len((bundle.get('acceptance') or '').encode())) // 2
        if sources and task and task.kind == 'patch':
            estimated_context += 8192
        selection = shortlist_models([self.models[mid] for mid in self.lane_models if mid in self.models],
            kind='code_draft' if task and task.kind == 'patch' else 'reason', ledger=ledger, hint=hint,
            minimum_context_tokens=estimated_context,
            requires_tools=self._worker_enabled() and getattr(self.worker, 'executor_name', 'hermes') == 'hermes')
        candidates, scores, details = selection['candidates'], selection['scores'], selection['details']
        self.state_dir.mkdir(parents=True, exist_ok=True)
        (self.state_dir / 'last_model_shortlist.json').write_text(json.dumps(selection, ensure_ascii=False, indent=2))
        if not candidates:
            return None
        default = max(scores, key=scores.get)
        if self.decision_core and task:
            decision = self.decision_core.decide("model_selection", candidates, scores, default_option=default,
                       context={"task_id": task.task_id, "strategy_hint": hint, "model_characteristics": details})
            return decision["final"] if decision["final"] in scores else default
        return default

    def _run_task(self, task, parallel_mode, model_alias):
        from selfopt_chain.evolution_inputs import task_prompt
        fp = self.fingerprint(task)
        bundle = {**self.inputs[fp], 'hardware_context': getattr(self.decision_core, 'hardware_context', {})}
        prior = self.store.snapshot().get(fp, {})
        prior_path = prior.get("receipt_path")
        if prior_path and prior.get("input_hash") == bundle["input_hash"] and Path(prior_path).is_file():
            previous = json.loads(Path(prior_path).read_text())
            if previous.get("validation_ok") and previous.get("review", {}).get("verdict") == "unreviewed":
                return self.revalidate(prior_path)
        if self.worker is not None and getattr(self.worker, "ledger", None) is not None and model_alias is None:
            return {"task_id": task.task_id, "status": "waiting_models", "error": "no_eligible_profile", "auto_applied": False}
        if self.worker is not None and getattr(self.worker, "ledger", None) is not None and not self.worker.ledger.can_use(model_alias):
            return {"task_id": task.task_id, "status": "waiting_budget", "auto_applied": False}
        lease = self.store.acquire(fp, task.task_id, bundle["input_hash"], promote_simulated=self._worker_enabled())
        if not lease:
            return {"task_id": task.task_id, "status": "duplicate_or_waiting", "auto_applied": False}
        run_id = f"task_{fp[:16]}_{lease[:8]}"
        out_dir = self.queue_dir / run_id
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "input_manifest.json").write_text(json.dumps(bundle, ensure_ascii=False, indent=2))
        receipt = {"run_id": run_id, "task_id": task.task_id, "title": task.title, "source": task.source,
                   "parallel_mode": parallel_mode, "model_alias": model_alias, "executor": "mock",
                   "fingerprint": fp, "input_hash": bundle["input_hash"], "proposal_path": None,
                   "auto_applied": False, "receipt_path": str(out_dir / "evolution_receipt.json")}
        try:
            if self._worker_enabled():
                receipt["executor"] = getattr(self.worker, "executor_name", "hermes")
                produced = self.worker.run_isolated(task_prompt(bundle), model_alias=model_alias, input_bundle=bundle)
                (out_dir / "hermes_receipt.json").write_text(json.dumps(produced, ensure_ascii=False, indent=2))
                receipt.update(hermes_run_id=produced.get("run_id"), hermes_executed=produced.get("executed"),
                               worker_exit_code=produced.get("exit_code"), hermes_exit_code=produced.get("exit_code") if receipt["executor"] == "hermes" else None, validation=produced.get("validation"),
                               security_ok=bool((produced.get("security_gate") or {}).get("ok")),
                               execution_ok=produced.get("executed") is True and produced.get("exit_code") == 0)
                validation = produced.get("validation") or {}
                texts = []
                output_root = Path(produced.get("quarantine_dir", out_dir))
                for name in ["PROPOSAL.md", "changes.patch"]:
                    path = output_root / name
                    if path.is_file() and not path.is_symlink():
                        texts.append(f"# {name}\n{path.read_text()}")
                        if name == "PROPOSAL.md":
                            receipt["proposal_path"] = str(path)
                text = "\n".join(texts)
                if len(text) > 16000:
                    receipt["error"] = "review_context_limit"
                    text = ""
                # Do not spend a review call on missing, unsafe or invalid production.
                receipt["review"] = review_by_strong_model(task, text + "\nValidation: " + json.dumps(validation), self.strategy_engine) if text and receipt["security_ok"] and validation.get("ok") else {"verdict": "unreviewed", "notes": "artifact not validated"}
                receipt["validation_ok"] = bool(validation.get("ok"))
                receipt["error"] = produced.get("error") or produced.get("stop_reason") or receipt.get("error")
                report = produced.get("security_gate") or {"ok": False}
            else:
                proposal_path = out_dir / "PROPOSAL.md"
                proposal_path.write_text(render_mock_proposal(task, parallel_mode, {"ok": True}))
                receipt.update(proposal_path=str(proposal_path), execution_ok=False, validation_ok=False,
                               security_ok=True, review={"verdict": "unreviewed", "notes": "simulated"})
                report = self.gate.inspect_code(proposal_path.read_text())
            receipt["review_ok"] = receipt["review"].get("verdict") == "pass"
            receipt["gate_ok"] = all(receipt.get(k) for k in ["execution_ok", "validation_ok", "security_ok", "review_ok"])
            receipt["ready_for_human_review"] = receipt["gate_ok"]
            receipt["status"] = "ready" if receipt["gate_ok"] else "simulated" if receipt["executor"] == "mock" else "needs_fixes"
            if receipt["validation_ok"] and receipt["execution_ok"] and receipt["security_ok"] and receipt["review"].get("verdict") == "unreviewed":
                receipt["status"] = "waiting_review"
            if receipt.get("error") in {"connection_error", "http_error", "bad_response"}:
                receipt["status"] = "waiting_provider"
            elif receipt.get("error") == "quota_exhausted":
                receipt["status"] = "waiting_budget"
            receipt["quarantined"] = not receipt["gate_ok"]
            (out_dir / "gate_report.json").write_text(json.dumps(report, indent=2))
            if receipt["gate_ok"]:
                self._archive(receipt)
        except Exception as error:
            receipt.update(status="needs_fixes", error=type(error).__name__, gate_ok=False, ready_for_human_review=False,
                           security_ok=False, validation_ok=False, execution_ok=False, review_ok=False,
                           review={"verdict": "unreviewed", "notes": "controller captured failure"}, validation={"ok": False, "error": type(error).__name__})
        return self._record(fp, lease, task, receipt)

    def _archive(self, receipt):
        import shutil
        archive = self.state_dir / "candidate_archive" / receipt["fingerprint"] / receipt["run_id"]
        archive.mkdir(parents=True, exist_ok=True)
        for name in ["PROPOSAL.md", "changes.patch"]:
            source = Path(receipt["proposal_path"]).parent / name
            if source.is_file():
                shutil.copyfile(source, archive / name)
        receipt["archive_path"] = str(archive)
        (archive / "candidate.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2))

    def _record(self, fp, lease, task, receipt):
        Path(receipt["receipt_path"]).write_text(json.dumps(receipt, ensure_ascii=False, indent=2))
        if receipt.get("gate_ok") and task.kind == "patch":
            try:
                import subprocess
                from selfopt_chain.evolution_publication import request_publication
                remote = subprocess.check_output(["git", "-C", str(self.repo_root), "remote", "get-url", "origin"], text=True).strip()
                match = re.search(r"github\.com[/:]([^/\s]+/[^/\s]+?)(?:\.git)?$", remote)
                if match:
                    receipt["publication_request"] = str(request_publication(self.state_dir, Path(receipt["receipt_path"]), match[1]))
            except (OSError, ValueError, subprocess.SubprocessError) as error:
                receipt["publication_error"] = type(error).__name__
            Path(receipt["receipt_path"]).write_text(json.dumps(receipt, ensure_ascii=False, indent=2))
        self.store.finish(fp, lease, receipt)
        return receipt


    def revalidate(self, receipt_path):
        """Recover controller validation or provider review without regenerating model code."""
        from selfopt_chain.evolution_validation import validate_patch
        from selfopt_chain.evolution_inputs import prepare_inputs
        path = Path(receipt_path).resolve()
        if not path.is_relative_to(self.queue_dir.resolve()):
            raise ValueError("receipt_outside_queue")
        old = json.loads(path.read_text())
        if not old.get("execution_ok") or not old.get("security_ok") or old.get("executor") == "mock":
            raise ValueError("production_not_revalidatable")
        task = next(t for t in collect_evolution_tasks(self.state_dir, self.docs_dir, 100) if t.task_id == old["task_id"])
        bundle = prepare_inputs(task, self.repo_root, self.state_dir, self.store.feedback(old["fingerprint"]))
        if bundle["input_hash"] != old["input_hash"]:
            raise ValueError("inputs_changed_require_new_generation")
        lease = self.store.acquire(old["fingerprint"], task.task_id, bundle["input_hash"])
        if not lease:
            return {"task_id":task.task_id,"status":"waiting_retry"}
        run_id = "revalidate_" + lease[:12]
        output = self.queue_dir / run_id
        output.mkdir(parents=True)
        (output / "input_manifest.json").write_text(json.dumps(bundle, ensure_ascii=False, indent=2))
        worker = json.loads((path.parent / "hermes_receipt.json").read_text())
        artifact = Path(worker["quarantine_dir"])
        snapshot = self.state_dir / "repo_snapshots" / worker["source_commit"]
        receipt = {**old, "run_id":run_id,"receipt_path":str(output / "evolution_receipt.json"),
                   "revalidated_from":str(path),"producer_rerun":False,"auto_applied":False,"error":None}
        receipt.pop("publication_request",None)
        receipt.pop("publication_error",None)
        validation = validate_patch(artifact, snapshot, bundle, self.state_dir / "validations" / run_id)
        receipt["validation"], receipt["validation_ok"] = validation, bool(validation.get("ok"))
        text = "\n".join((artifact / name).read_text() for name in ["PROPOSAL.md","changes.patch"])
        gate = self.gate.inspect_code(text)
        receipt["security_ok"] = gate["ok"]
        receipt["review"] = review_by_strong_model(task, text + "\nChecks: " + json.dumps(validation.get("checks")), self.strategy_engine) if validation.get("ok") and gate["ok"] else {"verdict":"unreviewed"}
        receipt["review_ok"] = receipt["review"].get("verdict") == "pass"
        receipt["gate_ok"] = all(receipt.get(k) for k in ["execution_ok","security_ok","validation_ok","review_ok"])
        receipt["ready_for_human_review"] = receipt["gate_ok"]
        receipt["quarantined"] = not receipt["gate_ok"]
        receipt["status"] = "ready" if receipt["gate_ok"] else "waiting_review" if receipt["validation_ok"] and receipt["security_ok"] and receipt["review"].get("verdict") == "unreviewed" else "needs_fixes"
        worker["original_api_calls"] = worker.get("api_calls",{})
        worker["api_calls"] = {}
        worker["validation"] = validation
        worker["revalidated_from"] = str(path.parent / "hermes_receipt.json")
        (output / "hermes_receipt.json").write_text(json.dumps(worker, ensure_ascii=False, indent=2))
        (output / "gate_report.json").write_text(json.dumps(gate, indent=2))
        if receipt["gate_ok"]:
            self._archive(receipt)
        return self._record(old["fingerprint"], lease, task, receipt)
