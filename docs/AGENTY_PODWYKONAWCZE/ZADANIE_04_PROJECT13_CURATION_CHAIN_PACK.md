# Zadanie 04: Project13 Curation Chain Pack

## 1. Cel wykonawczy

- Dowiezc execution surface dla packa curation: skrypt `curate_candidates.py` z automatycznym ukladaniem kandydatow do kanonicznych schematow katalogu, decyzjami kuracyjnymi i audit trail.

## 2. Wyzszy cel organizacji

- To zadanie formalizuje etap review i kuracji miedzy verification a exportem, zeby decyzja o przyjeciu kandydata do kanonicznego katalogu byla jawna, auditowalna i oddzielona od discovery, verification oraz exportu.
- Curation nie jest celem samym w sobie — chroni przed automatyczna promocja niesprawdzonych danych do kanonicznego katalogu.

## 3. Read First

- `docs/INSTRUKCJA_ROZWOJOWA_DLA_AGENTA.md`
- `docs/HANDOFF_DLA_NASTEPNEGO_AGENTA_2026-04-22.md`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/CHAIN_MAP.md`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-curation-01/manifest.json`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-curation-01/RUNBOOK.md`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-kaggle-verification-01/manifest.json`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-catalog-export-01/manifest.json`

## 4. Write Scope

- `PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-curation-01/`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/CHAIN_MAP.md`

## 5. Out Of Scope

- verification (OCR, frame check, disagreement scoring)
- downstream export (inventory.csv, seed.sql, mcp.json, inventree.jsonl)
- zmiany w finalizerze, helperze Artifact ani skryptach innych packow

## 6. Deliverables

- skrypt `scripts/curate_candidates.py` z 7 komendami (review, align, decide, apply, validate, report, dry-run)
- zaktualizowany manifest.json, task.json, readiness_gate.json, RUNBOOK.md, README.md
- zaktualizowana CHAIN_MAP.md

## 7. Acceptance Criteria

- skrypt dry-run przechodzi na danych testowych (test_db.jsonl jako fallback)
- skrypt nie robi verification ani exportu
- decyzje accept/defer/reject sa jawne w curation_decisions.jsonl z rationale
- curation_report.md zawiera counts, key cases, provenance i handoff do exportu
- readiness_gate.json odzwierciedla ze execution surface istnieje

## 8. Walidacja

- `python3 PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py dry-run --fallback-test-db`
- `python3 -m py_compile PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py`
- parsowanie manifest.json, task.json, readiness_gate.json
- `git diff --check`

## 9. Blokery i eskalacja

- brak verified snapshotu z packa verification (pack jest draft) — uzywaj `--fallback-test-db` do smoke-testu
- nie probuj generowac sztucznego verification reportu — kontynuuj z dostepnymi danymi i zapisuj braki jako ograniczenia

## 10. Mini-handoff

Na koniec zapisz:

- co zostalo zrobione,
- jakie pliki dotknieto,
- jakie komendy walidacyjne przeszly,
- co zostalo otwarte.

### Wynik mini-handoffu (2026-04-23)

#### Co zostalo zrobione

1. **Stworzono execution surface**: `scripts/curate_candidates.py` z 7 komendami (review, align, decide, apply, validate, report, dry-run).
2. **Dry-run smoke-test**: 82 kandydatow z test_db.jsonl — 33 accepted (confirmed z valid MPN), 49 rejected (invalid MPN albo verification=false), 0 deferred (brak disputed w test_db), 0 errors walidacyjnych.
3. **Zaktualizowano status packa**: `review_ready` -> `smoke_tested` w manifest.json, task.json, CHAIN_MAP.md.
4. **Zaktualizowano readiness_gate.json**: execution surface check zmieniony z `fail` na `pass`.
5. **Zaktualizowano RUNBOOK.md i README.md**: dodana sekcja execution surface z opisem komend.
6. **Zaktualizowano CHAIN_MAP.md**: status curation zmieniony na `smoke_tested`, dodano execution surface info, usunieta pozycja "realny execution surface" z brakow.

#### Jakie pliki dotknieto

Nowe:
- `PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py`

Zmienione:
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-curation-01/manifest.json`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-curation-01/task.json`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-curation-01/readiness_gate.json`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-curation-01/RUNBOOK.md`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-curation-01/README.md`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/CHAIN_MAP.md`

Wygenerowane (smoke-test artefakty):
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/curation_aligned.jsonl`
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/curation_decisions.jsonl`
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/curation_report.md`

#### Co zweryfikowano

- `python3 -m py_compile curate_candidates.py` — bez bledow
- `curate_candidates.py review` — poprawnie laduje katalog, raportuje braki verification inputu
- `curate_candidates.py dry-run --fallback-test-db` — 82 aligned, 33 accepted, 49 rejected, validate pass, report generated
- `curate_candidates.py validate` — catalog pass (4 devices, 4 parts, 4 links, 0 errors)
- manifest.json, task.json, readiness_gate.json parsuja sie poprawnie

#### Co zostalo otwarte

1. **Stabilny input z verification**: pack verification jest nadal `draft` — brak verified snapshotu, verification reportu i disagreement logu. Po pierwszym realnym runie verification, curation bedzie moglo pracowac na pelnych danych.
2. **Decyzje dla disputed**: obecny decide auto-odklada disputed jako `defer`. Manualne przejrzenie i ew. zmiana na accept/reject z rationale jest odpowiedzialnoscia maintainera.
3. **Walidacja po apply**: test `apply` nie byl uruchamiany w smoke-test (celowo — dry-run nie modyfikuje katalogu). Pelny workflow z apply wymaga potwierdzenia z review.
