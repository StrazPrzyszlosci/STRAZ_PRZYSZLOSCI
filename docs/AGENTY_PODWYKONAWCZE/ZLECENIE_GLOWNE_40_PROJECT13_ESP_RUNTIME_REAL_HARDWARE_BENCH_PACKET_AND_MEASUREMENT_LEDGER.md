# Zlecenie Glowne 40 Project13 ESP Runtime Real Hardware Bench Packet And Measurement Ledger

## 1. Misja zadania

Na bazie simulated precheck z `34` przygotuj operator-ready packet do pierwszego realnego bench testu `esp-runtime`. Chodzi o measurement ledger, kolejnosc testow i mapowanie wynikow do `readiness_gate`, ale bez wpisywania zadnych zmyslonych pomiarow.

## 2. Wyzszy cel organizacji

Po `34` wiemy juz, co pack potrafi bez plytki.
To zadanie ma przygotowac przejscie z symulacji do fizycznego hardware tak, zeby pierwszy operator z realna plytka nie zaczynal od pustej kartki.

## 3. Read First

- `docs/AGENTY_PODWYKONAWCZE/ODBIOR_PORTFELA_09_ZADAN_29_34_2026-04-28.md`
- `docs/AGENTY_PODWYKONAWCZE/MINI_HANDOFF_ZADANIE_34.md`
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/simulated_precheck_esp_runtime_01_2026-04-28.md`
- `PROJEKTY/13_baza_czesci_recykling/docs/BENCH_TEST_CONTRACT_ESP_RUNTIME_01.md`
- `PROJEKTY/13_baza_czesci_recykling/docs/SIMULATION_VS_REAL_HARDWARE_POLICY_ESP_RUNTIME_01.md`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-esp-runtime-01/`

## 4. Write Scope

- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-esp-runtime-01/`
- `PROJEKTY/13_baza_czesci_recykling/docs/`
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/`

## 5. Deliverables

- bench packet dla realnego hardware z kolejnoscia testow `BT-PWR`, `BT-FLS`, `BT-GPIO`, `BT-NET`, `BT-STO`
- measurement ledger template z miejscem na odczyty, obserwacje i verdicty
- mapowanie: ktory wynik domyka ktory sub-gate w `readiness_gate`
- jesli to pomaga: checklist operatora przed startem testu na plytce
- mini-handoff z tym, co juz da sie zrobic po otrzymaniu prawdziwej plytki

## 6. Acceptance Criteria

- operator z realna plytka widzi jedna spojna sciezke testowa od pierwszego wlaczenia do verdictu bench testu
- packet nie wpisuje zadnych pomiarow ani `PASS` bez realnego hardware
- sub-gates `review_ready`, `bench_test_real_hardware_pass` i `integrity_ready` maja jawny handoff do artefaktow i pomiarow
- symulacja i real hardware pozostaja rozdzielone zgodnie z policy

## 7. Walidacja

- kontrola spojnosci z `BENCH_TEST_CONTRACT_ESP_RUNTIME_01.md`
- kontrola spojnosci z `SIMULATION_VS_REAL_HARDWARE_POLICY_ESP_RUNTIME_01.md`
- jesli zmieniasz JSON-y packa: kontrola parsowania JSON
- `git diff --check`

## 8. Blokery

Brak realnej plytki nie blokuje przygotowania packetu i measurement ledgera.
Nie wolno jednak oznaczac bench testu jako wykonanego ani domykac gate bez prawdziwych pomiarow.

## 9. Mini-handoff

Zapisz:

- jaki packet i ledger dodano,
- jakie testy maja byc wykonane jako pierwsze po dostaniu plytki,
- jak wyniki mapuja sie na `readiness_gate`,
- co nadal musi potwierdzic osobny reviewer albo integrity review.
