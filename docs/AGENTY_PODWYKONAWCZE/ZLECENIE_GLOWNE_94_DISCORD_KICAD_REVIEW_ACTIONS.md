# ZLECENIE GŁÓWNE 94 - Discord KiCad review actions

## Cel

Dodać przyciski/akcje Discord dla wyników KiCad staging: `Wyślij do review`, `Zatwierdź`, `Odrzuć`, z zachowaniem tego samego ledgeru co Telegram.

## Kryteria odbioru

- Brak oddzielnej logiki biznesowej Discord; używać wspólnych funkcji review.
- Tylko uprawniony maintainer może zatwierdzać.
- Każda akcja zapisuje `reviewed_by`, `reviewed_at`, `reason` i poprzedni status.

## Status

DONE (2026-07-05) — odebrane w `ODBIOR_PORTFELA_24_ZADANIE_94_2026-07-05.md`.
Implementacja: `cloudflare/src/discord_kicad_actions.js` + integracja w `discord_api_handler.js` + testy `tests/discord_kicad_actions_test.mjs` (10 testów PASS). Cienka warstwa nad `kicad_review.js` z Z90, walidacja maintenera przez env `KICAD_REVIEW_MAINTAINER_IDS`/`KICAD_REVIEW_MAINTAINER_ROLES`.
