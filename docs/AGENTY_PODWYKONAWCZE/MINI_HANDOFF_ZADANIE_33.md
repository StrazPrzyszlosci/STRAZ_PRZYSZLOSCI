# Mini-Handoff Zadanie 33

## Co zostalo zrobione

1. Zintegrowano `validate_reuse_section_rows()` i `validate_assumptions_constraints_rows()` w glownym przeplywie `validate_design_brief.py` — wczesniej te funkcje istnialy, ale nie byly nigdy wywolywane.

2. Utrwalniono `validate_assumptions_constraints_rows()`:
   - min 2 konkretne punkty w assumptions i constraints (oddzielone kropkami)
   - kazdy punkt min 5 znakow (po usunieciu numeracji)
   - obsluga numerowanych list (np. "1. Foo. 2. Bar.") — numeracja jest usuwana przed sprawdzeniem dlugosci
   - wykrywanie placeholderow w poszczegolnych punktach

3. Dodano `validate_internal_consistency()` — sprawdza wewnetrzna spojnosc briefu:
   - I2C/SPI/UART wymienione w `inputs` ale nieobecne w `communication_interfaces`
   - voltage 3.3V z power_source USB 5V bez regulatora w assumptions
   - outdoor_exposed bez odpowiednich zalozen/ograniczen
   - max_bom_cost=0 z reuse_priority innym niz cost_first

4. Zintegrowano walidacje wierszy w `dry_run_blueprint_design.py` — nowy check `brief_row_validation` blokuje dry-run przy bledach w sekcjach 6/7.

5. Utworzono `smoke_test_blueprint_design.py` — minimalny smoke-test baseline z 4 testami:
   - INVALID_BRIEF (dry-run) — oczekiwany FAIL
   - INVALID_BRIEF (validator) — oczekiwany FAIL
   - VALID_BRIEF (dry-run) — oczekiwany PASS
   - VALID_BRIEF (validator) — oczekiwany PASS

6. Utworzono `INVALID_DESIGN_BRIEF_BAD_ROWS.md` — celowo bledny brief z 14 klasami bledow.

7. Zaktualizowano `RUNBOOK.md` — dodano dokumentacje walidacji wierszy i smoke-testu.

8. Zaktualizowano `manifest.json` — dodano `row_validation_added_by`, `smoke_test_script`, rozszerzono opis `note`.

## Jakie pliki dotknieto

- `PROJEKTY/13_baza_czesci_recykling/scripts/validate_design_brief.py` (edytowany)
- `PROJEKTY/13_baza_czesci_recykling/scripts/dry_run_blueprint_design.py` (edytowany)
- `PROJEKTY/13_baza_czesci_recykling/scripts/smoke_test_blueprint_design.py` (nowy)
- `PROJEKTY/13_baza_czesci_recykling/docs/INVALID_DESIGN_BRIEF_BAD_ROWS.md` (nowy)
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-blueprint-design-01/RUNBOOK.md` (edytowany)
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-blueprint-design-01/manifest.json` (edytowany)
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/smoke_test_blueprint_design_01_2026-04-28.md` (nowy)

## Co zweryfikowano

- `python3 -m py_compile` na 3 skryptach — brak bledow skladni
- `validate_design_brief.py` na SAMPLE_DESIGN_BRIEF — PASS
- `validate_design_brief.py` na INVALID_DESIGN_BRIEF — FAIL z 14 bledami
- `dry_run_blueprint_design.py` na SAMPLE_DESIGN_BRIEF — overall: pass, 15/15 checks pass
- `dry_run_blueprint_design.py` na INVALID_DESIGN_BRIEF — FAIL (przerwany po walidacji)
- `smoke_test_blueprint_design.py` — 4/4 testow przeszlo, OVERALL: PASS
- `git diff --check` — brak bledow whitespace
- `manifest.json` — poprawny JSON

## Jakie klasy bledow briefu sa teraz lapane wczesniej

1. Placeholder w part_slug sekcji 6.1 (`__DO_UZUPELNIENIA__`, `TBD`, `TODO`)
2. Bledny format part_slug (znaki inne niz male litery, cyfry, mysliniki, podkreslenia)
3. Nieprawidlowa quantity w sekcji 6.1 (tekst zamiast liczby, np. "zero", "TBD")
4. Placeholder w Funkcja sekcji 6.2
5. Pusty Wymagany parametr w sekcji 6.2
6. Bledna wartosc donor_available (nie TAK/NIE/SPRAWDZIC z wyjasnieniem)
7. Puste assumptions/constraints
8. Placeholder assumptions/constraints
9. Zbyt malo punktow w assumptions (min 2)
10. Zbyt malo punktow w constraints (min 2)
11. Zbyt krotkie punkty w assumptions/constraints (min 5 znakow)
12. Placeholder w poszczegolnych punktach assumptions/constraints
13. I2C/SPI/UART w inputs ale nie w communication_interfaces
14. Voltage 3.3V z USB 5V bez regulatora w assumptions
15. Empty section 6 (naglowek istnieje, ale brak wierszy)

## Czego nadal nie obejmuje ten dry-run

1. Pelny execution surface (`generate_blueprint.py`) — dry-run nie generuje CAD, schematic PCB, ani netlist
2. Gestosc `parts_master.jsonl` — tylko 4 rekordy, zbyt malo dla realnego BOM wielu urzadzen
3. Integracja z KiCad / InvenTree
4. IntegrityRiskAssessment i ReadinessGate(integrity_ready)
5. Walidacja required_param formatu w sekcji 6.2 (np. sprawdzanie czy "10k, B=3950" ma sens)
6. Automatyczne dopasowanie czesci z katalogu na podstawie parametrow briefu
7. Walidacja poprawnosci elektronicznej (np. czy zasilanie 3.3V i 5V jest spojne z czesciami w BOM)
