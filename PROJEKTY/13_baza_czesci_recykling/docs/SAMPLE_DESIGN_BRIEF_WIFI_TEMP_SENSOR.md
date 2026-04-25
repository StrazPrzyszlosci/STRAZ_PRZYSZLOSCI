# Sample Design Brief: Czujnik Temperatury Wi-Fi z ESP8266

Ten plik jest przykladowym wypelnieniem `DESIGN_BRIEF_TEMPLATE.md` dla prostego urzadzenia reuse-first. Sluzy jako wzorzec dla maintainerow i agentow tworzacych kolejne briefy.

---

## 1. Identyfikacja urzadzenia

| Pole | Wartosc |
|------|---------|
| brief_id | brief-wifi-temp-sensor-01 |
| device_name | Czujnik temperatury Wi-Fi z ESP8266 |
| device_purpose | Pomiar temperatury w pomieszczeniu i wysylka odczytow przez Wi-Fi na endpoint MQTT |
| target_user | Wolontariusz monitorujacy magazyn elektroodpadow |
| project_context | dossier-project13-resource-scouting-01 |

---

## 2. Funkcja urzadzenia

| Pole | Wartosc |
|------|---------|
| primary_function | Cykliczny pomiar temperatury co 60s i publish przez MQTT po Wi-Fi |
| secondary_functions | LED sygnalizujacy status polaczenia |
| inputs | 1x analog temperature sensor (NTC 10k), 1x GPIO status LED |
| outputs | 1x Wi-Fi MQTT telemetry, 1x GPIO LED |
| communication_interfaces | Wi-Fi (ESP8266), MQTT over TCP |
| data_flow | NTC -> ADC -> ESP8266 -> Wi-Fi -> MQTT broker |

---

## 3. Zasilanie

| Pole | Wartosc |
|------|---------|
| power_source | USB 5V z ladowarki telefonu |
| voltage_levels | 3.3V (ESP8266, sensor), 5V (USB input) |
| max_current_draw | 300mA peak (Wi-Fi transmit), 20mA idle |
| power_constraints | Brak baterii — zasilanie stale z USB |

---

## 4. Srodowisko pracy

| Pole | Wartosc |
|------|---------|
| operating_environment | indoor |
| temperature_range | 0C do 50C |
| humidity_range | 10-80% RH, non-condensing |
| mechanical_constraints | Brak obudowy w pierwszej iteracji — prototyp na plytce stykowej |
| emc_requirements | Brak |

---

## 5. Ograniczenia kosztowe

| Pole | Wartosc |
|------|---------|
| max_bom_cost | 20 PLN |
| reuse_priority | reuse_first |
| budget_notes | Koszt dotyczy tylko czesci brakujacych w katalogu reuse |

---

## 6. Reuse parts — preferencje z katalogu

### 6.1 Czesci z kanonicznego katalogu (data/parts_master.jsonl)

| part_slug | Ilosc | Uwagi |
|-----------|-------|-------|
| esp8266ex | 1 | MCU z Wi-Fi — kluczowy element reuse |
| lm7805-regulator | 1 | Stabilizator 5V — opcjonalny, zalezy od zrodla USB |
| resistor-100k-0805 | 2 | Pull-up dla ADC i LED |

### 6.2 Czesci spoza katalogu (missing parts)

| Funkcja | Wymagany parametr | Czy da sie pozyskac z donor board? | Uwagi |
|---------|------------------|-----------------------------------|-------|
| Termistor NTC 10k | 10k, B=3950 | TAK — popularny w starych termostatach | Brak w katalogu, ale czesty w elektroodpadach |
| Modul ESP8266 na plytce deweloperskiej | GPIO, ADC, Wi-Fi | TAK — z odzyskanych routerow/IoT | Uzyty jako czarna skrzynka, bez lutowania samego QFN |
| Rezystor 10k do dzielnika NTC | 10k, 0805 | TAK | Brak w katalogu, ale powszechny |

---

## 7. Zalozenia i ograniczenia projektowe

| Pole | Wartosc |
|------|---------|
| assumptions | 1. ESP8266 modul deweloperski jest dostepny z odzysku. 2. Zasilanie USB jest stale dostepne. 3. MQTT broker istnieje w sieci lokalnej. 4. ADC ESP8266 jest wystarczajacy do odczytu NTC (10-bit, 0-1V). |
| constraints | 1. Brak lutowania BGA/QFN — tylko moduly THT albo gotowe plytki deweloperskie. 2. Prototyp bez obudowy. 3. Brak zasilania bateryjnego w v1. |
| known_risks | 1. ADC ESP8266 ma tylko 1 kanal i zakres 0-1V — wymaga dzielnika napiecia. 2. Wi-Fi na ESP8266 moze byc niestabilny przy malym zasiegu. 3. Brak watchdog — ryzyko zawieszenia bez autorestartu. |
| compliance | Brak w prototypie |

---

## 8. Donor board profile

| Pole | Wartosc |
|------|---------|
| target_board | Nie dotyczy — projekt targetuje ESP8266, nie ESP32 |
| board_capabilities | Nie dotyczy |
| flash_method | UART przez USB-TTL albo bezposrednio przez USB-CDC na plytce NodeMCU |

---

## 9. Output packa blueprint-design-01

Oczekiwane artefakty po przetworzeniu tego briefu:

| Artefakt | Spodziewana tresc |
|----------|-------------------|
| design_dossier.md | Uzasadnienie wyboru ESP8266, schemat logiczny dzielnika NTC, opis polaczenia Wi-Fi/MQTT |
| bill_of_materials.json | 1x esp8266ex (reuse), 1x lm7805-regulator (reuse), 2x resistor-100k-0805 (reuse), 1x NTC 10k (missing), 1x rezystor 10k (missing) |
| assembly_instructions.md | Schemat podlaczenia na plytce stykowej, instrukcja flashowania firmware |
| design_risks.json | ADC range, Wi-Fi stability, watchdog |
| missing_parts_or_assumptions.json | NTC 10k, rezystor 10k, zalozenie o dostepnosci MQTT broker |

---

## 10. Governance

- Brief jest wejsciem do packa — nie wymaga Approval, ale wymaga ReadinessGate(review_ready).
- Poniewaz projekt dotyczy hardware, po wyprodukowaniu artefaktow packa potrzebny bedzie IntegrityRiskAssessment i ReadinessGate(integrity_ready) przed jakimkolwiek flashowaniem.
