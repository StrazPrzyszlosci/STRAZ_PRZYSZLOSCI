# Mini-Handoff Zadanie 16

## Co zostalo zrobione

Utworzono dokumentacyjne szkielety dwoch packow i zaktualizowano CHAIN_MAP.md.

### Pack `pack-project13-blueprint-design-01`

Pliki w `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-blueprint-design-01/`:

- `manifest.json` — status `draft`, execution mode `local_agent`, governance Wariant A, input contract: design brief + kanoniczny katalog
- `RUNBOOK.md` — docelowy przeplyw, co pack robi i czego nie robi, PLACEHOLDER na komende
- `PR_TEMPLATE.md` — pola dla brief_id, reuse parts summary, integrity notes
- `REVIEW_CHECKLIST.md` — 9 punktow sprawdzajacych
- `integrity_risk_assessment.json` — risk_level `low`, status `pass`
- `readiness_gate.json` — status `pending` (brak execution surface)
- `task.json` — status `pending`

### Pack `pack-project13-esp-runtime-01`

Pliki w `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-esp-runtime-01/`:

- `manifest.json` — status `draft`, execution mode `local_agent`, governance Wariant B (ostrzejszy), input contract: zatwierdzony design dossier + board profile
- `RUNBOOK.md` — ostrzezenie o sterowaniu swiatem fizycznym, Wariant B governance, PLACEHOLDER na komendy
- `PR_TEMPLATE.md` — sekcja Wariant B z integrity notes, board profile summary
- `REVIEW_CHECKLIST.md` — 3 sekcje (review merytoryczny, integrity review, bench test, governance) — ostrzejsze niz zwykle packi katalogowe
- `integrity_risk_assessment.json` — risk_level `high`, status `pending`
- `readiness_gate.json` — status `pending` (brak execution surface i bench test contract)
- `task.json` — status `pending`

### CHAIN_MAP.md

- zaktualizowano mape z nowymi packami
- dodano zaleznosci: `catalog-export-01` -> `blueprint-design-01` -> `esp-runtime-01`
- dodano opisy rol dla obu packow
- zmieniono status z `planned` na `draft`

## Jakie pliki dotknieto

- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-blueprint-design-01/` (nowy katalog, 7 plikow)
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-esp-runtime-01/` (nowy katalog, 7 plikow)
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/CHAIN_MAP.md` (aktualizacja)

## Czego packom nadal brakuje przed pierwszym uruchomieniem

### blueprint-design-01

- execution surface: skrypt `generate_blueprint.py` nie istnieje
- test na realnym design brief: SAMPLE_DESIGN_BRIEF moze byc uzyty jako test wejsciowy
- walidacja BOM wzgledem katalogu: automatyczna weryfikacja `part_slug` w `bill_of_materials.json`
- gestosc katalogu: `parts_master.jsonl` ma obecnie 4 rekordy — za malo dla realnego BOM

### esp-runtime-01

- execution surface: skrypty `generate_esp_runtime.py` i `bench_test_esp_runtime.py` nie istnieja
- bench test contract: brak definicji, co bench test ma testowac (ADC, GPIO, Wi-Fi, power consumption)
- polityka simulated vs real hardware: brak definicji, kiedy runtime moze byc uzywany w symulacji, a kiedy na realnym hardware
- fizyczna plytka do testu: brak potwierdzenia dostepnosci
- board profile z polami BRAKUJACE musi byc uzupelniony przed bench testem

## Jak wpisuja sie w lancuch po catalog-export-01

```text
catalog-export-01 -> blueprint-design-01 -> esp-runtime-01
```

- `catalog-export-01` domyka katalog i eksporty reuse — jego output jest zrodlem czesci dla blueprint
- `blueprint-design-01` przyjmuje katalog reuse + design brief i produkuje projekt urzadzenia — jego output jest wejsciem dla runtime
- `esp-runtime-01` przyjmuje projekt + board profile i produkuje runtime bundle z bench testem — jego output jest pakietem do flashowania

Kazdy pack ma jasny scope i nie udaja gotowego execution surface. Oba sa w statusie `draft` z placeholderami na komendy.
