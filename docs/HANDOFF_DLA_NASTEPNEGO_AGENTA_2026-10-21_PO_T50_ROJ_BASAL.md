# Handoff dla Następnego Agenta — po T50 (rój z rdzeniem decyzyjnym basal) — 2026-10-21

## Kontekst wejściowy

Przeczytano: `AGENTS.md`, claimy (T45–T47 zajęte: kilo-robotyka/kilo-webui;
pozostałe closed), handoffy `PO_T48...`, `PO_T49...`. PR #18 (T48) i #19 (T49)
**zmergowane do main**. Kierunek operatora (2026-10-21, trzy wiadomości):

1. Wszystkie połączone procesy mają działać jak **rój** wykorzystujący zasoby
   oceniane przez **małe modele decyzyjne**; na obwodach roju „ministerownicy";
   **przydział dostępnego sprzętu = decyzja modelu decyzyjnego, LLM robi
   strategię**.
2. **basal to model decyzyjny** (jak jev): mało zasobów, szybki, optymalne
   użycie zasobów przez decyzje o konfiguracji pracy roju wg dostępnych
   zasobów. Repozytorium HYC/basal służy routingowi LLM — ale na potrzeby
   roju **basal ma podejmować bardzo wiele decyzji**.
3. Przykład: rój ma stary telefon i płytkę ESP → basal decyduje, do którego
   z otwartych zadań/zapotrzebowań przydzielić sprzęt; czy uruchomić model
   llm/vision lokalnie; czy użyć algorytmu pisanego pod sprzęt, czy postawić
   w danym miejscu model decyzyjny. Inspiracja strategii zarządzania:
   github.com/open-mercato/cezar (przeczytane; rój ma mieć wiele strategii).
   Rój realizuje usługi dla ludności opisane w repo.

Zewnętrzne repozytoria (HYC/basal, MESHTASTIC ROUTER, cezar) — wyłącznie
ODCZYT; semantyka adaptowana do standardu repo (zero zależności, offline).

Claim: `docs/AGENT_CLAIMS/T50-kilo-swarm-basal.md` (in_progress → done).
Branch: `codex/T50-swarm-basal-kilo` (baza: origin/main 6b23e6f).
Zero zmian w plikach innych claimów; dotknięte wyłącznie selfopt_chain/*.

## Co zrobiono — T50

**`selfopt_chain/swarm.py`** — warstwa roju z rdzeniem decyzyjnym basal:

- **`BasalDecisionCore`** — semantyka decyzji 1:1 jak router.py basala:
  `choice` over options → rozkład prawdopodobieństw (softmax z temperaturami
  per typ pytania i bucket liczby opcji — seedy z CALIBRATION.custom.json),
  `ranking` (kolejność fallback), `confidence`, `confidence_floor` (default
  0.55), `confidence < floor → deferred → final = default`, pełny log
  `decisions.jsonl` (format zgodny z pętlą kalibracji basala; gotowy pod
  GEPA — optimizers.py już istnieje). Rdzeń wbudowany: deterministyczny,
  zero sieci; prawdziwy basal-serve (Ollama) opcjonalnie przez
  `SELFOPT_BASAL_URL` (pole engine: basal-serve|builtin).
- **`SwarmResource`/`resources_from_*`** — jednolity rejestr zasobów roju:
  modele z free_models.json (budżety/headroom) + sprzęt z rekordów
  resource_scout (telefon/ESP-płytka/selfhost/panel/PCB...) + capabilities.
- **`Demand`/`demand_from_need`** — zapotrzebowania misyjne z human_needs
  (deterministyczne reguły capabilities; oze_required → priorytet 2).
- **Strategie zarządzania (inspiracja cezar)**: speed_first, quality_first,
  load_balance, quota_preserve, energy_oze, redundancy (warianty),
  queue_when_busy (kolejka) — basal wybiera strategię cyklu wg sygnałów
  (backlog, quota_pressure, critical_jobs, oze_window).
- **`exec_mode_scores`/decyzja trybu wykonania**: device_profile (algorytm
  pod sprzęt, np. observer pack/edge_flasher) vs on_device_model (mały model
  decyzyjny na węźle) vs cloud_chain (łańcuch LLM w hubie) — dokładnie
  dylemat wskazany przez operatora.
- **Partial matching w `resource_score`**: zasób pokrywający część wymagań
  dostaje niski, ale realny score (0.05×pokrycie) — rój przydziela najlepsze
  pokrycie zamiast odmowy; równowagę rozstrzyga confidence+defer basala.
- **`SwarmPlanner.plan_cycle`** — dwa tory decyzji: (1) przydział sprzętu do
  WSZYSTKICH misji (tanich, bez limitów), (2) ranking zadań procdev do
  wykonania (kosztują limity darmowych tierów) — i tak basal realnie steruje.

**`selfopt_chain/orchestrator.py` (integracja)**: cykl zaczyna się planem
roju — `swarm_plans/cycle_<n>.json` + `cycle_<n>_allocations.md`
(suggest-only, „przydział sprzętu jest PROPOZYCJĄ; aktuation tylko operator"),
selekcja i kolejność zadań procdev wg rankingu basala, `receipt["swarm"]`,
log `decisions.jsonl`. Nowe CLI: `--needs`, `--confidence-floor`,
`--oze-window`.

## Weryfikacja (liczby obowiązkowe)

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
# Ran 425 tests — OK  ✅ (T49: 399 + 26 nowych test_selfopt_swarm.py)
node --test tests/*.mjs
# tests 378, pass 378, fail 0  ✅ (JS nietknięty)
python3 agentic_cells/validate_cell_manifest.py    # OK: 12 manifest(s) valid  ✅
# smoke live (offline, realne dane seed):
#   strategia: speed_first (defer → default), decyzji: 6,
#   need_aquaponics_observer_food -> hardware:phone:ewaste... tryb: device_profile,
#   need_local_edatabase_knowledge -> hardware:selfhost:... tryb: on_device_model,
#   kolejność procdev wg rankingu basala  ✅
```

## Jak to działa (operator)

```bash
python3 selfopt_chain/orchestrator.py --once          # cykl z planem roju (offline)
# nocne okno OZE zmienia strategię na energy_oze:
python3 selfopt_chain/orchestrator.py --once --oze-window
# podpięcie prawdziwego basal-serve (mały model 1.5B przez Ollama):
SELFOPT_BASAL_URL=http://127.0.0.1:8000 python3 selfopt_chain/orchestrator.py ...
```

## Następne zadania (propozycje T51+, ≤5 na turę)

1. **T51 pierwszy realny run free-api** (dawne T50 z listy): operator
   uzupełnia quota_snapshot + sekrety; run `--engine free-api --once`;
   realne confidence decyzji → start własnej kalibracji temperatur
   (decisions.jsonl już zbierane).
2. **T52 pętla kalibracji+GEPA nad decyzjami roju**: decisions.jsonl →
   fit temperatur (wzór basal-calibrate) → lepszy confidence; potem
   GEPA ewoluuje instrukcje/karty strategii (optimizers.py gotowe).
3. **T53 strategia redundancy (warianty cezar)**: krytyczne zapotrzebowania
   wykonywane na 2 zasobach równolegle, porównanie wyników (diff) → lepszy.
4. **T54 metryki roju**: automation_metrics (decyzje/cycle, defer-rate,
   allocation mix, strategy usage) — po pierwszych realnych runach.
5. **T55 inbox LoRa → field_feedback**: odpowiedzi z terena jako nowe
   zapotrzebowania/oceny decyzji roju (domknięcie pętli samodoskonalenia).

## Ryzyka

- Strategia cyklu przy niskich sygnałach ma niskie confidence → **defer do
  defaultu speed_first** — to zamierzone (basal nie zgadwa); wzrośnie po
  kalibracji (T52).
- Temperatury to SEEDY z repozytorium basal (eksperyment 45 decyzji) — do
  dopasowania własnymi danymi z decisions.jsonl.
- Przydziały sprzętu są suggest-only: fizyczna instalacja (telefon przy
  akwaponice) pozostaje aktem operatora (actuation gate).
- SELFOPT_BASAL_URL wskazuje zewnętrzny basal-serve; bez niego rdzeń
  wbudowany liczy decyzje offline (pole engine w logu mówi prawdę).
