# Instrukcja Montazu: Czujnik temperatury Wi-Fi z ESP8266

- dry_run: True
- generated_at: 2026-04-26T15:45:53+00:00

## Wymagane czesci

- [REUSE] 1x ESP8266EX
- [REUSE] 1x 7805
- [REUSE] 2x 100K Resistor
- [MISSING] 1x Termistor NTC 10k
- [MISSING] 1x Modul ESP8266 na plytce deweloperskiej
- [MISSING] 1x Rezystor 10k do dzielnika NTC

## Krok 1: Przygotowanie zasilania

Zrodlo zasilania: USB 5V z ladowarki telefonu

## Krok 2: Podlaczenie czesci reuse

> Szczegolowe schematy podlaczenia sa poza zakresem tego dry-run.
> Nie lutowac BGA/QFN bez odpowiedniego sprzetu i doswiadczenia.

## Krok 3: Flashowanie firmware

Metoda flashowania: UART przez USB-TTL albo bezposrednio przez USB-CDC na plytce NodeMCU

## Krok 4: Test podstawowy

> Urzadzenie musi przejsc IntegrityRiskAssessment i ReadinessGate(integrity_ready)
> przed jakimkolwiek flashowaniem na realnym hardware.

