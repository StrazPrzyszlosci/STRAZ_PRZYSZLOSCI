## Pack

- `pack_id`: `pack-project13-esp-runtime-01`
- `board_id`:
- `design_dossier_source`:

## Run Provenance

- `operator_kind`:
- `branch_name`:
- `command`: PLACEHOLDER — execution surface nie istnieje jeszcze
- `bench_test_command`: PLACEHOLDER

## Outputs

- [ ] `runtime_profile.json`
- [ ] `pin_map.md`
- [ ] `lua_runtime_bundle/`
- [ ] `flash_and_recovery_runbook.md`
- [ ] `bench_test_report.md`

## Board Profile Summary

- board_variant:
- flash_size:
- psram:
- antenna_condition:
- damaged_pins:

## Known Issues

-

## Integrity Notes (Wariant B)

- [ ] runtime targetuje jawnie nazwana plytke (board_id), a nie abstrakcyjne ESP32
- [ ] pin map i recovery path sa opisane przed pierwszym flash
- [ ] pack nie steruje swiatem fizycznym bez bench testu
- [ ] sekrety i credentiale nie trafiaja do firmware ani diffu
- [ ] board profile jest wypelniony z co najmniej polami POMIERZONE
- [ ] IntegrityRiskAssessment istnieje i odpowiada realnej zmianie
- [ ] ReadinessGate(integrity_ready) jest domkniety przed merge
- [ ] approver nie jest jednoczesnie glownym reviewerem
- [ ] brak self-approval