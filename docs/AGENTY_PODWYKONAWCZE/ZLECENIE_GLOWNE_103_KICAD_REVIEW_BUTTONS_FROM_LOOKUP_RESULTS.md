# ZLECENIE GŁÓWNE 103 - KiCad review buttons from lookup results

## Cel

Połączyć wyniki lookupu KiCad/NSIP z akcją `Wyślij do review`, tak aby operator nie musiał ręcznie konstruować callbacka `kicad_review:suggest:<master>:<component>`.

## Kryteria odbioru

- Gdy lookup zwraca parę `master_part_id` + `kicad_component_id`, UI pokazuje przycisk `Wyślij do review` dla tej pary.
- Gdy brakuje `master_part_id`, UI jasno mówi, że najpierw trzeba wskazać rekord NSIP master.
- Test obejmuje przypadek z pełną parą ID oraz przypadek tylko KiCad staging.
- Akcja nadal wywołuje `suggestKicadLink()`, bez duplikowania logiki ledgeru.

## Status

TODO — zależy od Z94.
