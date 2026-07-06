# Handoff dla Następnego Agenta - po T12/T13 (Resource Scout + Food-loop Pack) - 2026-07-06

## Kontekst

Kontynuacja po T11/T14. Użytkownik oczekuje kolejnych małych, wyspecjalizowanych ogniw automatyzacji agentycznej: zasób -> ocena -> dobór taniego/self-host modelu -> artefakt -> review -> decyzja człowieka. Ta iteracja domyka dwa brakujące ogniwa: wejście zasobów z terenu oraz pierwszy food-loop execution pack dla odzyskanego telefonu.

## Co zrobiono

### T12 — DONE: Resource scout input format

Dodano `resource_scout/` jako komórkę normalizacji sygnałów o darmowych lub tanich zasobach.

Nowe pliki:

- `resource_scout/README.md`,
- `resource_scout/validate_records.py`,
- `resource_scout/examples/ewaste_phone_batch.json`,
- `resource_scout/examples/selfhost_compute_node.json`,
- `tests/test_resource_scout.py`.

Walidator wymaga m.in.:

- źródła/provenance,
- lokalizacji,
- kosztu (`amount_pln`, gdzie `0` oznacza darmowe),
- klasy zasobu,
- możliwych produktów,
- ryzyk,
- wymaganych zdjęć/pomiarów,
- wymagań aktywacyjnych: energia + logistyka.

Przykłady obejmują:

- paczkę starych smartfonów jako potencjał dla `phone-aquaponics-observer` i `phone-sensor-gateway`,
- odzyskany/self-host compute node jako potencjał dla taniego lokalnego przetwarzania.

### T13 — DONE: Pierwszy food-loop execution pack

Dodano draft execution pack:

`PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-phone-aquaponics-observer-01/`

Pliki:

- `manifest.json`,
- `RUNBOOK.md`,
- `REVIEW_CHECKLIST.md`.

Zakres packa:

- tylko obserwacja,
- raport,
- pytania do operatora,
- receipt uruchomienia,
- brak fizycznego sterowania,
- brak decyzji biologicznych bez człowieka.

Pack jawnie używa artefaktów z `edge_flasher` jako wejścia:

- `edge_flasher device_profile.json`,
- `edge_flasher install_receipt.json`.

## Testy wykonane

```bash
python3 -m unittest tests.test_resource_scout tests.test_phone_aquaponics_observer_pack
python3 -m unittest discover -s tests -p 'test_*.py'
```

## Następne zadania

### T15 — PRIORYTET 1: Agentic cell manifest standard

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
- `edge_flasher`, `resource_scout`, `model_resource_selector`, `potential_pipeline` i `pack-phone-aquaponics-observer-01` dają się opisać jako komórki.
- Test blokuje komórkę bez `human_control_points` albo `audit_trail`.

### T16 — PRIORYTET 2: Human needs intake -> recommendations

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
- Format da się połączyć z `PotentialDossier`, `resource_scout` i `model_resource_selector`.

### T17 — PRIORYTET 3: Cell chain planner

Dodać deterministyczny planner, który z listy potrzeb i zasobów układa bezpieczny łańcuch małych ogniw, np.:

`human_need -> resource_scout -> potential_pipeline -> model_resource_selector -> edge_flasher -> food-loop pack -> handoff_builder`

Acceptance criteria:

- Planner generuje tylko plan/handoff, nie uruchamia fizycznego wykonania.
- Plan zawiera human approval checkpoints.
- Test sprawdza, że chain zawiera audit artifacts i rollback points.

### T18 — PRIORYTET 4: Energy/OZE activation ledger

Dodać lekki ledger decyzji energetycznych dla self-host i odzyskanego hardware.

Acceptance criteria:

- Rekord zawiera źródło energii, szacowany koszt, okno czasowe, ryzyko i uzasadnienie.
- High-cost runtime nie przechodzi bez wpisu ledger.
- Model/resource selector może wskazać wymagany ledger entry.

## Ryzyka i zasady dla następnego agenta

- Nie przechodzić do automatycznego wykonania fizycznego; to nadal planowanie, obserwacja i raportowanie.
- Nie robić monolitu. Łańcuch ma składać się z małych ogniw z własnymi input/output/test/review.
- Każde ogniwo musi mieć audit trail i punkt sterowania przez człowieka.
- Darmowa energia/OZE i odzyskany sprzęt są przewagą, ale muszą być jawnie opisane w ledgerach i receiptach.
