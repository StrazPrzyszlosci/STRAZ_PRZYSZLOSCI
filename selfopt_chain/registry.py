#!/usr/bin/env python3
"""Rejestr darmowych modeli AI (selfopt_chain).

Waliduje selfopt_chain/free_models.json: unikalne model_id, wyłącznie klasy
kosztu free_quota / owned_hardware_low_cost (płatne modele odrzucane), spójność
privacy zrodla (hosted_api => public_only, selfhost => local_private), sekrety
tylko jako nazwy zmiennych srodowiskowych. Bez zewnetrznych zaleznosci.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

DEFAULT_REGISTRY = Path(__file__).with_name("free_models.json")

SECRET_ENV_RE = re.compile(r"^[A-Z][A-Z0-9_]{2,}$")

SPEED_CLASSES = {"fast", "medium", "slow"}
PRIVACY_CLASSES = {"public_only", "local_private"}
COST_CLASSES = {"free_quota", "owned_hardware_low_cost"}
SELFHOST_PROVIDERS = {"selfhost_recovered_node"}
KNOWN_CAPABILITIES = {"text", "json", "vision", "long_context", "code", "reasoning"}

REQUIRED_MODEL_FIELDS = (
    "model_id", "provider", "role", "quality_tier", "speed_class",
    "capabilities", "privacy_class", "cost_class", "context_tokens",
    "rpm_seed", "rpd_seed", "api", "limits_verified", "notes",
)
REQUIRED_API_FIELDS = {"style", "secret_env"}


def validate_registry(payload: dict) -> list[str]:
    errors: list[str] = []
    models = payload.get("models")
    if not isinstance(models, list) or not models:
        return ["models must be a non-empty array"]

    seen_ids: set[str] = set()
    for i, m in enumerate(models):
        if not isinstance(m, dict):
            errors.append(f"models[{i}] must be object")
            continue
        mid = m.get("model_id", f"models[{i}]")
        missing = [f for f in REQUIRED_MODEL_FIELDS if f not in m]
        if missing:
            errors.append(f"{mid}: missing fields {sorted(missing)}")
            continue
        if mid in seen_ids:
            errors.append(f"{mid}: duplicate model_id")
        seen_ids.add(mid)

        if not isinstance(m.get("quality_tier"), int) or not 1 <= m["quality_tier"] <= 5:
            errors.append(f"{mid}: quality_tier must be int in 1..5")
        if m.get("speed_class") not in SPEED_CLASSES:
            errors.append(f"{mid}: speed_class must be one of {sorted(SPEED_CLASSES)}")
        caps = m.get("capabilities")
        if not isinstance(caps, list) or not caps or not all(isinstance(c, str) for c in caps):
            errors.append(f"{mid}: capabilities must be non-empty list of strings")
        elif not set(caps).issubset(KNOWN_CAPABILITIES):
            errors.append(f"{mid}: unknown capabilities {sorted(set(caps) - KNOWN_CAPABILITIES)}")
        if m.get("privacy_class") not in PRIVACY_CLASSES:
            errors.append(f"{mid}: privacy_class must be one of {sorted(PRIVACY_CLASSES)}")
        if m.get("cost_class") not in COST_CLASSES:
            errors.append(f"{mid}: cost_class must be one of {sorted(COST_CLASSES)} (platne modele sa zabronione)")
        for f in ("rpm_seed", "rpd_seed", "context_tokens"):
            if not isinstance(m.get(f), int) or m[f] <= 0:
                errors.append(f"{mid}: {f} must be positive int")

        provider = m.get("provider", "")
        api = m.get("api", {})
        if not isinstance(api, dict) or not set(api) >= REQUIRED_API_FIELDS:
            errors.append(f"{mid}: api must contain {sorted(REQUIRED_API_FIELDS)}")
        else:
            if "secret" in api or "api_key" in api or "key" in api:
                errors.append(f"{mid}: api must not contain secret values (tylko nazwy zmiennych env)")
            if not SECRET_ENV_RE.match(str(api.get("secret_env", ""))):
                errors.append(f"{mid}: api.secret_env must be UPPER_SNAKE_CASE name of env variable, nie wartosc sekretu")
            if provider in SELFHOST_PROVIDERS and api.get("style") != "local":
                errors.append(f"{mid}: selfhost provider must use api.style=local")
            if provider not in SELFHOST_PROVIDERS and api.get("style") == "local":
                errors.append(f"{mid}: hosted provider cannot use api.style=local")

        expected_privacy = "local_private" if provider in SELFHOST_PROVIDERS else "public_only"
        if m.get("privacy_class") != expected_privacy:
            errors.append(f"{mid}: privacy_class must be {expected_privacy} for provider {provider}")
        if m.get("limits_verified") is True and not str(m.get("notes", "")).strip():
            errors.append(f"{mid}: limits_verified=true requires wypelnione notes")
    return errors


def load_registry(path: Path | None = None) -> list[dict]:
    data = json.loads((path or DEFAULT_REGISTRY).read_text(encoding="utf-8"))
    errors = validate_registry(data)
    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        raise ValueError("invalid model registry")
    return data["models"]


def model_by_id(models: list[dict], model_id: str) -> dict | None:
    return next((m for m in models if m.get("model_id") == model_id), None)


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    args = parser.parse_args(argv if argv is not None else None)
    data: dict[str, Any] = json.loads(args.registry.read_text(encoding="utf-8"))
    errors = validate_registry(data)
    if errors:
        for e in errors:
            print(f"ERROR: {e}")
        return 1
    providers = sorted({m["provider"] for m in data["models"]})
    print(f"OK: {len(data['models'])} darmowych modeli, providers: {', '.join(providers)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
