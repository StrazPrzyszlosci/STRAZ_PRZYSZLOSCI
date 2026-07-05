# ZLECENIE GŁÓWNE 93 - CERN KiCad real checkout smoke albo blocker receipt

## Cel

Uruchomić `pipelines/import_cern_kicad_library.py` na realnym lokalnym checkout lub archiwum CERN KiCad Library i zapisać raport smoke bez commitowania pełnej biblioteki do repo.

## Zakres

- Wejście: lokalny checkout poza repo albo archiwum wskazane przez operatora.
- Wyjście: raport smoke z liczbą symboli/footprintów, przykładowymi rekordami i listą braków metadanych.
- Jeśli realny checkout nie jest dostępny, stworzyć blocker receipt z dokładnym opisem brakującego wejścia.

## Kryteria odbioru

- Nie commitować pełnego repo CERN ani dużych artefaktów.
- Raport zawiera commit SHA albo `unknown` z uzasadnieniem.
- Raport wskazuje, czy parser z Z87 wymaga rozszerzenia przed produkcyjnym ingestem.

## Status

**PARTIAL PASS (fixture substitute)** (2026-07-05) — realny checkout CERN nadal niedostępny (blocker receipt `Z93_BLOCKER_RECEIPT_CERN_CHECKOUT_2026-07-05.md`), ale smoke na fixture mini wykonany i udokumentowany w `Z93_FIXTURE_SMOKE_REPORT_2026-07-05.md`. Wszystkie 3 kryteria odbioru spełnione w trybie substytutu. Parser Z87 działa end-to-end (sym + footprint + provenance). Do pełnego PASS wymagany realny checkout CERN przez operatora (krok w blocker receipt).
