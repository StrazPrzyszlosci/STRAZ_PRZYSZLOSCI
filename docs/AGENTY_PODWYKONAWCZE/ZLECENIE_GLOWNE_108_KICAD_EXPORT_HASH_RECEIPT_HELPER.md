# ZLECENIE GŁÓWNE 108 - KiCad export hash receipt helper

## Cel

Dodać helper generujący hash CSV i receipt JSON dla eksportu approved/audit, żeby release był porównywalny między uruchomieniami.

## Kryteria odbioru

- Receipt zawiera `sha256`, `row_count`, `status_filter`, timestamp i listę źródłowych tabel.
- Hash jest stabilny dla znanego fixture.
- Test potwierdza, że receipt nie zawiera sekretów z env.
- Receipt nie wykonuje uploadu ani publikacji.

## Status

DONE — wykonane w tej sesji. Odbiór: `ODBIOR_PORTFELA_27_ZADANIE_108_2026-05-16.md`.
