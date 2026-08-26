# Handoff dla Następnego Agenta - po T27 T28 T29 T30 - 2026-08-26 (cykl 2)

## Kontekst wejściowy

Przeczytano ostatni handoff: `docs/HANDOFF_DLA_NASTEPNEGO_AGENTA_2026-08-26_PO_T21_T26_AUTONOMOUS_AGRI.md` (T21–T23, T25, T26 DONE). Priorytety wejściowe: T27 (pętla agri evaluate→events, P1), T28 (grow-agent edge, P2), T29 (telemetria czujników, P3), T30 (GitHub webhook sync, P4). Operator powtórzył cykl — tura realizuje dokładnie te 4 zadania w kierunku rolnictwa autonomicznego.

## Co zrobiono

### T27 — DONE: Zamknięcie pętli rolniczej (evaluate → events)

- Migracje D1: `20260826000003-agri-grow-policies`, `20260826000004-agri-grow-policies-cell-index`, `20260826000005-agri-autopilot-usage` (`schema_migrations.js`).
- `cloudflare/src/agri_evaluate.js` — port logiki `agri_autopilot/evaluate_readings.py` na JS (Worker nie uruchamia Pythona): `validateAgriPolicyRecord()` (odrzucanie `physical_actuation`), `upsertAgriPolicy()`, `getAgriPolicy()`, `evaluateAgriReadings()` (parzystość fixture z wersją Python), budżet dzienny **liczony serwerowo** w `agri_autopilot_usage` (klucz `policy_id|YYYY-MM-DD`).
- Endpointy: `POST /v1/agri/policy` (admin, X-Trust-Editor-Secret) i `POST /v1/agri/evaluate` (auth tokenem providera = grow_cell_id; zdarzenia publikowane przez `publishEdgeEvent` → widoczne na `/v1/ws/events`).
- `tests/agri_evaluate_test.mjs` — 5 testów (w tym pełna pętla: upsert → evaluate ×7 → budżet wyczerpany → fallback manualny).

### T28 — DONE: Grow-agent edge (Termux/proot, advisory-only)

- Nowa komórka `agri_grow_agent/`: `agent.py` (czysty stdlib) — poll `GET /v1/ws/events?provider_id=&since_id=&limit=` z kursorem w `.state/cursor.json` (.gitignore), render PL: `[ALARM]` / `[SUGESTIA]` / `[AUTO-W-PASMIE]` / `[INFO]`; kill switch plik `~/agri_kill_switch` wstrzymuje poll; token tylko w nagłówku, nigdy nie logowany (HTTP error bez wycieku tokenu). Zero aktuatorów.
- Manifest `agri_edge_agent` w seed (**11 komórek**) + aktualizacja `EXPECTED_CELL_IDS`/`EXPECTED_DIRS`.
- `tests/test_agri_grow_agent.py` — 10 testów.

### T29 — DONE: Telemetria czujników (batch NDJSON → staging + agregaty B4)

- Migracje D1: `20260826000006..09` — `sensor_readings_staging` (UNIQUE dedup checksum), indeksy, ledger `sensor_telemetry_events`.
- `cloudflare/src/sensor_telemetry.js` — kontrakt NDJSON (sensor `[a-z0-9_]+`, value liczba, recorded_at ISO; opcjonalne unit/source/provenance); dedup SHA-256(provider|sensor|ts|value); audit event per batch; agregaty dzienne avg/min/max per sensor do `automation_metrics` (window='daily', rekompute przy każdym batchu dotykającym sensora).
- Endpoint `POST /v1/agri/telemetry?provider_id=` (auth tokenem providera; provider nadpisywany z query — spoofing w liniach ignorowany).
- `tests/sensor_telemetry_test.mjs` — 4 testy.

### T30 — DONE: GitHub webhook sync statusów execution_packs

- `cloudflare/src/execution_pack_webhook.js` — `verifyWebhookSignature()` (HMAC SHA-256 + `timingSafeEqualString` z base_utils), `mapPullRequestAction()` (tylko action=closed: merged=false→'closed', merged=true→'merged'; reszta ignorowana), `findExecutionPackByPr()`, `syncExecutionPackFromWebhook()` (ledger append; reviewer=`github:<login>` człowieka, który kliknął merge/close; `skipGithubClose` — brak ponownego PATCH do GitHub).
- `execution_pack_initiator.js`: dodana opcja `skipGithubClose` w `updateExecutionPackStatus`.
- Endpoint `POST /v1/integrations/github/webhook` (env `GITHUB_WEBHOOK_SECRET`; brak konfiguracji → 503; złwy podpis → 401).
- `tests/execution_pack_webhook_test.mjs` — 6 testów.

## Testy wykonane

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
# Ran 313 tests in ~2.9s — OK (było 303, +10 grow agent)

# mjs: wszystkie tests/*.mjs przez node --test
# pass=307 fail=0 (było 292, +15: agri_evaluate 5 + telemetry 4 + webhook 6)

python3 agentic_cells/validate_cell_manifest.py   # OK: 11 manifest(s) valid
bash .githooks/pre-commit                          # OK
node --check cloudflare/src/{worker,agri_evaluate,sensor_telemetry,execution_pack_webhook}.js  # SYNTAX OK
```

## Status backlogu

| Zadanie | Status | Opis |
|---|---|---|
| T1–T26 | DONE | Patrz handoff PO_T21_T26_AUTONOMOUS_AGRI. |
| T27 | DONE (ta tura) | POST /v1/agri/policy + /v1/agri/evaluate; budżet serwerowy; publikacja do streamu T22. |
| T28 | DONE (ta tura) | agri_grow_agent: poller edge advisory-only z kursorem i kill switchem. |
| T29 | DONE (ta tura) | Telemetria NDJSON: staging + dedup + audit + agregaty dzienne do automation_metrics. |
| T30 | DONE (ta tura) | GitHub PR webhook → ledger execution_packs (HMAC timing-safe, bez merge). |
| T24 | ODOCZONE | Realny checkout CERN S1, hardware S6, proot/BLE na fizycznym sprzęcie. |
| T31 | NEXT / P1 | Retencja edge_event_stream (pruning/cap per provider) + expiry-renewal pipeline dla approvals. |
| T32 | OPEN / P2 | Dashboard metryki upraw: GET /v1/agri/metrics (agregaty dzienne + zużycie autopilota) dla maintainera. |
| T33 | OPEN / P3 | Wiele polityk per grow_cell + rotacja sezonowa (versioning polityk w D1). |
| API/worker hardening | OPEN | background-rate-limity, floating-ip healthchecks, secret-rotation. |

## Następne zadania

### T31 — PRIORYTET 1: Retencja streamu + renewal approvals

`edge_event_stream` rośnie bez limitu (T22/T27 piszą coraz więcej); zaplanować scheduled pruning (np. keep N dni lub cap M per provider). Drugi element ryzyka z poprzedniej tury: seedy approvals wygasają (ostatnio ratowane ręcznie) — pipeline/handoff-checker ostrzegający 30 dni przed expiry.

### T32 — PRIORYTET 2: Metryki upraw dla operatora

Read-only endpoint `/v1/agri/metrics` (X-Trust-Editor-Secret): dzienne agregaty czujników (już w automation_metrics od T29) + licznik użyć autopilota per policy/day. Ewentualnie komenda `/agri-metrics` Discord/Telegram wzorem `/metrics` (B4).

### T33 — PRIORYTET 3: Versioning polityk uprawy

Jedna polityka na grow_cell to za mało na rotację sezonową; dodać `superseded_by`/aktywne wersje w `agri_grow_policies` i wybór aktywnej przy evaluate.

## Kierunki rozwoju (analiza repo po 2 cyklach agri)

1. **Pętla agri jest już domknięta technicznie**: czujnik → `/v1/agri/telemetry` (T29) → `/v1/agri/evaluate` (T27) → `/v1/ws/events` (T22) → grow-agent na telefonie/ESP (T28) → człowiek. Brakuje tylko danych rzeczywistych: podłączyć 1 fizyczną półkę (T24-operator) i uruchomić pilot 2 tygodni.
2. **Dane historyczne = wartość**: agregaty dzienne w automation_metrics to fundament pod trend-y wzrostu; kolejny krok to korelacja odczytów z plonem (prosty rekord harvestu per grow_cell) — dopiero to zamienia monitoring w „autonomiczne rolnictwo" z pętlą uczenia.
3. **KiCad chain czeka na dane**: ingestion endpoint gotowy (T21), verifier/curator działają — realny checkout CERN (S1) odblokuje 17k komponentów jednorazowo.
4. **Hermes cykliczność**: queue T18 dalej staged; pierwsze `repo_scout_daily` skróci cykle tur. Rozważyć uruchomienie przez GitHub Actions cron zamiast lokalnego Termuxa (deterministyczność).
5. **Bezpieczeństwo operacyjne**: retencja streamu (T31), secret-rotation runbook, healthcheck floating-ip — trzy najtańsze uszczelnienia przed publicznym pilotem wolontariuszy.

## Zasady (konwencja bez zmian)

1. `PO_T<n>_T<m>_<OPIS>.md`, pipeline liniowy, ≤5 wykonanych zadań na turę.
2. Nowa komórka ⇒ manifest + aktualizacja `EXPECTED_CELL_IDS`/`EXPECTED_DIRS` (inaczej T25 CI blokuje).
3. Testy obowiązkowe z liczbami: Python discover (obecnie **313**) + wszystkie `tests/*.mjs` (obecnie **307**).
4. High-risk/biologia = actuation gate; `physical_actuation` niedostępna; bot nigdy nie merge'uje.
5. Sekrety tylko env Workera; webhooki zawsze HMAC/timing-safe.

## Ryzyka

- **Zbiorczy commit nadal oczekuje**: zmiany z obu tur (T21–T30) leżą w working tree — review operatora przed commitem (zgodnie z no_direct_push).
- `edge_event_stream` bez retencji (pilnuje T31); `sensor_readings_staging` analogicznie będzie rósł z telemetrią.
- Budżet autopilota jest per policy/day globalnie — przy wielu instancjach tej samej polityki (różne grow_cells) rozdzielić licznik per cell (T33).
- `GITHUB_WEBHOOK_SECRET` i polityki agri to nowe sekrety/konfiguracja do wpisania w wrangler przy deployu.

## Referencje zewnętrzne (do podglądu w kolejnych turach)

- `KnowFlow/KnowFlow_AWM`, `pkErbynn/IoT-WQMS` — progi jakości wody vs nasze pasma akwaponiki (możliwa kalibracja seed_policy).
- `espressif/esp-claw` — runtime edge; grow-agent docelowo może mieć wariant ESP-IDF/Lua obok Termuxa.
- `gnarzilla/deadmesh` (Meshtastic/LoRa) — transport dla pól bez WiFi; `/v1/ws/events` polling dobrze się kompresuje do LoRa payloadów.
