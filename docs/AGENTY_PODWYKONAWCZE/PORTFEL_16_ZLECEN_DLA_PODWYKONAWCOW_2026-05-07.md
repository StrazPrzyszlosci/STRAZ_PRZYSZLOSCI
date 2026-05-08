# Portfel 16 Zlecen Dla Podwykonawcow - Zadania 70-74 + nastepne

## Cel portfela

Domknac security hardening Discord i Telegram: pozostale fetch timeouty, konsolidacja duplikatow kodu, test coverage dla Content-Length i timing-safe comparisons.

## Zadania

| ID | Plik | Cel | Status |
|----|------|-----|--------|
| 70 | `ZLECENIE_GLOWNE_70_REMAINING_FETCH_TIMEOUTS.md` | fetchWithTimeout dla pozostalych raw fetch w telegram_ai.js (datasheet scraping), worker.js, github_issues.js, recycled_catalog.js | PASS |
| 71 | `ZLECENIE_GLOWNE_71_CONSOLIDATE_DUPLICATE_FUNCTIONS.md` | Skonsolidowac duplikat fetchTelegramFileAsBase64 (telegram_ai.js -> base_utils.js, history.js/telegram_issues.js import) | PASS |
| 72 | `ZLECENIE_GLOWNE_72_TELEGRAM_CALLBACK_TIMEOUTS.md` | fetchWithTimeout dla answerCallbackQuery, editMessageReplyMarkup w telegram_issues.js | PASS |
| 73 | `ZLECENIE_GLOWNE_73_GITHUB_API_TIMEOUTS.md` | fetchWithTimeout dla createGitHubIssue (telegram_issues.js, github_issues.js) i dispatches (telegram_ai.js, recycled_catalog.js) | PASS |
| 74 | `ZLECENIE_GLOWNE_74_UNIT_TESTS_TIMING_SAFE_EQUAL_AND_413.md` | Unit testy dla timingSafeEqualString + Content-Length 413 (Discord) | PASS |

## Zadania domkniete w tej sesji

- **Z60-Z69**: Zobacz PORTFEL_15
- **Z70**: fetchWithTimeout w searchGoogleForPdf (HEAD, 15s) i fetchExternalPdfAsBase64 (GET, 30s). Pozostale fetchy w telegram_ai.js datasheet path objete timeoutem.
- **Z71**: fetchTelegramFileAsBase64 przeniesiona do base_utils.js (canon). telegram_ai.js usunal duplikat (18 linii). history.js i telegram_issues.js importuja z base_utils.js.
- **Z72**: answerCallbackQuery i editMessageReplyMarkup w telegram_issues.js juz uzywaly fetchWithTimeout (confir dr Z61).
- **Z73**: createGitHubIssue w telegram_issues.js (15s) i github_issues.js (15s). GitHub dispatch w telegram_ai.js (5s) i recycled_catalog.js (5s).
- **Z74**: 15 unit testow: 7 dla timingSafeEqualString (equal, different, diff lengths, unicode, non-string, timing-sanity, prefix-match), 8 dla checkDiscordPayloadSize (within limit, exact limit, exceeding, custom env, fallback env, missing header, zero/negative, response body). 135/135 PASS.

## Statystyki testow

Suites: 32, Testy: 135, PASS: 135, FAIL: 0.
Szybkosc rate limitera: 30k userow w 86ms (byl 4.6s).

## Zasada portfela

Testy musza byc odtwarzalne bez zewnetrznych API. fetchWithTimeout musi zachowac istniejace sygnatury funkcji. Nie wpisywac placeholderow jako realnych decyzji.
