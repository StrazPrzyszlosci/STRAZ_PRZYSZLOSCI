# Runbook Dla Pack Project13 Kaggle Verification 01

## Cel

Ten pack domyka etap `verification chain` po wstepnym discovery i enrichment.

Docelowy przeplyw:

```text
candidate snapshot -> rule-based MPN validation -> OCR frame check (optional) -> disagreement scoring -> disputed triage -> verified snapshot + report + disagreement log + triage report
```

## Execution surface

Skrypt: `scripts/verify_candidates.py`

## Jak uruchomic

### Wymagania

- Python 3.10+
- Kandydacki snapshot z enrichment: `autonomous_test/results/test_db.jsonl`
- (Opcjonalnie) `GEMINI_API_KEY` — dla OCR weryfikacji rekordow spornych

### Dry-run (bez modyfikacji kanonicznych plikow)

```bash
python3 PROJEKTY/13_baza_czesci_recykling/scripts/verify_candidates.py dry-run
```

Outputy zapisane z sufiksem `.dry-run`. Kanoniczne pliki niezmienione.

### Pelny run

```bash
python3 PROJEKTY/13_baza_czesci_recykling/scripts/verify_candidates.py run
```

Zapisuje kanoniczne outputy do:
- `autonomous_test/results/test_db_verified.jsonl`
- `autonomous_test/reports/verification_report.md`
- `autonomous_test/reports/verification_disagreements.jsonl`
- `autonomous_test/reports/verification_triage.jsonl`

### Z OCR verification (dla rekordow spornych)

```bash
GEMINI_API_KEY=... python3 PROJEKTY/13_baza_czesci_recykling/scripts/verify_candidates.py run
```

Albo:

```bash
python3 PROJEKTY/13_baza_czesci_recykling/scripts/verify_candidates.py ocr-check --api-key YOUR_KEY
```

### Pojedyncze kroki

```bash
python3 scripts/verify_candidates.py load
python3 scripts/verify_candidates.py validate
python3 scripts/verify_candidates.py score
python3 scripts/verify_candidates.py triage
python3 scripts/verify_candidates.py snapshot
python3 scripts/verify_candidates.py report
```

## Input contract

| Pole | Wymagane | Opis |
|------|----------|------|
| `device` | tak | Nazwa urzadzenia zrodlowego |
| `part_name` | tak | Opis czesci |
| `part_number` | tak | Claimed MPN |
| `confidence` | nie | Enrichment confidence (0.0-1.0) |
| `verification.verified` | nie | Flag z enrichment OCR |
| `verification.observed_text` | nie | Tekst z OCR frame check |
| `yt_link` / `source_video` | nie | Link do zrodla wideo |

## Output contract

| Artefakt | Sciezka | Opis |
|----------|---------|------|
| Verified snapshot | `autonomous_test/results/test_db_verified.jsonl` | Wszystkie rekordy z `verification_status` i `disagreement_score` |
| Verification report | `autonomous_test/reports/verification_report.md` | Markdown: counts, metoda, sporne przypadki, ograniczenia |
| Disagreement log | `autonomous_test/reports/verification_disagreements.jsonl` | Subset: tylko rekordy `disputed` |
| Triage report | `autonomous_test/reports/verification_triage.jsonl` | Disputed records classified by triage category |

### Pole `verification_status`

- `confirmed` — MPN valid, niski disagreement, gotowy do curation
- `disputed` — MPN moze byc valid, ale sa sygnaly rozbieznosci; wymaga review
- `rejected` — MPN invalid albo wysoki disagreement; odrzucony z verification

### Pole `triage_category` (tylko dla disputed)

- `likely_confirmed` — Wysoka confidence MPN, niski disagreement; bezpieczny do auto-promote po review progow
- `ocr_needed` — OCR frame check moglby rozstrzygnac; wymaga GEMINI_API_KEY
- `manual_review` — Human reviewer potrzebny; brak automatycznej sciezki rozwiazania
- `threshold_tuning` — Rekord powinien byc odrzucony albo przekategoryzowany przez lepsze heurystyki MPN

## Co pack robi

1. Wczytuje kandydacki snapshot z etapu enrichment.
2. Waliduje MPN kazdego rekordu przez rule-based pattern matching.
3. Cross-checkuje pola z enrichment (verification flag, observed text, confidence).
4. Oblicza disagreement score (0.0 = pelna zgodnosc, 1.0 = maksymalna rozbieznosc).
5. Przypisuje `verification_status`: confirmed / disputed / rejected.
6. Klasyfikuje disputed rekordy do kategorii triage: likely_confirmed / ocr_needed / manual_review / threshold_tuning.
7. (Opcjonalnie) Uruchamia OCR frame check dla rekordow disputed przez GEMINI_API_KEY.
8. Zapisuje verified snapshot, verification report, disagreement log i triage report.

## Czego pack nie robi

- nie buduje downstream exportow (ecoEDA, InvenTree, D1)
- nie miesza rekordow confirmed z disputed bez jawnego statusu
- nie promuje danych do upstream bez PR
- nie wymaga GEMINI_API_KEY (rule-based flow dziala bez API key)

## Walidacja

```bash
python3 -m py_compile PROJEKTY/13_baza_czesci_recykling/scripts/verify_candidates.py
python3 PROJEKTY/13_baza_czesci_recykling/scripts/verify_candidates.py dry-run
```

Dry-run na 82 kandydatach z `test_db.jsonl` przechodzi bez bledow.

## Handoff do curation

Po review verification report i disagreement log:

```bash
python3 scripts/curate_candidates.py review --snapshot autonomous_test/results/test_db_verified.jsonl
python3 scripts/curate_candidates.py dry-run --fallback-test-db
```

## Co nadal blokuje pierwszy publiczny run

- brak OCR verification dla 7 rekordow `ocr_needed` (wymaga GEMINI_API_KEY)
- brak realnego Kaggle notebooka verification (obecny execution surface jest lokalny)
- 7 rekordow `threshold_tuning` wymaga poprawy heurystyk MPN zamiast recznego review
- 2 rekordy `manual_review` wymagaja obsady reviewerow
- 14 rekordow `likely_confirmed` czeka na decyzje o auto-promote do confirmed
