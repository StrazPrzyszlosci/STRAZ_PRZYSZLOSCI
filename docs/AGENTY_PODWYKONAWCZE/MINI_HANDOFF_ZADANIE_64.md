# Mini-Handoff ZADANIE 64

## Co zostalo zrobione

1. **Dodano Content-Length check do `handleTelegramWebhook`** w `telegram_issues.js`:
   - Sprawdza nagłówek `Content-Length` przed parsowaniem JSON body
   - Konfigurowalne przez `TELEGRAM_MAX_WEBHOOK_BODY_BYTES` lub `MAX_WEBHOOK_BODY_BYTES` (env var)
   - Domyslny limit: 5MB (5242880 bajtow)
   - Zwraca 413 `Payload Too Large` jesli Content-Length przekracza limit

2. **Dlaczego 5MB**:
   - Telegram API limit dla wiadomosci to 50MB (plik) ale webhook payload (JSON z metadanymi) rzadko przekracza 100KB
   - 5MB to bezpieczny gorny limit ktory blokuje ataki DoS przez ogromne payloady
   - Nie blokuje zdjec — zdjecia sa przesylane przez Telegram file API, nie przez webhook

## Jakie pliki zmieniono

- `cloudflare/src/telegram_issues.js` — dodano Content-Length check + 413 response
- `docs/AGENTY_PODWYKONAWCZE/MINI_HANDOFF_ZADANIE_64.md` (ten plik)

## Jakie komendy walidacyjne przeszly

- `node --check cloudflare/src/telegram_issues.js` — PASS

## Otwarte ryzyka

- Niektore proxy/CDN moga usuwac naglowek `Content-Length` (wtedy check jest pomijany — fallback na parsowanie JSON ktore i tak rzuci blad przy ogromnym payloadzie)
- Discord webhook handler (`discord_api_handler.js`) nie ma jeszcze Content-Length check — nalezaloby dodac analogicznie