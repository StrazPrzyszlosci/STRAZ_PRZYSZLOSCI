# Portfel 07 Zlecen Dla Podwykonawcow 2026-04-24

Ten portfel powstaje po odbiorze zadan `11-16`.

Jego celem nie jest dopisywanie kolejnych scaffoldow, tylko domkniecie najwazniejszych brakow, ktore zostaly po ich przyjeciu:

- disputed verification i realny handoff do curation,
- uproszczenie onboardingowego setupu wolontariusza,
- zamkniecie czesci readiness dla publicznego pilota,
- doprecyzowanie kontraktow zanim `blueprint` i `esp-runtime` dostana prawdziwe execution surface.

## Kolejnosc pracy

Najpierw dawaj zadania z priorytetu `A`, potem `B`.

## Portfel

1. `A` - `ZLECENIE_GLOWNE_19_PROJECT13_VOLUNTEER_SECRETS_SETUP_GUIDE_AND_ENV_EXAMPLE.md`
   - zaleznosci: `WOLONTARIUSZE_GOTOWE_PRZYDZIALY.md`, `PUBLIC_VOLUNTEER_RUN_READINESS.md`, `RUNBOOK.md`
   - odbior: acceptance criteria z pliku zadania
2. `A` - `ZLECENIE_GLOWNE_17_PROJECT13_VERIFICATION_DISPUTE_TRIAGE_AND_OCR_PACKET.md`
   - zaleznosci: wynik zadania `11`, `verify_candidates.py`, `verification_disagreements.jsonl`
   - odbior: acceptance criteria z pliku zadania
3. `A` - `ZLECENIE_GLOWNE_18_PROJECT13_CURATION_REAL_VERIFIED_SNAPSHOT_RUN.md`
   - zaleznosci: wynik zadania `11`, `curate_candidates.py`, `test_db_verified.jsonl`
   - odbior: acceptance criteria z pliku zadania
4. `A` - `ZLECENIE_GLOWNE_20_PROJECT13_PR_SECRET_SCAN_AND_BRANCH_PROTECTION_PACKET.md`
   - zaleznosci: wynik zadania `12`, `13`, readiness publicznego pilota
   - odbior: acceptance criteria z pliku zadania
5. `B` - `ZLECENIE_GLOWNE_21_PROJECT13_BLUEPRINT_BRIEF_VALIDATOR_AND_SCHEMA_BASELINE.md`
   - zaleznosci: wynik zadania `14`, skeleton `blueprint-design-01`
   - odbior: acceptance criteria z pliku zadania
6. `B` - `ZLECENIE_GLOWNE_22_PROJECT13_ESP_RUNTIME_BENCH_TEST_CONTRACT_AND_SIMULATION_POLICY.md`
   - zaleznosci: wynik zadania `15`, `16`, `REVIEW_ROTATION_GOVERNANCE.md`
   - odbior: acceptance criteria z pliku zadania

## Zasada dla glownego agenta

Glowny agent:

- nie ignoruje juz odebranego portfela `06`, tylko traktuje go jako stan bazowy,
- najpierw sprawdza, czy sa wyniki zadan `17-22`,
- odbiera je wzgledem acceptance criteria,
- wpisuje do kolejnego handoffu, co zostalo przyjete, co wymaga poprawek i ktore zlecenia nadal sa otwarte.

Brak odbioru tych zadan w nastepnej sesji bedzie oznaczal kolejna utrate ciaglosci pracy.
