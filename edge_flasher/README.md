# Edge Flasher Wizard Scaffold

`edge_flasher/` is a suggest-only scaffold for turning selected `PotentialDossier`
products into auditable edge-device preparation artifacts.

It does **not** flash firmware, deploy software, expose network services, control
actuators, or approve physical installation. Every profile must list allowed
low-risk actions, blocked high-risk actions, and human-approval gates.

## Profiles

- `phone-aquaponics-observer` — reused phone as an observation/reporting node for food loops.
- `recycle-bench-catalog-station` — local bench station for cataloging recovered parts.
- `phone-sensor-gateway` — reused phone as an offline-first sensor observation gateway.

## Generated artifacts

```bash
python3 edge_flasher/generate_artifacts.py \
  --profile phone-aquaponics-observer \
  --output-dir /tmp/phone-aquaponics-observer
```

The command writes:

- `device_profile.json`
- `install_receipt.json`
- `bench_test_report.md`
- `rollback.md`

All generated receipts default to `NOT_INSTALLED` and
`MISSING_HUMAN_APPROVAL`.
