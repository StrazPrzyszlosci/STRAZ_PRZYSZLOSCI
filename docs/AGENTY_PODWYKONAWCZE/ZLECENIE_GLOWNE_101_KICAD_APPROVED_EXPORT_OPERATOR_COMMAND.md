# ZLECENIE GŁÓWNE 101 - KiCad approved export operator command

## Cel

Dodać bezpieczną komendę operatora dla Discord/Telegram albo endpoint workerowy, który generuje podgląd eksportu `approved` z `kicad_export.js` bez automatycznego publikowania go jako release.

## Kryteria odbioru

- Komenda/endpoint używa `buildApprovedKicadEcoedaCsv()` albo równoważnego helpera z `cloudflare/src/kicad_export.js`.
- Dostęp jest ograniczony do maintainerów/operatorów, ale samo wywołanie nie zmienia danych.
- Odpowiedź zawiera count rekordów, informację o `approved only`, ostrzeżenie o provenance i link/attachment lub skrócony preview.
- Test obejmuje brak uprawnień oraz poprawny preview dla maintainer ID.

## Status

DONE — wykonane w tej sesji. Odbiór: `ODBIOR_PORTFELA_26_ZADANIE_101_2026-05-16.md`.
