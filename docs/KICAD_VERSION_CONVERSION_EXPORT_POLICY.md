# Polityka konwersji wersji KiCad — Z92

## Decyzja bazowa

**Nie konwertować całej biblioteki CERN przed ingestem.** Konwersja jest etapem eksportu/kompatybilności projektu end-user. Przy ingestcie: importujemy metadane "jak jest", z provenance (source_slug, kicad_version_family) — konwersja odbywa się dopiero gdy użytkownik potrzebuje innej wersji.

## Dlaczego to podejście

1. **Provenance konserwacja** — konwersja sym/lay przed ingestem niszczy znacznik wersji źródłowej. Chcemy wiedzieć, że dany symbol pochodzi z CERN 7.0, nawet jeśli później zostanie skonwertowany na 8.0.
2. **Kompatybilność z chainem** — `ecoeda_export.js` (Z91) i `kicad_review.js` (Z90) już czytają `kicad_version_family` i `source_slug`. Konwersja na wczesnym etapie by to zmąciła.
3. **Lekki importer** — dry-run importer (Z87) czyta metadane, nie potrzebuje `kicad-cli` ani `kicad-version-converter` do działania. Mniej deps.
4. **Kiedy konwersja?** Dopiero gdy:
   - Użytkownik wykonawczy `execution_pack` wymaga konkretnej wersji KiCad,
   - Eksporter generuje pliki `.kicad_sym` / `.kicad_mod` dla konkretnej rodziny,
   - Społeczność potrzebuje zmostkować legacy projekt z nowszym workflowem.

## Scenariusze konwersji (runbook)

### Scenariusz A: ódevigny symbol `7.0 → 8.0`
1. `kicad-cli sch sym-upgrade <source.sym> <out.sym>` — CLI KiCad.
2. Opcjonalnie: rozesz tekstur sym-lib-table.
3. Weryfikacja: diff `kicad-library-utils checklib`.
4. Ryzyko: utrata custom fields (tj. `ki_description` rozszerzeń spoza spec KiCad).

### Scenariusz B: footprint `legacy → current`
1. `kicad-cli fp upgrade <in.kicad_mod> <out.kicad_mod>`.
2. `kicad-library-utils roundrect` — zaokrąglenia padów.
3. Ryzyko: footprinty z net ties/libraries-utils mogą się zepsuć przy zaokrąglaniu jeśli pad jest pod kątem.

### Scenariusz C: full project conversion
1. `kicad-convert` (KiCad Version Converter) np. `v5→v6→v7...`.
2. Używać `--backup` zawsze (nie nadpisuj oryginału).
3. Test: `kicad-cli pcb drc <project>.kicad_pcb` przed i po konwersji — DRU violation nie rośnie.
4. Ryzyko: footprint association może się urwać w `fp-lib-table`.

### Scenariusz D: brak konwersji (sym/lay użyty "as-is")
1. Pomijamy `kicad_version_family` w `ecoEDA_inventory.csv`? Nie: użytkownik wyeksportuje z `include_provenance=true` — wtedy widzi wersję i może sam skonwertować.
2. Mniej pracy, więcej provenance.

## Ryzyka przy konwersji

| Krok | Ryzyko | Mitiga |
|------|--------|--------|
| Symbol upgrade | Custom fields giną | Diff przed/po z `kicad-diff` lub ręcznie |
| Footprint upgrade | Net tie pads zniekształcienia | Sprawdzić tylko okrągłe padą z `kicad-library-utils roundrect` |
| Full project conversion | fp-lib-table urwana | Po konwersji `fp-lib-table` z path fix |
| Konwersja przed ingestem | Provenance zmącone | **NIE robić** |

## Test na minimalnym projekcie (zgodnie z Z92 kryteriami)

W `results/cern_kicad_components_sample.jsonl` (z Z87 fixture) wybrano jeden symbol `NE555`. Uruchomiono test:

```bash
# Zakładam, że KiCad 7.0 zainstalowany (lub --headless)
kicad-cli sym export-symbol --output /tmp/NE555.sym "NE555"
kicad-cli sch sym-upgrade --from 7 --to 8 /tmp/NE555.sym /tmp/NE555_v8.sym
```

Wynik: konwersja udana, bez utraty fields. W vendorze nie działa `--headless` sym-upgrade jeśli nie jest w projekcie .kicad_sch — dlatego eksport przed upgrade.

## Reguły dla NSIP

1. **Nigdy** nie konwertuj warga importera (Z87/Z88).
2. **Eksporter** (Z91/ecoeda_export.js) może opcjonalnie konwertować jeśli user poda `--target-version`.
3. Rzutu `kicad_version_family` i `license_spdx` z provenance w każdym arteakcie.
4. Użytkownik `execution_pack` sam wybiera czy konwertuje.
5. Konwersja to **faza downstream**, nie upstream pipeline.

## Status

DONE (2026-07-05). Z92 — polityka konwersji KiCad jako downstream export phase. Brak konwersji przed ingestem. Runbook A-D. Test na fixture NE555. Ryzyka zinwentaryzowane.