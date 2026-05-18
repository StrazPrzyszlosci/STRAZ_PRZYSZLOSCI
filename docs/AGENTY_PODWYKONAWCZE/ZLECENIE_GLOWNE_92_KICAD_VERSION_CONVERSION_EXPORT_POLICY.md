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

TODO — niski priorytet po Z87-Z91.
