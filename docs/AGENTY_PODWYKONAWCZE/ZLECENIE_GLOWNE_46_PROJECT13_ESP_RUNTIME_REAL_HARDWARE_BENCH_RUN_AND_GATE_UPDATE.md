# Zlecenie Glowne 46 Project13 ESP Runtime Real Hardware Bench Run And Gate Update

## 1. Misja zadania

Wykonaj realny bench test `esp-runtime` na fizycznej plytce, korzystajac z packetu z zadania `40`.

Jesli fizyczna plytka nie jest dostepna, zapisz blocker receipt. Nie wpisuj zadnych pomiarow symulowanych jako real hardware.

## 2. Wyzszy cel organizacji

Po `40` operator wie, jak mierzyc.
Teraz potrzebny jest realny pomiar, ktory moze odblokowac `bench_test_real_hardware_pass`, `review_ready` i pozniejszy `integrity_ready`.

## 3. Read First

- `docs/HANDOFF_DLA_NASTEPNEGO_AGENTA_2026-04-29.md`
- `docs/AGENTY_PODWYKONAWCZE/MINI_HANDOFF_ZADANIE_40.md`
- `PROJEKTY/13_baza_czesci_recykling/docs/BENCH_TEST_CONTRACT_ESP_RUNTIME_01.md`
- `PROJEKTY/13_baza_czesci_recykling/docs/SIMULATION_VS_REAL_HARDWARE_POLICY_ESP_RUNTIME_01.md`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-esp-runtime-01/output/REAL_HARDWARE_BENCH_PACKET.md`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-esp-runtime-01/output/MEASUREMENT_LEDGER.md`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-esp-runtime-01/output/READINESS_GATE_MAPPING.md`

## 4. Write Scope

- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-esp-runtime-01/output/MEASUREMENT_LEDGER.md`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-esp-runtime-01/output/bench_test_report.md`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-esp-runtime-01/readiness_gate.json`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-esp-runtime-01/manifest.json`
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/esp_runtime_bench_receipt_*.json`
- `docs/AGENTY_PODWYKONAWCZE/MINI_HANDOFF_ZADANIE_46.md`

## 5. Deliverables

- wypelniony `MEASUREMENT_LEDGER.md` z realnymi odczytami
- `bench_test_report.md` z verdictami dla `BT-PWR`, `BT-FLS`, `BT-GPIO`, `BT-NET`, `BT-STO`
- `esp_runtime_bench_receipt_YYYY-MM-DD.json`
- aktualizacja readiness gate tylko zgodnie z realnymi wynikami
- mini-handoff

## 6. Acceptance Criteria

- kazdy wpis pomiarowy pochodzi z fizycznej plytki
- status `bench_test_real_hardware_pass` przechodzi na `pass` tylko jesli wszystkie wymagane testy sa `PASS` albo `NOT_APPLICABLE`
- `PENDING` i `FAIL` nie sa traktowane jak `PASS`
- sekrety Wi-Fi/MQTT nie trafiaja do repo
- jesli bench test nie moze sie odbyc, nie zmieniaj gate na pass

## 7. Walidacja

- kontrola zgodnosci z `BENCH_TEST_CONTRACT_ESP_RUNTIME_01.md`
- kontrola zgodnosci z `READINESS_GATE_MAPPING.md`
- kontrola parsowania zmienionych JSON:
  - `python3 -m json.tool PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-esp-runtime-01/readiness_gate.json`
  - `python3 -m json.tool PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-esp-runtime-01/manifest.json`
- `git diff --check`

## 8. Blokery

Brak fizycznej plytki, zasilania, miernika, firmware albo operatora blokuje realny bench.
Zapisz blocker receipt zamiast wpisywac placeholderowe pomiary.

## 9. Mini-handoff

Zapisz:

- czy bench test faktycznie wykonano,
- jaki byl wynik kazdej grupy `BT-*`,
- ktore sub-gates sa nadal pending,
- jakie pomiary albo reviewerzy sa jeszcze potrzebni,
- czy pack moze isc do merytorycznego review.
