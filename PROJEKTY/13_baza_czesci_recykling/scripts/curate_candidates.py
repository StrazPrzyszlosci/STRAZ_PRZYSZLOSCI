#!/usr/bin/env python3
"""
Execution surface for pack-project13-curation-01.

Curate verified candidates into canonical catalog schemas with
explicit accept/defer/reject decisions and audit trail.

Commands:
  review          — Load and summarize verification input (snapshot + report + disagreements)
  align           — Align each candidate to canonical catalog schemas
  decide          — Apply curation decisions (auto + manual for disputed)
  apply           — Write accepted candidates into canonical catalog files
  validate        — Validate catalog cross-file consistency after apply
  report          — Generate curation_report.md and curation_decisions.jsonl
  dry-run         — Run align+decide+validate+report without writing to catalog
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = PROJECT_ROOT / "data"
REPORTS_DIR = PROJECT_ROOT / "autonomous_test" / "reports"
RESULTS_DIR = PROJECT_ROOT / "autonomous_test" / "results"

DEVICES_PATH = DATA_DIR / "devices.jsonl"
PARTS_MASTER_PATH = DATA_DIR / "parts_master.jsonl"
DEVICE_PARTS_PATH = DATA_DIR / "device_parts.jsonl"

VERIFIED_SNAPSHOT_PATH = RESULTS_DIR / "test_db_verified.jsonl"
VERIFICATION_REPORT_PATH = REPORTS_DIR / "verification_report.md"
DISAGREEMENT_LOG_PATH = REPORTS_DIR / "verification_disagreements.jsonl"

CURATION_DECISIONS_PATH = REPORTS_DIR / "curation_decisions.jsonl"
CURATION_REPORT_PATH = REPORTS_DIR / "curation_report.md"

CATALOG_EXECUTION_SURFACE = PROJECT_ROOT / "scripts" / "curate_candidates.py"


def read_jsonl(path):
    if not path.exists():
        return []
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def write_jsonl(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def append_jsonl(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text)
    text = text.strip("-")
    return text


def normalize_part_number(pn):
    return re.sub(r"[^a-z0-9]", "", pn.lower())


DEVICE_CATEGORIES = [
    "laptop",
    "router",
    "smart_switch",
    "development_board",
    "set_top_box",
    "monitor",
    "phone",
    "tablet",
    "server",
    "industrial_pc",
    "power_supply",
    "printer",
    "camera",
    "audio_device",
    "unknown",
]

SPECIES_MAP = {
    "IC": [
        "mcu",
        "cpu",
        "gpu",
        "soc",
        "controller",
        "processor",
        "regulator",
        "amplifier",
        "driver",
        "transceiver",
        "converter",
        "chip",
    ],
    "Resistor": ["resistor", "resistors"],
    "Capacitor": ["capacitor", "capacitors", "cap"],
    "Inductor": ["inductor", "inductors", "coil", "choke"],
    "Diode": ["diode", "diodes", "led", "zener", "schottky", "tvs"],
    "Transistor": ["transistor", "mosfet", "fet", "bjt", "igbt"],
    "Connector": ["connector", "connector", "header", "socket", "jack", "plug"],
    "Crystal": ["crystal", "oscillator", "resonator"],
    "Fuse": ["fuse", "ptc", "polyfuse"],
    "Switch": ["switch", "button", "tactile"],
    "Relay": ["relay"],
    "Transformer": ["transformer"],
    "Battery": ["battery", "cell", "accu"],
    "Sensor": ["sensor", "accelerometer", "gyroscope", "thermistor", "hall"],
    "EMI_Filter": ["emi", "filter", "ferrite", "bead"],
    "PCB": ["pcb", "board", "module", "pcba"],
    "Unknown": [],
}

GENUS_MAP = {
    "IC": [
        "Power",
        "MCU",
        "CPU",
        "GPU",
        "Logic",
        "Analog",
        "RF",
        "Memory",
        "Interface",
        "Unknown",
    ],
    "Resistor": ["Passive"],
    "Capacitor": ["Passive"],
    "Inductor": ["Passive"],
    "Diode": ["Semiconductor"],
    "Transistor": ["Semiconductor"],
    "Connector": ["Electromechanical"],
    "Crystal": ["Passive"],
    "Fuse": ["Protection"],
    "Switch": ["Electromechanical"],
    "Relay": ["Electromechanical"],
    "Transformer": ["Passive"],
    "Battery": ["Energy"],
    "Sensor": ["Sensor"],
    "EMI_Filter": ["Passive"],
    "PCB": ["Assembly"],
    "Unknown": ["Unknown"],
}

MOUNTING_MAP = {
    "SMD": [
        "smd",
        "0402",
        "0603",
        "0805",
        "1206",
        "qfn",
        "qfp",
        "bga",
        "soic",
        "tssop",
        "sot-23",
        "dfn",
    ],
    "THT": ["tht", "dip", "to-220", "to-92", "to-252", "through-hole"],
}

REJECTION_PATTERNS = [
    (r"^[A-Z]\d{1,3}([,\s]+[A-Z]\d{1,3})+$", "looks_like_designator_list"),
    (r"^BRAK$", "empty_verification"),
    (r"^\s*$", "empty_field"),
    (r"^[A-ZĄĆĘŁŃÓŚŹŻa-ząćęłńóśźż\s]{4,}$", "looks_like_plain_text_phrase"),
    (r"^\d+[µu]?[FfHh]$", "looks_like_value_not_mpn"),
    (r"^\d+[KkMm]?[ΩΩ]$", "looks_like_value_not_mpn"),
]


def looks_like_valid_mpn(part_number):
    if not part_number or not part_number.strip():
        return False, "empty_field"
    pn = part_number.strip()
    for pattern, reason in REJECTION_PATTERNS:
        if re.match(pattern, pn):
            return False, reason
    if len(pn) < 2:
        return False, "too_short"
    has_alnum = any(c.isalnum() for c in pn)
    if not has_alnum:
        return False, "no_alphanumeric"
    return True, None


def infer_species(part_name, part_number):
    pn_lower = (part_name or "").lower()
    for species, keywords in SPECIES_MAP.items():
        if species == "Unknown":
            continue
        for kw in keywords:
            if kw in pn_lower:
                return species
    return "Unknown"


def infer_genus(species):
    return GENUS_MAP.get(species, ["Unknown"])[0]


def infer_mounting(part_name, part_number):
    pn_lower = (part_name or "").lower() + " " + (part_number or "").lower()
    for mounting, keywords in MOUNTING_MAP.items():
        for kw in keywords:
            if kw in pn_lower:
                return mounting
    return "unknown"


def infer_device_category(device_name):
    dn_lower = (device_name or "").lower()
    for cat in DEVICE_CATEGORIES:
        if cat.replace("_", " ") in dn_lower or cat in dn_lower:
            return cat
    if "laptop" in dn_lower or "notebook" in dn_lower:
        return "laptop"
    if "router" in dn_lower or "wi-fi" in dn_lower or "wifi" in dn_lower:
        return "router"
    if "panel pc" in dn_lower or "industrial" in dn_lower:
        return "industrial_pc"
    if "precision" in dn_lower and "dell" in dn_lower:
        return "laptop"
    return "unknown"


def build_device_slug(brand, model):
    return slugify(f"{brand}-{model}")


def build_part_slug(part_number, species):
    pn_slug = slugify(part_number)
    species_slug = slugify(species) if species else ""
    if species_slug:
        return f"{pn_slug}-{species_slug}"
    return pn_slug


def cmd_review(args):
    print("=== Curation Review: Loading verification input ===\n")

    limitations = []

    snapshot_path = Path(args.snapshot) if args.snapshot else VERIFIED_SNAPSHOT_PATH
    report_path = Path(args.report) if args.report else VERIFICATION_REPORT_PATH
    disagreement_path = (
        Path(args.disagreements) if args.disagreements else DISAGREEMENT_LOG_PATH
    )

    if snapshot_path.exists():
        candidates = read_jsonl(snapshot_path)
        print(f"  Verified snapshot: {snapshot_path}")
        print(f"  Records loaded: {len(candidates)}")
        if candidates:
            sample = candidates[0]
            print(f"  Sample fields: {list(sample.keys())}")
            statuses = {}
            for c in candidates:
                vs = c.get(
                    "verification_status",
                    c.get("verification", {}).get("status", "unknown"),
                )
                statuses[vs] = statuses.get(vs, 0) + 1
            print(f"  Verification status counts: {statuses}")
    else:
        print(f"  Verified snapshot NOT FOUND: {snapshot_path}")
        limitations.append(f"Brak verified snapshot: {snapshot_path}")
        candidates = []

    if report_path.exists():
        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()
        print(f"\n  Verification report: {report_path}")
        print(f"  Report length: {len(content)} chars")
        for line in content.split("\n"):
            stripped = line.strip().lower()
            if (
                "confirmed" in stripped
                or "disputed" in stripped
                or "rejected" in stripped
            ):
                print(f"    > {line.strip()}")
    else:
        print(f"\n  Verification report NOT FOUND: {report_path}")
        limitations.append(f"Brak verification report: {report_path}")

    if disagreement_path.exists():
        disagreements = read_jsonl(disagreement_path)
        print(f"\n  Disagreement log: {disagreement_path}")
        print(f"  Disagreement entries: {len(disagreements)}")
    else:
        print(f"\n  Disagreement log NOT FOUND: {disagreement_path}")
        limitations.append(f"Brak disagreement log: {disagreement_path}")
        disagreements = []

    catalog_devices = read_jsonl(DEVICES_PATH)
    catalog_parts = read_jsonl(PARTS_MASTER_PATH)
    catalog_links = read_jsonl(DEVICE_PARTS_PATH)
    print(f"\n=== Current canonical catalog ===")
    print(f"  devices.jsonl: {len(catalog_devices)} records")
    print(f"  parts_master.jsonl: {len(catalog_parts)} records")
    print(f"  device_parts.jsonl: {len(catalog_links)} records")

    if limitations:
        print(f"\n=== Limitations ===")
        for lim in limitations:
            print(f"  - {lim}")
        print(f"  Continuing with available data.")

    print(f"\n=== Review complete ===")
    print(f"  Candidates to curate: {len(candidates)}")
    print(f"  Disagreements to review: {len(disagreements)}")
    print(f"  Limitations: {len(limitations)}")
    return {
        "candidates": len(candidates),
        "disagreements": len(disagreements),
        "limitations": limitations,
    }


def cmd_align(args):
    print("=== Curation Align: Aligning candidates to canonical schemas ===\n")

    snapshot_path = Path(args.snapshot) if args.snapshot else VERIFIED_SNAPSHOT_PATH
    candidates = read_jsonl(snapshot_path) if snapshot_path.exists() else []

    if not candidates:
        print(
            "  No candidates found. Run with --fallback-test-db to use test_db.jsonl as input."
        )
        if args.fallback_test_db:
            test_db_path = RESULTS_DIR / "test_db.jsonl"
            if test_db_path.exists():
                candidates = read_jsonl(test_db_path)
                print(
                    f"  Loaded {len(candidates)} candidates from test_db.jsonl (fallback)"
                )
            else:
                print(f"  Fallback test_db.jsonl not found either. Exiting.")
                return

    catalog_devices = read_jsonl(DEVICES_PATH)
    catalog_parts = read_jsonl(PARTS_MASTER_PATH)
    catalog_links = read_jsonl(DEVICE_PARTS_PATH)

    existing_device_slugs = {d["device_slug"] for d in catalog_devices}
    existing_part_slugs = {p["part_slug"] for p in catalog_parts}
    existing_link_keys = {(l["device_slug"], l["part_slug"]) for l in catalog_links}

    aligned = []

    for idx, cand in enumerate(candidates):
        candidate_id = cand.get("candidate_id", f"candidate-{idx:04d}")
        device_raw = cand.get("device", "")
        part_name_raw = cand.get("part_name", "")
        part_number_raw = cand.get("part_number", "")
        confidence = cand.get("confidence", 0.0)
        yt_link = cand.get("yt_link", cand.get("source_video", ""))
        source_video = cand.get("source_video", "")

        verification = cand.get("verification", {})
        verified = verification.get("verified", None)
        observed_text = verification.get("observed_text", "")
        verification_status = cand.get("verification_status", "unknown")

        if verification_status == "unknown":
            if observed_text == "BRAK" or observed_text == "":
                verification_status = "rejected"
            elif verified is True:
                verification_status = "confirmed"
            elif verified is False:
                verification_status = "rejected"
            else:
                verification_status = "disputed"

        mpn_valid, reject_reason = looks_like_valid_mpn(part_number_raw)

        if not mpn_valid:
            verification_status = "rejected"
            cand["verification_status"] = verification_status

        brand = "Unknown"
        model = device_raw
        if " - " in device_raw:
            parts = device_raw.split(" - ", 1)
            brand = parts[0].strip()
            model = parts[1].strip()
        elif " " in device_raw:
            first_word = device_raw.split()[0]
            if first_word[0].isupper() and len(first_word) > 1:
                brand = first_word
                model = device_raw[len(first_word) :].strip() or device_raw

        device_slug = build_device_slug(brand, model)
        if not device_slug:
            device_slug = f"unknown-device-{idx:04d}"

        species = infer_species(part_name_raw, part_number_raw)
        genus = infer_genus(species)
        mounting = infer_mounting(part_name_raw, part_number_raw)
        device_category = infer_device_category(device_raw)

        part_slug = build_part_slug(part_number_raw, species)
        if not part_slug:
            part_slug = f"unknown-part-{idx:04d}"

        candidate_device = None
        if device_slug not in existing_device_slugs:
            candidate_device = {
                "device_slug": device_slug,
                "brand": brand,
                "model": model,
                "canonical_name": device_raw.strip(),
                "device_category": device_category,
                "description": f"Donor device from curation. Source: {source_video or yt_link}",
                "known_aliases": [],
                "serial_markers": [],
                "donor_rank": round(confidence * 0.9, 2),
                "teardown_url": yt_link if "youtube.com" in yt_link else "",
                "source_url": source_video or yt_link,
                "notes": "",
            }

        candidate_part = None
        if part_slug not in existing_part_slugs and mpn_valid:
            candidate_part = {
                "part_slug": part_slug,
                "part_number": part_number_raw.strip(),
                "normalized_part_number": normalize_part_number(part_number_raw),
                "part_name": part_name_raw.strip() or part_number_raw.strip(),
                "species": species,
                "genus": genus,
                "mounting": mounting,
                "value": "",
                "description": f"Candidate part from curation. Source: {source_video or yt_link}",
                "keywords": [
                    kw
                    for kw in (part_name_raw.lower().split() + species.lower().split())
                    if len(kw) > 2
                ],
                "part_aliases": [],
                "datasheet_url": "",
                "datasheet_file_id": "",
                "ipn": "",
                "category": species if species != "Unknown" else "",
                "parameters": {},
                "kicad_symbol": "",
                "kicad_footprint": "",
                "kicad_reference": "",
            }

        candidate_link = None
        link_key = (device_slug, part_slug)
        if link_key not in existing_link_keys and mpn_valid:
            candidate_link = {
                "device_slug": device_slug,
                "part_slug": part_slug,
                "source_url": source_video or yt_link,
                "quantity": 1,
                "designators": [],
                "confidence": round(confidence, 2),
                "stock_location": "",
                "evidence_url": yt_link if "youtube.com" in yt_link else "",
                "evidence_timecode": None,
            }

        aligned_entry = {
            "candidate_id": candidate_id,
            "source_record": cand,
            "verification_status": verification_status,
            "mpn_valid": mpn_valid,
            "reject_reason": reject_reason,
            "aligned_device": candidate_device,
            "aligned_part": candidate_part,
            "aligned_link": candidate_link,
            "device_slug": device_slug,
            "part_slug": part_slug,
            "is_new_device": device_slug not in existing_device_slugs,
            "is_new_part": part_slug not in existing_part_slugs,
            "is_new_link": link_key not in existing_link_keys,
        }

        aligned.append(aligned_entry)

        if candidate_device and device_slug not in existing_device_slugs:
            existing_device_slugs.add(device_slug)
        if candidate_part and part_slug not in existing_part_slugs:
            existing_part_slugs.add(part_slug)
        if candidate_link and link_key not in existing_link_keys:
            existing_link_keys.add(link_key)

    counts = {
        "total": len(aligned),
        "confirmed": sum(1 for a in aligned if a["verification_status"] == "confirmed"),
        "disputed": sum(1 for a in aligned if a["verification_status"] == "disputed"),
        "rejected": sum(1 for a in aligned if a["verification_status"] == "rejected"),
        "mpn_valid": sum(1 for a in aligned if a["mpn_valid"]),
        "mpn_invalid": sum(1 for a in aligned if not a["mpn_valid"]),
        "new_devices": sum(1 for a in aligned if a["is_new_device"]),
        "new_parts": sum(1 for a in aligned if a["is_new_part"]),
        "new_links": sum(1 for a in aligned if a["is_new_link"]),
    }

    print(f"  Candidates aligned: {counts['total']}")
    print(f"  Confirmed: {counts['confirmed']}")
    print(f"  Disputed: {counts['disputed']}")
    print(f"  Rejected: {counts['rejected']}")
    print(f"  Valid MPN: {counts['mpn_valid']}")
    print(f"  Invalid MPN: {counts['mpn_invalid']}")
    print(f"  New devices: {counts['new_devices']}")
    print(f"  New parts: {counts['new_parts']}")
    print(f"  New device-part links: {counts['new_links']}")

    aligned_path = REPORTS_DIR / "curation_aligned.jsonl"
    write_jsonl(aligned_path, aligned)
    print(f"\n  Aligned candidates saved to: {aligned_path}")

    return counts


def cmd_decide(args):
    print("=== Curation Decide: Applying curation decisions ===\n")

    aligned_path = REPORTS_DIR / "curation_aligned.jsonl"
    if not aligned_path.exists():
        print("  No aligned candidates found. Run 'align' first.")
        return

    aligned = read_jsonl(aligned_path)
    decisions = []

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    snapshot_path = Path(args.snapshot) if args.snapshot else VERIFIED_SNAPSHOT_PATH
    report_path = Path(args.report) if args.report else VERIFICATION_REPORT_PATH
    disagreement_path = (
        Path(args.disagreements) if args.disagreements else DISAGREEMENT_LOG_PATH
    )

    for entry in aligned:
        candidate_id = entry["candidate_id"]
        vs = entry["verification_status"]
        mpn_valid = entry["mpn_valid"]
        reject_reason = entry["reject_reason"]

        if vs == "rejected" or not mpn_valid:
            decision = "reject"
            if not mpn_valid:
                rationale = f"Invalid MPN ({reject_reason}): candidate part_number is not a valid manufacturer part number."
            else:
                rationale = f"Rejected in verification. Observed text indicates no valid part identification."
            if vs == "rejected" and mpn_valid:
                rationale = "Rejected in verification (observed_text=BRAK or verification=false)."

        elif vs == "confirmed":
            decision = "accept"
            rationale = "Confirmed in verification with valid MPN. Meets catalog-readiness criteria."

        elif vs == "disputed":
            decision = "defer"
            rationale = "Disputed in verification. Requires manual review before acceptance or rejection. Auto-deferred."

        else:
            decision = "defer"
            rationale = (
                f"Unknown verification status ({vs}). Deferred for manual review."
            )

        decisions.append(
            {
                "candidate_id": candidate_id,
                "decision": decision,
                "rationale": rationale,
                "verification_status": vs,
                "provenance": {
                    "verification_report": str(report_path),
                    "disagreement_ref": "",
                    "source_snapshot": str(snapshot_path),
                },
                "decided_at": now,
            }
        )

    counts = {
        "accept": sum(1 for d in decisions if d["decision"] == "accept"),
        "defer": sum(1 for d in decisions if d["decision"] == "defer"),
        "reject": sum(1 for d in decisions if d["decision"] == "reject"),
    }

    print(f"  Total decisions: {len(decisions)}")
    print(f"  Accept: {counts['accept']}")
    print(f"  Defer: {counts['defer']}")
    print(f"  Reject: {counts['reject']}")

    write_jsonl(CURATION_DECISIONS_PATH, decisions)
    print(f"\n  Decisions saved to: {CURATION_DECISIONS_PATH}")

    return counts


def cmd_apply(args):
    print("=== Curation Apply: Writing accepted candidates to canonical catalog ===\n")

    aligned_path = REPORTS_DIR / "curation_aligned.jsonl"
    if not aligned_path.exists():
        print("  No aligned candidates found. Run 'align' and 'decide' first.")
        return

    aligned = read_jsonl(aligned_path)
    decisions = read_jsonl(CURATION_DECISIONS_PATH)

    if not decisions:
        print("  No curation decisions found. Run 'decide' first.")
        return

    decision_map = {d["candidate_id"]: d["decision"] for d in decisions}

    catalog_devices = read_jsonl(DEVICES_PATH)
    catalog_parts = read_jsonl(PARTS_MASTER_PATH)
    catalog_links = read_jsonl(DEVICE_PARTS_PATH)

    existing_device_slugs = {d["device_slug"] for d in catalog_devices}
    existing_part_slugs = {p["part_slug"] for p in catalog_parts}
    existing_link_keys = {(l["device_slug"], l["part_slug"]) for l in catalog_links}

    new_devices = []
    new_parts = []
    new_links = []
    skipped = []

    for entry in aligned:
        cid = entry["candidate_id"]
        dec = decision_map.get(cid, "reject")

        if dec != "accept":
            skipped.append(
                {"candidate_id": cid, "decision": dec, "reason": "not accepted"}
            )
            continue

        dev = entry.get("aligned_device")
        part = entry.get("aligned_part")
        link = entry.get("aligned_link")

        if dev and dev["device_slug"] not in existing_device_slugs:
            catalog_devices.append(dev)
            new_devices.append(dev["device_slug"])
            existing_device_slugs.add(dev["device_slug"])

        if part and part["part_slug"] not in existing_part_slugs:
            catalog_parts.append(part)
            new_parts.append(part["part_slug"])
            existing_part_slugs.add(part["part_slug"])

        if link:
            lk = (link["device_slug"], link["part_slug"])
            if lk not in existing_link_keys:
                catalog_links.append(link)
                new_links.append(lk)
                existing_link_keys.add(lk)

    backup_dir = DATA_DIR / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    for src_path, name in [
        (DEVICES_PATH, "devices.jsonl"),
        (PARTS_MASTER_PATH, "parts_master.jsonl"),
        (DEVICE_PARTS_PATH, "device_parts.jsonl"),
    ]:
        if src_path.exists():
            import shutil

            shutil.copy2(src_path, backup_dir / f"{name}.pre-curation-{ts}")

    write_jsonl(DEVICES_PATH, catalog_devices)
    write_jsonl(PARTS_MASTER_PATH, catalog_parts)
    write_jsonl(DEVICE_PARTS_PATH, catalog_links)

    print(f"  New devices added: {len(new_devices)}")
    print(f"  New parts added: {len(new_parts)}")
    print(f"  New device-part links added: {len(new_links)}")
    print(f"  Skipped (not accepted): {len(skipped)}")
    print(f"  Backups saved in: {backup_dir}")
    print(f"\n  Catalog files updated:")
    print(f"    {DEVICES_PATH}: {len(catalog_devices)} records")
    print(f"    {PARTS_MASTER_PATH}: {len(catalog_parts)} records")
    print(f"    {DEVICE_PARTS_PATH}: {len(catalog_links)} records")

    return {
        "new_devices": len(new_devices),
        "new_parts": len(new_parts),
        "new_links": len(new_links),
    }


def cmd_validate(args):
    print("=== Curation Validate: Checking catalog cross-file consistency ===\n")

    catalog_devices = read_jsonl(DEVICES_PATH)
    catalog_parts = read_jsonl(PARTS_MASTER_PATH)
    catalog_links = read_jsonl(DEVICE_PARTS_PATH)

    errors = []
    warnings = []

    device_slugs = set()
    device_slug_counts = {}
    for d in catalog_devices:
        slug = d.get("device_slug", "")
        if not slug:
            errors.append(f"Device missing device_slug: {d.get('canonical_name', '?')}")
        else:
            device_slug_counts[slug] = device_slug_counts.get(slug, 0) + 1
        device_slugs.add(slug)

    for slug, count in device_slug_counts.items():
        if count > 1:
            errors.append(f"Duplicate device_slug: {slug} ({count} occurrences)")

    part_slugs = set()
    part_slug_counts = {}
    for p in catalog_parts:
        slug = p.get("part_slug", "")
        if not slug:
            errors.append(f"Part missing part_slug: {p.get('part_number', '?')}")
        else:
            part_slug_counts[slug] = part_slug_counts.get(slug, 0) + 1
        part_slugs.add(slug)

    for slug, count in part_slug_counts.items():
        if count > 1:
            errors.append(f"Duplicate part_slug: {slug} ({count} occurrences)")

    for p in catalog_parts:
        pn = p.get("part_number", "")
        if not pn:
            warnings.append(f"Part {p.get('part_slug', '?')} has empty part_number")

    for idx, link in enumerate(catalog_links):
        d_slug = link.get("device_slug", "")
        p_slug = link.get("part_slug", "")

        if d_slug and d_slug not in device_slugs:
            errors.append(
                f"device_parts row {idx}: device_slug '{d_slug}' not found in devices.jsonl"
            )
        if p_slug and p_slug not in part_slugs:
            errors.append(
                f"device_parts row {idx}: part_slug '{p_slug}' not found in parts_master.jsonl"
            )

    link_keys = set()
    for link in catalog_links:
        key = (link.get("device_slug", ""), link.get("part_slug", ""))
        if key in link_keys:
            errors.append(f"Duplicate device_parts link: {key}")
        link_keys.add(key)

    print(f"  Devices: {len(catalog_devices)}")
    print(f"  Parts: {len(catalog_parts)}")
    print(f"  Device-parts: {len(catalog_links)}")
    print(f"  Errors: {len(errors)}")
    print(f"  Warnings: {len(warnings)}")

    if errors:
        print(f"\n  ERRORS:")
        for e in errors[:20]:
            print(f"    - {e}")
        if len(errors) > 20:
            print(f"    ... and {len(errors) - 20} more")

    if warnings:
        print(f"\n  WARNINGS:")
        for w in warnings[:10]:
            print(f"    - {w}")
        if len(warnings) > 10:
            print(f"    ... and {len(warnings) - 10} more")

    if not errors and not warnings:
        print(f"\n  Catalog validation PASSED. No errors or warnings.")

    status = "pass" if not errors else "fail"
    print(f"\n  Validation status: {status}")

    return {"status": status, "errors": len(errors), "warnings": len(warnings)}


def cmd_report(args):
    print("=== Curation Report: Generating curation report ===\n")

    decisions = read_jsonl(CURATION_DECISIONS_PATH)
    aligned = (
        read_jsonl(REPORTS_DIR / "curation_aligned.jsonl")
        if (REPORTS_DIR / "curation_aligned.jsonl").exists()
        else []
    )

    if not decisions:
        print("  No curation decisions found. Run 'decide' first.")
        return

    snapshot_path = Path(args.snapshot) if args.snapshot else VERIFIED_SNAPSHOT_PATH
    report_path = Path(args.report) if args.report else VERIFICATION_REPORT_PATH
    disagreement_path = (
        Path(args.disagreements) if args.disagreements else DISAGREEMENT_LOG_PATH
    )

    total = len(decisions)
    accepted = [d for d in decisions if d["decision"] == "accept"]
    deferred = [d for d in decisions if d["decision"] == "defer"]
    rejected = [d for d in decisions if d["decision"] == "reject"]

    accepted_confirmed = [
        d for d in accepted if d["verification_status"] == "confirmed"
    ]
    accepted_disputed = [d for d in accepted if d["verification_status"] == "disputed"]
    deferred_disputed = [d for d in deferred if d["verification_status"] == "disputed"]
    rejected_rejected = [d for d in rejected if d["verification_status"] == "rejected"]

    key_cases = []
    for d in accepted_disputed:
        key_cases.append(
            f"- **ACCEPTED (disputed)**: {d['candidate_id']} — {d['rationale']}"
        )
    for d in deferred[:10]:
        key_cases.append(f"- **DEFERRED**: {d['candidate_id']} — {d['rationale']}")

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    report_lines = [
        "# Curation Report",
        "",
        f"Generated: {now}",
        f"Pack: pack-project13-curation-01",
        "",
        "## Counts",
        "",
        f"| Decision | Count |",
        f"|----------|-------|",
        f"| Accepted | {len(accepted)} |",
        f"| Deferred | {len(deferred)} |",
        f"| Rejected | {len(rejected)} |",
        f"| **Total** | {total} |",
        "",
        "### Breakdown by verification status",
        "",
        f"| Verification Status | Accepted | Deferred | Rejected |",
        f"|---------------------|----------|----------|----------|",
        f"| confirmed | {len(accepted_confirmed)} | {len([d for d in deferred if d['verification_status'] == 'confirmed'])} | {len([d for d in rejected if d['verification_status'] == 'confirmed'])} |",
        f"| disputed | {len(accepted_disputed)} | {len(deferred_disputed)} | {len([d for d in rejected if d['verification_status'] == 'disputed'])} |",
        f"| rejected | {len([d for d in accepted if d['verification_status'] == 'rejected'])} | {len([d for d in deferred if d['verification_status'] == 'rejected'])} | {len(rejected_rejected)} |",
        "",
        "## Key cases requiring review",
        "",
    ]

    if key_cases:
        report_lines.extend(key_cases)
    else:
        report_lines.append(
            "No special cases — all accepted candidates were confirmed in verification."
        )

    report_lines.extend(
        [
            "",
            "## Provenance",
            "",
            f"- Verification report: `{report_path}`",
            f"- Disagreement log: `{disagreement_path}`",
            f"- Source snapshot: `{snapshot_path}`",
            f"- Curation decisions: `{CURATION_DECISIONS_PATH}`",
            "",
            "## Handoff to export",
            "",
            "After merge of this curation PR, the downstream export pack is safe to run:",
            "",
            "```bash",
            "python3 PROJEKTY/13_baza_czesci_recykling/scripts/build_catalog_artifacts.py export-all",
            "python3 PROJEKTY/13_baza_czesci_recykling/scripts/build_catalog_artifacts.py validate",
            "```",
            "",
        ]
    )

    limitations = []
    if not report_path.exists():
        limitations.append(f"Verification report not found: {report_path}")
    if not disagreement_path.exists():
        limitations.append(f"Disagreement log not found: {disagreement_path}")
    if not snapshot_path.exists():
        limitations.append(f"Verified snapshot not found: {snapshot_path}")

    if limitations:
        report_lines.extend(
            [
                "## Limitations",
                "",
            ]
        )
        for lim in limitations:
            report_lines.append(f"- {lim}")
        report_lines.append("")

    report_content = "\n".join(report_lines)
    CURATION_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CURATION_REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report_content)

    print(f"  Curation report saved to: {CURATION_REPORT_PATH}")
    print(
        f"  Total: {total}, Accepted: {len(accepted)}, Deferred: {len(deferred)}, Rejected: {len(rejected)}"
    )
    print(f"  Key cases: {len(key_cases)}")

    return {
        "total": total,
        "accepted": len(accepted),
        "deferred": len(deferred),
        "rejected": len(rejected),
    }


def cmd_dry_run(args):
    print(
        "=== Curation Dry-Run: align + decide + validate + report (no catalog writes) ===\n"
    )

    align_args = argparse.Namespace(
        snapshot=args.snapshot,
        fallback_test_db=args.fallback_test_db,
    )
    align_counts = cmd_align(align_args)

    decide_args = argparse.Namespace(
        snapshot=args.snapshot,
        report=args.report,
        disagreements=args.disagreements,
    )
    decide_counts = cmd_decide(decide_args)

    validate_result = cmd_validate(argparse.Namespace())

    report_result = cmd_report(decide_args)

    print("\n=== Dry-Run Summary ===")
    print(f"  Aligned: {align_counts}")
    print(f"  Decisions: {decide_counts}")
    print(f"  Validation: {validate_result}")
    print(f"  Report: {report_result}")
    print(f"\n  NOTE: Canonical catalog files were NOT modified (dry-run mode).")
    print(f"  To apply accepted candidates, run: curate_candidates.py apply")


def main():
    parser = argparse.ArgumentParser(
        description="Curation execution surface for pack-project13-curation-01",
    )
    sub = parser.add_subparsers(dest="command", help="Available commands")

    for name, help_text in [
        ("review", "Load and summarize verification input"),
        ("align", "Align candidates to canonical catalog schemas"),
        (
            "decide",
            "Apply curation decisions (auto for confirmed/rejected, defer for disputed)",
        ),
        ("apply", "Write accepted candidates into canonical catalog files"),
        ("validate", "Validate catalog cross-file consistency"),
        ("report", "Generate curation_report.md"),
        ("dry-run", "Run align+decide+validate+report without writing to catalog"),
    ]:
        sp = sub.add_parser(name, help=help_text)
        sp.add_argument(
            "--snapshot",
            default=None,
            help="Path to verified snapshot (default: test_db_verified.jsonl)",
        )
        sp.add_argument(
            "--report",
            default=None,
            help="Path to verification report (default: verification_report.md)",
        )
        sp.add_argument(
            "--disagreements",
            default=None,
            help="Path to disagreement log (default: verification_disagreements.jsonl)",
        )
        if name in ("align", "dry-run"):
            sp.add_argument(
                "--fallback-test-db",
                action="store_true",
                help="Use test_db.jsonl if verified snapshot not found",
            )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    commands = {
        "review": cmd_review,
        "align": cmd_align,
        "decide": cmd_decide,
        "apply": cmd_apply,
        "validate": cmd_validate,
        "report": cmd_report,
        "dry-run": cmd_dry_run,
    }

    result = commands[args.command](args)


if __name__ == "__main__":
    main()
