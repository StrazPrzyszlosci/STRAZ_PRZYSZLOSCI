# Mini-Handoff Zadanie 35

## Co zostalo zrobione

Zamieniono placeholder `REVIEW_ASSIGNMENT_PACKET.md` w aktualny, queue-aware packet dla sesji ludzkiego review, z maszynowym eksportem pending cases i batch annotation.

### Nowe komendy w `scripts/curate_candidates.py`

1. **`list-pending`** — Listuje wszystkie kandydaty `pending_human_approval` z batch annotation i eksportuje do JSON:
   - Grupuje 14 cases w 3 batche (A: laptop, B: inne, C: e-waste/desktop)
   - Kazdy case dostaje `batch` annotation na podstawie `REVIEW_BATCH_RULES` (match_devices)
   - Eksportuje do `pending_human_approval_list.json` z `total_pending`, `batch_rules`, `pending_entries`
   - Zsynchronizowany z `curation_review_queue.jsonl` — nie wymaga recznej aktualizacji

### Nowe stale w `scripts/curate_candidates.py`

- `REVIEW_BATCH_RULES` — 3 reguly batchingu z `batch`, `name`, `match_devices`, `recommended_mode`
- `assign_batch(device)` — funkcja mapujaca device na batch

### Zaktualizowane artefakty

- `execution_packs/pack-project13-curation-01/REVIEW_ASSIGNMENT_PACKET.md`:
  - Dodana sekcja 8: maszynowy eksport listy pending (referencja do `list-pending` i `pending_human_approval_list.json`)
  - Zaktualizowany cel: wzmianka o synchronizacji z `list-pending`
  - Sekcja 9 (wczesniej 8): status z informacja o maszynowym eksportcie
- `docs/HUMAN_APPROVAL_LEDGER.md`:
  - Dodana sekcja 8: komenda `list-pending`, output JSON, przeznaczenie
  - Wyjasnienie: `list-pending` automatycznie zsynchronizowany z review queue
- `autonomous_test/reports/pending_human_approval_list.json` — maszynowy eksport 14 pending cases z batch annotation

### Zmiany w kodzie

- `scripts/curate_candidates.py`:
  - dodana stala `REVIEW_BATCH_RULES` (3 reguly batchingu)
  - dodana funkcja `assign_batch(device)` — mapowanie device na batch
  - dodana komenda `cmd_list_pending()` — lista pending z batch annotation + eksport JSON
  - docstring zaktualizowany na 12 komend (dodany `list-pending`)
  - CLI dispatcher zaktualizowany o nowa komende

## Jakie pliki zmieniono

- `PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-curation-01/REVIEW_ASSIGNMENT_PACKET.md`
- `PROJEKTY/13_baza_czesci_recykling/docs/HUMAN_APPROVAL_LEDGER.md`
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/pending_human_approval_list.json` (nowy)

## Jakie komendy walidacyjne przeszly

- `python3 -m py_compile PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py` — OK
- `python3 PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py list-pending` — OK (14 pending, 3 batche, JSON wyeksportowany)
- `python3 PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py review-status` — OK (14 pending, gate NOT READY)
- `python3 PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py export-gate` — OK (BLOCKED, poprawnie)
- `git diff --check` — OK

## Batch annotation

| Batch | Nazwa | Cases | Zalecany tryb review |
|-------|-------|-------|---------------------|
| A | Komponenty laptopowe (Lenovo + ASUS + Compal) | 6 | per-batch |
| B | Komponenty z innych urzadzen (Samsung TV, Electrolux, vintage, LED, Gigabyte) | 5 | per-candidate |
| C | IC z e-waste + desktop | 3 | per-batch |

## Otwarte ryzyka i blokery

- 14 kandydatow nadal czeka na prawdziwego reviewera — zadne fikcyjne approvale nie zostaly wpisane
- 9 deferred (7 ocr_needed + 2 manual_review) pozostaje poza `apply` / `export-all`, ale nadal blokuje `export-gate` dopoki nie zostanie rozstrzygniete
- REVIEW_ASSIGNMENT_PACKET.md ma pola `__DO_UZUPELNIENIA__` dla reviewerow — to jest celowe
- Batch assignment jest oparty na `match_devices` — jesli nowe device wejdzie do pending, trafi do `unbatched`

## Co powinien zrobic kolejny wykonawca

- Wypelnic pola `__DO_UZUPELNIENIA__` w REVIEW_ASSIGNMENT_PACKET.md sekcja 3
- Rozstrzygnac 14 pending_human_approval przez `record-review` z prawdziwym `--reviewed-by`
- Re-run `export-gate` po review — gate moze przejsc na OPEN dopiero, gdy rozstrzygniete sa wszystkie `pending_human_approval`, wszystkie `deferred` oraz istnieje min. 1 prawdziwy approval
- Jesli kolejka review zostanie wygenerowana ponownie, uruchomic `list-pending` by zsynchronizowac packet
- Rozstrzygnac 9 deferred (OCR lub manual review) — osobne zadanie (36, 37)
