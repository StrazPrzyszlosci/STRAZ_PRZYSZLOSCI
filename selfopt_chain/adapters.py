#!/usr/bin/env python3
"""Adaptery silników zewnetrznych (selfopt_chain, T48).

Rdzenie (graph.py, optimizers.py) sa zero-dependency. Gdy operator zainstaluje
prawdziwe pakiety (pip install langgraph gepa openevolve), adaptery wykryja je
i zwroca referencje; w przeciwnym razie lancuch biega na implementacjach
wbudowanych. Wybor silnika jest zawsze jawny (engine name w run_receipt).
"""
from __future__ import annotations

from typing import Any


def _try_import(module: str, attr: str) -> Any | None:
    try:
        mod = __import__(module, fromlist=[attr])
        return getattr(mod, attr, None)
    except Exception:
        return None


def get_graph_engine() -> dict[str, Any]:
    """LangGraph gdy dostepny, inaczej wbudowany StateGraph."""
    try:
        from langgraph.graph import END, START, StateGraph as LgStateGraph  # type: ignore

        return {"engine": "langgraph", "available": True, "StateGraph": LgStateGraph, "START": START, "END": END}
    except Exception:
        from . import graph

        return {"engine": "builtin", "available": False, "StateGraph": graph.StateGraph, "START": graph.START, "END": graph.END}


def get_gepa_engine() -> dict[str, Any]:
    gepa = _try_import("gepa", "optimize")
    return {"engine": "gepa" if gepa else "builtin", "available": gepa is not None, "optimize": gepa}


def get_openevolve_engine() -> dict[str, Any]:
    openevolve = _try_import("openevolve", "OpenEvolve")
    return {"engine": "openevolve" if openevolve else "builtin", "available": openevolve is not None, "OpenEvolve": openevolve}


def engines_summary() -> dict[str, Any]:
    return {
        "graph": get_graph_engine()["engine"],
        "gepa": get_gepa_engine()["engine"],
        "openevolve": get_openevolve_engine()["engine"],
        "note": "builtin = implementacje zero-dependency selfopt_chain; pakiety opcjonalne wg README",
    }
