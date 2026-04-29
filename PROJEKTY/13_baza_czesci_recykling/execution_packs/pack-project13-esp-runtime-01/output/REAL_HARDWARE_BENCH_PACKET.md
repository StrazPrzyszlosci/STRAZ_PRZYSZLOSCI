# Real Hardware Bench Packet: pack-project13-esp-runtime-01

- pack_id: pack-project13-esp-runtime-01
- board_id: recovered-esp-devkitc-v4-01
- board_variant: ESP32-WROOM-32D
- generated_at: 2026-04-29
- predecessor: zadanie 34 (simulated_precheck_pass, conditional)

---

## 1. Cel packetu

Ten packet przygotowuje operatora z realna plytka ESP32 do wykonania bench testu od pierwszego wlaczenia do verdictu. Nie zawiera zadnych zmyslonych pomiarow ani wartosci PASS — kazdy odczyt musi pochodzic z fizycznej plytki.

Symulacja z zadania 34 potwierdzila spojnosc konfiguracji (38 pass, 3 warn, 0 fail). Teraz przechodzimy z symulacji do real_hardware zgodnie z `SIMULATION_VS_REAL_HARDWARE_POLICY_ESP_RUNTIME_01.md`.

---

## 2. Wymagania wstepne

### 2.1 Sprzet

- Plytka ESP32-DevKitC-V4 z board_id = `recovered-esp-devkitc-v4-01`
- Kabel USB (Micro-USB dla DevKitC-V4)
- Multimetr cyfrowy (pomiar napiecia DC i pradu)
- Komputer z `esptool.py` zainstalowanym (`pip install esptool`)
- Opcjonalnie: logicanalyzer albo oscyloskop (do weryfikacji GPIO toggle)

### 2.2 Oprogramowanie

- `esptool.py` >= 4.x
- Serial terminal (minicom, screen, picocom)
- Firmware `.bin` do flashowania
- Testowe AP Wi-Fi (SSID i haslo do uzupelnienia w `.env` — nie w diffie)
- Testowy MQTT broker (adres do uzupelnienia w `.env` — nie w diffie)

### 2.3 Dokumenty referencyjne

- `docs/BENCH_TEST_CONTRACT_ESP_RUNTIME_01.md` — twardy kontrakt testow
- `docs/SIMULATION_VS_REAL_HARDWARE_POLICY_ESP_RUNTIME_01.md` — polityka rozdzielenia
- `output/simulated_precheck_report.md` — wynik symulacji (kontekst, nie zastepstwo)
- `output/flash_and_recovery_runbook.md` — runbook flashowania
- `output/bench_test_report_TEMPLATE.md` — template do wypelnienia po tescie

---

## 3. Kolejnosc testow

Zgodnie z `BENCH_TEST_CONTRACT_ESP_RUNTIME_01.md` sekcja 3:

```
BT-PWR -> BT-FLS -> BT-GPIO -> BT-NET -> BT-STO
```

Kolejnosc jest obowiazkowa. Bez stabilnego zasilania dalsze testy sa niewiarygodne. Bez udanego flash nie da sie testowac runtime.

### 3.1 Sekcja BT-PWR: Zasilanie (5 testow)

| Test ID | Test | Kategoria | Wymagany wynik | Sprzet potrzebny |
|---------|------|-----------|---------------|-----------------|
| BT-PWR-01 | Pomiar napiecia wejsciowego vs input_voltage (5V) | real_hardware | Delta <= 0.2V | Multimetr na pinie 5V/VIN |
| BT-PWR-02 | Pomiar napiecia roboczego MCU vs operating_voltage (3.3V) | real_hardware | Delta <= 0.1V od 3.3V | Multimetr na pinie 3.3V |
| BT-PWR-03 | Pomiar pradu idle vs power_consumption_idle | real_hardware | Pomiar zrealizowany; brak wartosci = BRAKUJACE -> test pending | Multimetr w trybie mA szeregowo |
| BT-PWR-04 | Pomiar pradu Wi-Fi TX vs power_consumption_wifi_tx | real_hardware | Pomiar zrealizowany; brak wartosci = BRAKUJACE -> test pending | Multimetr w trybie mA szeregowo + Wi-Fi active |
| BT-PWR-05 | Stabilnosc zasilania pod obciazeniem (GPIO + Wi-Fi) | real_hardware | Brak brownout reset w ciagu 60s | Obserwacja serial console |

### 3.2 Sekcja BT-FLS: Flashowanie (4 testy)

| Test ID | Test | Kategoria | Wymagany wynik | Sprzet potrzebny |
|---------|------|-----------|---------------|-----------------|
| BT-FLS-01 | Flash firmware przez USB-CDC (onboard CP2102) | real_hardware | Sukces — esptool verify | Kabel USB, esptool.py |
| BT-FLS-02 | Wejscie w download mode przez BOOT button + reset | real_hardware | Plytka wchodzi w download mode powtarzalnie | Kabel USB, obserwacja serial |
| BT-FLS-03 | Recovery po brick — reflashing przez USB-CDC | real_hardware | Plytka odzyskana po celowym bricku | esptool.py, firmware.bin |
| BT-FLS-04 | Backup oryginalnego firmware istnieje lub NIE DOTYCZY | either | Plik .bin na dysku albo jawny NIE DOTYCZY | Sprawdzenie dysku |

### 3.3 Sekcja BT-GPIO: GPIO i peryferia (5 testow)

| Test ID | Test | Kategoria | Wymagany wynik | Sprzet potrzebny |
|---------|------|-----------|---------------|-----------------|
| BT-GPIO-01 | Piny free odpowiadaja na toggle | real_hardware | Odczyt zwrotny HIGH/LOW | Multimetr / LED na pinie |
| BT-GPIO-02 | Piny damaged wykluczone z pin map | either | Pin map nie przypisuje funkcji do damaged pins | Sprawdzenie pin_map.md |
| BT-GPIO-03 | ADC1 odczyt z napiecia referencyjnego | real_hardware | Odczyt +/-10% wartosci oczekiwanej | Zrodlo napiecia referencyjnego |
| BT-GPIO-04 | I2C scan — wykrycie slave na magistrali | real_hardware | Adres slave wykryty albo jawne "no I2C device" | I2C slave device (opcjonalnie) |
| BT-GPIO-05 | UART0 komunikacja serial | real_hardware | Echo test — znak wyslany, znak odebrany | Kabel USB (UART0 = USB-Serial) |

### 3.4 Sekcja BT-NET: Siec i komunikacja (4 testy)

| Test ID | Test | Kategoria | Wymagany wynik | Sprzet potrzebny |
|---------|------|-----------|---------------|-----------------|
| BT-NET-01 | Wi-Fi scan — plytka widzi sieci 2.4GHz | real_hardware | Przynajmniej 1 siec wykryta | Testowe AP 2.4GHz |
| BT-NET-02 | Wi-Fi connect do testowego AP | real_hardware | Polaczenie nawiazane w <= 10s | Testowe AP + credentials |
| BT-NET-03 | MQTT publish do testowego broker | real_hardware | Message delivered, broker potwierdza | MQTT broker |
| BT-NET-04 | Antena — jakosc sygnalu (RSSI) | real_hardware | RSSI >= -80dBm w 3m od AP | Testowe AP, pomiar RSSI |

### 3.5 Sekcja BT-STO: Storage (2 testy)

| Test ID | Test | Kategoria | Wymagany wynik | Sprzet potrzebny |
|---------|------|-----------|---------------|-----------------|
| BT-STO-01 | Rozmiar flash vs flash_size (4MB) z board profile | real_hardware | Zgodnosc +/-0 (dokladny rozmiar) | esptool.py flash_id |
| BT-STO-02 | Odczyt tabeli partycji | real_hardware | Partycje czytelne, spojne z partition_table | esptool.py partition_table |

---

## 4. Sciezka testowa — krok po kroku

### Krok 0: Przedstartowy (operator checklist)

Patrz: `output/OPERATOR_PRE_START_CHECKLIST.md`

### Krok 1: Zasilanie (BT-PWR-01..05)

1. Podlaczyc plytke przez USB (bez firmware, factory default)
2. Zmierzyc napiecie wejsciowe na pinie 5V/VIN -> BT-PWR-01
3. Zmierzyc napiecie robocze na pinie 3.3V -> BT-PWR-02
4. Zmierzyc prad idle -> BT-PWR-03
5. Aktywowac Wi-Fi TX na plytce, zmierzyc prad -> BT-PWR-04
6. Obciazyc GPIO + Wi-Fi jednoczesnie, obserwowac 60s -> BT-PWR-05
7. **Wpisac odczyty do measurement ledger** -> `output/MEASUREMENT_LEDGER.md`

### Krok 2: Flashowanie (BT-FLS-01..04)

1. Wejsc w download mode: przytrzymac BOOT, nacisnac RESET, puscic BOOT -> BT-FLS-02
2. Sflashowac firmware przez esptool -> BT-FLS-01
3. Zweryfikowac: `esptool.py verify_flash 0x1000 firmware.bin`
4. Sprawdzic backup firmware na dysku -> BT-FLS-04
5. Celowo zbrickowac plytke (zly flash), potem odzyskac przez reflash -> BT-FLS-03
6. **Wpisac odczyty do measurement ledger**

### Krok 3: GPIO i peryferia (BT-GPIO-01..05)

1. Sprawdzic pin_map.md pod katem damaged pins -> BT-GPIO-02
2. Toggle kazdego free pinu HIGH/LOW, odczyt zwrotny -> BT-GPIO-01
3. Podlaczac napiecie referencyjne do ADC1 (GPIO32/33/34/35/36/39), odczytac -> BT-GPIO-03
4. Wykonac I2C scan na SDA=21, SCL=22 -> BT-GPIO-04
5. Echo test przez UART0 (USB-Serial) -> BT-GPIO-05
6. **Wpisac odczyty do measurement ledger**

### Krok 4: Siec (BT-NET-01..04)

1. Wi-Fi scan z plytki -> BT-NET-01
2. Wi-Fi connect do testowego AP -> BT-NET-02
3. MQTT publish testowej wiadomosci -> BT-NET-03
4. Zmierzyc RSSI w 3m od AP -> BT-NET-04
5. **Wpisac odczyty do measurement ledger**

### Krok 5: Storage (BT-STO-01..02)

1. `esptool.py flash_id` -> porownac z flash_size=4MB -> BT-STO-01
2. `esptool.py partition_table` -> porownac z partition_table -> BT-STO-02
3. **Wpisac odczyty do measurement ledger**

### Krok 6: Werdykt

1. Przepisac wyniki z measurement ledger do bench_test_report.md
2. Policzyc PASS/FAIL/PENDING/SKIP/NOT_APPLICABLE
3. Oznaczyc werdykt zgodnie z BENCH_TEST_CONTRACT sekcja 4

---

## 5. Ograniczenia i polityka

- Ten packet **nie wpisuje zadnych pomiarow** — odczyty pochodza wylacznie z realnej plytki
- Symulacja z zadania 34 jest kontekstem, nie zastepstwem
- Zgodnie z `SIMULATION_VS_REAL_HARDWARE_POLICY_ESP_RUNTIME_01.md` sekcja 6: jesli symulacja i real_hardware daja sprzeczne wyniki, real_hardware jest autorytatywne
- Zgodnie z polityka: zadne testy `real_hardware` nie moga byc zamkniete wynikiem `simulated`
- Sekrety (Wi-Fi SSID, haslo, MQTT credentials) **nie moga trafic do diffu ani firmware**
