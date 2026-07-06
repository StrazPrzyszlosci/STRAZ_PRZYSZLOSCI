# Handoff dla Następnego Agenta - po T8 (interpretacja celu + ExecutionPackSkill registry) - 2026-07-06

## Kontekst

Wejściem był feedback po poprzednim PR: potrzeba jaśniejszego omówienia pełnej wizji docelowej automatyzacji repo oraz kontynuacji kolejnych zadań.

Poprzedni handoff: `docs/HANDOFF_DLA_NASTEPNEGO_AGENTA_2026-07-06_PO_T7_HERMES_I_REGRESJE.md`.

## Moja interpretacja celu repo

Repo nie jest jedną aplikacją. To ma być system operacyjny organizacji, który produkuje audytowalne łańcuchy pracy:

```text
sygnał -> dossier -> execution pack -> skrypt/agent -> artefakt -> verifier -> curator -> reviewer -> approval -> deployment -> telemetry -> poprawa procesu
```

Pełny cel to połączenie odzysku odpadów, produkcji żywności, reuse smartfonów i low-power hardware, komunikacji mesh oraz agentowego nadzoru w jeden powtarzalny model. AI ma pracować szybko, ale w trybie kontrolowanym: dla fizycznych działań domyślnie `observe -> explain -> suggest -> wait for human approval`.

Szczegółowy opis dodano w `docs/INTERPRETACJA_DOCELOWEJ_AUTOMATYZACJI_REPO.md`.

## Co zrobiono

### T8A — DONE: Interpretacja docelowej automatyzacji

Dodano `docs/INTERPRETACJA_DOCELOWEJ_AUTOMATYZACJI_REPO.md` z opisem:

- repo jako systemu operacyjnego organizacji,
- pięciu „fabryk”: wiedzy, skryptów, odzysku sprzętu, biologiczno-żywnościowej i samodoskonalenia,
- warstw automatyzacji od sygnału do optymalizatora,
- łańcuchów dla śmieci, żywności i smartfonów-edge,
- granicy bezpieczeństwa dla działań fizycznych.

### T8B — DONE: ExecutionPackSkill registry seed

Dodano `execution_skills/`:

- `README.md` — zasady skill registry,
- `schema.json` — kontrakt `ExecutionPackSkill`,
- `seed_skills.json` — pierwsze skille:
  - `repo_scout`,
  - `edge_onboarding`,
  - `aquaponics_observer`,
  - `handoff_builder`.

Dodano test `tests/test_execution_skills.py`, który pilnuje:

- unikalnych ID,
- obecności audit contract,
- braku trybu `production` dla skillów food/water/hardware reuse,
- bramek blokujących high-risk actuation,
- zabezpieczenia przed fałszywym zielonym statusem w handoffach.

## Testy wykonane

```bash
python3 -m unittest tests.test_execution_skills
python3 -m unittest discover -s tests -p 'test_*.py'
```

## Następne zadania

### T9 — PRIORYTET 1: Edge flasher wizard scaffold

Zbudować minimalny scaffold lokalnego wizardu dla smartfonów i low-power node:

- katalog np. `edge_flasher/`,
- profile JSON: `phone-sensor-gateway`, `phone-aquaponics-observer`, `phone-recycle-bench`, `phone-mesh-console`,
- generator artefaktów: `device_profile.json`, `install_receipt.json`, `bench_test_report.md`, `rollback.md`,
- test, że profile high-risk nie mają automatycznego sterowania bez review gate.

### T10 — PRIORYTET 2: Realny upstream ingestion path dla B1

Dodać CI/offline job albo endpoint/queue dla JSONL z `pipelines/import_cern_kicad_library.py`. Import ma kończyć w staging + audit event, bez promocji do katalogu.

### T11 — PRIORYTET 3: Skill registry integration z execution packami

Powiązać `execution_skills/seed_skills.json` z istniejącymi execution packami i handoffami:

- dodać pole `skill_id` w nowych packach,
- stworzyć walidator, że pack wskazuje istniejący skill,
- dodać pierwszy pack `edge_onboarding` jako draft.

### T12 — PRIORYTET 4: Hermes-style RepoScout

Użyć registry zewnętrznych repo jako wejścia i wygenerować automatyczny raport różnic/inspiracji, ale tylko w trybie read-only/suggest-only.

## Ryzyka

- Nie przechodzić do sterowania fizycznego przed T9 safety gates.
- Nie traktować `hermes-agent` jako dependency runtime bez security/licence review.
- Nie oznaczać governance `BLOCKED` jako awarii, jeśli blokada wynika z braku human approval.
