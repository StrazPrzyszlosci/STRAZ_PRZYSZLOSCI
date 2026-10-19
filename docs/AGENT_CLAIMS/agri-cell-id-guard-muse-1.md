# CLAIM agri-cell-id-guard — muse-1
- Zadanie: FIX krytyczny — kanoniczne grow_cell_id (np. phone-aquaponics-observer-01) nie przechodzą validateProviderId (brak segmentu env), więc CAŁA pętla agri (telemetria/evaluate/harvest/trendy/korelacja) oraz rejestracja komórek zwracają 400. Naprawa: ensureAgriCellAllowed (strict-ID bez zmian; fallback: komórka znana z agri_grow_policies) + podpięcie w routach agri i provider-lifecycle + testy fetch-level
- Status: done (guard w workerze + 8 testów routów zielonych, pełna suita 379/0 + 318 OK)
- Start: 2026-10-02
- Branch/worktree: codex/T40-wizualizacja-diff-kalibracji (drzewo czyste)
- Dotknięte pliki: cloudflare/src/worker.js (NOWA funkcja + 9 swapów await, ZERO zmian bloków T40/T41), tests/agri_routes_test.mjs (rozszerzenie)
- Kolizje: wszystkie claimy done/inne obszary; worker.js wolny (ostatni commit 7aa9c15). Nie ruszam logiki limiterów/healthcheck
