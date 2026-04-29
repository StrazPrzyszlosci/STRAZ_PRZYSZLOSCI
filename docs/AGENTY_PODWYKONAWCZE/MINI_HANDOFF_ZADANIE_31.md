# Mini-Handoff Zadanie 31

## Co zostalo zrobione

Dodana uczciwa i wygodna sciezka zapisywania ludzkich approvali dla kandydatow `pending_human_approval`. Export gate nie zalezy juz od recznej, niesformatowanej edycji JSON-a.

### Nowe komendy w `scripts/curate_candidates.py`

1. **`record-review`** — Zapisuje ludzka decyzje review dla kandydata z kolejki:
   - `--candidate-id` (wymagany) — ID kandydata z review queue
   - `--decision` (wymagany) — `approved`, `rejected`, lub `defer`
   - `--reviewed-by` (wymagany) — identyfikator reviewera (bez fikcyjnych osob)
   - `--note` (opcjonalny) — notatka tlumaczaca decyzje
   - Efekt: tworzy wpis w `human_review_ledger.jsonl` + aktualizuje `curation_review_queue.jsonl`

2. **`review-status`** — Podsumowanie stanu review:
   - counts per review_status
   - lista pending_human_approval z kontekstem
   - lista approved z informacja o reviewerze
   - informacja o gotowosci export gate

### Nowe artefakty

- `autonomous_test/reports/human_review_ledger.jsonl` — append-only ledger zapisu review decisions (tworzony przez `record-review`)
- `docs/HUMAN_APPROVAL_LEDGER.md` — instrukcja: jak uzywac record-review, jak review wplywa na export gate, co musi zrobic prawdziwy reviewer
- `execution_packs/pack-project13-curation-01/REVIEW_ASSIGNMENT_PACKET.md` — placeholder packet z przydzialem reviewerow (DO_UZUPELNIENIA)

### Zmiany w kodzie

- `scripts/curate_candidates.py`:
  - dodana stala `HUMAN_REVIEW_LEDGER_PATH`
  - dodana komenda `cmd_record_review()` — ledger zapisu review decisions
  - dodana komenda `cmd_review_status()` — podglad stanu review
  - naprawiony bug w `cmd_export_gate()`: sprawdzanie `review_status == "approved"` zamiast `"pending_human_approval"` przy weryfikacji human review recorded
  - zaktualizowany `next_steps` w export gate: instruuje uzycie `record-review` zamiast recznej edycji JSONL
  - docstring zaktualizowany na 11 komend (dodane `record-review` i `review-status`)
  - CLI dispatcher zaktualizowany o nowe komendy

## Jakie pliki zmieniono

- `PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py`
- `PROJEKTY/13_baza_czesci_recykling/docs/HUMAN_APPROVAL_LEDGER.md` (nowy)
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-curation-01/REVIEW_ASSIGNMENT_PACKET.md` (nowy)

## Jakie komendy walidacyjne przeszly

- `python3 -m py_compile PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py` — OK
- `python3 PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py review-queue` — OK (14 pending_human_approval)
- `python3 PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py review-status` — OK (pokazuje pending, gate readiness NOT READY)
- `python3 PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py record-review --candidate-id candidate-0005 --decision approved --reviewed-by Test --note test` — OK (ledger entry utworzony, review queue zaktualizowany)
- `python3 PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py export-gate` — OK (BLOCKED, poprawnie, z nowymi next_steps wskazujacymi record-review)
- `git diff --check` — OK

## Nowy flow pending_human_approval -> approved/rejected/defer

1. `review-queue` — generuje kolejke z pending_human_approval
2. `review-status` — pokazuje ktore kandydaty czekaja
3. `record-review --candidate-id <ID> --decision approved --reviewed-by <NAME>` — zapisuje decyzje
4. `review-status` — weryfikuje ze pending=0
5. `export-gate` — sprawdza czy gate OPEN

## Otwarte ryzyka i blokery

- 14 kandydatow nadal czeka na prawdziwego reviewera — zadne fikcyjne approvale nie zostaly wpisane
- 9 deferred (7 ocr_needed + 2 manual_review) pozostaje poza exportem — to jest poprawne
- REVIEW_ASSIGNMENT_PACKET.md jest placeholderem z polami DO_UZUPELNIENIA
- `human_review_ledger.jsonl` nie istnieje dopoki pierwszy review nie zostanie zapisany — to jest poprawne (poczatkowy stan: brak ledgera)

## Co powinien zrobic kolejny wykonawca

- Wypelnic REVIEW_ASSIGNMENT_PACKET.md z prawdziwymi przydzialami reviewerow
- Rozstrzygnac 14 pending_human_approval przez `record-review` z prawdziwym `--reviewed-by`
- Re-run `export-gate` po review — gate powinien przejsc na OPEN jesli wszystkie pending rozstrzygniete + min 1 approved
- Rozstrzygnac 9 deferred (OCR lub manual review) — osobne zadanie
