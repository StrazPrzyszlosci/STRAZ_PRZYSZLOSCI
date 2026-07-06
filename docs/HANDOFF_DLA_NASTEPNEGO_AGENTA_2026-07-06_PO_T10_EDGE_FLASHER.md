# Handoff dla Następnego Agenta - po T10 (Edge Flasher Wizard Scaffold) - 2026-07-06

## Kontekst

Przeczytano ostatnie commity (`f11f96b`, `d4e8751`, `4158af6`, `0a1685a`, `9116c41`) oraz handoff `docs/HANDOFF_DLA_NASTEPNEGO_AGENTA_2026-07-06_PO_T9_POTENTIAL_PIPELINE.md`.

Użytkownik doprecyzował wizję: **Straż Przyszłości** ma być samoudoskonalającym się organizmem złożonym z audytowalnych komórek automatyzacji. Komórki mają analizować dostępne zasoby: energię elektryczną, darmowe modele AI, self-hostowane modele AI dobierane do zapotrzebowania, elektrośmieci, części, logistykę, dane i procesy instalacji/aktualizacji oprogramowania. Każda automatyzacja ma pozostawiać ślad review, artefakty i jawne bramki bezpieczeństwa.

## Co zrobiono

### T10 — DONE: Edge flasher wizard scaffold

Dodano `edge_flasher/` jako scaffold suggest-only dla pierwszych komórek edge wynikających z `potential_pipeline`.

Nowe pliki:

- `edge_flasher/README.md` — opis celu, profili i komendy generowania artefaktów.
- `edge_flasher/profiles.json` — trzy profile:
  - `phone-aquaponics-observer`,
  - `recycle-bench-catalog-station`,
  - `phone-sensor-gateway`.
- `edge_flasher/generate_artifacts.py` — deterministyczny generator artefaktów:
  - `device_profile.json`,
  - `install_receipt.json`,
  - `bench_test_report.md`,
  - `rollback.md`.
- `tests/test_edge_flasher.py` — testy profili i generatora.

### Zasady bezpieczeństwa zakodowane w scaffoldzie

- Generator nie flashuje firmware, nie steruje hardware, nie otwiera portów i nie wykonuje instalacji.
- Każdy profil ma jawne `allowed_actions`, `blocked_high_risk_actions` i `required_human_approval_before`.
- Wygenerowany `install_receipt.json` zawsze startuje jako:
  - `install_status: NOT_INSTALLED`,
  - `approval_status: MISSING_HUMAN_APPROVAL`.
- Raport bench startuje jako `BLOCKED_PENDING_REAL_BENCH_AND_HUMAN_APPROVAL`.

## Testy wykonane

```bash
python3 -m unittest tests.test_edge_flasher tests.test_potential_pipeline
python3 -m unittest discover -s tests -p 'test_*.py'
```

## Następne zadania

### T11 — PRIORYTET 1: Powiązać PotentialDossier z ExecutionPackSkill

Dodać walidator, który sprawdza, że każdy produkt w `potential_pipeline/seed_dossiers.json` wskazuje istniejący skill z `execution_skills/seed_skills.json` albo jawnie wskazuje `missing_skill_to_create`.

Acceptance criteria:

- `PotentialDossier.intended_products[]` ma pole `execution_skill_id` lub `missing_skill_to_create`.
- Test wykrywa produkt bez powiązania ze skillem.
- Test przechodzi dla obecnych seedów.

### T12 — PRIORYTET 2: Resource scout input format

Dodać `resource_scout/` z prostym formatem wejścia dla wykrywanych zasobów:

- link/źródło,
- lokalizacja,
- koszt,
- klasa zasobu,
- możliwe produkty,
- ryzyka,
- wymagane zdjęcia/pomiary,
- energia/logistyka wymagane do aktywacji.

Acceptance criteria:

- JSON schema lub walidator Python.
- Minimum 2 przykłady: elektrośmieć i darmowa moc obliczeniowa / lokalny host.
- Test, że brak kosztu, lokalizacji lub ryzyk blokuje rekord.

### T13 — PRIORYTET 3: Pierwszy food-loop execution pack

Dodać draft execution pack dla `phone-aquaponics-observer`.

Zakres dozwolony:

- obserwacja,
- raport,
- ręczny checklist operatora,
- brak sterowania pompami, karmieniem, dozowaniem, grzaniem albo zaworami.

Acceptance criteria:

- Pack ma `manifest.json`, `RUNBOOK.md`, `REVIEW_CHECKLIST.md`.
- Pack jawnie wskazuje artefakty z `edge_flasher` jako wejście.
- Test/reguła tekstowa wykrywa zakazane słowa akcji typu `control_pump`, `dose_nutrients`, `control_heater`, `feed_fish` w sekcjach wykonawczych.

### T14 — PRIORYTET 4: Model/resource selector cell

Dodać pierwszą komórkę planowania doboru modeli AI:

- darmowe API/model,
- lokalny self-host model,
- koszt energii,
- wymagana prywatność danych,
- minimalna jakość wyniku,
- fallback offline.

Acceptance criteria:

- Format `model_resource_profile` lub analogiczny.
- Test, że zadania prywatne nie wybierają publicznego modelu bez jawnej zgody.
- Test, że high-cost GPU/local runtime wymaga uzasadnienia energetycznego.

## Ryzyka i zasady dla następnego agenta

- Nie zamieniać scaffoldów w automatyczne wdrożenia fizyczne.
- Nie wpisywać fałszywych zielonych statusów dla hardware bez realnego bench-testu.
- Samoudoskonalanie repo ma działać przez PR, testy, handoff i approval, a nie przez cichy self-modifying runtime.
- Każda nowa komórka automatyzacji powinna mieć własne wejścia, wyjścia, review gates, rollback i test minimalny.
