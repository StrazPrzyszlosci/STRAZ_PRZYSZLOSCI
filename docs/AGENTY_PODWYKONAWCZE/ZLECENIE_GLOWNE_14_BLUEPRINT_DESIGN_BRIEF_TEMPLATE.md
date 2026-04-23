# Zlecenie Glowne 14 Blueprint Design Brief Template

## 1. Misja zadania

Przygotuj minimalny `design brief template` dla przyszlego packa `pack-project13-blueprint-design-01`.

## 2. Wyzszy cel organizacji

To zadanie zamienia inspiracje `Blueprint.am` w pierwszy realny kontrakt wejscia dla warstwy `Inzynier AI`.

## 3. Read First

- `docs/HANDOFF_DLA_NASTEPNEGO_AGENTA_2026-04-23.md`
- `PROJEKTY/13_baza_czesci_recykling/docs/PLAN_PACKOW_BLUEPRINT_ESP_CLAW.md`
- `PROJEKTY/13_baza_czesci_recykling/README.md`
- `PROJEKTY/13_baza_czesci_recykling/data/parts_master.jsonl`

## 4. Write Scope

- `PROJEKTY/13_baza_czesci_recykling/docs/`
- ewentualnie `PROJEKTY/13_baza_czesci_recykling/schemas/`

## 5. Deliverables

- template `design brief`
- opis wymaganych pol i ograniczen
- opcjonalny sample brief dla prostego urzadzenia reuse-first

## 6. Acceptance Criteria

- template wymaga funkcji urzadzenia, zasilania, IO, srodowiska pracy i ograniczen kosztowych
- rozroznia reuse parts, missing parts i zalozenia
- nadaje sie jako input contract dla przyszlego packa `blueprint-design-01`

## 7. Walidacja

- kontrola spojnosci z `PLAN_PACKOW_BLUEPRINT_ESP_CLAW.md`
- `git diff --check`

## 8. Blokery

Jesli brak jeszcze schematu JSON, dowiez najpierw dobry markdown template zamiast sztucznie wymuszac zly schema contract.

## 9. Mini-handoff

Zapisz:

- jaki template dodano,
- jakie pola uznano za nienegocjowalne,
- co nadal trzeba doprecyzowac przed pack skeletonem.
