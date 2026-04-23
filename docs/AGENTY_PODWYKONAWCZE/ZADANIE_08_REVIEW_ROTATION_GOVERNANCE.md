# Zadanie 08: Review Rotation Governance

## 1. Cel wykonawczy

- Przygotowac minimalny, jawny model governance dla review i approval, zeby ograniczac centralizacje review i samo-zatwierdzanie zmian.

## 2. Wyzszy cel organizacji

- To zadanie chroni interes wspolny i wzmacnia warstwe governance, bez ktorej wolontariacka architektura execution packow latwo zamieni sie w ukryty model kontroli przez bardzo mala liczbe osob.

## 3. Read First

- `docs/ARCHITEKTURA_ORGANIZACJI_AGENTOWEJ.md`
- `docs/ENCJE_I_WORKFLOWY_ORGANIZACJI_AGENTOWEJ.md`
- `docs/HANDOFF_DLA_NASTEPNEGO_AGENTA_2026-04-22.md`
- `PROJEKTY/13_baza_czesci_recykling/docs/PUBLIC_VOLUNTEER_RUN_READINESS.md`

## 4. Write Scope

- `docs/REVIEW_ROTATION_GOVERNANCE.md`
- `docs/ARCHITEKTURA_ORGANIZACJI_AGENTOWEJ.md`
- `docs/ENCJE_I_WORKFLOWY_ORGANIZACJI_AGENTOWEJ.md`
- `PROJEKTY/13_baza_czesci_recykling/docs/PUBLIC_VOLUNTEER_RUN_READINESS.md`

## 5. Deliverables

- nowy dokument governance dla review i approval,
- drobne doprecyzowania dokumentow organizacyjnych,
- mini-handoff z rekomendowanym modelem i otwartymi decyzjami.

## 6. Acceptance Criteria

- dokument nazywa role reviewerow,
- opisuje rotacje albo minimalne zasady unikania koncentracji review,
- laczy governance z `IntegrityRiskAssessment`, `ReadinessGate` i `Approval`,
- readiness dla pierwszego publicznego runu przestaje udawac, ze zadanie 08 nie istnieje.

## 7. Walidacja

- kontrola spojnosci z dokumentami organizacyjnymi,
- `python3 -m py_compile pipelines/export_chatbot_knowledge_bundle.py`,
- `git diff --check`

## 8. Blokery i eskalacja

- zespol reviewerow jest jeszcze maly, wiec dokument nie moze zakladac pelnej biurokracji ani sztucznie wymagac czegos, czego organizacja jeszcze nie ma.

## 9. Wynik mini-handoffu (2026-04-23)

### Co zostalo zrobione

1. Dodano `docs/REVIEW_ROTATION_GOVERNANCE.md` z baseline modelem rotacji review i approval.
2. Zdefiniowano role: `author_or_operator`, `pack_reviewer`, `integrity_reviewer`, `approver`, `review_coordinator`.
3. Zapisano twarde reguly: brak self-approval, brak jednoosobowego lancucha `autor -> review -> approval`, limit dwoch kolejnych review tego samego packa przez jedna osobe, gdy istnieja alternatywy.
4. Powiazano governance z `IntegrityRiskAssessment`, `ReadinessGate` i `Approval`.
5. Uaktualniono `PUBLIC_VOLUNTEER_RUN_READINESS.md`, zeby status rotacji review i governance byl zgodny z nowym dokumentem, zamiast pozostawac sztucznie `NIE GOTOWE`.

### Jakie pliki dotknieto

- `docs/REVIEW_ROTATION_GOVERNANCE.md`
- `docs/ARCHITEKTURA_ORGANIZACJI_AGENTOWEJ.md`
- `docs/ENCJE_I_WORKFLOWY_ORGANIZACJI_AGENTOWEJ.md`
- `PROJEKTY/13_baza_czesci_recykling/docs/PUBLIC_VOLUNTEER_RUN_READINESS.md`

### Jaki model governance jest rekomendowany

- **Wariant A** jako baseline dla obecnego etapu: lekka rotacja operacyjna, jeden reviewer merytoryczny, jeden approver niebedacy autorem, jawne wyjatki od rotacji.
- **Wariant B** dla packow krytycznych: rozdzielony reviewer merytoryczny, integrity reviewer i approver, bez merge do hardware runtime bez bench reportu.

### Co jest twarda regula

- brak self-approval dla promocji workflowu, katalogu i runtime,
- jawne polaczenie review z `ReadinessGate` i `IntegrityRiskAssessment`,
- publiczny run wolontariacki wymaga nazwanych reviewerow przed uruchomieniem.

### Co wymaga decyzji maintainerow

- sklad pierwszej realnej puli reviewerow dla `Project 13`,
- czy limit dwoch review z rzedu liczyc per pack czy per projekt,
- od jakiego progu hardware/runtime automatycznie uruchamiac wariant B.
