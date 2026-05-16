# ZLECENIE GŁÓWNE 96 - KiCad review audit export

## Cel

Dodać lekki eksport/audit log decyzji KiCad review dla maintainera, aby dało się pokazać kto, kiedy i dlaczego zatwierdził link CERN -> NSIP przed downstream eksportem ecoEDA.

## Kryteria odbioru

- Eksport czyta z `kicad_review_events` oraz `recycled_part_kicad_links`, bez nadpisywania danych produkcyjnych.
- Wynik zawiera co najmniej: `master_part_id`, `kicad_component_id`, `previous_status`, `next_status`, `reviewed_by`, `reason`, `created_at` oraz provenance źródła KiCad.
- Jest test jednostkowy na format eksportu i brak eventów spoza KiCad review.
- Dokumentacja wskazuje, że eksport jest audytem, a nie aktem zatwierdzenia.

## Status

DONE — wykonane w tej sesji. Odbiór: `ODBIOR_PORTFELA_25_ZADANIE_96_2026-05-16.md`.
