# Handoff T58 — praca nad stabilną ewolucją

Status: in_progress. Cel wątku „pracuj, żeby rój stabilnie ewoluował” pozostaje aktywny. Nie uznawać samej implementacji lub testów jednostkowych za zakończenie celu.

Branch: codex/T58-stable-swarm-evolution, baza ed63d23 (draft PR #26). Własny worktree codex-stable-evolution i atomowy claim T58; cudzych rezerwacji nie zmieniono.

Wdrożone w tej części: kontrakt i kompletne wejścia zadania; aktualny parser handoffu; lease/retry/feedback i trwałe numery batchy; prawdziwy backlog i cechy modeli; runtime Hermesa i niezależny walidator patcha z baseline fail / candidate pass / pełną regresją oraz archiwum kandydatów. Nie dopisano fikcyjnych etykiet ani akceptacji człowieka.

Dotychczasowa weryfikacja: 503 testy Python OK, 378 JavaScript pass / 0 fail, 12 manifestów, 2 ważne approvals, brak konfliktów claimów, składnia i diff OK. Walidator wykonano w prawdziwym sandboxie na kontrolowanym małym fixture: baseline rc=1, candidate rc=0, pełne testy fixture rc=0. Fixture sprawdza mechanizm, nie jest kandydatem wygenerowanym przez rój.

## Następne zadania

1. Uruchomić rzeczywisty cel daemon_failure_exit: pełny pakiet wejściowy, lokalny basal, Hermes i :free API. Zachować istniejący ledger i jawny łączny limit, bez resetu.
2. Zbadać patch, niezależny odbiór, pełną regresję i review; po błędzie sprawdzić realne ponowienie z feedbackiem i po restarcie.
3. Zachować gotowego kandydata i przygotować draft PR z dowodami, bez auto-merge. Nie przepisywać celu na „wystarczy jedna propozycja”.
4. Domknąć publikację/oceny i sprzężenie zwrotne oraz przeprowadzić dłuższą obserwację powtarzalności, ograniczeń i bezczynności bez duplikatów.
5. Dopiero po audycie wszystkich wymagań uznać cel za ukończony; do tego czasu pozostawić go aktywnym.

Nie dodano komórek ani tabel D1. T24 i aktuacja pozostają odroczone. Parametry i dowody środowiska opisuje STABLE_EVOLUTION_RUNBOOK.md.
