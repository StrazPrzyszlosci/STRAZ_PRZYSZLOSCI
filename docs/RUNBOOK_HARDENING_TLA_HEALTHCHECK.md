# Runbook: hardening tła i healthcheck (rate-limity tła + floating-IP)

## 1. Rate-limity zadań tła (`background_guard.js`)

`scheduled()` odpala 6 ciężkich zadań D1 (lifecycle, import, verify, curate,
2× pruning). Dzierżawa per zadanie (`background_leases`, single-flight):
drugie wywołanie w oknie jest **pomijane** (`backgroundSkipped` w wyniku
cronа), nie kolejkowane. Fail-open: bez D1 wszystko biegnie.

Env (domyślne, opcjonalne):

| Zmienna | Default | Znaczenie |
|---|---|---|
| `BACKGROUND_LEASE_TTL_SEC` | 600 | czas życia dzierżawy |
| `BACKGROUND_MIN_INTERVAL_SEC` | 300 | minimalny odstęp między runami zadania |

Alert: `backgroundSkipped` regularnie niepuste przy domyślnym cronie = cron
chodzi częściej niż co 5 min albo zadanie wiesza się ponad TTL — sprawdzić
logi workera, nie podbijać częstotliwości crona.

## 2. Healthcheck floating-IP (`floating_ip_health.js`, `GET /health`)

Odpowiedź (zawsze HTTP 200):

```json
{ "status": "ok", "ready": true, "db": "ok", "version": "abc123", "now": "..." }
```

- `db`: `ok` | `unconfigured` (brak bindingu D1) | `unreachable` | `unexpected_result`.
- `ready:false` przy padniętym D1 — **LB nie flapuje** (kod zawsze 200),
  monitoring ma alarmować po fladze `ready`, nie po kodzie.

Przykładowy check (Uptime Kuma / cron co 60 s):

```bash
curl -sf https://<worker>/health | python3 -c \
  "import json,sys; d=json.load(sys.stdin); sys.exit(0 if d.get('ready') else 1)"
```

## 3. Wersjonowanie deploya

Ustaw `DEPLOY_VERSION` (np. krótki hash commita) w env Workera przy
`wrangler deploy` — widać ją w `/health` i łatwiej powiązać regresje
z releasem. Bez niej `version:"dev"`.
