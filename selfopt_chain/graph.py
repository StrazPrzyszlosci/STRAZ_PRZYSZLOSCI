#!/usr/bin/env python3
"""Minimalny, zero-dependency StateGraph w stylu LangGraph (selfopt_chain, T48).

API celowo zgodne z langgraph.graph.StateGraph: add_node, add_edge,
add_conditional_edges, set_entry_point, compile().invoke(state). Dzieki temu
definicje lancuchow sa przenosne na prawdziwy pakiet langgraph, gdy jest
zainstalowany (patrz adapters.py), a bez niego biegna na tej implementacji.

Wezly zwracaja czesciowe slowniki scalane do stanu (merge), jak w LangGraph.
Zabezpieczenia: nieznane wezly odrzucane, limit krokow chroni przed petla.
"""
from __future__ import annotations

from typing import Any, Callable

START = "__start__"
END = "__end__"
DEFAULT_MAX_STEPS = 64


class GraphError(Exception):
    pass


class StateGraph:
    def __init__(self, schema: Any = None) -> None:
        self._schema = schema
        self._nodes: dict[str, Callable[[dict], dict]] = {}
        self._edges: list[tuple[str, str]] = []
        self._conditional: list[tuple[str, Callable[[dict], str], dict[str, str]]] = []
        self._entry: str | None = None

    def add_node(self, name: str, fn: Callable[[dict], dict]) -> "StateGraph":
        if name in (START, END):
            raise GraphError(f"add_node: nazwa {name} zarezerwowana")
        if name in self._nodes:
            raise GraphError(f"add_node: wezel {name} juz istnieje")
        self._nodes[name] = fn
        return self

    def _check_endpoint(self, name: str) -> None:
        if name not in (START, END) and name not in self._nodes:
            raise GraphError(f"krawedz wskazuje nieznany wezel: {name}")

    def add_edge(self, a: str, b: str) -> "StateGraph":
        self._check_endpoint(a)
        self._check_endpoint(b)
        self._edges.append((a, b))
        return self

    def add_conditional_edges(self, source: str, fn: Callable[[dict], str], mapping: dict[str, str]) -> "StateGraph":
        if source not in self._nodes:
            raise GraphError(f"add_conditional_edges: nieznany wezel zrodlowy: {source}")
        for target in mapping.values():
            self._check_endpoint(target)
        self._conditional.append((source, fn, mapping))
        return self

    def set_entry_point(self, name: str) -> "StateGraph":
        if name not in self._nodes:
            raise GraphError(f"set_entry_point: nieznany wezel: {name}")
        self._entry = name
        return self

    def compile(self) -> "CompiledGraph":
        cond_sources = {src for src, _, _ in self._conditional}
        for src, _ in self._edges:
            if src in cond_sources:
                raise GraphError(f"wezel {src} ma jednoczesnie krawedz stala i warunkowa")
        entry = self._entry
        if entry is None:
            starts = [b for a, b in self._edges if a == START]
            if not starts:
                raise GraphError("brak punktu wejscia: uzyc set_entry_point lub add_edge(START, ...)")
            if len(starts) > 1:
                raise GraphError("wiecej niz jeden punkt wejscia")
            entry = starts[0]
        return CompiledGraph(
            nodes=dict(self._nodes),
            edges=list(self._edges),
            conditional=list(self._conditional),
            entry=entry,
        )


class CompiledGraph:
    def __init__(self, nodes: dict, edges: list, conditional: list, entry: str) -> None:
        self._nodes = nodes
        self._edges = {(a, b) for a, b in edges}
        self._conditional = conditional
        self._entry = entry

    @property
    def entry_point(self) -> str:
        return self._entry

    def _next_node(self, current: str, state: dict) -> str:
        for src, fn, mapping in self._conditional:
            if src == current:
                key = fn(state)
                if key not in mapping:
                    raise GraphError(f"krawedz warunkowa {current}: brak mapowania dla klucza {key!r}")
                return mapping[key]
        targets = [b for a, b in sorted(self._edges) if a == current]
        if not targets:
            return END
        if len(targets) > 1:
            raise GraphError(f"wezel {current} ma wiecej niz jedna krawedz wychodzaca bez mapowania warunkowego")
        return targets[0]

    def invoke(self, state: dict[str, Any], config: dict[str, Any] | None = None, *, max_steps: int = DEFAULT_MAX_STEPS, on_event: Callable[[str, str], None] | None = None) -> dict[str, Any]:
        """Uruchomienie grafu; on_event(phase, node) sluzy trasowaniu."""
        result = dict(state)
        node = self._entry
        steps = 0
        while node != END:
            if steps >= max_steps:
                raise GraphError(f"przekroczono limit {max_steps} krokow (mozliwa petla)")
            if on_event:
                on_event("node_start", node)
            patch = self._nodes[node](result) or {}
            if not isinstance(patch, dict):
                raise GraphError(f"wezel {node} zwrocil {type(patch).__name__}, oczekiwano dict")
            result.update(patch)
            if on_event:
                on_event("node_end", node)
            node = self._next_node(node, result)
            steps += 1
        return result
