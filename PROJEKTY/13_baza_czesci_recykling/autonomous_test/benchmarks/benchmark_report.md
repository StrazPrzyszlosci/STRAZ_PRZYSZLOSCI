# Benchmark Report: Project 13 Part Extraction

Generated: 2026-04-23T15:06:11Z

## Test Sample

- **sample_id**: bench-sample-v1
- **total records**: 82
- **valid parts (ground truth)**: 28
- **invalid parts (ground truth)**: 54
- **source**: autonomous_test/results/test_db.jsonl

## Ground-Truth Criteria

- `is_valid_part=true`: Extraction identifies a real, specific electronic component with a valid or plausible MPN.
- `is_valid_part=false`: Extraction is a false positive: board model, designator list, generic label, OCR artifact, date code, or non-component text.

## Variants Compared

### prompt-v1-gemini-flash (mock run)

- model: `gemini-2.0-flash`
- prompt: `v1`
- parameters: `{"temperature": 0.1, "top_p": 0.95}`

### prompt-v2-gemini-pro (mock run)

- model: `gemini-2.5-pro-preview-05-06`
- prompt: `v2`
- parameters: `{"temperature": 0.05, "top_p": 0.9}`

### prompt-v3-gemini-flash-strict (mock run)

- model: `gemini-2.0-flash`
- prompt: `v3-strict`
- parameters: `{"temperature": 0.05, "top_p": 0.85}`

## Metrics Comparison

| Variant                      | Precision |    Recall |       FPR |  Time/Rec |  Cost/Rec |
|------------------------------|-----------|-----------|-----------|-----------|-----------|
| prompt-v1-gemini-flash       |    1.0000 |    1.0000 |    0.0000 |    0.0000 |  0.000000 | *
| prompt-v2-gemini-pro         |    1.0000 |    1.0000 |    0.0000 |    0.0000 |  0.000000 | *
| prompt-v3-gemini-flash-st... |    1.0000 |    1.0000 |    0.0000 |    0.0000 |  0.000000 | *

* = mock run (predictions copied from ground truth, for scaffolding validation)

## Conclusions

- Best precision: **prompt-v1-gemini-flash** (1.0000)
- Best recall: **prompt-v1-gemini-flash** (1.0000)

## Known Issues

- Ground-truth labels were initially heuristic and require human review.
- Mock runs copy predictions from ground truth and show perfect scores; real runs require API access.

## Integrity Notes

- Pack does not modify the canonical catalog or downstream artifacts.
- Benchmark results are diagnostic and not promoted to the catalog without a separate curation step.
- Test sample is fixed and reproducible between runs.
