# provider_quota_monitor

Komorka monitora limitow providerow AI (T17, dawniej H2). Czyta `agent_runtime_plans/hermes_pilot/provider_matrix.json`, tworzy `quota_snapshot.json`, blokuje agent chain bez poprawnego snapshotu z `status=ok` dla kazdego providera.

## Pliki

- `snapshot.py` - generator snapshotu + walidator + blocker.
- Wyjscie domyslne: `agent_runtime_plans/hermes_pilot/quota_snapshot.json`.

## Zasady

- Brak snapshotu albo walidacja bledna => agent chain zablokowany (`blocked=true`).
- NIM 40 RPM NIE jest gwarantowany (`guaranteed=false` zawsze).
- Google AI Studio wymaga notki o aktywnych limitach projektu (`AI Studio` / `project`).
- Komorka NIE odpytuje sieci - operator uzupelnia wartosci RPM/TPM/RPD.

## Uruchomienie

```bash
python3 provider_quota_monitor/snapshot.py
python3 provider_quota_monitor/snapshot.py --block-check
```
