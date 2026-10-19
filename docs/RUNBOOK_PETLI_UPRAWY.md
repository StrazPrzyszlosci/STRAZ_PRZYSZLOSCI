# Runbook pętli uprawy (pilot T24 — instrukcja operatora)

End-to-end autonomicznej uprawy: komórka zgłasza odczyty → autopilot ocenia
→ człowiek widzi alarmy → zbiory wracają jako plon → system uczy się
(korelacja/trendy) i PROPONUJE kalibrację (człowiek merge'uje).
Żelazna zasada: **suggest-only** — nic samo nie zmienia progów ani nie
steruje fizyką (`physical_actuation` zabroniona, T26).

Legenda nagłówków (zastąp wartościami):
- `API=https://twoj-worker.workers.dev`, `ADMIN=X-Trust-Editor-Secret`,
  `TOKEN=token komórki`, `CELL=phone-aquaponics-observer-01` (przykład).

## Krok 0. Rejestracja komórki (raz)

```bash
curl -X POST "$API/v1/providers/register" -H 'Content-Type: application/json' -d '{
  "provider_id": "'"$CELL"'",
  "provider_kind": "edge_node",
  "provider_label": "Polka 1 — pilot"
}'
# -> 201 { provider_id, write_token } — TOKEN ZAPISZ W SEJFIE (env, nie repo).
```

Komórki agri nie mają segmentu środowiska w ID — przechodzą przez
`ensureAgriCellAllowed`, jeśli istnieją w politykach (krok 1). Bez polityki:
400. Token ginie? Rotacja: `POST /v1/providers/{id}/tokens/rotate`.

## Krok 1. Polityka uprawy (admin, raz + rotacja sezonowa)

```bash
curl -X POST "$API/v1/agri/policy" \
  -H "X-Trust-Editor-Secret: $ADMIN" -H 'Content-Type: application/json' -d '{
  "id": "grow_policy_aquaponics_greens_01",
  "grow_cell_id": "'"$CELL"'",
  "crop_profile": "leafy_greens_aquaponics",
  "sensors": ["ph"],
  "bands": {"ph": {"safe_min": 5.9, "safe_max": 6.5, "alarm_below": 5.5, "alarm_above": 7.0}},
  "advisories": [{"action_id": "buffer_dose_ph_up", "trigger": "ph_below_safe_min",
    "actuation_class": "edge_auto_within_safe_band", "max_per_day": 2}],
  "autopilot_limits": {"max_auto_actions_per_day": 2},
  "kill_switch": "operator_kill",
  "human_control_point": "operator_review"
}'
# -> 201. Wzór pełny: agri_autopilot/seed_policy.json + walidator:
#    python3 agri_autopilot/validate_policy.py
```

Rotacja sezonowa: nowa wersja tym samym endpointem (auto-bump `version`),
stara: `POST /v1/agri/policies/<id>/deactivate {"superseded_by": "<nowe_id>"}`.
Evaluate zawsze bierze najnowszą AKTYWNĄ dla komórki.

## Krok 2. Agent na telefonie/Termuxie (nasłuch alarmów)

```bash
export AGRI_API_BASE="$API" AGRI_PROVIDER_ID="$CELL" AGRI_PROVIDER_TOKEN="$TOKEN"
python3 agri_grow_agent/agent.py --interval-seconds 300
# Kill switch (natychmiastowe wstrzymanie): touch ~/agri_kill_switch
# Stan/kursor: agri_grow_agent/.state/cursor.json. Token NIGDY w logach.
```

Ręczny podgląd strumienia: `GET /v1/ws/events?provider_id=$CELL&since_id=0&limit=50`
(nagłówek `X-Provider-Token`). Rodzaje: `[ALARM] / [SUGESTIA] / [AUTO-W-PASMIE] / [INFO]`.

## Krok 3. Telemetria (czujniki → staging, cyklicznie)

```bash
printf '%s\n' \
 '{"sensor":"ph","value":6.1,"recorded_at":"2026-10-02T10:00:00.000Z"}' \
 '{"sensor":"ph","value":6.3,"recorded_at":"2026-10-02T11:00:00.000Z"}' \
| curl -X POST "$API/v1/agri/telemetry?provider_id=$CELL" \
  -H "X-Provider-Token: $TOKEN" --data-binary @-
# -> 202. Limity: 5000 linii / 64KB na linię; duplikaty odrzucane (checksum).
# Agregaty dzienne avg/min/max lądują w automation_metrics (dashboard w kroku 6).
```

## Krok 4. Evaluate (odczyty → zdarzenia, na żądanie lub po telemetrii)

```bash
curl -X POST "$API/v1/agri/evaluate" \
  -H "X-Provider-Token: $TOKEN" -H 'Content-Type: application/json' -d '{
  "grow_cell_id": "'"$CELL"'", "readings": {"ph": 5.3}}'
# -> 200 { events: [...] } — zdarzenia widać też w /v1/ws/events.
# Budżet: max_auto_actions_per_day na (polityka, komórka, dzień); po wyczerpaniu
# fallback manualny (operator). Akcje auto TYLKO w paśmie safe.
```

## Krok 5. Zbiór (plon → ledger, po każdym ważeniu)

```bash
curl -X POST "$API/v1/agri/harvest?provider_id=$CELL" \
  -H "X-Provider-Token: $TOKEN" -H 'Content-Type: application/json' -d '{
  "crop_profile": "leafy_greens_aquaponics", "mass_g": 420.5,
  "harvested_at": "2026-10-02T12:00:00.000Z",
  "quality_note": "dobre liscie", "source": "operator_anna"}'
# -> 202. Duplikat (ten sam zbiór) -> 409. mass_g w (0, 1e6], data ISO (max +5 min).
```

## Krok 6. Odczyt pętli (dashboard + nauka, po 2–3 miesiącach danych)

```bash
# Metryki (admin): telemetria + zużycie autopilota
curl "$API/v1/agri/metrics" -H "X-Trust-Editor-Secret: $ADMIN"
# Korelacja plon<->warunki (token): które pasma dawały plon (r per czujnik)
curl "$API/v1/agri/correlation?provider_id=$CELL&months=6" -H "X-Provider-Token: $TOKEN"
# Trendy plonów (token): serie miesięczne + regresja per profil
curl "$API/v1/agri/harvest/trends?provider_id=$CELL&months=12" -H "X-Provider-Token: $TOKEN"
# W bocie: !agri-metrics — panel operatorski (Discord/Telegram).
```

Bez 2+ miesięcy danych wykresy puste — to normalne, nie błąd.

## Krok 7. Kalibracja (sugestia → review → draft-PR → człowiek merge'uje)

```bash
# Podgląd diff (admin, read-only): stare->nowe pasmo + gotowe body PR
curl -X POST "$API/v1/agri/calibration-suggest" \
  -H "X-Trust-Editor-Secret: $ADMIN" -H 'Content-Type: application/json' -d '{
  "grow_cell_id": "'"$CELL"'", "months_back": 6}'
# W bocie: !calibration preview <policy_id>  (podgląd, zero zapisów)
# W bocie: !calibration apply <policy_id> [reviewer]  (draft-PR, no_auto_merge)
```

Bot NIGDY nie merge'uje. PR scala człowiek po przeczytaniu diff
(pamiętaj: korelacja != przyczynowość). Komenda onboardingowa:
`!grow-agent setup <cell>` (drukuje instrukcję z kroku 2, bez tokenu).

## Troubleshooting

| Objaw | Znaczenie / akcja |
|---|---|
| 400 `Drugi segment provider_id...` | komórka spoza `agri_grow_policies` — wróć do kroku 1 (polityka = rejestr komórek) |
| 401 | zły `X-Provider-Token` / `X-Trust-Editor-Secret`; token po rotacji wymienić w env agenta |
| 403 | ID z segmentem env spoza allowlisty (`ALLOWED_PROVIDER_ENVIRONMENTS`) |
| 404 | brak polityki dla komórki (evaluate) / brak providera (token) |
| 409 | duplikat zbioru (ten sam checksum) — OK, nic nie rób |
| 429 | rate-limit (globalny lub per provider) — poczekaj na `Retry-After` |
| Puste trendy/korelacja | za mało miesięcy danych — kontynuuj kroki 3–5 |
| Agent milczy | sprawdź `~/agri_kill_switch` (usuń by wznowić), kursor w `.state/`, token w env |

## Co po pilocie

- Rotacja sekretów: `docs/RUNBOOK_ROTACJI_SEKRETOW.md` (co 90 dni).
- Seed approvals wygasają 31.12.2026 — odnowić przed pilotem ciągłym.
- Cron Workera (02:17) robi retencję i łańcuch KiCad — zweryfikować na prod D1.
- Wszystkie env dzielą jedno D1 — metryki demo/prod się mieszają (do rozdzielenia).
