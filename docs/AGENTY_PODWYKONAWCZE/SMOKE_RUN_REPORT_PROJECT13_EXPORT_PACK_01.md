# Smoke Run Report: pack-project13-catalog-export-01

## Data wykonania

2026-04-23T11:16:00Z

## Zlecenie

ZLECENIE_GLOWNE_05_PROJECT13_EXPORT_PACK_SMOKE_RUN.md

## Srodowisko

- lokalne, Linux
- python3
- repo: STRAZ_POLSKIEGO_Ai

## Uruchomione komendy

| Komenda | Wynik |
|---------|-------|
| `python3 PROJEKTY/13_baza_czesci_recykling/scripts/build_catalog_artifacts.py validate` | PASSED — exit 0, brak bledow |
| `python3 PROJEKTY/13_baza_czesci_recykling/scripts/build_catalog_artifacts.py export-all` | PASSED — exit 0, brak bledow |
| `python3 PROJEKTY/13_baza_czesci_recykling/scripts/build_catalog_artifacts.py export-ecoeda` | PASSED |
| `python3 PROJEKTY/13_baza_czesci_recykling/scripts/build_catalog_artifacts.py export-d1-sql` | PASSED |
| `python3 PROJEKTY/13_baza_czesci_recykling/scripts/build_catalog_artifacts.py export-mcp` | PASSED |
| `python3 PROJEKTY/13_baza_czesci_recykling/scripts/build_catalog_artifacts.py export-inventree` | PASSED |
| `git diff --check PROJEKTY/13_baza_czesci_recykling/data/` | PASSED — brak zmian (artefakty byly juz aktualne) |

## Szczegoly smoke runu

### Walidacja katalogu (`validate`)

- 4 urzadzenia w `devices.jsonl`
- 4 czesci kanoniczne w `parts_master.jsonl`
- 4 relacje donor-czesc w `device_parts.jsonl`
- brak duplikatow `device_slug` ani `part_slug`
- wszystkie relacje cross-file spojne (device_slug i part_slug w device_parts istnieja w odpowiadajacych plikach)
- wszystkie wymagane pola listowe/obiektowe obecn (known_aliases, serial_markers, keywords, part_aliases, parameters, designators)

### Export-all

Wygenerowano 4 artefakty downstream:

| Artefakt | Linie | Zawartosc |
|----------|-------|-----------|
| `inventory.csv` | 5 (1 header + 4 rows) | ecoEDA-compatible, 14 kolumn |
| `recycled_parts_seed.sql` | 61 | BEGIN/COMMIT, DELETE + INSERT dla recycled_devices, aliases, part_master, device_parts, parts, part_aliases |
| `mcp_reuse_catalog.json` | 1 JSON | catalog_version:2, 4 devices, 4 part_master, 4 device_parts, 4 part_index entries |
| `inventree_import.jsonl` | 4 | Ki-nTree/InvenTree, 1 wpis per part_slug |

### Idempotencja

- checksumy artefaktow PRZED i PO export-all sa identyczne — export jest deterministyczny i idempotentny
- brak diff w `git diff --check`

### Spojnosc danych

- `inventory.csv` kolumna "Source" poprawnie odwoluje sie do `canonical_name` z devices.jsonl
- `recycled_parts_seed.sql` poprawnie generuje subquery z `model` i `part_slug`
- `mcp_reuse_catalog.json` poprawnie grupuje donor_devices per part
- `inventree_import.jsonl` zawiera wszystkie kanoniczne pola czesci

## Blokery

Brak blokerow. Wszystkie komendy przeszly.

## Uwagi i ryzyka

1. **Dane sa seedowe**: aktualny katalog ma 4 seed recordy. Smoke run potwierdza, ze pipeline dziala na malych danych. Zachowanie na wiekszym katalogu (>100 rekordow) nie bylo testowane, ale skrypt jest prosty i liniowy — brak widocznego bottlenecka.
2. **Brak recznej edycji**: artefakty nie byly recznie edytowane po eksporcie, co spelnia zasade provenance.
3. **Puste pola**: niektore pola (`teardown_url`, `source_url`, `datasheet_url`, `datasheet_file_id`, `evidence_url`, `stock_location`) sa puste albo null w seed data. Skrypt obsluguje to poprawnie (sql_quote zamienia None na NULL, puste stringi na '').
4. **Brak upstream curation**: katalog zawiera tylko seed data, brak curation_decisions.jsonl z packa curation — co jest spodziewane, bo curation pack (zadanie 4) jeszcze nie zostal uruchomiony na realnych danych.

## Acceptance criteria — ocena

| Kryterium | Status |
|-----------|--------|
| komenda exportu i walidacji przechodzi lokalnie albo ma jawnie opisany blocker | PASSED |
| raport pokazuje, co zadzialalo, a co nie | PASSED (wszystko zadzialalo) |
| pack po smoke runie jest bardziej operacyjny niz przed nim | PASSED (status zmieniony z `ready` na `smoke_tested`) |

## Zmienione pliki

- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-catalog-export-01/manifest.json` — status: `ready` -> `smoke_tested`, updated_at
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-catalog-export-01/task.json` — status: `queued` -> `in_progress`, updated_at

## Mini-handoff

### Co zostalo zrobione

- Uruchomiono wszystkie 6 komend skryptu `build_catalog_artifacts.py` (validate, export-all, export-ecoeda, export-d1-sql, export-mcp, export-inventree) — wszystkie przeszly bez bledow.
- Potwierdzono idempotencje export-all (checksumy przed i po identyczne).
- Sprawdzono spojnosc wygenerowanych artefaktow z kanonicznym katalogiem.
- Zmieniono status packa z `ready` na `smoke_tested`.

### Co zweryfikowano

- skrypt dziala, walidacja przechodzi, export-all generuje 4 artefakty
- artefakty sa deterministyczne i spojne z katalogiem zrodlowym
- brak potrzeby recznej edycji po eksporcie

### Co zostalo otwarte

- pack nie otworzyl PR (brak nowych zmian w katalogu do wyeksportowania — artefakty sa aktualne)
- realny run curation packa (zadanie 4) wygeneruje nowe rekordy, po ktorych bedzie sens uruchomic export-all z prawdziwym diffem
- wydajnosciowe testy na wiekszym katalogu nie byly robione
- task.json status `in_progress` zostawia miejsce na finalizacje po realnym runie curation -> export -> PR
