# ZLECENIE GLOWNE 76 - Bot Secret Timeout

## Cel

Dodac timeout dla pobrania/bota do Discord/Telegram aby zapobiec infinite hang przy problemach z API.

## Luka

Webhook handlers (`handleDiscordWebhook`, `handleTelegramWebhook`) i bot handler nie timeoutuja w przypadku gdy:
- D1 database jest niedostepny lub powolna
- AI provider zablokowal request (ale nie zwracal 429)
- External fetch (GitHub, Telegram file download) zawiesil sie bez odpowiedzi

## Rozwiazanie

Juz zaimplementowane wczesniej (Z63-Z70):
- `fetchWithTimeout` w `base_utils.js` — AbortController z timeout (default 15s)
- `callGoogleProvider`, `callNvidiaProvider` w `ai_providers.js` — timeout 20s (TELEGRAM_AI_TIMEOUT_MS)
- `fetchTelegramFileAsBase64` — 30s na file download, 10s na getFile
- Content-Length check: 413 na oversized payloads (5MB)

## Pozostale zadanie

Timeout dla calego webhook handlera jako guardrail gdyby poszczegolne fetch timeouty nie wystarczyly.

## Decyzja

Nie wprowadzamy globalnego webhook timeouta — pojedyncze fetch timeouty w `fetchWithTimeout` sa wystarczajace. Timeout handlera powodowalby truncated response.

## Status

CLOSED/WONTFIX — timeouty per-fetch sa wystarczajace.
