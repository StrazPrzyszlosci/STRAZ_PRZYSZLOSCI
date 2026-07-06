# Handoff dla Następnego Agenta - po T15 (Agentic cell manifest standard) - 2026-07-06

## Kontekst wejściowy

Przeczytano ostatni handoff w tej samej fali: `docs/HANDOFF_DLA_NASTEPNEGO_AGENTA_2026-07-06_PO_T11_T14_AGENTIC_CELLS.md` (T11/T14 DONE) oraz `docs/HANDOFF_DLA_NASTEPNEGO_AGENTA_2026-07-06_PO_HERMES_PILOT.md` (status Hermes pilota).

Ostatnie commity przed pracą:

- `7ac78cb` Merge PR #15 (Hermes proot installer),
- `dda6eab` `feat(hermes): add termux proot installer`,
- `f11f96b` Merge PR #14 (potential: ewaste to food loop),
- `d4e8751` `feat(potential): model ewaste to food automation loop`,
- `4158af6` Merge PR #13 (provider lifecycle).

Priorytet wejściowy T15: uogólnić wspólny standard manifestu dla komórek agentic, opisujący istniejące moduły (`edge_flasher`, `resource_scout`, `model_resource_selector`, `potential_pipeline`, `pack-phone-aquaponics-observer-01`) jako komórki, bez zastępowania ich implementacji. Kryteria akceptacji z `PO_T11_T14_AGENTIC_CELLS`:

- jeden schemat lub walidator,
- wymienione moduły dają się opisać jako komórki,
- test blokuje komórkę bez human control points albo audit trail.

Uwaga: wystąpił rozjazd numeracji w poprzedniej fali (`T8` raz jako ingestion path, raz jako skill registry). Ten handoff NIE relokuje numerów T1–T14 i przywraca liniowy pipeline T15+, zgodnie z dotychczasową serialną konwencją handoffów (jeden handoff = jedno zadanie).

## Co zrobiono

### T15 — DONE: Agentic cell manifest standard

Dodano warstwę opisu komórek obok ich istniejących implementacji. Manifesty NIE zastępują implementacji modułów (`edge_flasher/`, `resource_scout/`, `model_resource_selector/`, `potential_pipeline/`, `.../pack-phone-aquaponics-observer-01/`) — tylko je opisują wspólnym kontraktem.

Nowe pliki:

1. `agentic_cells/cell_manifest_schema.json` — JSON Schema (draft 2020-12) kontraktu `AgenticCellManifest`. Wymagane: `cell_id`, `version`, `status`, `purpose`, `allowed_modes`, `input_contract`, `output_artifacts`, `model_resource_policy`, `energy_policy`, `human_control_points`, `audit_trail`, `rollback_plan`, `review_gates`. Opcjonalne: `safety_notes`, `implementation_ref`.
2. `agentic_cells/validate_cell_manifest.py` — walidator Python bez zewnętrznych zależności (spójny ze stylem `potential_pipeline/validate_skill_links.py`, `resource_scout/validate_records.py`). Sprawdza:
   - wymagane pola i typy,
   - `cell_id` wg `^[a-z0-9][a-z0-9_-]{2,80}$`, `version` wg `^v[0-9]+$`,
   - `allowed_modes`, `status`, `input_contract.kind`, `energy_policy.default_class` z listy enum,
   - `audit_trail` z czterema flagami bool,
   - `human_control_points` non-empty z `point`/`reviewer_role`/`blocks`,
   - `review_gates` non-empty z `gate`/`reviewer_role`/`blocks`,
   - `rollback_plan.strategy` ≥5 znaków i `rollback_artifact`,
   - `model_resource_policy.may_use_private_data_on_public_model` musi być `false` (seed nie może domyślnie wysyłać danych prywatnych do publicznego modelu),
   - tryby high-risk (`hardware-lab`, `production`) wymagają `human_control_points` lub `review_gates` odwołujących się do `actuation`/`physical`/`production`,
   - tryb `production` wymaga explicit gate reference do `production`,
   - unikalność `cell_id`.
3. `agentic_cells/seed_cell_manifests.json` — 5 manifestów opisujących istniejące komórki:
   - `edge_flasher` → `edge_flasher/`,
   - `resource_scout` → `resource_scout/`,
   - `model_resource_selector` → `model_resource_selector/`,
   - `potential_pipeline` → `potential_pipeline/`,
   - `aquaponics_observer_pack` → `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-phone-aquaponics-observer-01/` (`pack_id` powiązany z manifestem packa T13).
   Każdy manifest ma `implementation_ref.{directory,entry_artifact}` wskazujący na realną implementację.
4. `tests/test_cell_manifest.py` — 15 testów:
   - seed opisuje wszystkie 5 oczekiwanych komórek,
   - unikalne `cell_id`,
   - walidator akceptuje seed,
   - wymagane pola obecne w każdej komórce,
   - `audit_trail` wszystkie flagi `True`,
   - każda komórka blokuje private data na public model,
   - komórki high-risk mają gate actuation,
   - blokada: brak `human_control_points`,
   - blokada: brak pełnego `audit_trail`,
   - blokada: `production` bez explicit gate `production`,
   - blokada: `may_use_private_data_on_public_model=True`,
   - blokada: duplikat `cell_id`,
   - blokada: `rollback_plan.strategy` zbyt krótkie,
   - blokada: nieznany `input_contract.kind`,
   - każda komórka ma `implementation_ref.directory` i `entry_artifact`.

### Zgodność z konwencją

- NUMERACJA: T15 jest monotonicznie rosnący, NIE relokuję T8–T14 ani T1–T7. Skoro w `PO_T11_T14_AGENTIC_CELLS` pojawiło się już T15 (Agentic cell manifest) jako PRIORYTET 1, przejęto to znaczenie; kolejne zadanie to T16 (wg tamtego handoffu = Human needs intake).
- STRUKTURA: jeden handoff = jedno zadanie (T15), sekcje zgodne z T1–T7 (Kontekst wejściowy / Co zrobiono / Testy wykonane / Następne zadania / Status backlogu / Ryzyka).
- NIE wprowadzono nowych równoległych serii H* jako odrębnych; H2/H3/H4 z HERMES_PILOT wchodzą jako OPEN w backlogu i mogą być podjęte jako T17+ po T16.
- `staging-write` w `allowed_modes` NIE jest traktowane jako high-risk wymagające blokady actuation (to tryb zapisu draftów/D1), co poprawia semantykę `HIGH_RISK_MODES`. To wyłącznie zawężenie trybów fizycznie ryzykownych do `hardware-lab` i `production`.

## Testy wykonane

```bash
# Walidator manualnie
python3 agentic_cells/validate_cell_manifest.py
# OK: 5 agentic cell manifest(s) valid

# Testy jednostkowe T15
python3 -m unittest tests.test_cell_manifest -v
# Ran 15 tests in 0.003s — OK

# Pełna sciezka Python (regresja całości repo)
python3 -m unittest discover -s tests -p 'test_*.py'
# Ran 237 tests in 14.086s — OK

# Testy mjs (regresja Cloudflare Worker)
for f in tests/*.mjs; do node --test "$f" >/dev/null 2>&1; done
# 276 testów PASS, 0 FAIL
```

Status: PASS (15/15 nowy suite, 237/237 python, 276/276 mjs).

## Następne zadania

### T16 — PRIORYTET 1: Human needs intake -> recommendations

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
- Nowy manifest komórki (np. `needs_intake`) dodany do `agentic_cells/seed_cell_manifests.json` z `implementation_ref` wskazującym nowy katalog.
- Testy utrzymują 0 regresji w `python3 -m unittest discover -s tests -p 'test_*.py'` i `tests/*.mjs`.

Acceptance uzupełnione o ścieżkę komórkową (po T15 każda nowa komórka powinna mieć manifest w `agentic_cells/`).

### T17 — PRIORYTET 2 (po T16): Provider quota monitor cell (dawniej H2)

Provider quota monitor z `quota_snapshot.json`, blokujący agent chain bez snapshotu. Po zrobieniu, dodać manifest komórki `provider_quota_monitor` do `agentic_cells/seed_cell_manifests.json`. Acceptance jak w `PO_HERMES_PILOT` H2.

### T18 — PRIORYTET 3 (po T17): Hermes first work queue (dawniej H3)

Pierwsza kolejka prac Hermesa. Dodać manifest komórki `hermes_work_queue` do `agentic_cells/seed_cell_manifests.json`.

## Status backlogu

| Zadanie | Status | Opis |
|---|---|---|
| T1 / B4 | DONE | Dashboard metryk D1, `/metrics` Discord/Telegram, read-only. |
| T2 / B1 | DONE | Scheduled KiCad importer (staging + dedup + ingest events + cron). |
| T3 / B2 | DONE | KiCad verifier (schema-diff + dedup + OCR deferred + verify events). |
| T4 / B3 | DONE | KiCad curator (suggest-only + normalizacja + Z90 ledger). |
| T5 / B5 | DONE | Execution pack initiator (CANARY branch/PR + reviewer gate + D1 status + commands). |
| T6 | DONE | Provider lifecycle auto-deactivate >72h. |
| T7 | DONE | Naprawa regresji Telegram/Python + Hermes jako inspiracja referencyjna. |
| T8 | DONE | Interpretacja docelowej automatyzacji + ExecutionPackSkill registry seed (`execution_skills/`). |
| T9 | DONE | Potential Pipeline (`potential_pipeline/`: schema, generator, seed dossiers). |
| T10 | DONE | Edge flasher wizard scaffold (`edge_flasher/`). |
| T11 | DONE | PotentialDossier → ExecutionPackSkill links (`validate_skill_links.py`). |
| T12 | DONE | Resource scout input format (`resource_scout/`). |
| T13 | DONE | Pierwszy food-loop execution pack `pack-phone-aquaponics-observer-01`. |
| T14 | DONE | Model/resource selector cell (`model_resource_selector/`). |
| T15 | DONE (ta tura) | Agentic cell manifest standard (`agentic_cells/`). |
| T16 | NEXT / P1 | Human needs intake → recommendations. |
| T17 | OPEN / P2 | Provider quota monitor cell (dawniej H2). |
| T18 | OPEN / P3 | Hermes first work queue (dawniej H3). |
| H4 | OPEN / P4 | Human approval UI/command stub (może być włączone do T16+). |
| B1 ingestion path | OPEN (operator/CI) | Realny upstream JSONL ingestion path zamiast env-payload — operator/CI. |
| B5 follow-up GitHub App | OPEN (operator/CI) | Offline/CI branch flow, webhooki `started/closed/merged`, rollback test — operator. |
| WebSocket events stream | OPEN (H3 roadmap) | `/v1/ws/events` dla edge — po stabilizacji H2. |
| S1 (realny checkout CERN) | ODOCZONE (operator) | Operator/sprzęt. |
| S6 (testy hardware) | ODOCZONE (tester) | Tester/sprzęt. |
| T8/T9 operator (proot/BLE) | ODOCZONE (operator/tester) | Sprzęt fizyczny. |

## Ryzyka

- Manifesty komórek muszą być utrzymywane równolegle z realną implementacją. Jeśli ktoś zmieni moduł `edge_flasher/` bez aktualizacji `agentic_cells/seed_cell_manifests.json`, manifest zrobi się niespójny — kolejny agent powinien to sprawdzać (proponowany test porównujący `directory` z realnym katalogiem).
- `staging-write` NIE jest high-risk loss of physical actuation, ale NADAL wymaga `human_control_points` (ogólne kryterium non-empty). To zawężenie nie osłabia audytowalności.
- Każda nowa komórka (T16+, T17+) powinna mieć swój manifest w `agentic_cells/seed_cell_manifests.json`, inaczej zostanie poza standardem.
- Walidator NIE używa biblioteki `jsonschema` (brak GIL/externals w dotychczasowym pipeline) — schemat JSON Schema jest normatywnym odniesieniem, walidator reimplementuje krytyczne reguły recznie. Rozbieżność między schematem a walidatorem jest możliwa; kolejne zadanie może dodać opcjonalny strict-mode z `jsonschema` jeśli pojawi się w CI.

## Zasady dla następnego agenta (obowiązkowe)

Następny agent MUSI trzymać się dotychczasowej konwencji nazewnictwa i pipeline'u. Łamanie tych punktów psuje spójność repo i będzie odrzucane w review:

1. **Nazewnictwo handoffów**: jeden plik na zadanie, nazwa `docs/HANDOFF_DLA_NASTEPNEGO_AGENTA_<DATA>_PO_T<n>_<KRÓTKI_OPIS>.md` (dla zadań powiązanych z blokiem B1/B2/B3/B4/B5 dodawać suffix `_Bx_<NAZWA>`).
2. **Pipeline liniowy**: zadania numerujemy monotonicznie rosnąco (`T<n+1>`) — NIE relokować istniejących numerów T1..T15, NIE dublować znaczeń (zakazany przypadek: T8 jako ingestion path i jednocześnie jako skill registry).
3. **Jeden handoff = jedno zadanie**. NIE pisać wielu równoległych handoffów w jednej turze. W jednej turze robimy dokładnie jeden NEXT/PRIORYTET 1; P2/P3 mogą zostać jako OPEN do kolejnej tury.
4. **Struktura pliku**: `# Handoff...`, `## Kontekst wejściowy`, `## Co zrobiono`, `## Testy wykonane`, `## Następne zadania` (JEDNO NEXT, z acceptance criteria), `## Status backlogu` (skopiowany, nie redefiniowany), `## Ryzyka`.
5. **Brak równoległych serii literowych**. Stare serie `H1`/`H2`/`H3`/`H4` z `PO_HERMES_PILOT` są poprzypisywane do głównej numeracji (`T17` = był H2, `T18` = był H3); `H4` planowane do wbudowania w T16+. NIE tworzyć nowych serii literowych jako odrębnych ścieżek.
6. **Każda nowa komórka agentic** (T16+) MUSI dostać swój manifest w `agentic_cells/seed_cell_manifests.json` z `implementation_ref` wskazującym realną implementację (katalog + entry artifact). Brak manifestu = komórka poza standardem.
7. **Status backlog kopiujemy, nie piszemy na nowo**: kopiujemy tabelę DONE/OPEN z ostatniego handoffu w tej samej fali, tylko uzupełniając o nowo wykonane zadanie.
8. **Testy obowiązkowe**: po zrealizowaniu zadania uruchomić `python3 -m unittest discover -s tests -p 'test_*.py'` oraz `tests/*.mjs` i upisać wynik w `## Testy wykonane` (PASS/FAIL z liczbami). Czerwony suite Python = blokada zakończenia tury.
9. **Nie psuj audytowalności**: każda komórka high-risk (`hardware-lab`, `production`) musi mieć `human_control_points` lub `review_gates` odwołujące się do `actuation`/`physical`/`production`. `production` wymaga explicit gate `production`.
10. **Nie commitować sekretów ani przekraczać zasięgów** — blokady z T2–T6 (`physical_actuation`, `auto_merge`, `direct_push_main`, `secret_printing`, `unbounded_spend`) pozostają w mocy; nie omijać ich w nowych komórkach.

Historia rozjazdu numeracji (T8 dublowany jako ingestion path i skill registry w poprzedniej fali równoległych handoffów) jest traktowana jako precedens negatywny — nie powtarzać.
