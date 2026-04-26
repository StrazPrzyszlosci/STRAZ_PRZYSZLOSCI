# Runbook Dla Pack Project13 Blueprint Design 01

## Cel

Ten pack zamienia wypelniony design brief i katalog reuse parts w review-ready projekt urzadzenia.

Docelowy przeplyw:

```text
design brief + kanoniczny katalog -> design dossier, BOM, instrukcje, riske -> PR
```

## Co trzeba miec przed startem

- wypelniony design brief wg `docs/DESIGN_BRIEF_TEMPLATE.md`
- brief musi przejsc walidacje: `python3 scripts/validate_design_brief.py <brief_file>`
- aktualny snapshot kanonicznego katalogu `data/parts_master.jsonl`
- lokalne repo `Project 13`

### Walidacja briefu przed startem packa

Pack nie przyjmuje briefu, ktory nie przeszedl walidacji. Komenda:

```bash
python3 PROJEKTY/13_baza_czesci_recykling/scripts/validate_design_brief.py <brief_file>
```

Walidator sprawdza:
- obecnosc i niepustosc wszystkich pol `[WYMAGANE]` z szablonu
- enum constraints dla `operating_environment` i `reuse_priority`
- odrzuca placeholderowe wartosci (`__DO_UZUPELNIENIA__`, `TBD`, `TODO`)

Schema baseline: `schemas/design_brief.schema.json`

Jesli brief nie przechodzi walidacji, pack nie startuje — brakujace pola sa nazywane wprost w output walidatora.

## Komenda glowna

### Dry-run (minimal execution surface)

```bash
python3 PROJEKTY/13_baza_czesci_recykling/scripts/dry_run_blueprint_design.py \
  --brief PROJEKTY/13_baza_czesci_recykling/docs/SAMPLE_DESIGN_BRIEF_WIFI_TEMP_SENSOR.md
```

Opcje:

- `--catalog <path>` — sciezka do kanonicznego katalogu (domyslnie `data/parts_master.jsonl`)
- `--output-dir <dir>` — katalog wyjsciowy (domyslnie `execution_packs/pack-project13-blueprint-design-01/output/`)

Dry-run generuje 6 artefaktow w `output/`:

1. `design_dossier.md` — uzasadnienie wyboru czesci i opis logiczny
2. `bill_of_materials.json` — BOM z odniesieniami do katalogu lub oznaczeniem missing
3. `assembly_instructions.md` — instrukcja montazu (opisowa, nie CAD)
4. `design_risks.json` — zidentyfikowane ryzyka projektowe
5. `missing_parts_or_assumptions.json` — czesci brakujace i zalozenia
6. `dry_run_report.md` — raport z dry-run z checkami

### Docelowy pelny run (niezaimplementowany)

```bash
python3 PROJEKTY/13_baza_czesci_recykling/scripts/generate_blueprint.py --brief <brief_id> --catalog data/parts_master.jsonl
```

## Co pack powinien zrobic

1. Przyjac wypelniony design brief jako wejscie.
2. Wybrac reuse parts z kanonicznego katalogu na podstawie wymagan briefu.
3. Wygenerowac design dossier z uzasadnieniem wyboru czesci.
4. Zbudowac BOM z odniesieniami do `part_slug` albo oznaczeniem `missing`.
5. Zbudowac instrukcje montazu reviewowalna bez ukrytych promptow.
6. Zidentyfikowac riske projektowe i czesci brakujace.
7. Otworzyc PR z review-ready artefaktami projektu.

## Czego pack nie powinien robic

- nie powinien udawac gotowosci hardware'u bez bench review
- nie powinien ukrywac czesci brakujacych w BOM
- nie powinien generowac schematic PCB — to jest warstwa dokumentacyjna, nie CAD
- nie powinien omijac IntegrityRiskAssessment przed promocja do runtime

## Minimalne kryterium sukcesu

Pack jest wykonany poprawnie, gdy:

- design dossier rozroznia reuse parts od czesci hipotetycznych,
- BOM odnosi sie do kanonicznych rekordow katalogu albo jawnie oznacza brakujace elementy,
- instrukcja montazu jest czytelna bez czytania ukrytych promptow,
- reviewer moze przejrzec caly projekt jako jeden PR.