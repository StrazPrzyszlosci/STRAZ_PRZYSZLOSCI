# Zlecenie Glowne 17 Project13 Verification Dispute Triage And OCR Packet

## 1. Misja zadania

Domknij reviewer-ready packet dla `disputed` rekordow z verification po zadaniu `11`, tak aby downstream curation dostal jasny obraz: co jest tylko sporne, co czeka na OCR check, a co wymaga tuningu progow.

## 2. Wyzszy cel organizacji

To zadanie zamienia "verification ma execution surface" w "verification daje praktycznie uzywalny handoff dla review i curation".

## 3. Read First

- `docs/HANDOFF_DLA_NASTEPNEGO_AGENTA_2026-04-24.md`
- `docs/AGENTY_PODWYKONAWCZE/ODBIOR_PORTFELA_06_ZADAN_11_16_2026-04-24.md`
- `docs/AGENTY_PODWYKONAWCZE/MINI_HANDOFF_ZADANIE_11.md`
- `PROJEKTY/13_baza_czesci_recykling/scripts/verify_candidates.py`
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/verification_disagreements.jsonl`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-kaggle-verification-01/RUNBOOK.md`

## 4. Write Scope

- `PROJEKTY/13_baza_czesci_recykling/scripts/verify_candidates.py`
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-kaggle-verification-01/`
- ewentualnie `PROJEKTY/13_baza_czesci_recykling/docs/`

## 5. Deliverables

- reviewer-ready packet dla disputed rekordow
- jawna triage kategoria dla disputed (`ocr_needed`, `manual_review`, `threshold_tuning`, itp.)
- aktualizacja reportu verification albo osobny report triage
- mini-handoff z tym, co nadal blokuje curation

## 6. Acceptance Criteria

- disputed rekordy nie sa juz tylko surowym logiem bez dalszego rozroznienia
- istnieje jawny sposob odroznienia przypadkow wymagajacych OCR od przypadkow wymagajacych tylko review albo tuningu progow
- jesli `GEMINI_API_KEY` nie jest dostepny, packet nadal jest uzywalny i jawnie opisuje ten blocker
- pack nadal nie miesza verification z curation ani exportem

## 7. Walidacja

- `python3 -m py_compile PROJEKTY/13_baza_czesci_recykling/scripts/verify_candidates.py` jesli skrypt byl zmieniany
- lokalne uruchomienie przynajmniej jednego sensownego przebiegu verification/triage
- `git diff --check`

## 8. Blokery

Jesli nie ma `GEMINI_API_KEY`, nie zatrzymuj zadania. Dowiez packet triage bez OCR runu i jawnie oznacz, ktore rekordy czekaja na OCR check.

## 9. Mini-handoff

Zapisz:

- jak rozdzielono disputed przypadki,
- co wymaga OCR,
- czy potrzebny jest tuning progow,
- co nadal blokuje przejscie do curation.
