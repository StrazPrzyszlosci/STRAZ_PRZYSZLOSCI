# Zlecenie Glowne 55 Project13 Hardware And Canary Maintainer Closeout

## 1. Misja zadania

Domknac dwa pozostale blockery, ale tylko przy realnych warunkach: ESP runtime bench na fizycznej plytce oraz canary GO/NO-GO podpisany przez maintainera.

## 2. Read First

- `docs/AGENTY_PODWYKONAWCZE/MINI_HANDOFF_ZADANIE_46.md`
- `docs/AGENTY_PODWYKONAWCZE/MINI_HANDOFF_ZADANIE_49.md`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-esp-runtime-01/output/REAL_HARDWARE_BENCH_PACKET.md`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-esp-runtime-01/output/MEASUREMENT_LEDGER.md`
- `PROJEKTY/13_baza_czesci_recykling/docs/CANARY_GO_LIVE_OPERATOR_PACKET.md`

## 3. Write Scope

- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-esp-runtime-01/output/MEASUREMENT_LEDGER.md`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-esp-runtime-01/output/bench_test_report.md`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-esp-runtime-01/readiness_gate.json`
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/esp_runtime_bench_receipt_*.json`
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/canary_go_no_go_receipt_*.json`
- `PROJEKTY/13_baza_czesci_recykling/autonomous_test/reports/canary_run_receipt_*.json`
- `docs/AGENTY_PODWYKONAWCZE/MINI_HANDOFF_ZADANIE_55.md`

## 4. Deliverables

- Jesli jest fizyczna plytka: wypelniony bench report z realnymi pomiarami.
- Jesli nie ma fizycznej plytki: nie powielaj starego receipt bez nowych faktow; dopisz tylko mini-handoff z aktualnym blockerem.
- Jesli maintainer podpisuje GO/NO-GO: receipt jawnie rozrozniajacy maintainer signature od decyzji agenta.
- Jesli canary rusza: `canary_run_receipt`.
- Mini-handoff.

## 5. Acceptance Criteria

- Pomiary ESP musza pochodzic z fizycznej plytki i realnego miernika.
- `bench_test_real_hardware_pass` przechodzi na pass tylko przy wszystkich wymaganych PASS/NOT_APPLICABLE.
- Canary GO nie istnieje, jesli choc jeden C-1..C-5 jest OPEN.
- Sekrety Wi-Fi/MQTT/wolontariuszy nie trafiaja do repo.
- Brak maintainera albo hardware = blocker, nie kreatywne obejscie.

## 6. Walidacja

- `python3 -m json.tool PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-esp-runtime-01/readiness_gate.json`
- `python3 -m json.tool <new_receipt>.json`
- kontrola C-1..C-5 w `CANARY_GO_LIVE_OPERATOR_PACKET.md`
- `git diff --check`

