#!/usr/bin/env python3
"""Warstwa roju z rdzeniem decyzyjnym basal (selfopt_chain, T50).

Wizja operatora (2026-10-21): wszystkie połączone procesy repo działają jak
RÓJ realizujący usługi dla ludności. Na obwodach roju małe modele decyzyjne
("ministerownicy" w stylu BASAL — tanie, szybkie, małe zużycie zasobów)
podejmują BARDZO WIELE decyzji: przydział dostępnego sprzętu (telefon, płytka
ESP, węzeł selfhost) do otwartych zapotrzebowań, wybór trybu wykonania
(algorytm napisany pod sprzęt vs model on-device vs łańcuch LLM w chmurze),
dobór zadań cyklu i strategię zarządzania (inspiracja CEZAR: kolejka, warianty,
load-balance, autonomia). LLM pozostaje warstwą STRATEGII (procdev, drafts).

Semantyka decyzji zaadaptowana 1:1 z repozytoria basal (HYC, router.py):
- choice over options -> probability distribution + ranking (fallback order),
- kalibrowany confidence (temperatury per typ pytania i bucket liczby opcji,
  seed wg eksperymentalnego CALIBRATION.custom.json),
- confidence < floor -> deferred -> default/fallback (nic nie zgadujemy),
- każda decyzja ląduje w decisions.jsonl (format ready pod przyszłą
  kalibrację i pętlę GEPA, która już istnieje w selfopt_chain/optimizers.py).

Zero zależności, zero sieci (rdzeń wbudowany, deterministyczny); prawdziwy
basal-serve (Ollama) podpina się opcjonalnie przez SELFOPT_BASAL_URL.
Wszystko suggest-only: plan roju to artefakt do review, nie aktuation.
"""
from __future__ import annotations

import json
import re
import math
import time
import uuid
from pathlib import Path
from typing import Any, Callable

DEFAULT_CONFIDENCE_FLOOR = 0.55
TEMPERATURE_SEEDS: dict[str, dict[str, float]] = {
    "choice": {"small": 0.6639592783444488, "large": 1.7062550705226853, "default": 0.7711054127039705},
    "score": {"default": 1.9430638823072113},
}
TEMPERATURE_NOTE = (
    "seedy eksperymentalne z repozytorium basal (CALIBRATION.custom.json); "
    "docelowo dopasować własną kalibracją z decisions.jsonl"
)


def _bucket_for(count: int) -> str:
    return "small" if count <= 10 else "large"


def softmax_confidence(scores: dict[str, float], question_type: str = "choice", temperatures: dict[str, float] | None = None) -> tuple[dict[str, float], float]:
    """Rozkład prawdopodobieństw + confidence jak w rdzeniu basal.

    scores -> softmax(scores / T(question_type, n_options)); confidence = p(top).
    `temperatures` = kalibracja per typ pytania (CALIBRATION.selfopt.json);
    gdy brak — obowiązują seedy eksperymentalne.
    """
    if not scores:
        return {}, 0.0
    if temperatures is not None and question_type in temperatures:
        temperature = float(temperatures[question_type])
    else:
        temps = TEMPERATURE_SEEDS.get(question_type, TEMPERATURE_SEEDS["choice"])
        bucket = _bucket_for(len(scores))
        temperature = temps.get(bucket, temps.get("default", 0.77))
    values = list(scores.values())
    shift = max(values)
    exps = {k: math.exp(v / temperature - shift / temperature) for k, v in scores.items()}
    total = sum(exps.values())
    probabilities = {k: e / total for k, e in exps.items()}
    top = max(probabilities.values())
    return probabilities, round(top, 4)


class BasalDecisionCore:
    """Mały model decyzyjny roju: szybki, tani, deterministyczny (builtin).

    Opcjonalnie deleguje pytania do prawdziwego basal-serve (SELFOPT_BASAL_URL);
    wtedy jest tylko mostem, a decyzja liczy się tam. Log decyzji w formacie
    zgodnym z decisions.jsonl basala (pole group/question_type + context).
    """

    def __init__(self, decision_log: Path | None = None, confidence_floor: float = DEFAULT_CONFIDENCE_FLOOR, temperatures: dict[str, float] | None = None) -> None:
        self.decision_log = decision_log
        self.confidence_floor = confidence_floor
        self.temperatures = temperatures
        self.decisions: list[dict[str, Any]] = []
        self.remote_url: str | None = None
        import os

        self.remote_url = os.environ.get("SELFOPT_BASAL_URL") or None

    def decide(self, question_type: str, options: list[str], scores: dict[str, float], default_option: str | None = None, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Jedna decyzja basal: choice + confidence + defer + ranking + log.

        Przy SELFOPT_BASAL_URL decyzję liczy prawdziwy basal-serve (POST
        /v1/systemone); błąd połączenia/parsowania = spadek do rdzenia
        wbudowanego (engine zapisuje prawdę o tym, co się stało).
        """
        if not options:
            raise ValueError("decide: brak opcji")
        missing = [o for o in options if o not in scores]
        if missing:
            raise ValueError(f"decide: brak score dla opcji {missing}")
        engine = "builtin"
        probabilities, confidence = None, None
        remote_note = None
        if self.remote_url:
            remote = self._remote_decide(question_type, options, scores, context)
            if remote is not None:
                probabilities, confidence = remote
                engine = "basal-serve"
            else:
                remote_note = "basal-serve nieosiagalny/nieparsowalny; decyzja wbudowana"
        if probabilities is None:
            probabilities, confidence = softmax_confidence(scores, question_type, self.temperatures)
        if not probabilities or set(probabilities) != set(options) or not math.isfinite(confidence) or not 0 <= confidence <= 1 or any(not math.isfinite(v) or not 0 <= v <= 1 for v in probabilities.values()):
            probabilities, confidence = softmax_confidence(scores, question_type, self.temperatures)
            engine, remote_note = "builtin", "invalid remote candidates"
        ranking = sorted(probabilities.items(), key=lambda kv: -kv[1])
        chosen = ranking[0][0]
        default_option = default_option or options[0]
        if default_option not in scores:
            default_option = options[0]
        deferred = confidence < self.confidence_floor
        final = default_option if deferred else chosen
        decision = {
            "id": uuid.uuid4().hex[:8],
            "group": "swarm",
            "question_type": question_type,
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "options": list(options),
            "scores": {k: round(v, 4) for k, v in scores.items()},
            "probabilities": {k: round(v, 4) for k, v in ranking},
            "chosen": chosen,
            "confidence": confidence,
            "confidence_floor": self.confidence_floor,
            "deferred": deferred,
            "final": final,
            "default_option": default_option,
            "engine": engine,
            "remote_note": remote_note,
            "context": context or {},
        }
        self.decisions.append(decision)
        if self.decision_log is not None:
            self.decision_log.parent.mkdir(parents=True, exist_ok=True)
            with self.decision_log.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(decision, ensure_ascii=False) + "\n")
        return decision

    def select_model(self, routing_decision: dict[str, Any], task_kind: str) -> str:
        """basal wybiera LLM do zadania spośród kandydatów routera (dyrektywa operatora:
        LLM tworzy strategię; basal wybiera decyzje i odpowiedni LLM).

        Kandydaci w kolejności preferencji routera; score: wybór routera ma
        najwyższy priorytet, alternatywy malejąco. Defer = pozostaje wybór
        routera (basal nie zgadwa bez podstaw).
        """
        chosen = (routing_decision.get("chosen") or {}).get("model_id")
        alternatives = [a.get("model_id") for a in routing_decision.get("alternatives", []) if a.get("model_id")]
        options = [m for m in [chosen, *alternatives] if m]
        if not options or chosen is None:
            return chosen or ""
        if len(options) == 1:
            return options[0]
        scores = {m: (2.0 if m == chosen else round(0.5 - 0.05 * i, 2)) for i, m in enumerate(options[1:], start=0)}
        scores[chosen] = 2.0
        decision = self.decide(
            "model_selection", options, scores, default_option=chosen,
            context={"task_kind": task_kind, "required_tier": routing_decision.get("required_tier"), "router_policy": routing_decision.get("policy")},
        )
        return decision["final"]

    def _remote_decide(self, question_type: str, options: list[str], scores: dict[str, float], context: dict[str, Any] | None) -> tuple[dict[str, float], float] | None:
        """Decyzja z prawdziwego basal-serve (/v1/systemone); None = fallback.

        Kontrakt wg repozytorium basal (router.py build_request): state (obowiązkowe),
        lang, questions{name: {type: choice, instructions, criteria: {key: OPIS}}}.
        Wynik: answers{name: {choice, probabilities, confidence}}. Nasze heurystyczne
        score'e przekazujemy jako element opisu kryterium — basal czyta dowody, nie liczby.
        """
        import urllib.request

        instructions = REMOTE_INSTRUCTIONS.get(question_type, REMOTE_INSTRUCTIONS["default"])
        criteria = {}
        for option in options:
            score = scores.get(option, 0.0)
            criteria[option] = f"Opcja '{option}'. Heurystyczny score roju: {score:.3f} (im wyzej, tym lepsze dopasowanie wg strategii cyklu)."
        state = json.dumps({"pytanie": question_type, "kontekst_roju": context or {}, "opcje": options}, ensure_ascii=False)
        payload = {
            "state": state,
            "lang": "pl",
            "questions": {
                "decision": {
                    "type": "choice",
                    "instructions": instructions,
                    "criteria": criteria,
                }
            },
        }
        url = f"{self.remote_url.rstrip('/')}/v1/systemone"
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except Exception:
            return None
        answers = body.get("answers") if isinstance(body, dict) else None
        if not isinstance(answers, dict):
            return None
        answer = answers.get("decision") or next(iter(answers.values()), None)
        if not isinstance(answer, dict):
            return None
        probabilities = answer.get("probabilities")
        confidence = answer.get("confidence")
        if not isinstance(probabilities, dict) or not all(k in scores for k in probabilities) or not isinstance(confidence, (int, float)):
            return None
        return {k: float(v) for k, v in probabilities.items()}, round(float(confidence), 4)


class SwarmResource:
    """Zasób roju: model API, sprzęt (telefon/ESP/selfhost) albo człowiek-reviewer."""

    def __init__(self, resource_id: str, kind: str, label: str, capabilities: list[str], *, cost_class: str = "free_quota", energy_class: str = "external_provider", quality_tier: int = 1, speed_class: str = "medium", rpd_budget: int | None = None, rpd_used: int = 0, available: bool = True, origin: str = "registry") -> None:
        self.resource_id = resource_id
        self.kind = kind
        self.label = label
        self.capabilities = set(capabilities)
        self.cost_class = cost_class
        self.energy_class = energy_class
        self.quality_tier = quality_tier
        self.speed_class = speed_class
        self.rpd_budget = rpd_budget
        self.rpd_used = rpd_used
        self.available = available
        self.origin = origin

    @property
    def headroom(self) -> float:
        if self.rpd_budget is None:
            return 1.0
        return max(0.0, (self.rpd_budget - self.rpd_used) / self.rpd_budget)

    def to_dict(self) -> dict[str, Any]:
        return {
            "resource_id": self.resource_id,
            "kind": self.kind,
            "label": self.label,
            "capabilities": sorted(self.capabilities),
            "cost_class": self.cost_class,
            "energy_class": self.energy_class,
            "quality_tier": self.quality_tier,
            "speed_class": self.speed_class,
            "headroom": round(self.headroom, 3),
            "available": self.available,
            "origin": self.origin,
        }


def resources_from_models(models: list[dict], daily_calls: dict[str, int] | None = None) -> list[SwarmResource]:
    daily_calls = daily_calls or {}
    out: list[SwarmResource] = []
    for m in models:
        out.append(SwarmResource(
            f"model:{m['model_id']}", "model", m["model_id"], list(m.get("capabilities", [])),
            cost_class=m.get("cost_class", "free_quota"),
            energy_class="low_power_or_oze_preferred" if m.get("provider") == "selfhost_recovered_node" else "external_provider",
            quality_tier=m.get("quality_tier", 1),
            speed_class=m.get("speed_class", "medium"),
            rpd_budget=m.get("rpd_seed"),
            rpd_used=daily_calls.get(m["model_id"], 0),
            available=True,
            origin=f"registry:{m.get('provider')}",
        ))
    return out


HARDWARE_KINDS = {
    "old_smartphones": ("hardware:phone", "telefon (edge sensing/kamera)", ["vision", "sensing", "edge_compute"]),
    "router_boards": ("hardware:router", "płytka routerowa (mesh/LoRa)", ["mesh", "lora", "edge_compute"]),
    "selfhost_compute": ("hardware:selfhost", "odzyskany węzeł selfhost", ["local_inference", "private_data", "edge_compute"]),
    "tv_led_panels": ("hardware:led_panel", "panel LED/TV (energia/oświetlenie)", ["light", "energy_recovery"]),
    "pcb_scrap": ("hardware:pcb", "złom PCB (części/CAD)", ["parts_harvest", "design_input"]),
    "power_supplies": ("hardware:psu", "zasilacz (bench)", ["bench_power"]),
    "usb_cameras": ("hardware:camera", "kamera USB (obserwacja)", ["vision", "sensing"]),
    "3d_printer": ("hardware:3d_printer", "drukarka 3D (udostępniona przez człowieka)", ["additive_manufacturing", "production"]),
    "robot_arm": ("hardware:robot_arm", "ramię robota (udostępnione przez człowieka)", ["assembly", "production", "manufacturing"]),
    "mechanics_scrap": ("hardware:mechanics", "mechanika z odzysku (podwozia/motory)", ["mechanics", "parts_harvest", "assembly"]),
    "appliance_sensors": ("hardware:appliance_sensor", "czujniki z pralek/zmywarek (temp/przepływ/ciśnienie/poziom)", ["sensing", "water_level", "temperature", "pressure_flow"]),
    "esp_boards": ("hardware:esp", "płytka ESP (edge control)", ["edge_compute", "control", "mesh", "lora", "sensing"]),
    "field_feedback": ("hardware:field_msg", "wiadomość z pola (feedback)", ["field_data"]),
}

CHARTER_PATH = Path(__file__).with_name("charter.json")

REMOTE_INSTRUCTIONS: dict[str, str] = {
    "default": (
        "Wybierz najlepsza opcje dla roju Strazy Przyszlosci na podstawie stanu i kryteriow. "
        "Uwzglednij heurystyczny score roju jako dowod, ale ocen tez dopasowanie opisu opcji do sytuacji."
    ),
    "strategy": (
        "Decyzja: strategia zarzadzania rujem na ten cykl (inspiracja CEZAR). Sygnaly: backlog, "
        "presja limitow darmowych API, zadania krytyczne, okno OZE. Wybierz strategie, ktora "
        "maksymalizuje liczbe zweryfikowanych ulepszen przy dostepnych zasobach."
    ),
    "allocation": (
        "Decyzja: przydzial zasobu (sprzet/model) do zapotrzebowania misyjnego. Zasoby: telefony, "
        "czujniki z AGD, plytki ESP, drukarki 3D, ramiona robota, wczely selfhost, darmowe modele API. "
        "Wybierz zasob najlepiej pokrywajacy wymagania zapotrzebowania."
    ),
    "exec_mode": (
        "Decyzja: tryb wykonania zadania. device_profile = gotowy algorytm pisany pod sprzet; "
        "on_device_model = maly model decyzyjny na wezle; cloud_chain = lancuch LLM w hubie na "
        "darmowych API. Priorytet: lokalnie i tanszej, jesli wystarcza."
    ),
}


def load_charter(path: Path = CHARTER_PATH) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    for field in ("allowed_mission_classes", "forbidden_keywords"):
        if field not in data:
            raise ValueError(f"charter: brak pola {field}")
    return data


def charter_check(mission_demands: list[Demand], charter: dict[str, Any]) -> dict[str, Any]:
    """Twarde granice praw człowieka dla planu roju (bez nadzoru w polu).

    Misje z klasami poza allowed_mission_classes lub etykietami zawierającymi
    forbidden_keywords są blokowane — przydział nie powstaje.
    """
    violations: list[dict[str, Any]] = []
    allowed = set(charter["allowed_mission_classes"])
    forbidden = [kw.lower() for kw in charter["forbidden_keywords"]]
    for demand in mission_demands:
        text = (f"{demand.label} {' '.join(sorted(demand.required))} " + json.dumps(demand.payload or {}, ensure_ascii=False)).lower()
        hit = next((kw for kw in forbidden if re.search(r"(?<!\w)" + re.escape(kw) + (r"(?!\w)" if kw == "bron" else ""), text)), None)
        if hit:
            violations.append({"demand_id": demand.demand_id, "rule": "forbidden_keywords", "detail": hit})
            continue
        mission_classes = set((demand.payload or {}).get("mission_classes", []) or [])
        outside = mission_classes - allowed
        if mission_classes and outside:
            violations.append({"demand_id": demand.demand_id, "rule": "allowed_mission_classes", "detail": sorted(outside)})
    return {"checked": True, "ok": not violations, "violations": violations, "charter_version": charter.get("charter_version", "v1")}


def resources_from_records(records: list[dict]) -> list[SwarmResource]:
    """Sprzęt/zasoby z rekordów resource_scout (potencjalne, do zagospodarowania)."""
    out: list[SwarmResource] = []
    for record in records:
        cls = record.get("resource_class", "")
        pattern_id, label, caps = HARDWARE_KINDS.get(cls, ("hardware:unknown", f"zasób {cls}", ["unknown"]))
        out.append(SwarmResource(
            f"{pattern_id}:{record.get('id', uuid.uuid4().hex[:6])}", "hardware", label, caps,
            cost_class="owned_hardware_low_cost" if record.get("cost", {}).get("amount_pln", 0) == 0 else "low_cost",
            energy_class="low_power_or_oze_preferred",
            quality_tier=2, speed_class="medium", rpd_budget=None, rpd_used=0,
            available=True, origin="resource_scout",
        ))
    return out


class Demand:
    """Otwarte zapotrzebowanie roju (zadanie do wykonania w tym cyklu)."""

    def __init__(self, demand_id: str, label: str, required: list[str], source: str, priority: int = 1, payload: dict[str, Any] | None = None) -> None:
        self.demand_id = demand_id
        self.label = label
        self.required = set(required)
        self.source = source
        self.priority = priority
        self.payload = payload or {}


STRATEGY_DESCRIPTIONS: dict[str, str] = {
    "speed_first": "najszybszy wystarczający zasób (krótki czas reakcji roju)",
    "quality_first": "najwyższa jakość/tier (zadania krytyczne dla misji)",
    "load_balance": "rozkład na providerów/sprzęt (chroni limity darmowych tierów)",
    "quota_preserve": "oszczędzanie rzadkich zasobów (niski RPD/wysoki tier) na ciężkie zadania",
    "energy_oze": "preferencja local/OZE przy ograniczonym budżecie energii (noc/okno OZE)",
    "redundancy": "warianty (cezar): krytyczne zapotrzebowanie wykonane podwójnie",
    "queue_when_busy": "kolejka (cezar): przy wysokiej presji nowe zadania czekają",
}

STRATEGY_WEIGHTS: dict[str, dict[str, float]] = {
    "speed_first": {"speed": 1.0, "tier": 0.2, "headroom": 0.2, "balance": 0.0},
    "quality_first": {"speed": 0.0, "tier": 1.0, "headroom": 0.3, "balance": 0.0},
    "load_balance": {"speed": 0.3, "tier": 0.3, "headroom": 0.2, "balance": 1.0},
    "quota_preserve": {"speed": 0.3, "tier": 0.2, "headroom": 1.0, "balance": 0.3},
    "energy_oze": {"speed": 0.2, "tier": 0.3, "headroom": 0.2, "balance": 0.0},
    "redundancy": {"speed": 0.3, "tier": 0.5, "headroom": 0.3, "balance": 0.5},
    "queue_when_busy": {"speed": 0.5, "tier": 0.2, "headroom": 0.5, "balance": 0.3},
}

SPEED_SCORE = {"fast": 1.0, "medium": 0.5, "slow": 0.25}


def resource_score(resource: SwarmResource, demand: Demand, strategy: str, usage: dict[str, int]) -> float:
    """Score zasobu dla zapotrzebowania pod wybraną strategią (deterministycznie).

    Dopasowanie częściowe: zasób pokrywający część wymagań dostaje niski,
    ale realny score (0.05 * pokrycie) — rój przydziela najlepsze pokrycie,
    a brak jakiegokolwiek pokrycia dyskwalifikuje (równowagę pełnego dopasowania
    i pokrycia częściowego rozstrzyga confidence + defer basala).
    """
    overlap = demand.required & resource.capabilities
    if not overlap:
        return -10.0
    if not resource.available:
        return -10.0
    if resource.kind == "model" and resource.rpd_budget is not None and resource.headroom <= 0.0:
        return -10.0
    if not demand.required.issubset(resource.capabilities):
        return 0.05 * (len(overlap) / len(demand.required))
    w = STRATEGY_WEIGHTS[strategy]
    speed = SPEED_SCORE.get(resource.speed_class, 0.25)
    tier = min(resource.quality_tier / 5.0, 1.0)
    headroom = resource.headroom
    balance = 1.0 / (1.0 + usage.get(resource.resource_id, 0))
    local_bonus = 0.0
    if strategy == "energy_oze" and ("local" in resource.energy_class or "oze" in resource.energy_class):
        local_bonus = 0.5
    return w["speed"] * speed + w["tier"] * tier + w["headroom"] * headroom + w["balance"] * balance + local_bonus


EXEC_MODES = ["device_profile", "on_device_model", "cloud_chain"]


NEED_CAPABILITY_RULES: list[tuple[list[str], list[str]]] = [
    (["monitoring", "obserwac", "kamera", "wizj", "czujnik", "pomiar", "telemetri"], ["vision", "sensing"]),
    (["offline", "katalog", "lokaln", "selfhost", "bez api", "suweren"], ["local_inference", "edge_compute"]),
    (["mesh", "lora", "lacznos", "łącznoś", "komunikac", "izolac"], ["mesh", "lora"]),
    (["czesci", "części", "recykling", "cad", "pcb"], ["parts_harvest", "design_input"]),
    (["energi", "oze", "solar", "zasilan"], ["energy_recovery"]),
    (["druk", "drukarka", "wydruk"], ["additive_manufacturing", "production"]),
    (["montaz", "montaż", "ramie robota", "ramię robota", "produkcj", "zrobotyzowan"], ["assembly", "production"]),
    (["odchwaszcz", "chwast", "weeding", "platforma robota", "robot rol"], ["mechanics", "assembly", "vision"]),
]


def demand_from_need(record: dict[str, Any]) -> Demand:
    """Zapotrzebowanie misyjne z rekordu human_needs (deterministyczne reguły)."""
    text = " ".join([
        str(record.get("need_or_problem", "")),
        str(record.get("expected_outcome", "")),
        " ".join(record.get("mission_classes", []) or []),
    ]).lower()
    required: set[str] = set()
    for keywords, caps in NEED_CAPABILITY_RULES:
        if any(k in text for k in keywords):
            required.update(caps)
    if not required:
        required.update(["edge_compute"])
    priority = 2 if (record.get("energy_constraints", {}) or {}).get("oze_required") else 1
    return Demand(
        record.get("id", uuid.uuid4().hex[:8]),
        str(record.get("need_or_problem", "potrzeba"))[:80],
        sorted(required),
        "human_needs",
        priority=priority,
        payload=record,
    )


def exec_mode_scores(demand: Demand, resource: SwarmResource) -> dict[str, float]:
    """Kandydaci trybu wykonania (decyzja basal, nie sztywno w kodzie łańcucha).

    device_profile: algorytm napisany pod sprzęt (observer pack, edge_flasher);
    on_device_model: mały model decyzyjny postawiony na węźle (basal na brzegu);
    cloud_chain: łańcuch LLM w hubie na darmowych API (warstwa strategii).
    Przerwy między score'ami celowo duże: decyzja ma być confident, a przy
    równowadze basal ma deferować do bezpiecznego defaultu (cloud_chain).
    """
    scores = {m: 0.0 for m in EXEC_MODES}
    caps = resource.capabilities
    if resource.kind == "hardware":
        if "vision" in caps or "sensing" in caps:
            scores["device_profile"] += 1.2
        if "local_inference" in caps:
            scores["on_device_model"] += 0.4
        if "edge_compute" in caps:
            scores["on_device_model"] += 0.7
        scores["cloud_chain"] += 0.2
    else:
        scores["cloud_chain"] += 1.2
        scores["on_device_model"] += 0.1
    if demand.required & {"reasoning", "draft"}:
        scores["cloud_chain"] += 0.3
    if demand.required & {"field_data"}:
        scores["on_device_model"] += 0.3
    return scores


class SwarmPlanner:
    """Planista roju: bardzo wiele decyzji basal na cykl, suggest-only.

    Decyzje per cykl: (1) strategia zarządzania, (2) dobór zapotrzebowań,
    (3) przydział zasobu per zapotrzebowanie, (4) tryb wykonania per para.
    """

    def __init__(self, core: BasalDecisionCore, default_strategy: str = "speed_first") -> None:
        self.core = core
        self.default_strategy = default_strategy

    def decide_strategy(self, cycle_signals: dict[str, Any]) -> dict[str, Any]:
        """Strategia cyklu wg sygnałów kontekstu (cezar: wiele strategii zarządzania)."""
        quota_pressure = float(cycle_signals.get("quota_pressure", 0.0))
        backlog = int(cycle_signals.get("backlog", 0))
        critical = int(cycle_signals.get("critical_jobs", 0))
        oze_window = bool(cycle_signals.get("oze_window", False))
        scores = {
            "speed_first": 1.0 + 0.1 * backlog,
            "quality_first": 0.3 + 0.5 * critical,
            "load_balance": 0.5 + 1.2 * quota_pressure,
            "quota_preserve": 0.4 + 1.0 * quota_pressure,
            "energy_oze": 0.3 + (1.0 if oze_window else 0.0),
            "redundancy": 0.1 + 0.6 * critical,
            "queue_when_busy": 0.1 + 0.4 * max(0, backlog - 5),
        }
        options = list(STRATEGY_DESCRIPTIONS)
        return self.core.decide("strategy", options, scores, default_option=self.default_strategy, context={"cycle_signals": cycle_signals})

    def decide_job_selection(self, demands: list[Demand], max_jobs: int) -> dict[str, Any]:
        """Basal wybiera zapotrzebowania cyklu (ranking + confidence + defer)."""
        if not demands:
            return {"final": [], "deferred": False, "confidence": 1.0, "ranking": [], "decision": None}
        scores = {d.demand_id: float(d.priority) for d in demands}
        decision = self.core.decide("job_selection", [d.demand_id for d in demands], scores, default_option=max(demands, key=lambda d: d.priority).demand_id, context={"max_jobs": max_jobs})
        ranking = [k for k, _ in decision["probabilities"].items()]
        return {"final": ranking, "deferred": decision["deferred"], "confidence": decision["confidence"], "ranking": ranking, "decision": decision}

    def decide_allocation(self, demand: Demand, candidates: list[SwarmResource], strategy: str, usage: dict[str, int]) -> dict[str, Any]:
        """Przydział zasobu do zapotrzebowania — decyzja modelu decyzyjnego."""
        scores = {r.resource_id: resource_score(r, demand, strategy, usage) for r in candidates}
        if all(s <= -5.0 for s in scores.values()):
            return {"decision": None, "resource": None, "reason": "no_capable_resource"}
        options = list(scores)
        default = sorted(options, key=lambda k: -scores[k])[0]
        decision = self.core.decide("allocation", options, scores, default_option=default, context={"demand": demand.demand_id, "strategy": strategy})
        return {"decision": decision, "resource": decision["final"], "reason": "ok"}

    def decide_exec_mode(self, demand: Demand, resource: SwarmResource) -> dict[str, Any]:
        scores = exec_mode_scores(demand, resource)
        default = "cloud_chain"
        decision = self.core.decide("exec_mode", EXEC_MODES, scores, default_option=default, context={"demand": demand.demand_id, "resource": resource.resource_id})
        return decision

    def plan_cycle(self, mission_demands: list[Demand], procdev_demands: list[Demand], resources: list[SwarmResource], cycle_signals: dict[str, Any], max_jobs: int = 3) -> dict[str, Any]:
        """Pełny plan roju na cykl; sugeruje (suggest-only), nie wykonuje.

        Dwa tory decyzji basal:
        1. PRZYDZIAŁ SPRZĘTU: każde zapotrzebowanie misyjne (usługi dla
           ludności, human_needs) dostaje zasób (telefon/ESP/selfhost/model)
           + tryb wykonania (algorytm pod sprzęt vs model on-device vs cloud).
        2. KOLEJNOŚĆ WYKONANIA: zapotrzebowania procdev (łańcuchy AI,
           kosztują limity darmowych tierów) — basal wybiera i porządkuje
           do max_jobs wg priorytetów i sygnałów cyklu.
        """
        usage: dict[str, int] = {}
        strategy_decision = self.decide_strategy(cycle_signals)
        strategy = strategy_decision["final"]

        mission_allocations: list[dict[str, Any]] = []
        charter = load_charter()
        charter_result = charter_check(mission_demands + procdev_demands, charter)
        blocked_ids = {v["demand_id"] for v in charter_result["violations"]}
        for demand in mission_demands:
            if demand.demand_id in blocked_ids:
                mission_allocations.append({
                    "demand_id": demand.demand_id,
                    "label": demand.label,
                    "resource": None,
                    "exec_mode": None,
                    "reason": "charter_violation",
                    "charter_violation": next(v["detail"] for v in charter_result["violations"] if v["demand_id"] == demand.demand_id),
                })
                continue
            allocation = self.decide_allocation(demand, resources, strategy, usage)
            if allocation["resource"] is None:
                mission_allocations.append({"demand_id": demand.demand_id, "label": demand.label, "resource": None, "exec_mode": None, "reason": allocation["reason"]})
                continue
            resource = next(r for r in resources if r.resource_id == allocation["resource"])
            mode_decision = self.decide_exec_mode(demand, resource)
            usage[resource.resource_id] = usage.get(resource.resource_id, 0) + 1
            mission_allocations.append({
                "demand_id": demand.demand_id,
                "label": demand.label,
                "resource": resource.to_dict(),
                "exec_mode": mode_decision["final"],
                "exec_mode_decision": {k: mode_decision[k] for k in ("chosen", "confidence", "deferred", "final")},
                "allocation_confidence": allocation["decision"]["confidence"],
                "allocation_deferred": allocation["decision"]["deferred"],
                "reason": "ok",
            })

        execution = self.decide_job_selection([d for d in procdev_demands if d.demand_id not in blocked_ids], max_jobs)
        execution_order = execution["final"][:max_jobs]

        return {
            "strategy": strategy,
            "strategy_decision": {k: strategy_decision[k] for k in ("chosen", "confidence", "deferred", "final")},
            "mission_allocations": mission_allocations,
            "charter": charter_result,
            "execution_order": execution_order,
            "execution_confidence": execution["confidence"],
            "execution_deferred": execution["deferred"],
            "decisions_count": len(self.core.decisions),
            "policy": "suggest-only",
            "auto_applied": False,
            "temperature_note": TEMPERATURE_NOTE,
        }
