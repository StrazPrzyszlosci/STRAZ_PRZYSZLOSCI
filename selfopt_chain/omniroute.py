#!/usr/bin/env python3
"""OmniRoute jako warstwa wykonawcza darmowych LLM (selfopt_chain, T52).

Podział odpowiedzialności zgodny z architekturą operatora (2026-10-22):
- basal (mały model decyzyjny) wybiera zadania, strategie, tryb równoległości
  i wymagany poziom jakości — NIE wybiera konkretnego modelu;
- OmniRoute (gateway) dobiera model i dostawcę spośród podłączonych darmowych
  pul (wirtualne aliasy `auto`, `auto/fast`, `auto/smart`...);
- niniejszy adapter egzekwuje politykę FREE-ONLY (STRICT_ZERO_COST) po stronie
  roju: walidacja aliasu PRZED wywołaniem oraz realnego modelu PO odpowiedzi.

Bezpieczeństwo: SELFOPT_NETWORK=1 wymagane; tylko zadania public; brak
płatnego fallbacku (naruszenie = porażka zadania, nigdy eskalacja kosztu).
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import Any

NETWORK_ENV_FLAG = "SELFOPT_NETWORK"
OMNIROUTE_URL_ENV = "SELFOPT_OMNIROUTE_URL"
OMNIROUTE_KEY_ENV = "SELFOPT_OMNIROUTE_KEY"
DEFAULT_OMNIROUTE_URL = "http://127.0.0.1:20128/v1"
DEFAULT_MODEL_ALIAS = "auto"
DEFAULT_TIMEOUT_S = 180

FREE_ALIAS_PREFIX = "auto"
FREE_PROVIDER_IDS = {
    "mistral_free", "nvidia_nim_free", "google_ai_studio_free", "openrouter_free",
    "cerebras_free", "groq_free", "github_models_free",
    "mistral", "nvidia", "duckduckgo-web", "cloudflare-playground",
}


class FreeOnlyPolicy:
    """Twarda polityka darmowości: allowlista z rejestru free_models.json."""

    def __init__(self, models: list[dict]) -> None:
        self.free_model_ids = {m["model_id"] for m in models if m.get("cost_class") == "free_quota" and m.get("privacy_class") != "local_private"}
        self.default_model = next((m["model_id"] for m in models if m["model_id"] in self.free_model_ids), "")
        self.free_providers = {m.get("provider") for m in models}
        self.response_ids = {m["model_id"]: m.get("api", {}).get("response_model_id", m["model_id"]) for m in models if m["model_id"] in self.free_model_ids}

    def alias_allowed(self, model_alias: str) -> bool:
        if not model_alias:
            return False
        if model_alias in {"auto", "auto/fast", "auto/smart", "auto/best-fast", "auto/best-reasoning", "auto/best-coding"}:
            return True
        return model_alias in self.free_model_ids

    def actual_allowed(self, actual_model: str, provider: str | None = None) -> bool:
        if actual_model in self.free_model_ids or actual_model in self.response_ids.values():
            return True
        return False


def omniroute_url() -> str | None:
    return os.environ.get(OMNIROUTE_URL_ENV) or None


class OmniRouteAdapter:
    """Klient OpenAI-compatible do bramki OmniRoute z egzekwowaniem FREE-ONLY."""

    def __init__(self, policy: FreeOnlyPolicy, base_url: str | None = None, timeout_s: int = DEFAULT_TIMEOUT_S, api_key: str | None = None) -> None:
        import os

        self.policy = policy
        self.base_url = (base_url or omniroute_url() or DEFAULT_OMNIROUTE_URL).rstrip("/")
        self.timeout_s = min(timeout_s, int(os.environ.get("SELFOPT_REQUEST_TIMEOUT", "30")))
        self.api_key = api_key or os.environ.get(OMNIROUTE_KEY_ENV) or ""
        self._catalog_loaded = False

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def load_free_catalog(self) -> int:
        """Katalog /v1/models: modele free providerów dokładane do allowlisty.

        Allowlista pozostaje ścisła: owned_by musi być znanym darmowym
        providerem albo model musi być w naszym rejestrze/kończyć się ':free'.
        """
        try:
            req = urllib.request.Request(f"{self.base_url}/models", headers=self._headers())
            with urllib.request.urlopen(req, timeout=30) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except Exception:
            return 0
        # Discovery is informational: it cannot expand the operator's allowlist.
        self._catalog_loaded = True
        return 0

    @staticmethod
    def network_enabled() -> bool:
        return os.environ.get(NETWORK_ENV_FLAG) == "1"

    def complete(self, task: dict[str, Any], prompt: str, model_alias: str = DEFAULT_MODEL_ALIAS) -> dict[str, Any]:
        result: dict[str, Any] = {
            "ok": False, "output": "", "model_id": "", "provider": "omniroute",
            "latency_ms": 0, "tokens_est": 0, "error": None, "error_class": None,
            "requested_alias": model_alias,
        }
        if not self.network_enabled():
            result.update(error=f"network disabled: ustaw {NETWORK_ENV_FLAG}=1", error_class="network_disabled")
            return result
        if task.get("privacy") == "private":
            result.update(error="private task na publicznym gatewayu zabronione", error_class="privacy_violation")
            return result
        if not self.policy.alias_allowed(model_alias):
            result.update(error=f"alias '{model_alias}' poza polityka free-only", error_class="free_only_violation")
            return result
        if model_alias.startswith("auto"):
            model_alias = self.policy.default_model
        if model_alias not in self.policy.free_model_ids:
            result.update(error="FREE-ONLY: unknown model", error_class="free_only_violation")
            return result
        result["requested_alias"] = model_alias
        url = f"{self.base_url}/chat/completions"
        body = json.dumps({
            "model": model_alias,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "max_tokens": int(task.get("max_tokens", 4096)),
        }).encode("utf-8")
        req = urllib.request.Request(url, data=body, headers=self._headers())
        started = time.monotonic()
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            result.update(error=f"HTTP {exc.code} od OmniRoute", error_class="http_error", latency_ms=int((time.monotonic() - started) * 1000))
            return result
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            result.update(error=f"blad polaczenia z OmniRoute ({type(exc).__name__})", error_class="connection_error", latency_ms=int((time.monotonic() - started) * 1000))
            return result
        latency_ms = int((time.monotonic() - started) * 1000)
        actual_model = str(payload.get("model", ""))
        if not self.policy.actual_allowed(actual_model) or actual_model not in {model_alias, self.policy.response_ids.get(model_alias)}:
            result.update(
                error=f"FREE-ONLY naruszone: OmniRoute zwrocil '{actual_model}', ktorego nie ma w rejestrze darmowych modeli",
                error_class="free_only_violation",
                model_id=actual_model,
            )
            return result
        try:
            output = payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            result.update(error="nieoczekiwany format odpowiedzi OmniRoute", error_class="bad_response")
            return result
        if not isinstance(output, str) or not output.strip():
            result.update(error="empty response", error_class="bad_response")
            return result
        tokens = len(prompt.encode("utf-8")) // 4 + len(output.encode("utf-8")) // 4 + 32
        result.update(ok=True, output=output, model_id=actual_model, latency_ms=latency_ms, tokens_est=tokens)
        return result


class OmniRouteEngine:
    """Silnik łańcuchów roju na bramce OmniRoute (interfejs jak MockEngine).

    Router nadal wybiera z rejestru (budżety RPM/RPD), ale wywołanie idzie
    przez gateway z aliasem modelu; model spoza katalogu → fallback 'auto'.
    Katalog free dokładany raz na instancję (load_free_catalog).
    """

    def __init__(self, models: list[dict], base_url: str | None = None, api_key: str | None = None, timeout_s: int = DEFAULT_TIMEOUT_S) -> None:
        self.adapter = OmniRouteAdapter(FreeOnlyPolicy(models), base_url=base_url, timeout_s=timeout_s, api_key=api_key)
        # No network access during construction or implicit model discovery.

    def complete(self, task: dict[str, Any], model_id: str, prompt: str) -> dict[str, Any]:
        if model_id not in self.adapter.policy.free_model_ids:
            return {"ok": False, "output": "", "error": "explicit registered model required", "error_class": "free_only_violation"}
        alias = model_id
        result = self.adapter.complete(task, prompt, model_alias=alias)
        if result.get("requested_alias") == alias:
            result["model_id"] = result.get("model_id") or model_id
        return result
