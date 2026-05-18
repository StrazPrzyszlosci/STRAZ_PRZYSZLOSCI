# Odbiór Portfela 20 - Z81-Z83 + plan CERN KiCad - 2026-05-14

## Zakres odbioru

Odebrano zadania wykonane w commicie `4cf01fc` oraz wykonano dodatkową kontrolę jakości po uwadze, że testy 413 nie powinny replikować starej logiki lokalnie.

## Wynik odbioru

| ID | Zakres | Status | Uwagi odbioru |
|----|--------|--------|---------------|
| Z81 | CSP dla API JSON | PASS | `jsonResponse()` emituje `Content-Security-Policy: default-src 'none'; frame-ancestors 'none'`; test regresyjny sprawdza nagłówek. |
| Z82 | Permissions-Policy dla API JSON | PASS | `jsonResponse()` emituje restrykcyjny `Permissions-Policy`; test regresyjny sprawdza nagłówek. |
| Z83 | Wspólny helper Content-Length | PASS po korekcie testów | Discord i Telegram używają `checkPayloadSize()`. Testy 413 zostały poprawione tak, aby importowały produkcyjne funkcje zamiast lokalnych kopii starej logiki. |
| CERN KiCad plan | PASS jako decyzja architektoniczna | Decyzja: nie konwertować całej biblioteki przed ingestem; zacząć od staging/provenance i dry-run importera. |

## Dodatkowa korekta odbiorowa

Zmieniono testy:

- `tests/discord_api_handler_413_and_timing_safe_test.mjs` importuje teraz `timingSafeEqualString()` z `cloudflare/src/base_utils.js` i `checkDiscordPayloadSize()` z `cloudflare/src/discord_api_handler.js`.
- `tests/telegram_issues_413_test.mjs` importuje teraz `checkTelegramPayloadSize()` z `cloudflare/src/telegram_issues.js`.

Powód: testy regresyjne muszą chronić kod produkcyjny, a nie lokalnie skopiowaną implementację.

## Testy odbiorowe

```bash
node --test tests/discord_api_handler_413_and_timing_safe_test.mjs tests/telegram_issues_413_test.mjs tests/payload_size_shared_test.mjs tests/worker_security_headers_test.mjs
```

Wynik: 45 testów PASS, 0 FAIL.

## Decyzja odbiorowa

Portfel Z81-Z83 jest odebrany. Najlepszy kolejny krok techniczny to Z87: dry-run importer CERN KiCad Library, ponieważ dopiero realny raport z formatu danych powinien poprzedzać migracje D1 i komendy Discord.
