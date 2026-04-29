# Design Dossier: Czujnik temperatury Wi-Fi z ESP8266

- brief_id: `brief-wifi-temp-sensor-01`
- dry_run: True
- generated_at: 2026-04-28T01:23:38+00:00

## 1. Uzasadnienie wyboru czesci

Reuse priority: **reuse_first**

### Czesci z kanonicznego katalogu

- **ESP8266EX** (`esp8266ex`): Highly integrated Wi-Fi SoC commonly reused in automation and telemetry prototypes.  — 1x z katalogu reuse
- **7805** (`lm7805-regulator`): Standard 5 V linear regulator recovered from legacy consumer electronics.  — 1x z katalogu reuse
- **100K Resistor** (`resistor-100k-0805`): General purpose 100k resistor in 0805 package.  — 2x z katalogu reuse

### Czesci brakujace (missing parts)

- **Termistor NTC 10k** (10k, B=3950): donor=TAK — Brak w katalogu, ale czesty w elektroodpadach
- **Modul ESP8266 na plytce deweloperskiej** (GPIO, ADC, Wi-Fi): donor=TAK — Uzyty jako czarna skrzynka, bez lutowania samego QFN
- **Rezystor 10k do dzielnika NTC** (10k, 0805): donor=TAK — Brak w katalogu, ale powszechny

## 2. Schemat logiczny (dry-run)

- Funkcja glowna: Cykliczny pomiar temperatury co 60s i publish przez MQTT po Wi-Fi
- Zasilanie: USB 5V z ladowarki telefonu (3.3V (ESP8266, sensor), 5V (USB input))
- Komunikacja: Wi-Fi (ESP8266), MQTT over TCP
- Srodowisko: indoor

> Uwaga: To jest dry-run dossier. Schemat logiczny jest opisowy, nie CAD.
> Nie udaje gotowosci hardware bez bench review.

## 3. Przeplyw danych

- NTC -> ADC -> ESP8266 -> Wi-Fi -> MQTT broker

## 4. Zalozenia i ograniczenia

- Zalozenia: 1. ESP8266 modul deweloperski jest dostepny z odzysku. 2. Zasilanie USB jest stale dostepne. 3. MQTT broker istnieje w sieci lokalnej. 4. ADC ESP8266 jest wystarczajacy do odczytu NTC (10-bit, 0-1V).
- Ograniczenia: 1. Brak lutowania BGA/QFN — tylko moduly THT albo gotowe plytki deweloperskie. 2. Prototyp bez obudowy. 3. Brak zasilania bateryjnego w v1.
- Ryzyka: 1. ADC ESP8266 ma tylko 1 kanal i zakres 0-1V — wymaga dzielnika napiecia. 2. Wi-Fi na ESP8266 moze byc niestabilny przy malym zasiegu. 3. Brak watchdog — ryzyko zawieszenia bez autorestartu.

## 5. BOM summary

- Total items: 6
- Reuse z katalogu: 3
- Nie znalezione w katalogu: 0
- Missing (spoza katalogu): 3

