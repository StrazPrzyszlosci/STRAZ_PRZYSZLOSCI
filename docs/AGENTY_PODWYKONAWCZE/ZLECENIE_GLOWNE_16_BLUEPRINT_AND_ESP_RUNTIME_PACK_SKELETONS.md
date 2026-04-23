# Zlecenie Glowne 16 Blueprint And ESP Runtime Pack Skeletons

## 1. Misja zadania

Przygotuj dokumentacyjne szkielety packow `pack-project13-blueprint-design-01` i `pack-project13-esp-runtime-01`.

## 2. Wyzszy cel organizacji

To zadanie zamienia plan z `PLAN_PACKOW_BLUEPRINT_ESP_CLAW.md` w rzeczywiste miejsce w repo dla kolejnych execution packow.

## 3. Read First

- `docs/HANDOFF_DLA_NASTEPNEGO_AGENTA_2026-04-23.md`
- `PROJEKTY/13_baza_czesci_recykling/docs/PLAN_PACKOW_BLUEPRINT_ESP_CLAW.md`
- wyniki zadan `14` i `15`, jesli istnieja
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/CHAIN_MAP.md`

## 4. Write Scope

- `PROJEKTY/13_baza_czesci_recykling/execution_packs/`
- `PROJEKTY/13_baza_czesci_recykling/docs/`
- `PROJEKTY/13_baza_czesci_recykling/README.md`

## 5. Deliverables

- dwa nowe katalogi packow
- `manifest.json`, `RUNBOOK.md`, `PR_TEMPLATE.md`, `REVIEW_CHECKLIST.md`
- `task.json`, `integrity_risk_assessment.json`, `readiness_gate.json`
- aktualizacja `CHAIN_MAP.md`

## 6. Acceptance Criteria

- oba packi maja jasny scope i nie udaja gotowego execution surface
- `blueprint-design-01` ma input contract oparty o `design brief`
- `esp-runtime-01` ma input contract oparty o `ESP32 board profile`
- `esp-runtime-01` ma ostrzejsze safety/integrity notes niz zwykle packi katalogowe

## 7. Walidacja

- parsowanie `manifest.json`
- kontrola spojnosci z `PLAN_PACKOW_BLUEPRINT_ESP_CLAW.md`
- `git diff --check`

## 8. Blokery

Jesli `14` albo `15` nie istnieja, nie zatrzymuj calego zadania - dowiez skeleton z jawnymi placeholderami i wpisz brakujace kontrakty jako blokery.

## 9. Mini-handoff

Zapisz:

- jakie pack skeletony dodano,
- czego im nadal brakuje przed pierwszym uruchomieniem,
- jak wpisuja sie w lancuch po `catalog-export-01`.
