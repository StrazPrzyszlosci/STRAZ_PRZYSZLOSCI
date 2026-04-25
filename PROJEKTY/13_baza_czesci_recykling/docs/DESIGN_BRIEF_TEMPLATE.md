# Design Brief Template

## Cel dokumentu

Ten template jest wejsciowym kontraktem dla packa `pack-project13-blueprint-design-01`. Sluzy do przekazania warstwie `Inzynier AI` minimalnego opisu urzadzenia, ktore ma zostac zaprojektowane z naciskiem na reuse parts z kanonicznego katalogu `Project 13`.

Kazdy wypelniony brief staje sie wejsciem do packa i musi byc reviewowany przed uruchomieniem.

---

## Instrukcja wypelniania

- Pola oznaczone `[WYMAGANE]` sa nienegocjowalne — bez nich pack nie przyjmuje briefu.
- Pola oznaczone `[OPCJONALNE]` moga byc puste, ale ich wypelnienie zmniejsza ryzyko blednego projektu.
- Pola oznaczone `[DO_UZUPELNIENIA]` to wartosci domyslne, ktore maintainer moze nadpisac.
- Wszystkie odniesienia do czesci z katalogu musza uzywac `part_slug` z `data/parts_master.jsonl`.

---

## 1. Identyfikacja urzadzenia

| Pole | Wymagalnosc | Opis |
|------|------------|------|
| `brief_id` | [WYMAGANE] | Unikalny identyfikator briefu, np. `brief-<temat>-01` |
| `device_name` | [WYMAGANE] | Nazwa urzadzenia, np. `Czujnik temperatury z ESP8266` |
| `device_purpose` | [WYMAGANE] | Co urzadzenie ma robic (1-3 zdania) |
| `target_user` | [OPCJONALNE] | Kto bedzie uzywal urzadzenia |
| `project_context` | [OPCJONALNE] | Odniesienie do `PotentialDossier` albo `Experiment`, jesli istnieje |

---

## 2. Funkcja urzadzenia

| Pole | Wymagalnosc | Opis |
|------|------------|------|
| `primary_function` | [WYMAGANE] | Glowna funkcja urzadzenia, np. `pomiar temperatury i wilgotnosci z wysylka przez Wi-Fi` |
| `secondary_functions` | [OPCJONALNE] | Funkcje dodatkowe, np. `wyswietlanie odczytu na OLED` |
| `inputs` | [WYMAGANE] | Lista sygnalow wejsciowych, np. `1x analog temp sensor, 1x I2C humidity sensor` |
| `outputs` | [WYMAGANE] | Lista sygnalow wyjsciowych, np. `1x Wi-Fi telemetry, 1x I2C OLED display` |
| `communication_interfaces` | [WYMAGANE] | Interfejsy komunikacyjne, np. `Wi-Fi, I2C, UART` |
| `data_flow` | [OPCJONALNE] | Krotki opis przeplywu danych przez urzadzenie |

---

## 3. Zasilanie

| Pole | Wymagalnosc | Opis |
|------|------------|------|
| `power_source` | [WYMAGANE] | Rodzaj zasilania: `USB 5V`, `bateria 3.7V LiPo`, `DC 12V`, `solar`, `POE` itp. |
| `voltage_levels` | [WYMAGANE] | Wymagane poziomy napiecia, np. `3.3V (MCU), 5V (sensor)` |
| `max_current_draw` | [WYMAGANE] | Szacowany maksymalny pobor pradu, np. `300mA peak, 50mA idle` |
| `power_constraints` | [OPCJONALNE] | Ograniczenia energetyczne, np. `bateria ma wystarczyc na 48h` |

---

## 4. Srodowisko pracy

| Pole | Wymagalnosc | Opis |
|------|------------|------|
| `operating_environment` | [WYMAGANE] | Gdzie urzadzenie bedzie pracować: `indoor`, `outdoor_sheltered`, `outdoor_exposed`, `industrial`, `wet_area` |
| `temperature_range` | [WYMAGANE] | Zakres temperatur roboczych, np. `0C do 50C` |
| `humidity_range` | [OPCJONALNE] | Zakres wilgotnosci, np. `10-90% RH, non-condensing` |
| `mechanical_constraints` | [OPCJONALNE] | Ograniczenia mechaniczne: wibracje, obudowa, montaz |
| `emc_requirements` | [OPCJONALNE] | Wymagania EMC, jesli dotyczy |

---

## 5. Ograniczenia kosztowe

| Pole | Wymagalnosc | Opis |
|------|------------|------|
| `max_bom_cost` | [WYMAGANE] | Maksymalny koszt czesci niebedacych w katalogu reuse, np. `30 PLN` |
| `reuse_priority` | [WYMAGANE] | Priorytet reuse: `reuse_first` (domyslnie) albo `cost_first` |
| `budget_notes` | [OPCJONALNE] | Dodatkowe uwagi o budzecie |

---

## 6. Reuse parts — preferencje z katalogu

### 6.1 Czesci z kanonicznego katalogu (`data/parts_master.jsonl`)

| `part_slug` | Ilosc | Uwagi |
|-------------|-------|-------|
| __DO_UZUPELNIENIA__ | __DO_UZUPELNIENIA__ | __DO_UZUPELNIENIA__ |

### 6.2 Czesci spoza katalogu (missing parts)

| Funkcja | Wymagany parametr | Czy da sie pozyskac z donor board? | Uwagi |
|---------|------------------|-----------------------------------|-------|
| __DO_UZUPELNIENIA__ | __DO_UZUPELNIENIA__ | __DO_UZUPELNIENIA__ | __DO_UZUPELNIENIA__ |

---

## 7. Zalozenia i ograniczenia projektowe

| Pole | Wymagalnosc | Opis |
|------|------------|------|
| `assumptions` | [WYMAGANE] | Lista zalozen, na ktorych opiera sie brief, np. `ESP8266 wystarczy do obslugi Wi-Fi i I2C`, `zasilanie USB jest stale dostepne` |
| `constraints` | [WYMAGANE] | Lista twardych ograniczen, np. `brak lutowania BGA`, `obudowa max 100x60mm` |
| `known_risks` | [OPCJONALNE] | Znane ryzyka projektowe, np. `ESP8266 moze byc za wolny do ciaglego odczytu ADC` |
| `compliance` | [OPCJONALNE] | Wymagania zgodnosci, np. `CE`, `FCC`, `RoHS` |

---

## 8. Donor board profile (jezeli projekt targetuje ESP32)

| Pole | Wymagalnosc | Opis |
|------|------------|------|
| `target_board` | [OPCJONALNE] | Jawnie nazwana plytka `ESP32`, np. `ESP32-DevKitC-V4` albo `recovered-esp-wroom-32-01` |
| `board_capabilities` | [OPCJONALNE] | Odniesienie do `ESP32 Recovered Board Profile Template`, jesli plytka odzyskana |
| `flash_method` | [OPCJONALNE] | Sposob flashowania, np. `USB-CDC`, `UART`, `OTA` |

---

## 9. Output packa `blueprint-design-01`

Po przetworzeniu tego briefu pack powinien wyprodukowac:

| Artefakt | Opis |
|----------|------|
| `design_dossier.md` | Opis projektu z uzasadnieniem wyboru czesci |
| `bill_of_materials.json` | BOM z odniesieniami do `part_slug` z katalogu albo oznaczeniem `missing` |
| `assembly_instructions.md` | Instrukcja montazu reviewowalna bez ukrytych promptow |
| `design_risks.json` | Zidentyfikowane ryzyka projektowe i ich mitygacje |
| `missing_parts_or_assumptions.json` | Lista czesci brakujacych i zalozen, ktore trzeba potwierdzic |

---

## 10. Governance

- Brief musi przejsc przez `ReadinessGate(review_ready)` przed uruchomieniem packa.
- Jesli projekt dotyczy hardware runtime albo sterowania swiatem fizycznym, musi przejsc przez `IntegrityRiskAssessment` i `ReadinessGate(integrity_ready)`.
- Brief nie jest promowany do katalogu — jest wejsciem do packa, a nie artefaktem kanonicznym.
