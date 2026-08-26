# agri_autopilot — komórka rolnictwa autonomicznego (T26)

Polityka autopilota uprawy dla komórek żywnościowych (akwaponika, półki
mikro-zieleni). Buduje na istniejących elementach:

- `PROJEKTY/.../pack-phone-aquaponics-observer-01` — obserwacja bez aktuacji,
- `potential_pipeline` — pętla e-waste → żywność,
- `edge_events_stream` (T22) — format zdarzeń recommendation/alarm/status.

## Pliki

| Plik | Rola |
|---|---|
| `schema.json` | Kontrakt `AgriGrowPolicy` (czujniki, pasma, advisory, limity autopilota). |
| `validate_policy.py` | Walidator blokujący: brak `physical_actuation`, spójne pasma, budżet dzienny, kill switch. |
| `evaluate_readings.py` | Deterministyczny ewaluator odczytów → zdarzenia zgodne z T22. |
| `seed_policy.json` | 2 polityki startowe: akwaponika (zielenina liściasta) + półka mikro-zieleni. |

## Klasy wykonania (`actuation_class`)

1. `advisory_only` — sugestia dla operatora, zero automatyki.
2. `edge_auto_within_safe_band` — jedyna klasa auto; wymaga `max_per_day`
   oraz globalnego budżetu `autopilot_limits.max_auto_actions_per_day`;
   działa wyłącznie poza pasmem alarmowym i nigdy na urządzeniach
   biologicznych bez potwierdzenia.
3. `requires_human_approval` — zawsze człowiek.

Zabronione jest jakiekolwiek `physical_actuation` (pompa/dozowanie/grzałka/
zawory) — zgodnie z bramkami pack-phone-aquaponics-observer-01.

## Użycie

```bash
python3 agri_autopilot/validate_policy.py
python3 agri_autopilot/evaluate_readings.py \
  --policy-id grow_policy_aquaponics_greens_01 \
  --readings '{"ph": 5.3, "air_temp_c": 27.5}' \
  --used-today 0
```

Zwrócone zdarzenia można opublikować przez `publishEdgeEvent()`
(`cloudflare/src/edge_events_stream.js`) i pobrać na węźle edge przez
`GET /v1/ws/events?provider_id=<grow_cell_id>&since_id=<cursor>`.

## Testy

```bash
python3 -m unittest discover -s tests -p 'test_agri_autopilot.py' -v
```
