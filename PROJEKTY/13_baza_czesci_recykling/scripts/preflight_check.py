#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
PROJECT_DIR = Path(__file__).resolve().parents[1]
ENV_EXAMPLE = PROJECT_DIR / ".env.example"
ENV_FILE = PROJECT_DIR / ".env"
NOTEBOOK_PATH = PROJECT_DIR / "youtube-databaseparts.ipynb"
PACK_DIR = PROJECT_DIR / "execution_packs" / "pack-project13-kaggle-enrichment-01"
MANIFEST_PATH = PACK_DIR / "manifest.json"
RUNBOOK_PATH = PACK_DIR / "RUNBOOK.md"
PR_TEMPLATE_PATH = PACK_DIR / "PR_TEMPLATE.md"
REVIEW_CHECKLIST_PATH = PACK_DIR / "REVIEW_CHECKLIST.md"

REQUIRED_SECRETS = ["GITHUB_PAT", "YOUTUBE_API_KEY", "GEMINI_API_KEY"]

GITHUB_PAT_MINIMAL_SCOPES_HINT = (
    "Fine-grained: Contents=Read+Write na forku | "
    "Classic: scope repo"
)

YOUTUBE_QUOTA_HINT = (
    "Darmowa quota: ~10 000 jednostek/dobe; "
    "jeden search = 100 jednostek; "
    "sprawdz https://console.cloud.google.com/apis/api/youtube.googleapis.com/quotas"
)

GEMINI_QUOTA_HINT = (
    "Darmowy tier: limity requests/min i tokens/min; "
    "sprawdz https://ai.google.dev/pricing"
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def add_result(results: list[dict], name: str, status: str, details: str) -> None:
    results.append({"name": name, "status": status, "details": details})


def check_env_file(results: list[dict]) -> None:
    if ENV_FILE.exists():
        add_result(results, "env_file", "pass", f"Znaleziono {ENV_FILE.relative_to(REPO_ROOT)}")
    else:
        add_result(
            results,
            "env_file",
            "fail",
            f"Brak {ENV_FILE.relative_to(REPO_ROOT)} — skopiuj z .env.example: "
            f"cp {ENV_EXAMPLE.relative_to(REPO_ROOT)} {ENV_FILE.relative_to(REPO_ROOT)}",
        )


def check_secrets_present(results: list[dict]) -> None:
    if not ENV_FILE.exists():
        for secret_name in REQUIRED_SECRETS:
            add_result(
                results,
                f"secret::{secret_name}",
                "skip",
                "Plik .env nie istnieje — nie mozna sprawdzic",
            )
        return

    env_text = ENV_FILE.read_text(encoding="utf-8")
    for secret_name in REQUIRED_SECRETS:
        value = os.environ.get(secret_name, "")
        if not value:
            for line in env_text.splitlines():
                stripped = line.strip()
                if stripped.startswith(f"{secret_name}=") and not stripped.endswith("="):
                    value = stripped.split("=", 1)[1].strip()
                    break

        if value and value != "YOUR_TOKEN_HERE" and len(value) > 1:
            add_result(
                results,
                f"secret::{secret_name}",
                "pass",
                f"Wartosc znaleziona (dlugosc: {len(value)})",
            )
        else:
            add_result(
                results,
                f"secret::{secret_name}",
                "fail",
                f"Brak wartosci dla {secret_name} w .env lub srodowisku — "
                f"patrz README.md sekcja 'Jak ustawic sekrety'",
            )


def check_github_pat_scope(results: list[dict]) -> None:
    pat = os.environ.get("GITHUB_PAT", "")
    if not pat and ENV_FILE.exists():
        env_text = ENV_FILE.read_text(encoding="utf-8")
        for line in env_text.splitlines():
            stripped = line.strip()
            if stripped.startswith("GITHUB_PAT=") and not stripped.endswith("="):
                pat = stripped.split("=", 1)[1].strip()
                break

    if not pat:
        add_result(
            results,
            "github_pat::scope",
            "skip",
            "Brak GITHUB_PAT — nie mozna sprawdzic scope. "
            f"Wymagany scope: {GITHUB_PAT_MINIMAL_SCOPES_HINT}",
        )
        return

    if pat.startswith("ghp_") or pat.startswith("github_pat_"):
        add_result(
            results,
            "github_pat::format",
            "pass",
            f"Token ma format GitHub PAT (prefix: {pat[:7]}...)",
        )
    else:
        add_result(
            results,
            "github_pat::format",
            "warn",
            f"Token nie zaczyna sie od typowego prefiksu GitHub PAT — "
            f"upewnij sie, ze to wlasciwy token",
        )

    add_result(
        results,
        "github_pat::scope",
        "manual",
        f"Scope GITHUB_PAT musi byc sprawdzony recznie. "
        f"Wymagany: {GITHUB_PAT_MINIMAL_SCOPES_HINT}. "
        f"Sprawdz na https://github.com/settings/tokens",
    )


def check_quota(results: list[dict]) -> None:
    add_result(
        results,
        "quota::youtube",
        "manual",
        f"Quota YouTube API nie da sie sprawdzic offline. {YOUTUBE_QUOTA_HINT}. "
        f"Jesli runawny run zawiedzie z 403/429, quota mogla sie wyczerpac.",
    )
    add_result(
        results,
        "quota::gemini",
        "manual",
        f"Quota Gemini API nie da sie sprawdzic offline. {GEMINI_QUOTA_HINT}. "
        f"Jesli OCR albo analiza multimodalna zawioda, sprawdz limity.",
    )


def check_project_files(results: list[dict]) -> None:
    files_to_check = [
        ("notebook", NOTEBOOK_PATH),
        ("manifest", MANIFEST_PATH),
        ("runbook", RUNBOOK_PATH),
        ("pr_template", PR_TEMPLATE_PATH),
        ("review_checklist", REVIEW_CHECKLIST_PATH),
        ("env_example", ENV_EXAMPLE),
    ]
    for label, path in files_to_check:
        rel = str(path.relative_to(REPO_ROOT))
        if path.exists():
            add_result(results, f"file::{label}", "pass", rel)
        else:
            add_result(results, f"file::{label}", "fail", f"Brak: {rel}")


def check_notebook_smoke(results: list[dict]) -> None:
    if not NOTEBOOK_PATH.exists():
        add_result(
            results,
            "notebook::smoke",
            "fail",
            "Notebook nie istnieje — nie mozna wykonac smoke check",
        )
        return

    try:
        nb_data = json.loads(NOTEBOOK_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        add_result(
            results,
            "notebook::smoke",
            "fail",
            f"Notebook nie parsuje sie jako JSON: {exc}",
        )
        return

    cells = nb_data.get("cells", [])
    code_cells = [c for c in cells if c.get("cell_type") == "code"]
    add_result(
        results,
        "notebook::smoke",
        "pass",
        f"Notebook parsuje sie: {len(cells)} komorek ({len(code_cells)} kod, "
        f"{len(cells) - len(code_cells)} markdown)",
    )

    nb_text = NOTEBOOK_PATH.read_text(encoding="utf-8")
    markers = {
        "FORK_OWNER_placeholder": ("FORK_OWNER" in nb_text, "Wymagany do konfiguracji forka"),
        "secrets_client": ("UserSecretClient" in nb_text or "kaggle_secrets" in nb_text, "Odczyt sekretow z Kaggle Secrets"),
        "finalizer_call": ("finalize_execution_pack_run" in nb_text, "Wywolanie finalizera packa"),
        "git_push": ("git push" in nb_text or "git_commit" in nb_text or "subprocess" in nb_text, "Push wynikow do forka"),
    }
    for marker_name, (marker_ok, purpose) in markers.items():
        add_result(
            results,
            f"notebook::{marker_name}",
            "pass" if marker_ok else "warn",
            "Obecny" if marker_ok else f"Nie znaleziono — {purpose}",
        )


def check_git_remote(results: list[dict]) -> None:
    git_config = REPO_ROOT / ".git" / "config"
    if not git_config.exists():
        add_result(
            results,
            "git::remote",
            "skip",
            "Nie jestes w katalogu git — pomijam sprawdzanie remote",
        )
        return

    add_result(
        results,
        "git::remote",
        "manual",
        "Upewnij sie, ze 'git remote -v' pokazuje Twoj fork jako origin. "
        "Push do upstream nie jest dozwolony z poziomu notebooka.",
    )


def render_report(results: list[dict], *, env_mode: str) -> str:
    failures = [r for r in results if r["status"] == "fail"]
    warnings = [r for r in results if r["status"] == "warn"]
    manuals = [r for r in results if r["status"] == "manual"]
    skips = [r for r in results if r["status"] == "skip"]

    if failures:
        overall = "BRAKUJE — popraw bledy przed uruchomieniem notebooka"
    elif warnings:
        overall = "OSTRZEZENIA — mozesz kontynuowac, ale sprawdz uwagi"
    elif manuals:
        overall = (
            "WYMAGA RECZNEGO POTWIERDZENIA — "
            "skrypt nie moze automatycznie sprawdzic niektorych punktow"
        )
    else:
        overall = "GOTOWE — wszystkie sprawdzalne punkty sa zielone"

    lines = [
        "# Volunteer Pre-Flight Check Report",
        "",
        f"- executed_at_utc: {utc_now().replace(microsecond=0).isoformat()}",
        f"- env_mode: {env_mode}",
        f"- overall_status: {overall}",
        f"- checks_total: {len(results)}",
        f"- pass: {len([r for r in results if r['status'] == 'pass'])}",
        f"- fail: {len(failures)}",
        f"- warn: {len(warnings)}",
        f"- manual: {len(manuals)}",
        f"- skip: {len(skips)}",
        "",
        "## Wyniki",
        "",
    ]

    for status_label in ["fail", "warn", "manual", "pass", "skip"]:
        items = [r for r in results if r["status"] == status_label]
        if not items:
            continue
        for item in items:
            prefix = {
                "fail": "✗ FAIL",
                "warn": "⚠ WARN",
                "manual": "☝ MANUAL",
                "pass": "✓ PASS",
                "skip": "⊘ SKIP",
            }.get(item["status"], "?")
            lines.append(f"- [{prefix}] **{item['name']}**: {item['details']}")
        lines.append("")

    lines.extend(
        [
            "## Co zrobic dalej",
            "",
            "1. Popraw kazdy punkt FAIL przed uruchomieniem notebooka.",
            "2. Sprawdz recznie kazdy punkt MANUAL — skrypt nie mogl ich potwierdzic.",
            "3. Punkty WARN nie blokuja, ale warto je zweryfikowac.",
            "4. Jesli wszystko jest PASS lub MANUAL, mozesz przejsc do RUNBOOK.md.",
            "",
            "## Czego ten skrypt NIE sprawdza",
            "",
            "- Quota YouTube API — sprawdz recznie w Google Cloud Console",
            "- Quota Gemini API — sprawdz recznie na https://ai.google.dev/pricing",
            "- Scope GITHUB_PAT — sprawdz recznie na https://github.com/settings/tokens",
            "- Dostepnosc darmowego runtime Kaggle — sprawdz na https://www.kaggle.com/",
            "- Wersje pakietow Python na Kaggle — potwierdz dopiero po pierwszym runie",
            "",
        ]
    )
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Volunteer pre-flight check dla Project 13. "
        "Sprawdza lokalna gotowosc przed uruchomieniem notebooka Kaggle."
    )
    parser.add_argument(
        "--env-mode",
        choices=["local", "kaggle"],
        default="local",
        help="Srodowisko docelowe: 'local' (.env) albo 'kaggle' (Kaggle Secrets)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Sciezka do zapisu raportu (domyslnie: stdout)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    results: list[dict] = []

    check_env_file(results)
    check_secrets_present(results)
    check_github_pat_scope(results)
    check_quota(results)
    check_project_files(results)
    check_notebook_smoke(results)
    check_git_remote(results)

    report = render_report(results, env_mode=args.env_mode)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8")
        print(f"Raport zapisany: {args.output}")
    else:
        print(report)

    failures = [r for r in results if r["status"] == "fail"]
    print(
        json.dumps(
            {
                "overall": "fail" if failures else "ok",
                "fail_count": len(failures),
                "manual_count": len([r for r in results if r["status"] == "manual"]),
                "warn_count": len([r for r in results if r["status"] == "warn"]),
            },
            ensure_ascii=False,
        )
    )

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
