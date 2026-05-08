# Portfel 17 Zlecen Dla Podwykonawcow - Zadania 75-77 + nastepne

## Cel portfela

Wdrozyc per-model rate limits dla AI providerow (Google Gemini 3.1 Flash Lite, NVIDIA Gemma 4 31B). Domknac security hardening fetch timeoutow. Przygotowac grunt pod kolejne zadania.

## Zadania

| ID | Plik | Cel | Status |
|----|------|-----|--------|
| 75 | `ZLECENIE_GLOWNE_75_PER_MODEL_RATE_LIMITS.md` | Per-model rate limits: Gemma 4 31B (15 RPM, unlimited RPD, 1500 TPM) i Gemini 3.1 Flash Lite (15 RPM, 250K TPD, 500 TPM) | PASS |
| 76 | `ZLECENIE_GLOWNE_76_BOT_SECRET_TIMEOUT.md` | Timeout dla webhook handlers (CLOSED/WONTFIX - per-fetch timeouty juz wystarczajace) | WONTFIX |

## Zadania domkniete w tej sesji

- **Z60-Z74**: Zobacz PORTFEL_16
- **Z75**: Stworzono `cloudflare/src/ai_model_limits.js` — per-model rate limiter z fail-open (allowed gdy brak DB lub model nieznany). Wdrozono w `ai_providers.js` (callGoogleProvider, callNvidiaProvider przed request + recordModelUsage po success). RPD/TPM sledzenie przez `telegram_chat_limits` z prefixowanymi kluczami `platform:model:key:*`. Domyslne limity: Gemma 15 RPM / unlimited RPD / 1500 TPM; Flash Lite 15 RPM / 250K TPD / 500 TPM. Testy: 135/135 PASS bez regresji.
- **Z76**: N/A — per-fetch timeouty fetchWithTimeout juz pokrywaja przypadek. Global handler timeout nie dodany (truncation risk). CLOSED/WONTFIX.

## Statystyki testow

Suites: 32, Testy: 135, PASS: 135, FAIL: 0.
Szybkosc rate limitera: 30k userow w 111ms.

## Zasada portfela

Testy musza byc odtwarzalne bez zewnetrznych API. fetchWithTimeout musi zachowac istniejace sygnatury funkcji. Per-model rate limiter fail-open (allowed gdy brak DB/model nieznany).

## Zadania na pozniej

| ID | Opis | Priorytet |
|----|------|-----------|
| Z77 | Telegram webhook Content-Length testy (analogiczne do Z74 ale dla Telegrama) | medium |
| Z78 | Tracking tokenow per-model (TPM/RPD) w response zamiast request count | niski |
| Z79 | CORS allowed origins whitelist zamiast `*` (dla security) | medium |
| Z80 | CSRF tokens dla webhook handlers | low |

## Blockers

- Z55 ESP runtime: real hardware bench i maintainer signature (Canary C-1..C-5 OPEN)
