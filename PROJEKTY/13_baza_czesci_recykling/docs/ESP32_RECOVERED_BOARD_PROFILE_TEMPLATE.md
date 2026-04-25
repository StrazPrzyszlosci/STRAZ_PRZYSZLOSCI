# ESP32 Recovered Board Profile Template

## Cel dokumentu

Ten template jest wejsciowym kontraktem danych dla packa `pack-project13-esp-runtime-01`. Opisuje capabilities odzyskanej plytki ESP32, zeby runtime nie targetowal abstrakcyjnego "ESP32", lecz konkretna plytke z jej realnymi ograniczeniami.

Kazdy wypelniony profile staje sie wejsciem do packa runtime i musi byc reviewowany przed flashowaniem.

---

## Legenda pol

- `[POMIERZONE]` — wartosc zmierzona na fizycznej plytce (np. multimetrem, odczytana z silkscreen).
- `[DOMNIEMANE]` — wartosc odczytana z datasheetu albo z nazwy modulu, ale nie potwierdzona pomiarem na tej konkretnej plytce.
- `[BRAKUJACE]` — wartosc nieznana, wymaga pomiaru albo testu przed uzyciem w runtime.
- `[DO_UZUPELNIENIA]` — wartosc domyslna do nadpisania przez maintainera.

Bez wypelnionych pol `[POMIERZONE]` i `[DOMNIEMANE]` w sekcjach krytycznych profil nie moze byc uznany za gotowy do flashowania.

---

## 1. Identyfikacja plytki

| Pole | Wymagalnosc | Opis |
|------|------------|------|
| `board_id` | [POMIERZONE] | Unikalny identyfikator plytki w katalogu, np. `recovered-esp-wroom-32-01` |
| `board_variant` | [POMIERZONE] | Wariant modulu ESP32, np. `ESP32-WROOM-32D`, `ESP32-WROOM-32E`, `ESP32-S3-WROOM-1` |
| `chip_revision` | [DOMNIEMANE] | Rewizja chipu, np. `v3`, `v4` — odczytana z esptool albo z silkscreen |
| `module_manufacturer` | [DOMNIEMANE] | Producent modulu, np. `Espressif`, `Ai-Thinker`, `Lolin` |
| `carrier_board` | [POMIERZONE] | Plytka bazowa, np. `ESP32-DevKitC-V4`, `NodeMCU-32S`, `custom recycled PCB` |
| `donor_device` | [POMIERZONE] | Urzadzenie-dawca, z ktorego plytka pochodzi, np. `smart plug Sonoff S26`, `recycled IoT hub` |
| `recovery_date` | [POMIERZONE] | Data odzyskania plytki |
| `recovery_method` | [POMIERZONE] | Jak plytka zostala pozyskana: `desoldered`, `whole board reused`, `purchased as salvage`, `donated` |

---

## 2. Zasilanie

| Pole | Wymagalnosc | Opis |
|------|------------|------|
| `input_voltage` | [POMIERZONE] | Napiecie wejsciowe, np. `5V USB`, `3.7V LiPo`, `12V DC` |
| `operating_voltage` | [POMIERZONE] | Napiecie robocze MCU, np. `3.3V` |
| `regulator_type` | [DOMNIEMANE] | Typ stabilizatora na plytce, np. `AMS1117-3.3`, `RT9013` |
| `max_input_voltage` | [DOMNIEMANE] | Maksymalne dopuszczalne napiecie wejsciowe |
| `power_consumption_idle` | [BRAKUJACE] | Pobor pradu w stanie idle |
| `power_consumption_wifi_tx` | [BRAKUJACE] | Pobor pradu przy transmisji Wi-Fi |
| `power_consumption_deep_sleep` | [BRAKUJACE] | Pobor pradu w deep sleep |
| `usb_connector` | [POMIERZONE] | Typ zlacza USB, np. `USB-C`, `Micro-USB`, `brak` |

---

## 3. GPIO i peryferia

### 3.1 Dostepne piny GPIO

| GPIO | Funkcja alternatywna | Stan na plytce | Zuzycie w runtime |
|------|---------------------|---------------|-------------------|
| __DO_UZUPELNIENIA__ | __DO_UZUPELNIENIA__ | `[POMIERZONE]` | `[DO_UZUPELNIENIA]` |

Kolumna "Stan na plytce" opisuje, czy pin jest dostepny (`free`), zajety przez onboard peryferium (`used_onboard`), uszkodzony (`damaged`) albo niepewny (`untested`).

### 3.2 Peryferia wbudowane

| Peryferium | Dostepne? | Piny | Uwagi |
|-----------|----------|------|-------|
| ADC1 | [DOMNIEMANE] | __DO_UZUPELNIENIA__ | 2 kanaly 12-bit na ESP32 |
| ADC2 | [DOMNIEMANE] | __DO_UZUPELNIENIA__ | Niedostepny przy wlaczonym Wi-Fi |
| I2C | [DOMNIEMANE] | __DO_UZUPELNIENIA__ | Default SDA=21, SCL=22 |
| SPI | [DOMNIEMANE] | __DO_UZUPELNIENIA__ | Default MOSI=23, MISO=19, SCLK=18 |
| UART0 | [DOMNIEMANE] | __DO_UZUPELNIENIA__ | Uzyty do USB-Serial |
| UART1 | [DOMNIEMANE] | __DO_UZUPELNIENIA__ | |
| UART2 | [DOMNIEMANE] | __DO_UZUPELNIENIA__ | |
| PWM | [DOMNIEMANE] | __DO_UZUPELNIENIA__ | |
| Capacitive Touch | [DOMNIEMANE] | __DO_UZUPELNIENIA__ | |
| DAC | [DOMNIEMANE] | __DO_UZUPELNIENIA__ | Tylko ESP32 (nie S2/S3/C3) |

---

## 4. Siec i komunikacja

| Pole | Wymagalnosc | Opis |
|------|------------|------|
| `wifi_2_4ghz` | [DOMNIEMANE] | `TAK` / `NIE` — czy Wi-Fi 2.4GHz jest dostepne |
| `wifi_standard` | [DOMNIEMANE] | `802.11 b/g/n` itp. |
| `bluetooth_classic` | [DOMNIEMANE] | `TAK` / `NIE` |
| `bluetooth_le` | [DOMNIEMANE] | `TAK` / `NIE` |
| `ethernet` | [POMIERZONE] | `TAK` / `NIE` — czy na plytce jest kontroler Ethernet |
| `antenna_type` | [POMIERZONE] | `PCB trace`, `IPEX connector`, `external` |
| `antenna_condition` | [POMIERZONE] | `good`, `damaged`, `missing`, `untested` |

---

## 5. Storage

| Pole | Wymagalnosc | Opis |
|------|------------|------|
| `flash_size` | [POMIERZONE] | Rozmiar flash, np. `4MB`, `8MB`, `16MB` — odczytany z esptool |
| `flash_type` | [DOMNIEMANE] | Typ flash, np. `SPI`, `QIO`, `DIO` |
| `partition_table` | [DOMNIEMANE] | Domyślna tabela partycji albo `custom` |
| `psram` | [POMIERZONE] | `TAK` / `NIE` + rozmiar, np. `4MB` |
| `sd_card_slot` | [POMIERZONE] | `TAK` / `NIE` — czy na plytce jest slot SD |
| `eeprom_present` | [BRAKUJACE] | Czy na plytce jest dodatkowy EEPROM |

---

## 6. Recovery path

### 6.1 Flashowanie

| Pole | Wymagalnosc | Opis |
|------|------------|------|
| `flash_method` | [POMIERZONE] | Sposob flashowania: `USB-CDC`, `UART via USB-TTL`, `JTAG`, `OTA` |
| `boot_mode_entry` | [POMIERZONE] | Jak wejsc w download mode: `BOOT button`, `GPIO0 pulldown`, `auto-reset circuit` |
| `auto_reset_circuit` | [DOMNIEMANE] | Czy plytka ma uklad auto-reset (DTR/RTS): `TAK` / `NIE` |
| `esptool_baud_rate` | [DOMNIEMANE] | Maksymalny baud rate dla stabilnego flash, np. `460800` |

### 6.2 Odzyskiwanie po awarii

| Pole | Wymagalnosc | Opis |
|------|------------|------|
| `recovery_after_brick` | [POMIERZONE] | Sciezka odzysku po bricku: `reflash via UART`, `JTAG required`, `no recovery possible` |
| `backup_firmware_available` | [POMIERZONE] | Czy zrobiono backup oryginalnego firmware: `TAK` / `NIE` / `NIE DOTYCZY` |
| `backup_firmware_location` | [POMIERZONE] | Gdzie jest backup, np. `artifacts/recovered-esp-wroom-32-01/backup_firmware.bin` albo `brak` |

---

## 7. Known limitations

| Ograniczenie | Wymagalnosc | Opis |
|-------------|------------|------|
| `damaged_pins` | [POMIERZONE] | Lista uszkodzonych albo niedostepnych pinow, np. `GPIO12, GPIO15` |
| `known_bugs` | [DOMNIEMANE] | Znane problemy tego wariantu ESP32, np. `ADC2 unusable with Wi-Fi`, `bug in rev1 silicon` |
| `thermal_constraints` | [DOMNIEMANE] | Ograniczenia termiczne, np. `brak radiатора — max 60C obudowy` |
| `mechanical_constraints` | [POMIERZONE] | Ograniczenia mechaniczne, np. `brak otworow montazowych`, `plytka uszkodzona na krawedzi` |
| `firmware_constraints` | [BRAKUJACE] | Ograniczenia firmware, np. `brak supportu dla BLE w tej rewizji` |
| `safety_notes` | [POMIERZONE] | Uwagi bezpieczenstwa, np. `brak optoopcji na GPIO — nie podlaczac napiecia >3.3V` |

---

## 8. Governance

- Profile musi przejsc przez `ReadinessGate(review_ready)` przed wejsciem do packa `esp-runtime-01`.
- Poniewaz dotyczy hardware runtime, musi przejsc przez `IntegrityRiskAssessment` i `ReadinessGate(integrity_ready)` przed flashowaniem.
- Profile nie zastepuje bench testu — jest opisem wejsciowym, a nie potwierdzeniem, ze plytka dziala.
- Zmiana profile po flashowaniu wymaga nowego review.
- `board_id` musi byc unikalny w katalogu — nie wolac dwoch profile z tym samym `board_id`.

---

## 9. Output packa `esp-runtime-01`

Po przetworzeniu tego profile pack runtime powinien wyprodukowac:

| Artefakt | Opis |
|----------|------|
| `runtime_profile.json` | Konfiguracja runtime wygenerowana na podstawie profile |
| `pin_map.md` | Mapowanie pinow dla konkretnego projektu |
| `lua_runtime_bundle/` | Skrypty wykonawcze dla runtime |
| `flash_and_recovery_runbook.md` | Instrukcja flashowania i odzyskiwania |
| `bench_test_report.md` | Raport z testu bench po flashowaniu |
