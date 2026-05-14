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

TODO — równoległe do Z89, ale nie blokuje mock/fixture development.
