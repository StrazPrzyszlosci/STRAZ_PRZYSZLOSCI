# CLAIM T43 — muse-4 (dawniej muse-spark)
- Zadanie: T43 (podgląd diff kalibracji w bocie: `!calibration preview <policy_id>`, read-only, bez packa i bez PR)
- Status: in_progress
- Start: 2026-10-02
- Branch/worktree: codex/T43-calibration-preview-muse-4 (osobny branch — izolacja)
- Dotknięte pliki: `cloudflare/src/execution_pack_initiator.js` (NOWA sekcja T43, bez ruszania T42/T23),
  komendy w `discord_api_handler.js` / `telegram_issues.js` (NOWE subkomendy, additive),
  NOWY test `tests/calibration_preview_test.mjs`; ODCZYT: `agri_calibration.js`, `agri_calibration_view.js`
- Kolizje: brak (muse-1 testuje routy bez edycji handlerów; T40–T42 done; hardening cudzy obszar)
