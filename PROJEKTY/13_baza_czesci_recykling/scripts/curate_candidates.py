#!/usr/bin/env python3
"""
Execution surface for pack-project13-curation-01.

Curate verified candidates into canonical catalog schemas with
explicit accept/defer/reject decisions, review queue, and export gate.

Commands:
 review — Load and summarize verification input (snapshot + report + disagreements + status resolution)
 align — Align each candidate to canonical catalog schemas
 decide — Apply curation decisions (auto + triage-informed for disputed)
 review-queue — Generate explicit review queue from curation decisions
 record-review — Record a human review decision for a pending candidate (approved/rejected/defer)
 list-pending — List pending_human_approval cases with batch annotation and export to JSON
 review-status — Show current review status summary and remaining pending entries
 export-gate — Check whether export is allowed; generate export gate packet
 apply — Write accepted candidates into canonical catalog files
 validate — Validate catalog cross-file consistency after apply
 report — Generate curation_report.md and curation_decisions.jsonl
 dry-run — Run align+decide+review-queue+export-gate+validate+report without writing to catalog
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
REVIEW_QUEUE_PATH = REPORTS_DIR / "curation_review_queue.jsonl"
EXPORT_GATE_PACKET_PATH = REPORTS_DIR / "export_gate_packet.json"

HUMAN_REVIEW_LEDGER_PATH = REPORTS_DIR / "human_review_ledger.jsonl"

STATUS_RESOLUTION_PACKET_PATH = REPORTS_DIR / "status_resolution_packet.json"

EXPORT_GATE_POLICY = {
    "can_export_if": [
        "all accepted candidates have review_status=approved",
        "no deferred candidates remain in accept queue",
        "catalog validation passes (no duplicate slugs, no broken links)",
        "at least one human review approval recorded",
    ],
    "cannot_export_if": [
        "deferred candidates exist that have not been explicitly resolved",
        "accepted candidates still have review_status=pending",
        "catalog validation has errors",
        "no human review approval recorded",
    ],
}

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


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


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


def load_verified_snapshot_with_triage(snapshot_path):
    triage_map = {}
    if snapshot_path.exists():
        for idx, rec in enumerate(read_jsonl(snapshot_path)):
            cid = rec.get("candidate_id", f"candidate-{idx:04d}")
            triage = rec.get("triage", None)
            if triage:
                triage_map[cid] = triage
    return triage_map


def cmd_decide(args):
    print("=== Curation Decide: Applying curation decisions ===\n")

    aligned_path = REPORTS_DIR / "curation_aligned.jsonl"
    if not aligned_path.exists():
        print(" No aligned candidates found. Run 'align' first.")
        return

    aligned = read_jsonl(aligned_path)
    decisions = []

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    snapshot_path = Path(args.snapshot) if args.snapshot else VERIFIED_SNAPSHOT_PATH
    report_path = Path(args.report) if args.report else VERIFICATION_REPORT_PATH
    disagreement_path = (
        Path(args.disagreements) if args.disagreements else DISAGREEMENT_LOG_PATH
    )

    triage_map = load_verified_snapshot_with_triage(snapshot_path)
    if triage_map:
        print(f" Loaded triage data for {len(triage_map)} disputed candidates from verified snapshot")

    triage_counts = {"likely_confirmed_promoted": 0, "threshold_tuning_rejected": 0, "ocr_needed_deferred": 0, "manual_review_deferred": 0, "disputed_no_triage_deferred": 0}

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
            triage = triage_map.get(candidate_id, None)
            triage_category = triage.get("triage_category", "unknown") if triage else "unknown"

            if triage_category == "likely_confirmed":
                decision = "accept"
                rationale = f"Disputed in verification but triage=likely_confirmed ({', '.join(triage.get('triage_indicators', []))}). Auto-promoted to accept per triage recommendation."
                triage_counts["likely_confirmed_promoted"] += 1
            elif triage_category == "threshold_tuning":
                decision = "reject"
                rationale = f"Disputed in verification, triage=threshold_tuning ({', '.join(triage.get('triage_indicators', []))}). Rejected: part_number should be recategorized by improved MPN heuristics."
                triage_counts["threshold_tuning_rejected"] += 1
            elif triage_category == "ocr_needed":
                decision = "defer"
                rationale = f"Disputed in verification, triage=ocr_needed ({', '.join(triage.get('triage_indicators', []))}). Deferred: requires OCR frame check (GEMINI_API_KEY) to resolve."
                triage_counts["ocr_needed_deferred"] += 1
            elif triage_category == "manual_review":
                decision = "defer"
                rationale = f"Disputed in verification, triage=manual_review ({', '.join(triage.get('triage_indicators', []))}). Deferred: human reviewer needed to assess part number validity."
                triage_counts["manual_review_deferred"] += 1
            else:
                decision = "defer"
                rationale = f"Disputed in verification (no triage data). Deferred for manual review."
                triage_counts["disputed_no_triage_deferred"] += 1

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
                "triage_category": triage_map.get(candidate_id, {}).get("triage_category", "") if candidate_id in triage_map else "",
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

    print(f" Total decisions: {len(decisions)}")
    print(f" Accept: {counts['accept']}")
    print(f" Defer: {counts['defer']}")
    print(f" Reject: {counts['reject']}")

    if triage_map:
        print(f"\n Triage-informed disputed breakdown:")
        print(f"   likely_confirmed -> accept: {triage_counts['likely_confirmed_promoted']}")
        print(f"   threshold_tuning -> reject: {triage_counts['threshold_tuning_rejected']}")
        print(f"   ocr_needed -> defer: {triage_counts['ocr_needed_deferred']}")
        print(f"   manual_review -> defer: {triage_counts['manual_review_deferred']}")
        print(f"   no_triage -> defer: {triage_counts['disputed_no_triage_deferred']}")

    write_jsonl(CURATION_DECISIONS_PATH, decisions)
    print(f"\n Decisions saved to: {CURATION_DECISIONS_PATH}")

    return counts


def cmd_review_queue(args):
    print("=== Curation Review Queue: Generating explicit review queue ===\n")

    decisions = read_jsonl(CURATION_DECISIONS_PATH)
    if not decisions:
        print(" No curation decisions found. Run 'decide' first.")
        return {"queue_entries": 0}

    snapshot_path = Path(args.snapshot) if args.snapshot else VERIFIED_SNAPSHOT_PATH
    candidates = read_jsonl(snapshot_path) if snapshot_path.exists() else []

    cand_map = {}
    for idx, rec in enumerate(candidates):
        cid = rec.get("candidate_id", f"candidate-{idx:04d}")
        cand_map[cid] = rec

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    queue_entries = []

    for d in decisions:
        cid = d["candidate_id"]
        decision = d["decision"]
        vs = d.get("verification_status", "unknown")
        tc = d.get("triage_category", "")
        rationale = d.get("rationale", "")

        rec = cand_map.get(cid, {})
        part_number = rec.get("part_number", "")
        part_name = rec.get("part_name", "")
        device = rec.get("device", "")
        triage = rec.get("triage", {})
        status_resolution = rec.get("status_resolution", {})
        sr_policy = status_resolution.get("policy", "")

        if decision == "accept":
            if vs == "confirmed" and tc != "likely_confirmed":
                review_status = "auto_approved"
                review_note = "Confirmed by verification; no additional review needed"
            elif tc == "likely_confirmed" or sr_policy == "likely_confirmed_promote_v2":
                review_status = "pending_human_approval"
                review_note = "Auto-promoted from disputed (likely_confirmed) per status resolution policy v2; requires human approval before export"
            else:
                review_status = "pending_human_approval"
                review_note = f"Accepted ({vs}, triage={tc}); requires human approval before export"
        elif decision == "defer":
            review_status = "deferred"
            review_note = f"Deferred ({tc}): {rationale}"
        elif decision == "reject":
            review_status = "auto_rejected"
            review_note = f"Rejected ({vs}): {rationale}"
        else:
            review_status = "unknown"
            review_note = f"Unknown decision: {decision}"

        queue_entries.append({
            "candidate_id": cid,
            "part_number": part_number,
            "part_name": part_name,
            "device": device,
            "curation_decision": decision,
            "verification_status": vs,
            "triage_category": tc,
            "status_resolution_policy": sr_policy,
            "review_status": review_status,
            "review_note": review_note,
            "rationale": rationale,
            "reviewed_by": None,
            "reviewed_at": None,
            "queue_added_at": now,
        })

    pending = [e for e in queue_entries if e["review_status"] == "pending_human_approval"]
    auto_approved = [e for e in queue_entries if e["review_status"] == "auto_approved"]
    auto_rejected = [e for e in queue_entries if e["review_status"] == "auto_rejected"]
    deferred = [e for e in queue_entries if e["review_status"] == "deferred"]

    print(f" Review queue entries: {len(queue_entries)}")
    print(f"  auto_approved: {len(auto_approved)}")
    print(f"  pending_human_approval: {len(pending)}")
    print(f"  auto_rejected: {len(auto_rejected)}")
    print(f"  deferred: {len(deferred)}")

    if pending:
        print(f"\n Candidates pending human approval:")
        for e in pending:
            print(f"  - {e['part_number']} ({e['part_name']}, {e['device']}) — {e['review_note']}")

    if deferred:
        print(f"\n Deferred candidates (not in export queue):")
        for e in deferred:
            print(f"  - {e['part_number']} ({e['part_name']}, {e['device']}) — {e['review_note']}")

    write_jsonl(REVIEW_QUEUE_PATH, queue_entries)
    print(f"\n Review queue saved to: {REVIEW_QUEUE_PATH}")

    print(f"\n=== Review Queue complete ===")
    return {
        "queue_entries": len(queue_entries),
        "auto_approved": len(auto_approved),
        "pending_human_approval": len(pending),
        "auto_rejected": len(auto_rejected),
        "deferred": len(deferred),
    }


VALID_REVIEW_DECISIONS = ("approved", "rejected", "defer")

REVIEW_BATCH_RULES = [
    {
        "batch": "A",
        "name": "Komponenty laptopowe (Lenovo + ASUS + Compal)",
        "match_devices": [
            "Lenovo Laptop",
            "ASUS K52F",
            "Compal LA-G021P",
        ],
        "recommended_mode": "per-batch",
    },
    {
        "batch": "B",
        "name": "Komponenty z innych urzadzen (Samsung TV, Electrolux, vintage, LED, Gigabyte)",
        "match_devices": [
            "Samsung UE50MU6102K",
            "Electrolux EnergySaver",
            "Various Vintage Electronics",
            "DesignLight LDF-12V16W",
            "Gigabyte Graphics Card",
        ],
        "recommended_mode": "per-candidate",
    },
    {
        "batch": "C",
        "name": "IC z e-waste + desktop",
        "match_devices": [
            "Unknown Electronic Waste",
            "Generic Desktop Motherboard (Socket 939)",
        ],
        "recommended_mode": "per-batch",
    },
]


def assign_batch(device):
    for rule in REVIEW_BATCH_RULES:
        if device in rule["match_devices"]:
            return rule["batch"]
    return "unbatched"


def cmd_record_review(args):
    print("=== Curation Record Review: Recording human review decision ===\n")

    candidate_id = args.candidate_id
    decision = args.decision
    reviewed_by = args.reviewed_by
    note = args.note or ""

    if decision not in VALID_REVIEW_DECISIONS:
        print(f" ERROR: Invalid decision '{decision}'. Must be one of: {', '.join(VALID_REVIEW_DECISIONS)}")
        return {"status": "error", "reason": f"invalid_decision:{decision}"}

    if not reviewed_by:
        print(f" ERROR: --reviewed-by is required. No fictional reviewers allowed.")
        return {"status": "error", "reason": "missing_reviewed_by"}

    review_queue = read_jsonl(REVIEW_QUEUE_PATH)
    if not review_queue:
        print(f" No review queue found. Run 'review-queue' first.")
        return {"status": "error", "reason": "no_review_queue"}

    target_entry = None
    target_idx = None
    for idx, entry in enumerate(review_queue):
        if entry.get("candidate_id") == candidate_id:
            target_entry = entry
            target_idx = idx
            break

    if target_entry is None:
        print(f" ERROR: candidate_id '{candidate_id}' not found in review queue.")
        available = [e["candidate_id"] for e in review_queue if e.get("review_status") == "pending_human_approval"]
        if available:
            print(f" Candidates pending human approval: {', '.join(available)}")
        return {"status": "error", "reason": f"candidate_not_found:{candidate_id}"}

    current_review_status = target_entry.get("review_status", "")
    if current_review_status not in ("pending_human_approval", "deferred"):
        print(f" WARNING: candidate '{candidate_id}' has review_status='{current_review_status}', not 'pending_human_approval' or 'deferred'.")
        print(f" Recording review anyway, but this may not change export gate behavior.")

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    ledger_entry = {
        "ledger_id": f"review-{candidate_id}-{now.replace(':', '-').replace('T', '-').rstrip('Z')}",
        "candidate_id": candidate_id,
        "part_number": target_entry.get("part_number", ""),
        "part_name": target_entry.get("part_name", ""),
        "device": target_entry.get("device", ""),
        "previous_review_status": current_review_status,
        "review_decision": decision,
        "reviewed_by": reviewed_by,
        "reviewed_at": now,
        "note": note,
        "curation_decision_before": target_entry.get("curation_decision", ""),
        "verification_status": target_entry.get("verification_status", ""),
        "triage_category": target_entry.get("triage_category", ""),
    }

    append_jsonl(HUMAN_REVIEW_LEDGER_PATH, [ledger_entry])

    if decision == "approved":
        review_queue[target_idx]["review_status"] = "approved"
        review_queue[target_idx]["reviewed_by"] = reviewed_by
        review_queue[target_idx]["reviewed_at"] = now
        if note:
            review_queue[target_idx]["review_note"] = (
                review_queue[target_idx].get("review_note", "") + f" | Human review: {note}"
            )
    elif decision == "rejected":
        review_queue[target_idx]["review_status"] = "human_rejected"
        review_queue[target_idx]["reviewed_by"] = reviewed_by
        review_queue[target_idx]["reviewed_at"] = now
        review_queue[target_idx]["curation_decision"] = "reject"
        if note:
            review_queue[target_idx]["review_note"] = (
                review_queue[target_idx].get("review_note", "") + f" | Human review rejection: {note}"
            )
    elif decision == "defer":
        review_queue[target_idx]["review_status"] = "deferred"
        review_queue[target_idx]["reviewed_by"] = reviewed_by
        review_queue[target_idx]["reviewed_at"] = now
        if note:
            review_queue[target_idx]["review_note"] = (
                review_queue[target_idx].get("review_note", "") + f" | Human review defer: {note}"
            )

    write_jsonl(REVIEW_QUEUE_PATH, review_queue)

    print(f" Recorded review for: {candidate_id}")
    print(f" Part: {target_entry.get('part_number', '')} ({target_entry.get('part_name', '')})")
    print(f" Device: {target_entry.get('device', '')}")
    print(f" Decision: {decision}")
    print(f" Reviewed by: {reviewed_by}")
    print(f" Reviewed at: {now}")
    if note:
        print(f" Note: {note}")
    print(f" Previous review_status: {current_review_status}")
    print(f" New review_status: {review_queue[target_idx]['review_status']}")
    print(f"\n Ledger entry saved to: {HUMAN_REVIEW_LEDGER_PATH}")
    print(f" Review queue updated: {REVIEW_QUEUE_PATH}")

    remaining_pending = sum(
        1 for e in review_queue if e.get("review_status") == "pending_human_approval"
    )
    total_approved = sum(
        1 for e in review_queue if e.get("review_status") == "approved"
    )
    total_human_rejected = sum(
        1 for e in review_queue if e.get("review_status") == "human_rejected"
    )
    print(f"\n Remaining pending_human_approval: {remaining_pending}")
    print(f" Total approved (human): {total_approved}")
    print(f" Total human-rejected: {total_human_rejected}")

    if remaining_pending > 0:
        print(f"\n To review remaining candidates:")
        pending_ids = [e["candidate_id"] for e in review_queue if e.get("review_status") == "pending_human_approval"]
        for pid in pending_ids:
            entry = next(e for e in review_queue if e["candidate_id"] == pid)
            print(f"   python3 scripts/curate_candidates.py record-review --candidate-id {pid} --decision approved --reviewed-by <YOUR_NAME>")
    else:
        print(f"\n All pending_human_approval entries have been reviewed!")
        print(f" Re-run export gate to check if gate opens:")
        print(f"   python3 scripts/curate_candidates.py export-gate")

    return {
        "status": "recorded",
        "candidate_id": candidate_id,
        "review_decision": decision,
        "remaining_pending": remaining_pending,
    }


def cmd_list_pending(args):
    print("=== Curation List Pending: Pending human approval cases with batch annotation ===\n")

    review_queue = read_jsonl(REVIEW_QUEUE_PATH)
    if not review_queue:
        print(" No review queue found. Run 'review-queue' first.")
        return {"pending": 0}

    pending = [e for e in review_queue if e.get("review_status") == "pending_human_approval"]

    if not pending:
        print(" No pending_human_approval entries found.")
        return {"pending": 0}

    for e in pending:
        e["_batch"] = assign_batch(e.get("device", ""))

    batch_order = {r["batch"]: i for i, r in enumerate(REVIEW_BATCH_RULES)}
    batch_order["unbatched"] = len(REVIEW_BATCH_RULES)
    pending.sort(key=lambda e: (batch_order.get(e["_batch"], 99), e["candidate_id"]))

    batch_groups = {}
    for e in pending:
        b = e["_batch"]
        if b not in batch_groups:
            batch_groups[b] = []
        batch_groups[b].append(e)

    print(f" Total pending_human_approval: {len(pending)}")
    print(f" Batches: {len(batch_groups)}")
    print()

    for batch_id in sorted(batch_groups.keys(), key=lambda b: batch_order.get(b, 99)):
        entries = batch_groups[batch_id]
        rule = next((r for r in REVIEW_BATCH_RULES if r["batch"] == batch_id), None)
        batch_name = rule["name"] if rule else "Unbatched"
        recommended_mode = rule["recommended_mode"] if rule else "per-candidate"
        print(f" Batch {batch_id}: {batch_name} ({len(entries)} cases, recommended: {recommended_mode})")
        for e in entries:
            print(f"  {e['candidate_id']} | {e.get('part_number', '')} | {e.get('part_name', '')} | {e.get('device', '')}")
        print()

    pending_export_path = REPORTS_DIR / "pending_human_approval_list.json"
    export_data = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_pending": len(pending),
        "batch_rules": REVIEW_BATCH_RULES,
        "pending_entries": [
            {
                "candidate_id": e["candidate_id"],
                "part_number": e.get("part_number", ""),
                "part_name": e.get("part_name", ""),
                "device": e.get("device", ""),
                "verification_status": e.get("verification_status", ""),
                "triage_category": e.get("triage_category", ""),
                "status_resolution_policy": e.get("status_resolution_policy", ""),
                "review_note": e.get("review_note", ""),
                "batch": e["_batch"],
            }
            for e in pending
        ],
    }
    write_json(pending_export_path, export_data)
    print(f" Pending list exported to: {pending_export_path}")

    return {"pending": len(pending), "batches": len(batch_groups)}


def cmd_review_status(args):
    print("=== Curation Review Status: Current review state summary ===\n")

    review_queue = read_jsonl(REVIEW_QUEUE_PATH)
    if not review_queue:
        print(" No review queue found. Run 'review-queue' first.")
        return {"status": "no_queue"}

    ledger = read_jsonl(HUMAN_REVIEW_LEDGER_PATH)

    status_counts = {}
    for entry in review_queue:
        rs = entry.get("review_status", "unknown")
        status_counts[rs] = status_counts.get(rs, 0) + 1

    print(f" Review queue entries: {len(review_queue)}")
    print(f" Review status breakdown:")
    for rs, count in sorted(status_counts.items()):
        print(f"   {rs}: {count}")

    pending = [e for e in review_queue if e.get("review_status") == "pending_human_approval"]
    if pending:
        print(f"\n Pending human approval ({len(pending)}):")
        for e in pending:
            print(f"   - {e['candidate_id']}: {e.get('part_number', '')} ({e.get('part_name', '')}, {e.get('device', '')})")
            print(f"     Note: {e.get('review_note', '')}")
    else:
        print(f"\n No pending_human_approval entries remaining.")

    approved = [e for e in review_queue if e.get("review_status") == "approved"]
    if approved:
        print(f"\n Human-approved ({len(approved)}):")
        for e in approved:
            print(f"   - {e['candidate_id']}: {e.get('part_number', '')} | reviewed_by={e.get('reviewed_by', 'N/A')}, reviewed_at={e.get('reviewed_at', 'N/A')}")

    deferred = [e for e in review_queue if e.get("review_status") == "deferred"]
    human_rejected = [e for e in review_queue if e.get("review_status") == "human_rejected"]
    if human_rejected:
        print(f"\n Human-rejected ({len(human_rejected)}):")
        for e in human_rejected:
            print(f"   - {e['candidate_id']}: {e.get('part_number', '')} | reviewed_by={e.get('reviewed_by', 'N/A')}")

    if ledger:
        print(f"\n Review ledger entries: {len(ledger)}")
        print(f" Ledger file: {HUMAN_REVIEW_LEDGER_PATH}")
        reviewers = set(e.get("reviewed_by", "") for e in ledger if e.get("reviewed_by"))
        print(f" Reviewers who recorded decisions: {', '.join(sorted(reviewers))}")
    else:
        print(f"\n No review ledger entries yet.")
        print(f" To record a review:")
        print(f"   python3 scripts/curate_candidates.py record-review --candidate-id <ID> --decision approved --reviewed-by <YOUR_NAME>")

    all_resolved = len(pending) == 0 and len(deferred) == 0
    gate_ready = all_resolved and len(approved) > 0

    print(f"\n Export gate readiness:")
    if gate_ready:
        print(f"   READY: No pending approvals, no unresolved deferrals, {len(approved)} human approvals recorded.")
        print(f"   Run: python3 scripts/curate_candidates.py export-gate")
    else:
        if pending:
            print(f"   NOT READY: {len(pending)} candidates still pending human approval.")
        if deferred:
            print(f"   NOT READY: {len(deferred)} candidates still deferred and block export gate OPEN.")
        if not approved:
            print(f"   NOT READY: No human approvals recorded yet.")
        print(f"   Record reviews with: python3 scripts/curate_candidates.py record-review --candidate-id <ID> --decision <approved|rejected|defer> --reviewed-by <YOUR_NAME>")

    return {
        "queue_entries": len(review_queue),
        "status_counts": status_counts,
        "pending_human_approval": len(pending),
        "approved": len(approved),
        "human_rejected": len(human_rejected),
        "ledger_entries": len(ledger),
        "gate_ready": gate_ready,
    }


def cmd_export_gate(args):
    print("=== Curation Export Gate: Checking export readiness ===\n")

    decisions = read_jsonl(CURATION_DECISIONS_PATH)
    review_queue = read_jsonl(REVIEW_QUEUE_PATH)
    snapshot_path = Path(args.snapshot) if args.snapshot else VERIFIED_SNAPSHOT_PATH

    status_resolution = {}
    if STATUS_RESOLUTION_PACKET_PATH.exists():
        with open(STATUS_RESOLUTION_PACKET_PATH, "r", encoding="utf-8") as f:
            status_resolution = json.load(f)

    gate_checks = []
    blockers = []
    warnings = []

    pending_approval = [e for e in review_queue if e.get("review_status") == "pending_human_approval"]
    if not pending_approval:
        gate_checks.append(("no_pending_approvals", True, "No candidates pending human approval"))
    else:
        pns = [e["part_number"] for e in pending_approval]
        gate_checks.append(("no_pending_approvals", False, f"{len(pending_approval)} candidates pending human approval: {', '.join(pns)}"))
        blockers.append(f"{len(pending_approval)} accepted candidates still pending human approval: {', '.join(pns)}")

    deferred_entries = [e for e in review_queue if e.get("review_status") == "deferred"]
    if deferred_entries:
        pns = [e["part_number"] for e in deferred_entries]
        gate_checks.append(("no_unresolved_deferrals", False, f"{len(deferred_entries)} deferred candidates: {', '.join(pns)}"))
        blockers.append(f"{len(deferred_entries)} deferred candidates still unresolved: {', '.join(pns)}")
    else:
        gate_checks.append(("no_unresolved_deferrals", True, "No unresolved deferrals"))

    validate_result = cmd_validate(argparse.Namespace())
    check_3_pass = validate_result.get("status") == "pass"
    if check_3_pass:
        gate_checks.append(("catalog_validation_passes", True, "Catalog validation passed"))
    else:
        gate_checks.append(("catalog_validation_passes", False, f"Catalog validation failed: {validate_result.get('errors', 0)} errors"))
        blockers.append(f"Catalog validation failed with {validate_result.get('errors', 0)} errors")

    human_approvals = [e for e in review_queue if e.get("reviewed_by") is not None and e.get("review_status") == "approved"]
    if human_approvals:
        gate_checks.append(("human_review_recorded", True, f"{len(human_approvals)} human reviews recorded (approved)"))
    else:
        detail = "No human review approval recorded yet"
        if pending_approval:
            detail = "No human review approval recorded for pending candidates"
        gate_checks.append(("human_review_recorded", False, detail))
        blockers.append(detail)

    if status_resolution:
        ocr_remaining = len(status_resolution.get("ocr_needed_remaining", []))
        manual_remaining = len(status_resolution.get("manual_review_remaining", []))
        if ocr_remaining > 0:
            warnings.append(f"{ocr_remaining} records still deferred by verification (ocr_needed)")
        if manual_remaining > 0:
            warnings.append(f"{manual_remaining} records still deferred by verification (manual_review)")

    all_pass = all(c[1] for c in gate_checks)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    accepted_count = sum(1 for e in review_queue if e.get("curation_decision") == "accept")
    deferred_count = sum(1 for e in review_queue if e.get("curation_decision") == "defer")
    rejected_count = sum(1 for e in review_queue if e.get("curation_decision") == "reject")

    packet = {
        "generated_at": now,
        "gate_result": "OPEN" if all_pass else "BLOCKED",
        "gate_checks": [{"check": c[0], "pass": c[1], "detail": c[2]} for c in gate_checks],
        "blockers": blockers,
        "warnings": warnings,
        "queue_summary": {
            "accept": accepted_count,
            "defer": deferred_count,
            "reject": rejected_count,
            "pending_human_approval": len(pending_approval),
            "auto_approved": sum(1 for e in review_queue if e.get("review_status") == "auto_approved"),
        },
        "status_resolution_ref": str(STATUS_RESOLUTION_PACKET_PATH) if status_resolution else None,
        "next_steps": [],
    }

    if all_pass:
        packet["next_steps"].append("Export gate is OPEN. Run: python3 scripts/build_catalog_artifacts.py export-all")
        packet["next_steps"].append("Then validate: python3 scripts/build_catalog_artifacts.py validate")
    else:
        packet["next_steps"].append(f"Resolve {len(blockers)} blocker(s) before export:")
        for b in blockers:
            packet["next_steps"].append(f"  - {b}")
    if pending_approval:
        packet["next_steps"].append("To approve pending candidates, use record-review command:")
        for e in pending_approval[:5]:
            packet["next_steps"].append(f"  python3 scripts/curate_candidates.py record-review --candidate-id {e['candidate_id']} --decision approved --reviewed-by <REVIEWER_NAME>")
        if len(pending_approval) > 5:
            packet["next_steps"].append(f"  ... and {len(pending_approval) - 5} more pending candidates")
        packet["next_steps"].append("Then re-run: python3 scripts/curate_candidates.py export-gate")

    write_json(EXPORT_GATE_PACKET_PATH, packet)

    print(f" Export gate result: {'OPEN' if all_pass else 'BLOCKED'}")
    print(f"\n Gate checks:")
    for check_name, passed, detail in gate_checks:
        mark = "PASS" if passed else "FAIL"
        print(f"  [{mark}] {check_name}: {detail}")

    if blockers:
        print(f"\n Blockers ({len(blockers)}):")
        for b in blockers:
            print(f"  - {b}")

    if warnings:
        print(f"\n Warnings ({len(warnings)}):")
        for w in warnings:
            print(f"  - {w}")

    print(f"\n Next steps:")
    for step in packet["next_steps"]:
        print(f"  {step}")

    print(f"\n Export gate packet saved to: {EXPORT_GATE_PACKET_PATH}")

    print(f"\n=== Export Gate complete ===")
    return {
        "gate_result": packet["gate_result"],
        "blockers": len(blockers),
        "warnings": len(warnings),
        "checks": len(gate_checks),
    }


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

    triage_breakdown = {}
    for d in decisions:
        tc = d.get("triage_category", "") or "no_triage"
        key = f"{d['decision']}|{tc}"
        triage_breakdown[key] = triage_breakdown.get(key, 0) + 1

    key_cases = []
    for d in accepted_disputed:
        tc = d.get("triage_category", "unknown")
        key_cases.append(
            f"- **ACCEPTED (disputed, triage={tc})**: {d['candidate_id']} — {d['rationale']}"
        )
    for d in deferred[:10]:
        tc = d.get("triage_category", "unknown")
        key_cases.append(f"- **DEFERRED (triage={tc})**: {d['candidate_id']} — {d['rationale']}")

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
            "## Triage-informed curation breakdown",
            "",
            "Disputed candidates were resolved using triage categories from verification:",
            "",
            "| Triage Category | Curation Decision | Count |",
            "|----------------|-------------------|-------|",
        ]
    )

    triage_category_order = [
        "likely_confirmed",
        "threshold_tuning",
        "ocr_needed",
        "manual_review",
        "no_triage",
    ]
    for tc in triage_category_order:
        for dec in ["accept", "defer", "reject"]:
            key = f"{dec}|{tc}"
            count = triage_breakdown.get(key, 0)
            if count > 0:
                report_lines.append(f"| {tc} | {dec} | {count} |")

    report_lines.extend(
        [
            "",
            "## Verified snapshot stability assessment",
            "",
        ]
    )

    snapshot_exists = snapshot_path.exists()
    report_exists = report_path.exists()
    disagreement_exists = disagreement_path.exists()

    if snapshot_exists and report_exists and disagreement_exists:
        report_lines.append("Verified snapshot is **structurally complete**: all three verification artifacts (snapshot, report, disagreement log) are present.")
        report_lines.append("")
        if len(deferred) > 0:
            report_lines.append(f"However, **{len(deferred)} candidates remain deferred** and block full pipeline completion:")
            ocr_deferred = sum(1 for d in deferred if d.get("triage_category") == "ocr_needed")
            manual_deferred = sum(1 for d in deferred if d.get("triage_category") == "manual_review")
            no_triage_deferred = sum(1 for d in deferred if not d.get("triage_category"))
            if ocr_deferred:
                report_lines.append(f"- {ocr_deferred} deferred due to missing OCR (requires GEMINI_API_KEY)")
            if manual_deferred:
                report_lines.append(f"- {manual_deferred} deferred requiring manual human review")
            if no_triage_deferred:
                report_lines.append(f"- {no_triage_deferred} deferred without triage data")
        report_lines.append("")
        if len(accepted_disputed) > 0:
            report_lines.append(f"**{len(accepted_disputed)} disputed candidates were auto-promoted to accept** based on triage=likely_confirmed. These should be reviewed by a human before export.")
            report_lines.append("")
    else:
        missing = []
        if not snapshot_exists:
            missing.append(f"verified snapshot ({snapshot_path})")
        if not report_exists:
            missing.append(f"verification report ({report_path})")
        if not disagreement_exists:
            missing.append(f"disagreement log ({disagreement_path})")
        report_lines.append(f"Verified snapshot is **incomplete**. Missing: {', '.join(missing)}.")
        report_lines.append("Curation proceeded with available data, but results may not reflect the full verification state.")
        report_lines.append("")

    gate_packet = {}
    if EXPORT_GATE_PACKET_PATH.exists():
        with open(EXPORT_GATE_PACKET_PATH, "r", encoding="utf-8") as f:
            gate_packet = json.load(f)

    gate_result = gate_packet.get("gate_result", "UNKNOWN")
    gate_blockers = gate_packet.get("blockers", [])
    gate_warnings = gate_packet.get("warnings", [])

    report_lines.extend(
        [
            "## Provenance",
            "",
            f"- Verification report: `{report_path}`",
            f"- Disagreement log: `{disagreement_path}`",
            f"- Source snapshot: `{snapshot_path}`",
            f"- Curation decisions: `{CURATION_DECISIONS_PATH}`",
            f"- Review queue: `{REVIEW_QUEUE_PATH}`",
            f"- Export gate packet: `{EXPORT_GATE_PACKET_PATH}`",
            "",
            "## Export gate status",
            "",
            f"**Gate: {gate_result}**",
            "",
        ]
    )

    if gate_result == "OPEN":
        report_lines.extend(
            [
                "Export gate is OPEN. Downstream export pack is safe to run:",
                "",
                "```bash",
                "python3 PROJEKTY/13_baza_czesci_recykling/scripts/build_catalog_artifacts.py export-all",
                "python3 PROJEKTY/13_baza_czesci_recykling/scripts/build_catalog_artifacts.py validate",
                "```",
                "",
            ]
        )
    else:
        report_lines.append("Export gate is **BLOCKED**. Do not run export until blockers are resolved:")
        report_lines.append("")
        if gate_blockers:
            for b in gate_blockers:
                report_lines.append(f"- BLOCKER: {b}")
        if gate_warnings:
            for w in gate_warnings:
                report_lines.append(f"- warning: {w}")
        if not gate_blockers and not gate_warnings:
            report_lines.append("- (no explicit blockers listed in gate packet — re-run export-gate)")
        report_lines.append("")
        report_lines.append("To resolve:")
        report_lines.append("1. Review pending_human_approval candidates in curation_review_queue.jsonl")
        report_lines.append("2. Set reviewed_by and reviewed_at for approved entries")
        report_lines.append("3. Re-run: python3 scripts/curate_candidates.py export-gate")
        report_lines.append("")

    if gate_packet.get("next_steps"):
        report_lines.extend(
            [
                "### Next steps (from gate packet)",
                "",
            ]
        )
        for step in gate_packet["next_steps"]:
            report_lines.append(f"- {step}")
        report_lines.append("")

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

    blockers = []
    ocr_deferred_count = sum(1 for d in deferred if d.get("triage_category") == "ocr_needed")
    manual_deferred_count = sum(1 for d in deferred if d.get("triage_category") == "manual_review")
    no_triage_deferred_count = sum(1 for d in deferred if not d.get("triage_category"))

    if ocr_deferred_count > 0:
        blockers.append(f"{ocr_deferred_count} candidates deferred pending OCR (GEMINI_API_KEY not available)")
    if manual_deferred_count > 0:
        blockers.append(f"{manual_deferred_count} candidates deferred pending manual human review")
    if no_triage_deferred_count > 0:
        blockers.append(f"{no_triage_deferred_count} candidates deferred without triage classification")
    if len(accepted_disputed) > 0:
        blockers.append(f"{len(accepted_disputed)} disputed candidates auto-promoted to accept (need human confirmation before export)")

    if blockers:
        report_lines.extend(
            [
                "## Deferred candidates detail",
                "",
            ]
        )
        for b in blockers:
            report_lines.append(f"- {b}")
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
        "=== Curation Dry-Run: align + decide + review-queue + export-gate + validate + report (no catalog writes) ===\n"
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

    review_queue_args = argparse.Namespace(
        snapshot=args.snapshot,
    )
    queue_result = cmd_review_queue(review_queue_args)

    export_gate_args = argparse.Namespace(
        snapshot=args.snapshot,
    )
    gate_result = cmd_export_gate(export_gate_args)

    validate_result = cmd_validate(argparse.Namespace())

    report_result = cmd_report(decide_args)

    print("\n=== Dry-Run Summary ===")
    print(f" Aligned: {align_counts}")
    print(f" Decisions: {decide_counts}")
    print(f" Review queue: {queue_result}")
    print(f" Export gate: {gate_result}")
    print(f" Validation: {validate_result}")
    print(f" Report: {report_result}")
    print(f"\n NOTE: Canonical catalog files were NOT modified (dry-run mode).")
    print(f" To apply accepted candidates, run: curate_candidates.py apply")


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
        ("review-queue", "Generate explicit review queue from curation decisions"),
        ("record-review", "Record a human review decision (approved/rejected/defer) for a pending candidate"),
        ("list-pending", "List pending_human_approval cases with batch annotation; export to JSON"),
        ("review-status", "Show current review status summary and remaining pending entries"),
        ("export-gate", "Check whether export is allowed; generate export gate packet"),
        ("apply", "Write accepted candidates into canonical catalog files"),
        ("validate", "Validate catalog cross-file consistency"),
        ("report", "Generate curation_report.md"),
        ("dry-run", "Run align+decide+review-queue+export-gate+validate+report without writing to catalog"),
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
        if name == "record-review":
            sp.add_argument(
                "--candidate-id",
                required=True,
                help="Candidate ID from review queue (e.g. candidate-0005)",
            )
            sp.add_argument(
                "--decision",
                required=True,
                choices=list(VALID_REVIEW_DECISIONS),
                help="Review decision: approved, rejected, or defer",
            )
            sp.add_argument(
                "--reviewed-by",
                required=True,
                help="Name or identifier of the human reviewer (no fictional reviewers)",
            )
            sp.add_argument(
                "--note",
                default="",
                help="Optional note explaining the review decision",
            )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    commands = {
        "review": cmd_review,
        "align": cmd_align,
        "decide": cmd_decide,
        "review-queue": cmd_review_queue,
        "record-review": cmd_record_review,
        "list-pending": cmd_list_pending,
        "review-status": cmd_review_status,
        "export-gate": cmd_export_gate,
        "apply": cmd_apply,
        "validate": cmd_validate,
        "report": cmd_report,
        "dry-run": cmd_dry_run,
    }

    result = commands[args.command](args)


if __name__ == "__main__":
    main()
