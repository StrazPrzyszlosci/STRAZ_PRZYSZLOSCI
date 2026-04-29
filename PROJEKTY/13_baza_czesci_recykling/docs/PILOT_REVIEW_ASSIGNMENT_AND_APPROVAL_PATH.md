# Pilot Review Assignment And Approval Path

## Cel dokumentu

Ten dokument tlumaczy governance z `docs/REVIEW_ROTATION_GOVERNANCE.md` na operacyjny scaffold pierwszego publicznego pilota `Project 13`.

Zawiera:

- template przypisania reviewerow z polami do wypelnienia,
- jawny approval path dla pierwszego publicznego PR,
- exception flow, gdy reviewerow jest za malo.

Rozdziela zasady stale od pol `do_uzupelnienia` przez maintainera.

---

## 1. Zasady stale

Ponizsze zasady pochodza z `REVIEW_ROTATION_GOVERNANCE.md` i obowiazuja niezaleznie od tego, kto wypelni pola:

1. Autor zmiany nie zatwierdza sam swojej promocji do katalogu, workflowu ani deploymentu.
2. Ta sama osoba nie powinna byc jednoczesnie autorem, jedynym reviewerem i approverem tej samej zmiany.
3. `pack_reviewer` dla tego samego packa nie powinien powtarzac sie wiecej niz dwa razy z rzedu.
4. Zmiana promujaca artefakt do kanonicznej bazy wiedzy musi przejsc przez jawny `ReadinessGate(review_ready)` przed `Approval`.
5. Publiczny wynik wolontariusza nie moze byc mergowany poza `fork -> PR -> review`.
6. Zmiana o istotnym ryzyku governance musi przejsc przez `ReadinessGate(integrity_ready)` albo rownowazna jawna ocene integrity przed merge.
7. Pierwszy publiczny run idzie w modelu `controlled canary pilot` z jawnym przydzialem reviewerow przed uruchomieniem notebooka. Sekwencja canary jest opisana w `CANARY_PILOT_PACKET.md`.
8. Po pierwszym canary runie przeprowadza sie retro wg `CANARY_RETRO_TEMPLATE.md`.

---

## 2. Role i przypisanie reviewerow

### 2.1 Role wymagane dla pierwszego pilota

| Rola | Odpowiedzialnosc | Osoba (`do_uzupelnienia`) | Login GitHub (`do_uzupelnienia`) |
|------|-----------------|---------------------------|----------------------------------|
| `primary_pack_reviewer` | Ocena merytoryczna: czy wynik spelnia acceptance criteria packa, czy provenance jest jawne, czy diff jest reviewowalny | __DO_UZUPELNIENIA__ | __DO_UZUPELNIENIA__ |
| `backup_reviewer` albo `integrity_reviewer` | Ocena integrity: czy zmiana nie omija review, czy nie wzmacnia zjawisk niekorzystnych (`private_capture`, `volunteer_work_appropriation`, `opaque_approval_path`), czy `IntegrityRiskAssessment` istnieje i odpowiada realnej zmianie | __DO_UZUPELNIENIA__ | __DO_UZUPELNIENIA__ |
| `approver` | Jawne `Approval` dla `pilot_run`; nie powinien byc autorem zmiany ani jedynym `pack_reviewer` | __DO_UZUPELNIENIA__ | __DO_UZUPELNIENIA__ |
| `review_coordinator` | Wyznacza reviewerow przed uruchomieniem pilota, pilnuje zeby review nie utknelo w jednej osobie, zapisuje wyjatki od rotacji | __DO_UZUPELNIENIA__ | __DO_UZUPELNIENIA__ |

### 2.2 Ograniczenia przydzialu

- `approver` nie moze byc jednoczesnie jedynym `pack_reviewer` tej samej zmiany.
- `primary_pack_reviewer` nie moze byc autorem PR (czyli nie moze byc wolontariuszem skladajacym PR).
- Jesli `backup_reviewer` pelni jednoczesnie role `integrity_reviewer`, musi to byc jawnie zapisane w przydziale.
- Na obecnym etapie `review_coordinator` moze byc maintainer prowadzacy dany pilot, ale nie moze byc jednoczesnie `approver` tego samego PR.

### 2.3 Wymagany minimalny przydzial przed pilotem

Przed uruchomieniem pierwszego publicznego pilota maintainer musi wypelnic wszystkie cztery pola w tabeli powyzej. Brak wypelnionego pola = brak startu pilota.

---

## 3. Approval path

### 3.1 Kanoniczny lancuch approval dla pierwszego publicznego PR

```text
Wolontariusz sklada PR z forka
  -> primary_pack_reviewer: review merytoryczny wg REVIEW_CHECKLIST.md
  -> ReadinessGate(review_ready): artefakt czytelny, ma provenance, spelnia acceptance criteria
  -> integrity_reviewer: IntegrityRiskAssessment dla zmiany
  -> ReadinessGate(integrity_ready): ryzyka governance ocenione
  -> approver: jawne Approval(pilot_run)
  -> merge
```

### 3.2 ReadinessGate

| Brama | Kto potwierdza | Co sprawdza |
|-------|---------------|-------------|
| `review_ready` | `primary_pack_reviewer` | Artefakt jest czytelny, ma provenance i acceptance criteria spelnione |
| `integrity_ready` | `integrity_reviewer` albo `backup_reviewer` | Ryzyka governance i public-interest zostaly jawnie ocenione; `IntegrityRiskAssessment` istnieje i odpowiada realnej zmianie |
| `pack_ready` | juz spelniony | `gate-pack-ready-project13-01` status: pass |

### 3.3 Zakres Approval

Dla pierwszego pilota zakres to `pilot_run`. Oznacza to, ze:

- Approval dotyczy tylko wyniku tego jednego runu.
- Nie promuje automatycznie do `knowledge_base_promotion` ani `workflow_promotion`.
- Promocja do katalogu kanonicznego wymaga osobnego Approval z zakresem `knowledge_base_promotion`.

### 3.4 Rekord Approval

Po wydaniu Approval nalezy utworzyc rekord zgodny z `data/sample/organization_approval.json`:

```json
{
  "schema_version": "v1",
  "approval_id": "approval-project13-pilot-pr-<NUMER>",
  "artifact_id": "artifact-project13-pilot-pr-<NUMER>",
  "decision": "approved | rejected | needs_changes | deferred",
  "approval_scope": "pilot_run",
  "reviewer_role": "approver",
  "reason_codes": ["PROVENANCE_COMPLETE", "INTEGRITY_PASS", "REVIEW_CHECKLIST_COMPLETE"],
  "integrity_assessments": [
    {
      "entity_kind": "integrity_risk_assessment",
      "entity_id": "integrity-project13-pilot-pr-<NUMER>"
    }
  ],
  "notes": "__DO_UZUPELNIENIA__",
  "next_step": "Scalic PR i przejsc do retro z wolontariuszem.",
  "decided_at": "__DO_UZUPELNIENIA__"
}
```

---

## 4. Exception flow — gdy reviewerow za malo

### 4.1 Kiedy stosowac exception

Exception od rotacji jest dopuszczalny, gdy:

- cala dostepna pula reviewerow liczy mniej niz 3 osoby,
- jedyny dostepny `pack_reviewer` jest tym samym co `approver`,
- `integrity_reviewer` nie jest dostepny w rozsadnym czasie (powyzej 72h od zlozenia PR).

### 4.2 Procedura exception

1. `review_coordinator` zapisuje w PR komentarz oznaczony `rotation_exception`.
2. Komentarz opisuje:
   - czemu nie bylo alternatywnego reviewera,
   - ktora regula zostala tymczasowo zawieszona,
   - jaki jest plan przywrucenia pelnej rotacji.
3. Exception nie znosi zakazu self-approval dla zmian sredniego i wysokiego ryzyka.
4. Po merge trzeba dopisac follow-up, jak zmniejszyc zaleznosc od jednej osoby.

### 4.3 Template komentarza exception w PR

```markdown
## rotation_exception

- **Regula zawieszona**: [np. rozdzial approver i pack_reviewer]
- **Powod**: [np. pula reviewerow liczy 2 osoby, obu niedostepnych w oknie 72h]
- **Plan przywrucenia**: [np. rekrutacja 1 reviewera z kregu zaufanych osob do konca Q2]
- **Approver**: [login]
- **Review wykonal**: [login]
- **Self-approval**: NIE (zawsze dla sredniego i wysokiego ryzyku)
```

### 4.4 Granice exception

- Exception nie moze stac sie domyslnym trybem pracy.
- Nie wiecej niz 2 kolejne PR w trybie exception dla tego samego packa.
- Po 2 exceptionach `review_coordinator` musi zablokowac kolejne runy az do rozszerzenia puli reviewerow.

---

## 5. Checklist maintainera przed pierwszym pilotem

- [ ] Wypelniono wszystkie pola `__DO_UZUPELNIENIA__` w sekcji 2.1
- [ ] `primary_pack_reviewer` nie jest autorem PR
- [ ] `approver` nie jest jednoczesnie jedynym `pack_reviewer`
- [ ] `review_coordinator` jest wyznaczony
- [ ] Branch protection na upstream jest wlaczona (instrukcja weryfikacji: `BRANCH_PROTECTION_OPERATOR_PACKET.md`)
- [ ] `.github/CODEOWNERS` ma uzupelnione loginy GitHub zamiast `@DO_UZUPELNIENIA_*` (patrz `REVIEW_ENFORCEMENT_BASELINE.md` krok 1)
- [ ] `require_code_owner_reviews` jest wlaczone w branch protection (patrz `REVIEW_ENFORCEMENT_BASELINE.md` krok 2)
- [ ] REVIEW_CHECKLIST.md jest gotowy do uzycia przez reviewerow
- [ ] Rekord `Approval` bedzie utworzony po wydaniu approval
- [ ] Kanal komunikacji z wolontariuszem jest potwierdzony (GitHub Issues z labelka `volunteer-support` jako minimum)
- [ ] Retro z wolontariuszem jest zaplanowane po pierwszym PR (template: `CANARY_RETRO_TEMPLATE.md`)

Ta checklist odpowiada blockerom C-1..C-5 w `CANARY_GO_LIVE_OPERATOR_PACKET.md`. Zamkniecie wszystkich blockerow = decyzja GO.

---

## 6. Spoijnosc z governance

| Element w tym dokumencie | Odniesienie w REVIEW_ROTATION_GOVERNANCE.md |
|--------------------------|---------------------------------------------|
| Role: `primary_pack_reviewer`, `backup_reviewer`/`integrity_reviewer`, `approver` | Sekcja "Model dla pierwszego publicznego runu wolontariackiego" |
| Zasada: autor nie zatwierdza sam | Regula 1 |
| Zasada: nie jednoczesnie autor, reviewer i approver | Regula 2 |
| Zasada: rotacja max 2x z rzedu | Regula 3 |
| Exception flow | Sekcja "Wyjatki od rotacji" |
| Wariant A jako baseline | Sekcja "Wariant A: lekka rotacja operacyjna" |
| `ReadinessGate(review_ready)` i `ReadinessGate(integrity_ready)` | Sekcja "Zwiazek z encjami: ReadinessGate" |
| `Approval` z zakresem `pilot_run` | Sekcja "Zwiazek z encjami: Approval" |

| Element w tym dokumencie | Odniesienie w PUBLIC_VOLUNTEER_RUN_READINESS.md |
|--------------------------|----------------------------------------------|
| Wymagany przydzial reviewerow przed pilotem | Sekcja 3.1: "Reviewer jest zdefiniowany — CZESCIOWO" |
| Branch protection | Sekcja 5.2: ryzyko "PR omija review — DO POTWIERDZENIA" |
| Controlled pilot | Sekcja 7: rekomendacja |
| Retro z wolontariuszem | Sekcja 7: punkt 4 |

---

## 7. Otwarte decyzje dla maintainera

- [ ] Czy `Approval` ma byc zapisywany od razu jako osobny rekord przy pierwszym publicznym pilocie, czy dopiero po ustabilizowaniu procesu.
- [ ] Czy limit dwoch review z rzedu ma byc liczony per pack, czy per caly projekt.
- [ ] Kto w praktyce wchodzi do pierwszej puli reviewerow dla `Project 13`.
- [ ] Czy kanal na zywo (Discord/Telegram) bedzie dostepny podczas pierwszego pilota, czy GitHub Issues wystarczy.
