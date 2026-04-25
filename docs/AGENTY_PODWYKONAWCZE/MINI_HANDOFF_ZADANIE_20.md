# Mini-Handoff Zadanie 20

## Jaki secret scan / pre-PR check dodano

1. **GitHub Actions workflow** `.github/workflows/pr_secret_scan.yml`:
   - uruchamiany automatycznie na pull_request (opened, synchronize, reopened)
   - skanuje diff PR wzgledem bazy pod katem 6 wzorcow sekretow (GitHub PAT, Google API key, Google OAuth token, OpenAI/Anthropic key, private key, hardcoded credential value)
   - przy wykryciu potencjalnego sekretu: oznacza run jako failed (`::error::`) i dodaje komentarz w PR z raportem
   - pomija pliki `.env.example` oraz katalogi `tests/`

2. **Lokalny pre-PR skrypt** `PROJEKTY/13_baza_czesci_recykling/scripts/scan_pr_secrets.py`:
   - ten sam zestaw wzorcow co workflow
   - trzy tryby: wszystkie pliki (`--staged`), diff wzgledem ref (`--diff REF`), wszystkie trackowane
   - pomija `.env.example`, katalogi `tests/`, rozszerzenia `.jsonl`, `.csv`, `.sql`
   - exit code 0 = czysto, 1 = znaleziono sekrety, 2 = blad

3. **REVIEW_CHECKLIST.md** zaktualizowany — punkt o sekretach odsyla teraz do automatycznego scanu

## Jak maintainer ma potwierdzac branch protection

Instrukcja krok po kroku w `PROJEKTY/13_baza_czesci_recykling/docs/BRANCH_PROTECTION_OPERATOR_PACKET.md`:

1. Sprawdz aktualny stan przez UI albo `gh api`
2. Wlacz protection dla `main` z: wymagany PR, min. 1 approval, required status check `secret-scan`, brak force push, brak deletions
3. Zweryfikuj dzialanie proba bezposredniego pushu (powinno byc odrzucone) i proba merge bez approval (powinno byc zablokowane)
4. Zapisz potwierdzenie w readiness

Otwarte decyzje: `enforce_admins` (rekomendacja: `false` na czas pilota, `true` po ustabilizowaniu), required status check `secret-scan` (wymaga zmergeowania workflow przez PR na `main`), `CODEOWNERS` (brak na razie).

## Ktore pozycje readiness zostaly domkniete

- Sekcja 2.2 "PR nie zawiera sekretow": DO POTWIERDZENIA → **GOTOWE** (automatyczny scan istnieje)
- Sekcja 5.2 ryzyko "PR omija review": DO POTWIERDZENIA → **CZESCIOWO** (operator packet istnieje, ale maintainer musi wykonac weryfikacje)
- NIE GOTOWE "Automatyczne skanowanie PR na obecnosc sekretow" → **GOTOWE**
- NIE GOTOWE "Branch protection na upstream" → **CZESCIOWO** (packet gotowy, czeka na reczna weryfikacje)
- Dodano wpisy w DOMKNIETE W TEJ ITERACJI: secret scan + operator packet

## Co nadal wymaga decyzji poza repo

- **Reczna weryfikacja branch protection** — maintainer musi fizycznie wlaczyc i przetestowac protection na upstream; ten packet daje instrukcje, ale nie robi tego automatycznie
- **Czy `enforce_admins: true`** — decyzja maintainera; rekomendacja: `false` na czas pilota
- **Czy `secret-scan` jako required status check** — wymaga zmergeowania workflow na `main` przez PR; po zmergeowaniu mozna dodac do branch protection
- **Czy dodac `CODEOWNERS`** — obecnie brak; do przyszlej iteracji
- **Obsadzenie rotacji review** — nadal CZESCIOWO (poza zakresem zadania 20)
