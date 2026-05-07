# Zlecenie Glowne 67 — Discord Rate Limiter Performance Bug Fix

## 1. Misja

Naprawic performance bug w rate limiterze Discorda: cleanup O(n) skan calej mapy przy kazdym insercie powyzej 10k wpisow, prowadzacy do O(n²) przy >10k requestow w oknie rate limitu.

## 2. Read First

- `discord/discord_security.mjs`
- `docs/AGENTY_PODWYKONAWCZE/MINI_HANDOFF_ZADANIE_62.md`
- `tests/discord_rate_limiter_load_test.mjs`

## 3. Problem

Gdy `rateLimitMap.size > 10000`, kazdy insert iteruje cala mape i usuwa stare wpisy. Jesli zadne wpisy nie sa starsze niz cutoff (okno 2x rate limit), cleanup nic nie usuwa, ale skanuje 10k+ wpisow. Przy 30k unikalnych userow: 30k * O(n) skanow = O(n²), co dalo 4.6s w load tescie.

## 4. Rozwiazanie

Zamiast cleanup przy kazdym insercie powyzej 10k, zastosowano batched cleanup co 100 insertow (`CLEANUP_INTERVAL = 100`). Counter `cleanupCounter` inkrementowany przy kazdym insercie, resetowany po cleanup. Efekt: 30k userow z 111ms (zamiast 4.6s).

## 5. Acceptance Criteria

- `node --test tests/discord_rate_limiter_load_test.mjs` — 16/16 PASS
- `node --test tests/discord_bot_security_test.mjs` — 75/75 PASS
- 30k unikalnych userow < 1s (bylo 4.6s)

## 6. Zmienione pliki

- `discord/discord_security.mjs` — dodano `cleanupCounter`, `CLEANUP_INTERVAL = 100`
