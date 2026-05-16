# ZLECENIE GŁÓWNE 94 - Discord KiCad review actions

## Cel

Dodać przyciski/akcje Discord dla wyników KiCad staging: `Wyślij do review`, `Zatwierdź`, `Odrzuć`, z zachowaniem tego samego ledgeru co Telegram.

## Kryteria odbioru

- Brak oddzielnej logiki biznesowej Discord; używać wspólnych funkcji review.
- Tylko uprawniony maintainer może zatwierdzać.
- Każda akcja zapisuje `reviewed_by`, `reviewed_at`, `reason` i poprzedni status.

## Status

DONE — wykonane w tej sesji. Odbiór: `ODBIOR_PORTFELA_24_ZADANIE_94_2026-05-16.md`.
