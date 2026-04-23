# Zlecenie Glowne 15 ESP32 Recovered Board Profile Template

## 1. Misja zadania

Przygotuj minimalny template `recovered ESP32 board profile` dla przyszlego packa runtime inspirowanego `ESP-Claw`.

## 2. Wyzszy cel organizacji

To zadanie buduje pierwszy kontrakt danych potrzebny do tego, zeby runtime odzyskanego hardware'u nie byl abstrakcyjnym haslem.

## 3. Read First

- `docs/HANDOFF_DLA_NASTEPNEGO_AGENTA_2026-04-23.md`
- `PROJEKTY/13_baza_czesci_recykling/docs/PLAN_PACKOW_BLUEPRINT_ESP_CLAW.md`
- `docs/REVIEW_ROTATION_GOVERNANCE.md`

## 4. Write Scope

- `PROJEKTY/13_baza_czesci_recykling/docs/`
- ewentualnie `PROJEKTY/13_baza_czesci_recykling/schemas/`

## 5. Deliverables

- template `ESP32 recovered board profile`
- opis wymaganych pol dla runtime
- opcjonalny sample profile dla jednej odzyskanej plytki

## 6. Acceptance Criteria

- template obejmuje co najmniej: board id, wariant MCU, GPIO, zasilanie, siec, storage, recovery path, known limitations
- profile nadaje sie jako input contract dla przyszlego packa `esp-runtime-01`
- dokument jawnie rozroznia pola pomierzone, pola domniemane i pola brakujace

## 7. Walidacja

- kontrola spojnosci z `PLAN_PACKOW_BLUEPRINT_ESP_CLAW.md`
- `git diff --check`

## 8. Blokery

Jesli brak sample hardware, dowiez najpierw dobry template i jawne pola `unknown`, zamiast wpisywac zmyslone capability.

## 9. Mini-handoff

Zapisz:

- jaki template dodano,
- ktore pola sa nienegocjowalne dla runtime,
- czego nadal brakuje przed pierwszym skeletonem packa.
