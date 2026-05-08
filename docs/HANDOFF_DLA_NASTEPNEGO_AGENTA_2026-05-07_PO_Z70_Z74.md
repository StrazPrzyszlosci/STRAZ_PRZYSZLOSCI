# Handoff dla Nastepnego Agenta - 2026-05-07 po Z70-Z74

## Cel sesji

Domkniecie security hardening Zlecen 70-74: pozostale fetch timeouty, konsolidacja duplikatow, test coverage timing-safe + 413.

## Zmiany w kodzie (Z70-Z74)

### Z70 - Pozostale fetch timeouty
- `cloudflare/src/telegram_ai.js`:
  - `searchGoogleForPdf`: HEAD fetch -> `fetchWithTimeout(url, {method: 'HEAD', headers: {...}}, 15000)` (~line 5320)
  - `fetchExternalPdfAsBase64`: GET fetch -> `fetchWithTimeout(url, {redirect: 'follow', headers: {...}}, 30000)` (~line 5342)
- Potwierdzone wczesniej: `worker.js` (webhook-info 15s, setWebhook 15s), `github_issues.js` (createGitHubIssue 15s), `recycled_catalog.js` (dispatch 5s)

### Z71 - Konsolidacja duplikatu fetchTelegramFileAsBase64
- Usuniety duplikat z `telegram_ai.js` (byl na linii ~2018)
- `history.js` importuje z `base_utils.js`
- `telegram_issues.js` importuje z `base_utils.js`
- `telegram_ai.js` nie importuje (nie potrzebuje, ale jesli kiedykolwiek bedzie potrzebowal - uzywaj base_utils.js)

### Z72 - Telegram callback timeouts
- `answerCallbackQuery` i `editMessageReplyMarkup` w `telegram_issues.js` juz uzywaly `fetchWithTimeout` (10s) - confir software z sesji Z61

### Z73 - GitHub API timeouts
- `createGitHubIssue` w `telegram_issues.js` (15s) i `github_issues.js` (15s)
- GitHub dispatch w `telegram_ai.js` (5s) i `recycled_catalog.js` (5s)

### Z74 - Unit testy timingSafeEqualString + Content-Length 413
- Nowy plik: `tests/discord_api_handler_413_and_timing_safe_test.mjs` (15 testow)
- Testuje `timingSafeEqualString` (7 scenariuszy) i `checkDiscordPayloadSize` (8 scenariuszy)
- 135/135 PASS lacznie

## Dodatkowe zmiany (niezaplanowane)

- **Z69 kontynuacja**: `discord_api_handler.js` usunal duplikat `timingSafeEqualString` (48-60) i importuje z `base_utils.js` (47)

## Testy

```bash
node --test tests/discord_bot_security_test.mjs tests/discord_bot_ed25519_test.mjs tests/discord_rate_limiter_load_test.mjs tests/discord_api_handler_413_and_timing_safe_test.mjs
# Suites: 32, Tests: 135, Pass: 135, Fail: 0
```

### Lista plikow testowych
- `tests/discord_bot_security_test.mjs` - 75 testow (sanitize, rate limit, mime types, attachments)
- `tests/discord_bot_ed25519_test.mjs` - 29 testow (Ed25519 verification)
- `tests/discord_rate_limiter_load_test.mjs` - 16 testow (performance + regression)
- `tests/discord_api_handler_413_and_timing_safe_test.mjs` - 15 testow (timingSafeEqualString, 413 logic)

## Architektura - nowe kluczowe pliki

| Plik | Zawartosc |
|------|-----------|
| `discord/discord_security.mjs` | checkRateLimit, sanitizeDiscordInput, isAllowedMimeType, mapAttachmentToPayload |
| `cloudflare/src/base_utils.js` | fetchWithTimeout, fetchTelegramFileAsBase64, timingSafeEqualString, knowledgeBundle |
| `cloudflare/src/discord_api_handler.js` | Handled importy z base_utils.js, Content-Length check, timingSafeEqualString |
| `cloudflare/src/telegram_issues.js` | Content-Length check w handleTelegramWebhook (juz byl), fetchWithTimeout wszedzie |

## Decyzje i kontekst

| Decyzja | Uzasadnienie |
|---------|-------------|
| `CLEANUP_INTERVAL = 100` | Cleanup rate limitera co 100 insertow, nie co insert. 30k userow: 86ms. |
| Content-Length default 5MB | Bezpieczny limit dla JSON metadata webhook. Telegram: TELEGRAM_MAX_WEBHOOK_BODY_BYTES, fallback MAX_WEBHOOK_BODY_BYTES. Discord: DISCORD_MAX_WEBHOOK_BODY_BYTES, fallback MAX_WEBHOOK_BODY_BYTES. |
| `timingSafeEqualString` w base_utils.js | Pure JS XOR, zawsze sama dlugosc petli, dziala w Node.js i CF Workers (brak dep na Web Crypto). |
| fetchWithTimeout domyslnie 15s | Z bezpieczenstwa; pliki 30s, callbacks 10s, dispatches 5s. |

## Istniejace luki / praca na pozniej

| ID | Opis | Priorytet |
|----|------|-----------|
| Z75 | Content-Length 413 testy dla Telegram (telegram_issues.js) - analogiczne do Z74 ale dla Telegrama | medium |
| Z76 | Wrap pozostalych raw fetch w cloudflare/src/telegram_ai.js (inne niz datasheet scraping, jesli jakies zostaly) | low |
| Z55 | ESP runtime - real hardware bench i maintainer signature (Canary C-1..C-5 OPEN) | blocked |

## Approved / Rejected

| Element | Decyzja | Kto |
|---------|---------|-----|
| Z70-Z74 | Approved | system (self-audit) |
| HANDOFF | Draft | krzysiek |

## Portfel

`docs/AGENTY_PODWYKONAWCZE/PORTFEL_16_ZLECEN_DLA_PODWYKONAWCOW_2026-05-07.md`

