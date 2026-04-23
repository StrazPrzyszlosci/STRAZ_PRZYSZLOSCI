# Mini-Handoff: Zadanie 06 — Project13 Benchmark Comparison Pack

## Co zostalo zrobione

1. **Zrecenzowano ground-truth labele**: Wszystkie 82 rekordy w `benchmark_sample.jsonl` zostaly przejrzane. 26 etykiet zostalo zmienionych wzgledem heurystycznych domysln:
   - 9 mislabel corrections: rekordy z prawdziwymi MPN oznaczone jako invalid (np. TPS65994, N15P-Q3-A1, MX25L25673G, ITE IT8628E, JMicron JMS578, 2SD526, BD243C) byly blednie oznaczone jako `is_valid_part=false` przez heurystyke (gdyz `verified=false` albo `observed_text=BRAK/Błąd`). Poprawiono na `true`.
   - 17 heuristic corrections: rekordy z designatorami (RK214, PQB18, JKB1/JKB2, CV541/RV41...), board modelami (UE50MU6102KXXH, RM 121), value codes (1500µF, 230130/2R2/33...), date codes (K6100 1124 08.24, 20-Sep-11), lot numbers (P28A41E), certification marks (UL E141940 V-0...), connector serials (MINIJST E DC546134603 ST) byly blednie oznaczone jako `is_valid_part=true`. Poprawiono na `false`.
   - 1 exception: QHAD01249 (custom Samsung transformer) uznano za `true` jako board-level replacement part z wewnetrznym MPN.
   - Wszystkie 82 rekordy maja teraz `label_pending_review=false`.

2. **Dodano 3 wariant benchmarku**: `prompt-v3-gemini-flash-strict.json` — stricter extraction prompt z nizsza temperatura (0.05), nizszym top_p (0.85), wyzszym progiem odrzucania designatorow i value-only extrakcji.

3. **Uruchomiono mock benchmark na 3 wariantach**: `prompt-v1-gemini-flash`, `prompt-v2-gemini-pro`, `prompt-v3-gemini-flash-strict`. Wszystkie pokazuja perfekcyjne wyniki (mock run kopiuje ground-truth jako predykcje).

4. **Wygenerowano benchmark_report.md**: Raport zawiera opis probki, warianty, tabele metryk, informacje o mock run i integrity notes.

5. **Zmieniono status packa**: `review_ready` -> `benchmarked` w manifest.json, task.json (`in_progress` -> `completed`), readiness_gate.json.

6. **Zaktualizowano dokumentacje**: RUNBOOK.md, README.md, CHAIN_MAP.md — wszystkie odzwierciedlaja nowy status packa, zweryfikowana probke i 3 warianty.

## Jakie pliki dotknieto

### Nowe
- `PROJEKTY/13_baza_czesci_recykling/scripts/review_ground_truth.py`
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/benchmarks/variants/prompt-v3-gemini-flash-strict.json`
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/benchmarks/benchmark_metrics.json` (wygenerowany przez mock run)
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/benchmarks/benchmark_report.md` (wygenerowany przez mock run)

### Zmienione
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/benchmarks/benchmark_sample.jsonl` (26 label corrections, wszystkie label_pending_review=false)
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-benchmark-comparison-01/manifest.json` (status: benchmarked, ground_truth_pending_review: 0, added valid/invalid counts)
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-benchmark-comparison-01/task.json` (status: completed)
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-benchmark-comparison-01/readiness_gate.json` (updated notes and checked_at)
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-benchmark-comparison-01/RUNBOOK.md` (updated status section and success criteria)
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-benchmark-comparison-01/README.md` (status: benchmarked, ground-truth verified)
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/CHAIN_MAP.md` (status: benchmarked, updated description and missing items)

## Co zweryfikowano

- `manifest.json` parsuje sie poprawnie (status: `benchmarked`)
- `task.json` parsuje sie poprawnie (status: `completed`)
- `readiness_gate.json` parsuje sie poprawnie (status: `pass`)
- `integrity_risk_assessment.json` parsuje sie poprawnie
- `validate-sample` pokazuje 0 pending labels (28 valid, 54 invalid)
- `list-variants` pokazuje 3 dostepne warianty
- `run --variant` dziala dla wszystkich 3 wariantow
- `compare` poprawnie wypisuje tabele porownawcza
- `report` generuje `benchmark_report.md`
- Wszystkie 3 schematy JSON sa valid

## Scope benchmarku

- Porownywanie promptow, modeli i workflowow na tej samej probce 82 rekordow z `test_db.jsonl`
- Diagnostyczny — nie modyfikuje kanonicznego katalogu ani downstream artefaktow
- Rownolegly do glownego lancucha (enrichment -> verification -> curation -> export)

## Metryki

| Metryka | Znaczenie |
|---------|-----------|
| precision | ile z wygenerowanych kandydatow jest poprawnych |
| recall | ile z oczekiwanych kandydatow zostalo znalezionych |
| false_positive_rate | ile falszywych trafien wzgledem wszystkich negatywow |
| time_per_record_s | czas przetwarzania na rekord |
| cost_per_record_usd | koszt API na rekord |

## Czego jeszcze brakuje przed pierwszym prawdziwym runem

1. **API key (GEMINI_API_KEY)**: Prawdziwy run wymaga dostepu do modelu. Mock run pokazuje perfekcyjne wyniki bo kopiuje ground-truth jako predykcje — prawdziwy run pokaze roznice miedzy wariantami.
2. **Wiecej wariantow**: Obecnie sa 3 seed warianty (Gemini Flash v1, Gemini Pro v2, Gemini Flash v3-strict). Dodanie wariantow z roznymi progi confidence, roznymi strategiami OCR itp. jest zachecane.
3. **Powtorzenie benchmarku na wiekszej probce**: 82 rekordy to minimum; docelowo probka powinna byc rozszerzona o kolejne urzadzenia i typy czesci.
