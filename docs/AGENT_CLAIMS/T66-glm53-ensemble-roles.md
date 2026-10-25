# CLAIM T66 — glm53 (rój: ensemble ról modeli + porównanie wyników + pełny paralelizm)

- Zadanie: T66 — rój wykorzystuje wszystkie dostępne zasoby maksymalnie efektywnie: K producentów (różne modele, różne role) na JEDNO zadanie równolegle, walidacja + niezależny review każdego wyniku, ranking (gate > review > walidacja > wykonanie), zwycięzca publikowany, ALL kandydaci auto-etykietowani; odblokowany paralelizm zadań (--evolve-max-tasks przekazywany z unitu, nie zaszyty na 1).
- Status: done (590 testów OK; ranking gate>review>validation>execution; ensemble_report.json; auto-etykiety ról; max-tasks przekazywany z unitu)
- Start: 2026-10-25
- Branch/worktree: codex/T66-ensemble-roles (worktree glm53-swarm)
- Dotknięte pliki: `selfopt_chain/evolver.py`, `selfopt_chain/orchestrator.py`, `tools/run_swarm_pilot.mjs`, NOWY test `tests/test_selfopt_ensemble.py`, unit `~/.config/systemd/user/straz-swarm-evolution.service` (poza git)
- Dyrektywy operatora (2026-10-25): „przecież mogą być przydzielane różne role itd a potem wyniki badane itd"; „rój ma wykorzystywać wszystkie możliwe dostępne zasoby w sposób maksymalnie efektywny".
