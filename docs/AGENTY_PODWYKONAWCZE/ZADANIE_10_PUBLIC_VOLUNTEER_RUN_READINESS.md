# Zadanie 10: Public Volunteer Run Readiness

## 1. Cel wykonawczy

- Przygotowac checkliste gotowosci do pierwszego publicznego wolontariackiego runu Project 13, obejmujaca nie tylko stan techniczny, ale tez fork flow, review, provenance i komunikacje z wolontariuszem.

## 2. Wyzszy cel organizacji

- To zadanie pomaga przejsc od lokalnie gotowych packow do realnego uruchomienia przez ludzi, bez chaosu organizacyjnego. Bez readiness checklista pierwszy publiczny run moze sie udac technicznie, ale zalamac organizacyjnie.

## 3. Read First

- `docs/INSTRUKCJA_ROZWOJOWA_DLA_AGENTA.md`
- `docs/HANDOFF_DLA_NASTEPNEGO_AGENTA_2026-04-22.md`
- `PROJEKTY/13_baza_czesci_recykling/README.md`
- `PROJEKTY/13_baza_czesci_recykling/docs/MODEL_WOLONTARIACKICH_NOTEBOOKOW_KAGGLE.md`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-kaggle-enrichment-01/RUNBOOK.md`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/CHAIN_MAP.md`

## 4. Write Scope

- `PROJEKTY/13_baza_czesci_recykling/docs/`
- `docs/AGENTY_PODWYKONAWCZE/ZADANIE_10_PUBLIC_VOLUNTEER_RUN_READINESS.md`
- `docs/AGENTY_PODWYKONAWCZE/MINI_HANDOFF_ZADANIE_10.md`

## 5. Out Of Scope

- Zmiany w notebooku `youtube-databaseparts.ipynb`
- Zmiany w skryptach finalizera, rebuilda albo helpera Artifact
- Zmiany w manifest.json packa
- Realny publiczny run — to zadanie przygotowuje checkliste, nie wykonuje runu

## 6. Deliverables

- dokument readiness: `PROJEKTY/13_baza_czesci_recykling/docs/PUBLIC_VOLUNTEER_RUN_READINESS.md`
- lista prerekwizytow technicznych, review i komunikacyjnych (wewnatrz dokumentu)
- mini-handoff z najwiekszymi ryzykami

## 7. Acceptance Criteria

- checklista obejmuje nie tylko kod, ale tez fork flow, review, provenance i komunikacje z wolontariuszem
- jasno rozdziela "gotowe lokalnie" od "gotowe publicznie"
- daje sie wykorzystac przez maintainerow przed pierwszym realnym runem

## 8. Walidacja

- kontrola spojnosci z obecnym runbookiem i handoffem
- `git diff --check`

## 9. Blokery i eskalacja

- Brak danych o prawdziwym wolontariackim runie — zostawiono jawne pola "DO POTWIERDZENIA" zamiast zgadywania.
- Brak realizacji zadania 08 (Review Rotation Governance) — odnotowano jako ryzyko, ale nie zablokowano checklisty.

## 10. Mini-handoff

Zapisz:

- co musi byc potwierdzone przed publicznym runem,
- co juz jest gotowe,
- co nadal jest ryzykiem.
