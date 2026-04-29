# Zlecenie Glowne 36 Project13 OCR Deferred Case Selector And Prompt Packet

## 1. Misja zadania

Dla `7` cases `ocr_needed` przygotuj bardziej chirurgiczny execution surface niz samo "uruchom wszystko od nowa". Chodzi o selector, helper albo packet, ktory pozwala operatorowi z `GEMINI_API_KEY` wziasc pojedynczy case albo mala grupe cases i wykonac OCR bez ponownego sledztwa po wielu plikach.

## 2. Wyzszy cel organizacji

Po `30` wiemy juz, ktore cases czekaja na OCR.
To zadanie ma zamienic te informacje w praktyczny interfejs operatorski, ktory obniza koszt pierwszego realnego ruchu po pojawieniu sie `GEMINI_API_KEY`.

## 3. Read First

- `docs/AGENTY_PODWYKONAWCZE/ODBIOR_PORTFELA_09_ZADAN_29_34_2026-04-28.md`
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/deferred_resolution_workpack.json`
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/deferred_resolution_workpack.md`
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/status_resolution_packet.json`
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/verification_triage.jsonl`
- `PROJEKTY/13_baza_czesci_recykling/scripts/verify_candidates.py`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-kaggle-verification-01/RUNBOOK.md`

## 4. Write Scope

- `PROJEKTY/13_baza_czesci_recykling/scripts/verify_candidates.py`
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/`
- `PROJEKTY/13_baza_czesci_recykling/docs/`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-kaggle-verification-01/`

## 5. Deliverables

- helper, selector albo packet pozwalajacy uruchomic OCR na pojedynczym case albo malej grupie cases
- jawna mapa `candidate_id -> evidence_url -> expected_text -> next command`
- instrukcja co dokladnie uruchomic, gdy `GEMINI_API_KEY` jest dostepny
- jesli to pomaga: stable artifact z lista `7` OCR cases do kolejnych przebiegow
- mini-handoff z tym, jak uruchomic pierwszy realny OCR ruch

## 6. Acceptance Criteria

- kazdy z `7` cases `ocr_needed` da sie wziac osobno bez ponownego skladania kontekstu z wielu raportow
- packet albo helper nie miesza toru OCR z `manual_review`
- dokumenty nie udaja, ze OCR juz sie wydarzylo
- kolejny agent z `GEMINI_API_KEY` wie, od jakiej komendy zaczac i jakie cases zamknie tym ruchem

## 7. Walidacja

- kontrola counts wzgledem `deferred_resolution_workpack.json`
- kontrola zgodnosci `candidate_id`, `part_number` i `evidence_url` z packetem `30`
- jesli zmieniasz skrypt: `python3 -m py_compile PROJEKTY/13_baza_czesci_recykling/scripts/verify_candidates.py`
- `git diff --check`

## 8. Blokery

Brak `GEMINI_API_KEY` nie blokuje tego zadania.
Nie wolno jednak oznaczac zadnego OCR case jako rozwiazanego bez realnego przebiegu OCR i review wyniku.

## 9. Mini-handoff

Zapisz:

- jaki helper albo packet dodano,
- jak operator ma uruchomic pojedynczy OCR case,
- ktore cases da sie zgrupowac w jednym przebiegu,
- co nadal wymaga czlowieka po OCR.
