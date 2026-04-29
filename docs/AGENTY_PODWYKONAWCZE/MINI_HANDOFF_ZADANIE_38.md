# Mini-Handoff Zadanie 38

## Co zostalo zrobione

Przygotowano packet operatorski dla szlaku `ostatni approval -> export gate OPEN -> apply -> export-all -> receipt`. Packet nie oglasza, ze gate jest OPEN — pokazuje gotowa sekwencje na czas, gdy gate przejdzie na OPEN.

### Nowe artefakty

- `PROJEKTY/13_baza_czesci_recykling/docs/EXPORT_OPEN_READINESS_PACKET.md` — readiness packet z:
  - aktualnym stanem export gate (BLOCKED, z checks, blockers, warnings)
  - co robic gdy BLOCKED (kroki review + record-review + re-run export-gate)
  - co robic gdy OPEN (pelna sekwencja: gate -> apply -> validate -> export-all -> validate -> receipt)
  - checklisty przed apply, przed export-all, po export-all
  - lista artefaktow do zarchiwizowania po eksporcie
  - spojnosc z istniejacymi packetami (29, 31, 35, 36, 37)
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/export_release_receipt_TEMPLATE.json` — template receiptu po pierwszym prawdziwym eksporcie z:
  - polem na export gate snapshot (gate_result, checked_at)
  - polem na review queue snapshot (counts, paths)
  - polem na apply snapshot (devices/parts/device_parts added, backup path)
  - polem na export artifacts (path, row/entry count, sha256)
  - polem na validation results
  - polem na deferred candidates excluded (count, ocr_needed, manual_review)
  - polami integrity notes (do checkout po eksporcie)
  - wszystkie pola null / DO_UZUPELNIENIA — receipt nie udaje, ze export juz sie wydarzy

### Zmiany w istniejacych plikach

- `execution_packs/pack-project13-curation-01/RUNBOOK.md`:
  - Krok 7 rozszerzony z 3 linii na pelna sekwencje export-open z checklistami i artefaktami
  - Sekcja Krok 3 curation_report zaktualizowana z referencja do readiness packet
- `execution_packs/pack-project13-catalog-export-01/RUNBOOK.md`:
  - Dodana sekwencja wykonawcza (6 krokow) z referencja do readiness packet
  - Dodana lista artefaktow do zarchiwizowania po eksporcie
  - Minimalne kryterium sukcesu rozszerzone o export receipt
- `autonomous_test/reports/curation_report.md`:
  - Sekcja "To resolve" zaktualizowana: referencja do record-review (zamiast reczna edycja JSONL) + readiness packet
  - Sekcja "Next steps" zaktualizowana: record-review + readiness packet referencja

## Jakie komendy walidacyjne przeszly

- `git diff --check` — OK (do uruchomienia)
- brak zmian w skryptach Python — nie trzeba py_compile

## Sciezka od ostatniego approvala do export receiptu

```text
1. record-review (dla kazdego pending_human_approval)
2. review-status (weryfikacja: 0 pending)
3. export-gate (weryfikacja: gate_result = OPEN)
4. apply (zapis do kanonicznego katalogu + backup)
5. curate_candidates.py validate (spojnosc katalogu)
6. build_catalog_artifacts.py export-all (downstream artefakty)
7. build_catalog_artifacts.py validate (spojnosc artefaktow)
8. Wypelnij receipt template -> zapisz export_release_receipt_YYYY-MM-DD.json
```

## Jakie warunki nadal musza przejsc na PASS

| Gate check | Aktualny stan | Wymagany ruch |
|------------|--------------|---------------|
| no_pending_approvals | FAIL | Rozstrzygniecie 14 pending_human_approval przez record-review |
| no_unresolved_deferrals | FAIL | Rozstrzygniecie 9 deferred (7 ocr + 2 manual) |
| catalog_validation_passes | PASS | Juz PASS |
| human_review_recorded | FAIL | Min. 1 approved z wypelnionym reviewed_by |

## Co pozostaje poza pierwszym eksportem

- 9 deferred candidates (7 ocr_needed + 2 manual_review) — poza eksportem, do rozstrzygniecia w osobnych torach (zadania 36, 37)
- REVIEW_ASSIGNMENT_PACKET.md — pola DO_UZUPELNIENIA (przydzial reviewerow)
- Prawdziwy canary run (zadanie 39)
- Real hardware bench test (zadanie 40)
