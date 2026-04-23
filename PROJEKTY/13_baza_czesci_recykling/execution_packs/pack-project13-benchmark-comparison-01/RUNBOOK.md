# Runbook Dla Pack Project13 Benchmark Comparison 01

## Cel

Ten pack pozwala porownywac rozne prompty, modele i workflowy na tej samej probce danych `Project 13`.

Docelowy przeplyw:

```text
fixed test sample -> variant A vs variant B -> metrics -> benchmark report -> PR
```

## Co trzeba miec przed startem

- konto `GitHub` i fork repo
- konto `Kaggle` (dla pelnych runow) albo lokalne srodowisko z kluczem API
- klucz `GEMINI_API_KEY`
- opcjonalnie `YOUTUBE_API_KEY`, jesli benchmark wymaga odswiezenia probki discovery
- zdefiniowana probke testowa (komenda `init-sample`) i zweryfikowane ground-truth labele

## Komendy

### Inicjalizacja probki testowej

```bash
python3 PROJEKTY/13_baza_czesci_recykling/scripts/run_benchmark.py init-sample
```

Generuje `benchmark_sample.jsonl` z `test_db.jsonl`. Labele `is_valid_part` sa heurystyczne i wymagaja ludzkiego review.

### Walidacja probki

```bash
python3 PROJEKTY/13_baza_czesci_recykling/scripts/run_benchmark.py validate-sample
```

Sprawdza, czy wszystkie ground-truth labele zostaly zweryfikowane przez czlowieka.

### Lista wariantow

```bash
python3 PROJEKTY/13_baza_czesci_recykling/scripts/run_benchmark.py list-variants
```

Pokazuje dostepne konfiguracje wariantow w `autonomous_test/benchmarks/variants/`.

### Uruchomienie wariantu

```bash
python3 PROJEKTY/13_baza_czesci_recykling/scripts/run_benchmark.py run --variant prompt-v1-gemini-flash
```

Uruchamia benchmark dla konkretnego wariantu. W trybie scaffold (brak API key) generuje mock wynik dla walidacji pipeline'u.

### Porownanie wariantow

```bash
python3 PROJEKTY/13_baza_czesci_recykling/scripts/run_benchmark.py compare
```

Wypisuje tabele porownawcza wszystkich uruchomionych wariantow.

### Generowanie raportu

```bash
python3 PROJEKTY/13_baza_czesci_recykling/scripts/run_benchmark.py report
```

Generuje `benchmark_report.md` z pelnym opisem probki, wariantow, metryk i wnioskow.

## Krok 1. Zainicjuj probke testowa

1. Uruchom `init-sample` zeby wygenerowac `benchmark_sample.jsonl`.
2. Otworz probke i zweryfikuj ground-truth labele `is_valid_part` dla kazdego rekordu.
3. Ustaw `label_pending_review` na `false` dla kazdego sprawdzonego rekordu.
4. Uruchom `validate-sample` — musi pokazac 0 pending przed przejsciem dalej.

### Kryteria ground-truth

- `is_valid_part=true`: Ekstrakcja identyfikuje realny, specyficzny komponent elektroniczny z prawidlowym lub wiarygodnym MPN (manufacturer part number). Designatory, identyfikatory plyt, i ogolne opisy bez konkretnego numeru czesci NIE sa valid.
- `is_valid_part=false`: Ekstrakcja jest falszywie pozytywna: model plyty, lista designatorow, ogolna etykieta, artefakt OCR (np. "WARSZTAT AUTOMATYKI"), date code, albo tekst nieidentyfikujacy konkretnego komponentu.

## Krok 2. Zdefiniuj warianty do porownania

Kazdy wariant to plik JSON w `autonomous_test/benchmarks/variants/`:

```json
{
  "variant_id": "prompt-v1-gemini-flash",
  "description": "Original extraction prompt with Gemini Flash",
  "model": "gemini-2.0-flash",
  "prompt_template": "v1",
  "parameters": {"temperature": 0.1, "top_p": 0.95},
  "cost_per_1k_tokens_input": 0.000075,
  "cost_per_1k_tokens_output": 0.00030
}
```

Przykladowe wymiary porownania:

- rozne prompty extraction parts
- rozne modele multimodalne (Gemini Flash vs Pro)
- rozne strategie OCR i frame check
- rozne progi filtrowania kandydatow

## Krok 3. Uruchom benchmark

1. Uruchom kazdy wariant: `run_benchmark.py run --variant <name>`
2. Skrypt oblicza metryki:
   - `precision`: ile z wygenerowanych kandydatow jest poprawnych
   - `recall`: ile z oczekiwanych kandydatow zostalo znalezionych
   - `false_positive_rate`: ile falszywych trafien na rekord
   - `cost_per_record`: zuzycie tokenow API na rekord
   - `time_per_record`: czas przetwarzania na rekord
3. Wyniki zapisane w `benchmark_metrics.json`.

## Krok 4. Porownaj i wygeneruj raport

1. Uruchom `compare` dla szybkiego podsumowania w terminalu.
2. Uruchom `report` dla pelnego raportu markdown.
3. Raport zawiera: opis probki, opis wariantow, tabele metryk, wnioski, ograniczenia.

## Krok 5. Otworz PR

1. Stworz branch w formacie `benchmark-<variant-a>-vs-<variant-b>`.
2. Commituj raport, metryki, probke testowa i konfiguracje wariantow.
3. Otworz PR do upstream z trescia z `PR_TEMPLATE.md`.

## Czego pack nie powinien robic

- nie powinien modyfikowac kanonicznego katalogu (`data/devices.jsonl`, `data/parts_master.jsonl`, `data/device_parts.jsonl`)
- nie powinien generowac kandydatow do lancucha kuracji
- nie powinien uruchamiac exportu downstream
- nie powinien automatycznie promowac wynikow benchmarku do katalogu

## Aktualny status

Pack jest `benchmarked`:

- execution surface istnieje (`run_benchmark.py`),
- probka testowa jest zweryfikowana z 82 rekordami z `test_db.jsonl` (28 valid, 54 invalid, 0 pending review),
- 3 seed warianty sa dostepne w `variants/` (prompt-v1-gemini-flash, prompt-v2-gemini-pro, prompt-v3-gemini-flash-strict),
- mock benchmark przebiegl na wszystkich 3 wariantach — pokazuje perfekcyjne wyniki (scaffold validation),
- metryki, schematy i raport sa zdefiniowane,
- prawdziwy run wymaga API key (GEMINI_API_KEY) i pokaze rzeczywiste roznice miedzy wariantami.

## Minimalne kryterium sukcesu

Pack bedzie gotowy do pierwszego realnego uruchomienia, gdy:

- bedzie mial API key (GEMINI_API_KEY) do wywolania modelu,
- prawdziwy run pokaze roznice miedzy wariantami w metrykach jakosciowych i kosztowych,
- reviewer dostanie raport z prawdziwych przebiegow zamiast mock wynikow.

## Schematy

- `schemas/benchmark_sample.schema.json` — schemat rekordu probki testowej
- `schemas/benchmark_variant.schema.json` — schemat konfiguracji wariantu
- `schemas/benchmark_metrics.schema.json` — schemat wpisu metryk
