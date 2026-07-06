# Handoff dla Następnego Agenta - po T11/T14 (Agentic Cells + Model Resource Selector) - 2026-07-06

## Kontekst

Poprzedni scaffold T10 był zbyt wąski wobec wizji użytkownika. Doprecyzowanie: Straż Przyszłości ma być **wieloogniwową automatyzacją agentyczną**. Ogniwa mają być małe, wyspecjalizowane, audytowalne i dobierane do zapotrzebowania. System ma preferować darmowe przydziały, tanie modele z internetu, lokalne/self-hostowane modele na odzyskanym sprzęcie oraz energię OZE. Celem jest przetwarzanie dostępnych materiałów i elektrośmieci na produkty potrzebne inicjatywie i ludziom, ale w sposób jawny, sterowalny przez ludzi i reviewowalny.

## Co zrobiono

### T11 — DONE: PotentialDossier -> ExecutionPackSkill links

Dodano jawne powiązanie produktów z `potential_pipeline/seed_dossiers.json` do istniejących skilli w `execution_skills/seed_skills.json`:

- `phone-aquaponics-observer` -> `aquaponics_observer`,
- `recycled-sensor-gateway` -> `edge_onboarding`,
- `recycle-bench-catalog-station` -> `edge_onboarding`.

Dodano `potential_pipeline/validate_skill_links.py`, który wymaga, aby każdy produkt miał dokładnie jedno z pól:

- `execution_skill_id`, albo
- `missing_skill_to_create`.

Skrypt blokuje produkt bez ogniwa wykonawczego lub z linkiem do nieistniejącego skilla.

### T14 — DONE: Model/resource selector cell

Dodano pierwszą komórkę doboru modeli/zasobów: `model_resource_selector/`.

Komórka koduje regułę, że nie trzeba domyślnie kupować drogich modeli:

- publiczne, niskiego ryzyka zadania -> `free_public_small_model`,
- prywatne zadania -> `selfhost_recovered_low_power_node`,
- ciężkie zadania lokalne/GPU -> `selfhost_gpu_high_cost_node`, ale tylko z `energy_justification`.

Dodane pliki:

- `model_resource_selector/README.md`,
- `model_resource_selector/profiles.json`,
- `model_resource_selector/select_model.py`,
- `tests/test_model_resource_selector.py`.

### Testy regresyjne

Dodano:

- `tests/test_potential_skill_links.py`,
- `tests/test_model_resource_selector.py`.

Testy potwierdzają, że:

- produkty z dossier nie mogą wisieć bez ogniwa wykonawczego,
- prywatne zadanie nie może zostać przepchnięte do publicznego modelu przez prosty przełącznik zgody,
- drogi runtime GPU wymaga uzasadnienia energetycznego,
- tanie/publiczne zadania używają darmowego profilu.

## Testy wykonane

```bash
python3 -m unittest tests.test_potential_skill_links tests.test_model_resource_selector tests.test_edge_flasher tests.test_potential_pipeline
python3 -m unittest discover -s tests -p 'test_*.py'
```

## Następne zadania

### T12 — PRIORYTET 1: Resource scout input format

Dodać `resource_scout/` z formatem wejścia dla zasobów wykrywanych przez ludzi i agentów:

- link/źródło,
- lokalizacja,
- koszt,
- klasa zasobu,
- możliwe produkty,
- ryzyka,
- wymagane zdjęcia/pomiary,
- energia/logistyka wymagane do aktywacji,
- informacja, czy zasób nadaje się do darmowej/OZE aktywacji.

Acceptance criteria:

- JSON schema lub walidator Python.
- Minimum 2 przykłady: elektrośmieć oraz darmowy/self-host compute node.
- Test, że brak kosztu, lokalizacji lub ryzyk blokuje rekord.

### T13 — PRIORYTET 2: Pierwszy food-loop execution pack

Dodać draft execution pack dla `phone-aquaponics-observer`.

Zakres dozwolony:

- obserwacja,
- raport,
- checklist operatora,
- brak sterowania pompami, karmieniem, dozowaniem, grzaniem albo zaworami.

Acceptance criteria:

- Pack ma `manifest.json`, `RUNBOOK.md`, `REVIEW_CHECKLIST.md`.
- Pack jawnie wskazuje artefakty z `edge_flasher` jako wejście.
- Test/reguła tekstowa wykrywa zakazane akcje w sekcjach wykonawczych.

### T15 — PRIORYTET 3: Agentic cell manifest standard

Uogólnić wspólny standard dla małych ogniw automatyzacji.

Proponowane pola:

- `cell_id`,
- `purpose`,
- `allowed_modes`,
- `input_contract`,
- `output_artifacts`,
- `model_resource_policy`,
- `energy_policy`,
- `human_control_points`,
- `audit_trail`,
- `rollback_plan`,
- `review_gates`.

Acceptance criteria:

- Jeden schemat lub walidator.
- `edge_flasher`, `potential_pipeline` i `model_resource_selector` mogą być opisane jako komórki.
- Test blokuje komórkę bez human control points albo audit trail.

### T16 — PRIORYTET 4: Human needs intake -> recommendations

Dodać mały format zgłoszenia potrzeb ludzi/inicjatywy:

- kto zgłasza i publiczny zakres widoczności,
- potrzeba/problem,
- lokalizacja lub obszar,
- ograniczenia kosztu/energii,
- czy zgłaszający wybiera z rekomendacji czy wnosi własny opis,
- oczekiwany rezultat.

Acceptance criteria:

- Walidator blokuje prywatne dane bez jawnego zakresu widoczności.
- Rekomendacja nie wybiera wykonania fizycznego bez human approval.
- Format da się połączyć z `PotentialDossier` i `model_resource_selector`.

## Ryzyka i zasady dla następnego agenta

- Nie budować monolitu. Każde ogniwo ma być małe, tanie, testowalne i wymienialne.
- Preferować darmowe przydziały, odzyskany sprzęt, OZE i self-host tylko wtedy, gdy ma to sens energetyczny.
- Ludzie dostarczają potrzeby jawnie lub wybierają z rekomendacji; automatyzacja nie może ukrycie zmieniać priorytetów społecznych.
- Autonomia ma być audytowalna: input -> model/resource choice -> artifact -> review -> approval/rollback.
