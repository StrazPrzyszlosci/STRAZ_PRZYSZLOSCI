# Handoff dla Nastepnego Agenta - 2026-05-08 po Z75-Z77

## Cel sesji

Wdrozenie per-model rate limits dla AI providerow oraz domkniecie security hardening Z75-Z77.

## Zmiany w kodzie (Z75)

### Nowe pliki
- `cloudflare/src/ai_model_limits.js` (per-model rate limiter)

### Zmienione pliki
- `cloudflare/src/ai_providers.js`:
  - `callGoogleProvider`: `checkModelRateLimit` przed requestem, `recordModelUsage` po success
  - `callNvidiaProvider`: `checkModelRateLimit` przed requestem, `recordModelUsage` po success

### Architektura per-model rate limiter

Zapisuje usage w istniejacej tabeli `telegram_chat_limits` z prefixowanymi kluczami:
- `{platform}:model:{modelName}:5m` — 5-min RPM okno
- `{platform}:model:{modelName}:1d` — 24h RPD okno

Domyslne limity:
| Model | RPM | RPD | TPM |
|-------|-----|-----|-----|
| google/gemma-4-31b-it | 15 | unlimited | 1500 |
| gemini-3.1-flash-lite-preview | 15 | 250K tokens/day | 500 |

### Mozliwe override (env vars)

```ini
GOOGLE_GEMMA_RPM, GOOGLE_GEMMA_RPD, GOOGLE_GEMMA_TPD, GOOGLE_GEMMA_TPM
FLASH_LITE_RPM, FLASH_LITE_RPD, FLASH_LITE_TPD, FLASH_LITE_TPM
```

### Zmiana w telegram_ai.js

Ograniczone — rate limiter jest w ai_providers.js (point-of-call). Chat-level rate limit (checkTelegramChatRateLimit) nie zmieniony.

## Zmiany w kodzie (Z76)

**CLOSED/WONTFIX** — per-fetch timeout (fetchWithTimeout) juz pokrywa przypadek.

## Testy

```bash
node --test tests/discord_bot_security_test.mjs tests/discord_bot_ed25519_test.mjs tests/discord_rate_limiter_load_test.mjs tests/discord_api_handler_413_and_timing_safe_test.mjs
# Suites: 32, Tests: 135, Pass: 135, Fail: 0
```

## Decyzje

| Decyzja | Uzasadnienie |
|---------|-------------|
| Fail-open rate limiter (allowed gdy brak DB/model nieznany) | Nie blokowac chatow gdy infrastructure nieoperacyjna |
| Token tracking (TPM/TPD) NIE zaimplementowane w tej iteracji | Wymaga response token counting, dodatkowa tabela. W TODO Z78. |
| Z76 CLOSED/WONTFIX | Timeout per-fetch fetchWithTimeout wystarcza; global handler timeout ryzykuje truncation. |

## Luki pozostale

| ID | Opis | Priorytet |
|----|------|-----------|
| Z77 | Telegram webhook Content-Length testy (analogiczne do Z74) | medium |
| Z78 | Token tracking per-model (TPM/RPD) | low |
| Z79 | CORS whitelist zamiast `*` | medium |
| Z80 | CSRF tokens dla webhook handlers | low |
| Z55 | ESP runtime - real hardware bench | blocked |

## Portfel

`docs/AGENTY_PODWYKONAWCZE/PORTFEL_17_ZLECEN_DLA_PODWYKONAWCOW_2026-05-08.md`

## ZLECENIE_GLOWNE

- `docs/AGENTY_PODWYKONAWCZE/ZLECENIE_GLOWNE_75_PER_MODEL_RATE_LIMITS.md`
- `docs/AGENTY_PODWYKONAWCZE/ZLECENIE_GLOWNE_76_BOT_SECRET_TIMEOUT.md` (WONTFIX)
