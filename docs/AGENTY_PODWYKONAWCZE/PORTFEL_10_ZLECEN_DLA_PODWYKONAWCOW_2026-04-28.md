# Portfel 10 Zlecen Dla Podwykonawcow 2026-04-28

Ten portfel powstaje po odbiorze portfela `09`.

Nie sluzy do dalszego rozpychania `Project 13` bez kontroli.
Ma zamienic obecne blokery review, OCR, canary i real-hardware w packet ready dla ludzi i operatorow, tak zeby kolejna sesja nie zaczynala od ponownego skladania kontekstu.

## Kolejnosc pracy

Najpierw dawaj zadania z priorytetu `A`, potem `B`.

## Portfel

1. `A` - `ZLECENIE_GLOWNE_35_PROJECT13_CURATION_REVIEW_ASSIGNMENT_PACKET_AND_BATCHING.md`
   - zaleznosci: wynik `31`, `curation_review_queue.jsonl`, `HUMAN_APPROVAL_LEDGER.md`, placeholder `REVIEW_ASSIGNMENT_PACKET.md`
   - odbior: acceptance criteria z pliku zadania
2. `A` - `ZLECENIE_GLOWNE_36_PROJECT13_OCR_DEFERRED_CASE_SELECTOR_AND_PROMPT_PACKET.md`
   - zaleznosci: wynik `30`, `deferred_resolution_workpack.json`, `verify_candidates.py`, `status_resolution_packet.json`
   - odbior: acceptance criteria z pliku zadania
3. `A` - `ZLECENIE_GLOWNE_37_PROJECT13_MANUAL_REVIEW_RUBRIC_AND_DECISION_PACKET.md`
   - zaleznosci: wynik `30`, `deferred_resolution_workpack.md`, `verification_report.md`, `verification_triage.jsonl`
   - odbior: acceptance criteria z pliku zadania
4. `B` - `ZLECENIE_GLOWNE_38_PROJECT13_EXPORT_OPEN_READINESS_PACKET_AND_RELEASE_RECEIPT_TEMPLATE.md`
   - zaleznosci: wyniki `29` i `31`, `export_gate_packet.json`, runbooki `curation` i `catalog-export`
   - odbior: acceptance criteria z pliku zadania
5. `B` - `ZLECENIE_GLOWNE_39_PROJECT13_CANARY_GO_LIVE_OPERATOR_PACKET_AND_BLOCKER_LEDGER.md`
   - zaleznosci: wynik `32`, `CANARY_PILOT_PACKET.md`, `PUBLIC_VOLUNTEER_RUN_READINESS.md`, `BRANCH_PROTECTION_OPERATOR_PACKET.md`, `docs/WOLONTARIUSZE_GOTOWE_PRZYDZIALY.md`
   - odbior: acceptance criteria z pliku zadania
6. `B` - `ZLECENIE_GLOWNE_40_PROJECT13_ESP_RUNTIME_REAL_HARDWARE_BENCH_PACKET_AND_MEASUREMENT_LEDGER.md`
   - zaleznosci: wynik `34`, `simulated_precheck_esp_runtime_01_2026-04-28.md`, `BENCH_TEST_CONTRACT_ESP_RUNTIME_01.md`, `SIMULATION_VS_REAL_HARDWARE_POLICY_ESP_RUNTIME_01.md`, `pack-project13-esp-runtime-01`
   - odbior: acceptance criteria z pliku zadania

## Zasada dla glownego agenta

Glowny agent:

- jako stan bazowy przyjmuje `docs/AGENTY_PODWYKONAWCZE/ODBIOR_PORTFELA_09_ZADAN_29_34_2026-04-28.md`
- ten datowany portfel traktuje jako kanoniczny dla tej iteracji, a nie starszy, niedatowany `PORTFEL_10_ZLECEN_DLA_PODWYKONAWCOW.md`
- zanim rozda `35-40`, sprawdza, czy lokalne wyniki `31-34` zostaly juz commitowane albo celowo odseparowane
- odbiera wyniki wzgledem acceptance criteria
- wpisuje do kolejnego handoffu, co jest juz kanoniczne, a co nadal istnieje tylko w `worktree`

Najwyzsza dzwignia jest teraz w `35-39`.
`40` przygotowuje przejscie z symulacji do realnego hardware, ale nie powinno wyprzedzac review gate ani canary gate.
