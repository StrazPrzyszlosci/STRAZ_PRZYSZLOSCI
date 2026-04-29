# OCR Deferred Case Selector And Prompt Packet

Generated: 2026-04-29
Pack: pack-project13-kaggle-verification-01
Task: Zlecenie Glowne 36

## Cel

Chirurgiczny execution surface dla 7 cases `ocr_needed`, ktory pozwala operatorowi z `GEMINI_API_KEY` wziasc pojedynczy case albo grupe cases i wykonac OCR bez ponownego sledztwa po wielu plikach.

## Mapa case'ow OCR

| # | candidate_id | part_number | part_name | device | expected_text | evidence_url |
|---|-------------|-------------|-----------|--------|---------------|-------------|
| 1 | candidate-0008 | 3336220400007 | RAM slots | Dell Precision M4800 | 3336220400007 | https://www.youtube.com/watch?v=7ZbFOgtHvFg&t=127s |
| 2 | candidate-0012 | UE50MU6102KXXH | Płyta główna (Mainboard) | Samsung UE50MU6102K | UE50MU6102KXXH | https://www.youtube.com/watch?v=OONXjU17iNc&t=9s |
| 3 | candidate-0018 | 1244-2 | Speaker | Samsung UE32EH4000 | 1244-2 | https://www.youtube.com/watch?v=IJYjZasRQ6w&t=227s |
| 4 | candidate-0073 | LF80537 | Heat Sink / Heat Pipe | Laptop (Generic/Unspecified) | LF80537 | https://www.youtube.com/watch?v=WRKu1dDCVEw&t=306s |
| 5 | candidate-0074 | TS8121K | CPU | Laptop (Generic/Unspecified) | TS8121K | https://www.youtube.com/watch?v=WRKu1dDCVEw&t=442s |
| 6 | candidate-0079 | BD243C | Transistor | Samsung Power Supply Board (BN44-00213A) | BD243C | https://www.youtube.com/watch?v=Abhlw8diSrk&t=486s |
| 7 | candidate-0080 | QHA001249 | Capacitor | Samsung Power Supply Board (BN44-00213A) | QHA001249 | https://www.youtube.com/watch?v=Abhlw8diSrk&t=1559s |

## Mapa: candidate_id -> evidence_url -> expected_text -> next command

### candidate-0008
- evidence_url: https://www.youtube.com/watch?v=7ZbFOgtHvFg&t=127s
- expected_text: 3336220400007
- next command: `GEMINI_API_KEY=... python3 scripts/verify_candidates.py ocr-selector --case candidate-0008`

### candidate-0012
- evidence_url: https://www.youtube.com/watch?v=OONXjU17iNc&t=9s
- expected_text: UE50MU6102KXXH
- next command: `GEMINI_API_KEY=... python3 scripts/verify_candidates.py ocr-selector --case candidate-0012`

### candidate-0018
- evidence_url: https://www.youtube.com/watch?v=IJYjZasRQ6w&t=227s
- expected_text: 1244-2
- next command: `GEMINI_API_KEY=... python3 scripts/verify_candidates.py ocr-selector --case candidate-0018`

### candidate-0073
- evidence_url: https://www.youtube.com/watch?v=WRKu1dDCVEw&t=306s
- expected_text: LF80537
- next command: `GEMINI_API_KEY=... python3 scripts/verify_candidates.py ocr-selector --case candidate-0073`

### candidate-0074
- evidence_url: https://www.youtube.com/watch?v=WRKu1dDCVEw&t=442s
- expected_text: TS8121K
- next command: `GEMINI_API_KEY=... python3 scripts/verify_candidates.py ocr-selector --case candidate-0074`

### candidate-0079
- evidence_url: https://www.youtube.com/watch?v=Abhlw8diSrk&t=486s
- expected_text: BD243C
- next command: `GEMINI_API_KEY=... python3 scripts/verify_candidates.py ocr-selector --case candidate-0079`

### candidate-0080
- evidence_url: https://www.youtube.com/watch?v=Abhlw8diSrk&t=1559s
- expected_text: QHA001249
- next command: `GEMINI_API_KEY=... python3 scripts/verify_candidates.py ocr-selector --case candidate-0080`

## Grupowanie po zrodle wideo (do pojedynczego przebiegu OCR)

Cases z tego samego wideo mozna uruchomic razem w jednym przebiegu:

| Video source | Cases | candidate_ids |
|-------------|-------|---------------|
| https://www.youtube.com/watch?v=7ZbFOgtHvFg | 1 | candidate-0008 |
| https://www.youtube.com/watch?v=OONXjU17iNc | 1 | candidate-0012 |
| https://www.youtube.com/watch?v=IJYjZasRQ6w | 1 | candidate-0018 |
| https://www.youtube.com/watch?v=WRKu1dDCVEw | 2 | candidate-0073, candidate-0074 |
| https://www.youtube.com/watch?v=Abhlw8diSrk | 2 | candidate-0079, candidate-0080 |

Wybor grupy:
```bash
python3 scripts/verify_candidates.py ocr-selector --group "https://www.youtube.com/watch?v=WRKu1dDCVEw"
```

## Instrukcja: co uruchomic gdy GEMINI_API_KEY jest dostepny

### Krok 1: Ustaw klucz

```bash
export GEMINI_API_KEY=your_key_here
```

### Krok 2: Wybierz case lub grupe

```bash
# Pojedynczy case
python3 scripts/verify_candidates.py ocr-selector --case candidate-0008

# Grupa cases z tego samego wideo
python3 scripts/verify_candidates.py ocr-selector --group "https://www.youtube.com/watch?v=WRKu1dDCVEw"

# Wszystkie OCR cases
python3 scripts/verify_candidates.py ocr-selector
```

### Krok 3: Uruchom OCR

```bash
GEMINI_API_KEY=... python3 scripts/verify_candidates.py ocr-check
```

### Krok 4: Przejrzyj wyniki

```bash
# Sprawdz verification_scored.jsonl -> pole ocr_check per candidate_id
```

### Krok 5: Re-run pipeline po OCR

```bash
python3 scripts/verify_candidates.py run
python3 scripts/curate_candidates.py dry-run --fallback-test-db
python3 scripts/curate_candidates.py export-gate
```

## Sciezki rozstrzygniecia per case

Dla kazdego OCR case wynik prowadzi do jednej z 3 sciezek:

| Wynik OCR | Akcja |
|-----------|-------|
| confirmed | promote to confirmed -> re-run curation pipeline |
| rejected | reject -> update status_resolution -> re-run curation |
| inconclusive | escalate to manual_review |

## Oddzielenie toru OCR od manual_review

Ten packet dotyczy wylacznie 7 cases `ocr_needed`. Nie zawiera zadnych cases z toru `manual_review` (candidate-0076, candidate-0077). Te cases znajduja sie w `deferred_resolution_workpack.json` pod kluczem `manual_review` i wymagaja decyzji czlowieka, nie OCR.

## Artefakty

- JSON packet: `autonomous_test/reports/ocr_deferred_case_packet.json`
- Zrodlowy workpack: `autonomous_test/reports/deferred_resolution_workpack.json`
- Skrypt: `scripts/verify_candidates.py` (komenda `ocr-selector`)

## Co nadal wymaga czlowieka po OCR

Nawet po zakonczeniu wszystkich 7 OCR przebiegow:

1. Wyniki OCR trzeba przejrzec (pole `ocr_check` w `verification_scored.jsonl`) — automation promuje/rejectuje, ale wyniki inconclusive wymagaja ludzkiej decyzji
2. 2 cases `manual_review` (candidate-0076: BN44-00213A, candidate-0077: QHAD01249) nie sa rozwiazywalne przez OCR
3. Pipeline curation trzeba re-runowac po rozstrzygnieciu wszystkich deferred cases
4. Export gate pozostaje BLOCKED dopoki pending_human_approval cases nie zostana rozstrzygniete
