#!/usr/bin/env python3
"""Headless worker Hermes/OpenClaw w roju + bramka bezpieczeństwa kodu (T52).

Hermes (https://github.com/NousResearch hermes-agent CLI; zainstalowany lokalnie)
= gotowe, wyizolowane środowisko agenticzne do REUSE_OSS -> ADAPT -> SYNTHESIZE.
OpenClaw = drugi wykonawca headless (wymaga instalacji CLI u operatora).

IZOLACJA na tym komputerze (dyrektywa operatora 2026-10-22):
- każdy run w osobnym katalogu sandbox `scratch/selfopt/hermes_sandbox/<run_id>`;
- `hermes chat --in <sandbox> --worktree --safe-mode --run-budget --max-turns`
  (safe-mode + worktree + limit czasu to natywna izolacja CLI Hermes);
- środowisko scrubowane: ZERO sekretów w env workera (jawna whitelistka);
- kwarantanna: wszystko, co worker wyprodukuje, ląduje w
  `scratch/selfopt/hermes_quarantine/<run_id>/` i NIGDY nie wchodzi do repo
  bez przejścia SecurityGate + review człowieka (PR, no_auto_merge).

SecurityGate ("zly kod nie moze wejsc do roju"):
- wzorce zakazane (sekrety, destrukcja, exfiltracja, network w testach,
  physical actuation, obuszenie env);
- licencje copyleft -> flaga do review (nie auto-blok, ale wymagany czlowiek);
- wynik: {ok, violations, licenses_review} — ok=false => kwarantanna trzyma.
"""
from __future__ import annotations

import json
import ast
import hashlib
import signal
import subprocess
import time
import os
import re
import shutil
import uuid
from pathlib import Path
from typing import Any

HERMES_RUN_ENV_FLAG = "SELFOPT_HERMES"
SANDBOX_ROOT = Path("scratch/selfopt/hermes_sandbox")
QUARANTINE_ROOT = Path("scratch/selfopt/hermes_quarantine")
DEFAULT_TOOLSETS = "web,terminal,skills"
DEFAULT_MAX_TURNS = 20
DEFAULT_RUN_BUDGET_S = 900
ENV_WHITELIST = {"PATH", "HOME", "LANG", "LC_ALL", "TERM", "TMPDIR", "XDG_RUNTIME_DIR"}

FORBIDDEN_CODE_PATTERNS: list[tuple[str, str]] = [
    ("secret_aws", r"AKIA[0-9A-Z]{16}"),
    ("secret_openai_like", r"\bsk-[A-Za-z0-9]{20,}"),
    ("secret_private_key", r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    ("secret_generic_token", r"(api[_-]?key|token|password|secret)\s*[:=]\s*['\"][A-Za-z0-9_\-]{16,}['\"]"),
    ("destructive_fs", r"\brm\s+-rf\s+/(?!tmp)"),
    ("privilege_escalation", r"\bsudo\b"),
    ("pipe_to_shell", r"(curl|wget)[^\n|]*\|\s*(ba)?sh\b"),
    ("env_exfiltration", r"printenv|os\.environ\.items\(\)|dumpenv"),
    ("physical_actuation", r"\b(physical_actuation|pump_on|valve_open|laser_on)\b"),
    ("network_in_tests", r"urlopen|requests\.(get|post)|httpx\.client\("),
    ("eval_of_input", r"\beval\s*\(|\bexec\s*\("),
]

LICENSE_REVIEW_PATTERNS = [
    (r"GNU GENERAL PUBLIC LICENSE|SPDX-License-Identifier:\s*GPL", "GPL (copyleft) — review licencji wymagany"),
    (r"GNU AFFERO GENERAL PUBLIC LICENSE|AGPL", "AGPL (copyleft sieciowy) — review licencji wymagany"),
    (r"SPDX-License-Identifier:\s*BUSL|Business Source License", "BSL — nie open source, review wymagany"),
]


class SecurityGate:
    """Bramka bezpieczeństwa kodu wyprodukowanego przez worker/LLM."""

    def inspect_code(self, text: str) -> dict[str, Any]:
        violations: list[dict[str, str]] = []
        for rule, pattern in FORBIDDEN_CODE_PATTERNS:
            if re.search(pattern, text or "", re.IGNORECASE):
                violations.append({"rule": rule, "hint": pattern[:60]})
        licenses_review: list[str] = []
        for pattern, note in LICENSE_REVIEW_PATTERNS:
            if re.search(pattern, text or "", re.IGNORECASE):
                licenses_review.append(note)
        return {
            "ok": not violations and not licenses_review,
            "blocked": bool(violations),
            "violations": violations,
            "licenses_review": licenses_review,
            "quarantine_required": bool(violations or licenses_review),
        }

    def inspect_tree(self, root: Path, skip: set[str] | None = None) -> dict[str, Any]:
        """Bramka nad WYPRODUKOWANYMI artefaktami; surowe logi strumienia (output.json)
        zostają zapieczętowane w kwarantannie, ale nie są oceniane jako kod — zawierają
        echo zapytania i ruch narzędzi, nie produkcję modelu."""
        skip = skip or set()
        report: dict[str, Any] = {"ok": True, "blocked": False, "violations": [], "licenses_review": [], "scanned_files": 0}
        for path in sorted(root.rglob("*")):
            if path.name in skip:
                continue
            if path.is_symlink():
                report["violations"].append({"rule": "symlink_forbidden", "file": str(path)})
                continue
            if path.is_file() and path.suffix in {".py", ".js", ".mjs", ".ts", ".c", ".cpp", ".h", ".sh", ".md", ".json", ".yaml", ".yml", ".toml", ".patch", ".diff"}:
                try:
                    content = path.read_text(encoding="utf-8", errors="ignore")
                except OSError:
                    continue
                single = self.inspect_code(content)
                if not content.strip():
                    continue
                report["scanned_files"] += 1
                for v in single["violations"]:
                    v2 = {**v, "file": str(path)}
                    report["violations"].append(v2)
                report["licenses_review"].extend(f"{note} [{path}]" for note in single["licenses_review"])
        if report["scanned_files"] == 0:
            report["violations"].append({"rule": "no_artifacts"})
        report["blocked"] = bool(report["violations"])
        report["ok"] = not report["violations"] and not report["licenses_review"]
        report["quarantine_required"] = report["blocked"] or bool(report["licenses_review"])
        return report


class HermesWorker:
    """Builder izolowanego wywołania headless Hermes + obsługa wyniku.

    `build_command` zwraca pełną listę argumentów (bezpieczna do przekazania
    przez subprocess bez shell). Rzeczywiste uruchomienie tylko przy
    SELFOPT_HERMES=1; wynik zawsze przez kwarantannę + SecurityGate.
    """

    def __init__(self, omniroute_base_url: str | None = None, model_alias: str = "auto", api_key: str | None = None, ledger=None, should_stop=None, repo_root=None, models=None, state_dir=None, max_turns=12, run_budget_s=360) -> None:
        import os

        self.omniroute_base_url = (omniroute_base_url or "http://127.0.0.1:20128/v1").rstrip("/")
        self.model_alias = model_alias
        self.api_key = api_key or os.environ.get("SELFOPT_OMNIROUTE_KEY") or ""
        self.ledger, self.should_stop, self.repo_root = ledger, should_stop or (lambda: False), repo_root
        self.models = models
        self.state_dir = Path(state_dir) if state_dir else None
        self.max_turns, self.run_budget_s = max_turns, run_budget_s

    def sandbox_dir(self, run_id: str) -> Path:
        base = self.state_dir / "hermes_sandbox" if self.state_dir else SANDBOX_ROOT if SANDBOX_ROOT.is_absolute() else Path.cwd() / SANDBOX_ROOT
        path = base / run_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def quarantine_dir(self, run_id: str) -> Path:
        base = self.state_dir / "hermes_quarantine" if self.state_dir else QUARANTINE_ROOT if QUARANTINE_ROOT.is_absolute() else Path.cwd() / QUARANTINE_ROOT
        path = base / run_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def write_task_file(self, run_id: str, task_md: str, query: str) -> Path:
        task_file = self.sandbox_dir(run_id) / task_md
        task_file.write_text(query, encoding="utf-8")
        return task_file

    def build_command(self, task_file: Path, run_dir: Path, *, max_turns: int = DEFAULT_MAX_TURNS, run_budget_s: int = DEFAULT_RUN_BUDGET_S, toolsets: str = DEFAULT_TOOLSETS) -> list[str]:
        """Izolowane wywołanie headless (zweryfikowane wobec hermes CLI 2026-10).

        Tryb gateway/oneshot NIE przyjmuje --worktree ani --run-budget (opcje TUI);
        budżet czasu egzekwujemy w run_isolated przez timeout subprocess, a izolację
        zapewniają --in <sandbox> + --safe-mode + scrub_env.
        """
        command = [
            "hermes", "chat",
            "--oneshot",
            "--query-file", str(task_file),
            "--provider", "custom",
            "--base-url", self.omniroute_base_url,
            "--model", self.model_alias,
            "--format", "stream-json",
            "--max-turns", str(max_turns),
            "--in", str(run_dir),
            "--safe-mode",
            "-t", toolsets,
        ]
        return command

    @staticmethod
    def scrub_env() -> dict[str, str]:
        """Minimalne środowisko workera: zero sekretów (whitelistka)."""
        scrubbed = {k: v for k, v in os.environ.items() if k in ENV_WHITELIST}
        for secret_key in ("GEMINI_API_KEY", "GROQ_API_KEY", "MISTRAL_API_KEY", "CEREBRAS_API_KEY", "OPENROUTER_API_KEY", "NVIDIA_API_KEY", "GITHUB_MODELS_TOKEN"):
            scrubbed.pop(secret_key, None)
        return scrubbed

    @staticmethod
    def enabled() -> bool:
        return os.environ.get(HERMES_RUN_ENV_FLAG) == "1"

    def run_isolated(self, query, *, max_turns=None, run_budget_s=None, model_alias=None, input_bundle=None):
        from selfopt_chain.sandbox import Sandbox
        from selfopt_chain.quota_proxy import QuotaProxy
        from selfopt_chain.omniroute import OmniRouteAdapter, FreeOnlyPolicy
        from selfopt_chain.registry import load_registry
        from selfopt_chain.evolution_inputs import repository_snapshot
        from selfopt_chain.evolution_validation import validate_patch
        run_id = uuid.uuid4().hex[:12]
        run_dir, quarantine = self.sandbox_dir(run_id), self.quarantine_dir(run_id)
        max_turns, run_budget_s = max_turns or self.max_turns, run_budget_s or self.run_budget_s
        model = model_alias or self.model_alias
        receipt = {"run_id": run_id, "sandbox_dir": str(run_dir), "quarantine_dir": str(quarantine),
                   "executed": False, "exit_code": None, "security_gate": {"ok": False},
                   "validation": {"ok": False, "error": "not_executed"}, "released_from_quarantine": False}
        if not self.enabled():
            receipt["skipped_reason"] = "SELFOPT_HERMES=1 required"
            return receipt
        runtime = os.environ.get("SELFOPT_HERMES_RUNTIME")
        if not runtime or self.ledger is None or not (Path(runtime) / "bin/hermes").is_file():
            receipt["error"] = "isolated_runtime_and_accounted_gateway_required"
            return receipt
        adapter = OmniRouteAdapter(FreeOnlyPolicy(self.models or load_registry()), base_url=self.omniroute_base_url, api_key=self.api_key)
        if not adapter.policy.actual_allowed(model) or not adapter.network_enabled():
            receipt["error"] = "explicit_allowed_model_and_network_required"
            return receipt
        self.write_task_file(run_id, "task.md", query)
        output = run_dir / "output"
        output.mkdir()
        mounts = []
        bundle = input_bundle or {"kind": "proposal", "allowed_paths": [], "input_files": {}}
        if input_bundle:
            inputs = (self.state_dir or quarantine.parent.parent) / "controller_inputs" / run_id
            inputs.mkdir(parents=True)
            (inputs / "task.json").write_text(json.dumps(bundle, ensure_ascii=False, indent=2))
            mounts.append((inputs, "/input"))
        snapshot = None
        if self.repo_root:
            snapshot, commit = repository_snapshot(self.repo_root, self.state_dir or quarantine.parent.parent)
            receipt["source_commit"] = commit
            mounts.append((snapshot, "/repo"))
            if any(not (snapshot / name).is_file() or (snapshot / name).read_text() != text for name, text in bundle.get("input_files", {}).items()):
                receipt["error"] = "input_source_does_not_match_committed_snapshot"
                return receipt
        before = self.ledger.rpd_used
        started = time.monotonic()
        with QuotaProxy(adapter, self.ledger, model, self.should_stop) as proxy:
            relay = Path(__file__).with_name("gateway_relay.py")
            args = ["/bin/sh", "-c", "python3 /relay.py /gateway.sock & exec \"$@\"", "sh",
                    "/runtime/bin/hermes", "chat", "--oneshot", "--query-file", "/work/task.md",
                    "--provider", "custom", "--base-url", "http://127.0.0.1:20129/v1", "--model", model,
                    "--format", "stream-json", "--max-turns", str(max_turns), "--in", "/work", "--safe-mode", "--source", "tool", "-t", "terminal"]
            command = Sandbox(run_dir).command(args, mounts=[(runtime, "/runtime"), (relay, "/relay.py"), (proxy.path, "/gateway.sock"), *mounts],
                      environment={"OPENAI_API_KEY": proxy.token, "HERMES_HOME": "/work/home", "HERMES_CUSTOM_API_KEY": proxy.token})
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True)
            reason = None
            while True:
                try:
                    raw, errors = process.communicate(timeout=0.25)
                    break
                except subprocess.TimeoutExpired:
                    if self.should_stop() or time.monotonic() - started > run_budget_s:
                        reason = "stopped" if self.should_stop() else "timeout"
                        os.killpg(process.pid, signal.SIGTERM)
                        try:
                            raw, errors = process.communicate(timeout=2)
                        except subprocess.TimeoutExpired:
                            os.killpg(process.pid, signal.SIGKILL)
                            raw, errors = process.communicate()
                        break
        def redact(text):
            text = text.replace(proxy.token, "<REDACTED>")
            return text.replace(self.api_key, "<REDACTED>") if self.api_key else text
        (quarantine / "output.json").write_text(redact(raw))
        (quarantine / "stderr.log").write_text(redact(errors))
        after = self.ledger.rpd_used
        receipt.update(executed=True, exit_code=process.returncode, stop_reason=reason,
                       latency_ms=int((time.monotonic() - started) * 1000),
                       api_calls=dict(proxy.usage), proxy_events=list(proxy.events))
        gate = {"ok": False, "violations": [{"rule": "unsafe_output_directory"}], "quarantine_required": True}
        if output.is_dir() and not output.is_symlink():
            gate = SecurityGate().inspect_tree(output)
            if not any(p.is_symlink() for p in output.rglob("*")):
                for produced in sorted(output.rglob("*")):
                    if produced.is_file():
                        target = quarantine / produced.relative_to(output)
                        target.parent.mkdir(parents=True, exist_ok=True)
                        target.write_bytes(produced.read_bytes())
        if process.returncode != 0 or reason:
            gate.update(ok=False, quarantine_required=True)
            gate.setdefault("violations", []).append({"rule": reason or "worker_failed"})
        receipt["security_gate"] = gate
        receipt["artifacts"] = [{"path": str(p.relative_to(quarantine)), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in quarantine.rglob("*") if p.is_file() and p.name not in {"output.json", "stderr.log"}]
        if gate["ok"] and receipt["artifacts"]:
            if bundle.get("kind") == "patch" and snapshot:
                receipt["validation"] = validate_patch(quarantine, snapshot, bundle, (self.state_dir or quarantine.parent.parent) / "validations" / run_id)
            else:
                proposal = quarantine / "PROPOSAL.md"
                code = [p for p in quarantine.rglob("*") if p.suffix in {".py", ".js", ".patch", ".diff"}]
                receipt["validation"] = {"ok": proposal.is_file() and bool(proposal.read_text().strip()) and not code, "method": "proposal_only"}
        if not receipt["validation"].get("ok"):
            receipt["error"] = receipt["validation"].get("error", "production_not_validated")
        if not receipt["artifacts"]:
            final = [e for e in parse_stream_json_output(raw) if e.get("type") == "result"]
            receipt["error"] = "no_artifacts: " + (str(final[-1].get("error") or final[-1].get("text", ""))[:2000] if final else redact(errors[-2000:]))
        # T60: rozróżnienie stanów błędu — przez to proxy HTTP 429 może pochodzić
        # WYŁĄCZNIE z lokalnej rezerwy/budżetu (provider-429 wychodzi jako 502),
        # więc 429 = local_quota_exhausted, nie myli się z porażką treści.
        error_text = str(receipt.get("error", ""))
        if "HTTP 429" in error_text:
            receipt["error_class"] = "local_quota_exhausted"
            receipt["error_origin"] = "local"
        elif reason == "timeout":
            receipt["error_class"] = "timeout"
        return receipt


def parse_stream_json_output(raw: str) -> list[dict[str, Any]]:
    """Parsuje --format stream-json Hermes do listy eventów (tolerancyjnie)."""
    events: list[dict[str, Any]] = []
    for line in (raw or "").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events
