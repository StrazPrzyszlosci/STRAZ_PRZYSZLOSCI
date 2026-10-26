# CLAIM T68 — glm53 (rój: maksymalizacja utylizacji modeli + pętla OSS z internetu)

- Zadanie: T68 — dyrektywa operatora 2026-10-25: (a) jak największa liczba modeli z przydzielonym zadaniem — misje tła dla bezczynnych modeli gdy backlog cienki (tematy: PROJEKTY do realizacji na laptop+API, skan OSS, przegląd modułów selfopt, zdrowie repo); (b) pętla internetowa: watchlist OSS → shallow-clone do cache → katalog jako runtime-input celu adoptacji (tylko źródła approved; nowe źródła wymagają jednorazowej akceptacji operatora — bezpieczeństwo); (c) utylizacja modeli w raporcie asystenta (armed vs z zadaniem) — dyrektor widzi i optymalizuje przydziały; (d) brak stałej architektury — ewolucja celów/kadencji już w T67, T68 dodaje paliwo zadań.
- Status: done (604 testów OK; misje tła w pending(); oss fetch + katalog; utylizacja w raporcie asystenta)
- Start: 2026-10-25 (późny wieczór)
- Branch/worktree: codex/T68-idle-missions-oss (worktree glm53-swarm; stack na T67)
- Dotknięte pliki: `selfopt_chain/evolver.py` (misje tła), `selfopt_chain/orchestrator.py` (scout: oss fetch + utylizacja w raporcie), `selfopt_chain/evolution_inputs.py` (allowlist oss_catalog.json), `selfopt_chain/evolution_targets.json` (runtime_refs), NOWE testy `tests/test_selfopt_missions.py`, unit (max-tasks 4)
