# Human Approval Ledger

## Cel

Ten dokument opisuje jawny mechanizm zapisu ludzkich review decisions dla kandydatow `pending_human_approval` w curation pipeline. Mechanizm zastepuje reczna, niesformatowana edycja JSON-a strukturalnym ledgerem z komendami CLI.

---

## 1. Problem

Export gate (`curate_candidates.py export-gate`) pozostaje BLOCKED dopoki:
- wszystkie kandydaci `pending_human_approval` nie zostana rozstrzygnieci,
- co najmniej jeden ludzki approval nie zostanie zapisany.

Wczesniej jedyna sciezka byla reczna edycja `curation_review_queue.jsonl` — ustawianie `reviewed_by` i `reviewed_at` recznie w JSONL. To bylo:
- podatne na bledy formatu,
- nieaudytowalne (brak historii zmian),
- niejawne (trzeba bylo wiedziec, gdzie i co dopisac).

---

## 2. Mechanizm: `record-review` i `review-status`

### 2.1 Komenda `record-review`

Zapisuje ludzka decyzje review dla kandydata z kolejki review:

```bash
python3 PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py record-review \
  --candidate-id candidate-0005 \
  --decision approved \
  --reviewed-by "Jan Kowalski" \
  --note "MPN potwierdzony w datasheet Texas Instruments"
```

Parametry:
- `--candidate-id` (wymagany) — ID kandydata z review queue
- `--decision` (wymagany) — jeden z: `approved`, `rejected`, `defer`
- `--reviewed-by` (wymagany) — nazwa lub identyfikator reviewera (bez fikcyjnych osob)
- `--note` (opcjonalny) — notatka tlumaczaca decyzje

Efekt:
1. Tworzy wpis w `human_review_ledger.jsonl` z pelnym kontekstem decyzyjnym
2. Aktualizuje `curation_review_queue.jsonl`:
   - `approved` → `review_status` = `approved`, `reviewed_by` i `reviewed_at` wypelnione
   - `rejected` → `review_status` = `human_rejected`, `curation_decision` zmienione na `reject`
   - `defer` → `review_status` = `deferred`, wpis pozostaje poza exportem

### 2.2 Komenda `review-status`

Pokazuje aktualny stan review i gotowosc export gate:

```bash
python3 PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py review-status
```

Wyswietla:
- podzial na kategorie review_status z counts
- liste kandydatow `pending_human_approval` z kontekstem
- liste kandydatow `approved` z informacja o reviewerze
- czy export gate jest gotowy do otwarcia

---

## 3. Format ledgera

Kazdy wpis w `human_review_ledger.jsonl` ma format:

```json
{
  "ledger_id": "review-candidate-0005-2026-04-27-20-30-00",
  "candidate_id": "candidate-0005",
  "part_number": "M425R1GB4BB0-CWM0D",
  "part_name": "Battery Connector",
  "device": "Lenovo Laptop",
  "previous_review_status": "pending_human_approval",
  "review_decision": "approved",
  "reviewed_by": "Jan Kowalski",
  "reviewed_at": "2026-04-27T20:30:00Z",
  "note": "MPN potwierdzony w datasheet Texas Instruments",
  "curation_decision_before": "accept",
  "verification_status": "confirmed",
  "triage_category": "likely_confirmed"
}
```

Pola:
- `ledger_id` — unikalny identyfikator wpisu
- `candidate_id` — powiazanie z review queue
- `previous_review_status` — stan przed decyzja
- `review_decision` — decyzja reviewera: `approved`, `rejected`, `defer`
- `reviewed_by` — identyfikator reviewera (zawsze wymagany, nigdy fikcyjny)
- `reviewed_at` — timestamp UTC
- `note` — dowolna notatka reviewera

---

## 4. Flow: pending_human_approval -> approved/rejected/defer

```text
1. curate_candidates.py review-queue
   -> generuje curation_review_queue.jsonl
   -> kandydaci z triage=likely_confirmed dostaja review_status=pending_human_approval

2. curate_candidates.py review-status
   -> pokazuje ile i ktore kandydaty czekaja na review

3. Dla kazdego pending_human_approval:
   curate_candidates.py record-review \
     --candidate-id <ID> \
     --decision <approved|rejected|defer> \
     --reviewed-by <REVIEWER_NAME> \
     --note <OPTIONAL_NOTE>
   -> zapisuje wpis w human_review_ledger.jsonl
   -> aktualizuje curation_review_queue.jsonl

4. curate_candidates.py review-status
   -> weryfikuje ze nie ma juz pending_human_approval

5. curate_candidates.py export-gate
   -> sprawdza warunki gate
   -> jesli OPEN: mozna uruchomic apply i export
   -> jesli BLOCKED: pokazuje konkretne kroki do odblokowania
```

---

## 5. Jak review wplywa na export gate

| Zmiana review | Wplyw na export gate |
|---------------|---------------------|
| `pending_human_approval` -> `approved` | Zmniejsza liczbe pending, zwieksza liczbe human approvals |
| `pending_human_approval` -> `human_rejected` | Zmniejsza liczbe pending, kandydat nie wchodzi do exportu |
| `pending_human_approval` -> `deferred` | Zmniejsza liczbe pending, ale kandydat nadal blokuje `OPEN`, dopoki pozostaje `deferred` |
| Wszystkie pending i deferred rozstrzygniete + min. 1 approved | Gate moze przejsc na OPEN (jesli pozostale checki przechodza) |

Warunki export gate:
1. `no_pending_approvals` — PASS gdy 0 kandydatow z `review_status=pending_human_approval`
2. `no_unresolved_deferrals` — FAIL gdy sa deferred; blokuje `OPEN`, nawet jesli approved sa juz gotowe do `apply`
3. `catalog_validation_passes` — walidacja spojnosci katalogu
4. `human_review_recorded` — PASS gdy min. 1 kandydat z `review_status=approved` i `reviewed_by` wypelnione

---

## 6. Co musi zrobic prawdziwy reviewer

1. Uruchom `review-status` aby zobaczyc kandydatow do review
2. Dla kazdego kandydata `pending_human_approval`:
   - sprawdz part_number, part_name, device, triage_category w kontekscie
   - podejmij decyzje: approved (potwierdzam), rejected (odrzucam), defer (wstrzymuje)
   - zapisz decyzje przez `record-review` ze swoim identyfikatorem jako `--reviewed-by`
3. Po rozstrzygnieciu wszystkich pending i deferred, uruchom `export-gate`
4. Jesli gate OPEN, mozna przejsc do `apply` i `export-all`

---

## 7. Bloker: brak prawdziwych osob do review

Jesli nie ma jeszcze prawdziwych osob do review:
- mechanizm `record-review` jest gotowy do uzycia, ale nie wpisuj fikcyjnych reviewerow
- `--reviewed-by` jest wymagany i nie akceptuje pustych wartosci
- export gate pozostanie BLOCKED dopoki prawdziwy reviewer nie zapisze decyzji i dopoki w queue pozostaja `deferred`
- to jest poprawne: nie udajemy, ze review zostalo wykonane

Placeholder packet: `execution_packs/pack-project13-curation-01/REVIEW_ASSIGNMENT_PACKET.md`

Packet zostal zaktualizowany w zadaniu 35 i enumeruje wszystkie 14 pending cases z kontekstem, propozycja batchingu (A: laptop, B: inne, C: e-waste/desktop) i polami do wypelnienia przez maintainera.

---

## 8. Komenda list-pending

Od zadania 35 dostepna jest komenda `list-pending`, ktora generuje maszynowy eksport pending cases z batch annotation:

```bash
python3 PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py list-pending
```

- Output JSON: `autonomous_test/reports/pending_human_approval_list.json`
- Zawiera: `total_pending`, `batch_rules` (z match_devices i recommended_mode), `pending_entries` (z batch annotation)
- Automatycznie zsynchronizowany z `curation_review_queue.jsonl` — nie wymaga recznej aktualizacji
- Uzyj przed review session zeby miec aktualna liste z batch przydzialem
