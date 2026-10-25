# CLAIM T65 — glm53 (rój: pula kandydatów basala + samodzielność)

- Zadanie: T65 — pula kandydatów basala: listowanie NVIDIA NIM i dodanie mocnych modeli do rejestru bojowego; twardy guard „recenzent >= producent"; auto-etykiety z wyników mechanicznych (bez czekania na operatora); initial labels z dowodów (PR #32 merged).
- Status: done (575 testów OK; 13 modeli w puli w tym nvidia/z-ai/glm-5.3; guard recenzent>=producent; auto-etykiety; kadencja refresh 14d; labels 86)
- Start: 2026-10-25
- Branch/worktree: codex/T65-basal-candidate-pool (worktree glm53-swarm)
- Dotknięte pliki: `selfopt_chain/runtime_model_profiles.json`, `tools/run_swarm_pilot.mjs`, `selfopt_chain/evolver.py`, `selfopt_chain/evolution_store.py`, `scratch/selfopt/continuous-live/labels.jsonl` (dane wejściowe, poza git), NOWE testy `tests/test_selfopt_capability_pool.py`
- Dyrektywy operatora (2026-10-25): „przecież musisz zlistować nvidia nim i dodać modele stamtąd"; „niech działa jak najbardziej samodzielnie i się nie blokuje na tematach użytkownika"; GLM 5.3 (NVIDIA NIM) = obecnie najsilniejszy, wsparcie upstream kończy się wkrótce.
