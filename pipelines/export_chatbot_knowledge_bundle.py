from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_JSON = REPO_ROOT / "data" / "chatbot" / "telegram_knowledge_bundle_v1.json"
OUTPUT_JS = REPO_ROOT / "cloudflare" / "src" / "generated_knowledge_bundle.js"

ALLOWLIST = [
    "README.md",
    "MARKETING.md",
    "docs/ARCHITEKTURA_ONBOARDINGU.md",
    "docs/STRATEGIA_INTEGRACJI.md",
    "docs/PRZYKLADY_GOTOWEGO_KODU.md",
    "docs/JAK_ZOSTAC_DOSTAWCA_DANYCH.md",
    "docs/ARCHITEKTURA_MOSTU_TELEGRAM_GITHUB_ISSUES.md",
    "PROJEKTY/01_inteligentna_akwakultura.md",
    "PROJEKTY/02_wirtualne_ogrodzenia.md",
    "PROJEKTY/03_ai_monitoring_porodow.md",
    "PROJEKTY/04_lampa_z_recyklingu_tv.md",
    "PROJEKTY/05_recykling_pv_laserem.md",
    "PROJEKTY/05_recykling_pv_szczegoly_techniczne.md",
    "PROJEKTY/06_smartfony_jako_sterowniki.md",
    "PROJEKTY/07_uniwersalna_platforma_sterowania.md",
    "PROJEKTY/08_openbot_autonomiczne_maszyny_rolnicze.md",
    "PROJEKTY/09_monitoring_iot_livestock.md",
    "PROJEKTY/10_lacznosc_mesh_lora.md",
    "PROJEKTY/11_autonomiczne_systemy_rd.md",
    "PROJEKTY/12_autonomiczne_pcb_ze_smieci.md",
    "PROJEKTY/13_baza_czesci_recykling/README.md",
    "PROJEKTY/14_autonomiczne_projektowanie_3d_cad.md",
    ".github/ISSUE_TEMPLATE/nowy_straznik.md",
    ".github/ISSUE_TEMPLATE/pomysl_rozwiazanie.md",
    ".github/ISSUE_TEMPLATE/zastrzezenie_uwaga.md",
    "data/onboarding/straznik_rekomendator_v1.json",
]


@dataclass
class SourceDocument:
    path: str
    title: str
    category: str
    text: str


def read_text(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def extract_markdown_title(path: str, text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip()
    return path


def split_markdown_sections(path: str, text: str) -> list[dict[str, Any]]:
    normalized = normalize_whitespace(text)
    parts = re.split(r"(?m)^##\s+", normalized)
    sections: list[dict[str, Any]] = []

    if parts:
        intro = parts[0].strip()
        if intro:
            sections.append(
                {
                    "id": f"{slugify(path)}-intro",
                    "source_path": path,
                    "title": "Wprowadzenie",
                    "category": "document",
                    "content": intro,
                }
            )

    for index, part in enumerate(parts[1:], start=1):
        lines = part.splitlines()
        if not lines:
            continue
        title = lines[0].strip()
        content = normalize_whitespace("\n".join(lines[1:]))
        if not content:
            continue
        sections.append(
            {
                "id": f"{slugify(path)}-{index}-{slugify(title)}",
                "source_path": path,
                "title": title,
                "category": "document",
                "content": content,
            }
        )

    return sections


def build_source_documents() -> list[SourceDocument]:
    documents: list[SourceDocument] = []
    for path in ALLOWLIST:
        if path.endswith(".json"):
            continue
        text = read_text(path)
        category = "issue_template" if path.startswith(".github/ISSUE_TEMPLATE/") else "document"
        documents.append(
            SourceDocument(
                path=path,
                title=extract_markdown_title(path, text),
                category=category,
                text=normalize_whitespace(text),
            )
        )
    return documents


def build_sections(documents: list[SourceDocument]) -> list[dict[str, Any]]:
    sections: list[dict[str, Any]] = []
    for document in documents:
        if document.category == "issue_template":
            sections.append(
                {
                    "id": f"{slugify(document.path)}-template",
                    "source_path": document.path,
                    "title": document.title,
                    "category": document.category,
                    "content": document.text,
                }
            )
            continue
        sections.extend(split_markdown_sections(document.path, document.text))
    return sections


def build_quick_facts(sections: list[dict[str, Any]]) -> list[str]:
    facts: list[str] = []
    for section in sections:
        source_path = section["source_path"]
        if source_path not in {"README.md", "docs/ARCHITEKTURA_ONBOARDINGU.md", "docs/STRATEGIA_INTEGRACJI.md"}:
            continue
        content = section["content"]
        for line in content.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith(("- ", "* ", "1.", "2.", "3.", "4.", "5.", "6.")):
                facts.append(stripped.lstrip("-*1234567890. ").strip())
            elif len(facts) < 5:
                facts.append(stripped)
            if len(facts) >= 18:
                return facts
    return facts


def build_routes() -> list[dict[str, Any]]:
    raw_data = json.loads(read_text("data/onboarding/straznik_rekomendator_v1.json"))
    return raw_data["routes"]


def build_bundle() -> dict[str, Any]:
    documents = build_source_documents()
    sections = build_sections(documents)
    routes = build_routes()
    return {
        "schema_version": "v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "allowlist": ALLOWLIST,
        "documents": [
            {
                "path": document.path,
                "title": document.title,
                "category": document.category,
            }
            for document in documents
        ],
        "quick_facts": build_quick_facts(sections),
        "sections": sections,
        "onboarding_routes": routes,
        "issue_templates": {
            "new_guardian": ".github/ISSUE_TEMPLATE/nowy_straznik.md",
            "idea": ".github/ISSUE_TEMPLATE/pomysl_rozwiazanie.md",
            "feedback": ".github/ISSUE_TEMPLATE/zastrzezenie_uwaga.md",
        },
        "github_base_url": "https://github.com/StrazPrzyszlosci/STRAZ_PRZYSZLOSCI/blob/main/",
        "issue_new_base_url": "https://github.com/StrazPrzyszlosci/STRAZ_PRZYSZLOSCI/issues/new?template=",
    }


def write_outputs(bundle: dict[str, Any]) -> None:
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JS.parent.mkdir(parents=True, exist_ok=True)

    serialized = json.dumps(bundle, ensure_ascii=False, indent=2)
    OUTPUT_JSON.write_text(serialized + "\n", encoding="utf-8")
    OUTPUT_JS.write_text(
        "export const knowledgeBundle = "
        + serialized
        + ";\n",
        encoding="utf-8",
    )


def main() -> int:
    bundle = build_bundle()
    write_outputs(bundle)
    print(json.dumps({"status": "ok", "output_json": str(OUTPUT_JSON), "output_js": str(OUTPUT_JS)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
