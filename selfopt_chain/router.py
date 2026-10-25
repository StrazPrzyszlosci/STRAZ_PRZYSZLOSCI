#!/usr/bin/env python3
"""Router darmowych modeli AI (selfopt_chain, T48).

Polityka operatora: przydziel model o ODPOWIEDNIEJ jakości do zadania, żeby
maksymalizować szybkość przy zachowaniu jakości. Konkretne reguły:

1. Prywatność najpierw: zadanie private tylko na modele local_private.
2. Kandydaci: tier >= wymagany dla kind, capabilities pokrywają requires,
   budżet RPM/RPD per run nieprzekroczony, provider nie zablokowany w
   quota_snapshot (gdy podany).
3. Sortowanie deterministyczne: minimalny NADMIAR tieru (nie marnujemy
   mocnych darmowych modeli na lekkie zadania), potem speed_class
   (fast > medium > slow), potem największy zapas limitu RPD.
4. Zero losowości; remisy rozstrzyga kolejność w rejestrze.

Bez zewnetrznych zaleznosci; bez sieci - router tylko wybiera.
"""
from __future__ import annotations

from typing import Any

DEFAULT_REQUIRED_TIER: dict[str, int] = {
    "format": 1,
    "classify": 1,
    "route": 1,
    "summarize": 2,
    "extract": 2,
    "translate": 2,
    "triage": 2,
    "draft": 3,
    "review": 4,
    "code_draft": 4,
    "reason": 4,
    "multimodal_reason": 4,
    "vision_extract": 5,
    "large_batch_extraction": 5,
}

DEFAULT_REQUIRED_TIER_FOR_UNKNOWN_KIND = 3

SPEED_SCORE = {"fast": 3, "medium": 2, "slow": 1}

SELFHOST_PROVIDERS = {"selfhost_recovered_node"}

BLOCKED_SNAPSHOT_STATUSES = {"missing", "stale"}


def required_tier_for_kind(kind: str, table: dict[str, int] | None = None) -> int:
    t = table or DEFAULT_REQUIRED_TIER
    return t.get(kind, DEFAULT_REQUIRED_TIER_FOR_UNKNOWN_KIND)


from selfopt_chain.quota import QuotaLedger, QuotaExceeded


def _provider_blocked_by_snapshot(provider: str, quota_snapshot: dict[str, Any] | None) -> bool:
    if not isinstance(quota_snapshot, dict):
        return False
    for entry in quota_snapshot.get("entries", []):
        if isinstance(entry, dict) and entry.get("provider") == provider:
            if entry.get("status") in BLOCKED_SNAPSHOT_STATUSES:
                return True
    return False


def route_task(
    task: dict[str, Any],
    models: list[dict],
    ledger: QuotaLedger,
    quota_snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Wybór modelu do pojedynczego zadania. Zwraca decyzję z audytem."""
    kind = task.get("kind", "")
    privacy = task.get("privacy", "public")
    requires = set(task.get("requires", []) or [])
    required = required_tier_for_kind(kind)

    decision: dict[str, Any] = {
        "task_id": task.get("task_id", ""),
        "kind": kind,
        "privacy": privacy,
        "required_tier": required,
        "policy": "public_prefers_hosted_then_min_tier_excess_then_speed_then_headroom",
        "chosen": None,
        "alternatives": [],
        "blocked": False,
        "blocked_reason": None,
    }

    candidates: list[tuple[tuple, dict]] = []
    rejected: dict[str, list[str]] = {"privacy": [], "tier": [], "capabilities": [], "quota": [], "snapshot": [], "role": []}

    for idx, m in enumerate(models):
        mid = m["model_id"]
        if kind not in m.get('routing_roles', [kind]):
            rejected['role'].append(mid)
            continue
        if privacy == "private" and m.get("privacy_class") != "local_private":
            rejected["privacy"].append(mid)
            continue
        if m.get("quality_tier", 0) < required:
            rejected["tier"].append(mid)
            continue
        if not requires.issubset(set(m.get("capabilities", []))):
            rejected["capabilities"].append(mid)
            continue
        if not ledger.can_use(mid):
            rejected["quota"].append(mid)
            continue
        if _provider_blocked_by_snapshot(m.get("provider", ""), quota_snapshot):
            rejected["snapshot"].append(mid)
            continue
        tier_excess = m["quality_tier"] - required
        selfhost_penalty = 1 if (privacy != "private" and m.get("provider") in SELFHOST_PROVIDERS) else 0
        sort_key = (selfhost_penalty, tier_excess, -SPEED_SCORE.get(m.get("speed_class", "slow"), 1), -ledger.rpd_headroom(mid), idx)
        candidates.append((sort_key, m))

    if not candidates:
        decision["blocked"] = True
        if rejected["privacy"] and not rejected["tier"] + rejected["capabilities"] + rejected["quota"] + rejected["snapshot"] + rejected['role']:
            decision["blocked_reason"] = "privacy_conflict"
        elif rejected["quota"] and not rejected["tier"] + rejected["capabilities"] + rejected['role']:
            decision["blocked_reason"] = "quota_exhausted"
        elif rejected["snapshot"]:
            decision["blocked_reason"] = "provider_blocked_by_snapshot"
        elif rejected["capabilities"]:
            decision["blocked_reason"] = "no_capability_match"
        elif rejected["tier"]:
            decision["blocked_reason"] = "no_tier_match"
        elif rejected['role']:
            decision['blocked_reason'] = 'no_role_match'
        else:
            decision["blocked_reason"] = "empty_registry"
        decision["rejected"] = rejected
        return decision

    candidates.sort(key=lambda pair: pair[0])
    chosen = candidates[0][1]
    decision["chosen"] = {
        "model_id": chosen["model_id"],
        "provider": chosen["provider"],
        "quality_tier": chosen["quality_tier"],
        "speed_class": chosen["speed_class"],
    }
    decision["alternatives"] = [
        {"model_id": m["model_id"], "provider": m["provider"], "quality_tier": m["quality_tier"], "speed_class": m["speed_class"]}
        for _, m in candidates[1:4]
    ]
    decision["candidates_count"] = len(candidates)
    decision["rejected"] = rejected
    return decision
