# Review Assignment Packet

## Cel

Ten packet enumeruje wszystkie kandydaty `pending_human_approval` z aktualnego review queue, proponuje sensowny batching i zostawia jawne miejsca na prawdziwych reviewerow. Nie zawiera fikcyjnych przydzialow.

Packet jest zsynchronizowany z wyjsciow komendy `list-pending` (zadanie 35), ktora generuje maszynowy eksport `pending_human_approval_list.json` z batch annotation. Reczna edycja nie jest wymagana — `list-pending` odtwarza aktualny stan z `curation_review_queue.jsonl`.

---

## 1. Kandydaci do review — 14 pending_human_approval

Wszyscy kandydaci ponizej maja `review_status=pending_human_approval`, `verification_status=confirmed`, `triage_category=likely_confirmed`, `status_resolution_policy=likely_confirmed_promote_v2`. Zostali auto-promotowani z disputed per status resolution policy v2.

### Batch A: Komponenty laptopowe (Lenovo + ASUS + Compal) — 6 cases

Kandydaci z laptopow, glownie IC i connektory. Wymagaja weryfikacji MPN w datasheetach producentow.

| # | candidate_id | part_number | part_name | device | Kontekst decyzji |
|---|--------------|-------------|-----------|--------|------------------|
| 1 | candidate-0005 | M425R1GB4BB0-CWM0D | Battery Connector | Lenovo Laptop | Samsung IC MPN, potwierdzic w Samsung datasheet |
| 2 | candidate-0006 | P28A41E | SMD Capacitors | Lenovo Laptop | Skrocony kod SMD, potwierdzic dekodowanie |
| 3 | candidate-0007 | 230130, 2R2, 33 25V H33 | SMD Resistors | Lenovo Laptop | Multiple SMD kody w jednym polu, potwierdzic czy poprawne |
| 4 | candidate-0032 | JKB1, JKB2 | PQB11 | Compal LA-G021P | Designatory zamiast MPN? potwierdzic czy JKB1/JKB2 to poprawne MPN |
| 5 | candidate-0041 | INTEL 08 i7-628M | Intel Core i3-380M Processor | ASUS K52F | Intel CPU marking, potwierdzic czy "i7-628M" to poprawny model (moze i3-380M) |
| 6 | candidate-0042 | BD82HM55 SLGZR | Thermal Paste | ASUS K52F | Intel chipset FPO/BPO marking, potwierdzic czy to MPN czy marking code |

### Batch B: Komponenty z innych urzadzen — 5 cases

Kandydaci z roznych zrodel (Samsung TV, Electrolux, vintage, LED). Roznorodne kategorie.

| # | candidate_id | part_number | part_name | device | Kontekst decyzji |
|---|--------------|-------------|-----------|--------|------------------|
| 7 | candidate-0015 | K6100 1124 08.24 | Układ scalony (prawdopodobnie EMMC) | Samsung UE50MU6102K | Kod IC z TV, potwierdzic producenta i MPN |
| 8 | candidate-0028 | MINIJST E DC546134603 ST | Washing machine control board (PCB) | Electrolux EnergySaver | PCB marking Electrolux, potwierdzic czy to MPN czy kod PCB |
| 9 | candidate-0054 | RM 121 | Unitra RM 121 Automatic Radio | Various Vintage Electronics | Vintage radio model jako MPN, potwierdzic czy model=MPN |
| 10 | candidate-0057 | LDF-12V16W | LED Power Supply Unit | DesignLight LDF-12V16W | DesignLight PSU model, potwierdzic czy to jest poprawny MPN |
| 11 | candidate-0062 | V17081 | PWM Controller | Gigabyte Graphics Card | PWM controller marking, potwierdzic producenta i MPN |

### Batch C: IC z e-waste + desktop — 3 cases

Kandydaci z e-waste i desktop. Mniejsze konteksty, trudniejsi do weryfikacji.

| # | candidate_id | part_number | part_name | device | Kontekst decyzji |
|---|--------------|-------------|-----------|--------|------------------|
| 12 | candidate-0019 | M51413ASP | Integrated Circuit (IC) | Unknown Electronic Waste | Mitsubishi IC MPN, potwierdzic w datasheet |
| 13 | candidate-0020 | MT1588AE 0311-ARS HF986 | Integrated Circuit (IC) | Unknown Electronic Waste | Mediatek IC marking, potwierdzic czy to pelny MPN |
| 14 | candidate-0052 | 775i65G | CPU Socket | Generic Desktop Motherboard (Socket 939) | Asrock model plyty jako MPN, potwierdzic czy to MPN czy model plyty |

---

## 2. Propozycja batchingu

### Grupowanie

| Batch | Kandydatow | Logiczna podstawa | Zalecany tryb review |
|-------|-----------|-------------------|---------------------|
| A | 6 | Komponenty laptopowe — podobny typ MPN (IC, marking codes) | `per-batch` — reviewer moze pracowac nad cala grupa z jednym kontekstem (laptop components) |
| B | 5 | Komponenty z roznych urzadzen — rozny typ (IC, PCB, PSU, vintage) | `per-candidate` — rozny kontekst per kandydat, trudniej batchowac |
| C | 3 | IC z e-waste + desktop — najmniejszy kontekst | `per-batch` — malo cases, mozna zamknac w jednej sesji |

### Zalecenia

1. **Batch A** jest najlatwiejszy do szybkiego review — to glownie IC marking codes z laptopow. Reviewer z doswiadczeniem w komponentach elektronicznych moze zamknac te 6 cases w jednej sesji.
2. **Batch B** wymaga wiecej kontekstu per kandydat — vintage radio vs LED PSU vs PCB marking to rozne domeny.
3. **Batch C** ma najmniej cases — mozna polaczyc z Batch A jesli reviewer ma czas.
4. Nie zaleca sie review wszystkich 14 cases naraz przez jedna osobe — lepsza rotacja (zgodnie z governance).

---

## 3. Przypisanie reviewerow

| Rola | Osoba | Identyfikator do `--reviewed-by` | Przypisany batch |
|------|-------|----------------------------------|-----------------|
| primary_curation_reviewer | __DO_UZUPELNIENIA__ | __DO_UZUPELNIENIA__ | __DO_UZUPELNIENIA__ (zalecane: Batch A + C) |
| backup_curation_reviewer | __DO_UZUPELNIENIA__ | __DO_UZUPELNIENIA__ | __DO_UZUPELNIENIA__ (zalecane: Batch B) |

Zasady (zgodne z PILOT_REVIEW_ASSIGNMENT_AND_APPROVAL_PATH.md):
- Autor curation decision nie moze byc jednoczesnie jedynym approverem
- Ta sama osoba nie powinna byc jednoczesnie primary i backup reviewerem dla tego samego batcha
- Przydzial musi byc wypelniony przed faktycznym review

---

## 4. Tryb review: per-candidate vs per-batch

### per-candidate

Kazdy kandydat jest rozpatrywany niezaleznie. Reviewer zapisuje decyzje osobno per candidate_id.

```bash
python3 PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py record-review \
  --candidate-id candidate-0005 \
  --decision approved \
  --reviewed-by "<IDENTYFIKATOR>" \
  --note "Samsung IC MPN potwierdzony w datasheet"
```

### per-batch

Reviewer rozpatruje caly batch naraz, ale zapisuje decyzje nadal per kandydat (mechanizm `record-review` nie ma batch mode — kazda decyzja jest osobnym wpisem w ledgerze).

Zalecany flow dla batcha:

```bash
# 1. Przejrzyj caly batch w review-status
python3 PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py review-status

# 2. Zapisz decyzje dla kazdego kandydata w batchu
python3 PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py record-review \
  --candidate-id candidate-0005 --decision approved \
  --reviewed-by "<IDENTYFIKATOR>" --note "Batch A: laptop IC MPN confirmed"

python3 PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py record-review \
  --candidate-id candidate-0006 --decision approved \
  --reviewed-by "<IDENTYFIKATOR>" --note "Batch A: SMD code decoded"

# ... itd. dla kazdego kandydata w batchu

# 3. Po zamknieciu batcha, sprawdz gate
python3 PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py export-gate
```

---

## 5. Najkrotszy ruch do otwarcia export gate

1. Maintainer wypelnia pola `__DO_UZUPELNIENIA__` w sekcji 3 powyzej
2. Reviewer przegladaja kandydatow w przypisanych batchach
3. Reviewer zapisuja decyzje przez `record-review` z prawdziwym `--reviewed-by`
4. Po rozstrzygnieciu wszystkich 14 pending:
   ```bash
   python3 PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py review-status
   python3 PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py export-gate
   ```
5. Gate moze przejsc na `OPEN` dopiero wtedy, gdy:
   - wszystkie `pending_human_approval` zostaly rozstrzygniete,
   - wszystkie `deferred` znikna z review queue albo polityka gate zostanie jawnie zmieniona,
   - istnieje przynajmniej 1 prawdziwy human approval zapisany przez `record-review`
6. 9 deferred pozostaje poza `apply` / `export-all`, ale dopoki maja `review_status=deferred`, `export-gate` nadal pozostaje `BLOCKED`

---

## 6. Co nadal musi dopisac prawdziwy maintainer przed review

- [ ] Kto pelni role `primary_curation_reviewer` (sekcja 3)
- [ ] Kto pelni role `backup_curation_reviewer` (sekcja 3)
- [ ] Ktory batch jest przypisany do ktorego reviewera (sekcja 3)
- [ ] Czy wymagane sa dodatkowe dowody (datasheet, OCR) przed approval dla konkretnych cases
- [ ] Czy review ma byc `per-candidate` czy `per-batch` dla kazdego batcha
- [ ] Czy kandydaci z kontekstem "model=MPN" (np. 775i65G, RM 121) wymagaja dodatkowego potwierdzenia

---

## 7. Spojnosc z zrodlami

- Counts pochodza z `curation_review_queue.jsonl` (generated 2026-04-27T21:32:09Z)
- Zgodne z `export_gate_packet.json`: 14 pending_human_approval, 9 deferred, 9 auto_approved, 50 auto_rejected
- Flow prowadzi przez `record-review` i `export-gate`, nie przez reczna edycje JSONL
- Zgodne z `HUMAN_APPROVAL_LEDGER.md` (sekcja 4: flow pending -> approved/rejected/defer)
- Zgodne z `PILOT_REVIEW_ASSIGNMENT_AND_APPROVAL_PATH.md` (role, zasady, exception flow)

---

## 8. Maszynowy eksport listy pending

Powyższa lista i batch annotation nie musza byc utrzymywane recznie. Komenda `list-pending` odtwarza aktualny stan z review queue:

```bash
python3 PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py list-pending
```

Output JSON: `autonomous_test/reports/pending_human_approval_list.json`

Zawiera:
- `total_pending` — liczba pending cases
- `batch_rules` — reguly batchingu (match_devices, recommended_mode)
- `pending_entries` — kazdy case z `candidate_id`, `part_number`, `part_name`, `device`, `batch`

Jesli kolejka review zostanie wygenerowana ponownie, `list-pending` automatycznie zsynchronizuje packet z nowym stanem.

---

## 9. Status

**READY FOR ASSIGNMENT** — packet enumeruje wszystkie 14 pending cases z kontekstem, proponuje batching i zostawia pola do wypelnienia przez maintainera. Zadne fikcyjne approvale nie zostaly wpisane. Maszynowy eksport jest dostepny przez `list-pending`.
