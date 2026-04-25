# Review Checklist Dla Pack Project13 ESP Runtime 01

## Wariant B — ostrzejszy model governance

### Review merytoryczny

- [ ] runtime targetuje jawnie nazwana plytke (board_id), a nie abstrakcyjne ESP32
- [ ] pin map jest spojny z board profile (dostepne GPIO, uszkodzone piny wykluczone)
- [ ] recovery path jest opisany i wykonalny
- [ ] Lua bundle jest czytelny i nie zawiera ukrytych zaleznosci
- [ ] flash runbook prowadzi krok po kroku bez luk informacyjnych

### Integrity review

- [ ] IntegrityRiskAssessment istnieje i odpowiada realnej zmianie
- [ ] pack nie steruje swiatem fizycznym bez bench testu
- [ ] sekrety (Wi-Fi credentials, API keys) nie trafiaja do firmware ani diffu
- [ ] brak vendor lock-in — jawne alternatywy dla uzanych komponentow runtime
- [ ] approver nie jest jednoczesnie glownym reviewerem
- [ ] brak self-approval

### Bench test

- [ ] bench_test_report.md istnieje i pokazuje wyniki testow
- [ ] bench test zostal wykonany na realnym hardware, a nie tylko w symulacji
- [ ] uszkodzone piny z board profile nie sa uzywane w runtime bez potwierdzenia pomiarem
- [ ] wyniki bench testu sa spojne z board profile (napiecie, GPIO, siec)
- [ ] wszystkie testy real_hardware z BENCH_TEST_CONTRACT maja status PASS albo NOT_APPLICABLE
- [ ] zaden test real_hardware nie ma status PENDING albo FAIL
- [ ] symulacja nie zastapila testow real_hardware w bench_test_report
- [ ] bench test report zawiera metryke: data, board_id, board_variant, flash_method, tester
- [ ] kolejnosc testow: zasilanie -> flash -> GPIO -> siec -> storage (zgodnie z BENCH_TEST_CONTRACT)

### Symulacja vs real hardware (polityka)

- [ ] runtime bundle w trybie draft moze istniec z testami PENDING, ale nie moze byc mergowany
- [ ] decyzja o przejsciu z symulacji do real_hardware jest udokumentowana
- [ ] board profile ma pola krytyczne jako [POMIERZONE] przed przejsciem do real_hardware
- [ ] sprzecznosc miedzy symulacja a real_hardware jest odnotowana z analiza przyczyny

### Governance

- [ ] ReadinessGate(integrity_ready) jest domkniety przed merge
- [ ] reviewer merytoryczny i integrity reviewer sa rozdzieleni
- [ ] PR nie miesza runtime z design dossier — to sa osobne packi