# Mini-Handoff Zadanie 26

## Jaki baseline review enforcement dodano

1. **`.github/CODEOWNERS`** — baseline mapowanie krytycznych sciezek na role review:
   - `execution_packs/`, `scripts/`, `pipelines/` → `primary_pack_reviewer`
   - `data/`, `schemas/`, dokumenty governance → `integrity_reviewer`
   - `workers/`, `D1` → `approver`
   - domyslne `*` → `approver`
   - Loginy sa `@DO_UZUPELNIENIA_*` — maintainer musi uzupelnic przed wlaczeniem `require_code_owner_reviews`

2. **`PROJEKTY/13_baza_czesci_recykling/docs/REVIEW_ENFORCEMENT_BASELINE.md`** — dokument tlumaczy:
   - jak CODEOWNERS, secret scan i branch protection sie uzupelniaja (warstwowy model)
   - krok po kroku instrukcja aktywacji dla maintainera (uzupelnij CODEOWNERS → wlacz branch protection → potwierdz w readiness)
   - uzasadnienie kazdej sciezki w CODEOWNERS
   - czego ten baseline NIE robi (nie wymusza automatycznie, nie zastepuje recznego review, nie rozwiazuje braku osob)

## Jak CODEOWNERS mapuje sie na pilotowy tor review

- Role w CODEOWNERS odpowiadaja rola z `PILOT_REVIEW_ASSIGNMENT_AND_APPROVAL_PATH.md` sekcja 2.1:
  - `@DO_UZUPELNIENIA_primary_pack_reviewer` ← `primary_pack_reviewer`
  - `@DO_UZUPELNIENIA_integrity_reviewer` ← `backup_reviewer` / `integrity_reviewer`
  - `@DO_UZUPELNIENIA_approver` ← `approver`
- Po uzupelnieniu loginow i wlaczeniu `require_code_owner_reviews: true`, GitHub bedzie automatycznie wymagal approval od wlasciciela sciezki przy PR
- CODEOWNERS nie zastepuje review rotation — nadal obowiazuja reguly z `REVIEW_ROTATION_GOVERNANCE.md`

## Ktore pozycje readiness przesunely sie do przodu

- "CODEOWNERS istnieje": NIE ISTNIAL → GOTOWE
- "Dokument review enforcement": NIE ISTNIAL → GOTOWE
- "PR omija review" mitygacja: branch protection → branch protection + CODEOWNERS
- "Sciezka approval jest jawna": CZESCIOWO → CZESCIOWO (CODEOWNERS dodaje warstwe jawnosci, ale loginy nadal DO_UZUPELNIENIA)
- Section 5 checklist maintainera: dodano 2 punkty (CODEOWNERS loginy, require_code_owner_reviews)
- REVIEW_CHECKLIST.md: dodano punkt o review owner z CODEOWNERS
- BRANCH_PROTECTION_OPERATOR_PACKET.md: zaktualizowano "Czy wymagac code owner reviews?" — juz nie "brak CODEOWNERS", tylko instrukcja aktywacji

## Co nadal zostaje po stronie upstream albo maintainera

- **Uzupelnienie loginow w CODEOWNERS** — maintainer musi zamienic `@DO_UZUPELNIENIA_*` na loginy GitHub; patrz `REVIEW_ENFORCEMENT_BASELINE.md` krok 1
- **Wlaczenie `require_code_owner_reviews: true` w branch protection** — wymaga najpierw uzupelnienia CODEOWNERS; patrz `REVIEW_ENFORCEMENT_BASELINE.md` krok 2
- **Weryfikacja branch protection** — nadal czeka na reczne wykonanie przez maintainera; patrz `BRANCH_PROTECTION_OPERATOR_PACKET.md`
- **Nazwanie konkretnych osob w puli reviewerow** — CODEOWNERS mapuje role na sciezki, ale nie rozwiazuje braku osob; nadal CZESCIOWO
- **Test `require_code_owner_reviews` z prawdziwym PR** — nie da sie przetestowac bez uzupelnionych loginow i wlaczonej protection
