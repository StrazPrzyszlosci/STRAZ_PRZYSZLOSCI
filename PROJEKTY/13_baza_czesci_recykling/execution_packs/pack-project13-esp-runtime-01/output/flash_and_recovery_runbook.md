# Flash and Recovery Runbook: recovered-esp-devkitc-v4-01

- dry_run: True
- generated_at: 2026-04-28T07:52:54+00:00

## 1. Flashowanie

- Metoda: USB-CDC (onboard CP2102)
- Boot mode entry: BOOT button + reset albo auto-reset circuit
- Komenda (przykladowa):

```bash
esptool.py --chip esp32 --port /dev/ttyUSB0 --baud 460800 write_flash -z 0x1000 firmware.bin
```

> Uwaga: Komenda jest przykladowa. Zaleznie od plytki i konfiguracji moze wymagac zmiany.

## 2. Recovery po brick

- Metoda odzyskiwania: reflash via USB-CDC
- Kroki:
  1. Podlaczyc plytke przez USB
  2. Wejsc w download mode: BOOT button + reset albo auto-reset circuit
  3. Reflashowac firmware (krok 1)
  4. Zweryfikowac: `esptool.py verify_flash 0x1000 firmware.bin`

## 3. Backup firmware

- Backup dostepny: TAK
- Lokalizacja: artifacts/recovered-esp-devkitc-v4-01/backup_firmware.bin

## Ostrzezenie

> Ten runbook zostal wygenerowany przez simulated precheck.
> Nie flashowac bez bench testu na realnym hardware i bez ReadinessGate(integrity_ready).
> Patrz: `docs/BENCH_TEST_CONTRACT_ESP_RUNTIME_01.md`
