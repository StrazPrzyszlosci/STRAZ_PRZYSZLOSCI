# Handoff dla Nastepnego Agenta - PORTFEL_19 (Z84) - 2026-05-08

## Cel sesji

Domkniecie Z84 (security headers regression test) i przygotowanie grunt dla Z85 (global API rate limit) i Z86 (D1 schema migrations).

## Zmiany w kodzie (Z84)

### Nowe pliki
- `cloudflare/src/security_headers.js` — wspoldzielony modul security headers (`getCorsAllowOrigin`, `jsonResponse`)
- `tests/worker_security_headers_test.mjs` — 12 testow regresji

### Zmienione pliki
- `cloudflare/src/worker.js` — usunieto inline definice `getCorsAllowOrigin` i `jsonResponse`; importuje z `security_headers.js`

### Architektura security headers (security_headers.js)

```javascript
export function getCorsAllowOrigin(env, request) {...}
export function jsonResponse(payload, status, env, request) {...}
```

- `getCorsAllowOrigin`: wyczytaj `CORS_ALLOWED_ORIGINS` (comma-separated), default `"*"` (wildcard). Gdy whitelist: dopasuj `Origin` header; gdy nie pasuje lub brak `Origin` — zwraca pierwszy allowed origin (info disclosure prevention).
- `jsonResponse`: zwraca `Response` z security headers (HSTS, nosniff, XFO, Referrer, CORS).

### Decyzje

| Decyzja | Uzasadnienie |
|---------|-------------|
| Single source of truth (security_headers.js) | Unika duplikacji; testy bez replikowania kodu; kazdy nowy endpoint importuje ten sam modul |
| getCorsAllowOrigin bez request zwraca pierwszy origin | Zapobiega ujawnieniu whitelisted origins nieautoryzowanemu hostowi |
| Import instead of inline | Testowalny kod; kazda zmiana w security headers jest testowana |

## Wynik testow

```bash
node --test tests/worker_security_headers_test.mjs
# suites: 1, tests: 12, pass: 12, fail: 0

node --test tests/discord_bot_security_test.mjs tests/discord_bot_ed25519_test.mjs tests/discord_rate_limiter_load_test.mjs tests/discord_api_handler_413_and_timing_safe_test.mjs tests/telegram_issues_413_test.mjs tests/worker_security_headers_test.mjs
# suites: 34, tests: 161, pass: 161, fail: 0
```

## Nastepne zadania

| ID | Opis | Priorytet |
|----|------|-----------|
| Z85 | Global API rate limit (per IP / per API key / per project) | wysoki |
| Z86 | D1 Schema migrations framework | sredni |
| Z81 | CSP (Content-Security-Policy) dla API | niski |
| Z82 | Permissions-Policy dla API | niski |
| Z83 | Global checkWebhookPayloadSize refaktoryzacja | niski |

## Blockers

- Z55 ESP runtime: real hardware + maintainer signature (wymaga fizyczny sprzet)

## Pliki

- `docs/AGENTY_PODWYKONAWCZE/PORTFEL_19_ZLECEN_DLA_PODWYKONAWCOW_2026-05-08.md`
- `docs/HANDOFF_DLA_NASTEPNEGO_AGENTA_2026-05-08_POZ_19.md`
