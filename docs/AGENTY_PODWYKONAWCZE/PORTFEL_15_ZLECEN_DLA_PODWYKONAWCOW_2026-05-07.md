# Portfel 15 Zlecen Dla Podwykonawcow - Zadania 67-69 + nastepne

## Cel portfela

Domknac security hardening Discord i Telegram: performance fix, Content-Length, fetchWithTimeout, timing-safe secrets. Przygotowac infrastrukture na dalsze fetch timeouty i konsolidacje duplikatow kodu.

## Zadania

| ID | Plik | Cel | Status |
|----|------|-----|--------|
| 67 | `ZLECENIE_GLOWNE_67_DISCORD_RATE_LIMITER_PERFORMANCE_FIX.md` | Naprawic O(n) cleanup w rate limiterze Discorda (batched cleanup co 100 insertow) | PASS |
| 68 | `ZLECENIE_GLOWNE_68_DISCORD_WEBHOOK_CONTENT_LENGTH_LIMIT.md` | Dodac Content-Length check w Discord webhook handlerze (413 na oversized) | PASS |
| 69 | `ZLECENIE_GLOWNE_69_DISCORD_FETCH_TIMEOUT_AND_TIMING_SAFE_SECRET.md` | fetchWithTimeout dla Discord fetches + timingSafeEqualString dla bot secret | PASS |
| 70 | `ZLECENIE_GLOWNE_70_REMAINING_FETCH_TIMEOUTS.md` | Objac fetchWithTimeout pozostale fetch calls w telegram_ai.js, history.js, datasheet.js, github_utils.js | TODO |
| 71 | `ZLECENIE_GLOWNE_71_CONSOLIDATE_DUPLICATE_FUNCTIONS.md` | Skonsolidowac duplikat fetchTelegramFileAsBase64 miedzy telegram_ai.js a history.js | TODO |
| 72 | `ZLECENIE_GLOWNE_72_TELEGRAM_CALLBACK_TIMEOUTS.md` | Dodac fetchWithTimeout do Telegram answerCallbackQuery, editMessageReplyMarkup i innych Telegram API fetchow | TODO |
| 73 | `ZLECENIE_GLOWNE_73_GITHUB_API_TIMEOUTS.md` | Dodac fetchWithTimeout do wszystkich GitHub API fetch calls (issues, dispatches) | TODO |

## Zadania domkniete w tej sesji

- **Z60-Z66**: Zobacz PORTFEL_14
- **Z67**: Rate limiter cleanup co 100 insertow zamiast co insert. 30k userow: 111ms (bylo 4.6s). 120/120 testow PASS.
- **Z68**: Content-Length check w Discord webhook (DISCORD_MAX_WEBHOOK_BODY_BYTES, default 5MB, 413 response).
- **Z69**: fetchWithTimeout w fetchDiscordAttachmentBase64 (30s) i createGitHubIssue (15s). timingSafeEqualString dla X-Discord-Bot-Secret.
- **Z66 (update)**: export-gate OPEN, export-all done, receipt saved.

## Zasada portfela

Testy musza byc odtwarzalne bez zewnetrznych API. fetchWithTimeout musi zachowac istniejace sygnatury funkcji. Nie wpisywac placeholderow jako realnych decyzji.
