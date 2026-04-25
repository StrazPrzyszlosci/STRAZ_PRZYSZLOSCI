# Mini-Handoff Zadanie 14

## Co zostalo zrobione

Utworzono `design brief template` i przykladowy wypelniony brief:

- `PROJEKTY/13_baza_czesci_recykling/docs/DESIGN_BRIEF_TEMPLATE.md`
- `PROJEKTY/13_baza_czesci_recykling/docs/SAMPLE_DESIGN_BRIEF_WIFI_TEMP_SENSOR.md`

## Jakie pliki dotknieto

- `PROJEKTY/13_baza_czesci_recykling/docs/DESIGN_BRIEF_TEMPLATE.md` (nowy)
- `PROJEKTY/13_baza_czesci_recykling/docs/SAMPLE_DESIGN_BRIEF_WIFI_TEMP_SENSOR.md` (nowy)

## Jakie pola uznano za nienegocjowalne

Pola oznaczone `[WYMAGANE]` w szablonie:

- `brief_id`, `device_name`, `device_purpose`
- `primary_function`, `inputs`, `outputs`, `communication_interfaces`
- `power_source`, `voltage_levels`, `max_current_draw`
- `operating_environment`, `temperature_range`
- `max_bom_cost`, `reuse_priority`
- `assumptions`, `constraints`

Bez ktoregokolwiek z tych pol pack nie przyjmuje briefu.

## Co zweryfikowano

- spojnosc z `PLAN_PACKOW_BLUEPRINT_ESP_CLAW.md`: input contract z sekcji "Pack 1" pokrywa sie z polami szablonu (brief funkcjonalny, ograniczenia projektowe, snapshot katalogu, donor board profiles)
- szablon rozroznia reuse parts (sekcja 6.1 z `part_slug`), missing parts (sekcja 6.2) i zalozenia (sekcja 7)
- sample brief uzywal realnych `part_slug` z `data/parts_master.jsonl`: `esp8266ex`, `lm7805-regulator`, `resistor-100k-0805`
- `git diff --check`: brak bledow whitespace

## Co nadal trzeba doprecyzowac przed pack skeletonem

- czy `brief_id` ma byc generowany automatycznie, czy nadawany recznie przez maintainera
- czy szablon wymaga formalnego schema JSON, czy markdown wystarczy jako input contract (zgodnie z blockerem: bez sztucznego wymuszania zlego schema contract)
- czy `parts_master.jsonl` ma wystarczajaca gestosc danych dla warstwy projektowej (obecnie 4 rekordy — za malo dla realnego BOM)
- czy `donor board profile template` (zadanie 15) jest gotowy, zeby podpiac sekcje 8 szablonu
- czy pack `blueprint-design-01` ma walidowac `part_slug` wzgledem katalogu automatycznie, czy recznie przez review
