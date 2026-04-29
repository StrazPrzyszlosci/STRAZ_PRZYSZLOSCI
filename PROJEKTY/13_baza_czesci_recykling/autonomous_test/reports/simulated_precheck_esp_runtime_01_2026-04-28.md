# Simulated Precheck Report: pack-project13-esp-runtime-01

- executed_at_utc: 2026-04-28T07:52:54+00:00
- run_mode: simulated_precheck
- overall_status: conditional
- pack_id: pack-project13-esp-runtime-01
- board_profile: PROJEKTY/13_baza_czesci_recykling/docs/SAMPLE_ESP32_BOARD_PROFILE_DEVKITC_V4.md
- board_id: recovered-esp-devkitc-v4-01
- run_stamp: 20260428T075254Z

## Checks

- [pass] board_profile::parseable: Parsowalny board profile z 80 polami
- [pass] board_profile::board_id: board_id = 'recovered-esp-devkitc-v4-01'
- [pass] board_profile::required_field::board_id: board_id = 'recovered-esp-devkitc-v4-01'
- [pass] board_profile::required_field::board_variant: board_variant = 'ESP32-WROOM-32D'
- [pass] board_profile::required_field::input_voltage: input_voltage = '5V USB albo 5V VIN'
- [pass] board_profile::required_field::operating_voltage: operating_voltage = '3.3V'
- [pass] board_profile::required_field::flash_method: flash_method = 'USB-CDC (onboard CP2102)'
- [pass] board_profile::required_field::boot_mode_entry: boot_mode_entry = 'BOOT button + reset albo auto-reset circuit'
- [pass] board_profile::required_field::recovery_after_brick: recovery_after_brick = 'reflash via USB-CDC'
- [pass] board_profile::required_field::antenna_condition: antenna_condition = 'good'
- [pass] board_profile::required_field::damaged_pins: damaged_pins = 'brak uszkodzonych'
- [pass] board_profile::required_field::safety_notes: safety_notes = 'brak optoopcji na GPIO — nie podlaczac napiecia powyzej 3.3V bezpośrednio; GPIO34-39 tylko input'
- [pass] simulation_readiness::board_id: board_id: wymagalnosc = POMIERZONE
- [pass] simulation_readiness::board_variant: board_variant: wymagalnosc = POMIERZONE
- [pass] simulation_readiness::flash_method: flash_method: wymagalnosc = POMIERZONE
- [pass] simulation_readiness::boot_mode_entry: boot_mode_entry: wymagalnosc = POMIERZONE
- [pass] simulation_readiness::recovery_after_brick: recovery_after_brick: wymagalnosc = POMIERZONE
- [pass] simulation_readiness::safety_notes: safety_notes: wymagalnosc = POMIERZONE
- [pass] real_hardware_readiness::input_voltage: input_voltage: POMIERZONE
- [pass] real_hardware_readiness::operating_voltage: operating_voltage: POMIERZONE
- [pass] real_hardware_readiness::antenna_condition: antenna_condition: POMIERZONE
- [pass] real_hardware_readiness::damaged_pins: damaged_pins: POMIERZONE
- [warn] real_hardware_blocker::power_consumption_idle: power_consumption_idle = unknown/brakujace — test bedzie PENDING na real_hardware
- [warn] real_hardware_blocker::power_consumption_wifi_tx: power_consumption_wifi_tx = unknown/brakujace — test bedzie PENDING na real_hardware
- [pass] gpio::damaged_pins_declared: Brak uszkodzonych pinow w board profile
- [pass] gpio::pin_inventory: free=20, used_onboard=3, damaged=0
- [pass] flash::method_declared: flash_method = 'USB-CDC (onboard CP2102)'
- [pass] flash::boot_mode_declared: boot_mode_entry = 'BOOT button + reset albo auto-reset circuit'
- [pass] flash::recovery_path_declared: recovery_after_brick = 'reflash via USB-CDC'
- [pass] flash::backup_firmware: backup_firmware_available = 'TAK'
- [pass] network::wifi_declared: Wi-Fi 2.4GHz zadeklarowane
- [pass] network::antenna_condition: antenna_condition = 'good'
- [pass] storage::flash_size_declared: flash_size = '4MB'
- [warn] runtime_profile::not_provided: Brak runtime_profile.json — sprawdzanie pin map pominięte
- [pass] bench_contract::exists: /home/krzysiek/Dokumenty/INFO_GROUP/STRAZ_POLSKIEGO_Ai/PROJEKTY/13_baza_czesci_recykling/docs/BENCH_TEST_CONTRACT_ESP_RUNTIME_01.md
- [pass] simulation_policy::exists: /home/krzysiek/Dokumenty/INFO_GROUP/STRAZ_POLSKIEGO_Ai/PROJEKTY/13_baza_czesci_recykling/docs/SIMULATION_VS_REAL_HARDWARE_POLICY_ESP_RUNTIME_01.md
- [pass] artifact::simulated_precheck_report: /home/krzysiek/Dokumenty/INFO_GROUP/STRAZ_POLSKIEGO_Ai/PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-esp-runtime-01/output/simulated_precheck_report.md
- [pass] artifact::bench_test_report_template: /home/krzysiek/Dokumenty/INFO_GROUP/STRAZ_POLSKIEGO_Ai/PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-esp-runtime-01/output/bench_test_report_TEMPLATE.md
- [pass] artifact::runtime_profile_stub: /home/krzysiek/Dokumenty/INFO_GROUP/STRAZ_POLSKIEGO_Ai/PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-esp-runtime-01/output/runtime_profile.json
- [pass] artifact::flash_and_recovery_runbook: /home/krzysiek/Dokumenty/INFO_GROUP/STRAZ_POLSKIEGO_Ai/PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-esp-runtime-01/output/flash_and_recovery_runbook.md
- [pass] artifact::pin_map: /home/krzysiek/Dokumenty/INFO_GROUP/STRAZ_POLSKIEGO_Ai/PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-esp-runtime-01/output/pin_map.md

## Czego symulacja NIE potwierdza

Symulacja NIE zastepuje testow na realnym hardware. Nastepujace testy wymagaja
fizycznej plytki ESP32 i nie moga byc potwierdzone w symulacji:

- **BT-PWR-01..05**: pomiary napiecia i pradu (wymagaja multimetru + plytka)
- **BT-FLS-01..03**: flashowanie i recovery (wymagaja fizycznego flash + esptool verify)
- **BT-GPIO-01,03,04,05**: fizyczny toggle, ADC, I2C, UART (wymagaja sygnalow)
- **BT-NET-01..04**: Wi-Fi scan, connect, MQTT, RSSI (wymagaja RF)
- **BT-STO-01..02**: odczyt flash i partycji (wymagaja esptool na plytce)

Symulacja moze potwierdzic:

- **BT-GPIO-02**: pin map nie uzywa damaged pins (sprawdzalne bez plytki)
- **BT-FLS-04**: backup firmware istnieje (sprawdzalne na dysku)

## Sciezka: simulated precheck -> real hardware bench

1. **Simulated precheck** (ten raport) — walidacja struktury i spojnosci konfiguracji
2. **Decyzja maintainera** — czy przechodzic do real_hardware (wymaga plytki + pola POMIERZONE)
3. **Bench test real_hardware** — wykonanie BT-PWR..BT-STO na fizycznej plytce
4. **Bench test report** — wyniki z plytki, autorytatywne
5. **Review Wariant B** — reviewer merytoryczny + integrity reviewer
6. **ReadinessGate(integrity_ready) = PASS** -> Approval -> merge

> Zobacz: `docs/BENCH_TEST_CONTRACT_ESP_RUNTIME_01.md` i
> `docs/SIMULATION_VS_REAL_HARDWARE_POLICY_ESP_RUNTIME_01.md`
