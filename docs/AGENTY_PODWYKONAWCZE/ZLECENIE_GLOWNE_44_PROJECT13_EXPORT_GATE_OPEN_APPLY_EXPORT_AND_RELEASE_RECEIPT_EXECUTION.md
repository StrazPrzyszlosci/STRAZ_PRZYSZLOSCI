# Zlecenie Glowne 44 Project13 Export Gate Open Apply Export And Release Receipt Execution

## 1. Misja zadania

Jesli `export-gate` jest realnie `OPEN`, wykonaj kontrolowana sekwencje `apply -> validate -> export-all -> validate -> release receipt`.

Jesli gate nadal jest `BLOCKED`, nie uruchamiaj exportu. Zapisz blocker receipt z aktualnymi powodami blokady.

## 2. Wyzszy cel organizacji

Po `38` sciezka exportu jest opisana.
To zadanie ma wykonac ja tylko wtedy, gdy dane sa faktycznie gotowe, a nie gdy dokumentacja wyglada gotowo.

## 3. Read First

- `docs/HANDOFF_DLA_NASTEPNEGO_AGENTA_2026-04-29.md`
- `docs/AGENTY_PODWYKONAWCZE/MINI_HANDOFF_ZADANIE_38.md`
- `PROJEKTY/13_baza_czesci_recykling/docs/EXPORT_OPEN_READINESS_PACKET.md`
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/export_release_receipt_TEMPLATE.json`
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/export_gate_packet.json`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-curation-01/RUNBOOK.md`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-catalog-export-01/RUNBOOK.md`

## 4. Write Scope

- `PROJEKTY/13_baza_czesci_recykling/data/`
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/export_release_receipt_*.json`
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/export_blocker_receipt_*.json`
- `docs/AGENTY_PODWYKONAWCZE/MINI_HANDOFF_ZADANIE_44.md`

## 5. Deliverables

- jesli gate `OPEN`: wykonany `apply`, downstream `export-all`, walidacje i wypelniony `export_release_receipt_YYYY-MM-DD.json`
- jesli gate `BLOCKED`: `export_blocker_receipt_YYYY-MM-DD.json` z aktualnymi checks i blockers
- mini-handoff z pelna sekwencja komend i wynikiem

## 6. Acceptance Criteria

- przed `apply` uruchomiono `export-gate` i potwierdzono `gate_result: OPEN`
- nie ma `pending_human_approval` ani `deferred` w review queue
- po `apply` walidacja katalogu przechodzi
- po `export-all` downstream artefakty przechodza walidacje
- release receipt ma checksums/counts albo jawnie opisuje, ktorych pol nie dalo sie wypelnic

## 7. Walidacja

- `python3 PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py export-gate`
- `python3 PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py apply`
- `python3 PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py validate`
- `python3 PROJEKTY/13_baza_czesci_recykling/scripts/build_catalog_artifacts.py export-all`
- `python3 PROJEKTY/13_baza_czesci_recykling/scripts/build_catalog_artifacts.py validate`
- `git diff --check`

## 8. Blokery

`BLOCKED` gate zatrzymuje zadanie.
Nie wolno uruchamiac `apply` ani `export-all` "na probe", jesli gate nie jest `OPEN`.

## 9. Mini-handoff

Zapisz:

- czy gate byl `OPEN` czy `BLOCKED`,
- jakie komendy uruchomiono,
- jakie artefakty powstaly,
- gdzie jest release albo blocker receipt,
- co zostalo do zamkniecia przed kolejnym exportem.
