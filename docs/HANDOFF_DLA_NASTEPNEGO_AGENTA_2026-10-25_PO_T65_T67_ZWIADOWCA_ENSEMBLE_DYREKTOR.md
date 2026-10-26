# HANDOFF po T65–T67 — rój: pula NIM/GLM 5.3, ensemble ról, zwiadowca całościowy, dyrektor/asystent

Data: 2026-10-25 (wieczór). Autor: agent GLM (worktree `.kilo/worktrees/glm53-swarm`).
Wcześniejszy stos scalony do main: **#26 (T53–T55), #33 (T58), #28 (T59), #31 (T60), #32 (łatka ewolucji roju!)** — pełna pętla samopublikacji domknięta.

## Otwarte PR-y (czekają na review operatora — `no_auto_merge`)

| PR | Zadanie | Zawartość |
|---|---|---|
| #34 | T65 | pula kandydatów basala: NVIDIA NIM (GLM 5.3!) + guard recenzent>=producent + auto-etykiety + kadencja + labels 86 |
| #35 | — | README: LiteWeed wzorzec referencyjny (zlecenie operatora) |
| #36 | T66 | ensemble ról modeli + porównanie wyników + pełny paralelizm (stack na #34) |
| #37 | T67 | zwiadowca całościowy + dyrektor/asystent + cele misyjne (stack na #36) |

Merge kolejność: #34 → #36 → #37 (stack; diff po scaleniu pokaże tylko najwyższy).

## Stan roju (live, 22:04)

- Daemon: systemd `straz-swarm-evolution.service`, **non-stop**, worktree glm53-swarm (branch T67).
- Pula bojowa: **13 modeli** (NIM: GLM 5.3 tier 5, nemotron-ultra-550b/4-340b/253b/super-120b/70b, glm-5.3-flash, deepseek-v4.1-flash, kimi-k2.6; kilocode: cohere, lightning, ultra-550b:free, super-120b:free). RPM: NIM 40, kilocode 8. Walidator rejestru: OK.
- Zwiadowca (T67, live): `open_prs.json` (2 PR-y), `hardware_changes.json` (diff vs poprzedni cykl), `parts_db_changes.json` (przyrost bazy części), `assistant_report.json` (365 decyzji, 160 etykiet) → raport asystenta→dyrektora w każdym cyklu strategii.
- Etykiety: **160** (86 dowodowych od operatora + auto_outcome z wyników mechanicznych); auto-etykiety działają (każdy wynik zadania etykietowany, source `auto_outcome`).
- Znane blokady produkcyjne w t60-live/continuous-live: sesje Hermes na wolnych modelach NIM padają na limicie RPM (fix: rpm 40 NIM — w #34) i budżecie 360 s (fix: slow=900 s, NIM floor 720 s — w #34/#36). Po merge #34 oczekiwane przejście produkcji do fazy review.

## Konwencje i dyrektywy operatora (obowiązują)

1. **Rój nie merge'uje** (`no_auto_merge`, `no_direct_push`) — wszystkie PR draft.
2. Tylko darmowe modele; basal = **asystent dyrektora** (nie główny mózg) — duży model daje `model_hints` + `assistant_feedback`, basal wykonuje decyzje operacyjne i raportuje.
3. Recenzent >= producent (twardy guard `reviewer_floor`; fail-closed bez kwalifikowanego recenzenta).
4. Ensemble: K producentów na zadanie, ranking gate>review>walidacja>wykonanie, `ensemble_report.json`, auto-etykiety ról (winner/candidate).
5. Kadencja celów (`reset_after_days`) — re-audit rejestru 14d, PR triage 3d, sprzęt/baza części/OSS 7d, aktuation 14d.
6. `physical_actuation` pozostaje gated wg `charter.json`; zmiany konstytucji tylko PR człowieka.

## Testy (obowiązkowe przed każdą turą)

- Python: **596 OK** (`python3 -m unittest discover -s tests -p 'test_*.py'`; znany szum: `human_approval` expiry warning — nie jest FAILem).
- `node --check tools/run_swarm_pilot.mjs` — OK. Walidator rejestru: `validate_registry` — OK na live arming.
- Nowe pliki testów T65–T67: `test_selfopt_capability_pool.py` (14), `test_selfopt_ensemble.py` (11), `test_selfopt_scout.py` (6).

## Następne kroki (propozycje dla kolejnej tury)

1. Merge #34/#36/#37 (operator) → restart daemona na main.
2. Obserwacja: czy router_weights finally przechodzi gate z GLM 5.3 + ensemble; jeśli tak — pierwszy publikowany PR z ensemble.
3. Cel `external_oss_adoption` (7d) po pierwszym uruchomieniu da propozycje adoptacji OSS — kierować do PR.
4. Rozważyć (operator): podniesienie `--evolve-max-tasks` po sprawdzeniu pamięci hosta (16 GB, desktop zjada ~7 GB; ollama auto-restart działa — 2 crash/e wczoraj, NRestarts=2).
5. Basal pico: brak nowego GGUF na HF (snapshot = HEAD, kalibracja hash zgodny); re-check przez `free_models_registry_refresh` co 14 dni.
