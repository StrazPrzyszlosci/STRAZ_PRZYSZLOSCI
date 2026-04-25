# Sample ESP32 Board Profile: Recovered DevKitC-V4

Ten plik jest przykladowym wypelnieniem `ESP32_RECOVERED_BOARD_PROFILE_TEMPLATE.md` dla odzyskanej plytki ESP32-DevKitC-V4. Sluzy jako wzorzec i test wejsciowy dla packa `pack-project13-esp-runtime-01`.

---

## 1. Identyfikacja plytki

| Pole | Wartosc | Wymagalnosc |
|------|---------|-------------|
| board_id | recovered-esp-devkitc-v4-01 | POMIERZONE |
| board_variant | ESP32-WROOM-32D | POMIERZONE |
| chip_revision | v3 | DOMNIEMANE |
| module_manufacturer | Espressif | DOMNIEMANE |
| carrier_board | ESP32-DevKitC-V4 | POMIERZONE |
| donor_device | IoT smart hub (recycled) | POMIERZONE |
| recovery_date | 2026-04-20 | POMIERZONE |
| recovery_method | whole board reused | POMIERZONE |

---

## 2. Zasilanie

| Pole | Wartosc | Wymagalnosc |
|------|---------|-------------|
| input_voltage | 5V USB albo 5V VIN | POMIERZONE |
| operating_voltage | 3.3V | POMIERZONE |
| regulator_type | AMS1117-3.3 | DOMNIEMANE |
| max_input_voltage | 12V (VIN pin) | DOMNIEMANE |
| power_consumption_idle | unknown | BRAKUJACE |
| power_consumption_wifi_tx | unknown | BRAKUJACE |
| power_consumption_deep_sleep | unknown | BRAKUJACE |
| usb_connector | Micro-USB | POMIERZONE |

---

## 3. GPIO i peryferia

### 3.1 Dostepne piny GPIO

| GPIO | Funkcja alternatywna | Stan na plytce | Zuzycie w runtime |
|------|---------------------|---------------|-------------------|
| 0 | BOOT button | used_onboard | DO_UZUPELNIENIA |
| 1 | UART0 TX | used_onboard | DO_UZUPELNIENIA |
| 2 | — | free | DO_UZUPELNIENIA |
| 3 | UART0 RX | used_onboard | DO_UZUPELNIENIA |
| 4 | — | free | DO_UZUPELNIENIA |
| 5 | — | free | DO_UZUPELNIENIA |
| 12 | JTAG MTDI | free (z uwaga na boot voltage) | DO_UZUPELNIENIA |
| 13 | JTAG MTCK | free | DO_UZUPELNIENIA |
| 14 | JTAG MTMS | free | DO_UZUPELNIENIA |
| 15 | JTAG MTDO | free | DO_UZUPELNIENIA |
| 16 | UART2 RX (PSRAM na WROVER) | free (na WROOM) | DO_UZUPELNIENIA |
| 17 | UART2 TX (PSRAM na WROVER) | free (na WROOM) | DO_UZUPELNIENIA |
| 18 | SPI SCLK | free | DO_UZUPELNIENIA |
| 19 | SPI MISO | free | DO_UZUPELNIENIA |
| 21 | I2C SDA (default) | free | DO_UZUPELNIENIA |
| 22 | I2C SCL (default) | free | DO_UZUPELNIENIA |
| 23 | SPI MOSI | free | DO_UZUPELNIENIA |
| 25 | — | free | DO_UZUPELNIENIA |
| 26 | DAC2 | free | DO_UZUPELNIENIA |
| 27 | — | free | DO_UZUPELNIENIA |
| 32 | ADC1_CH4, Touch9 | free | DO_UZUPELNIENIA |
| 33 | ADC1_CH5, Touch8 | free | DO_UZUPELNIENIA |
| 34 | ADC1_CH6 (input only) | free | DO_UZUPELNIENIA |
| 35 | ADC1_CH7 (input only) | free | DO_UZUPELNIENIA |
| 36 | ADC1_CH0 (input only, VP) | free | DO_UZUPELNIENIA |
| 39 | ADC1_CH3 (input only, VN) | free | DO_UZUPELNIENIA |

### 3.2 Peryferia wbudowane

| Peryferium | Dostepne? | Piny | Uwagi |
|-----------|----------|------|-------|
| ADC1 | TAK | 32, 33, 34, 35, 36, 39 | DOMNIEMANE — 6 kanalow 12-bit |
| ADC2 | TAK teoretycznie | 4, 0, 2, 15, 13, 12, 14, 27, 25, 26 | DOMNIEMANE — niedostepny przy wlaczonym Wi-Fi |
| I2C | TAK | SDA=21, SCL=22 (default) | DOMNIEMANE |
| SPI | TAK | MOSI=23, MISO=19, SCLK=18 | DOMNIEMANE |
| UART0 | TAK | TX=1, RX=3 | DOMNIEMANE — uzyty do USB-Serial |
| UART1 | TAK | dowolne GPIO | DOMNIEMANE |
| UART2 | TAK | RX=16, TX=17 (default) | DOMNIEMANE |
| PWM | TAK | dowolne GPIO | DOMNIEMANE |
| Capacitive Touch | TAK | 0, 2, 4, 12, 13, 14, 15, 27, 32, 33 | DOMNIEMANE |
| DAC | TAK | DAC1=25, DAC2=26 | DOMNIEMANE — tylko ESP32 classic, nie S2/S3/C3 |

---

## 4. Siec i komunikacja

| Pole | Wartosc | Wymagalnosc |
|------|---------|-------------|
| wifi_2_4ghz | TAK | DOMNIEMANE |
| wifi_standard | 802.11 b/g/n | DOMNIEMANE |
| bluetooth_classic | TAK | DOMNIEMANE |
| bluetooth_le | TAK | DOMNIEMANE |
| ethernet | NIE | POMIERZONE |
| antenna_type | PCB trace | POMIERZONE |
| antenna_condition | good | POMIERZONE |

---

## 5. Storage

| Pole | Wartosc | Wymagalnosc |
|------|---------|-------------|
| flash_size | 4MB | POMIERZONE |
| flash_type | SPI DIO | DOMNIEMANE |
| partition_table | default | DOMNIEMANE |
| psram | NIE | POMIERZONE |
| sd_card_slot | NIE | POMIERZONE |
| eeprom_present | unknown | BRAKUJACE |

---

## 6. Recovery path

### 6.1 Flashowanie

| Pole | Wartosc | Wymagalnosc |
|------|---------|-------------|
| flash_method | USB-CDC (onboard CP2102) | POMIERZONE |
| boot_mode_entry | BOOT button + reset albo auto-reset circuit | POMIERZONE |
| auto_reset_circuit | TAK | DOMNIEMANE |
| esptool_baud_rate | 460800 | DOMNIEMANE |

### 6.2 Odzyskiwanie po awarii

| Pole | Wartosc | Wymagalnosc |
|------|---------|-------------|
| recovery_after_brick | reflash via USB-CDC | POMIERZONE |
| backup_firmware_available | TAK | POMIERZONE |
| backup_firmware_location | artifacts/recovered-esp-devkitc-v4-01/backup_firmware.bin | POMIERZONE |

---

## 7. Known limitations

| Ograniczenie | Wartosc | Wymagalnosc |
|-------------|---------|-------------|
| damaged_pins | brak uszkodzonych | POMIERZONE |
| known_bugs | ADC2 unusable with Wi-Fi on; strapping pin GPIO12 affects boot voltage selection | DOMNIEMANE |
| thermal_constraints | brak radiatora — recomendowany max 60C obudowy przy ciaglym Wi-Fi | DOMNIEMANE |
| mechanical_constraints | brak uszkodzen; 2 otwory montazowe | POMIERZONE |
| firmware_constraints | unknown | BRAKUJACE |
| safety_notes | brak optoopcji na GPIO — nie podlaczac napiecia powyzej 3.3V bezpośrednio; GPIO34-39 tylko input | POMIERZONE |

---

## 8. Governance

- Profile jest wejsciem do packa `esp-runtime-01` — nie jest potwierdzeniem, ze plytka dziala.
- Wymaga `ReadinessGate(review_ready)` przed wejsciem do packa.
- Poniewaz dotyczy hardware runtime, wymaga `IntegrityRiskAssessment` i `ReadinessGate(integrity_ready)` przed flashowaniem.
- Pola `[BRAKUJACE]` (power consumption, eeprom, firmware constraints) nalezy uzupelnic przez bench test przed uzyciem w runtime produkcyjnym.

---

## 9. Output packa esp-runtime-01

Oczekiwane artefakty po przetworzeniu tego profile:

| Artefakt | Spodziewana tresc |
|----------|-------------------|
| runtime_profile.json | Konfiguracja runtime dla ESP32-WROOM-32D z 4MB flash, bez PSRAM |
| pin_map.md | Mapowanie pinow dla konkretnego projektu na bazie dostepnych GPIO |
| lua_runtime_bundle/ | Skrypty wykonawcze dostosowane do dostepnych peryferiow |
| flash_and_recovery_runbook.md | Instrukcja flashowania przez USB-CDC i odzyskiwania po awarii |
| bench_test_report.md | Raport z testu: ADC linearity, Wi-Fi range, power consumption, GPIO integrity |
