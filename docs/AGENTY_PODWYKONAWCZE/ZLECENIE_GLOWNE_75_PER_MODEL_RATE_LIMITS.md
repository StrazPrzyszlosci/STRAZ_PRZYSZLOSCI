# ZLECENIE GLOWNE 75 - Per-Model Rate Limits (Gemma 4 31B, Gemini 3.1 Flash Lite)

## Cel

Wdrożyc per-model rate limits dla dwoch AI providerow:
- **Google Gemma 4 31B** (NVIDIA NIM - "Other models"): 15 RPM, unlimited RPD, 1500 tokens/min
- **Gemini 3.1 Flash Lite** (Google AI Studio - "Text-out models"): 15 RPM, 250K tokens/day, 500 tokens/min

## Luki

Brak rozroznienia rate limitow miedzy modelami - obecnie tylko global `TELEGRAM_AI_REQUESTS_PER_5_MIN` i `TELEGRAM_AI_REQUESTS_PER_DAY` per chat, bez sledzenia limitow per model.

## Rozwiazanie

Stworzono modul `cloudflare/src/ai_model_limits.js`.

### Architektura

Nowy modul reuzywajacy tabeli `telegram_chat_limits` (istniejaca) z prefixowanymi kluczami:
- `{platform}:model:{modelKey}:5m` — 5-minutowe okno RPM
- `{platform}:model:{modelKey}:1d` — 24-godzinne okno RPD/tokens/day

### Funkcje exportowane

- `checkModelRateLimit(env, db, model, platform)` — sprawdza limit przed requestem AI
- `recordModelUsage(env, db, model, platform)` — zapisuje usage po successful response
- `DEFAULT_MODEL_LIMITS` — konfiguracja domyslna dla kazdego modelu

### Wdrozenie w ai_providers.js

- `callGoogleProvider`: przed requestem `checkModelRateLimit()` z modelem Google
- `callNvidiaProvider`: przed requestem `checkModelRateLimit()` z modelem NVIDIA
- Po successful response: `recordModelUsage()` dla obslugi analytics

### Konfiguracja env (wrangler.toml)

Brak nowych zmiennych env — domyslne wartosci z `DEFAULT_MODEL_LIMITS`. Mozliwe override:
- `GOOGLE_GEMMA_RPM`, `GOOGLE_GEMMA_RPD`, `GOOGLE_GEMMA_TPD`, `GOOGLE_GEMMA_TPM`
- `FLASH_LITE_RPM`, `FLASH_LITE_RPD`, `FLASH_LITE_TPD`, `FLASH_LITE_TPM`

## Statystyki

- Nowy plik: `cloudflare/src/ai_model_limits.js` (~250 linijek)
- Zmieniony: `cloudflare/src/ai_providers.js` (dodano import i calli do checkModelRateLimit/recordModelUsage)
- Testy: 135/135 PASS (bez regresji)

## Zasady

- Jesli model nieznany — `allowed: true` (fail-open na bezpieczenstwo)
- Jesli `env.DB` nie istnieje — `allowed: true` (fail-open)
- Tokeny (TPM/RPD) NIE sa sledzone w tej implementacji — wymagaloby counting tokenow w response, co jest todo na pozniej
