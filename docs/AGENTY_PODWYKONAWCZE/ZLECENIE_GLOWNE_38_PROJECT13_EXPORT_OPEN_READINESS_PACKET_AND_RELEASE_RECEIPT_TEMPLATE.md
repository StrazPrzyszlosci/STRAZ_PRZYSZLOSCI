# Zlecenie Glowne 38 Project13 Export Open Readiness Packet And Release Receipt Template

## 1. Misja zadania

Przygotuj packet operatorski dla ruchu `ostatni approval -> export gate OPEN -> apply -> export-all -> receipt`, ale bez udawania, ze gate jest juz otwarty. Chodzi o gotowy szlak wykonawczy i template receiptu, zeby po prawdziwych approvalach nie improwizowac exportu.

## 2. Wyzszy cel organizacji

Po `29` i `31` wiemy juz, co blokuje export.
To zadanie ma sprawic, ze otwarcie gate i sam export beda kontrolowanym ruchem z jawna sekwencja, a nie "szybka reczna akcja maintainera".

## 3. Read First

- `docs/AGENTY_PODWYKONAWCZE/ODBIOR_PORTFELA_09_ZADAN_29_34_2026-04-28.md`
- `docs/AGENTY_PODWYKONAWCZE/MINI_HANDOFF_ZADANIE_29.md`
- `docs/AGENTY_PODWYKONAWCZE/MINI_HANDOFF_ZADANIE_31.md`
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/export_gate_packet.json`
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/curation_review_queue.jsonl`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-curation-01/RUNBOOK.md`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-catalog-export-01/RUNBOOK.md`

## 4. Write Scope

- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-curation-01/`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-catalog-export-01/`
- `PROJEKTY/13_baza_czesci_recykling/docs/`
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/`

## 5. Deliverables

- export-open readiness packet z kolejka krokow od ostatniego approvala do export receiptu
- template receiptu po pierwszym prawdziwym eksporcie
- jawne rozroznienie: co robimy przy `BLOCKED`, a co dopiero przy `OPEN`
- jesli to pomaga: doprecyzowany checklist / runbook dla `apply` i `export-all`
- mini-handoff z tym, jak bedzie wygladac pierwszy uczciwy export

## 6. Acceptance Criteria

- kolejny maintainer widzi jedna spojna sciezke `review -> gate -> apply -> export -> receipt`
- packet nie oglasza `OPEN`, jesli gate nadal jest `BLOCKED`
- template receiptu nie udaje, ze export juz sie wydarzy
- nie trzeba juz zgadywac, jakie artefakty zarchiwizowac po eksporcie

## 7. Walidacja

- kontrola spojnosci packetu z `export_gate_packet.json`
- kontrola spojnosci z runbookiem `curation` i `catalog-export`
- jesli zmieniasz skrypt: odpowiedni `python3 -m py_compile`
- `git diff --check`

## 8. Blokery

Jesli gate nadal jest `BLOCKED`, packet ma to utrzymac jako stan bazowy.
Nie wolno przygotowac "receiptu po eksporcie" tak, jakby export juz zostal wykonany.

## 9. Mini-handoff

Zapisz:

- jaki packet i template dodano,
- jaka jest sciezka od ostatniego approvala do export receiptu,
- jakie warunki nadal musza przejsc na `PASS`,
- co pozostaje poza pierwszym eksportem.
