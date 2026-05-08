# Portfel 19 Zlecen Dla Podwykonawcow - Zadania 84-86 + nastepne

## Cel portfela

Automatyzacja bezpieczenstwa: regresyjne testy security headers, globalny rate limit API, framework migracji D1 schema. Kontynuacja paradygmatu zero-regression security pipeline.

## Zadania

| ID | Plik | Cel | Status |
|----|------|-----|--------|
| 84 | ZLECENIE_GLOWNE_84_SECURITY_HEADERS_REGRESSION_TEST.md | Automatyczne testy regresji security headers (HSTS, nosniff, XFO, Referrer) dla wszystkich endpointow | PASS |
| 85 | ZLECENIE_GLOWNE_85_GLOBAL_API_RATE_LIMIT.md | Globalny rate limit API (per IP / per API key) - rozszerzenie per-chat rate limitera | TODO |
| 86 | ZLECENIE_GLOWNE_86_D1_SCHEMA_MIGRATIONS.md | Framework migracji schema D1 (ALTER TABLE, CREATE INDEX, transakcje) oparty na split_d1_backup.py | TODO |

## Zadania z PORTFEL_18 (uzupelnienie)

| ID | Cel | Status |
|----|-----|--------|
| Z81 | CSP (Content-Security-Policy) dla API response | TODO |
| Z82 | Permissions-Policy dla API response | TODO |
| Z83 | Global checkWebhookPayloadSize — refaktoryzacja Discord + Telegram | TODO |

## Zadania domkniete w tej sesji

### Z84
- Stworzono `cloudflare/src/security_headers.js` (modul wspoldzielony)
- Przeniesiono `getCorsAllowOrigin()` i `jsonResponse()` z `worker.js` do `security_headers.js`
- `worker.js` importuje z nowego modulu
- `tests/worker_security_headers_test.mjs` — 12 testow regresji:
  - jsonResponse domyslny zawiera wszystkie security headers (HSTS, nosniff, XFO, Referrer, CORS)*5 statusow (200, 400, 403, 413) — kazdy z security headers
  - getCorsAllowOrigin: matching Origin, non-matching Origin, no request (info disclosure guard), empty/undefined env
  - jsonResponse z wlasciwym Origin i whitelista odzwierciedla dopasowany origin
  - HSTS max-age 31536000 includeSubDomains
  - Wszystkie testy PASS (12/12)

## Statystyki testow

```
Suites: 34, Tests: 161, PASS: 161, FAIL: 0
```

## Zasada portfela

Testy regresji > manual audit. Kazdy nowy endpoint musi przechodzic test security headers. Security headers module (security_headers.js) jest single source of truth (od teraz nie inline w worker.js).

## Zadania na pozniej

| ID | Opis | Priorytet |
|----|------|-----------|
| Z55 | ESP runtime - real hardware bench i maintainer signature | blocked |
| Z85 | Global API rate limit (per IP / per API key) | wysoki (nastepne) |
| Z86 | D1 Schema migrations framework | sredni |
| Z81 | CSP dla API response | niski |
| Z82 | Permissions-Policy dla API response | niski |
| Z83 | Global checkWebhookPayloadSize refaktoryzacja | niski |

## Pliki utworzone/zmienione

- `cloudflare/src/security_headers.js` — nowy modul wspoldzielony security headers (Z84)
- `cloudflare/src/worker.js` — importuje jsonResponse z security_headers.js zamiast inline (Z84)
- `tests/worker_security_headers_test.mjs` — 12 testow regresji (Z84)
