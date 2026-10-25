# CLAIM T67 — glm53 (rój: zwiadowca całościowy + dyrektor/asystent + masowy pool)

- Zadanie: T67 — realizacja dyrektywy architektonicznej operatora 2026-10-25: (a) zwiadowca bada stan repo, NIESCALONE PR-y, PROJEKTY/ i architekturę sprzętową, szuka zadań gdy brak; (b) basal = asystent dyrektora (szybkie decyzje operacyjne + raport do większego modelu, który daje dyrektywy); (c) wiele wątków naraz — modele NIM niezależnie (każdy ma osobne 40 RPM); (d) ewolucja: zmiana sprzętu → zadanie adaptacyjne, przyrost bazy części → odświeżenie, adoptacja kodu zewnętrznego optymalizującego projekty; (e) cele: rozwój software + przygotowanie do produkcji/aktuation na sprzęcie z odzysku (suggest-only, charter gated).
- Status: in_progress
- Start: 2026-10-25
- Branch/worktree: codex/T67-scout-director-pool (worktree glm53-swarm; stack na T66)
- Dotknięte pliki: `selfopt_chain/evolution_targets.json`, `selfopt_chain/evolver.py` (generate_llm_strategy + raport asystenta), `selfopt_chain/orchestrator.py` (scout snapshot: open PRs/hardware/parts; przekazanie raportu), `tools/run_swarm_pilot.mjs` (forward --evolve-lanes), NOWE testy `tests/test_selfopt_scout.py`, unit systemd (poza git)
