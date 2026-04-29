# Readiness Gate Mapping: Bench Test Results to Sub-Gates

- pack_id: pack-project13-esp-runtime-01
- board_id: recovered-esp-devkitc-v4-01
- created_at: 2026-04-29

---

## 1. Sub-gates w readiness_gate.json

Stan aktualny (po zadaniu 34):

| Sub-gate | Status | Opis |
|----------|--------|------|
| simulated_precheck_pass | pass | Symulacja przeszla conditional (38 pass, 3 warn, 0 fail) |
| review_ready | pending | Runtime bundle czytelny z provenance i acceptance criteria |
| bench_test_contract_defined | pass | BENCH_TEST_CONTRACT istnieje |
| simulation_policy_defined | pass | SIMULATION_VS_REAL_HARDWARE_POLICY istnieje |
| bench_test_real_hardware_pass | pending | Wszystkie testy real_hardware = PASS albo NOT_APPLICABLE |
| integrity_ready | pending | IntegrityRiskAssessment domkniety, Wariant B governance |

---

## 2. Mapowanie testow -> sub-gates

### 2.1 bench_test_real_hardware_pass

Ten sub-gate wymaga: wszystkie testy `real_hardware` = PASS albo NOT_APPLICABLE.

| Test ID | Wymagalnosc dla sub-gate | Uwagi |
|---------|--------------------------|-------|
| BT-PWR-01 | PASS wymagany | Bez stabilnego napiecia wejsciowego dalsze testy niewiarygodne |
| BT-PWR-02 | PASS wymagany | Bez stabilnego 3.3V runtime niestabilny |
| BT-PWR-03 | PASS wymagany (pomiar zrealizowany) | Brak wartosci referencyjnej = BRAKUJACE, ale pomiar musi byc zrealizowany |
| BT-PWR-04 | PASS wymagany (pomiar zrealizowany) | Jw. |
| BT-PWR-05 | PASS wymagany | Brownout = FAIL = caly sub-gate FAIL |
| BT-FLS-01 | PASS wymagany | Bez udanego flash nie ma runtime |
| BT-FLS-02 | PASS wymagany | Bez download mode nie da sie flashowac powtarzalnie |
| BT-FLS-03 | PASS wymagany | Bez recovery path brick jest nieodwracalny |
| BT-FLS-04 | PASS albo NOT_APPLICABLE | Backup na dysku albo jawne NIE DOTYCZY |
| BT-GPIO-01 | PASS wymagany | Fizycznie uszkodzony pin = FAIL na tym tescie |
| BT-GPIO-02 | PASS wymagany (either) | Sprawdzalne bez plytki, ale wchodzi w sub-gate |
| BT-GPIO-03 | PASS wymagany | ADC jest krytyczny dla peryferiow |
| BT-GPIO-04 | PASS albo NOT_APPLICABLE | Brak I2C na plytce = NOT_APPLICABLE z jawnym uzasadnieniem |
| BT-GPIO-05 | PASS wymagany | UART0 to podstawowy kanaal diagnostyczny |
| BT-NET-01 | PASS wymagany | Wi-Fi scan = minimalna weryfikacja RF |
| BT-NET-02 | PASS wymagany | Connect do AP = podstawowa funkcja sieciowa |
| BT-NET-03 | PASS albo NOT_APPLICABLE | MQTT = opcjonalny, ale jezeli deklarowany to musi dzialac |
| BT-NET-04 | PASS wymagany | RSSI >= -80dBm = akceptowalna jakosc anteny |
| BT-STO-01 | PASS wymagany | Rozmiar flash musi byc zgodny z board profile |
| BT-STO-02 | PASS wymagany | Partycje musza byc czytelne |

**Regula domkniecia**: `bench_test_real_hardware_pass` = PASS jesli wszystkie 20 testow powyzej = PASS albo NOT_APPLICABLE. Jeden FAIL = sub-gate FAIL.

### 2.2 review_ready

Ten sub-gate wymaga: runtime bundle czytelny, ma provenance i acceptance criteria.

| Artefakt | Wymagalnosc | Jak bench test domyka |
|----------|-------------|----------------------|
| runtime_profile.json | Nie stub (dry_run=false, simulated=false) | BT-FLS-01 potwierdza, ze plytka przyjela firmware -> runtime_profile moze byc podniesiony do real |
| pin_map.md | Spojny z pomiarami GPIO | BT-GPIO-01 potwierdza, ze free piny dzialaja -> pin_map jest weryfikowany |
| lua_runtime_bundle/ | Istnieje i jest parsowalny | Niezbedny przed bench test, ale bench test weryfikuje jego dzialanie na plytce |
| bench_test_report.md | Z prawdziwymi wynikami, nie PENDING | Wszystkie testy real_hardware wypelnione -> report jest review-ready |
| measurement_ledger.md | Wypelniony odczytami z plytki | Ledger z odczytami = provenance pomiarow |

**Regula domkniecia**: `review_ready` = PASS jesli bench_test_report.md i measurement_ledger.md sa wypelnione, a runtime_profile nie jest stub.

### 2.3 integrity_ready

Ten sub-gate wymaga: IntegrityRiskAssessment domkniety, Wariant B governance.

| Wymaganie | Jak bench test domyka |
|-----------|----------------------|
| IntegrityRiskAssessment status = assessed | Po bench tescie: risk_level moze byc zaktualizowany na podstawie wynikow |
| Brak ukrytych uszkodzonych pinow | BT-GPIO-01 i BT-GPIO-02 potwierdzaja, ze pin map nie ukrywa uszkodzen |
| Brak sterowania fizycznym bez bench testu | Bench test wykonany = to wymaganie jest spelnione |
| Sekrety nie w diffie | Jawny check w REVIEW_CHECKLIST — operator potwierdza |
| Reviewer merytoryczny ocenil wyniki | Review po bench tescie (Wariant B flow) |
| Integrity reviewer ocenil governance | Integrity review po bench tescie (Wariant B flow) |

**Regula domkniecia**: `integrity_ready` = PASS jesli:
1. bench_test_real_hardware_pass = PASS
2. IntegrityRiskAssessment zaktualizowany po wynikach bench testu
3. Reviewer merytoryczny zaakceptowal wyniki
4. Integrity reviewer zaakceptowal governance
5. Approver nie jest jednoczesnie reviewerem

---

## 3. Flow domkniecia sub-gates

```
bench test na real hardware
|
+-- BT-PWR-01..05 -> odczyty w measurement_ledger
+-- BT-FLS-01..04 -> odczyty w measurement_ledger
+-- BT-GPIO-01..05 -> odczyty w measurement_ledger
+-- BT-NET-01..04 -> odczyty w measurement_ledger
+-- BT-STO-01..02 -> odczyty w measurement_ledger
|
v
wszystkie real_hardware = PASS albo NOT_APPLICABLE?
|
+-- TAK -> bench_test_real_hardware_pass = PASS
|           |
|           +-> runtime_profile nie stub, pin_map zweryfikowany
|           +-> review_ready = PASS
|           |
|           +-> reviewer merytoryczny ocenia wyniki
|           +-> integrity reviewer ocenia governance
|           +-> IntegrityRiskAssessment zaktualizowany
|           +-> integrity_ready = PASS
|           |
|           +-> Approval -> merge
|
+-- NIE -> bench_test_real_hardware_pass = FAIL albo PENDING
            |
            +-> review_ready = pending (brak wypelnionego report)
            +-> integrity_ready = pending (brak review)
            +-> merge zablokowany
```

---

## 4. Co nadal musi potwierdzic osobny reviewer albo integrity review

Nawet po bench test PASS:

1. **Reviewer merytoryczny** musi potwierdzic:
   - Wyniki bench testu sa spojne z board profile (napiecie, GPIO, siec)
   - Runtime bundle jest kompletny (runtime_profile, pin_map, lua_bundle, runbook)
   - Pin map nie uzywa uszkodzonych pinow (cross-check z BT-GPIO-01/02)
   - Recovery path jest wykonalny (cross-check z BT-FLS-03)

2. **Integrity reviewer** musi potwierdzic:
   - IntegrityRiskAssessment odpowiada realnej zmianie
   - Pack nie steruje swiatem fizycznym bez bench testu (spelnione przez wykonanie testu)
   - Sekrety nie trafiaja do firmware ani diffu
   - Brak vendor lock-in (jawne alternatywy)
   - Approver nie jest jednoczesnie glownym reviewerem

3. **Approver** (nie bedacy reviewerem) musi:
   - Potwierdzic, ze review merytoryczny i integrity review sa domkniete
   - Podjac decyzje o merge

---

## 5. Pola BRAKUJACE, ktore bench test uzupelni

| Pole board profile | Status przed bench | Jak bench test uzupelni |
|--------------------|--------------------|------------------------|
| power_consumption_idle | BRAKUJACE | BT-PWR-03 wpisuje zmierzona wartosc do measurement_ledger |
| power_consumption_wifi_tx | BRAKUJACE | BT-PWR-04 wpisuje zmierzona wartosc do measurement_ledger |

Po bench tescie operator powinien zaktualizowac board profile z BRAKUJACE na POMIERZONE dla tych dwoch pol, wpisujac wartosci z measurement_ledger.
