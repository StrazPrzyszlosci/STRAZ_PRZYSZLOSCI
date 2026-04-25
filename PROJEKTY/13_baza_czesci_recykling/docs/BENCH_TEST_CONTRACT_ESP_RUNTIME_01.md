# Bench Test Contract Dla Pack Project13 ESP Runtime 01

## Cel dokumentu

Ten dokument definiuje bench test contract — jawną listę testów, które muszą przejść przed pierwszym flashowaniem albo merge runtime bundle do `pack-project13-esp-runtime-01`.

Bez bench testu pack nie promuje runtime do realnego hardware. To nie jest rekomendacja — to twardy kontrakt.

---

## 1. Co musi być przetestowane przed pierwszym flash

### 1.1 Zasilanie (power)

| Test ID | Test | Kategoria | Wymagany wynik |
|---------|------|-----------|---------------|
| `BT-PWR-01` | Pomiar napięcia wejściowego vs `input_voltage` z board profile | real_hardware | Δ ≤ 0.2V od deklarowanej wartości |
| `BT-PWR-02` | Pomiar napięcia roboczego MCU vs `operating_voltage` z board profile | real_hardware | Δ ≤ 0.1V od 3.3V (typowe) |
| `BT-PWR-03` | Pomiar prądu idle vs `power_consumption_idle` z board profile | real_hardware | Pomiar zrealizowany; brak wartości = `BRAKUJACE` → test pending |
| `BT-PWR-04` | Pomiar prądu Wi-Fi TX vs `power_consumption_wifi_tx` z board profile | real_hardware | Pomiar zrealizowany; brak wartości = `BRAKUJACE` → test pending |
| `BT-PWR-05` | Stabilność zasilania pod obciążeniem (GPIO + Wi-Fi jednocześnie) | real_hardware | Brak brownout reset w ciągu 60s |

### 1.2 Flashowanie (recovery path)

| Test ID | Test | Kategoria | Wymagany wynik |
|---------|------|-----------|---------------|
| `BT-FLS-01` | Flash firmware przez metodę zadeklarowaną w `flash_method` | real_hardware | Sukces — firmware załadowany, verified by `esptool verify` |
| `BT-FLS-02` | Wejście w download mode przez `boot_mode_entry` | real_hardware | Plytka wchodzi w download mode powtarzalnie |
| `BT-FLS-03` | Recovery po brick — reflashing przez `recovery_after_brick` | real_hardware | Plytka odzyskana po celowym bricku |
| `BT-FLS-04` | Backup oryginalnego firmware istnieje lub `backup_firmware_available = NIE DOTYCZY` | either | Plik `.bin` istnieje na dysku albo jawny NIE DOTYCZY |

### 1.3 GPIO i peryferia

| Test ID | Test | Kategoria | Wymagany wynik |
|---------|------|-----------|---------------|
| `BT-GPIO-01` | Każdy pin oznaczony jako `free` w board profile odpowiada na toggle | real_hardware | Odczyt zwrotny potwierdza stan HIGH/LOW |
| `BT-GPIO-02` | Piny oznaczone jako `damaged` są wykluczone z pin map | either | Pin map nie przypisuje funkcji do damaged pins |
| `BT-GPIO-03` | ADC1 odczyt z napięcia referencyjnego | real_hardware | Odczyt ±10% wartości oczekiwanej |
| `BT-GPIO-04` | I2C scan — wykrycie przynajmniej jednego slave na magistrali | real_hardware | Adres slave wykryty albo jawne `no I2C device on this board` |
| `BT-GPIO-05` | UART0 komunikacja serial | real_hardware | Echo test — znak wysłany, znak odebrany |

### 1.4 Sieć i komunikacja

| Test ID | Test | Kategoria | Wymagany wynik |
|---------|------|-----------|---------------|
| `BT-NET-01` | Wi-Fi scan — plytka widzi sieci 2.4GHz | real_hardware | Przynajmniej 1 sieć wykryta |
| `BT-NET-02` | Wi-Fi connect do testowego AP | real_hardware | Połączenie nawiązane w ≤ 10s |
| `BT-NET-03` | MQTT publish do testowego broker | real_hardware | Message delivered, broker potwierdza |
| `BT-NET-04` | Antena — jakość sygnału (RSSI) | real_hardware | RSSI ≥ -80dBm w odległości 3m od AP |

### 1.5 Storage

| Test ID | Test | Kategoria | Wymagany wynik |
|---------|------|-----------|---------------|
| `BT-STO-01` | Rozmiar flash odczytany przez `esptool` vs `flash_size` z board profile | real_hardware | Zgodność ±0 (dokładny rozmiar) |
| `BT-STO-02` | Odczyt tabeli partycji | real_hardware | Partycje czytelne, spójne z `partition_table` z board profile |

---

## 2. Kategoria testów: simulated vs real_hardware

Każdy test ma przypisaną kategorię:

- **`real_hardware`** — wymaga fizycznej plytki ESP32. Nie da się zastąpić symulacją.
- **`simulated`** — może być wykonany bez fizycznej plytki, np. walidacja pin map, sprawdzenie konfiguracji.
- **`either`** — może być wykonany w symulacji z zastępczym wynikiem, ale real_hardware jest docelowo wymagany.

### Reguła kategoryzacji

1. Każdy test dotykający fizycznego napięcia, prądu, RF albo flashowania jest `real_hardware`.
2. Testy strukturalne (czy pin map nie używa damaged pins, czy konfiguracja jest spójna) mogą być `simulated`.
3. Żaden test `real_hardware` nie może zostać zastąpiony wynikiem `simulated` w bench test report dla celów merge.

---

## 3. Kolejność testów

Bench test wykonuje się w kolejności zasilanie → flashowanie → GPIO → sieć → storage:

1. Zasilanie (BT-PWR-*) — bez stabilnego zasilania dalsze testy są niewiarygodne
2. Flashowanie (BT-FLS-*) — bez udanego flash nie da się testować runtime
3. GPIO (BT-GPIO-*) — peryferia po flash
4. Sieć (BT-NET-*) — komunikacja po GPIO
5. Storage (BT-STO-*) — diagnostyka końcowa

---

## 4. Wynik bench testu

### Statusy pojedynczego testu

| Status | Znaczenie |
|--------|-----------|
| `PASS` | Test przeszedł, wynik w granicach akceptacji |
| `FAIL` | Test nie przeszedł — runtime nie może być promowany |
| `SKIP` | Test pominięty z jawnego powodu (np. brak I2C na plytce) |
| `PENDING` | Test nie wykonany — brak real_hardware albo brak pola w board profile |
| `NOT_APPLICABLE` | Test nie dotyczy tej konfiguracji (np. brak BLE w tym wariancie ESP32) |

### Reguła merge

- Runtime bundle może być mergowany tylko jeśli **wszystkie testy `real_hardware`** mają status `PASS` albo `NOT_APPLICABLE`.
- Testy `PENDING` blokują merge — nie wolno traktować `PENDING` jak `PASS`.
- Jeden `FAIL` na teście `real_hardware` blokuje cały runtime bundle.
- Testy `simulated` nie zastępują testów `real_hardware`.

---

## 5. Co wolno w symulacji, a co wymaga realnej plytki

### Wolno w symulacji (bez fizycznej plytki)

- Walidacja struktury runtime profile (JSON schema, required fields)
- Sprawdzenie pin map vs board profile (czy damaged pins są wykluczone)
- Walidacja Lua bundle (składnia, brak ukrytych zależności)
- Generowanie flash runbook (dokumentacja, nie flash)
- Sprawdzenie obecności i poprawności board profile

### Wymaga realnej plytki (nie zastąpi symulacja)

- Każdy test z kategorią `real_hardware` w sekcji 1
- Flashowanie firmware
- Pomiar napięcia i prądu
- Testy RF (Wi-Fi, Bluetooth)
- Testy GPIO z fizycznym odczytem/odczytem
- Recovery po brick

### Symulacja jako krok pośredni

Symulacja może być uruchomiona **przed** real_hardware bench testem jako pre-check. Przejście symulacji nie jest warunkiem merge, ale może oszczędzić czas na early detection błędów konfiguracyjnych.

---

## 6. Governance Wariant B a bench test

Zgodnie z `REVIEW_ROTATION_GOVERNANCE.md` Wariant B:

- Bench test report jest wymagany przed `ReadinessGate(integrity_ready)`
- Reviewer merytoryczny sprawdza: poprawność wyników, spójność z board profile
- Integrity reviewer sprawdza: czy runtime nie steruje fizycznie bez bench testu, czy nie ukryto uszkodzonych pinów
- Approver nie jest jednocześnie głównym reviewerem
- Brak self-approval

### Flow bench testu w Wariantcie B

```text
runtime bundle wygenerowany
  -> pre-check symulowany (opcjonalny, nie blokuje)
  -> bench test real_hardware
  -> bench_test_report.md z wynikami
  -> reviewer merytoryczny ocenia wyniki
  -> integrity reviewer ocenia governance
  -> ReadinessGate(integrity_ready) = PASS
  -> Approval
  -> merge
```

---

## 7. Raport bench test

Format `bench_test_report.md`:

```markdown
# Bench Test Report: <board_id>

## Metryka
- Data testu
- board_id
- board_variant
- flash_method
- Tester (osoba albo automated)

## Wyniki

| Test ID | Test | Kategoria | Status | Wartość zmierzona | Wartość oczekiwana | Delta |
|---------|------|-----------|--------|-------------------|-------------------|-------|
| BT-PWR-01 | ... | real_hardware | PASS/FAIL/PENDING | ... | ... | ... |
...

## Podsumowanie
- PASS: N
- FAIL: N
- PENDING: N
- SKIP: N
- NOT_APPLICABLE: N

## Werdykt
- [ ] Runtime bundle może być promowany (wszystkie real_hardware = PASS albo NOT_APPLICABLE)
- [ ] Runtime bundle nie może być promowany (istnieje FAIL albo PENDING na real_hardware)
```

---

## 8. Brak realnej plytki

Jeśli fizyczna plytka ESP32 nie jest dostępna:

- Wszystkie testy `real_hardware` otrzymują status `PENDING`
- `bench_test_report.md` zawiera jawną notatkę: `REAL_HARDWARE_REQUIRED — bench test nie został wykonany na fizycznej plytce`
- Runtime bundle **nie może być mergowany**
- Dozwolone jest wygenerowanie runtime bundle w trybie `draft` z pełnym pre-check symulowanym
- Kiedy plytka stanie się dostępna, bench test musi zostać powtórzony od sekcji 1

To nie jest blokada prac — to blokada promocji do runtime. Prace projektowe, dokumentacyjne i symulacyjne mogą trwać dalej.
