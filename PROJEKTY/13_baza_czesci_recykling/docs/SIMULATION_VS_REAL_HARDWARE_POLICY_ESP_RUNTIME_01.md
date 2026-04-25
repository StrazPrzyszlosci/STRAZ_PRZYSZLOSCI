# Simulation vs Real Hardware Policy Dla Pack Project13 ESP Runtime 01

## Cel dokumentu

Ten dokument definiuje politykę rozdzielenia symulacji od realnego hardware w `pack-project13-esp-runtime-01`. Odpowiada na pytanie: co wolno zrobić w symulacji, co wymaga realnej plytki, i kto decyduje o przejściu z jednego trybu do drugiego.

---

## 1. Definicje

### Symulacja (simulated mode)

Dowolna weryfikacja runtime bundle **bez** fizycznej plytki ESP32. Obejmuje:

- walidację strukturalną konfiguracji i pin map,
- parsowanie i sprawdzanie Lua bundle,
- generowanie dokumentacji (runtime profile, flash runbook),
- pre-check kodu i konfiguracji przed flash.

### Real hardware (real mode)

Dowolna weryfikacja runtime bundle **z** fizyczną plytką ESP32 podłączoną do komputera testowego. Obejmuje:

- flashowanie firmware,
- pomiary elektryczne (napięcie, prąd),
- testy RF (Wi-Fi, Bluetooth),
- testy GPIO z fizycznym sygnałem,
- recovery po brick.

---

## 2. Co wolno w symulacji

Symulacja jest **zawsze dozwolona** jako krok pośredni. Nigdy nie jest warunkiem koniecznym, ale nigdy nie jest też zastępstwem dla real_hardware testu.

Dozwolone w symulacji:

| Czynność | Czy wymaga plytki | Czy może być mergowana |
|----------|-------------------|----------------------|
| Walidacja runtime_profile.json (schema, required fields) | NIE | NIE — tylko pre-check |
| Sprawdzenie pin map vs board profile (spójność) | NIE | NIE — tylko pre-check |
| Parsowanie Lua bundle (składnia) | NIE | NIE — tylko pre-check |
| Generowanie flash_and_recovery_runbook.md | NIE | NIE — tylko dokumentacja |
| Sprawdzenie, czy damaged pins są wykluczone | NIE | NIE — tylko pre-check |
| Walidacja board profile przed wejściem do packa | NIE | NIE — tylko pre-check |

Symulacja może produkować artefakty draft, ale **nie może promować runtime bundle do merge**.

---

## 3. Co wymaga realnej plytki

| Czynność | Czy wymaga plytki | Uzasadnienie |
|----------|-------------------|-------------|
| Flash firmware | TAK | Flashowanie modyfikuje fizyczny storage plytki |
| Pomiar napięcia wejściowego i roboczego | TAK | Bez multimetru i plytki wynik jest domniemany |
| Pomiar prądu idle / Wi-Fi TX | TAK | Prąd jest właściwością fizyczną, nie konfiguracyjną |
| Test GPIO toggle | TAK | Stan pinu trzeba odczytać fizycznie |
| Test ADC | TAK | ADC wymaga napięcia referencyjnego na wejściu |
| Test I2C scan | TAK | Magistrala I2C wymaga fizycznych slave'ów |
| Test Wi-Fi scan i connect | TAK | RF nie da się symulować wiarygodnie |
| Test MQTT publish | TAK | MQTT wymaga działania sieci |
| Recovery po brick | TAK | Bricking i odzysk dotyczą fizycznego storage |
| Test RSSI / anteny | TAK | RF jest właściwością fizyczną |

---

## 4. Przejście z symulacji do realnego hardware

### Kiedy przejść

Przejście jest możliwe, gdy:

1. Runtime bundle przechodzi wszystkie testy symulowane (pre-check).
2. Board profile ma pola `[POMIERZONE]` uzupełnione w sekcjach krytycznych (zasilanie, flashowanie, GPIO, antena).
3. Fizyczna plytka jest dostępna i zidentyfikowana (board_id match).
4. Flash method jest znany i sprawdzony na tej konkretnej plytce.

### Kto decyduje

Decyzję o przejściu z symulacji do real_hardware podejmuje **maintainer prowadzący runtime**, po:

- sprawdzeniu, że pre-check symulowany przeszedł,
- weryfikacji, że board profile nie ma pól `[BRAKUJACE]` w sekcjach krytycznych,
- potwierdzeniu dostępności plytki.

W Governance Wariant B ta decyzja nie wymaga approval — jest decyzją operacyjną. Ale bench test na real_hardware musi przejść pełny flow review przed merge.

---

## 5. Co, jeśli plytka nie jest dostępna

Jeśli fizyczna plytka ESP32 nie jest dostępna:

- Runtime bundle może być generowany w trybie `draft` z pełnym pre-check symulowanym.
- Wszystkie testy `real_hardware` otrzymują status `PENDING` w bench test report.
- **Runtime bundle nie może być mergowany.**
- Prace nad runtime profile, pin map, Lua bundle, flash runbook mogą trwać.
- Kiedy plytka stanie się dostępna, bench test real_hardware jest uruchamiany jako pierwszy krok.

To **nie jest** blokada inicjatywy — to blokada promocji do realnego runtime bez weryfikacji.

---

## 6. Co, jeśli symulacja i real_hardware dają sprzeczne wyniki

Jeśli test symulowany przeszedł, ale test na real_hardware nie:

- Wynik real_hardware jest **zawsze** autorytatywny.
- Symulacja może produkować false positives (np. pin map poprawny strukturalnie, ale pin fizycznie uszkodzony).
- Nigdy nie wolno nadpisywać wyniku real_hardware wynikiem symulowanym.
- Sprzeczność musi być odnotowana w bench test report z analizą przyczyny.

---

## 7. Pola board profile a tryb testu

| Pole board profile | Minimalny status dla symulacji | Minimalny status dla real_hardware |
|-------------------|-------------------------------|-----------------------------------|
| `board_id` | `[POMIERZONE]` | `[POMIERZONE]` |
| `board_variant` | `[POMIERZONE]` | `[POMIERZONE]` |
| `input_voltage` | `[DOMNIEMANE]` | `[POMIERZONE]` |
| `operating_voltage` | `[DOMNIEMANE]` | `[POMIERZONE]` |
| `flash_method` | `[POMIERZONE]` | `[POMIERZONE]` |
| `boot_mode_entry` | `[POMIERZONE]` | `[POMIERZONE]` |
| `recovery_after_brick` | `[POMIERZONE]` | `[POMIERZONE]` |
| `antenna_condition` | `[DOMNIEMANE]` | `[POMIERZONE]` |
| `damaged_pins` | `[DOMNIEMANE]` | `[POMIERZONE]` |
| `safety_notes` | `[POMIERZONE]` | `[POMIERZONE]` |
| `power_consumption_*` | `[BRAKUJACE]` dopuszczalne | `[BRAKUJACE]` → test `PENDING` |

Zasada: im bliżej fizycznego świata, tym więcej pól musi być `[POMIERZONE]`.

---

## 8. Governance Wariant B — wpisanie w politykę

Zgodnie z `REVIEW_ROTATION_GOVERNANCE.md`:

- Hardware runtime wymaga Wariantu B: rozdzielony reviewer merytoryczny i integrity reviewer.
- Promocja do hardware runtime wymaga bench reportu (sekcja 7 w `BENCH_TEST_CONTRACT_ESP_RUNTIME_01.md`).
- Brak merge bez domkniętego `ReadinessGate(integrity_ready)`.
- Brak self-approval.
- Brak merge z testami `PENDING` albo `FAIL` na kategorii `real_hardware`.

### Flow polityki w Wariantcie B

```text
1. Symulacja (pre-check)
   - runtime_profile.json valid
   - pin_map spójny z board_profile
   - Lua bundle parsowalny
   - damaged pins wykluczone

2. Decyzja maintainera: przejście do real_hardware
   - board profile ma pola krytyczne jako [POMIERZONE]
   - plytka dostępna

3. Bench test real_hardware
   - sekcje 1.1-1.5 z BENCH_TEST_CONTRACT
   - bench_test_report.md

4. Review
   - reviewer merytoryczny: wyniki bench testu
   - integrity reviewer: governance, brak ukrytych ryzyk
   - approver: nie jest reviewerem

5. ReadinessGate(integrity_ready) = PASS

6. Approval → merge
```
