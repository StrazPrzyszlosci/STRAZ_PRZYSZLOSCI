## Pack 2:
- `pack_id`: `pack-project13-benchmark-comparison-01`
- `test_sample_ref`: `bench-sample-v1` (82 records from `autonomous_test/results/test_db.jsonl`)
- `sample_ground_truth_status`:

## Run Provenance

- `run_id`:
- `fork_owner`:
- `branch_name`:
- `benchmark_run_timestamp_utc`:
- `execution_surface`: `python3 PROJEKTY/13_baza_czesci_recykling/scripts/run_benchmark.py`

## Outputs

- [ ] `autonomous_test/benchmarks/benchmark_report.md`
- [ ] `autonomous_test/benchmarks/benchmark_metrics.json`
- [ ] `autonomous_test/benchmarks/benchmark_sample.jsonl`

## Variants Compared

- variant A:
- variant B:
- (dodaj kolejne w razie potrzeby)

## Metrics Summary

| Metric | Variant A | Variant B |
|--------|-----------|-----------|
| precision | | |
| recall | | |
| false_positive_rate | | |
| cost_per_record | | |
| time_per_record | | |

## Conclusions

- _do_uzupelnienia_

## Known Issues

- _do_uzupelnienia_

## Integrity Notes

- [ ] wynik pochodzi z forka wolontariusza albo jawnego brancha review
- [ ] nie ma sekretow w diffie
- [ ] probka testowa jest stala i odtwarzalna
- [ ] wszystkie ground-truth labele sa zweryfikowane (`label_pending_review=false` dla wszystkich rekordow)
- [ ] pack nie modyfikuje kanonicznego katalogu ani downstream artefaktow
