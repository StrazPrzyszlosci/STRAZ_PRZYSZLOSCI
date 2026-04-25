# Review Checklist Dla Pack Project13 Kaggle Enrichment 01

- [ ] PR wskazuje `pack_id`, `run_id`, branch i notebook
- [ ] wynik pochodzi z forka wolontariusza, a nie z upstream
- [ ] diff nie zawiera sekretow, plikow tymczasowych ani pobranych wideo (automatyczny scan: workflow `pr_secret_scan.yml` + lokalny skrypt `scripts/scan_pr_secrets.py --staged`)
- [ ] `processed_videos.json` ma sensowny przyrost albo jawne wyjasnienie braku przyrostu
- [ ] `test_db.jsonl` zawiera tylko review-ready rekordy albo jawnie opisane ograniczenia
- [ ] `inventree_import.jsonl` i `ecoEDA_inventory.csv` sa zgodne z wynikami runu
- [ ] `last_run_summary.md` opisuje provenance, counts i known issues
- [ ] `rebuild_autonomous_outputs_report.md` wyjasnia, ile rekordow weszlo do outputow review-ready i co odrzucono
- [ ] `rebuild_autonomous_outputs_skipped.jsonl` jest spojny z rebuild report i pozwala przejrzec odrzucone rekordy
- [ ] autorstwo commita i branch sa zgodne z wolontariuszem wykonujacym run
- [ ] PR nie omija normalnego review ani promocji do kanonicznego katalogu
