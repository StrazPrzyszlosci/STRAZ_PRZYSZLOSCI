# Mini-Handoff Zadanie 27

## Co zostalo zrobione

Utworzono minimalny dry-run execution surface dla packa `pack-project13-blueprint-design-01`:

- Skrypt `dry_run_blueprint_design.py` przyjmuje wypelniony design brief (markdown), waliduje go, parsuje pola, dopasowuje reuse parts z sekcji 6 do kanonicznego katalogu `parts_master.jsonl`, generuje 6 review-ready artefaktow
- Artefakty generowane w `pack-project13-blueprint-design-01/output/`:
  1. `design_dossier.md` — uzasadnienie wyboru czesci i opis logiczny
  2. `bill_of_materials.json` — BOM z odniesieniami do katalogu lub oznaczeniem missing
  3. `assembly_instructions.md` — instrukcja montazu (opisowa, nie CAD)
  4. `design_risks.json` — zidentyfikowane ryzyka projektowe
  5. `missing_parts_or_assumptions.json` — czesci brakujace i zalozenia
  6. `dry_run_report.md` — raport z dry-run z 14 checkami
- Zaktualizowano `manifest.json` — status zmieniony z `draft` na `dry_run_ready`, dodano sekcje `dry_run_surface`
- Zaktualizowano `RUNBOOK.md` — komenda dry-run zamiast PLACEHOLDERa
- Zaktualizowano `readiness_gate.json` — status zmieniony z `pending` na `conditional`
- Zaktualizowano `task.json` — status zmieniony z `pending` na `dry_run_ready`
- Skopiowano dry-run report do `autonomous_test/reports/`

## Jakie pliki dotknieto

- `PROJEKTY/13_baza_czesci_recykling/scripts/dry_run_blueprint_design.py` (nowy)
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-blueprint-design-01/manifest.json` (zmieniony)
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-blueprint-design-01/RUNBOOK.md` (zmieniony)
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-blueprint-design-01/readiness_gate.json` (zmieniony)
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-blueprint-design-01/task.json` (zmieniony)
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-blueprint-design-01/output/` (nowy katalog z 6 artefaktami)
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/dry_run_blueprint_design_01_2026-04-26.md` (nowy)

## Jak walidowac dry-run

```bash
python3 PROJEKTY/13_baza_czesci_recykling/scripts/dry_run_blueprint_design.py \
  --brief PROJEKTY/13_baza_czesci_recykling/docs/SAMPLE_DESIGN_BRIEF_WIFI_TEMP_SENSOR.md
```

Wynik: `overall: pass`, 14/14 checks pass, BOM summary: total=6, reuse=3, missing=3.

Dodatkowe komendy walidacyjne wykonane:
- `python3 -m py_compile` — brak bledow skladni
- `git diff --check` — brak bledow whitespace
- parsowanie `manifest.json`, `readiness_gate.json`, `task.json` — poprawny JSON

## Jaki dry-run surface dodano

Skrypt `dry_run_blueprint_design.py` realizuje pelny pipeline packa na minimalnym, uczciwym poziomie:
1. Walidacja briefu przez istniejacy `validate_design_brief.py`
2. Parsowanie pol z markdown tables
3. Parsowanie sekcji 6.1 (reuse parts z katalogu) i 6.2 (missing parts)
4. Lookup reuse parts w `parts_master.jsonl`
5. Generowanie BOM z oznaczeniem source (reuse_catalog / missing_from_catalog / missing)
6. Generowanie design dossier z uzasadnieniem wyboru czesci
7. Generowanie assembly instructions (opisowe, nie CAD)
8. Generowanie design risks (z briefu + z analizy catalog coverage + ADC check)
9. Generowanie missing_parts_or_assumptions
10. Generowanie dry-run report z checkami

## Jaki artefakt powstaje z poprawnego briefu

Dla `SAMPLE_DESIGN_BRIEF_WIFI_TEMP_SENSOR.md`:
- BOM: 6 pozycji (3 reuse z katalogu: esp8266ex, lm7805-regulator, resistor-100k-0805; 3 missing: NTC 10k, modul ESP8266 dev board, rezystor 10k)
- Design dossier: uzasadnienie wyboru ESP8266, schemat logiczny dzielnika NTC, opis polaczenia Wi-Fi/MQTT
- Design risks: 4 ryzyka (ADC range, Wi-Fi stability, watchdog, brak data_flow w briefie — uzupelniony)
- Assembly instructions: 4 kroki montazowe + ostrzezenie o BGA/QFN

## Jaki jest nowy status blueprint-design-01

- manifest: `dry_run_ready` (byl: `draft`)
- readiness_gate: `conditional` (byl: `pending`)
- task: `dry_run_ready` (byl: `pending`)

Pack nie przeskoczyl sztucznie na `active` ani `pass` — dry-run dziala, ale pelny execution surface nie istnieje.

## Czego nadal brakuje do pierwszego realnego runu

1. Pelny execution surface (`generate_blueprint.py`) — dry-run nie generuje CAD, schematic PCB, ani netlist
2. Gestosc `parts_master.jsonl` — tylko 4 rekordy, zbyt malo dla realnego BOM wielu urzadzen
3. Walidacja `part_slug` wzgledem katalogu jest sprawdzana w dry-run (warn), ale nie blokuje
4. Pola sekcji 6 (Reuse parts) nie sa walidowane per-wiersz przez validator briefu
5. Integracja z KiCad / InvenTree — brak powiazania z symbolami i footprintami poza metadanymi w katalogu
6. IntegrityRiskAssessment i ReadinessGate(integrity_ready) nadal wymagane przed promocja do runtime
7. Brak testow automatycznych (unit/integration) dla `dry_run_blueprint_design.py`
8. Brak mozliwosci wyboru czesci z katalogu na podstawie parametrow briefu (automatyczne dopasowanie) — obecnie tylko lookup po slugach z sekcji 6.1
