# Export Open Readiness Packet

## Cel

Ten packet definiuje gotowy szlak wykonawczy od ostatniego approvala do export receiptu. Nie oglasza, ze gate jest OPEN — pokazuje, co robic, gdy gate przejdzie na OPEN, oraz co robic dopoki jest BLOCKED.

---

## 1. Aktualny stan export gate

**Gate: BLOCKED** (stan z `export_gate_packet.json` po walidacji z 2026-04-29)

### Gate checks

| Check | Result | Detail |
|-------|--------|--------|
| no_pending_approvals | FAIL | 14 candidates pending human approval |
| no_unresolved_deferrals | FAIL | 9 deferred candidates |
| catalog_validation_passes | PASS | Catalog validation passed |
| human_review_recorded | FAIL | No human review approval recorded |

### Blockers (3)

1. 14 accepted candidates still pending human approval (auto-promotowane z disputed, triage=likely_confirmed)
2. 9 deferred candidates remain unresolved (`7` OCR + `2` manual_review)
3. No human review approval recorded for pending candidates

### Warnings (2)

1. 7 records still deferred by verification (ocr_needed)
2. 2 records still deferred by verification (manual_review)

---

## 2. Co robic, gdy gate jest BLOCKED

Nie uruchamiaj `apply` ani `export-all`. Gate BLOCKED oznacza, ze katalog nie jest gotowy do exportu.

### Krok po kroku

```bash
# 1. Sprawdz aktualny stan review
python3 PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py review-status

# 2. Zobacz liste pending cases z batch annotation
python3 PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py list-pending

# 3. Dla kazdego pending_human_approval, zapisz decyzje reviewera
python3 PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py record-review \
  --candidate-id <CANDIDATE_ID> \
  --decision <approved|rejected|defer> \
  --reviewed-by "<REVIEWER_NAME>" \
  --note "<OPTIONAL_NOTE>"

# 4. Po rozstrzygnieciu wszystkich pending, sprawdz gate ponownie
python3 PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py export-gate
```

### Co z 9 deferred

- 7 `ocr_needed` — wymaga `GEMINI_API_KEY` do OCR frame check (packet: `docs/OCR_DEFERRED_CASE_SELECTOR_AND_PROMPT_PACKET.md`)
- 2 `manual_review` — wymaga ludzkiego rubric decision (packet: `docs/MANUAL_REVIEW_RUBRIC_AND_DECISION_PACKET.md`)
- Deferred sa poprawnie poza `apply` / `export-all`, ale nadal blokuja `OPEN`, bo gate check `no_unresolved_deferrals` pozostaje `FAIL`
- Nie wolno traktowac "poza exportem" jako "nieistotne dla gate" — najpierw trzeba je rozstrzygnac albo jawnie zmienic polityke gate

### Kiedy gate moze przejsc na OPEN

Gate przejdzie na OPEN, gdy:

1. `no_pending_approvals` -> PASS: 0 kandydatow z `review_status=pending_human_approval`
2. `no_unresolved_deferrals` -> PASS: 0 kandydatow z `review_status=deferred` (albo zmiana polityki gate)
3. `catalog_validation_passes` -> PASS: juz PASS
4. `human_review_recorded` -> PASS: min. 1 kandydat z `review_status=approved` i `reviewed_by` wypelnione

**Minimalny ruch do OPEN**: rozstrzygniecie wszystkich 14 pending, rozstrzygniecie wszystkich 9 deferred oraz zapisanie co najmniej 1 prawdziwego approvala.

---

## 3. Co robic, gdy gate jest OPEN

Gdy `export_gate_packet.json` pokazuje `gate_result: "OPEN"`:

### Sekwencja wykonawcza: review -> gate -> apply -> export -> receipt

```bash
# KROK 1: Potwierdz stan gate
python3 PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py export-gate
# Oczekiwany wynik: gate_result: OPEN

# KROK 2: Zapisz approved candidates do kanonicznego katalogu
python3 PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py apply
# Efekt: data/devices.jsonl, data/parts_master.jsonl, data/device_parts.jsonl zaktualizowane
# Backup: data/backups/ przed apply

# KROK 3: Walidacja spojnosci katalogu po apply
python3 PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py validate
# Oczekiwany wynik: 0 bledow spojnosci

# KROK 4: Wygeneruj downstream artefakty
python3 PROJEKTY/13_baza_czesci_recykling/scripts/build_catalog_artifacts.py export-all
# Efekt: data/inventory.csv, data/recycled_parts_seed.sql,
#         data/mcp_reuse_catalog.json, data/inventree_import.jsonl

# KROK 5: Walidacja downstream artefaktow
python3 PROJEKTY/13_baza_czesci_recykling/scripts/build_catalog_artifacts.py validate
# Oczekiwany wynik: wszystkie artefakty spojne

# KROK 6: Zapisz export receipt
# Recznie wypelnij receipt template (patrz: autonomous_test/reports/export_release_receipt_TEMPLATE.json)
# Zapisz jako: autonomous_test/reports/export_release_receipt_YYYY-MM-DD.json
```

### Checklist przed apply

- [ ] `export-gate` zwraca `gate_result: OPEN`
- [ ] `review-status` pokazuje 0 pending_human_approval
- [ ] `curation_review_queue.jsonl` nie ma zadnych wpisow z `review_status: deferred`
- [ ] `human_review_ledger.jsonl` zawiera min. 1 wpis z `review_decision: approved`
- [ ] `curation_review_queue.jsonl` nie ma zadnych wpisow z `reviewed_by: null` dla approved
- [ ] `curation_report.md` odzwierciedla aktualny stan gate (BLOCKED/OPEN)

### Checklist przed export-all

- [ ] `apply` zakonczony sukcesem
- [ ] `validate` po apply przechodzi bez bledow
- [ ] `data/devices.jsonl`, `data/parts_master.jsonl`, `data/device_parts.jsonl` sa zaktualizowane
- [ ] `data/backups/` zawiera backup sprzed apply

### Checklist po export-all

- [ ] `data/inventory.csv` wygenerowany i niepusty
- [ ] `data/recycled_parts_seed.sql` wygenerowany i niepusty
- [ ] `data/mcp_reuse_catalog.json` wygenerowany i niepusty
- [ ] `data/inventree_import.jsonl` wygenerowany i niepusty
- [ ] `build_catalog_artifacts.py validate` przechodzi
- [ ] Export receipt wypelniony i zapisany

---

## 4. Artefakty do zarchiwizowania po eksporcie

Po pierwszym prawdziwym eksporcie nalezy zarchiwizowac:

| Artefakt | Sciezka | Opis |
|----------|---------|------|
| Export gate packet | `autonomous_test/reports/export_gate_packet.json` | Stan gate w momencie OPEN |
| Review queue | `autonomous_test/reports/curation_review_queue.jsonl` | Stan kolejki w momencie exportu |
| Human review ledger | `autonomous_test/reports/human_review_ledger.jsonl` | Wszystkie decyzje reviewerow |
| Curation decisions | `autonomous_test/reports/curation_decisions.jsonl` | Decyzje kuracyjne |
| Curation report | `autonomous_test/reports/curation_report.md` | Raport kuracyjny |
| Catalog backup (pre-apply) | `data/backups/` | Backup katalogu sprzed apply |
| Export receipt | `autonomous_test/reports/export_release_receipt_YYYY-MM-DD.json` | Receipt po eksporcie |
| Inventory CSV | `data/inventory.csv` | Wygenerowany inventory |
| Seed SQL | `data/recycled_parts_seed.sql` | Wygenerowany SQL |
| MCP catalog | `data/mcp_reuse_catalog.json` | Wygenerowany MCP catalog |
| InvenTree import | `data/inventree_import.jsonl` | Wygenerowany InvenTree import |

---

## 5. Spojnosc z istniejacymi packetami

| Packet | Relacja |
|--------|---------|
| `export_gate_packet.json` (zadanie 29) | Zrodlo prawdy o stanie gate — ten readiness packet go czyta, nie zastepuje |
| `HUMAN_APPROVAL_LEDGER.md` (zadanie 31) | Mechanizm zapisu approvali — ten packet go referencjuje |
| `REVIEW_ASSIGNMENT_PACKET.md` (zadanie 31/35) | Przydzial reviewerow — musi byc wypelniony przed review |
| `OCR_DEFERRED_CASE_SELECTOR_AND_PROMPT_PACKET.md` (zadanie 36) | Tor dla 7 ocr_needed cases |
| `MANUAL_REVIEW_RUBRIC_AND_DECISION_PACKET.md` (zadanie 37) | Tor dla 2 manual_review cases |
| Curation RUNBOOK (zadanie 29+) | Krok 6 (review-queue + export-gate) i Krok 7 (handoff do exportu) |
| Catalog-export RUNBOOK | Wymagany export gate OPEN przed uruchomieniem |

---

## 6. Status

**PACKET READY** — packet definiuje gotowy szlak wykonawczy, ale nie oglasza, ze gate jest OPEN. Gate pozostaje BLOCKED dopoki 14 `pending_human_approval` i 9 `deferred` nie zostana rozstrzygniete przez prawdziwych operatorow i reviewerow.
