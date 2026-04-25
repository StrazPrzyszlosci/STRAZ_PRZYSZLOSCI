# Mini-Handoff Zadanie 22

## Co zostalo zrobione

Utworzono bench test contract i polityke simulated vs real hardware dla `pack-project13-esp-runtime-01`:

- `BENCH_TEST_CONTRACT_ESP_RUNTIME_01.md` — 17 testow w 5 kategoriach (zasilanie, flashowanie, GPIO, siec, storage) z kategoriami `real_hardware`/`simulated`/`either`, reguly statusow i merge, format raportu
- `SIMULATION_VS_REAL_HARDWARE_POLICY_ESP_RUNTIME_01.md` — rozdzielenie symulacji od realnego hardware, reguly przejscia, wymagania board profile per tryb, sprzecznosci
- Zaktualizowano `RUNBOOK.md` — dodano sekcje bench test contract i polityka symulacji
- Zaktualizowano `REVIEW_CHECKLIST.md` — dodano 9 nowych punktow sprawdzajacych (bench test contract + polityka symulacji)
- Zaktualizowano `readiness_gate.json` — 5 sub-gates: review_ready, bench_test_contract_defined (PASS), simulation_policy_defined (PASS), bench_test_real_hardware_pass (pending), integrity_ready (pending)
- Zaktualizowano `manifest.json` — dodano input_contracts dla bench_test_contract i simulation_policy

## Jakie pliki dotknieto

- `PROJEKTY/13_baza_czesci_recykling/docs/BENCH_TEST_CONTRACT_ESP_RUNTIME_01.md` (nowy)
- `PROJEKTY/13_baza_czesci_recykling/docs/SIMULATION_VS_REAL_HARDWARE_POLICY_ESP_RUNTIME_01.md` (nowy)
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-esp-runtime-01/RUNBOOK.md` (zmieniony)
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-esp-runtime-01/REVIEW_CHECKLIST.md` (zmieniony)
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-esp-runtime-01/readiness_gate.json` (zmieniony)
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-esp-runtime-01/manifest.json` (zmieniony)

## Jak rozdzielono symulacje od realnego hardware

- **Symulacja**: walidacja struktury runtime_profile.json, pin map vs board profile, parsowanie Lua bundle, generowanie dokumentacji, sprawdzanie damaged pins. Symulacja jest zawsze dozwolona, ale nigdy nie zastepuje real_hardware.
- **Real hardware**: flashowanie, pomiary elektryczne, testy RF (Wi-Fi/BT), testy GPIO z fizycznym sygnalem, recovery po brick. Bez tych testow merge jest zablokowany.
- **Zasada glowna**: test real_hardware jest autorytatywny. Symulacja moze dac false positive (pin map poprawny strukturalnie, ale fizycznie uszkodzony).

## Jakie gate'y musza byc domkniete przed pierwszym runtime runem

1. `bench_test_contract_defined` — **PASS** (contract istnieje)
2. `simulation_policy_defined` — **PASS** (polityka istnieje)
3. `review_ready` — **PENDING** (wymaga runtime bundle i pre-check symulowany)
4. `bench_test_real_hardware_pass` — **PENDING** (wymaga fizycznej plytki i udanych testow)
5. `integrity_ready` — **PENDING** (wymaga rozdzielonego review i approval)

## Walidacja

- Spojnosc z `REVIEW_ROTATION_GOVERNANCE.md`: Wariant B referowany w obu dokumentach, regula merge z bench reportem zgodna z governance
- Spojnosc z `ESP32_RECOVERED_BOARD_PROFILE_TEMPLATE.md`: pola krytyczne (input_voltage, flash_method, damaged_pins, safety_notes itp.) referowane w bench test contract
- `manifest.json` i `readiness_gate.json`: poprawny JSON
- `git diff --check`: brak bledow whitespace

## Czego nadal brakuje przed execution surface

- Skrypt `generate_esp_runtime.py` — execution surface nie istnieje
- Skrypt `bench_test_esp_runtime.py` — bench test execution surface nie istnieje
- Fizyczna plytka ESP32 do bench testu — brak potwierdzenia dostepnosci
- Pola `[BRAKUJACE]` w sample board profile (power_consumption_*, eeprom, firmware_constraints) — musza byc uzupelnione przez bench test
- Realne wejscie z packa `blueprint-design-01` — pack jest w statusie draft bez execution surface
