# Pack Project13 Benchmark Comparison 01

To jest pack dla `benchmark chain` w `Project 13`.

Nie sluzy do discovery, verification, kuracji ani eksportu.
Sluzy do porownywania jakosci, kosztu i czasu roznych promptow, modeli i workflowow na tej samej probce danych.

## Zakres

- execution mode: `kaggle_notebook` (real runs) / `local_agent` (mock/dry runs)
- status: `benchmarked`
- docelowy output: `report`

## Rola w lancuchu

```text
enrichment -> verification -> curation -> export
|
+--> benchmark-comparison (rownolegly, diagnostyczny)
```

Ten pack ma:

- definiowac stabilna probke testowa dla `Project 13`,
- uruchamiac rozne warianty promptow, modeli i workflowow na tej samej probce,
- porownywac wyniki wzgledem metryk jakosci, kosztu i czasu,
- zostawiac jawny benchmark report z reusable wynikami,
- nie modyfikowac kanonicznego katalogu ani downstream artefaktow.

## Execution surface

Skrypt `scripts/run_benchmark.py` udostepnia:

```bash
python3 PROJEKTY/13_baza_czesci_recykling/scripts/run_benchmark.py init-sample
python3 PROJEKTY/13_baza_czesci_recykling/scripts/run_benchmark.py validate-sample
python3 PROJEKTY/13_baza_czesci_recykling/scripts/run_benchmark.py list-variants
python3 PROJEKTY/13_baza_czesci_recykling/scripts/run_benchmark.py run --variant <name>
python3 PROJEKTY/13_baza_czesci_recykling/scripts/run_benchmark.py compare
python3 PROJEKTY/13_baza_czesci_recykling/scripts/run_benchmark.py report
```

## Najwazniejsza roznica wzgledem innych packow

- `enrichment` produkuje kandydatow do lancucha
- `verification` sprawdza poprawnosc kandydatow
- `curation` decyduje o przyjeciu do katalogu
- `export` przebudowuje downstream artefakty
- `benchmark-comparison` jest diagnostyczny: nie produkuje kandydatow do katalogu, tylko porownuje metody pracy

## Ground-truth probka testowa

- **sample_id**: `bench-sample-v1`
- **source**: `autonomous_test/results/test_db.jsonl` (82 rekordy)
- **kryterium `is_valid_part=true`**: ekstrakcja identyfikuje realny, specyficzny komponent elektroniczny z wiarygodnym MPN
- **kryterium `is_valid_part=false`**: board model, designator list, OCR artifact, date code, generic label
- **status**: labele w pelni zweryfikowane (28 valid, 54 invalid, 0 pending review)

## Metryki

| Metryka | Znaczenie |
|---------|-----------|
| precision | ile z wygenerowanych kandydatow jest poprawnych |
| recall | ile z oczekiwanych kandydatow zostalo znalezionych |
| false_positive_rate | ile falszywych trafien wzgledem wszystkich negatywow |
| time_per_record_s | czas przetwarzania na rekord |
| cost_per_record_usd | koszt API na rekord |

## Schematy

- `schemas/benchmark_sample.schema.json`
- `schemas/benchmark_variant.schema.json`
- `schemas/benchmark_metrics.schema.json`

## Wejscie dla kolejnego agenta

Zacznij od:

1. `manifest.json`
2. `RUNBOOK.md`
3. `REVIEW_CHECKLIST.md`
4. `../CHAIN_MAP.md`
