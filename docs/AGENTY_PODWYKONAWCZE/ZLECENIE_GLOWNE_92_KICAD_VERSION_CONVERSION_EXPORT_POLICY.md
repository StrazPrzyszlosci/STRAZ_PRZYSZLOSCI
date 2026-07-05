# ZLECENIE GŁÓWNE 92 - Polityka konwersji wersji KiCad jako etap eksportu

## Cel

Opisać i przetestować kiedy używać KiCad Version Converter albo `kicad-cli` w workflow NSIP.

## Decyzja bazowa

Nie konwertować całej biblioteki CERN przed ingestem. Konwersja jest etapem eksportu/kompatybilności projektu.

## Kryteria odbioru

- Runbook z przypadkami: KiCad 9.x -> 10.x, legacy project -> aktualny workflow, eksport dla użytkownika.
- Test na minimalnym projekcie przykładowym, nie na pełnej bibliotece CERN.
- Jasne oznaczenie ryzyk utraty informacji przy konwersji.

## Status

DONE (2026-07-05) — `docs/KICAD_VERSION_CONVERSION_EXPORT_POLICY.md`.
Decyzja bazowa: konwersja to downstream export, nie przed ingestem. Runbook A-D, test na fixture NE555, ryzyka zinwentaryzowane. Reguły dla NSIP: provenance konserwowana, eksporter może opcjonalnie konwertować z `--target-version`.
