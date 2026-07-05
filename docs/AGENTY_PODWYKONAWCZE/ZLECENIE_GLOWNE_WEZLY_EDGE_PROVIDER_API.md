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

## Planowane rozszerzenia (zlecenie dla implementatora)

### A. Rate limit / throttling
Jeśli provider wysyła >60 events/min, API throttluje i zwraca `429 Too Many Requests`. Provider otrzymuje `rate_limited` status i retry-after. New table `provider_rate_limit` z TTL.

### B. Offline bufor / retry
W `nsip-client.sh`: jeśli observation rejected lub network error, buffor do `/sdcard/NSIP/observations/rejected.jsonl`. Retry z exponential backoff (1m, 2m, 5m, 10m).

### C. Heartbeat + provider_status endpoint
- `POST /v1/providers/<id>/heartbeat` — updates `last_seen_at` (już w schemacie).
- `GET /v1/providers/<id>/status` — zwraca status providera (active, rate_limited, blocked).
- Auto-deactivate jeśli brak heartbeat przez >72h.

### D. Provider trust_level + decision gate
Każdy provider ma `trust_level` (0 = unverified, 2 = auto-decision allowed). Tylko provider_z trust_level >= 2 może wysyłać `kind=decision` events.

### E. Węzeł-as-service: WebSocket events stream
Opcjonalnie: `/v1/ws/events?provider_id=<id>` — provider odbiera push events z centrali (rekomendacje, alarmy) przez WebSocket, bez polling.

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

DONE (2026-07-05) jako zlecenie spec. Implementacja: A/B/C/D/E do wykonania przez implementatora w kolejnej sesji. Klient `nsip-client.sh` gotowy (Q5). API `/v1/providers/register`, `/v1/observations`, `/v1/events` już istnieje w `cloudflare/src/worker.js`.