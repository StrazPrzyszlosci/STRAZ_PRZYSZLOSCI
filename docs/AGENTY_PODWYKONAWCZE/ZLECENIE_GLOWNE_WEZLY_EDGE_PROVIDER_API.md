# ZLECENIE GŁÓWNE — Węzły Edge Provider API w D1

## Cel

Zstandaryzować sposób integracji węzłów edge (stare smartfony z proot + straz-edge-installer) z centralną warstwą API Straży w D1. Każdy smartfon-węzeł = jeden `provider_id` w D1, wysyłający observations/events przez `write_token`.

## Powiązania

- `docs/ROADMAPA_WEZLOW_EDGE.md` — roadmapa edge.
- `docs/ARCHITEKTURA_EDGE_SMARTFONY_CLOUD.md` — architektura bramek edge.
- `docs/MAPOWANIE_ENCJI_ORGANIZACJI_DO_D1_I_SQLITE.md` — encje w D1.
- `cloudflare/src/worker.js` — istniejące API: `/v1/providers/register`, `/v1/observations`, `/v1/events`, `/v1/providers/<id>/tokens/rotate`.
- `straz-edge-installer/scripts/nsip-client.sh` — klient (gotowy, Q5).

## Kontrakt API (już istnieje w worker.js, spec dla dalszych ulepszeń)

### POST /v1/providers/register
Registers a node as provider. Request:
```json
{
  "provider_id": "straz-edge:<hostname>:węzeł-nazwa",
  "provider_name": "węzeł-nazwa",
  "description": "Straz Edge node (smartfon proot)",
  "schema_version": "v1",
  "provider_environment": "prod"|"demo"|"local",
  "capabilities": ["observations", "events", "gpio-control"]
}
```
Response 201: `{provider_id, write_token, registration_status, schema_version}`.
Token rotowalny przez `POST /v1/providers/<id>/tokens/rotate` (Bearer token).

### POST /v1/observations
```json
{
  "provider": {"provider_id":"straz-edge:...", "provider_environment":"prod"},
  "pond": {"pond_id":"default-node"},
  "kind": "observation",
  "metric": "temp",
  "value": 24.1,
  "unit": "C",
  "measurement_time": "2026-07-05T12:00:00Z"
}
```
Response 202: `{status:"accepted", provider_id, pond_id}`. Token w Authorization Bearer.

### POST /v1/events
```json
{
  "provider": {"provider_id":"straz-edge:...", "provider_environment":"prod"},
  "pond": {"pond_id":"default-node"},
  "kind": "event"|"decision",
  "event_type": "pump_on",
  "details": "gpio 12=1 by maintainer-01",
  "reviewed_by": "maintainer-01" (if kind=decision),
  "event_time": "2026-07-05T12:05:00Z"
}
```
Response 202. Decisions wymagają `reviewed_by` (patrz roadmapa edge, gate).

## Planowane rozszerzenia — status realizacji (aktualizacja 2026-07-05)

### A. Rate limit / throttling — DONE (commit 309ec98)
Jeśli provider wysyła >`PROVIDER_MAX_RPM` (default 30, konfigurowalny) events/min, API throttluje i zwraca `429 Too Many Requests` z `Retry-After`. `<=0` wyłącza limit (allow-all). Implementacja: `cloudflare/src/provider_rate_limiter.js` (token bucket per provider_id, współdzieli tabelę `telegram_chat_limits` z prefiksem `pr:`). Middleware w `worker.js` dla `/v1/observations`, `/v1/events`, `/v1/providers/<id>/heartbeat`. Fail-open po błędzie D1. 8 testów PASS (`tests/provider_rate_limiter_test.mjs`).

### B. Offline bufor / retry — DONE (commit 42b6618)
W `nsip-client.sh`: błąd sieci (NETERR: timeout/DNS/TLS) → payload trafia do `${SPOOL_DIR}/*.jsonl` (chmod 0600, dir 0700). `nsip-client flush` ponawia z exponential backoff (2^(n-1)s, max 16s), drop po `SPOOL_MAX_RETRIES`. Błąd HTTP 4xx/5xx (HTTPERR) NIE spooluje (retry bez sensu). Cyber: `load_env` biała-lista kluczy + obcinanie cudzysłowów (anti-injection via provider.env). `prod` wymaga `https://` API URL (token w plain HTTP = podsłuch). `register`/`observe`/`event` — python argv (anti-apostrof injection). `rotate` — python regex (anti-sed-injection). `status` — python urllib z Bearer. 8 cyber-testów PASS.

### C. Heartbeat + provider_status endpoint — DONE (commit 309ec98 + 42b6618)
- `POST /v1/providers/<id>/heartbeat` — updates `last_seen_at` + zwraca `trust_level`. Gate rate-limit (429). Implementacja: `worker.js`.
- `nsip-client heartbeat [interval]` (min 5s) — pętla: flush spoolu + POST heartbeat. Implementacja: `nsip-client.sh`.
- `GET /v1/providers/<id>/status` — istniał (curl), zaktualizowany do python urllib + Bearer token (cyber: autoryzacja).
- Auto-deactivate >72h: TODO (wskazane w roadmapie H3).

### D. Provider trust_level + decision gate — DONE (commit 309ec98)
Każdy provider ma `trust_level` INTEGER (0 = unverified, domyślne). `kind=decision` events wymagają `trust_level >= PROVIDER_DECISION_TRUST_LEVEL` (default 2). Endpoint `PATCH /v1/providers/<id>/trust-level` z `X-Trust-Editor-Secret` (maintainer-only). `validateTrustLevel` 0-10. 8 testów PASS (`tests/provider_trust_level_test.mjs`). `validateEvent` akceptuje opcjonalne pole `kind` (default `telemetry`).

### E. Węzeł-as-service: WebSocket events stream — OPEN
Opcjonalnie: `/v1/ws/events?provider_id=<id>` — provider odbiera push events z centrali (rekomendacje, alarmy) przez WebSocket, bez polling. Sakrane dla H3 roadmapy (węzły edge jako providery).

## Kryteria odbioru (dla implementatora)

1. Węzeł z `nsip-client register` → otrzymuje `provider_id` i `write_token`, zapisuje do `provider.env` (0600).
2. `nsip-client observe '{"metric":"heartbeat","value":1}'` → API zwraca `{status:"accepted"}`.
3. `nsip-client rotate-token` → nowy token zapisany do provider.env, stary odrzucany przez API.
4. Provider_env nie committowany do repo (0600, wykluczony z git).
5. Throttling jeśli >60 events/min (rate_limited status), retry backoff.
6. Test na smartfonie z proot — rejestracja rzeczywistego providera.

## Decyzje bezpieczeństwa

- `write_token` trzymany w `provider.env` (chmod 0600), NIGDY w repo.
- Rotacja tokena nie zmienia `provider_id` — zachowujemy historię.
- Provider_id zawiera environment slug (`straz-edge:hostname-name:prod`) — API sprawdza czy environment jest dopuszczony w deploymencie (już w worker.js).
- Decisions z `kind=decision` muszą mieć `reviewed_by` — gate przed autonomicznym sterowaniem GPIO.

## Status

DONE (2026-07-05) jako spec + realizacja A/B/C/D (commity 309ec98, 42b6618, b8c224a dla parsera Z87 wspierajacego import dla H2).
Klient `nsip-client.sh` — gotowy (Q5 + cyber hardening S2-B). API `/v1/providers/register`, `/v1/observations`, `/v1/events`, `/v1/providers/<id>/heartbeat`, `/v1/providers/<id>/trust-level` (PATCH, maintainer) — zaimplementowane w `cloudflare/src/worker.js`.
Rozszerzenia E (WebSocket) — OPEN, dla H3 roadmapy.