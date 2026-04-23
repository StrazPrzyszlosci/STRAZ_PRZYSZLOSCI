# Pack Project13 Curation 01

To jest pack dla `curation chain` w `Project 13`.

Jego celem nie jest discovery, OCR ani eksport downstream.
Jego celem jest formalizacja etapu review i kuracji kandydatow, ktorzy przeszli przez verification, przed dopuszczeniem do kanonicznego katalogu.

## Zakres

- execution mode: `local_agent`
- status: `smoke_tested`
- docelowy output: `pull_request`
- execution surface: `scripts/curate_candidates.py`

## Rola w lancuchu

```text
enrichment -> verification -> [CURATION] -> catalog-export
```

Ten pack ma:

- przyjmowac zweryfikowanych kandydatow z etapu verification (upstream),
- porzadkowac ich do kanonicznych schematow katalogu (`devices.jsonl`, `parts_master.jsonl`, `device_parts.jsonl`),
- oznaczac kandydatow jako `accept`, `defer` albo `reject` z rationale,
- zostawiac jawny audit trail decyzji kuracyjnych w `curation_decisions.jsonl`,
- otwierac PR do kanonicznego katalogu z czytelnym opisem decyzji i handoff point do exportu.

## Granice scope'u wzgledem innych packow

| Aspekt | Verification | Curation | Export |
|--------|-------------|----------|--------|
| Co robi | sprawdza poprawnosc kandydatow | decyduje o przyjeciu do katalogu | przebudowuje artefakty z katalogu |
| Input | surowe kandydatki z enrichment | verified candidates | reviewed catalog |
| Output | confirmed/disputed/rejected + disagreement log | catalog-ready records + decisions | inventory.csv, seed.sql, mcp.json, inventree.jsonl |
| Decyzja | poprawnosc vs zrodlo | przyjecie vs odrzucenie | mechaniczna przebudowa |

Bez curation review i kuracja pozostalyby niejawnym krokiem miedzy packami, a decyzja o tym, co trafia do kanonicznego katalogu, bylaby nieauditowalna.

## Co znaczy "gotowe do katalogu"

Kandydat jest gotowy do katalogu, gdy:

1. ma poprawny `part_number` (MPN, nie designator lista ani placeholder),
2. ma `device_id` powiazany z donor device w `devices.jsonl`,
3. ma uzupelnione kanoniczne pola: `category`, `parameters`, `donor_device`,
4. zostal potwierdzony w verification (`confirmed`) albo ma silny dowod z `disputed` + rationale,
5. nie dubluje istniejacego rekordu w katalogu.

Pelny checklist review znajduje sie w `REVIEW_CHECKLIST.md`.

## Handoff do exportu

Po merge PR curation, pack export downstream jest bezpieczny do uruchomienia:

```bash
python3 PROJEKTY/13_baza_czesci_recykling/scripts/build_catalog_artifacts.py export-all
python3 PROJEKTY/13_baza_czesci_recykling/scripts/build_catalog_artifacts.py validate
```

## Wejscie dla kolejnego agenta

Zacznij od:

1. `manifest.json`
2. `RUNBOOK.md`
3. `REVIEW_CHECKLIST.md`
4. `PR_TEMPLATE.md`
5. `../CHAIN_MAP.md`

## Execution surface

Skrypt `scripts/curate_candidates.py` oferuje 7 komend:

| Komenda | Co robi |
|---------|---------|
| `review` | Laduje i podsumowuje wejscie z verification (snapshot + report + disagreements) |
| `align` | Uklada kazdego kandydata do kanonicznych schematow katalogu |
| `decide` | Stosuje decyzje kuracyjne (auto accept dla confirmed, defer dla disputed, reject dla rejected/invalid) |
| `apply` | Zapisuje zaakceptowanych kandydatow do plikow kanonicznego katalogu |
| `validate` | Waliduje spojnosc cross-file katalogu po apply |
| `report` | Generuje `curation_report.md` i `curation_decisions.jsonl` |
| `dry-run` | Uruchamia align+decide+validate+report bez zapisu do katalogu |

Przykladowy dry-run:

```bash
python3 PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py dry-run --fallback-test-db
```

Pelny workflow:

```bash
python3 PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py review
python3 PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py align
python3 PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py decide
python3 PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py apply
python3 PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py validate
python3 PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py report
```

## Co nadal brakuje

- stabilny input z verification: verified snapshot, verification report, disagreement log
- pierwszy realny run po uzyskaniu wynikow z packa verification
