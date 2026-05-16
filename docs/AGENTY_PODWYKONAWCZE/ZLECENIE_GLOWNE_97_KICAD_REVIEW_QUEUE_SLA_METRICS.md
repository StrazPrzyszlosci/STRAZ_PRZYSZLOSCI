# ZLECENIE GŁÓWNE 97 - KiCad review queue SLA metrics

## Cel

Dodać metryki kolejki KiCad review, żeby operator widział liczbę oczekujących sugestii, wiek najstarszej sugestii oraz tempo zamykania decyzji.

## Kryteria odbioru

- Funkcja agreguje statusy `suggested`, `needs_more_data`, `approved`, `rejected` z linków i eventów.
- Odpowiedź operatora zawiera: pending count, oldest pending age, decisions in last 7 days, approval ratio.
- Brak automatycznego zatwierdzania; metryki są tylko informacyjne.
- Jest test na pustą kolejkę i kolejkę z co najmniej jednym starym rekordem.

## Status

DONE — wykonane w tej sesji. Odbiór: `ODBIOR_PORTFELA_25_ZADANIE_97_2026-05-16.md`.
