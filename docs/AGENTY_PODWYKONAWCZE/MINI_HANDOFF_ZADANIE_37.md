# Mini Handoff Zadanie 37

## Co zostalo zrobione

1. Napisano `MANUAL_REVIEW_RUBRIC_AND_DECISION_PACKET.md` — rubric rozdzielajacy board-model case (`BN44-00213A`) od custom-transformer case (`QHAD01249`) z jawnymi kryteriami `accept` / `reject` / `defer` dla kazdego
2. Wygenerowano `manual_review_decision_packet.json` — maszynowy decision packet z evidence, rubric summary i pustymi polami decyzyjnymi dla reviewera
3. Packet nie podejmuje zadnych decyzji ani nie wpisuje fikcyjnych reviewerow

## Jakie pliki dotknieto

- `PROJEKTY/13_baza_czesci_recykling/docs/MANUAL_REVIEW_RUBRIC_AND_DECISION_PACKET.md` — nowy dokument (rubric + instrukcja dla reviewera + evidence snapshot + tabela porownawcza)
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/manual_review_decision_packet.json` — nowy artefakt (maszynowy packet z pustymi polami decyzyjnymi)

## Co zweryfikowano

- Packet obejmuje dokladnie 2 cases manual_review: candidate-0076 (`BN44-00213A`) i candidate-0077 (`QHAD01249`)
- `candidate_id`, `part_number`, `evidence_url` zgodne z `deferred_resolution_workpack.json` (zadanie 30)
- `triage_indicators` zgodne z `verification_triage.jsonl`
- Oba cases opisane osobno — nie sa wrzucone do jednego worka
- Kryteria `accept` / `reject` / `defer` sa jawne dla kazdego case
- Zadne decyzje nie sa zapisane (`decision: null`, `reviewed_by: null`)

## Co zostalo otwarte

- Obie decyzje (`BN44-00213A` i `QHAD01249`) czekaja na prawdziwego reviewera — packet przygotowuje kontekst, ale nie zastepuje sadu
- Po decyzjach: uruchomic `record-review` dla obu kandydatow, potem `review-status` i `export-gate`
- 7 cases `ocr_needed` nadal czeka na `GEMINI_API_KEY` (oddzielny tor, packet z zadania 36)
- OCR inconclusive cases moga eskalowac do manual_review — wtedy dolacza do toru z tym packetem
- Nierozstrzygniete bez czlowieka: scope katalogu (cale plyty vs komponenty) i polityka wpisow bez datasheetu
