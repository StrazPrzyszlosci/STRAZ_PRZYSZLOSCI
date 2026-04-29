# Manual Review Rubric And Decision Packet

Generated: 2026-04-29
Source: deferred_resolution_workpack.json (zadanie 30)
Cases: 2 manual_review

---

## 1. Cel

Ten packet daje ludzkiemu reviewerowi gotowy kontekst do podjecia decyzji
`accept` / `reject` / `defer` dla dwoch przypadkow manual_review,
ktore nie moga byc rozstrzygniete ani przez OCR, ani przez heurystyke.

Po tym packetce review jest decyzja operacyjna, a nie sledztwo zaczynane od zera.

---

## 2. Przeglad dwoch przypadkow

| Pole | Case A | Case B |
|------|--------|--------|
| **candidate_id** | candidate-0076 | candidate-0077 |
| **part_number** | BN44-00213A | QHAD01249 |
| **part_name** | Power Supply Board | Transformer |
| **device** | Samsung Power Supply Board (BN44-00213A) | Samsung Power Supply Board (BN44-00213A) |
| **triage_indicator** | `board_model_number` | `custom_wound_transformer_no_datasheet` |
| **disagreement_score** | 0.38 | 0.38 |
| **confidence** | 1.0 | 0.95 |
| **verification_verified** | null | null |
| **verification_observed_text** | (empty) | (empty) |
| **verification_raw_verified** | true | true |
| **verification_raw_observed_text** | BN44-00213A | QHAD01249 |
| **evidence_url** | https://www.youtube.com/watch?v=Abhlw8diSrk&t=6s | https://www.youtube.com/watch?v=Abhlw8diSrk&t=8s |
| **source_video** | https://www.youtube.com/watch?v=Abhlw8diSrk | https://www.youtube.com/watch?v=Abhlw8diSrk |
| **datasheet_url** | https://www.google.com/search?q=BN44-00213A schematic diagram pdf | https://www.google.com/search?q=QHAD01249 transformer datasheet |
| **footprint** | PCB | Custom Transformer Package |
| **ocr_actionable** | false | false |
| **next_action** | human_review_decision | human_review_decision |

---

## 3. Rubric: rozdzial dwoch typow przypadkow

### 3.1 Case A — Board Model Number (`BN44-00213A`)

**Charakterystyka:**

- `BN44-00213A` jest identyfikatorem plyty (board model number), nie pojedynczej czesci
- Samsung uzywa formatu `BN44-XXXXXXA` jako part number dla calych plyt zasilajacych
- To jest **katalogowy identyfikator plyty**, nie komponent na plycie
- `verification_raw_observed_text` potwierdza tekst `BN44-00213A` w zrodle wideo
- `confidence = 1.0` — najwyzsza mozliwa, enrichment jest pewny co do tekstu
- `footprint = PCB` — cala plyta, nie pojedynczy komponent
- `datasheet_url` prowadzi do schematic diagram (schemat calosci), nie datasheet pojedynczego komponentu

**Pytanie decyzyjne dla reviewera:**

> Czy `BN44-00213A` powinien byc wpisany w katalogu jako **samodzielna pozycja**
> reprezentujaca cala Power Supply Board, czy jest to identyfikator urzadzenia-
> -kontekstu, ktory nie stanowi recyklingowej czesci?

**Kryteria decyzji:**

| Decyzja | Warunek |
|---------|---------|
| **accept** | Plyty zasilajace sa w scope katalogu recyklingowego jako wymienna jednostka; `BN44-00213A` jest realnym part number uzywany w handlu i serwisie; reviewer potwierdza, ze Samsung PSU board jest realnie demontowana i sprzedawana jako czesc |
| **reject** | Katalog ma obejmowac tylko komponenty na plycie, nie cale plyty; `BN44-00213A` jest identyfikatorem urzadzenia-zrodla, nie czescia; reviewer uznaje, ze board-level entries nie sa w scope |
| **defer** | Reviewer nie ma pewnosci co do scope katalogu; potrzebuje konsensusu z maintainerem co do tego, czy cale plyty sa w scope; potrzebuje wiecej informacji o polityce katalogu |

### 3.2 Case B — Custom Wound Transformer (`QHAD01249`)

**Charakterystyka:**

- `QHAD01249` jest identyfikatorem transformera nawijanego na zamowienie (custom wound)
- Samsung uzywa kodow `QHA*` / `QHAD*` dla transformatorow dedykowanych na konkretne plyty
- Nie istnieje publiczny datasheet — custom transformery nie maja standardowego dokumentu
- `verification_raw_observed_text` potwierdza tekst `QHAD01249` w zrodle wideo
- `confidence = 0.95` — bardzo wysoka, ale nie 1.0 (transformer moze byc oznaczony z boku lub nieczytelnie)
- `footprint = Custom Transformer Package` — niestandardowa obudowa, brak uniwersalnego pinioutu
- `datasheet_url` prowadzi do ogolnego wyszukiwania, nie konkretnego datasheetu
- `triage_indicator = custom_wound_transformer_no_datasheet` — system juz zweryfikowal brak datasheetu

**Pytanie decyzyjne dla reviewera:**

> Czy `QHAD01249` powinien byc wpisany w katalogu jako czesc recyklingowa,
> mimo braku datasheetu, pinoutu i niestandardowej obudowy?

**Kryteria decyzji:**

| Decyzja | Warunek |
|---------|---------|
| **accept** | Transformery sa realnie odzyskiwane z plyt zasilajacych; `QHAD01249` jest unikalnym identyfikatorem uzywany przez Samsung; nawet bez datasheetu, czesc jest wymienne jako calosc (nie do nawijania, ale do wymiany plyta-po-plycie); reviewer potwierdza, ze custom transformer jest realnym kandydatem do recyklingu jako calosc |
| **reject** | Bez datasheetu nie da sie okreslic parametrow elektrycznych; custom transformer nie jest uniwersalnie zamienny; recykling transformera jako calosc jest malo prawdopodobny bez znajomosci parametrow; reviewer uznaje, ze wpis bez parametrow jest gorszy niz brak wpisu |
| **defer** | Reviewer potrzebuje dodatkowej weryfikacji (np. czy inni sprzedawcy oferuja ten transformer); potrzebuje informacji o tym, czy katalog dopuszcza wpisy bez datasheetu; mozna poprosic o OCR na wideo celem dodatkowego potwierdzenia kodu |

---

## 4. Porownanie dwoch przypadkow

| Aspekt | BN44-00213A (Board) | QHAD01249 (Transformer) |
|--------|---------------------|-------------------------|
| Typ identyfikatora | Board model number | Custom component code |
| Dostepnosc datasheetu | Schematic diagram (ogolny) | Brak |
| Uniwersalnosc | Plyta jest wymienne caloscia | Transformer jest dedykowany do konkretnej plyty |
| Scope recyklingu | Plyta jako calosc = realna jednostka | Transformer jako calosc = kontrowersyjny |
| Confidence | 1.0 (pewny tekst) | 0.95 (prawie pewny tekst) |
| Kluczowe ryzyko | Czy cale plyty sa w scope? | Czy wpis bez parametrow jest uzywany? |
| Analogia | Jak entry dla `Dell M4800 motherboard` | Jak entry dla `transformer model X bez specyfikacji` |

---

## 5. Evidence Snapshot

Zrodlo: `deferred_resolution_workpack.json` (zadanie 30), `verification_triage.jsonl`

### 5.1 candidate-0076 (BN44-00213A)

```json
{
  "candidate_id": "candidate-0076",
  "part_number": "BN44-00213A",
  "part_name": "Power Supply Board",
  "device": "Samsung Power Supply Board (BN44-00213A)",
  "disagreement_score": 0.38,
  "confidence": 1.0,
  "triage_indicators": ["board_model_number"],
  "evidence_url": "https://www.youtube.com/watch?v=Abhlw8diSrk&t=6s",
  "source_video": "https://www.youtube.com/watch?v=Abhlw8diSrk",
  "datasheet_url": "https://www.google.com/search?q=BN44-00213A schematic diagram pdf",
  "footprint": "PCB",
  "ocr_actionable": false,
  "verification_raw_verified": true,
  "verification_raw_observed_text": "BN44-00213A"
}
```

### 5.2 candidate-0077 (QHAD01249)

```json
{
  "candidate_id": "candidate-0077",
  "part_number": "QHAD01249",
  "part_name": "Transformer",
  "device": "Samsung Power Supply Board (BN44-00213A)",
  "disagreement_score": 0.38,
  "confidence": 0.95,
  "triage_indicators": ["custom_wound_transformer_no_datasheet"],
  "evidence_url": "https://www.youtube.com/watch?v=Abhlw8diSrk&t=8s",
  "source_video": "https://www.youtube.com/watch?v=Abhlw8diSrk",
  "datasheet_url": "https://www.google.com/search?q=QHAD01249 transformer datasheet",
  "footprint": "Custom Transformer Package",
  "ocr_actionable": false,
  "verification_raw_verified": true,
  "verification_raw_observed_text": "QHAD01249"
}
```

---

## 6. Instrukcja dla reviewera

### Krok 1: Przeczytaj kontekst

- Przejrzyj powyzszy rubric i evidence snapshot
- Obejrzyj wideo: https://www.youtube.com/watch?v=Abhlw8diSrk (t=6s dla board, t=8s dla transformer)
- Opcjonalnie: sprawdz datasheet_url w wyszukiwarce

### Krok 2: Podejmij decyzje

Dla kazdego z dwoch przypadkow wybierz jedna z trzech decyzji:

| Decyzja | Znaczenie |
|---------|-----------|
| `accept` | Kandydat jest realnym i uytecznym wpisem katalogowym |
| `reject` | Kandydat nie powinien byc w katalogu |
| `defer` | Za malo informacji, potrzeba wiecej kontekstu lub konsensusu |

### Krok 3: Zapisz decyzje

Uzyj mechanizmu z `HUMAN_APPROVAL_LEDGER.md`:

```bash
python3 PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py record-review \
  --candidate-id candidate-0076 \
  --decision <approved|rejected|defer> \
  --reviewed-by "TWOJ IDENTYFIKATOR" \
  --note "Uzasadnienie decyzji"
```

```bash
python3 PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py record-review \
  --candidate-id candidate-0077 \
  --decision <approved|rejected|defer> \
  --reviewed-by "TWOJ IDENTYFIKATOR" \
  --note "Uzasadnienie decyzji"
```

### Krok 4: Weryfikuj stan

```bash
python3 PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py review-status
```

### Krok 5: Sprawdz export gate

```bash
python3 PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py export-gate
```

---

## 7. Pola decyzyjne do wypelnienia

Reviewer wypelnia ponizsze pola przez `record-review` (nie reczna edycja):

| Pole | Wartosc | Opis |
|------|---------|------|
| `candidate_id` | `candidate-0076` lub `candidate-0077` | ID z workpacka |
| `decision` | `approved` / `rejected` / `defer` | Decyzja reviewera |
| `reviewed_by` | (identyfikator reviewera) | Prawdziwe imie lub handle, nie fikcja |
| `note` | (uzasadnienie) | Dlaczego ta decyzja, co sprawdzono |

---

## 8. Co ten packet NIE robi

- Nie podejmuje decyzji za reviewera — zadne decyzje nie sa zapisane
- Nie wpisuje fikcyjnych reviewerow — `reviewed_by` musi byc prawdziwa osoba
- Nie modyfikuje `curation_review_queue.jsonl` bez `record-review`
- Nie otwiera export gate — to zalezy od wynikow review
- Nie udaje, ze rubric zastepuje ludzki sad

---

## 9. Powiazane artefakty

| Artefakt | Sciezka |
|----------|---------|
| Deferred resolution workpack (JSON) | `autonomous_test/reports/deferred_resolution_workpack.json` |
| Deferred resolution workpack (MD) | `autonomous_test/reports/deferred_resolution_workpack.md` |
| Verification report | `autonomous_test/reports/verification_report.md` |
| Verification triage | `autonomous_test/reports/verification_triage.jsonl` |
| Human approval ledger | `docs/HUMAN_APPROVAL_LEDGER.md` |
| Verification runbook | `execution_packs/pack-project13-kaggle-verification-01/RUNBOOK.md` |
| OCR deferred case packet | `docs/OCR_DEFERRED_CASE_SELECTOR_AND_PROMPT_PACKET.md` |
