#!/usr/bin/env python3
"""Simulated precheck runner dla packa pack-project13-esp-runtime-01.

Przyjmuje board profile (markdown), waliduje strukture konfiguracji,
sprawdza pin map vs board profile (damaged pins exclusion), weryfikuje
spojnosc pol krytycznych z BENCH_TEST_CONTRACT i SIMULATION_POLICY,
generuje precheck report z checkami (pass/warn/fail).

Wszystkie testy real_hardware sa oznaczone jako PENDING — symulacja
nie zastepuje realnego bench testu.

Uzycie:
    python3 simulated_precheck_esp_runtime.py --board-profile <profile.md>
    python3 simulated_precheck_esp_runtime.py --board-profile <profile.md> --runtime-profile <runtime_profile.json>
    python3 simulated_precheck_esp_runtime.py --board-profile <profile.md> --output-dir <dir>
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
PACK_ID = "pack-project13-esp-runtime-01"
PACK_DIR = PROJECT_ROOT / "execution_packs" / PACK_ID
DEFAULT_OUTPUT_DIR = PACK_DIR / "output"
MANIFEST_PATH = PACK_DIR / "manifest.json"
RUNBOOK_PATH = PACK_DIR / "RUNBOOK.md"
REVIEW_CHECKLIST_PATH = PACK_DIR / "REVIEW_CHECKLIST.md"
BENCH_TEST_CONTRACT_PATH = PROJECT_ROOT / "docs" / "BENCH_TEST_CONTRACT_ESP_RUNTIME_01.md"
SIMULATION_POLICY_PATH = PROJECT_ROOT / "docs" / "SIMULATION_VS_REAL_HARDWARE_POLICY_ESP_RUNTIME_01.md"

BENCH_TEST_IDS = {
    "power": ["BT-PWR-01", "BT-PWR-02", "BT-PWR-03", "BT-PWR-04", "BT-PWR-05"],
    "flash": ["BT-FLS-01", "BT-FLS-02", "BT-FLS-03", "BT-FLS-04"],
    "gpio": ["BT-GPIO-01", "BT-GPIO-02", "BT-GPIO-03", "BT-GPIO-04", "BT-GPIO-05"],
    "network": ["BT-NET-01", "BT-NET-02", "BT-NET-03", "BT-NET-04"],
    "storage": ["BT-STO-01", "BT-STO-02"],
}

BENCH_TEST_CATEGORIES = {
    "BT-PWR-01": "real_hardware", "BT-PWR-02": "real_hardware",
    "BT-PWR-03": "real_hardware", "BT-PWR-04": "real_hardware",
    "BT-PWR-05": "real_hardware",
    "BT-FLS-01": "real_hardware", "BT-FLS-02": "real_hardware",
    "BT-FLS-03": "real_hardware", "BT-FLS-04": "either",
    "BT-GPIO-01": "real_hardware", "BT-GPIO-02": "either",
    "BT-GPIO-03": "real_hardware", "BT-GPIO-04": "real_hardware",
    "BT-GPIO-05": "real_hardware",
    "BT-NET-01": "real_hardware", "BT-NET-02": "real_hardware",
    "BT-NET-03": "real_hardware", "BT-NET-04": "real_hardware",
    "BT-STO-01": "real_hardware", "BT-STO-02": "real_hardware",
}

BENCH_TEST_NAMES = {
    "BT-PWR-01": "Pomiar napiecia wejsciowego vs input_voltage",
    "BT-PWR-02": "Pomiar napiecia roboczego MCU vs operating_voltage",
    "BT-PWR-03": "Pomiar pradu idle vs power_consumption_idle",
    "BT-PWR-04": "Pomiar pradu Wi-Fi TX vs power_consumption_wifi_tx",
    "BT-PWR-05": "Stabilnosc zasilania pod obciazeniem",
    "BT-FLS-01": "Flash firmware przez zadeklarowana metode",
    "BT-FLS-02": "Wejscie w download mode przez boot_mode_entry",
    "BT-FLS-03": "Recovery po brick",
    "BT-FLS-04": "Backup oryginalnego firmware istnieje lub NIE DOTYCZY",
    "BT-GPIO-01": "Piny free odpowiadaja na toggle",
    "BT-GPIO-02": "Piny damaged wykluczone z pin map",
    "BT-GPIO-03": "ADC1 odczyt z napiecia referencyjnego",
    "BT-GPIO-04": "I2C scan — wykrycie slave",
    "BT-GPIO-05": "UART0 komunikacja serial",
    "BT-NET-01": "Wi-Fi scan — plytka widzi sieci 2.4GHz",
    "BT-NET-02": "Wi-Fi connect do testowego AP",
    "BT-NET-03": "MQTT publish do testowego broker",
    "BT-NET-04": "Antena — jakosc sygnalu (RSSI)",
    "BT-STO-01": "Rozmiar flash vs flash_size z board profile",
    "BT-STO-02": "Odczyt tabeli partycji",
}

REQUIRED_BOARD_PROFILE_FIELDS = [
    "board_id", "board_variant", "input_voltage", "operating_voltage",
    "flash_method", "boot_mode_entry", "recovery_after_brick",
    "antenna_condition", "damaged_pins", "safety_notes",
]

POMIERZONE_REQUIRED_FOR_SIMULATION = [
    "board_id", "board_variant", "flash_method",
    "boot_mode_entry", "recovery_after_brick", "safety_notes",
]

POMIERZONE_REQUIRED_FOR_REAL_HARDWARE = [
    "input_voltage", "operating_voltage", "antenna_condition", "damaged_pins",
]

BRAKUJACE_FIELDS_BLOCK_REAL_HARDWARE = [
    "power_consumption_idle", "power_consumption_wifi_tx",
]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def add_check(checks: list[dict], name: str, status: str, details: str) -> None:
    checks.append({"name": name, "status": status, "details": details})


def parse_board_profile_fields(text: str) -> dict[str, dict[str, str]]:
    sections: dict[str, dict[str, str]] = {}
    current_section: str = ""
    lines = text.split("\n")

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("## "):
            current_section = line.lstrip("# ").strip()
            sections[current_section] = {}
            i += 1
            continue

        if current_section and line.startswith("|"):
            cells = [c.strip() for c in line.split("|")[1:-1]]
            if len(cells) >= 3 and cells[0] not in ("Pole", "GPIO", "Funkcja", "---", "", "Test ID") and not cells[0].startswith("-"):
                field_name = cells[0].strip("`")
                value = cells[1] if len(cells) > 1 else ""
                wymagalnosc = cells[2] if len(cells) > 2 else ""
                sections.setdefault(current_section, {})[field_name] = {
                    "value": value,
                    "wymagalnosc": wymagalnosc,
                }
        i += 1

    return sections


def parse_gpio_table(text: str) -> list[dict]:
    gpio_entries: list[dict] = []
    in_gpio = False
    lines = text.split("\n")

    for line in lines:
        stripped = line.strip()
        if "3.1" in stripped and stripped.startswith("###"):
            in_gpio = True
            continue
        if stripped.startswith("###") and "3.1" not in stripped:
            in_gpio = False
            continue

        if in_gpio and stripped.startswith("|"):
            cells = [c.strip() for c in stripped.split("|")[1:-1]]
            if len(cells) >= 3 and cells[0] not in ("GPIO", "---", "") and not cells[0].startswith("-"):
                try:
                    int(cells[0])
                    gpio_entries.append({
                        "gpio": cells[0],
                        "alt_func": cells[1] if len(cells) > 1 else "",
                        "board_status": cells[2] if len(cells) > 2 else "",
                        "runtime_usage": cells[3] if len(cells) > 3 else "",
                    })
                except ValueError:
                    pass

    return gpio_entries


def flatten_fields(sections: dict[str, dict[str, str]]) -> dict[str, str]:
    flat: dict[str, str] = {}
    for section_fields in sections.values():
        for field_name, field_data in section_fields.items():
            flat[field_name] = field_data["value"] if isinstance(field_data, dict) else str(field_data)
    return flat


def flatten_wymagalnosc(sections: dict[str, dict[str, str]]) -> dict[str, str]:
    flat: dict[str, str] = {}
    for section_fields in sections.values():
        for field_name, field_data in section_fields.items():
            if isinstance(field_data, dict):
                flat[field_name] = field_data.get("wymagalnosc", "")
    return flat


def run_simulated_checks(
    sections: dict[str, dict[str, str]],
    gpio_entries: list[dict],
    runtime_profile: dict | None,
) -> list[dict]:
    checks: list[dict] = []
    flat = flatten_fields(sections)
    wym = flatten_wymagalnosc(sections)

    add_check(checks, "board_profile::parseable", "pass",
              f"Parsowalny board profile z {len(flat)} polami")

    board_id = flat.get("board_id", "")
    if board_id:
        add_check(checks, "board_profile::board_id", "pass",
                  f"board_id = '{board_id}'")
    else:
        add_check(checks, "board_profile::board_id", "fail",
                  "Brak board_id — pack wymaga jawnie nazwanej plytki")

    for field_name in REQUIRED_BOARD_PROFILE_FIELDS:
        value = flat.get(field_name, "")
        if value and value.lower() not in ("", "unknown", "__do_uzupelnienia__", "tbd", "todo"):
            add_check(checks, f"board_profile::required_field::{field_name}", "pass",
                      f"{field_name} = '{value}'")
        else:
            add_check(checks, f"board_profile::required_field::{field_name}", "fail",
                      f"Pole wymagane puste albo brakujace: {field_name}")

    for field_name in POMIERZONE_REQUIRED_FOR_SIMULATION:
        w = wym.get(field_name, "").upper()
        if "POMIERZONE" in w:
            add_check(checks, f"simulation_readiness::{field_name}", "pass",
                      f"{field_name}: wymagalnosc = POMIERZONE")
        elif "DOMNIEMANE" in w:
            add_check(checks, f"simulation_readiness::{field_name}", "warn",
                      f"{field_name}: wymagalnosc = DOMNIEMANE (wymaga POMIERZONE dla real_hardware)")
        elif "BRAKUJACE" in w:
            add_check(checks, f"simulation_readiness::{field_name}", "warn",
                      f"{field_name}: wymagalnosc = BRAKUJACE (wymaga uzupelnienia)")
        else:
            add_check(checks, f"simulation_readiness::{field_name}", "warn",
                      f"{field_name}: wymagalnosc nie okreslona")

    for field_name in POMIERZONE_REQUIRED_FOR_REAL_HARDWARE:
        w = wym.get(field_name, "").upper()
        if "POMIERZONE" in w:
            add_check(checks, f"real_hardware_readiness::{field_name}", "pass",
                      f"{field_name}: POMIERZONE")
        elif "DOMNIEMANE" in w:
            add_check(checks, f"real_hardware_readiness::{field_name}", "warn",
                      f"{field_name}: DOMNIEMANE — musi byc POMIERZONE przed real_hardware bench test")
        elif "BRAKUJACE" in w:
            add_check(checks, f"real_hardware_readiness::{field_name}", "fail",
                      f"{field_name}: BRAKUJACE — blokuje real_hardware bench test")

    for field_name in BRAKUJACE_FIELDS_BLOCK_REAL_HARDWARE:
        value = flat.get(field_name, "").lower()
        if value in ("unknown", "brakujace", ""):
            add_check(checks, f"real_hardware_blocker::{field_name}", "warn",
                      f"{field_name} = unknown/brakujace — test bedzie PENDING na real_hardware")

    damaged_pins_raw = flat.get("damaged_pins", "brak uszkodzonych").lower()
    has_damaged = damaged_pins_raw not in ("brak uszkodzonych", "brak", "none", "nie dotyczy", "")
    if has_damaged:
        add_check(checks, "gpio::damaged_pins_declared", "warn",
                  f"Board profile deklaruje uszkodzone piny: '{flat.get('damaged_pins', '')}'")
    else:
        add_check(checks, "gpio::damaged_pins_declared", "pass",
                  "Brak uszkodzonych pinow w board profile")

    free_gpios = [g for g in gpio_entries if g["board_status"] == "free"]
    used_gpios = [g for g in gpio_entries if g["board_status"] == "used_onboard"]
    damaged_gpios = [g for g in gpio_entries if "damaged" in g["board_status"].lower()]
    add_check(checks, "gpio::pin_inventory", "pass" if free_gpios else "warn",
              f"free={len(free_gpios)}, used_onboard={len(used_gpios)}, damaged={len(damaged_gpios)}")

    flash_method = flat.get("flash_method", "")
    if flash_method:
        add_check(checks, "flash::method_declared", "pass",
                  f"flash_method = '{flash_method}'")
    else:
        add_check(checks, "flash::method_declared", "fail",
                  "Brak flash_method — pack nie wie jak flashowac plytke")

    boot_mode = flat.get("boot_mode_entry", "")
    if boot_mode:
        add_check(checks, "flash::boot_mode_declared", "pass",
                  f"boot_mode_entry = '{boot_mode}'")
    else:
        add_check(checks, "flash::boot_mode_declared", "fail",
                  "Brak boot_mode_entry — recovery path niezdefiniowany")

    recovery = flat.get("recovery_after_brick", "")
    if recovery:
        add_check(checks, "flash::recovery_path_declared", "pass",
                  f"recovery_after_brick = '{recovery}'")
    else:
        add_check(checks, "flash::recovery_path_declared", "fail",
                  "Brak recovery_after_brick — brak odzyskiwania po awarii")

    backup = flat.get("backup_firmware_available", "")
    if backup.upper() in ("TAK", "YES", "NIE DOTYCZY", "NIE"):
        add_check(checks, "flash::backup_firmware", "pass",
                  f"backup_firmware_available = '{backup}'")
    else:
        add_check(checks, "flash::backup_firmware", "warn",
                  f"backup_firmware_available = '{backup}' — wymaga wyjasnienia")

    wifi = flat.get("wifi_2_4ghz", "")
    if wifi.upper() in ("TAK", "YES"):
        add_check(checks, "network::wifi_declared", "pass",
                  "Wi-Fi 2.4GHz zadeklarowane")
    else:
        add_check(checks, "network::wifi_declared", "warn",
                  f"Wi-Fi 2.4GHz = '{wifi}' — sprawdzic czy plytka ma Wi-Fi")

    antenna = flat.get("antenna_condition", "")
    if antenna.lower() in ("good", "dobry", "dobra"):
        add_check(checks, "network::antenna_condition", "pass",
                  f"antenna_condition = '{antenna}'")
    elif antenna:
        add_check(checks, "network::antenna_condition", "warn",
                  f"antenna_condition = '{antenna}' — moze wplywac na testy RF")
    else:
        add_check(checks, "network::antenna_condition", "warn",
                  "Brak antenna_condition")

    flash_size = flat.get("flash_size", "")
    if flash_size:
        add_check(checks, "storage::flash_size_declared", "pass",
                  f"flash_size = '{flash_size}'")
    else:
        add_check(checks, "storage::flash_size_declared", "fail",
                  "Brak flash_size — BT-STO-01 niemozliwy")

    if runtime_profile is not None:
        if isinstance(runtime_profile, dict):
            add_check(checks, "runtime_profile::parseable", "pass",
                      "runtime_profile.json parsuje sie jako JSON dict")
            rp_board_id = runtime_profile.get("board_id", "")
            if rp_board_id and rp_board_id == board_id:
                add_check(checks, "runtime_profile::board_id_match", "pass",
                          f"runtime_profile.board_id = '{rp_board_id}' zgadza sie z board profile")
            elif rp_board_id:
                add_check(checks, "runtime_profile::board_id_match", "fail",
                          f"runtime_profile.board_id = '{rp_board_id}' NIE zgadza sie z board_id = '{board_id}'")
            else:
                add_check(checks, "runtime_profile::board_id_match", "warn",
                          "runtime_profile nie ma board_id")

            pin_map = runtime_profile.get("pin_map", {})
            if isinstance(pin_map, dict):
                damaged_in_map = []
                for pin_name, gpio_num in pin_map.items():
                    gpio_str = str(gpio_num)
                    for dg in damaged_gpios:
                        if gpio_str == dg["gpio"]:
                            damaged_in_map.append(f"{pin_name}=GPIO{gpio_str}")
                if damaged_in_map:
                    add_check(checks, "runtime_profile::damaged_pins_in_map", "fail",
                              f"Pin map uzywa uszkodzonych pinow: {damaged_in_map}")
                else:
                    add_check(checks, "runtime_profile::damaged_pins_in_map", "pass",
                              "Pin map nie uzywa uszkodzonych pinow (zgadza sie z BT-GPIO-02)")
            else:
                add_check(checks, "runtime_profile::pin_map", "warn",
                          "runtime_profile nie ma pin_map albo pin_map nie jest dict")
        else:
            add_check(checks, "runtime_profile::parseable", "fail",
                      "runtime_profile.json nie jest dict")
    else:
        add_check(checks, "runtime_profile::not_provided", "warn",
                  "Brak runtime_profile.json — sprawdzanie pin map pominięte")

    add_check(checks, "bench_contract::exists", "pass" if BENCH_TEST_CONTRACT_PATH.exists() else "fail",
              str(BENCH_TEST_CONTRACT_PATH))
    add_check(checks, "simulation_policy::exists", "pass" if SIMULATION_POLICY_PATH.exists() else "fail",
              str(SIMULATION_POLICY_PATH))

    return checks


def build_bench_test_report_template(
    flat: dict[str, str],
    board_id: str,
) -> str:
    board_variant = flat.get("board_variant", "UNKNOWN")
    flash_method = flat.get("flash_method", "UNKNOWN")

    lines = [
        f"# Bench Test Report: {board_id}",
        "",
        "## Metryka",
        "",
        f"- Data testu: [DO_UZUPELNIENIA]",
        f"- board_id: `{board_id}`",
        f"- board_variant: `{board_variant}`",
        f"- flash_method: `{flash_method}`",
        f"- Tester: [DO_UZUPELNIENIA — osoba albo automated]",
        "",
        "## Wyniki",
        "",
        "| Test ID | Test | Kategoria | Status | Wartosc zmierzona | Wartosc oczekiwana | Delta |",
        "|---------|------|-----------|--------|-------------------|-------------------|-------|",
    ]

    for section_name, test_ids in BENCH_TEST_IDS.items():
        for test_id in test_ids:
            cat = BENCH_TEST_CATEGORIES.get(test_id, "real_hardware")
            test_name = BENCH_TEST_NAMES.get(test_id, test_id)
            if cat == "real_hardware":
                status = "PENDING"
            else:
                status = "[DO_UZUPELNIENIA]"
            lines.append(f"| {test_id} | {test_name} | {cat} | {status} | | | |")

    pass_count = 0
    pending_count = sum(1 for tid in BENCH_TEST_CATEGORIES if BENCH_TEST_CATEGORIES[tid] == "real_hardware")
    either_count = sum(1 for tid in BENCH_TEST_CATEGORIES if BENCH_TEST_CATEGORIES[tid] == "either")

    lines.extend([
        "",
        "## Podsumowanie",
        "",
        f"- PASS: {pass_count}",
        f"- FAIL: 0",
        f"- PENDING: {pending_count}",
        f"- SKIP: 0",
        f"- NOT_APPLICABLE: 0",
        "",
        "## Werdykt",
        "",
        "- [ ] Runtime bundle moze byc promowany (wszystkie real_hardware = PASS albo NOT_APPLICABLE)",
        "- [x] Runtime bundle NIE MOZE byc promowany (istnieje PENDING na real_hardware — brak fizycznej plytki albo brak wynikow)",
        "",
        "> **UWAGA**: To jest template wygenerowany przez simulated precheck. Wszystkie testy `real_hardware`",
        "> sa PENDING dopoki nie zostana wykonane na fizycznej plytce ESP32. Symulacja NIE zastepuje",
        "> realnego bench testu. Patrz: `docs/BENCH_TEST_CONTRACT_ESP_RUNTIME_01.md`",
        "> i `docs/SIMULATION_VS_REAL_HARDWARE_POLICY_ESP_RUNTIME_01.md`.",
    ])

    return "\n".join(lines) + "\n"


def build_precheck_report(
    board_profile_path: Path,
    checks: list[dict],
    board_id: str,
    run_stamp: str,
) -> str:
    failures = [c for c in checks if c["status"] == "fail"]
    warnings = [c for c in checks if c["status"] == "warn"]
    overall = "pass"
    if failures:
        overall = "needs_changes"
    elif warnings:
        overall = "conditional"

    lines = [
        f"# Simulated Precheck Report: {PACK_ID}",
        "",
        f"- executed_at_utc: {utc_now().replace(microsecond=0).isoformat()}",
        f"- run_mode: simulated_precheck",
        f"- overall_status: {overall}",
        f"- pack_id: {PACK_ID}",
        f"- board_profile: {board_profile_path}",
        f"- board_id: {board_id}",
        f"- run_stamp: {run_stamp}",
        "",
        "## Checks",
        "",
    ]

    for c in checks:
        lines.append(f"- [{c['status']}] {c['name']}: {c['details']}")

    lines.extend([
        "",
        "## Czego symulacja NIE potwierdza",
        "",
        "Symulacja NIE zastepuje testow na realnym hardware. Nastepujace testy wymagaja",
        "fizycznej plytki ESP32 i nie moga byc potwierdzone w symulacji:",
        "",
        "- **BT-PWR-01..05**: pomiary napiecia i pradu (wymagaja multimetru + plytka)",
        "- **BT-FLS-01..03**: flashowanie i recovery (wymagaja fizycznego flash + esptool verify)",
        "- **BT-GPIO-01,03,04,05**: fizyczny toggle, ADC, I2C, UART (wymagaja sygnalow)",
        "- **BT-NET-01..04**: Wi-Fi scan, connect, MQTT, RSSI (wymagaja RF)",
        "- **BT-STO-01..02**: odczyt flash i partycji (wymagaja esptool na plytce)",
        "",
        "Symulacja moze potwierdzic:",
        "",
        "- **BT-GPIO-02**: pin map nie uzywa damaged pins (sprawdzalne bez plytki)",
        "- **BT-FLS-04**: backup firmware istnieje (sprawdzalne na dysku)",
        "",
        "## Sciezka: simulated precheck -> real hardware bench",
        "",
        "1. **Simulated precheck** (ten raport) — walidacja struktury i spojnosci konfiguracji",
        "2. **Decyzja maintainera** — czy przechodzic do real_hardware (wymaga plytki + pola POMIERZONE)",
        "3. **Bench test real_hardware** — wykonanie BT-PWR..BT-STO na fizycznej plytce",
        "4. **Bench test report** — wyniki z plytki, autorytatywne",
        "5. **Review Wariant B** — reviewer merytoryczny + integrity reviewer",
        "6. **ReadinessGate(integrity_ready) = PASS** -> Approval -> merge",
        "",
        "> Zobacz: `docs/BENCH_TEST_CONTRACT_ESP_RUNTIME_01.md` i",
        "> `docs/SIMULATION_VS_REAL_HARDWARE_POLICY_ESP_RUNTIME_01.md`",
    ])

    return "\n".join(lines) + "\n"


def build_runtime_profile_stub(flat: dict[str, str], gpio_entries: list[dict]) -> dict:
    free_gpios = [g for g in gpio_entries if g["board_status"] == "free"]
    pin_map_stub: dict[str, str] = {}
    for g in free_gpios[:5]:
        pin_map_stub[f"available_GPIO{g['gpio']}"] = g["gpio"]

    return {
        "schema_version": "v1",
        "board_id": flat.get("board_id", ""),
        "board_variant": flat.get("board_variant", ""),
        "operating_voltage": flat.get("operating_voltage", ""),
        "flash_size": flat.get("flash_size", ""),
        "flash_method": flat.get("flash_method", ""),
        "pin_map": pin_map_stub,
        "wifi": flat.get("wifi_2_4ghz", "") == "TAK",
        "bluetooth_le": flat.get("bluetooth_le", "") == "TAK",
        "damaged_pins": flat.get("damaged_pins", ""),
        "dry_run": True,
        "simulated": True,
        "generated_at": utc_now().replace(microsecond=0).isoformat(),
        "note": "To jest stub wygenerowany przez simulated precheck. Nie jest runtime profilem gotowym do flashowania.",
    }


def build_flash_runbook_stub(flat: dict[str, str]) -> str:
    board_id = flat.get("board_id", "UNKNOWN")
    flash_method = flat.get("flash_method", "UNKNOWN")
    boot_mode = flat.get("boot_mode_entry", "UNKNOWN")
    recovery = flat.get("recovery_after_brick", "UNKNOWN")
    backup = flat.get("backup_firmware_available", "UNKNOWN")
    backup_loc = flat.get("backup_firmware_location", "NIE DOTYCZY")

    lines = [
        f"# Flash and Recovery Runbook: {board_id}",
        "",
        f"- dry_run: True",
        f"- generated_at: {utc_now().replace(microsecond=0).isoformat()}",
        "",
        "## 1. Flashowanie",
        "",
        f"- Metoda: {flash_method}",
        f"- Boot mode entry: {boot_mode}",
        "- Komenda (przykladowa):",
        "",
        f"```bash",
        f"esptool.py --chip esp32 --port /dev/ttyUSB0 --baud 460800 write_flash -z 0x1000 firmware.bin",
        f"```",
        "",
        "> Uwaga: Komenda jest przykladowa. Zaleznie od plytki i konfiguracji moze wymagac zmiany.",
        "",
        "## 2. Recovery po brick",
        "",
        f"- Metoda odzyskiwania: {recovery}",
        "- Kroki:",
        "  1. Podlaczyc plytke przez USB",
        f"  2. Wejsc w download mode: {boot_mode}",
        "  3. Reflashowac firmware (krok 1)",
        "  4. Zweryfikowac: `esptool.py verify_flash 0x1000 firmware.bin`",
        "",
        "## 3. Backup firmware",
        "",
        f"- Backup dostepny: {backup}",
        f"- Lokalizacja: {backup_loc}",
        "",
        "## Ostrzezenie",
        "",
        "> Ten runbook zostal wygenerowany przez simulated precheck.",
        "> Nie flashowac bez bench testu na realnym hardware i bez ReadinessGate(integrity_ready).",
        "> Patrz: `docs/BENCH_TEST_CONTRACT_ESP_RUNTIME_01.md`",
    ]

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Simulated precheck runner dla pack-project13-esp-runtime-01"
    )
    parser.add_argument(
        "--board-profile", type=Path, required=True,
        help="Sciezka do board profile (markdown)",
    )
    parser.add_argument(
        "--runtime-profile", type=Path, default=None,
        help="Opcjonalna sciezka do runtime_profile.json",
    )
    parser.add_argument(
        "--output-dir", type=Path, default=None,
        help="Katalog wyjsciowy (domyslnie: pack_dir/output/)",
    )
    args = parser.parse_args()

    run_stamp = utc_now().strftime("%Y%m%dT%H%M%SZ")
    output_dir = args.output_dir or DEFAULT_OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    if not args.board_profile.exists():
        print(f"BLAD: Board profile nie istnieje: {args.board_profile}", file=sys.stderr)
        return 1

    text = args.board_profile.read_text(encoding="utf-8")
    sections = parse_board_profile_fields(text)
    flat = flatten_fields(sections)
    gpio_entries = parse_gpio_table(text)

    runtime_profile: dict | None = None
    if args.runtime_profile and args.runtime_profile.exists():
        try:
            runtime_profile = json.loads(args.runtime_profile.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            print(f"UWAGA: runtime_profile.json nie parsuje sie: {args.runtime_profile}", file=sys.stderr)

    checks = run_simulated_checks(sections, gpio_entries, runtime_profile)

    board_id = flat.get("board_id", "unknown")

    precheck_report = build_precheck_report(args.board_profile, checks, board_id, run_stamp)
    precheck_path = output_dir / "simulated_precheck_report.md"
    precheck_path.write_text(precheck_report, encoding="utf-8")
    add_check(checks, "artifact::simulated_precheck_report", "pass", str(precheck_path))

    bench_template = build_bench_test_report_template(flat, board_id)
    bench_template_path = output_dir / "bench_test_report_TEMPLATE.md"
    bench_template_path.write_text(bench_template, encoding="utf-8")
    add_check(checks, "artifact::bench_test_report_template", "pass", str(bench_template_path))

    runtime_stub = build_runtime_profile_stub(flat, gpio_entries)
    runtime_stub_path = output_dir / "runtime_profile.json"
    runtime_stub_path.write_text(
        json.dumps(runtime_stub, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    add_check(checks, "artifact::runtime_profile_stub", "pass", str(runtime_stub_path))

    flash_runbook = build_flash_runbook_stub(flat)
    flash_runbook_path = output_dir / "flash_and_recovery_runbook.md"
    flash_runbook_path.write_text(flash_runbook, encoding="utf-8")
    add_check(checks, "artifact::flash_and_recovery_runbook", "pass", str(flash_runbook_path))

    pin_map_lines = [
        f"# Pin Map: {board_id}",
        "",
        f"- dry_run: True",
        f"- generated_at: {utc_now().replace(microsecond=0).isoformat()}",
        "",
        "## Dostepne piny (free GPIO z board profile)",
        "",
        "| GPIO | Funkcja alternatywna | Przydzial runtime |",
        "|------|---------------------|-------------------|",
    ]
    free_gpios = [g for g in gpio_entries if g["board_status"] == "free"]
    for g in free_gpios:
        pin_map_lines.append(f"| {g['gpio']} | {g['alt_func']} | DO_UZUPELNIENIA |")
    used_gpios = [g for g in gpio_entries if g["board_status"] == "used_onboard"]
    if used_gpios:
        pin_map_lines.extend([
            "",
            "## Piny uzywane na plytce (used_onboard)",
            "",
            "| GPIO | Funkcja | Uwagi |",
            "|------|---------|-------|",
        ])
        for g in used_gpios:
            pin_map_lines.append(f"| {g['gpio']} | {g['alt_func']} | Zablokowany na plytce |")
    damaged_gpios = [g for g in gpio_entries if "damaged" in g["board_status"].lower()]
    if damaged_gpios:
        pin_map_lines.extend([
            "",
            "## Piny uszkodzone (damaged) — NIE UZYWAC",
            "",
            "| GPIO | Uwagi |",
            "|------|-------|",
        ])
        for g in damaged_gpios:
            pin_map_lines.append(f"| {g['gpio']} | USZKODZONY — wykluczony z runtime |")

    pin_map_lines.extend([
        "",
        "> Ten pin map zostal wygenerowany przez simulated precheck.",
        "> Przydzial runtime (DO_UZUPELNIENIA) wymaga zatwierdzonego design dossier.",
    ])

    pin_map_path = output_dir / "pin_map.md"
    pin_map_path.write_text("\n".join(pin_map_lines) + "\n", encoding="utf-8")
    add_check(checks, "artifact::pin_map", "pass", str(pin_map_path))

    failures = [c for c in checks if c["status"] == "fail"]
    warnings = [c for c in checks if c["status"] == "warn"]
    overall = "pass"
    if failures:
        overall = "needs_changes"
    elif warnings:
        overall = "conditional"

    precheck_report = build_precheck_report(args.board_profile, checks, board_id, run_stamp)
    precheck_path.write_text(precheck_report, encoding="utf-8")

    result = {
        "status": "ok",
        "overall": overall,
        "pack_id": PACK_ID,
        "board_id": board_id,
        "output_dir": str(output_dir),
        "artifacts": [
            str(precheck_path),
            str(bench_template_path),
            str(runtime_stub_path),
            str(flash_runbook_path),
            str(pin_map_path),
        ],
        "checks_total": len(checks),
        "checks_pass": sum(1 for c in checks if c["status"] == "pass"),
        "checks_warn": len(warnings),
        "checks_fail": len(failures),
        "run_stamp": run_stamp,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

    return 0 if overall != "needs_changes" else 1


if __name__ == "__main__":
    raise SystemExit(main())
