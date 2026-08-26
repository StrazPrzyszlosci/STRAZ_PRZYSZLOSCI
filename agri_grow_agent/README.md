# agri_grow_agent — grow-agent na węźle edge (T28)

Poller zdarzeń uprawy dla Termux/proot (czysty Python stdlib, zero
zależności). Pobiera zdarzenia z `GET /v1/ws/events` (T22) z kursorem
i renderuje je advisory-only po polsku. **Nie wykonuje żadnych akcji
fizycznych** — pompa/dozowanie/grzałka/zawory zawsze ręcznie.

## Bezpieczeństwo

- Kill switch: istnienie pliku `~/agri_kill_switch` wstrzymuje polla.
- Token tylko w nagłówku HTTP; nigdy nie logowany, nie zapisywany w state.
- Kursor trzymany lokalnie w `.state/cursor.json` (dodane do .gitignore).

## Użycie

```bash
export AGRI_PROVIDER_ID="phone-aquaponics-observer-01"
export AGRI_PROVIDER_TOKEN="<token z /v1/providers/register>"

# pojedynczy poll:
python3 agri_grow_agent/agent.py --api-base https://<worker>.workers.dev

# pętla co 5 minut, maks. 12 cykli (Termux: uruchamiaj w termux-wake-lock):
python3 agri_grow_agent/agent.py --interval-seconds 300 --cycles 12
```

Przykład wyjścia:

```
[AUTO-W-PASMIE] ph=5.7 (below_safe_min) | akcja: buffer_dose_ph_up | tryb: manual_by_operator | human_control_point: ...
[ALARM] ph=5.3 (below_alarm) | sugerowana akcja: buffer_dose_ph_up — WYŁĄCZNIE RĘCZNIE | kill switch: gniazdo R1
```

## Testy

```bash
python3 -m unittest discover -s tests -p 'test_agri_grow_agent.py' -v
```
