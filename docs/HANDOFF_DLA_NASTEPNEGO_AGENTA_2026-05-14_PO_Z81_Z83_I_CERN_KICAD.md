# Handoff dla Następnego Agenta - Z81-Z83 + analiza CERN KiCad - 2026-05-14

## Cel sesji

Kontynuacja po `HANDOFF_DLA_NASTEPNEGO_AGENTA_2026-05-08_POZ_19.md`: domknięcie zadań Z81, Z82, Z83 oraz przygotowanie decyzji architektonicznej dla integracji CERN KiCad Library z bazą NSIP/botem Discord.

## Zmiany w kodzie

### Z81/Z82 — security headers

- `cloudflare/src/security_headers.js` ma teraz wspólny `getSecurityHeaders(env, request)`.
- `jsonResponse()` dodaje:
  - `Content-Security-Policy: default-src 'none'; frame-ancestors 'none'`
  - `Permissions-Policy: geolocation=(), camera=(), microphone=(), accelerometer=(), magnetometer=(), gyroscope=(), payment=(), usb=()`
- Test regresyjny `tests/worker_security_headers_test.mjs` sprawdza nowe nagłówki razem z HSTS, nosniff, XFO, Referrer-Policy i CORS.

### Z83 — wspólny payload size helper

- Dodano `cloudflare/src/payload_size.js`:
  - `DEFAULT_WEBHOOK_BODY_BYTES`
  - `getMaxPayloadBytes(env, opts)`
  - `checkPayloadSize(request, env, opts)`
- `cloudflare/src/discord_api_handler.js` eksportuje `checkDiscordPayloadSize()` i używa shared helpera.
- `cloudflare/src/telegram_issues.js` używa shared helpera w `checkTelegramPayloadSize()`.
- Dodano `tests/payload_size_shared_test.mjs`.

## Dokumentacja dodana

- `docs/ARCHITEKTURA_INTEGRACJI_CERN_KICAD_NSIP_2026-05-14.md` — decyzja: nie konwertować całej biblioteki CERN przed importem; najpierw dry-run importer i staging/provenance.
- `docs/AGENTY_PODWYKONAWCZE/PORTFEL_20_ZLECEN_DLA_PODWYKONAWCOW_2026-05-14.md` — zadania Z87-Z92.

## Testy wykonane

```bash
node --check cloudflare/src/security_headers.js
node --check cloudflare/src/payload_size.js
node --check cloudflare/src/discord_api_handler.js
node --check cloudflare/src/telegram_issues.js
node --test tests/worker_security_headers_test.mjs tests/payload_size_shared_test.mjs tests/discord_api_handler_413_and_timing_safe_test.mjs tests/telegram_issues_413_test.mjs
node --test tests/*.mjs
```

Wynik testów wycinkowych: 45 testów PASS, 0 FAIL. Dodatkowo pełny `node --test tests/*.mjs`: 179 testów PASS, 0 FAIL.

## Decyzja CERN KiCad Library

Odpowiedź dla właściciela projektu: nie musi najpierw konwertować bazy CERN. Integracja jest wykonalna bez wstępnej konwersji wersji, jeśli potraktujemy CERN jako źródło danych KiCad 9.x i zaimportujemy metadane do staging/provenance. Konwerter wersji powinien być używany później, dla eksportu projektów albo kompatybilności narzędzi, nie jako pierwszy etap ingestu.

## Najlepszy następny krok

Z87: zbudować dry-run importer CERN KiCad Library. Importer powinien działać na lokalnym checkout repo/archiwum, nie wymagać zapisu do D1, i wygenerować raport jakości z próbką dopasowań do `recycled_part_master`.

## Pliki kluczowe

- `cloudflare/src/security_headers.js`
- `cloudflare/src/payload_size.js`
- `cloudflare/src/discord_api_handler.js`
- `cloudflare/src/telegram_issues.js`
- `tests/worker_security_headers_test.mjs`
- `tests/payload_size_shared_test.mjs`
- `docs/ARCHITEKTURA_INTEGRACJI_CERN_KICAD_NSIP_2026-05-14.md`
- `docs/AGENTY_PODWYKONAWCZE/PORTFEL_20_ZLECEN_DLA_PODWYKONAWCOW_2026-05-14.md`
