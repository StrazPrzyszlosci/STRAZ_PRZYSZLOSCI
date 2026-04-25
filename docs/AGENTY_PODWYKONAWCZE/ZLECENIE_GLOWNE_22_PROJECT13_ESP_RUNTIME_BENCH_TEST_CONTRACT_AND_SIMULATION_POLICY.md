# Zlecenie Glowne 22 Project13 ESP Runtime Bench Test Contract And Simulation Policy

## 1. Misja zadania

Domknij najwazniejszy brak po zadaniach `15-16`: zdefiniuj bench test contract i polityke `simulated vs real hardware` dla `pack-project13-esp-runtime-01`.

## 2. Wyzszy cel organizacji

To zadanie chroni inicjatywe przed zbyt wczesnym przejsciem z dokumentacyjnego skeletonu runtime do faktycznego flashowania i sterowania swiatem fizycznym.

## 3. Read First

- `docs/HANDOFF_DLA_NASTEPNEGO_AGENTA_2026-04-24.md`
- `docs/AGENTY_PODWYKONAWCZE/ODBIOR_PORTFELA_06_ZADAN_11_16_2026-04-24.md`
- `docs/AGENTY_PODWYKONAWCZE/MINI_HANDOFF_ZADANIE_15.md`
- `docs/AGENTY_PODWYKONAWCZE/MINI_HANDOFF_ZADANIE_16.md`
- `PROJEKTY/13_baza_czesci_recykling/docs/ESP32_RECOVERED_BOARD_PROFILE_TEMPLATE.md`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-esp-runtime-01/`
- `docs/REVIEW_ROTATION_GOVERNANCE.md`

## 4. Write Scope

- `PROJEKTY/13_baza_czesci_recykling/docs/`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-esp-runtime-01/`
- ewentualnie `PROJEKTY/13_baza_czesci_recykling/schemas/`

## 5. Deliverables

- bench test contract dla `esp-runtime-01`
- polityka `simulated vs real hardware`
- aktualizacja runbooka, review checklist i readiness gate packa runtime

## 6. Acceptance Criteria

- dokument jawnie mowi, co musi byc przetestowane przed pierwszym flash albo merge
- dokument rozroznia, co wolno zrobic w symulacji, a co wymaga realnej plytki
- governance Wariant B jest wpisany w flow bench testu i approval
- pack `esp-runtime-01` ma po zmianie czytelniejszy gate przed prawdziwym runtime

## 7. Walidacja

- kontrola spojnosci z `REVIEW_ROTATION_GOVERNANCE.md`
- kontrola spojnosci z `ESP32_RECOVERED_BOARD_PROFILE_TEMPLATE.md`
- `git diff --check`

## 8. Blokery

Jesli brak jeszcze realnej plytki do testu, nie zatrzymuj zadania. Dowiez kontrakt i polityke, ale jawnie zostaw `real hardware required` tam, gdzie symulacja nie wystarcza.

## 9. Mini-handoff

Zapisz:

- jaki bench test contract dodano,
- jak rozdzielono symulacje od realnego hardware,
- jakie gate'y musza byc domkniete przed pierwszym runtime runem.
