# Zlecenie Glowne 18 Project13 Curation Real Verified Snapshot Run

## 1. Misja zadania

Uruchom pack `curation` na realnym wejsciu z verification (`test_db_verified.jsonl`), a nie tylko na fallbackowym `test_db.jsonl`, i zostaw jawny raport, czy handoff `verification -> curation` jest juz praktycznie stabilny.

## 2. Wyzszy cel organizacji

To zadanie sprawdza pierwszy realny downstream po zadaniu `11` i zamienia lokalny execution surface verification w cos, co faktycznie pracuje dalej w lancuchu.

## 3. Read First

- `docs/HANDOFF_DLA_NASTEPNEGO_AGENTA_2026-04-24.md`
- `docs/AGENTY_PODWYKONAWCZE/ODBIOR_PORTFELA_06_ZADAN_11_16_2026-04-24.md`
- `docs/AGENTY_PODWYKONAWCZE/MINI_HANDOFF_ZADANIE_11.md`
- `PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-curation-01/RUNBOOK.md`
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/results/test_db_verified.jsonl`

## 4. Write Scope

- `PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py`
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-curation-01/`
- ewentualnie `PROJEKTY/13_baza_czesci_recykling/execution_packs/CHAIN_MAP.md`

## 5. Deliverables

- realny dry-run albo review-ready run curation na `test_db_verified.jsonl`
- raport, czy input z verification jest stabilny
- jawna informacja, ile rekordow idzie do `accept`, `defer`, `reject`
- mini-handoff z tym, co blokuje export

## 6. Acceptance Criteria

- curation korzysta z `test_db_verified.jsonl` jako realnego inputu
- powstaje jawny raport counts i decyzji
- pack nie miesza curation z exportem downstream
- jesli input z verification ma luki, raport nazywa je wprost zamiast ukrywac fallback

## 7. Walidacja

- `python3 PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py review`
- `python3 PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py dry-run`
- `git diff --check`

## 8. Blokery

Jesli verified snapshot okazuje sie zbyt slaby przez liczbe disputed, nie omijaj tego fallbackowym test_db. Zostaw jawny raport, co konkretnie blokuje stabilny handoff do curation.

## 9. Mini-handoff

Zapisz:

- czy verified snapshot wystarczyl jako input,
- jakie byly counts decyzji kuracyjnych,
- co blokuje przejscie do exportu bez dodatkowego review.
