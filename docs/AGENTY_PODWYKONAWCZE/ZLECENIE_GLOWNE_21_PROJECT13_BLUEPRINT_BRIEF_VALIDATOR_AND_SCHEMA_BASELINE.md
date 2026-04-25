# Zlecenie Glowne 21 Project13 Blueprint Brief Validator And Schema Baseline

## 1. Misja zadania

Wzmocnij input contract dla `pack-project13-blueprint-design-01` przez walidator albo schema baseline dla `DESIGN_BRIEF_TEMPLATE`, tak aby pack nie startowal na zbyt luznym, tylko tekstowym briefie.

## 2. Wyzszy cel organizacji

To zadanie zamienia dobry szablon w cos, co da sie sprawdzic automatycznie lub polautomatycznie przed pierwszym execution surface.

## 3. Read First

- `docs/HANDOFF_DLA_NASTEPNEGO_AGENTA_2026-04-24.md`
- `docs/AGENTY_PODWYKONAWCZE/ODBIOR_PORTFELA_06_ZADAN_11_16_2026-04-24.md`
- `docs/AGENTY_PODWYKONAWCZE/MINI_HANDOFF_ZADANIE_14.md`
- `PROJEKTY/13_baza_czesci_recykling/docs/DESIGN_BRIEF_TEMPLATE.md`
- `PROJEKTY/13_baza_czesci_recykling/docs/SAMPLE_DESIGN_BRIEF_WIFI_TEMP_SENSOR.md`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-blueprint-design-01/manifest.json`

## 4. Write Scope

- `PROJEKTY/13_baza_czesci_recykling/docs/`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-blueprint-design-01/`
- `PROJEKTY/13_baza_czesci_recykling/schemas/`
- `PROJEKTY/13_baza_czesci_recykling/scripts/`

## 5. Deliverables

- schema baseline albo walidator dla design brief
- walidacja sample brief
- aktualizacja manifestu/runbooka packa blueprint, jesli kontrakt sie doprecyzowal

## 6. Acceptance Criteria

- pack `blueprint-design-01` ma jawny sposob sprawdzania, czy brief jest kompletny
- sample brief przechodzi walidacje
- brakujace pola wymagane sa nazywane wprost, a nie ukrywane w swobodnym markdownzie
- rozwiazanie nie wymusza sztucznie zlego kontraktu tylko po to, zeby miec schema file

## 7. Walidacja

- uruchomienie walidatora na sample brief albo jawna walidacja schema contract
- `git diff --check`

## 8. Blokery

Jesli formalny JSON schema jest przedwczesny, dowiez dobry walidator markdown albo prosty parser z lista required fields. Nie udawaj kompletnej standaryzacji, jesli dane nie sa jeszcze gotowe.

## 9. Mini-handoff

Zapisz:

- jaki validator albo schema baseline dodano,
- jak walidowac sample brief,
- czego nadal brakuje przed execution surface `blueprint-design-01`.
