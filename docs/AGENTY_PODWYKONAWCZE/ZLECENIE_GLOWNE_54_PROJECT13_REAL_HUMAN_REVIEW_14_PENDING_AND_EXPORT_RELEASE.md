# Zlecenie Glowne 54 Project13 Real Human Review 14 Pending And Export Release

## 1. Misja zadania

Zamknac realnym human review wszystkie 14 `pending_human_approval`, a nastepnie tylko przy `export-gate = OPEN` wykonac release sekwencje `apply -> validate -> export-all -> validate`.

## 2. Read First

- `docs/AGENTY_PODWYKONAWCZE/MINI_HANDOFF_ZADANIE_47.md`
- `docs/AGENTY_PODWYKONAWCZE/MINI_HANDOFF_ZADANIE_48.md`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-curation-01/REVIEW_ASSIGNMENT_PACKET.md`
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/pending_human_approval_list.json`
- `PROJEKTY/13_baza_czesci_recykling/docs/EXPORT_OPEN_READINESS_PACKET.md`

## 3. Write Scope

- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/human_review_ledger.jsonl`
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/review_session_receipt_*.json`
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/export_gate_packet.json`
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/export_release_receipt_*.json`
- `PROJEKTY/13_baza_czesci_recykling/data/` tylko po `export-gate = OPEN`
- `docs/AGENTY_PODWYKONAWCZE/MINI_HANDOFF_ZADANIE_54.md`

## 4. Deliverables

- 14 decyzji `record-review` z realnym `--reviewed-by`.
- `review_session_receipt` z lista candidate_id, decyzji i reviewerem.
- Jesli gate OPEN: export release receipt.
- Jesli nadal BLOCKED: krotki blocker receipt bez powielania starych blockerow.
- Mini-handoff.

## 5. Acceptance Criteria

- Zero placeholder reviewerow typu `agent`, `maintainer`, `krzysiek`, jesli ta osoba realnie nie podjela decyzji.
- Nie edytuj recznie `human_review_ledger.jsonl`.
- `apply` i `export-all` wolno uruchomic dopiero po swiezym `export-gate = OPEN`.
- Po `apply` musi przejsc `curate_candidates.py validate`.
- Po `export-all` musi przejsc `build_catalog_artifacts.py validate`.

## 6. Walidacja

- `python3 PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py list-pending`
- `python3 PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py review-status`
- `python3 PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py export-gate`
- `python3 PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py validate`
- `python3 PROJEKTY/13_baza_czesci_recykling/scripts/build_catalog_artifacts.py validate`
- `git diff --check`

