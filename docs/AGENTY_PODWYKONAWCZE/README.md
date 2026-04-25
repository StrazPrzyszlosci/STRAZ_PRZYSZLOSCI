# Agenty Podwykonawcze

Ten katalog zawiera **wewnetrzne** pliki robocze dla agentow, ktorzy maja wykonywac konkretne zadania w repo, ale nie przejmowac roli glownego agenta rozwijajacego cala inicjatywe.

To nie jest onboarding dla nowych wolontariuszy.

Nowy wolontariusz i jego lokalny agent powinni startowac od:

- `docs/WOLONTARIUSZE_GOTOWE_PRZYDZIALY.md`

`docs/AGENTY_PODWYKONAWCZE/` sluzy do delegacji prac przez operatora repo wtedy, gdy brakuje jeszcze realnych wolontariuszy albo trzeba zlecic wewnetrzny zakres o scisle kontrolowanym write scope.

## Jak tego uzywac

1. Kazdy agent podwykonawczy najpierw czyta:
   - `docs/AGENTY_PODWYKONAWCZE/INSTRUKCJA_DLA_AGENTA_PODWYKONAWCZEGO.md`
   - aktualny przydzielony portfel, na przyklad `docs/AGENTY_PODWYKONAWCZE/PORTFEL_10_ZLECEN_DLA_PODWYKONAWCOW.md`, `docs/AGENTY_PODWYKONAWCZE/PORTFEL_06_ZLECEN_DLA_PODWYKONAWCOW_2026-04-23.md` albo `docs/AGENTY_PODWYKONAWCZE/PORTFEL_07_ZLECEN_DLA_PODWYKONAWCOW_2026-04-24.md`
   - przydzielony plik `ZLECENIE_GLOWNE_*.md`
2. Agent pracuje tylko w zakresie plikow wskazanych w swoim zadaniu.
3. Agent ma rozumiec, czemu jego zadanie sluzy wyzszemu celowi inicjatywy, ale nie ma samodzielnie przestawiac priorytetow calego repo.
4. Jesli trafi na blocker, raportuje go w swoim pliku wynikowym lub mini-handoffie i nie zaczyna samowolnie innego duzego watku bez nowego przydzialu.

## Co tu jest

- `INSTRUKCJA_DLA_AGENTA_PODWYKONAWCZEGO.md`: kanoniczna instrukcja roli
- `PORTFEL_10_ZLECEN_DLA_PODWYKONAWCOW.md`: zbiorcza mapa 10 zadan z priorytetami i zaleznosciami
- `SZABLON_ZADANIA_DLA_AGENTA_PODWYKONAWCZEGO.md`: wzorzec do kolejnych task file
- `ZLECENIE_GLOWNE_01_SYNC_ENCJI_ORGANIZACJI_DO_D1_SQLITE.md`: aktualne glowne zlozone zadanie do niezaleznego wykonania
- `ZLECENIE_GLOWNE_02_PROJECT13_RUN_CONTEXT_I_ARTIFACT_FLOW.md`
- `ZLECENIE_GLOWNE_03_PROJECT13_VERIFICATION_EXECUTION_SURFACE.md`
- `ZLECENIE_GLOWNE_04_PROJECT13_CURATION_CHAIN_PACK.md`
- `ZLECENIE_GLOWNE_05_PROJECT13_EXPORT_PACK_SMOKE_RUN.md`
- `ZLECENIE_GLOWNE_06_PROJECT13_BENCHMARK_COMPARISON_PACK.md`
- `ZLECENIE_GLOWNE_07_KNOWLEDGE_BUNDLE_DLA_NOWYCH_PACKOW.md`
- `ZLECENIE_GLOWNE_08_REVIEW_ROTATION_GOVERNANCE.md`
- `ZLECENIE_GLOWNE_09_D1_SQLITE_QUERY_COOKBOOK.md`
- `ZLECENIE_GLOWNE_10_PUBLIC_VOLUNTEER_RUN_READINESS.md`
- `PORTFEL_06_ZLECEN_DLA_PODWYKONAWCOW_2026-04-23.md`: kolejny portfel zadan `11-16`
- `ZLECENIE_GLOWNE_11_PROJECT13_VERIFICATION_REAL_EXECUTION_SURFACE.md`
- `ZLECENIE_GLOWNE_12_PROJECT13_PUBLIC_VOLUNTEER_PILOT_PACKET.md`
- `ZLECENIE_GLOWNE_13_PROJECT13_PILOT_REVIEW_ASSIGNMENT_AND_APPROVAL.md`
- `ZLECENIE_GLOWNE_14_BLUEPRINT_DESIGN_BRIEF_TEMPLATE.md`
- `ZLECENIE_GLOWNE_15_ESP32_RECOVERED_BOARD_PROFILE_TEMPLATE.md`
- `ZLECENIE_GLOWNE_16_BLUEPRINT_AND_ESP_RUNTIME_PACK_SKELETONS.md`
- `ODBIOR_PORTFELA_06_ZADAN_11_16_2026-04-24.md`: odbior zadan `11-16` wraz z werdyktem i lukami po przyjeciu
- `PORTFEL_07_ZLECEN_DLA_PODWYKONAWCOW_2026-04-24.md`: kolejny portfel zadan `17-22`
- `ZLECENIE_GLOWNE_17_PROJECT13_VERIFICATION_DISPUTE_TRIAGE_AND_OCR_PACKET.md`
- `ZLECENIE_GLOWNE_18_PROJECT13_CURATION_REAL_VERIFIED_SNAPSHOT_RUN.md`
- `ZLECENIE_GLOWNE_19_PROJECT13_VOLUNTEER_SECRETS_SETUP_GUIDE_AND_ENV_EXAMPLE.md`
- `ZLECENIE_GLOWNE_20_PROJECT13_PR_SECRET_SCAN_AND_BRANCH_PROTECTION_PACKET.md`
- `ZLECENIE_GLOWNE_21_PROJECT13_BLUEPRINT_BRIEF_VALIDATOR_AND_SCHEMA_BASELINE.md`
- `ZLECENIE_GLOWNE_22_PROJECT13_ESP_RUNTIME_BENCH_TEST_CONTRACT_AND_SIMULATION_POLICY.md`
- `CHECKLISTA_ODBIORU_ZLECENIA_GLOWNEGO_01_SYNC_ENCJI_ORGANIZACJI_DO_D1_SQLITE.md`: checklista dla glownego agenta sprawdzajacego wynik pracy podwykonawcy
- `ZADANIE_01_SYNC_ENCJI_ORGANIZACJI_DO_D1_SQLITE.md`: task dla warstwy wspolnej pamieci
- `ZADANIE_02_PROJECT13_RUN_CONTEXT_I_ARTIFACT_FLOW.md`: task dla dopiecia `Run -> Artifact`
- `ZADANIE_03_PROJECT13_NEXT_EXECUTION_PACKS.md`: task dla rozbicia kolejnych packow
- `ZADANIE_04_PROJECT13_CURATION_CHAIN_PACK.md`: task dla execution surface curation
- `ZADANIE_08_REVIEW_ROTATION_GOVERNANCE.md`: task i wynik dla governance review/approval
- `ZADANIE_09_D1_SQLITE_QUERY_COOKBOOK.md`: task dla query cookbook i lookup helpera
- `ZADANIE_10_PUBLIC_VOLUNTEER_RUN_READINESS.md`: task dla checklisty pierwszego publicznego runu
- `MINI_HANDOFF_ZADANIE_06.md`, `MINI_HANDOFF_ZADANIE_07.md`, `MINI_HANDOFF_ZADANIE_09.md`, `MINI_HANDOFF_ZADANIE_10.md`, `MINI_HANDOFF_ZADANIE_11.md`, `MINI_HANDOFF_ZADANIE_12.md`, `MINI_HANDOFF_ZADANIE_13.md`, `MINI_HANDOFF_ZADANIE_14.md`, `MINI_HANDOFF_ZADANIE_15.md`, `MINI_HANDOFF_ZADANIE_16.md`: wyniki przyjetych prac podwykonawczych
- `SMOKE_RUN_REPORT_PROJECT13_EXPORT_PACK_01.md`: raport lokalnego smoke runu export packa

## Zasada nadrzedna

Agent podwykonawczy nie jest "mniejsza kopia glownego stratega".
Jest wykonawca konkretnego zakresu.

Ma:

- dobrze dowiezc powierzony zakres,
- nie rozwalac pracy innych,
- zostawic po sobie czysty wynik i krotki mini-handoff,
- rozumiec wyzszy cel zadania.

Nie ma:

- sam wybierac nowej strategii dla calej inicjatywy,
- tunelowac pobocznych tematow poza swoim write scope,
- przepisywac architektury repo bez wyraznego przydzialu.

## Obowiazek glownego agenta po kolejnej sesji

Jesli zostal przygotowany nowy portfel zadan dla podwykonawcow, kolejna sesja glownego agenta ma najpierw:

1. sprawdzic, czy pojawily sie wyniki tych zadan,
2. odebrac je wzgledem acceptance criteria,
3. wpisac wynik odbioru do nowego handoffu,
4. dopiero potem wybierac nastepny duzy ruch portfelowy.
