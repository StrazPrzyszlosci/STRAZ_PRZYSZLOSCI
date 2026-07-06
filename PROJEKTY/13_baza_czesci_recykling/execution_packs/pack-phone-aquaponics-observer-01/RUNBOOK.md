# RUNBOOK: phone-aquaponics-observer-01

## Scope

This pack turns a reused phone into an observation/reporting node for aquaponics.
It reads operator notes, photos and manual measurements, then produces a report
and questions for a human operator.

## Inputs

1. `edge_flasher` `device_profile.json` for `phone-aquaponics-observer`.
2. `edge_flasher` `install_receipt.json` with `NOT_INSTALLED` or a reviewed lab note.
3. Manual measurements such as temperature, pH, conductivity or visual condition.
4. Optional photos of plants, water surface or fish condition with provenance.

## Execution steps

1. Verify that the device profile matches `phone-aquaponics-observer`.
2. Verify that the install receipt does not claim unreviewed physical deployment.
3. Collect only observation data and operator notes.
4. Produce `aquaponics_observation_report.md` with uncertainty and missing data.
5. Produce `operator_questions.md` for decisions that require a human.
6. Produce `run_receipt.json` with inputs, timestamps, model/resource profile and artifacts.

## Out of scope

The pack must not perform physical actuation, chemical changes, feeding changes,
network exposure, firmware changes or unattended biological decisions.

## Handoff

After review, accepted reports can update a `PotentialDossier`, a resource scout
record or a future design pack. Any physical change remains blocked until explicit
human approval and food/electrical safety review.
