# Rebuild Autonomous Outputs Report

- source: autonomous_test/results/test_db.jsonl
- total_records: 82
- accepted_records: 77
- skipped_records: 5
- inventree_rows: 74
- ecoeda_rows: 74

## Outputs

- autonomous_test/results/inventree_import.jsonl
- autonomous_test/results/ecoEDA_inventory.csv
- autonomous_test/reports/rebuild_autonomous_outputs_skipped.jsonl

## Skip Reasons

- empty_or_placeholder_part_number: 2
- looks_like_designator_list: 1
- looks_like_plain_text_phrase: 2

## Sample Accepted Parts

- 1500µF | Power Supply Unit (PSU) internal components | Industrial Panel PC (likely Advantech or similar)
- TPS65994 | TPS65994 | ASUS ROG Flow Z13 GZ301Z
- Lenovo NOK ILG5081008 308C1K835W000Y 43398 7628365100030 | RAM Module | Lenovo Laptop
- M425R1GB4BB0-CWM0D | Battery Connector | Lenovo Laptop
- P28A41E | SMD Capacitors | Lenovo Laptop
- 230130, 2R2, 33 25V H33 | SMD Resistors | Lenovo Laptop
- 3336220400007 | RAM slots | Dell Precision M4800
- N15P-Q3-A1 | GPU chip (NVIDIA) | Dell Precision M4800
- CD3301BRHHR | Power management IC | Dell Precision M4800
- 4217 | LVDS Signal Generator | Unknown TV Mainboard

## Sample Skipped Records

- looks_like_designator_list | part_number=R29, C13 | part_name=Electrolytic Capacitors (Motherboard) | device=Industrial Panel PC (likely Advantech or similar)
- looks_like_plain_text_phrase | part_number=WARSZTAT AUTOMATYKI | part_name=Electrolytic Capacitors (PSU) | device=Industrial Panel PC (likely Advantech or similar)
- looks_like_plain_text_phrase | part_number=Technics | part_name=Cassette mechanism assembly | device=Technics Cassette Deck
- empty_or_placeholder_part_number | part_number=null | part_name=USB Flash Drive PCB | device=Samsung 850 EVO SSD / SVOD Programmer
- empty_or_placeholder_part_number | part_number=None | part_name= | device=Nieznany Model
