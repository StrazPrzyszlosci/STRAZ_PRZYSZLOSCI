# Operator Packet: Branch Protection Verification

## Cel

Ten dokument jest krok po kroku instrukcja dla maintainera, jak potwierdzic, ze branch protection na upstream jest wlaczona przed pierwszym publicznym pilotem `Project 13`.

Bez branch protection kazdy z collaberatorow moze pushowac bezposrednio do `main`, omijajac review — co podwaza caly model `fork -> PR -> review -> merge`.

---

## Krok 1. Sprawdz aktualny stan branch protection

Otworz w przegladarce:

```
https://github.com/StrazPrzyszlosci/STRAZ_PRZYSZLOSCI/settings/branches
```

Albo przez GitHub CLI:

```bash
gh api repos/StrazPrzyszlosci/STRAZ_PRZYSZLOSCI/branches/main/protection 2>&1
```

Jesli endpoint zwroci `404`, branch protection **nie jest wlaczona** dla `main`.

Jesli zwroci JSON, przejrzyj ustawienia — kluczowe pola to `required_pull_request_reviews` i `restrictions`.

---

## Krok 2. Wlacz branch protection dla `main`

Przez GitHub UI:

1. Wejdz na `https://github.com/StrazPrzyszlosci/STRAZ_PRZYSZLOSCI/settings/branches`.
2. Kliknij **Add branch protection rule**.
3. W polu **Branch name pattern** wpisz `main`.
4. Zaznacz:
   - **Require a pull request before merging**
     - **Require approvals** (min. 1)
     - Opcjonalnie: **Dismiss stale pull request approvals when new commits are pushed**
   - **Require status checks to pass before merging**
     - Dodaj: `secret-scan` (nazwa joba z workflow `pr_secret_scan.yml`)
   - **Do not allow force pushes**
   - **Do not allow deletions**
5. Kliknij **Create** albo **Save changes**.

Przez GitHub CLI (alternatywa):

```bash
gh api repos/StrazPrzyszlosci/STRAZ_PRZYSZLOSCI/branches/main/protection \
  -X PUT \
  --input - <<'EOF'
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["secret-scan"]
  },
  "required_pull_request_reviews": {
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": false,
    "required_approving_review_count": 1
  },
  "restrictions": null,
  "enforce_admins": false,
  "allow_force_pushes": false,
  "allow_deletions": false
}
EOF
```

Uwaga: wymaganie `enforce_admins: true` oznacza, ze rowniez admini repo musza przechodzic przez PR. Dla pierwszego pilota rekomendowane jest `false`, ale maintainer powinien rozwayc zmiane na `true` po ustabilizowaniu procesu.

---

## Krok 3. Zweryfikuj, ze protection dziala

1. Sprobuj pushowac bezposrednio do `main` z konta nie-admina (albo z `enforce_admins: true` — z konta admina):

```bash
git checkout main
echo "test" >> test_branch_protection.txt
git add test_branch_protection.txt
git commit -m "test: branch protection check"
git push origin main
```

Oczekiwany wynik: **push powinien zostac odrzucony** z komunikatem o wymaganiu PR.

2. Uslij testowy commit przez nowy branch i PR:

```bash
git checkout -b test/branch-protection-check
echo "test" >> test_branch_protection.txt
git add test_branch_protection.txt
git commit -m "test: branch protection check via PR"
git push origin test/branch-protection-check
gh pr create --title "test: branch protection check" --body "Verification that branch protection requires PR review before merge."
```

3. Sprobuj mergowac PR bez approval:

Oczekiwany wynik: **merge powinien byc zablokowany** az co najmniej jeden reviewer zatwierdzi.

4. Po weryfikacji zamknij testowy PR bez mergowania i usun branch:

```bash
gh pr close <numer> --delete-branch
git checkout main
git branch -D test/branch-protection-check
rm -f test_branch_protection.txt
```

---

## Krok 4. Zapisz potwierdzenie

Po udanej weryfikacji maintainer powinien:

1. Zapisac date i wynik w `PUBLIC_VOLUNTEER_RUN_READINESS.md` — zmienic status z DO POTWIERDZENIA na POTWIERDZONO.
2. Opcjonalnie: dodac komentarz w `PILOT_REVIEW_ASSIGNMENT_AND_APPROVAL_PATH.md` sekcja 5 checklist, ze branch protection jest potwierdzone.

---

## Krok 5. Otwarte decyzje

- **Czy `enforce_admins` ma byc `true`?** Rekomendacja: na czas pilota `false`, po ustabilizowaniu `true`. Decyzja maintainera.
- **Czy wymagac `secret-scan` jako required status check?** Rekomendacja: tak. Workflow `pr_secret_scan.yml` musi jednak najpierw przejsc na branchu `main` (trzeba zmergeowac workflow przez PR).
- **Czy wymagac code owner reviews?** Baseline `CODEOWNERS` istnieje w `.github/CODEOWNERS`. Aby wymusic code owner reviews: (1) uzupelnij loginy `@DO_UZUPELNIENIA_*` na prawdziwe loginy GitHub, (2) wlacz `require_code_owner_reviews: true` w branch protection. Patrz `REVIEW_ENFORCEMENT_BASELINE.md` krok 1 i 2.

---

## Czego ten packet NIE robi

- Nie wlacza branch protection automatycznie — maintainer musi to zrobic recznie.
- Nie gwarantuje, ze protection przetrwa zmiane ustawien organizacji — maintainer powinien okresowo sprawdzac stan.
- Nie zastepuje review — protection to warstwa konieczna, ale nie wystarczajaca.
