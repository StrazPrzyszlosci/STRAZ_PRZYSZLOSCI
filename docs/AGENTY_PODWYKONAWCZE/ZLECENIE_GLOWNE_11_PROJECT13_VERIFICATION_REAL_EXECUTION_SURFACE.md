# Zlecenie Glowne 11 Project13 Verification Real Execution Surface

## 1. Misja zadania

Zmien `pack-project13-kaggle-verification-01` z dokumentacyjnego szkielu w realny execution surface, ktory da sie lokalnie uruchomic i reviewowac.

## 2. Wyzszy cel organizacji

To zadanie oddziela `verification` od enrichment i usuwa najbardziej oczywisty reczny, ukryty etap w lancuchu `Project 13`.

## 3. Read First

- `docs/HANDOFF_DLA_NASTEPNEGO_AGENTA_2026-04-23.md`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/CHAIN_MAP.md`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-kaggle-verification-01/manifest.json`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-kaggle-verification-01/RUNBOOK.md`
- `PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py`
- `PROJEKTY/13_baza_czesci_recykling/youtube-databaseparts.ipynb`

## 4. Write Scope

- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-kaggle-verification-01/`
- `PROJEKTY/13_baza_czesci_recykling/scripts/`
- ewentualnie nowy notebook lub lokalny skrypt verification

## 5. Deliverables

- realny punkt uruchomienia verification
- zaktualizowany manifest i runbook
- jawny input/output contract
- mini-handoff z opisem, co nadal blokuje pierwszy realny run

## 6. Acceptance Criteria

- verification nie jest juz tylko opisem
- istnieje realny execution surface (`script`, `notebook` albo `CLI`)
- output `verified snapshot`, `verification_report.md` i `verification_disagreements.jsonl` jest jawnie zdefiniowany
- pack nadal nie miesza verification z curation ani exportem

## 7. Walidacja

- lokalne uruchomienie wybranego execution surface
- parsowanie `manifest.json`
- `python3 -m py_compile <nowy_lub_zmieniony_skrypt>`
- `git diff --check`

## 8. Blokery

Jesli nie da sie jeszcze zrobic calego flowu Kaggle, dowiez lokalny review-ready execution surface z jawnym fallbackiem i opisanymi brakami.

## 9. Mini-handoff

Zapisz:

- co jest execution surface,
- jak go uruchomic,
- jakie outputy produkuje,
- co nadal blokuje pierwszy publiczny run.
