# Measurement Ledger: pack-project13-esp-runtime-01

- pack_id: pack-project13-esp-runtime-01
- board_id: recovered-esp-devkitc-v4-01
- board_variant: ESP32-WROOM-32D
- flash_method: USB-CDC (onboard CP2102)
- created_at: 2026-04-29
- tester: [DO_UZUPELNIENIA — osoba albo automated]
- test_date: [DO_UZUPELNIENIA]
- run_stamp: [DO_UZUPELNIENIA]

---

## Legenda

| Kolumna | Znaczenie |
|---------|-----------|
| Test ID | Identyfikator testu z BENCH_TEST_CONTRACT |
| Odczyt | Zmierzona wartosc z fizycznej plytki (nie symulacja) |
| Oczekiwane | Wartosc z board profile albo z kontraktu |
| Delta | Odczyt - Oczekiwane |
| Verdict | PASS / FAIL / PENDING / SKIP / NOT_APPLICABLE |
| Obserwacje | Wolny tekst — anomalie, uwagi, warunki pomiaru |

---

## Sekcja BT-PWR: Zasilanie

### BT-PWR-01: Pomiar napiecia wejsciowego

| Pole | Wartosc |
|------|---------|
| Odczyt | [DO_UZUPELNIENIA] V |
| Oczekiwane | 5V (z board profile: input_voltage = 5V USB albo 5V VIN) |
| Tolerancja | Delta <= 0.2V |
| Delta | [DO_UZUPELNIENIA] V |
| Verdict | [DO_UZUPELNIENIA] |
| Obserwacje | [DO_UZUPELNIENIA] |

### BT-PWR-02: Pomiar napiecia roboczego MCU

| Pole | Wartosc |
|------|---------|
| Odczyt | [DO_UZUPELNIENIA] V |
| Oczekiwane | 3.3V (z board profile: operating_voltage = 3.3V) |
| Tolerancja | Delta <= 0.1V od 3.3V |
| Delta | [DO_UZUPELNIENIA] V |
| Verdict | [DO_UZUPELNIENIA] |
| Obserwacje | [DO_UZUPELNIENIA] |

### BT-PWR-03: Pomiar pradu idle

| Pole | Wartosc |
|------|---------|
| Odczyt | [DO_UZUPELNIENIA] mA |
| Oczekiwane | power_consumption_idle = unknown (BRAKUJACE w board profile) |
| Tolerancja | Pomiar zrealizowany; brak wartosci = BRAKUJACE -> test pending |
| Delta | Nie dotyczy (brak wartosci referencyjnej) |
| Verdict | [DO_UZUPELNIENIA] — pomiar zrealizowany = PASS na artefakt; BRAKUJACE w board profile = test pending domkniecia |
| Obserwacje | [DO_UZUPELNIENIA] — wpisac zmierzona wartosc, ktora uzupelni board profile |

### BT-PWR-04: Pomiar pradu Wi-Fi TX

| Pole | Wartosc |
|------|---------|
| Odczyt | [DO_UZUPELNIENIA] mA |
| Oczekiwane | power_consumption_wifi_tx = unknown (BRAKUJACE w board profile) |
| Tolerancja | Pomiar zrealizowany; brak wartosci = BRAKUJACE -> test pending |
| Delta | Nie dotyczy (brak wartosci referencyjnej) |
| Verdict | [DO_UZUPELNIENIA] — pomiar zrealizowany = PASS na artefakt; BRAKUJACE w board profile = test pending domkniecia |
| Obserwacje | [DO_UZUPELNIENIA] — wpisac zmierzona wartosc, ktora uzupelni board profile |

### BT-PWR-05: Stabilnosc zasilania pod obciazeniem

| Pole | Wartosc |
|------|---------|
| Czas obserwacji | [DO_UZUPELNIENIA] s (wymagane >= 60s) |
| Brownout reset wystapil | [DO_UZUPELNIENIA] — TAK/NIE |
| Odczyt | [DO_UZUPELNIENIA] — opis zachowania plytki |
| Oczekiwane | Brak brownout reset w ciagu 60s |
| Verdict | [DO_UZUPELNIENIA] |
| Obserwacje | [DO_UZUPELNIENIA] — warunki obciazenia (ile GPIO, czy Wi-Fi aktywne) |

---

## Sekcja BT-FLS: Flashowanie

### BT-FLS-01: Flash firmware przez USB-CDC

| Pole | Wartosc |
|------|---------|
| Komenda | `esptool.py --chip esp32 --port /dev/ttyUSB0 --baud 460800 write_flash -z 0x1000 firmware.bin` |
| Wynik flash | [DO_UZUPELNIENIA] — sukces/porazka |
| Wynik verify | `esptool.py verify_flash 0x1000 firmware.bin` -> [DO_UZUPELNIENIA] |
| Verdict | [DO_UZUPELNIENIA] |
| Obserwacje | [DO_UZUPELNIENIA] — port, baud, bledy |

### BT-FLS-02: Wejscie w download mode

| Pole | Wartosc |
|------|---------|
| Metoda | BOOT button + reset albo auto-reset circuit |
| Proba 1 | [DO_UZUPELNIENIA] — sukces/porazka |
| Proba 2 | [DO_UZUPELNIENIA] — sukces/porazka |
| Proba 3 | [DO_UZUPELNIENIA] — sukces/porazka |
| Powtarzalnosc | [DO_UZUPELNIENIA] — 3/3, 2/3, 1/3 |
| Verdict | [DO_UZUPELNIENIA] |
| Obserwacje | [DO_UZUPELNIENIA] |

### BT-FLS-03: Recovery po brick

| Pole | Wartosc |
|------|---------|
| Metoda bricku | [DO_UZUPELNIENIA] — np. zly flash, uszkodzony bootloader |
| Plytka zbrickowana | [DO_UZUPELNIENIA] — TAK/NIE |
| Metoda recovery | Reflash via USB-CDC |
| Wynik recovery | [DO_UZUPELNIENIA] — sukces/porazka |
| Verdict | [DO_UZUPELNIENIA] |
| Obserwacje | [DO_UZUPELNIENIA] — uwagi o auto-reset circuit |

### BT-FLS-04: Backup oryginalnego firmware

| Pole | Wartosc |
|------|---------|
| Plik backup | artifacts/recovered-esp-devkitc-v4-01/backup_firmware.bin |
| Istnieje na dysku | [DO_UZUPELNIENIA] — TAK/NIE |
| Rozmiar pliku | [DO_UZUPELNIENIA] |
| Verdict | [DO_UZUPELNIENIA] |
| Obserwacje | [DO_UZUPELNIENIA] |

---

## Sekcja BT-GPIO: GPIO i peryferia

### BT-GPIO-01: Piny free odpowiadaja na toggle

| GPIO | Stan HIGH (odczyt) | Stan LOW (odczyt) | Verdict | Obserwacje |
|------|--------------------|--------------------|---------|------------|
| 2 | [DO_UZUPELNIENIA] | [DO_UZUPELNIENIA] | [DO_UZUPELNIENIA] | [DO_UZUPELNIENIA] |
| 4 | [DO_UZUPELNIENIA] | [DO_UZUPELNIENIA] | [DO_UZUPELNIENIA] | [DO_UZUPELNIENIA] |
| 5 | [DO_UZUPELNIENIA] | [DO_UZUPELNIENIA] | [DO_UZUPELNIENIA] | [DO_UZUPELNIENIA] |
| 12 | [DO_UZUPELNIENIA] | [DO_UZUPELNIENIA] | [DO_UZUPELNIENIA] | [DO_UZUPELNIENIA] |
| 13 | [DO_UZUPELNIENIA] | [DO_UZUPELNIENIA] | [DO_UZUPELNIENIA] | [DO_UZUPELNIENIA] |
| 14 | [DO_UZUPELNIENIA] | [DO_UZUPELNIENIA] | [DO_UZUPELNIENIA] | [DO_UZUPELNIENIA] |
| 15 | [DO_UZUPELNIENIA] | [DO_UZUPELNIENIA] | [DO_UZUPELNIENIA] | [DO_UZUPELNIENIA] |
| 16 | [DO_UZUPELNIENIA] | [DO_UZUPELNIENIA] | [DO_UZUPELNIENIA] | [DO_UZUPELNIENIA] |
| 17 | [DO_UZUPELNIENIA] | [DO_UZUPELNIENIA] | [DO_UZUPELNIENIA] | [DO_UZUPELNIENIA] |
| 18 | [DO_UZUPELNIENIA] | [DO_UZUPELNIENIA] | [DO_UZUPELNIENIA] | [DO_UZUPELNIENIA] |
| 19 | [DO_UZUPELNIENIA] | [DO_UZUPELNIENIA] | [DO_UZUPELNIENIA] | [DO_UZUPELNIENIA] |
| 21 | [DO_UZUPELNIENIA] | [DO_UZUPELNIENIA] | [DO_UZUPELNIENIA] | [DO_UZUPELNIENIA] |
| 22 | [DO_UZUPELNIENIA] | [DO_UZUPELNIENIA] | [DO_UZUPELNIENIA] | [DO_UZUPELNIENIA] |
| 23 | [DO_UZUPELNIENIA] | [DO_UZUPELNIENIA] | [DO_UZUPELNIENIA] | [DO_UZUPELNIENIA] |
| 25 | [DO_UZUPELNIENIA] | [DO_UZUPELNIENIA] | [DO_UZUPELNIENIA] | [DO_UZUPELNIENIA] |
| 26 | [DO_UZUPELNIENIA] | [DO_UZUPELNIENIA] | [DO_UZUPELNIENIA] | [DO_UZUPELNIENIA] |
| 27 | [DO_UZUPELNIENIA] | [DO_UZUPELNIENIA] | [DO_UZUPELNIENIA] | [DO_UZUPELNIENIA] |
| 32 | [DO_UZUPELNIENIA] | [DO_UZUPELNIENIA] | [DO_UZUPELNIENIA] | [DO_UZUPELNIENIA] |
| 33 | [DO_UZUPELNIENIA] | [DO_UZUPELNIENIA] | [DO_UZUPELNIENIA] | [DO_UZUPELNIENIA] |

**Podsumowanie toggle**: [DO_UZUPELNIENIA] — N pass, M fail z 19 free GPIO

### BT-GPIO-02: Piny damaged wykluczone z pin map

| Pole | Wartosc |
|------|---------|
| damaged_pins z board profile | brak uszkodzonych |
| Pin map uzywa damaged pins | [DO_UZUPELNIENIA] — TAK/NIE |
| Verdict | [DO_UZUPELNIENIA] |
| Obserwacje | [DO_UZUPELNIENIA] |

### BT-GPIO-03: ADC1 odczyt z napiecia referencyjnego

| ADC kanal | GPIO | Napiecie ref. | Odczyt ADC | Oczekiwane (+/-10%) | Delta | Verdict |
|-----------|------|---------------|------------|---------------------|-------|---------|
| ADC1_CH4 | 32 | [DO_UZUPELNIENIA] V | [DO_UZUPELNIENIA] | [DO_UZUPELNIENIA] | [DO_UZUPELNIENIA] | [DO_UZUPELNIENIA] |
| ADC1_CH5 | 33 | [DO_UZUPELNIENIA] V | [DO_UZUPELNIENIA] | [DO_UZUPELNIENIA] | [DO_UZUPELNIENIA] | [DO_UZUPELNIENIA] |
| ADC1_CH6 | 34 | [DO_UZUPELNIENIA] V | [DO_UZUPELNIENIA] | [DO_UZUPELNIENIA] | [DO_UZUPELNIENIA] | [DO_UZUPELNIENIA] |
| ADC1_CH7 | 35 | [DO_UZUPELNIENIA] V | [DO_UZUPELNIENIA] | [DO_UZUPELNIENIA] | [DO_UZUPELNIENIA] | [DO_UZUPELNIENIA] |

Obserwacje: [DO_UZUPELNIENIA]

### BT-GPIO-04: I2C scan

| Pole | Wartosc |
|------|---------|
| SDA | GPIO21 |
| SCL | GPIO22 |
| Adresy wykryte | [DO_UZUPELNIENIA] — np. 0x3C, 0x68, albo "no I2C device on this board" |
| Verdict | [DO_UZUPELNIENIA] |
| Obserwacje | [DO_UZUPELNIENIA] |

### BT-GPIO-05: UART0 komunikacja serial

| Pole | Wartosc |
|------|---------|
| TX | GPIO1 |
| RX | GPIO3 |
| Baud | [DO_UZUPELNIENIA] — domyslnie 115200 |
| Znak wyslany | [DO_UZUPELNIENIA] |
| Znak odebrany | [DO_UZUPELNIENIA] |
| Verdict | [DO_UZUPELNIENIA] |
| Obserwacje | [DO_UZUPELNIENIA] |

---

## Sekcja BT-NET: Siec i komunikacja

### BT-NET-01: Wi-Fi scan

| Pole | Wartosc |
|------|---------|
| Liczba sieci wykrytych | [DO_UZUPELNIENIA] |
| Czestotliwosc | 2.4GHz |
| Verdict | [DO_UZUPELNIENIA] — wymagane >= 1 siec |
| Obserwacje | [DO_UZUPELNIENIA] |

### BT-NET-02: Wi-Fi connect do testowego AP

| Pole | Wartosc |
|------|---------|
| SSID | [DO_UZUPELNIENIA — nie wpisywac hasla] |
| Czas polaczenia | [DO_UZUPELNIENIA] s (wymagane <= 10s) |
| Verdict | [DO_UZUPELNIENIA] |
| Obserwacje | [DO_UZUPELNIENIA] |

### BT-NET-03: MQTT publish

| Pole | Wartosc |
|------|---------|
| Broker | [DO_UZUPELNIENIA — adres, nie credentials] |
| Topic | [DO_UZUPELNIENIA] |
| Message delivered | [DO_UZUPELNIENIA] — TAK/NIE |
| Broker potwierdza | [DO_UZUPELNIENIA] — TAK/NIE |
| Verdict | [DO_UZUPELNIENIA] |
| Obserwacje | [DO_UZUPELNIENIA] |

### BT-NET-04: Antena — RSSI

| Pole | Wartosc |
|------|---------|
| RSSI | [DO_UZUPELNIENIA] dBm |
| Odleglosc od AP | 3m |
| Wymagane | RSSI >= -80dBm |
| Verdict | [DO_UZUPELNIENIA] |
| Obserwacje | [DO_UZUPELNIENIA] — srodowisko, przeszkody |

---

## Sekcja BT-STO: Storage

### BT-STO-01: Rozmiar flash

| Pole | Wartosc |
|------|---------|
| `esptool.py flash_id` output | [DO_UZUPELNIENIA] |
| Rozmiar odczytany | [DO_UZUPELNIENIA] MB |
| Rozmiar z board profile | 4MB |
| Zgodnosc | [DO_UZUPELNIENIA] — wymagane +/-0 |
| Verdict | [DO_UZUPELNIENIA] |
| Obserwacje | [DO_UZUPELNIENIA] |

### BT-STO-02: Odczyt tabeli partycji

| Pole | Wartosc |
|------|---------|
| `esptool.py partition_table` output | [DO_UZUPELNIENIA] |
| Partycje czytelne | [DO_UZUPELNIENIA] — TAK/NIE |
| Spojne z partition_table z board profile | [DO_UZUPELNIENIA] — TAK/NIE |
| Verdict | [DO_UZUPELNIENIA] |
| Obserwacje | [DO_UZUPELNIENIA] |

---

## Podsumowanie ledgera

| Status | Liczba |
|--------|--------|
| PASS | 0 |
| FAIL | 0 |
| PENDING | 20 |
| SKIP | 0 |
| NOT_APPLICABLE | 0 |

> **UWAGA**: To jest pusty measurement ledger. Wszystkie odczyty i verdicty sa [DO_UZUPELNIENIA].
> Zadna wartosc nie zostala wpisana bez fizycznej plytki.
> Po wypelnieniu ledger staje sie autorytatywnym zrodlem prawd dla bench_test_report.md.

### Status zadanie 46 (2026-04-30)

Agent podwykonawczy zadania 46 potwierdzil: **brak fizycznej plytki ESP32** na stanowisku roboczym. Wszystkie 20 testow real_hardware pozostaja PENDING. Zadna wartosc symulowana nie zostala wpisana jako realny pomiar. Bench test nie zostal wykonany. Blocker receipt: `esp_runtime_bench_receipt_2026-04-30.json`.

Gdy operator z fizyczna plytka bedzie dostepny, powinien:
1. Przejsc `OPERATOR_PRE_START_CHECKLIST.md`
2. Wykonac bench test wg `REAL_HARDWARE_BENCH_PACKET.md`
3. Wpisac odczyty ponizej (zastapic [DO_UZUPELNIENIA] realnymi wartosciami)
4. Uzupelnic `bench_test_report.md` wynikami
5. Zaktualizowac `readiness_gate.json`
