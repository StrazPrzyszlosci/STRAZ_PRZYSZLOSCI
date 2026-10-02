# CLAIM T43 — muse-4 (dawniej muse-spark)
- Zadanie: T43 (podgląd diff kalibracji w bocie: `!calibration preview <policy_id>`, read-only, bez packa i bez PR)
- Status: done (implementacja + 4 testy; 2 testy dopisał muse-2 — plik współdzielony;
  1 fix asercji T42 po stronie muse-2; pełna suita czeka na cell-id guard muse-1)
- Handoff: docs/HANDOFF_DLA_NASTEPNEGO_AGENTA_2026-10-02_PO_T43_CALIBRATION_PREVIEW.md
- Weryfikacja: Python 318 OK + preview 6/6 + node --check + manifest/approvals OK;
  pełny mjs 385/3 (3 fail cudze, w toku)
- Start: 2026-10-02
- Branch/worktree: codex/T43-calibration-preview-muse-4 (osobny branch — izolacja)
- Dotknięte pliki: `cloudflare/src/execution_pack_initiator.js` (NOWA sekcja T43, bez ruszania T42/T23),
  komendy w `discord_api_handler.js` / `telegram_issues.js` (NOWE subkomendy, additive),
  NOWY test `tests/calibration_preview_test.mjs`; ODCZYT: `agri_calibration.js`, `agri_calibration_view.js`
- Kolizje: brak (muse-1 testuje routy bez edycji handlerów; T40–T42 done; hardening cudzy obszar)
