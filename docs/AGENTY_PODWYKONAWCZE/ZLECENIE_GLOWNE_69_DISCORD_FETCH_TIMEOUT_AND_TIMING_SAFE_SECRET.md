# Zlecenie Glowne 69 — Discord fetchWithTimeout i Timing-Safe Secret Comparison

## 1. Misja

1. Zastosowac `fetchWithTimeout` do `fetchDiscordAttachmentBase64` i `createGitHubIssue` w Discord handlerze.
2. Zamienic `!==` porownanie secretu Discord na timing-safe porownanie (analogicznie do Telegram Z63).

## 2. Read First

- `cloudflare/src/discord_api_handler.js`
- `cloudflare/src/base_utils.js` — `fetchWithTimeout()`
- `docs/AGENTY_PODWYKONAWCZE/MINI_HANDOFF_ZADANIE_63.md`

## 3. Rozwiazanie

1. `fetchDiscordAttachmentBase64()`: zamieniono `fetch(url)` na `fetchWithTimeout(url, {}, 30000)` (30s timeout na pobieranie zalacznikow).
2. `createGitHubIssue()`: zamieniono `fetch(githubApiUrl, ...)` na `fetchWithTimeout(githubApiUrl, {...}, 15000)` (15s timeout na GitHub API).
3. Dodano `timingSafeEqualString(a, b)` — staloczasowe porownanie stringow (XOR po charcode, always-same-length loop).
4. `X-Discord-Bot-Secret` porownanie zmienione z `!==` na `timingSafeEqualString()`.

## 4. Acceptance Criteria

- `node --check cloudflare/src/discord_api_handler.js` — PASS
- Wszystkie 120 testow Discord nadal przechodza

## 5. Zmienione pliki

- `cloudflare/src/discord_api_handler.js` — import `fetchWithTimeout`, timeout w fetchDiscordAttachmentBase64 (30s) i createGitHubIssue (15s), `timingSafeEqualString()`
