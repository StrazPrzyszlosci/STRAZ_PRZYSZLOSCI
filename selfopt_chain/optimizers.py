#!/usr/bin/env python3
"""Optymalizatory samodoskonalące (selfopt_chain, T48).

GEPA (Genetic-Pareto): wybor kandydatow promptow na froncie Pareto
(jakosc ^, latencja v, koszt v) + refleksja w jezyku naturalnym z feedbacku.
OpenEvolve (AlphaEvolve): archiwum MAP-Elites z niszami (kind, complexity),
akceptacja kandydata tylko przy przewyższeniu inkumbenta niszy.

Obie metody produkują WYŁĄCZNIE propozycje (auto_apply=false) do review
człowieka - spójnie z zasadą suggest-only repo (T38).
"""
from __future__ import annotations

from typing import Any

DIMENSIONS = ("quality", "latency_ms", "cost")


def _dominates(a: dict[str, Any], b: dict[str, Any]) -> bool:
    """Czy kandydat a dominuje b: >= wszędzie i > co najmniej w jednym."""
    qa, la, ca = a["scores"]["quality"], a["scores"]["latency_ms"], a["scores"]["cost"]
    qb, lb, cb = b["scores"]["quality"], b["scores"]["latency_ms"], b["scores"]["cost"]
    ge = (qa >= qb) and (la <= lb) and (ca <= cb)
    gt = (qa > qb) or (la < lb) or (ca < cb)
    return ge and gt


class GepaPromptOptimizer:
    def pareto_front(self, candidates: list[dict[str, Any]]) -> list[str]:
        front = [
            c for c in candidates
            if not any(_dominates(o, c) for o in candidates if o is not c)
        ]
        return [c["id"] for c in front]

    def optimize(self, candidates: list[dict[str, Any]]) -> dict[str, Any]:
        if not candidates:
            return {"method": "gepa-pareto-v1", "pareto_front": [], "chosen_id": None, "auto_apply": False, "rationale": "brak kandydatow"}
        front_ids = self.pareto_front(candidates)
        front = [c for c in candidates if c["id"] in front_ids]
        chosen = sorted(front, key=lambda c: (-c["scores"]["quality"], c["scores"]["latency_ms"], c["scores"]["cost"]))[0]
        worst = sorted(candidates, key=lambda c: (c["scores"]["quality"], -c["scores"]["latency_ms"]))[0]
        return {
            "method": "gepa-pareto-v1",
            "pareto_front": sorted(front_ids),
            "chosen_id": chosen["id"],
            "auto_apply": False,
            "rationale": (
                f"Wybrano {chosen['id']} (quality={chosen['scores']['quality']}, "
                f"latency_ms={chosen['scores']['latency_ms']}); kandydat {worst['id']} dominowany "
                f"(quality={worst['scores']['quality']}). Nic nie zostalo auto-zaaplikowane."
            ),
            "feedback_merged": [c.get("feedback", "") for c in candidates if c.get("feedback")],
        }

    def propose_reflection(self, candidates: list[dict[str, Any]], insights: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        """Refleksja GEPA: scal feedback kandydatow i insights w propozycje patcha promptu."""
        feedback_lines = [c.get("feedback", "") for c in candidates if c.get("feedback")]
        insight_lines = [i.get("suggested_skill_patch", "") for i in insights or [] if i.get("suggested_skill_patch")]
        patch_lines = ["### Propozycja patcha promptu (suggest-only)"]
        if feedback_lines:
            patch_lines.append("Uwagi z wykonan:")
            patch_lines.extend(f"- {line}" for line in feedback_lines)
        if insight_lines:
            patch_lines.append("Insighty strukturalne (Abstral):")
            patch_lines.extend(f"- {line}" for line in insight_lines)
        if len(patch_lines) == 1:
            patch_lines.append("Brak feedbacku do scalenia - zbierz wiecej sladow wykonania.")
        return {"method": "gepa-reflection-v1", "auto_apply": False, "prompt_patch_proposal": "\n".join(patch_lines)}


def default_fitness(scores: dict[str, Any]) -> float:
    """Fitness MAP-Elites: jakosc z kara za latencje (normalizowana do 3000 ms)."""
    latency_penalty = min(scores.get("latency_ms", 0) / 3000.0, 1.0)
    return float(scores.get("quality", 0.0)) - 0.25 * latency_penalty


class MapElitesOptimizer:
    """Archiwum Quality-Diversity: nisza = (kind, complexity)."""

    def __init__(self, fitness_fn=None) -> None:
        self.archive: dict[tuple[str, str], dict[str, Any]] = {}
        self.fitness_fn = fitness_fn or default_fitness

    def niche_of(self, program: dict[str, Any]) -> tuple[str, str]:
        return (program.get("kind", ""), program.get("complexity", ""))

    def step(self, programs: list[dict[str, Any]]) -> list[dict[str, Any]]:
        accepted: list[dict[str, Any]] = []
        for program in programs:
            niche = self.niche_of(program)
            fitness = self.fitness_fn(program["scores"])
            incumbent = self.archive.get(niche)
            if incumbent is None or fitness > incumbent["fitness"]:
                self.archive[niche] = {"program_id": program["id"], "fitness": round(fitness, 4), "program_ref": program}
                accepted.append({"niche": list(niche), "program_id": program["id"], "fitness": round(fitness, 4), "replaced": incumbent["program_id"] if incumbent else None})
        return accepted

    def proposal(self) -> dict[str, Any]:
        rows = []
        for (kind, complexity), entry in sorted(self.archive.items()):
            rows.append({
                "kind": kind,
                "complexity": complexity,
                "program_id": entry["program_id"],
                "fitness": entry["fitness"],
            })
        return {
            "method": "openevolve-map-elites-v1",
            "auto_apply": False,
            "niches": len(rows),
            "archive": rows,
            "note": "Wszystkie programy-kandydaci czekaja na review czlowieka; nic nie zostalo auto-zaaplikowane.",
        }
