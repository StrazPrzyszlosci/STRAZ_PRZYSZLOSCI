# CLAIM T44 — muse-4
- Zadanie: T44 (refactor: wspólne resolveCalibrationSuggestion dla preview T43 i apply T42 — usunięcie ~30 linii duplikacji ładowania polityki/korelacji/sugestii; zero zmian zachowania)
- Status: done (refactor + test resolvera; 318 OK + 384/0 w worktree; handoff PO_T44)
- Weryfikacja: jw.
- Start: 2026-10-02
- Branch/worktree: codex/T44-calibration-dedupe-muse-4 w `.kilo/worktrees/muse-4` (IZOLACJA — własny worktree, koniec wojen edycji)
- Dotknięte pliki: `cloudflare/src/execution_pack_initiator.js` (tylko sekcje T42/T43 — moje),
  `tests/execution_pack_calibration_test.mjs` + `tests/calibration_preview_test.mjs` (dopiski asercji, moje pliki);
  ODCZYT: `agri_calibration.js`. CUDZE pliki i branche NIETYKANE.
- Kolizje: brak (worktree izolowany; współdzielone drzewo tylko do odczytu ls/claims)
