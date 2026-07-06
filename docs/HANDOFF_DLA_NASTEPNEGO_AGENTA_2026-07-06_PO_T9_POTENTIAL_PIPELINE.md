# Handoff dla Następnego Agenta - po T9 (Potential Pipeline) - 2026-07-06

## Kontekst

Użytkownik doprecyzował, że automatyzacja ma wykorzystywać potencjał: elektrośmieci są darmowe i mają olbrzymi potencjał, a repo ma budować automatyzacje do ich przetwarzania na potrzeby Straży Przyszłości, np. urządzenia do hodowli żywności. Kluczowa pętla: **analiza potencjału -> zamysł -> projekt -> wykonanie -> optymalizacja**.

## Co zrobiono

### T9A — DONE: Potential Pipeline jako konkretna struktura danych

Dodano `potential_pipeline/`:

- `README.md` — opis pętli potencjał -> zamysł -> projekt -> wykonanie -> optymalizacja,
- `potential_schema.json` — kontrakt `PotentialDossier`,
- `seed_dossiers.json` — pierwszy dossier `ewaste_to_food_edge_devices`, który mapuje darmowe elektrośmieci na produkty dla food/hardware reuse:
  - `phone-aquaponics-observer`,
  - `recycled-sensor-gateway`,
  - `recycle-bench-catalog-station`.

### T9B — DONE: deterministyczny generator planu

Dodano `potential_pipeline/generate_execution_plan.py`.

Skrypt:

- waliduje kolejność etapów: `analiza_potencjalu`, `zamysl`, `projekt`, `wykonanie`, `optymalizacja`,
- wymaga, aby seed dotyczył darmowego/taniego potencjału,
- pilnuje, żeby produkty edge/fizyczne wymagały approval,
- generuje Markdown planu bez deploymentu i bez kontroli hardware.

### T9C — DONE: testy pętli potencjału

Dodano `tests/test_potential_pipeline.py`, który sprawdza:

- pełną kolejność pętli,
- powiązanie elektrośmieci z żywnością, odpadami i hardware reuse,
- approval dla produktów fizycznych,
- działanie `--validate-only`,
- deterministyczny output planu.

### T9D — DONE: uzupełnienie interpretacji celu repo

Rozszerzono `docs/INTERPRETACJA_DOCELOWEJ_AUTOMATYZACJI_REPO.md` o najkrótszy wzorzec wykonawczy: potencjał -> zamysł -> projekt -> wykonanie -> optymalizacja.

## Testy wykonane

```bash
python3 -m unittest tests.test_potential_pipeline
python3 -m unittest discover -s tests -p 'test_*.py'
```

## Następne zadania

### T10 — PRIORYTET 1: Edge flasher wizard scaffold

Na bazie `potential_pipeline` zbudować pierwszy scaffold `edge_flasher/`:

- profile: `phone-aquaponics-observer`, `recycle-bench-catalog-station`, `phone-sensor-gateway`,
- generator artefaktów: `device_profile.json`, `install_receipt.json`, `bench_test_report.md`, `rollback.md`,
- test, że high-risk actions są zablokowane do human approval.

### T11 — PRIORYTET 2: Powiązać PotentialDossier z ExecutionPackSkill

Dodać walidator, który sprawdza, że każdy produkt w `PotentialDossier` wskazuje skill z `execution_skills/seed_skills.json` albo jawnie mówi, jaki skill trzeba utworzyć.

### T12 — PRIORYTET 3: Resource scout input format

Dodać prosty format wejścia dla scoutingu zasobów:

- link/źródło,
- lokalizacja,
- koszt,
- klasa zasobu,
- możliwe produkty,
- ryzyka,
- wymagane zdjęcia/pomiary.

### T13 — PRIORYTET 4: Pierwszy food-loop execution pack

Dodać draft execution pack dla `phone-aquaponics-observer`: tylko obserwacja i raport, bez sterowania pompami, karmieniem, dozowaniem lub grzaniem.

## Ryzyka

- Nie mylić „duży potencjał” z pozwoleniem na deployment fizyczny.
- Nie promować planów bez bench-testu i human approval.
- Utrzymywać pętlę optymalizacji jako PR/propozycję, nie samoczynny self-modifying runtime.
