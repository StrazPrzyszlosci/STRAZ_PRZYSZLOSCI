# Mini-Handoff Zadanie 40

## Co zostalo zrobione

1. Stworzono `REAL_HARDWARE_BENCH_PACKET.md` — operator-ready bench packet z:
   - wymaganiami wstepnymi (sprzet, oprogramowanie, dokumenty)
   - kolejnoscia testow: BT-PWR -> BT-FLS -> BT-GPIO -> BT-NET -> BT-STO
   - tabelami 20 testow z kategoria, wymaganym wynikiem i potrzebnym sprzetem
   - sciezka testowa krok po kroku (krok 0..6)
   - ograniczeniami i polityka (zadne zmyslone pomiary, rozdzielenie symulacji/real)
2. Stworzono `MEASUREMENT_LEDGER.md` — template ledger z:
   - miejscem na odczyty, obserwacje i verdicty dla kazdego z 20 testow
   - szczegolowymi tabelami dla BT-GPIO-01 (19 free GPIO z osobnymi wierszami)
   - szczegolowymi tabelami dla BT-GPIO-03 (4 kanaly ADC1)
   - wyrazna notatka: zadna wartosc nie zostala wpisana bez fizycznej plytki
3. Stworzono `OPERATOR_PRE_START_CHECKLIST.md` — checklist operatora z:
   - identyfikacja plytki, zasilanie, oprogramowanie, backup, siec, GPIO, dokumenty, governance
   - decyzja o przejsciu z symulacji do real_hardware
4. Stworzono `READINESS_GATE_MAPPING.md` — mapowanie wynikow na sub-gates z:
   - szczegolowym mapowaniem: ktory test domyka ktory sub-gate
   - flow domkniecia sub-gates (bench_test_real_hardware_pass, review_ready, integrity_ready)
   - lista tego, co nadal musi potwierdzic osobny reviewer albo integrity review
   - pola BRAKUJACE (power_consumption_idle, power_consumption_wifi_tx), ktore bench test uzupelni
5. Zaktualizowano pack metadata:
   - `manifest.json`: status -> `real_hardware_bench_packet_ready`, dodano output_paths i expected_artifacts, dodano sekcje `real_hardware_bench_packet`
   - `readiness_gate.json`: status -> `real_hardware_bench_packet_ready`, dodano sub-gate `real_hardware_bench_packet_ready` = pass, zaktualizowano notes i checked_at
   - `task.json`: status -> `real_hardware_bench_packet_ready`, zaktualizowano updated_at
   - `RUNBOOK.md`: dodano sekcje o real hardware bench packet i instrukcje operatora

## Jakie pliki dotknieto

- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-esp-runtime-01/output/REAL_HARDWARE_BENCH_PACKET.md` (nowy)
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-esp-runtime-01/output/MEASUREMENT_LEDGER.md` (nowy)
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-esp-runtime-01/output/OPERATOR_PRE_START_CHECKLIST.md` (nowy)
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-esp-runtime-01/output/READINESS_GATE_MAPPING.md` (nowy)
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-esp-runtime-01/manifest.json` (zmieniony)
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-esp-runtime-01/readiness_gate.json` (zmieniony)
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-esp-runtime-01/task.json` (zmieniony)
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-esp-runtime-01/RUNBOOK.md` (zmieniony)
- `docs/AGENTY_PODWYKONAWCZE/MINI_HANDOFF_ZADANIE_40.md` (nowy)

## Jakie testy maja byc wykonane jako pierwsze po dostaniu plytki

1. **BT-PWR-01..05** — zasilanie jest warunkiem wszystkich pozostalych testow
2. **BT-FLS-01..04** — flashowanie jest warunkiem testow runtime (GPIO, NET, STO)
3. **BT-GPIO-01..05** — peryferia po flash
4. **BT-NET-01..04** — siec po GPIO
5. **BT-STO-01..02** — diagnostyka koncowa

Kazdy odczyt wpisujemy do `MEASUREMENT_LEDGER.md`. Nie pomijamy zadnego testu — kolejnosc jest obowiazkowa.

## Jak wyniki mapuja sie na readiness_gate

- **bench_test_real_hardware_pass**: wszystkie 20 testow real_hardware = PASS albo NOT_APPLICABLE -> sub-gate PASS. Jeden FAIL = sub-gate FAIL.
- **review_ready**: bench_test_report.md wypelniony + measurement_ledger wypelniony + runtime_profile nie stub -> sub-gate PASS.
- **integrity_ready**: bench_test_real_hardware_pass = PASS + IntegrityRiskAssessment zaktualizowany + reviewer merytoryczny zaakceptowal + integrity reviewer zaakceptowal -> sub-gate PASS.

Patrz: `output/READINESS_GATE_MAPPING.md` po szczegoly.

## Co nadal musi potwierdzic osobny reviewer albo integrity review

1. Reviewer merytoryczny: wyniki bench testu spojne z board profile, runtime bundle kompletny, pin map nie uzywa damaged pins, recovery path wykonalny.
2. Integrity reviewer: IntegrityRiskAssessment zaktualizowany, pack nie steruje swiatem fizycznym bez bench testu, sekrety nie w diffie, brak vendor lock-in, approver nie jest reviewerem.
3. Approver: potwierdza, ze review merytoryczny i integrity review sa domkniete, podejmuje decyzje o merge.

## Nowy status packa

- `manifest.status`: `real_hardware_bench_packet_ready`
- `readiness_gate.status`: `real_hardware_bench_packet_ready`
- `task.status`: `real_hardware_bench_packet_ready`
- Sub-gates: `simulated_precheck_pass`=pass, `real_hardware_bench_packet_ready`=pass, `bench_test_contract_defined`=pass, `simulation_policy_defined`=pass, `review_ready`=pending, `bench_test_real_hardware_pass`=pending, `integrity_ready`=pending

## Otwarte ryzyka

- Packet nie wpisuje zadnych pomiarow — operator z realna plytka musi wypelnic measurement ledger
- 3 warnings z simulated precheck (power_consumption BRAKUJACE) — bench test uzupelni te pola
- Brak skryptu `bench_test_esp_runtime.py` — operator wykonuje testy recznie z użyciem REAL_HARDWARE_BENCH_PACKET.md i MEASUREMENT_LEDGER.md
- Brak Lua runtime bundle — niezbedny przed review_ready
- Brak realnego runtime_profile.json (aktualny to stub z dry_run=true)
