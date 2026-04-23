# Plan Packow Blueprint I ESP Claw

## Cel dokumentu

Ten dokument zamienia inspiracje `Blueprint.am` i `ESP-Claw` w minimalny plan operacjonalizacji jako kolejne execution packi po obecnym lancuchu `Project 13`.

To nie jest plan wdrozenia na slepo z zewnetrznych vendorow. To plan wykorzystania ich jako wzorcow:

- `Blueprint.am` jako inspiracji dla warstwy `Inzynier AI`,
- `ESP-Claw` jako inspiracji dla warstwy runtime odzyskanego hardware'u `ESP32`.

## Zasada nadrzedna

Oba packi maja byc budowane na obecnym modelu Strazy:

- wejscie jest GitHub-first i reviewowalne,
- czesci pochodza z kanonicznego katalogu albo sa jawnie oznaczone jako brakujace,
- promocja do runtime nie omija `PR`, `ReadinessGate`, `IntegrityRiskAssessment` ani `Approval`,
- zewnetrzne projekty sa najpierw warstwa wzorca i RAG, a nie automatycznym zrodlem prawdy.

## Gdzie te packi wchodza w lancuch

Docelowe rozszerzenie po obecnym katalogu i eksporcie wyglada tak:

```text
enrichment -> verification -> curation -> catalog-export
                                      |
                                      v
                        blueprint-design-01 -> esp-runtime-01
```

Znaczenie:

- `catalog-export` domyka katalog i eksporty reuse,
- `blueprint-design-01` zamienia katalog czesci + brief funkcjonalny w projekt urzadzenia,
- `esp-runtime-01` zamienia zatwierdzony projekt + profil odzyskanej plytki `ESP32` w rzeczywisty runtime wykonawczy.

## Pack 1: `pack-project13-blueprint-design-01`

### Rola

To ma byc pierwszy pack warstwy `Inzyniera AI`.

Jego zadanie:

- przyjac brief funkcjonalny,
- wybrac reuse parts z katalogu,
- zbudowac review-ready szkic urzadzenia,
- zostawic jawny BOM, schemat logiczny i instrukcje montazu.

### Minimalny input contract

- brief funkcjonalny urzadzenia,
- ograniczenia projektowe (`zasilanie`, `IO`, `srodowisko pracy`, `koszt`, `dostepnosc czesci`),
- snapshot kanonicznego katalogu reuse parts,
- lista dopuszczonych donor board profiles, jesli projekt ma targetowac `ESP32`.

### Minimalny output contract

- `design_dossier.md`,
- `bill_of_materials.json`,
- `assembly_instructions.md`,
- `design_risks.json`,
- `missing_parts_or_assumptions.json`.

### Acceptance criteria

- BOM odnosi sie do kanonicznych rekordow katalogu albo jawnie oznacza brakujace elementy,
- projekt rozroznia reuse parts od czesci hipotetycznych,
- instrukcja montazu i zalozenia sa reviewowalne bez czytania ukrytych promptow,
- pack nie udaje gotowosci hardware'u bez jawnego bench review.

### Najwazniejsze blokery

- brak formalnego `design brief` dla packow,
- brak profilu `board capabilities` dla odzyskanych donor boards,
- brak jawnego evaluatora dla "czy projekt jest fizycznie sensowny".

## Pack 2: `pack-project13-esp-runtime-01`

### Rola

To ma byc pierwszy pack warstwy runtime odzyskanego hardware'u.

Jego zadanie:

- przyjac zatwierdzony design dossier,
- dobrac konkretny donor board `ESP32`,
- wygenerowac runtime config, mapowanie pinow i skrypty wykonawcze,
- zostawic bench-ready pakiet do flashowania i testow.

### Minimalny input contract

- zatwierdzony output z `blueprint-design-01`,
- profil odzyskanej plytki `ESP32`,
- lista peryferiow i pinow wymaganych przez projekt,
- constraints bezpieczenstwa i warunki testu.

### Minimalny output contract

- `runtime_profile.json`,
- `pin_map.md`,
- `lua_runtime_bundle/`,
- `flash_and_recovery_runbook.md`,
- `bench_test_report.md`.

### Acceptance criteria

- runtime targetuje jawnie nazwana plytke, a nie abstrakcyjne `ESP32`,
- pin map i recovery path sa opisane przed pierwszym flash,
- pack nie steruje swiatem fizycznym bez bench testu,
- sekrety i credentiale nie trafiaja do firmware ani diffu.

### Najwazniejsze blokery

- brak kanonicznego schematu `board profile` dla odzyskanych plytek `ESP32`,
- brak test bench contract dla `power`, `GPIO`, `sensors`, `network`,
- brak polityki, kiedy runtime jest tylko `simulated`, a kiedy moze wejsc na realny hardware.

## Minimalna kolejnosc wdrozenia

### Etap 1: przygotowac dane i kontrakty

1. Dodac szablon `design brief` dla urzadzenia reuse-first.
2. Dodac szablon `board profile` dla odzyskanych plytek `ESP32`.
3. Zapisac, ktore pola katalogu sa obowiazkowe dla warstwy projektowej (`package`, `voltage`, `interfaces`, `donor evidence`).

### Etap 2: zrobic pack planistyczny przed execution surface

1. Utworzyc dokumentacyjne szkielety packow `blueprint-design-01` i `esp-runtime-01`.
2. Zdefiniowac acceptance criteria, gates i misuse risks.
3. Dopisac evaluator "czy BOM i runtime nie przemycaja czesci poza katalogiem".

### Etap 3: dopiero potem execution surface

1. Dla `blueprint-design-01`: agent lokalny generujacy `design_dossier`, BOM i instrukcje.
2. Dla `esp-runtime-01`: generator runtime profile + bundle flash/test dla konkretnej plytki.
3. Najpierw `dry-run` i bench simulation, dopiero pozniej realny hardware pilot.

## Co warto zrobic najpierw praktycznie

Najmniejszy sensowny ruch nie polega na flashowaniu czegokolwiek.

Najmniejszy sensowny ruch to:

1. dopisac `design brief template`,
2. dopisac `ESP32 recovered board profile template`,
3. dopiero na tym zbudowac szkielety packow.

Bez tego `Blueprint.am` i `ESP-Claw` pozostana tylko inspiracjami marketingowymi.

## Rekomendacja portfelowa

Na obecnym etapie:

- `blueprint-design-01` powinien wejsc wczesniej niz `esp-runtime-01`,
- `esp-runtime-01` powinien dostac ostrzejszy model governance i review niz zwykle packi katalogowe,
- oba packi powinny byc traktowane jako rozszerzenie `Project 13`, a nie osobny swiat poza katalogiem reuse parts.
