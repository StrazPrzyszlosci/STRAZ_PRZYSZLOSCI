# Bench Test Report: recovered-esp-devkitc-v4-01

## Metryka
- Data testu: BRAK — bench test nie zostal wykonany
- board_id: `recovered-esp-devkitc-v4-01`
- board_variant: `ESP32-WROOM-32D`
- flash_method: `USB-CDC (onboard CP2102)`
- Tester: BRAK — brak operatora z fizyczna plytka

> **REAL_HARDWARE_REQUIRED** — bench test nie zostal wykonany na fizycznej plytce.
> Zadne wartosci symulowane nie zostaly wpisane jako realne pomiary.
> Zgodnie z `SIMULATION_VS_REAL_HARDWARE_POLICY_ESP_RUNTIME_01.md` sekcja 5:
> runtime bundle nie moze byc mergowany bez bench testu na real_hardware.
> Patrz: `esp_runtime_bench_receipt_2026-04-30.json` (blocker receipt).

## Wyniki

| Test ID | Test | Kategoria | Status | Wartosc zmierzona | Wartosc oczekiwana | Delta |
|---------|------|-----------|--------|-------------------|-------------------|-------|
| BT-PWR-01 | Pomiar napiecia wejsciowego vs input_voltage | real_hardware | PENDING | BRAK | 5V (+/-0.2V) | N/A |
| BT-PWR-02 | Pomiar napiecia roboczego MCU vs operating_voltage | real_hardware | PENDING | BRAK | 3.3V (+/-0.1V) | N/A |
| BT-PWR-03 | Pomiar pradu idle vs power_consumption_idle | real_hardware | PENDING | BRAK | BRAKUJACE w board profile | N/A |
| BT-PWR-04 | Pomiar pradu Wi-Fi TX vs power_consumption_wifi_tx | real_hardware | PENDING | BRAK | BRAKUJACE w board profile | N/A |
| BT-PWR-05 | Stabilnosc zasilania pod obciazeniem | real_hardware | PENDING | BRAK | Brak brownout w 60s | N/A |
| BT-FLS-01 | Flash firmware przez USB-CDC | real_hardware | PENDING | BRAK | esptool verify sukces | N/A |
| BT-FLS-02 | Wejscie w download mode przez BOOT+RESET | real_hardware | PENDING | BRAK | Powtarzalny download mode | N/A |
| BT-FLS-03 | Recovery po brick | real_hardware | PENDING | BRAK | Plytka odzyskana | N/A |
| BT-FLS-04 | Backup oryginalnego firmware istnieje lub NIE DOTYCZY | either | PENDING | BRAK | .bin na dysku albo NIE DOTYCZY | N/A |
| BT-GPIO-01 | Piny free odpowiadaja na toggle (19 free GPIO) | real_hardware | PENDING | BRAK | Odczyt zwrotny HIGH/LOW | N/A |
| BT-GPIO-02 | Piny damaged wykluczone z pin map | either | PENDING | BRAK | Pin map nie uzywa damaged | N/A |
| BT-GPIO-03 | ADC1 odczyt z napiecia referencyjnego | real_hardware | PENDING | BRAK | +/-10% wartosci ref | N/A |
| BT-GPIO-04 | I2C scan — wykrycie slave | real_hardware | PENDING | BRAK | Adres slave albo no device | N/A |
| BT-GPIO-05 | UART0 komunikacja serial | real_hardware | PENDING | BRAK | Echo test | N/A |
| BT-NET-01 | Wi-Fi scan — plytka widzi sieci 2.4GHz | real_hardware | PENDING | BRAK | >=1 siec wykryta | N/A |
| BT-NET-02 | Wi-Fi connect do testowego AP | real_hardware | PENDING | BRAK | Connect <=10s | N/A |
| BT-NET-03 | MQTT publish do testowego broker | real_hardware | PENDING | BRAK | Message delivered | N/A |
| BT-NET-04 | Antena — jakosc sygnalu (RSSI) | real_hardware | PENDING | BRAK | RSSI >= -80dBm @ 3m | N/A |
| BT-STO-01 | Rozmiar flash vs flash_size (4MB) | real_hardware | PENDING | BRAK | Zgodnosc +/-0 | N/A |
| BT-STO-02 | Odczyt tabeli partycji | real_hardware | PENDING | BRAK | Partycje czytelne | N/A |

## Podsumowanie

- PASS: 0
- FAIL: 0
- PENDING: 20
- SKIP: 0
- NOT_APPLICABLE: 0

## Werdykt

- [ ] Runtime bundle moze byc promowany (wszystkie real_hardware = PASS albo NOT_APPLICABLE)
- [x] Runtime bundle NIE MOZE byc promowany (istnieje PENDING na real_hardware — brak fizycznej plytki)

## Blokery (zadanie 46, 2026-04-30)

1. **Brak fizycznej plytki** — ESP32-DevKitC-V4 (recovered-esp-devkitc-v4-01) niedostepna
2. **Brak multimetru** — brak sprzetu do pomiaru napiecia i pradu
3. **Brak firmware .bin** — brak pliku firmware do flashowania
4. **Brak testowego AP Wi-Fi** — brak sieci 2.4GHz z kontrola credentials
5. **Brak MQTT broker** — brak testowego broker do publish testu

### Nastepny ruch

Gdy operator z fizyczna plytka bedzie dostepny:
1. Przejsc `OPERATOR_PRE_START_CHECKLIST.md`
2. Wykonac bench test wg `REAL_HARDWARE_BENCH_PACKET.md` krok po kroku
3. Wpisac odczyty do `MEASUREMENT_LEDGER.md`
4. Uzupelnic ten report rzeczywistymi wynikami
5. Zaktualizowac `readiness_gate.json` zgodnie z `READINESS_GATE_MAPPING.md`
