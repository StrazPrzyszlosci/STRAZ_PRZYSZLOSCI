# Zlecenie Glowne 68 — Discord Webhook Content-Length Limit

## 1. Misja

Dodac Content-Length check w Discord webhook handlerze, analogicznie do Telegram webhook handlera (Z64).

## 2. Read First

- `cloudflare/src/discord_api_handler.js`
- `docs/AGENTY_PODWYKONAWCZE/MINI_HANDOFF_ZADANIE_64.md`

## 3. Rozwiazanie

Dodano sprawdzenie naglowka `Content-Length` na poczatku `handleDiscordWebhook()`. Limit konfigurowalny przez `DISCORD_MAX_WEBHOOK_BODY_BYTES` lub `MAX_WEBHOOK_BODY_BYTES` (default 5MB). Zwraca 413 `Payload Too Large` jesli Content-Length przekracza limit.

## 4. Acceptance Criteria

- `node --check cloudflare/src/discord_api_handler.js` — PASS
- Webhook z Content-Length > max zwraca 413

## 5. Zmienione pliki

- `cloudflare/src/discord_api_handler.js` — Content-Length check + 413 response
