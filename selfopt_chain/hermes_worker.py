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

    def inspect_tree(self, root: Path) -> dict[str, Any]:
        report: dict[str, Any] = {"ok": True, "blocked": False, "violations": [], "licenses_review": [], "scanned_files": 0}
        for path in sorted(root.rglob("*")):
            if path.is_file() and path.suffix in {".py", ".js", ".mjs", ".ts", ".c", ".cpp", ".h", ".sh", ".md", ".json", ".yaml", ".yml", ".toml"}:
                try:
                    content = path.read_text(encoding="utf-8", errors="ignore")
                except OSError:
                    continue
                single = self.inspect_code(content)
                report["scanned_files"] += 1
                for v in single["violations"]:
                    v2 = {**v, "file": str(path)}
                    report["violations"].append(v2)
                report["licenses_review"].extend(f"{note} [{path}]" for note in single["licenses_review"])
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

    def __init__(self, omniroute_base_url: str | None = None, model_alias: str = "auto", api_key: str | None = None) -> None:
        import os

        self.omniroute_base_url = (omniroute_base_url or "http://127.0.0.1:20128/v1").rstrip("/")
        self.model_alias = model_alias
        self.api_key = api_key or os.environ.get("SELFOPT_OMNIROUTE_KEY") or ""

    def sandbox_dir(self, run_id: str) -> Path:
        path = SANDBOX_ROOT / run_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def quarantine_dir(self, run_id: str) -> Path:
        path = QUARANTINE_ROOT / run_id
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
        if self.api_key:
            command.extend(["--api-key", self.api_key])
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

    def run_isolated(self, query: str, *, max_turns: int = DEFAULT_MAX_TURNS, run_budget_s: int = DEFAULT_RUN_BUDGET_S) -> dict[str, Any]:
        """Pełny izolowany run (tylko przy SELFOPT_HERMES=1) z kwarantanną."""
        run_id = uuid.uuid4().hex[:12]
        run_dir = self.sandbox_dir(run_id)
        task_file = self.write_task_file(run_id, "task.md", query)
        command = self.build_command(task_file, run_dir, max_turns=max_turns, run_budget_s=run_budget_s)
        receipt: dict[str, Any] = {
            "run_id": run_id,
            "command": command,
            "sandbox_dir": str(run_dir),
            "quarantine_dir": str(self.quarantine_dir(run_id)),
            "executed": False,
            "exit_code": None,
            "raw_output": None,
            "security_gate": None,
        }
        if not self.enabled():
            receipt["skipped_reason"] = f"{HERMES_RUN_ENV_FLAG}=1 wymagane do uruchomienia workera"
            return receipt
        import subprocess

        completed = subprocess.run(
            command,
            cwd=str(run_dir),
            env=self.scrub_env(),
            capture_output=True,
            text=True,
            timeout=run_budget_s + 60,
        )
        receipt.update(executed=True, exit_code=completed.returncode)
        raw = completed.stdout or ""
        quarantine = self.quarantine_dir(run_id)
        (quarantine / "output.json").write_text(raw, encoding="utf-8")
        for produced in sorted(run_dir.glob("**/*")):
            if produced.is_file() and produced != task_file:
                target = quarantine / produced.relative_to(run_dir)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(produced, target)
        gate = SecurityGate().inspect_tree(quarantine)
        receipt["security_gate"] = gate
        receipt["released_from_quarantine"] = False
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
