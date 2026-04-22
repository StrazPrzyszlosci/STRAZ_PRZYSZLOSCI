# Pack Project13 Kaggle Enrichment 01

To jest pierwszy realny `KaggleNotebookPack` dla `Project 13`.

Jego celem jest zamienic ogolny opis wolontariackich notebookow Kaggle w konkretny, powtarzalny loop:

```text
fork repo -> import notebooka do Kaggle -> ustawienie sekretow ->
run -> wygenerowanie artefaktow -> push brancha do forka -> PR do upstream
```

## Zakres packa

- notebook: `PROJEKTY/13_baza_czesci_recykling/youtube-databaseparts.ipynb`
- fazy: `discovery -> verification -> enrichment -> review-ready artifacts`
- execution mode: `kaggle_notebook`
- docelowy output: `pull_request`

## Co jest w srodku

- `manifest.json`: kanoniczny rekord `ExecutionPack`
- `task.json`: gotowy rekord `Task` dla pierwszego uruchomienia
- `integrity_risk_assessment.json`: ocena ryzyk dla interesu wspolnego
- `readiness_gate.json`: bramka `pack_ready`
- `RUNBOOK.md`: instrukcja dla wolontariusza i lokalnego agenta
- `PR_TEMPLATE.md`: szablon opisu pull requesta
- `REVIEW_CHECKLIST.md`: checklista review artefaktow
- `scripts/create_execution_records.py`: generator kanonicznych rekordow `Run` i `Artifact` po faktycznym uruchomieniu packa
- `scripts/finalize_execution_pack_run.py`: orkiestrator konca runu packa, ktory robi rebuild, summary, `Run` record i git push do forka
- `scripts/dry_run_execution_pack.py`: lokalny dry-run packa bez prawdziwego Kaggle runu

## Najwazniejsze zasady

- pack zaklada, ze wolontariusz ma wlasny fork repozytorium i pushuje tylko do niego
- sekrety sa ustawiane tylko na koncie `Kaggle` wolontariusza
- wynik nie trafia bezposrednio do upstream bez review
- kazdy run ma zostawic jawny slad provenance: `pack_id`, branch, notebook, timestamp, raport przebiegu i kanoniczny `Run` record

## Oczekiwane artefakty

- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/processed_videos.json`
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/results/test_db.jsonl`
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/results/inventree_import.jsonl`
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/results/ecoEDA_inventory.csv`
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/last_run_summary.md`
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/rebuild_autonomous_outputs_report.md`
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/rebuild_autonomous_outputs_skipped.jsonl`

## Wejscie dla kolejnego agenta

Jesli chcesz rozwijac ten pack dalej, zacznij od:

1. `RUNBOOK.md`
2. `manifest.json`
3. `REVIEW_CHECKLIST.md`
4. notebooka `youtube-databaseparts.ipynb`
