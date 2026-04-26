# Review Enforcement Baseline

## Cel

Ten dokument tlumaczy, jak trzy mechanizmy review enforcement wspolpracuja ze soba w repo STRAZ_PRZYSZLOSCI, i instruuje maintainera, jak je aktywowac przed pierwszym publicznym pilotem `Project 13`.

Trzy mechanizmy to:

1. **`.github/CODEOWNERS`** — jawny wlasciciel review dla krytycznych sciezek
2. **`.github/workflows/pr_secret_scan.yml`** — automatyczny scan PR pod katem sekretow
3. **Branch protection** — wymuszenie PR + approval na `main`

---

## 1. Jak trzy mechanizmy sie uzupelniaja

```text
PR z forka wolontariusza
  │
  ├─→ CODEOWNERS: GitHub automatycznie zadala review od wlasciciela sciezki
  │     (np. integrity_reviewer dla governance, primary_pack_reviewer dla packa)
  │
  ├─→ pr_secret_scan.yml: GitHub Actions skanuje diff pod katem sekretow
  │     (job: secret-scan; jesli znajdzie, run failuje i dodaje komentarz w PR)
  │
  └─→ Branch protection: PR nie moze byc scalony bez:
        - min. 1 approval (od wlasciciela CODEOWNERS, jesli require_code_owner_reviews: true)
        - passed status check: secret-scan
        - brak force push i brak deletions
```

Zadny z tych mechanizmow sam nie wystarcza. Razem tworza warstwowy model:

| Warstwa | Co robi | Co NIE robi | Stan |
|---------|---------|-------------|------|
| CODEOWNERS | Mapuje sciezki na role review; GitHub UI pokazuje wymaganych reviewerow | Nie wymusza approval — wymaga branch protection z `require_code_owner_reviews: true` | Baseline gotowy; loginy DO_UZUPELNIENIA |
| secret-scan | Automatycznie skanuje diff PR pod katem 6 wzorcow sekretow | Nie zastepuje recznego review; nie lapie wszystkich typow sekretow | Workflow gotowy; status check wymaga dodania do branch protection po zmergeowaniu |
| Branch protection | Wymusza PR + approval + status checks na `main` | Nie dziala, dopoki maintainer go recznie nie wlaczy | Operator packet gotowy; czeka na reczna weryfikacje maintainera |

---

## 2. Instrukcja aktywacji dla maintainera

### Krok 1. Uzupelnij CODEOWNERS

Otworz `.github/CODEOWNERS` i zamien wszystkie `@DO_UZUPELNIENIA_*` na loginy GitHub osob pelniacych role:

| Placeholder | Rola z PILOT_REVIEW_ASSIGNMENT_AND_APPROVAL_PATH.md | Kto |
|-------------|-----------------------------------------------------|-----|
| `@DO_UZUPELNIENIA_primary_pack_reviewer` | `primary_pack_reviewer` | DO_UZUPELNIENIA |
| `@DO_UZUPELNIENIA_integrity_reviewer` | `backup_reviewer` / `integrity_reviewer` | DO_UZUPELNIENIA |
| `@DO_UZUPELNIENIA_approver` | `approver` | DO_UZUPELNIENIA |

Minimalne: uzupelnij przynajmniej `primary_pack_reviewer` i `integrity_reviewer` przed pierwszym pilotem.

Jesli nie masz jeszcze konkretnych osob, mozesz uzyc nazwy organizacji GitHub albo teamu (np. `@StrazPrzyszlosci/reviewers`), ale musisz najpierw utworzyc ten team.

### Krok 2. Wlacz branch protection

Sledz instrukcje w `BRANCH_PROTECTION_OPERATOR_PACKET.md` — kroki 1-4.

Po zmergeowaniu `pr_secret_scan.yml` na `main`:

1. Wlacz protection dla `main` z:
   - Require a pull request before merging
   - Require approvals: min. 1
   - **Require status checks to pass**: dodaj `secret-scan`
   - **Do not allow force pushes**
   - **Do not allow deletions**
2. Opcjonalnie (rekomendowane po ustabilizowaniu): wlacz `require_code_owner_reviews: true` — wtedy GitHub bedzie wymagal approval od osoby przypisanej w CODEOWNERS

### Krok 3. Potwierdz w readiness

Po uzupelnieniu CODEOWNERS i wlaczeniu branch protection:

1. Zmien status w `PUBLIC_VOLUNTEER_RUN_READINESS.md`:
   - "CODEOWNERS istnieje" → POTWIERDZONO
   - "Branch protection na upstream jest wlaczona" → POTWIERDZONO
   - "Recenzent pierwszego PR jest wyznaczony" → POTWIERDZONO (jesli uzupelniono loginy)
2. Zmien status w `PILOT_REVIEW_ASSIGNMENT_AND_APPROVAL_PATH.md` sekcja 5 checklist

---

## 3. Sciezki w CODEOWNERS i ich uzasadnienie

| Sciezka | Wlasciciel | Uzasadnienie |
|---------|-----------|-------------|
| `PROJEKTY/13_baza_czesci_recykling/execution_packs/` | primary_pack_reviewer | Packi definiuja kontrakt wykonawczy; zmiana bez review moze zlamac provenance albo acceptance criteria |
| `PROJEKTY/13_baza_czesci_recykling/scripts/` | primary_pack_reviewer | Skrypty wykonawcze finalizuja run, buduja artefakty, skanuja sekrety; blad tu propaguje sie do downstream |
| `PROJEKTY/13_baza_czesci_recykling/pipelines/` | primary_pack_reviewer | Pipeline dostarcza surowe sygnaly do katalogu |
| `PROJEKTY/13_baza_czesci_recykling/data/` | integrity_reviewer | Kanoniczny katalog czesci; zmiana bez integrity review moze wprowadzic niereviewowany rekord |
| `PROJEKTY/13_baza_czesci_recykling/schemas/` | integrity_reviewer | Schematy definiuja kontrakt rekordu; zmiana bez integrity review moze oslabic provenance |
| `PROJEKTY/13_baza_czesci_recykling/docs/` (governance) | integrity_reviewer | Dokumenty governance ustalaja reguly review; zmiana bez integrity review to zmiana regul gry przez gracza |
| `docs/REVIEW_ROTATION_GOVERNANCE.md` | integrity_reviewer | Reguly rotacji review |
| `docs/AGENTY_PODWYKONAWCZE/` | integrity_reviewer | Zlecenia dla podwykonawcow; integralnosc toru pracy |
| `.github/CODEOWNERS` | integrity_reviewer | Sam CODEOWNERS — kto moze zmieniac reguly review? |
| `.github/workflows/` | integrity_reviewer | Workflows CI wymuszaja scan i checki |
| `docs/WOLONTARIUSZE_GOTOWE_PRZYDZIALY.md` | integrity_reviewer | Kanoniczny przydzial wolontariuszy |
| `workers/` | approver | Worker i D1 schema sa infrastruktura produkcyjna |
| `*` (domyslne) | approver | Wszystkie inne zmiany wymagaja co najmniej jednego approval |

---

## 4. Czego ten baseline NIE robi

- Nie wymusza automatycznie code owner reviews — wymaga `require_code_owner_reviews: true` w branch protection, a to z kolei wymaga uzupelnienia loginow w CODEOWNERS
- Nie zastepuje recznego review — CODEOWNERS wskazuje, KTO ma reviewowac, ale nie MAMY reviewowac
- Nie gwarantuje, ze review faktycznie nastapi — github moze pokazac "required reviewer", ale reviewer musi zatwierdzic recznie
- Nie rozwiazuje braku osob w puli reviewerow — patrz `PILOT_REVIEW_ASSIGNMENT_AND_APPROVAL_PATH.md` sekcja 4 (exception flow)
- Nie udaje, ze branch protection jest juz wymuszone — patrz `BRANCH_PROTECTION_OPERATOR_PACKET.md`

---

## 5. Relacja z innymi dokumentami

| Dokument | Relacja |
|----------|---------|
| `BRANCH_PROTECTION_OPERATOR_PACKET.md` | Instrukcja weryfikacji i wlaczenia branch protection; odsyla do CODEOWNERS przy `require_code_owner_reviews` |
| `PILOT_REVIEW_ASSIGNMENT_AND_APPROVAL_PATH.md` | Definiuje role review i przydzial osob; CODEOWNERS mapuje role na sciezki repo |
| `REVIEW_ROTATION_GOVERNANCE.md` | Definiuje reguly rotacji i reguly stale; CODEOWNERS je wspiera operacyjnie |
| `REVIEW_CHECKLIST.md` | Lista kontrolna dla reviewerow; nie zalezy bezposrednio od CODEOWNERS |
| `pr_secret_scan.yml` | Automatyczny scan; status check wymagany przez branch protection |
| `PUBLIC_VOLUNTEER_RUN_READINESS.md` | Checklista gotowosci; CODEOWNERS i branch protection sa elementami readiness |

---

## 6. Otwarte decyzje dla maintainera

- [ ] Czy wlaczyc `require_code_owner_reviews: true` od razu, czy dopiero po uzupelnieniu loginow
- [ ] Czy `enforce_admins: true` — rekomendacja: `false` na czas pilota, `true` po ustabilizowaniu
- [ ] Czy dodac wiecej sciezek do CODEOWNERS (np. osobne packi `verification`, `curation`, `export`)
- [ ] Czy uzyc teamow GitHub (`@org/team`) zamiast pojedynczych loginow
- [ ] Czy dolaczyc CODEOWNERS do packow `blueprint-design-01` i `esp-runtime-01` z bardziej restrykcyjna rola (wariant B z REVIEW_ROTATION_GOVERNANCE.md)
