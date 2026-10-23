#!/usr/bin/env python3
"""Silniki modeli dla selfopt_chain (T48).

MockEngine: deterministyczny, offline - podstawowy tryb testow i dry-runu.
FreeApiEngine: realne darmowe API, ale twardo bramkowane:
- wymaga SELFOPT_NETWORK=1 (domyslnie wylaczone),
- przyjmuje wylacznie zadania publiczne (privacy=public),
- sekrety czyta wylacznie ze zmiennych srodowiskowych, nigdy nie loguje.

Zero zewnetrznych zaleznosci (stdlib urllib).
"""
from __future__ import annotations

import hashlib
import json
import time
import os
import urllib.error
import urllib.request
from typing import Any

from .transport import DEFAULT_CRITICAL_KEYWORDS

NETWORK_ENV_FLAG = "SELFOPT_NETWORK"
DEFAULT_TIMEOUT_S = 30

SPEED_LATENCY_MS = {"fast": 250, "medium": 800, "slow": 2000}


class NetworkDisabledError(RuntimeError):
    pass


def estimate_latency_ms(model: dict) -> int:
    return SPEED_LATENCY_MS.get(model.get("speed_class", "slow"), 2000)


def _result(ok: bool, output: str, model: dict, latency_ms: int, tokens: int, error: str | None = None, error_class: str | None = None) -> dict[str, Any]:
    return {
        "ok": ok,
        "output": output,
        "model_id": model.get("model_id", ""),
        "provider": model.get("provider", ""),
        "latency_ms": latency_ms,
        "tokens_est": tokens,
        "error": error,
        "error_class": error_class,
    }


class MockEngine:
    """Deterministyczny silnik offline. fail_kinds symuluje awarie dla optymalizatora."""

    def __init__(self, models: list[dict], fail_kinds: set[str] | None = None) -> None:
        self._models = {m["model_id"]: m for m in models}
        self.fail_kinds = set(fail_kinds or set())

    def complete(self, task: dict[str, Any], model_id: str, prompt: str) -> dict[str, Any]:
        model = self._models.get(model_id)
        if model is None:
            return _result(False, "", {"model_id": model_id, "provider": "?"}, 0, 0, "unknown model", "unknown_model")
        kind = task.get("kind", "")
        latency = estimate_latency_ms(model)
        tokens = len(prompt.encode("utf-8")) // 4 + 32
        if kind in self.fail_kinds:
            return _result(False, "", model, latency, tokens, f"mock failure for kind={kind}", "mock_failure")
        digest = hashlib.sha1(prompt.encode("utf-8")).hexdigest()[:12]
        upper_prompt = prompt.upper()
        if kind == "classify":
            output = "ALARM" if any(kw.upper() in upper_prompt for kw in DEFAULT_CRITICAL_KEYWORDS) else "OK"
        elif kind == "draft" and any(kw.upper() in upper_prompt for kw in DEFAULT_CRITICAL_KEYWORDS):
            output = f"[mock:draft|{model_id}|{digest}] ALARM: advisory dla operatora w terenie"
        else:
            output = f"[mock:{kind}|{model_id}|{digest}]"
        return _result(True, output, model, latency, tokens)


class FreeApiEngine:
    """Realne darmowe API (OpenAI-compatible lub Google Gemini).

    Safety: dziala TYLKO przy SELFOPT_NETWORK=1 i TYLKO dla zadan publicznych.
    """

    def __init__(self, models: list[dict], timeout_s: int = DEFAULT_TIMEOUT_S) -> None:
        self._models = {m["model_id"]: m for m in models}
        self.timeout_s = min(timeout_s, int(os.environ.get("SELFOPT_REQUEST_TIMEOUT", "30")))

    @staticmethod
    def network_enabled() -> bool:
        return os.environ.get(NETWORK_ENV_FLAG) == "1"

    def complete(self, task: dict[str, Any], model_id: str, prompt: str) -> dict[str, Any]:
        if not self.network_enabled():
            return _result(False, "", {"model_id": model_id, "provider": "?"}, 0, 0, f"network disabled: ustaw {NETWORK_ENV_FLAG}=1, aby wlaczyc", "network_disabled")
        if task.get("privacy") == "private":
            return _result(False, "", {"model_id": model_id, "provider": "?"}, 0, 0, "private task na publicznym API zabronione", "privacy_violation")
        model = self._models.get(model_id)
        if model is None:
            return _result(False, "", {"model_id": model_id, "provider": "?"}, 0, 0, "unknown model", "unknown_model")
        if model.get("api", {}).get("style") == "local":
            return _result(False, "", model, 0, 0, "local engine unavailable", "local_engine_unavailable")
        secret_env = model.get("api", {}).get("secret_env", "")
        api_key = os.environ.get(secret_env, "")
        if not api_key:
            return _result(False, "", model, 0, 0, f"brak sekretu w zmiennej srodowiskowej {secret_env}", "missing_secret")
        started = time.monotonic()
        try:
            output = self._call(model, api_key, prompt)
        except urllib.error.HTTPError as exc:
            return _result(False, "", model, 0, 0, f"HTTP {exc.code} od providera", "http_error")
        except (KeyError, IndexError, TypeError, ValueError):
            return _result(False, "", model, 0, 0, "invalid response", "bad_response")
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            reason = type(exc).__name__
            return _result(False, "", model, 0, 0, f"blad polaczenia ({reason})", "connection_error")
        if not isinstance(output, str) or not output.strip():
            return _result(False, "", model, 0, 0, "empty response", "bad_response")
        tokens = len(prompt.encode("utf-8")) // 4 + len(output.encode("utf-8")) // 4 + 32
        return _result(True, output, model, int((time.monotonic() - started) * 1000), tokens)

    def _call(self, model: dict, api_key: str, prompt: str) -> str:
        style = model.get("api", {}).get("style")
        base = model.get("api", {}).get("base_url", "").rstrip("/")
        if style == "openai_chat":
            url = f"{base}/chat/completions"
            body = json.dumps({"model": model["model_id"], "messages": [{"role": "user", "content": prompt}], "max_tokens": 2048}).encode("utf-8")
            req = urllib.request.Request(url, data=body, headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"})
        elif style == "google_gemini":
            url = f"{base}/v1beta/models/{model['model_id']}:generateContent"
            body = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode("utf-8")
            req = urllib.request.Request(url, data=body, headers={"x-goog-api-key": api_key, "Content-Type": "application/json"})
        else:
            raise ValueError(f"nieobslugiwany styl API: {style}")
        with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        if style == "openai_chat":
            return payload["choices"][0]["message"]["content"]
        return payload["candidates"][0]["content"]["parts"][0]["text"]
