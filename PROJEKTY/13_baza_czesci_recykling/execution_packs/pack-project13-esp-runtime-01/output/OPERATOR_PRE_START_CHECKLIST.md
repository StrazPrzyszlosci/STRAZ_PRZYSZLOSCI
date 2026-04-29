# Operator Pre-Start Checklist: Real Hardware Bench Test

- pack_id: pack-project13-esp-runtime-01
- board_id: recovered-esp-devkitc-v4-01
- created_at: 2026-04-29

---

## 1. Identyfikacja plytki

- [ ] Plytka fizycznie dostepna i oznaczona jako `recovered-esp-devkitc-v4-01`
- [ ] board_variant = ESP32-WROOM-32D zgodny z napisem na obudowie plytki
- [ ] Wizualna kontrola plytki — brak widocznych uszkodzen, przypalen, pękniec

## 2. Zasilanie

- [ ] Kabel USB sprawdzony (ladowanie/transfer danych)
- [ ] Multimetr cyfrowy sprawdzony i skalibrowany
- [ ] Multimetr ustawiony na pomiar napiecia DC
- [ ] Zrodlo zasilania gotowe (USB z komputera albo zasilacz 5V)

## 3. Oprogramowanie

- [ ] `esptool.py` zainstalowany i dostepny w PATH (`esptool.py version`)
- [ ] Serial terminal zainstalowany (minicom, screen, picocom)
- [ ] Firmware `.bin` dostepny na dysku
- [ ] Python >= 3.8 dostepny

## 4. Backup

- [ ] `artifacts/recovered-esp-devkitc-v4-01/backup_firmware.bin` istnieje na dysku
- [ ] Albo: jawne NIE DOTYCZY (plytka factory new / backup niepotrzebny)

## 5. Siec

- [ ] Testowe AP Wi-Fi 2.4GHz dostepne i dzialajace
- [ ] SSID i haslo w `.env` (nie w repo, nie w diffie)
- [ ] MQTT broker dostepny i dzialajacy
- [ ] Adres broker w `.env` (nie w repo, nie w diffie)

## 6. GPIO i peryferia

- [ ] Zrodlo napiecia referencyjnego dla ADC gotowe (np. 1.0V z diody Zenera albo potencjometru)
- [ ] Opcjonalnie: urzadzenie I2C slave do testow (np. czujnik na adresie 0x3C albo 0x68)
- [ ] Opcjonalnie: LED albo multimetr do weryfikacji GPIO toggle

## 7. Dokumenty

- [ ] `docs/BENCH_TEST_CONTRACT_ESP_RUNTIME_01.md` przeczytany
- [ ] `docs/SIMULATION_VS_REAL_HARDWARE_POLICY_ESP_RUNTIME_01.md` przeczytany
- [ ] `output/REAL_HARDWARE_BENCH_PACKET.md` przeczytany
- [ ] `output/MEASUREMENT_LEDGER.md` wydrukowany albo otwarty na drugim ekranie
- [ ] `output/flash_and_recovery_runbook.md` przeczytany

## 8. Governance

- [ ] Wiem, ze nie wolno flashowac bez bench testu i bez integrity_ready
- [ ] Wiem, ze nie wolno wpisywac sekretow do diffu ani firmware
- [ ] Wiem, ze wynik real_hardware jest autorytatywny nad symulacja
- [ ] Wiem, ze PENDING nie jest PASS — nie domykam gate bez prawdziwych pomiarow

## 9. Decyzja o przejsciu

- [ ] Simulated precheck przeszedl (zadanie 34: conditional, 38 pass, 3 warn, 0 fail)
- [ ] Board profile nie ma BRAKUJACE w sekcjach krytycznych (oprocz power_consumption — uzupelni bench test)
- [ ] Plytka fizycznie dostepna (board_id match)
- [ ] Flash method znany i sprawdzony (USB-CDC)

---

> Po zaznaczeniu wszystkich checkboxow operator moze rozpoczac bench test od kroku 1 (BT-PWR-01) zgodnie z `REAL_HARDWARE_BENCH_PACKET.md`.
