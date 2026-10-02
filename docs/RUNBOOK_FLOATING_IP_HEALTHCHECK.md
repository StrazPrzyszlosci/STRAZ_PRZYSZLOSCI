# RUNBOOK: floating-IP healthcheck + rate-limity zadań tła

Stan: moduły gotowe, NIEPODPIĘTE w `worker.js` (celowo — podpięcie przy `wrangler deploy`,
decyzja operatora). Ten runbook mówi jak je włączyć i jak czytać sygnały.

## 1. Po co to jest

- Bez healthchecka floating-IP milcząco wypada z rotacji: ruch idzie w próżnię,
  a cron/retencja T31 i webhooki B5/T23/T30 milkną bez jednego loga.
- Bez limiterów tła zawieszony cron albo podwójny trigger potrafi zwielokrotnić
  obciążenie D1 (import KiCad, verifier, curator, pruning T31, lifecycle).

## 2. Moduły (read-only, testowane)

| Moduł | Plik | Testy |
|---|---|---|
| Bramka tła per zadanie (D1, fail-open) | `cloudflare/src/background_rate_limiter.js` | `tests/background_rate_limiter_test.mjs` |
| Healthcheck floating-IP (fail-safe, nigdy nie rzuca) | `cloudflare/src/floating_ip_healthcheck.js` | `tests/floating_ip_healthcheck_test.mjs` |
| Strażnik lease single-flight | `cloudflare/src/background_guard.js` | `tests/background_guard_test.mjs` |

Limity tła używają ISTNIEJĄCEJ tabeli `telegram_chat_limits` (klucze `bg:…`) —
zero nowych migracji D1 (wzór limitera globalnego Z85).

## 3. Konfiguracja (env Workera)

```bash
# Limiter globalny per zadanie (nadpisywalne per task: BG_<TASK>_WINDOW_MS / BG_<TASK>_MAX_RUNS,
# gdzie <TASK> to nazwa zadania upper-snake, np. BG_KICAD_IMPORT_WINDOW_MS)
BG_DEFAULT_WINDOW_MS=3600000   # domyślnie 1h
BG_DEFAULT_MAX_RUNS=6           # domyślnie 6 uruchomień / okno

# Healthcheck: URL-e po przecinku konfigurowane przy deployu (BEZ tokenów w URL!);
# timeout: FLOATING_IP_HEALTH_TIMEOUT_MS (default 10000, min 1000)
```

Sekrety (tokeny GitHub/providerów) rotować wg `docs/RUNBOOK_ROTACJI_SEKRETOW.md` —
URL-e healthchecka NIGDY nie zawierają sekretów (moduł ucina body do 2000 znaków
i nie loguje nagłówków).

## 4. Podpięcie w `scheduled()` (szkic dla operatora, NIE aplikować zdalnie)

```js
import { checkBackgroundTaskAllowance } from "./background_rate_limiter.js";
import { checkFloatingIpHealth, formatFloatingIpHealthSummary } from "./floating_ip_healthcheck.js";
import { fetchWithTimeout } from "./base_utils.js";

// Na początku scheduled():
const gate = await checkBackgroundTaskAllowance(env.DB, "nightly_kicad_import");
if (!gate.allowed) {
  console.log(`[cron] skip nightly_kicad_import: ${gate.reason}, retry za ${gate.retry_after_seconds}s`);
  return;
}
// Osobny lekki cron lub koniec scheduled():
const health = await checkFloatingIpHealth(
  (url, opts, ms) => fetchWithTimeout(url, opts, ms),
  env.FLOATING_IP_HEALTH_URL
);
console.log(formatFloatingIpHealthSummary(health));
// health.healthy === false → alert do operatora (Discord/Telegram), NIE auto-failover:
// przełączenie IP to decyzja człowieka (actuation gate).
```

## 5. Interpretacja sygnałów

- `background_rate_limited` + `retry_after_seconds` — zdrowy objaw (bramka działa); jeśli
  permanentnie, zwiększ `BG_<TASK>_MAX_RUNS` albo podziel zadanie.
- `db_error` / `no_db` — bramka OTWARTA (fail-open): cron leci dalej. Sprawdź D1.
- `healthy:false reason=http_XXX` — backend za floating-IP odpowiada błędem HTTP.
- `healthy:false reason=payload_down|unexpected_body` — HTTP 200, ale treść zła (fałszywy OK).
- `healthy:false reason=fetch_error` — IP nieosiągalne / timeout → kandydat do rotacji.

## 6. Czego NIE robi automatyzacja (bramki)

- Bot/agent NIGDY nie przełącza floating-IP sam (actuation gate, decyzja operatora).
- Healthcheck NIGDY nie rzuca wyjątkami (zwraca `unhealthy` — monitoring ma świecić, nie padać).
- Limiter NIGDY nie blokuje przy awarii D1 (fail-open — cron nie staje).
