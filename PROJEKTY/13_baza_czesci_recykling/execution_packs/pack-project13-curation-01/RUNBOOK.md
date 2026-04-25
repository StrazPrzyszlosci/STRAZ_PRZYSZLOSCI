# Runbook Dla Pack Project13 Curation 01

## Cel

Ten pack formalizuje etap review i kuracji miedzy verification a downstream exportem. Jest pomostem miedzy wynikami verification (potwierdzone/sporne kandydaci) a exportem (mechaniczna przebudowa artefaktow z kanonicznego katalogu).

Docelowy przeplyw:

```text
verified candidates -> schema alignment -> curation decisions -> catalog-ready records -> PR
```

W wiekszym lancuchu:

```text
enrichment -> verification -> [CURATION] -> catalog-export
```

## Wyzszy cel organizacji

Curation nie jest celem samym w sobie. Sluzy:

- zamianie niejawnego kroku miedzy packami w jawny, auditowalny etap,
- ochronie przed automatyczna promocja niesprawdzonych danych do kanonicznego katalogu,
- budowie reusable capability kuracyjnej, ktora da sie podpiac pod kolejne lancuchy packow,
- jasnej granicy odpowiedzialnosci: verification sprawdza poprawnosc, curation decyduje o przyjeciu, export przebudowuje.

## Co trzeba miec przed startem

- verification report (`autonomous_test/reports/verification_report.md`) z packa verification
- disagreement log (`autonomous_test/reports/verification_disagreements.jsonl`) z packa verification
- kandydacki snapshot (`autonomous_test/results/test_db_verified.jsonl`) z packa verification
- lokalne repo z kanonicznym katalogiem `Project 13`
- znajomosc schematow katalogu: `devices.jsonl`, `parts_master.jsonl`, `device_parts.jsonl`
- obecny stan kanonicznego katalogu (istniejace rekordy do sprawdzenia duplikatow)

Jesli ktorys z wejsciowych plikow nie istnieje, zapisz to jako jawne ograniczenie w curation_report.md i kontynuuj z dostepnymi danymi.

## Krok 1. Przejrzyj wejscie z verification

1. Wczytaj `verification_report.md` i `verification_disagreements.jsonl` z packa verification.
2. Wczytaj `test_db_verified.jsonl` jako wejsciowy snapshot kandydatow.
3. Zrozum, ktore rekordy sa potwierdzone (`confirmed`), ktore sporne (`disputed`) i ktore odrzucone (`rejected`).
4. Zanotuj counts: ile confirmed, ile disputed, ile rejected — beda potrzebne w curation_report.md.

## Krok 2. Ukladanie do kanonicznych schematow

Dla kazdego kandydata ze snapshotu:

### Kandydaci `confirmed` z verification:

1. Sprawdz, czy sa zgodne ze schematem `devices.jsonl`, `parts_master.jsonl` i `device_parts.jsonl`.
2. Uzupelnij brakujace pola kanoniczne:
   - `device_id` — unikalny identyfikator urzadzenia-dawcy
   - `part_number` — kanoniczny numer czesci (MPN, nie designator)
   - `category` — kategoria czesci wg klasyfikacji katalogu
   - `parameters` — parametry techniczne w formacie katalogu
   - `donor_device` — powiazanie z urzadzeniem-dawca
3. Sprawdz, czy kandydat nie dubluje istniejacego rekordu w katalogu.
4. Oznacz jako `accept` w curation_decisions.jsonl.

### Kandydaci `disputed` z verification:

1. Ocen wagę dowodu z disagreement log.
2. Jesli istnieje silny dowod potwierdzajacy, oznacz jako `accept` z rationale.
3. Jesli dowod jest niepewny, oznacz jako `defer` z wyjasnieniem, co trzeba doprecyzowac.
4. Jesli dowod wskazuje na falszywe trafienie, oznacz jako `reject` z rationale.

### Kandydaci `rejected` z verification:

1. Nie promuj do katalogu.
2. Zapisz decyzje `reject` w audit trail z odeslaniem do verification reportu.

## Krok 3. Zapisz decyzje kuracyjne

1. Zapisz `curation_decisions.jsonl` z wpisami:

```json
{
  "candidate_id": "<id-rekordu-z-snapshotu>",
  "decision": "accept|defer|reject",
  "rationale": "<dlaczego-ta-decyzja>",
  "verification_status": "confirmed|disputed|rejected",
  "provenance": {
    "verification_report": "autonomous_test/reports/verification_report.md",
    "disagreement_ref": "<entry-id-z-disagreement-log>",
    "source_snapshot": "autonomous_test/results/test_db_verified.jsonl"
  },
  "decided_at": "2026-04-23T01:00:00Z"
}
```

2. Zapisz `curation_report.md` z:
   - **counts**: accepted, deferred, rejected (z podzialam na confirmed/disputed/rejected z verification)
   - **najwazniejsze przypadki wymagajace review**: kandydaci sporni zaakceptowani, kandydaci deferred
   - **provenance**: odeslanie do wejsciowego verification reportu i snapshotu
   - **handoff do exportu**: informacja, ze po merge PR mozna uruchomic `pack-project13-catalog-export-01`

## Krok 4. Zaktualizuj kanoniczny katalog

1. Dodaj zaakceptowanych kandydatow do odpowiednich plikow katalogu:
   - `data/devices.jsonl` — nowy donor device albo aktualizacja istniejacego
   - `data/parts_master.jsonl` — nowe czesci kanoniczne
   - `data/device_parts.jsonl` — nowe relacje czesc-donor
2. Upewnij sie, ze nie dublujesz istniejacych rekordow (sprawdz po `device_id`, `part_number`).
3. Sprawdz spojnosc relacji miedzy plikami katalogu:
   - kazdy `device_id` w `device_parts.jsonl` istnieje w `devices.jsonl`
   - kazdy `part_number` w `device_parts.jsonl` istnieje w `parts_master.jsonl`
4. Nie uruchamiaj exportu downstream — to jest odpowiedzialnosc packa `catalog-export`.

## Krok 5. Otworz PR

1. Stworz branch w formacie `curation-<timestamp>` albo `curation-<batch-id>`.
2. Commituj zmiany w katalogu, raport kuracyjny i decyzje.
3. Otworz PR do upstream z trescia z `PR_TEMPLATE.md`.
4. Dolacz `curation_report.md` i `curation_decisions.jsonl` jako czesc PR.
5. W opisie PR jawnie wskaz handoff point: po merge tego PR mozna uruchomic `pack-project13-catalog-export-01`.

## Krok 6. Handoff do exportu

Po merge PR curation:

1. Uruchomienie packa `pack-project13-catalog-export-01` jest bezpieczne, bo katalog jest po review.
2. Komenda:

```bash
python3 PROJEKTY/13_baza_czesci_recykling/scripts/build_catalog_artifacts.py export-all
```

3. Walidacja przed PR exportu:

```bash
python3 PROJEKTY/13_baza_czesci_recykling/scripts/build_catalog_artifacts.py validate
```

## Czego pack nie powinien robic

- nie powinien automatycznie akceptowac wszystkich kandydatow bez review
- nie powinien uruchamiac discovery, OCR, frame check ani disagreement scoring (to scope verification)
- nie powinien uruchamiac downstream exportu do ecoEDA, InvenTree, D1, MCP (to scope export)
- nie powinien recznie edytowac wygenerowanych plikow exportowych
- nie powinien pomijac audit trail decyzji kuracyjnych
- nie powinien pushowac bezposrednio do upstream bez PR i review

## Granice scope'u wzgledem innych packow

| Aspekt | Verification | Curation | Export |
|--------|-------------|----------|--------|
| Co robi | sprawdza poprawnosc kandydatow | decyduje o przyjeciu do katalogu | przebudowuje artefakty z katalogu |
| Input | surowe kandydatki z enrichment | verified candidates | reviewed catalog |
| Output | confirmed/disputed/rejected + disagreement log | catalog-ready records + decisions | inventory.csv, seed.sql, mcp.json, inventree.jsonl |
| Decyzja | poprawnosc vs zrodlo | przyjecie vs odrzucenie | mechaniczna przebudowa |

## Aktualny status

Pack jest `real_verified_tested`:

- kontrakt dokumentacyjny jest gotowy,
- outputy i acceptance criteria sa nazwane,
- scope jest jasno oddzielony od verification i exportu,
- handoff point do exportu jest czytelny,
- review checklist definiuje, co znaczy "gotowe do katalogu",
- execution surface jest dostepny: `scripts/curate_candidates.py` z 7 komendami,
- dry-run na 82 kandydatach z `test_db_verified.jsonl` (realny verified input): 23 accepted (9 confirmed + 14 triage=likely_confirmed), 9 deferred (7 ocr_needed + 2 manual_review), 50 rejected (43 rejected + 7 threshold_tuning),
- disputed candidates sa teraz rozstrzygane na podstawie triage z verification (likely_confirmed->accept, threshold_tuning->reject, ocr_needed/manual_review->defer),
- raport curation zawiera triage breakdown, stability assessment i jawne blockers do exportu.

## Minimalne kryterium sukcesu

Pack spelnia kryteria sukcesu:

- ma stabilny input z verification (verified snapshot + report + disagreement log),
- ma jawny output curation decisions z rationale i triage category,
- reviewer dostaje audit trail zamiast czarnej skrzynki,
- handoff do packa export jest czytelny w PR.

Pozostale warunki do domkniecia przed realnym apply:

- 14 auto-promotowanych disputed candidates (triage=likely_confirmed) wymaga ludzkiego potwierdzenia,
- 9 deferred candidates (7 ocr_needed + 2 manual_review) wymaga rozstrzygniecia.

## Execution surface

Skrypt `scripts/curate_candidates.py` oferuje 7 komend:

### `review` — przeglad wejscia z verification

```bash
python3 PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py review
```

Laduje verified snapshot, verification report i disagreement log. Jesli ktorys z plikow nie istnieje, zapisuje to jako ograniczenie. Pokazuje counts: ile confirmed, ile disputed, ile rejected, oraz aktualny stan kanonicznego katalogu.

### `align` — ukladanie kandydatow do schematow katalogu

```bash
python3 PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py align
python3 PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py align --fallback-test-db
```

Dla kazdego kandydata ze snapshotu:
- wyciaga device_slug, part_slug z danych zrodlowych,
- buduje candidate device/part/link zgodne z kanonicznymi schematami,
- sprawdza MPN pod katem waznosci (odrzuca designatory, puste pola, tekst bez MPN),
- wykrywa duplikaty wzgledem istniejacego katalogu,
- zapisuje `curation_aligned.jsonl` z pelnym kontekstem kuracyjnym.

Opcja `--fallback-test-db` pozwala uzyc `test_db.jsonl` zamiast brakujacego verified snapshotu (do smoke-testu).

### `decide` — decyzje kuracyjne

```bash
python3 PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py decide
```

Stosuje automatyczne decyzje kuracyjne z wykorzystaniem triage z verification:
- `confirmed` z waznym MPN -> `accept` z rationale,
- `disputed` + triage=`likely_confirmed` -> `accept` (auto-promote per triage recommendation),
- `disputed` + triage=`threshold_tuning` -> `reject` (part_number nie jest waznym MPN),
- `disputed` + triage=`ocr_needed` -> `defer` (wymaga OCR frame check z GEMINI_API_KEY),
- `disputed` + triage=`manual_review` -> `defer` (wymaga ludzkiego review),
- `rejected` lub niewazny MPN -> `reject` z rationale,
- zapisuje `curation_decisions.jsonl` z pelnym audit trail (candidate_id, decision, rationale, verification_status, triage_category, provenance, decided_at).

### `apply` — zapis do kanonicznego katalogu

```bash
python3 PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py apply
```

Dodaje zaakceptowanych kandydatow do plikow kanonicznego katalogu:
- `data/devices.jsonl` — nowy donor device,
- `data/parts_master.jsonl` — nowa czesc kanoniczna,
- `data/device_parts.jsonl` — nowa relacja czesc-donor.

Przed apply tworzy backup plikow katalogu w `data/backups/`.

### `validate` — walidacja spojnosci katalogu

```bash
python3 PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py validate
```

Sprawdza:
- brak duplikatow device_slug i part_slug,
- spojnosc relacji cross-file (device_id w device_parts istnieje w devices, part_slug istnieje w parts_master),
- brak pustych part_number,
- brak duplikatow relacji device-part.

### `report` — raport kuracyjny

```bash
python3 PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py report
```

Generuje `curation_report.md` z counts, najwazniejszymi przypadkami, provenance i handoff do exportu.

### `dry-run` — pelny test bez zapisu

```bash
python3 PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py dry-run --fallback-test-db
```

Uruchamia align + decide + validate + report bez modyfikacji kanonicznego katalogu. Sluzy do smoke-testu pipeline'u przed realnym runem.
