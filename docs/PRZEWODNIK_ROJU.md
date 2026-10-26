# Przewodnik roju — jak działa i jak nim sterować

> Przewodnik operatora po **roju `selfopt_chain`**: cyklicznym, samouczącym się
> orchestratorze, który zamienia dostępne zasoby (darmowe modele LLM, laptop,
> internet, a docelowo telefony/ESP32/LoRa) na rozwój tego repozytorium — zawsze
> **suggest-only**: rój proponuje, człowiek scala.
>
> Stan: opisuje kod działający w daemonie (stack T65–T68; części w otwartych
> PR #34/#36/#37/#38). Filozofia: *Intelekt wyprzedza Kapitał*.

---

## 1. Czym jest rój

Rój to **proces, nie usługa**: pętla, która co ~2–5 minut (systemd, non-stop):

1. **zwiaduje** otoczenie (repo, niescalone PR-y, projekty, sprzęt, baza części, OSS),
2. **planuje** (duży model = dyrektor strategii; basal = asystent decyzji operacyjnych),
3. **wykonuje** zadania na wielu darmowych modelach **równolegle** (ensemble ról),
4. **ocenia** wyniki (walidacja, SecurityGate, niezależny recenzent ≥ producent),
5. **publikuje** najlepsze jako draft PR,
6. **uczy się** z wyników (auto-etykiety → kalibracja decyzji).

Rój nie ma stałej architektury: **zarządza sam swoim wykorzystaniem zasobów**
(cele kadencyjne, misje tła, metryka utylizacji modeli) i ewoluuje, gdy zasoby
się zmieniają (nowy model w API, nowy sprzęt, przyrost bazy części).

## 2. Role i warstwy

| Rola | Kto | Plik/logika |
|---|---|---|
| **Dyrektor** | duży darmowy model (reason) | `generate_llm_strategy()` — priorytety, `model_hints`, dyrektywa `assistant_feedback`, dekompozycja na podzadania |
| **Asystent** | basal (lokalny, szybki, `basal-omni-pico` na ollamie) | `BasalDecisionCore` — decyzje operacyjne: wybór modeli, tryb równoległości; **raportuje** do dyrektora (`assistant_report.json`) |
| **Robotnicy** | pula darmowych modeli (NIM: GLM 5.3, nemotrony…; kilocode) | `HermesWorker`/`direct_patch` — produkcja propozycji/łatek w sandboxie |
| **Recenzent** | model o tierze ≥ producent | `review_by_strong_model()` — fail-closed, gdy brak kwalifikowanego |
| **Zwiadowca** | krok orchestratora | `_scout_snapshots()` — PR-y/sprzęt/części/OSS jako dane wejściowe |

Warstwy zasobów (gotowość): **L0** darmowe API (już), **L1** laptop-koordynator
(już), **L2** smartfony (apka/YOLOX/OpenBot — checklisty gotowe), **L3** ESP32
(LLM→algorytm→sandbox→PR→człowiek flashuje). Gdy L2/L3 dostarczysz, rój przyjmie
je przez cel `hardware_adaptation` i misje gotowości.

## 3. Pętla cyklu — krok po kroku

**0. Non-stop.** systemd: `straz-ollama`, `straz-basal`, `straz-omniroute`,
`straz-swarm-evolution` (`Restart=always`, linger). Awaria (np. ollama pod presją
pamięci) = auto-powrót; rój wznawia sesje z kolejki.

**1. Zwiad** (każdy cykl, best-effort, awaria kroku nie blokuje cyklu):
- `open_prs.json` — niescalone PR-y (`gh pr list`),
- `hardware_changes.json` — diff architektury sprzętowej między cyklami,
- `parts_db_changes.json` — przyrost bazy części z recyklingu,
- `oss_catalog.json` — płytkie klony źródeł z `oss_watchlist.json` (tylko `approved: true`),
- `assistant_report.json` — raport asystenta: decyzje, etykiety, PR-y, sprzęt,
  **utylizacja modeli** (`models_with_task` vs `models_armed`).

**2. Bramki.** KILL_SWITCH (plik w state-dir ⇒ stop), quota gate (snapshot limitów),
charter (konstytucja: broń, inwigilacja, prawa człowieka — twardy stop).

**3. Dyrektor.** Czyta backlog (cele + misje tła + handoffy + propozycje +
podzadania własne) + raport asystenta → JSON: `brief`, `priorities`,
`model_hints`, `assistant_feedback`, `subtasks`. Offline → fallback deterministyczny.

**4. Asystent (basal).** Dla każdego zadania: `model_selection` z krótkiej listy
(floor per rodzaj zadania: review≥4, code_draft≥4…), tryb `single|wide|deep`.
Każda decyzja ląduje w `decisions.jsonl` (id, confidence, probabilities).

**5. Zadania.** Źródła: **cele operatora** (`evolution_targets.json` — z kadencją
`reset_after_days`: PR triage 3d, sprzęt/części/OSS 7d, aktuation 14d, rejestr modeli 14d),
**misje tła** (gdy backlog cieńszy niż pasma: analizy PROJEKTY, OpenBot, LoRa,
modułów, zdrowia repo — niskopriorytetowe, tygodniowo świeże), handoffy, propozycje
z wcześniejszych cykli. Wszystkie przechodzą tę samą ścieżkę charter→inputy→shortlist.

**6. Wykonanie.** Ensemble: **K producentów na jedno zadanie równolegle**
(`--evolve-ensemble 2`) — różne modele, różne role; budżet sesji wg `speed_class`
(slow NIM = 900 s, minimum NIM 720 s; cold-start upstreamu), RPM per model
(NIM 40, kilocode 8) rozliczane w `quota_ledger.json`. Wykonawcy: Hermes w sandboxie
(bwrap, bez sieci poza API, kwarantanna) lub `direct_patch` dla łatek.

**7. Ocena.** Walidacja: baseline **FAIL** → candidate **PASS** → pełna regresja
PASS (odizolowane uruchomienie testów). SecurityGate: wzorce, licencje, PII,
charter; naruszenie = kwarantanna. Recenzja: **niezależny model o tierze ≥ producent**
(mocny sprawdza słabego — zawsze), fail-closed `no_reviewer_at_required_tier`.

**8. Ranking ensemble.** `rank_ensemble_candidates`: gate > review > walidacja >
wykonanie; zwycięzca = wynik zadania; pełne porównanie w `ensemble_report.json`.

**9. Publikacja.** `gate_ok` ⇒ stage-branch + commit + **draft PR**
(`no_auto_merge`, `no_direct_push`). Scalanie to wyłączna decyzja człowieka.
Pierwsza samodzielna publikacja roju: PR #32 (scalona).

**10. Nauka.** Każdy wynik → **auto-etykieta** decyzji (source `auto_outcome`,
mechaniczne bramki, nie samoocena modelu) + etykiety operatora. `fit_temperatures`
kalibruje pewność decyzji; dyrektor widzi statystyki w raporcie asystenta;
`metrics.py` raportuje skuteczność (zwalidowane artefakty/100 wywołań, recenzje,
duplikaty, missing_data).

## 4. Bezpieczeństwo — nieprzetargowalne

- **Suggest-only**: rój nigdy nie merge'uje, nie pushuje do main, nie wdraża.
- **Charter**: prawa człowieka, broń, inwigilacja — blokada misji i produkcji.
- **Actuation gate**: `physical_actuation` zabroniona; firmware/flash/montaż =
  zawsze człowiek (e-stop fizyczny na urządzeniu).
- **Tylko darmowe modele** (rejestr bojowy + `FreeOnlyPolicy`); sekrety tylko w env.
- **Nowe źródła OSS** wymagają `approved: true` w watchliście (kontrola człowieka).

## 5. Jak obserwować roju

```bash
systemctl --user status straz-swarm-evolution      # żyje?
ls scratch/selfopt/continuous-live/evolution_batches | tail  # batche
cat scratch/selfopt/continuous-live/last_evolution_plan.json   # plan dyrektora
cat scratch/selfopt/continuous-live/assistant_report.json      # raport basal
python3 selfopt_chain/metrics.py --state-dir scratch/selfopt/continuous-live
```

Stany batchy: `wide/deep/single` (praca), `waiting_inputs` (brak zadań — zwiadowca
szuka), `waiting_budget`/`waiting_rate_limit` (pacing RPM/dzienny), `waiting_provider`
(cooldown modelu po porażkach), `waiting_models` (brak profilu ≥ floor),
`blocked` (charter/quota/kill switch). Pomyłki sesji: `no_artifacts`
(model nie zapisał pliku), `HTTP 429` (limit — sprawdzić RPM w ledgerze),
`timeout` (podnieść budget wg speed_class).

## 6. Jak sterować

- **Unit** `~/.config/systemd/user/straz-swarm-evolution.service`:
  `--evolve-max-tasks` (równoległe zadania), `--evolve-ensemble` (producenci na
  zadanie), `--turns` (tury Hermes), `--pause` (przerwa między cyklami).
  Zmiana: edycja + `systemctl --user daemon-reload && systemctl --user restart straz-swarm-evolution`.
- **Kill switche**: plik `KILL_SWITCH` w state-dir zatrzymuje pętlę;
  `~/.local/share/straz/KILL_BASAL` blokuje basal.
- **Cele**: `selfopt_chain/evolution_targets.json` (dodanie wpisu = nowe zadanie;
  `reset_after_days` = cel samo-wracający).
- **Modele**: `selfopt_chain/runtime_model_profiles.json` (profil = kwalifikacja
  do rejestru bojowego; NIM przechodzi przez `nvidia/*` + profil).
- **OSS**: `scratch/selfopt/<run>/oss_watchlist.json` — `{"name":…, "url":…, "approved":true}`.

## 7. Gdy przybędzie sprzęt (telefon/ESP32/LoRa)

1. Podłącz zasób — zwiadowca wykryje zmianę w `hardware_changes.json`
   (cel `hardware_adaptation` przygotuje adaptację: konteksty, pasma, budżety).
2. Misje gotowości wyplują checklisty wdrożenia: apka OpenBot (PROJEKTY 06/08),
   YOLOX on-device, węzeł LoRa (PROJEKTY 10), firmware ESP32
   (LLM → sandbox → PR → **człowiek flashuje**).
3. Fizyczna aktuation pozostaje gated do czasu decyzji operatora (charter).

## 8. Mapa kodu

- `selfopt_chain/orchestrator.py` — cykl, zwiad, admission, kalibracja
- `selfopt_chain/evolver.py` — strategia dyrektora, misje tła, ensemble, ranking
- `selfopt_chain/hermes_worker.py`, `evolution_validation.py`, `evolution_store.py`,
  `evolution_publication.py` — wykonanie, walidacja, kolejka prób, draft PR
- `selfopt_chain/swarm.py`, `router.py`, `model_selection.py`, `calibrate.py`,
  `metrics.py`, `quota.py` — basal, routing, krótkie listy, nauka, metryki, budżety
- `selfopt_chain/charter.json`, `capability_map.json`, `runtime_model_profiles.json`,
  `evolution_targets.json` — konstytucja, klasy zasobów, pula modeli, cele
- Testy: `python3 -m unittest discover -s tests -p 'test_*.py'` (604 OK na T68)

**Powiązane dokumenty:** `docs/SCHEMAT_ALGORYTMU_ROJU.md`,
`docs/RUNBOOK_PILOTA_ROJU_T53_2026-10-23.md`, `docs/LITEWEED_WZORZEC_REFERENCYJNY.md`,
najnowszy `docs/HANDOFF_DLA_NASTEPNEGO_AGENTA_*.md`.
