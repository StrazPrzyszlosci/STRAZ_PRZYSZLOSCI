# RUNBOOK: floating-IP healthcheck + rate-limity zadań tła

Status: moduły gotowe (`background_rate_limiter.js`, `floating_ip_healthcheck.js`),
podpięcie w `worker.js` (cron `scheduled()` + endpoint admin-only) dla operatora przy deployu.

## 1. Rate-limity zadań tła

- Bramka per zadanie w oknie 1h (domyślnie maks. 6 uruchomień), klucze `bg:<zadanie>:<okno>`
  w istniejącej tabeli `telegram_chat_limits` — zero nowych migracji.
- Konfiguracja per zadanie przez env: `BG_<ZADANIE>_WINDOW_MS`, `BG_<ZADANIE>_MAX_RUNS`
  (np. `BG_PRUNE_MAX_RUNS=2`). Zadania: `kicad_import`, `verifier`, `curator`, `prune`, `lifecycle`.
- Fail-open przy awarii D1 (jak limiter globalny Z85): cron nie staje, błąd w logach.
- Gate interwałowy bez D1: `shouldRunBackgroundTask(lastRunAtMs, minIntervalMs)`.

Docelowe podpięcie w `scheduled()` (osobny commit, własny blok z markerami):
przed każdym zadaniem `checkBackgroundTaskAllowance(env.DB, "<zadanie>")` → przy
`allowed:false` pomiń zadanie i zaloguj `retry_after_seconds`.

## 2. Floating-IP healthcheck

- `checkFloatingIpHealth(fetcher, url, { timeoutMs })` — wstrzykiwalny fetcher
  (prod: `fetchWithTimeout`), nigdy nie rzuca; wynik `{healthy, reason, statusCode, latencyMs}`.
- Docelowo: cron co N minut + endpoint admin-only `GET /v1/ops/floating-ip/health`
  (sekret `X-Trust-Editor-Secret`); przy 3 kolejnych `UNHEALTHY` — alert do operatora,
  NIE automatyczny failover (actuation gate, jak kalibracja T38: człowiek decyduje).
- URL healthchecka bez tokenów; odpowiedź przycinana przed logowaniem.

## 3. Weryfikacja

```bash
node --test tests/background_rate_limiter_test.mjs tests/floating_ip_healthcheck_test.mjs
# 14 pass / 0 fail
```
