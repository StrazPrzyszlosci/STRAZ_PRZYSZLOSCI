# Runbook Dla Pack Project13 ESP Runtime 01

## Cel

Ten pack zamienia zatwierdzony projekt urzadzenia i profil odzyskanej plytki ESP32 w review-ready pakiet runtime z bench testem.

Docelowy przeplyw:

```text
zatwierdzony design dossier + board profile -> runtime profile, pin map, Lua bundle -> bench test -> PR
```

## Ostrzezenie

Ten pack steruje swiatem fizycznym. Wymaga ostrzejszego governance (Wariant B):

- rozdzielony reviewer merytoryczny i integrity reviewer
- approver nie jest jednoczesnie glownym reviewerem
- brak merge bez domknietego integrity_ready
- brak self-approval
- brak sterowania fizycznym GPIO bez bench testu

## Co trzeba miec przed startem

- zatwierdzony design dossier z packa blueprint-design-01 (po Approval)
- wypelniony board profile wg `docs/ESP32_RECOVERED_BOARD_PROFILE_TEMPLATE.md`
- fizyczna plytke ESP32 (do bench testu) — patrz polityka symulacji ponizej
- lokalne repo `Project 13`

### Bench test contract

Pack musi spelnic bench test contract przed merge: `docs/BENCH_TEST_CONTRACT_ESP_RUNTIME_01.md`

Contract definiuje 20 testow w 5 kategoriach (zasilanie, flashowanie, GPIO, siec, storage). Kazdy test ma kategorie `real_hardware`, `simulated` albo `either`.

Zasada: runtime bundle nie moze byc mergowany, jesli jakikolwiek test `real_hardware` ma status inny niz `PASS` albo `NOT_APPLICABLE`.

### Polityka simulated vs real hardware

Pelna polityka: `docs/SIMULATION_VS_REAL_HARDWARE_POLICY_ESP_RUNTIME_01.md`

Zasady kluczowe:

- Symulacja jest zawsze dozwolona jako krok posredni, ale **nie zastepuje** testu na realnym hardware.
- Testy symulowane to pre-check (walidacja struktury, pin map, Lua bundle).
- Testy na realnym hardware to flash, pomiary, GPIO, RF, recovery.
- Brak plytki = testy `real_hardware` sa `PENDING` = merge zablokowany.
- Sprzecznosc miedzy symulacja a real_hardware: wynik real_hardware jest autorytatywny.

## Komenda glowna

Simulated precheck (nie wymaga plytki):

```bash
python3 PROJEKTY/13_baza_czesci_recykling/scripts/simulated_precheck_esp_runtime.py \
  --board-profile PROJEKTY/13_baza_czesci_recykling/docs/SAMPLE_ESP32_BOARD_PROFILE_DEVKITC_V4.md
```

Z opcjonalnym runtime_profile:

```bash
python3 PROJEKTY/13_baza_czesci_recykling/scripts/simulated_precheck_esp_runtime.py \
  --board-profile <board_profile.md> \
  --runtime-profile <runtime_profile.json> \
  --output-dir <dir>
```

Docelowo (po zatwierdzonym design dossier):

```bash
python3 PROJEKTY/13_baza_czesci_recykling/scripts/generate_esp_runtime.py --dossier <dossier_path> --board-profile <board_id>
```

Bench test (wymaga plytki; obecnie manualny, bo `scripts/bench_test_esp_runtime.py` jeszcze nie istnieje):

Real hardware bench test (operator-ready):

1. Przeczytaj `output/REAL_HARDWARE_BENCH_PACKET.md` — sciezka testowa krok po kroku
2. Przejdz `output/OPERATOR_PRE_START_CHECKLIST.md` — wszystkie checkboxy zaznaczone
3. Wykonuj testy w kolejnosci: BT-PWR -> BT-FLS -> BT-GPIO -> BT-NET -> BT-STO
4. Wpisuj odczyty do `output/MEASUREMENT_LEDGER.md`
5. Po zakonczeniu: przepisz wyniki do bench_test_report.md
6. Sprawdz mapowanie na sub-gates: `output/READINESS_GATE_MAPPING.md`

### Status wykonania

Simulated precheck zostal uruchomiony na `SAMPLE_ESP32_BOARD_PROFILE_DEVKITC_V4.md` z wynikiem `conditional` (38 pass, 3 warn, 0 fail). Output artifacts w `output/`:

- `simulated_precheck_report.md` — raport z precheck
- `bench_test_report_TEMPLATE.md` — template bench test report (wszystkie real_hardware = PENDING)
- `runtime_profile.json` — stub runtime profile (dry_run, simulated)
- `pin_map.md` — pin map z board profile
- `flash_and_recovery_runbook.md` — runbook flashowania

Real hardware bench packet (zadanie 40) przygotowany. Output artifacts w `output/`:

- `REAL_HARDWARE_BENCH_PACKET.md` — operator-ready bench packet z kolejnoscia testow i sciezka testowa
- `MEASUREMENT_LEDGER.md` — template ledger z miejscem na odczyty, obserwacje i verdicty
- `OPERATOR_PRE_START_CHECKLIST.md` — checklist operatora przed startem testu na plytce
- `READINESS_GATE_MAPPING.md` — mapowanie wynikow bench testu na sub-gates readiness_gate

**Uwaga**: Simulated precheck NIE jest bench testem na realnym hardware. Wszystkie testy `real_hardware` pozostaja PENDING. Real hardware bench packet jest gotowy do uzycia, ale nie zawiera zadnych zmyslonych pomiarow.

## Co pack powinien zrobic

1. Przyjac zatwierdzony design dossier i board profile jako wejscie.
2. Wygenerowac runtime profile na podstawie capabilities plytki.
3. Zbudowac pin map na podstawie dostepnych GPIO z board profile.
4. Wygenerowac Lua bundle ze skryptami wykonawczymi.
5. Zbudowac flash and recovery runbook z instrukcja krok po kroku.
6. Uruchomic bench test i wygenerowac raport.
7. Otworzyc PR z review-ready runtime bundle.

## Czego pack nie powinien robic

- NIE flashowac bez bench testu i bez ReadinessGate(integrity_ready)
- NIE sterowac swiatem fizycznym bez jawnego bench review
- NIE ukrywac uszkodzonych pinow w pin map
- NIE traktowac bench simulation jako bench testu na realnym hardware
- NIE wpisac sekretow do firmware ani diffu
- NIE promowac do runtime bez Wariantu B governance

## Minimalne kryterium sukcesu

Pack jest wykonany poprawnie, gdy:

- runtime targetuje jawnie nazwana plytke (board_id), a nie abstrakcyjne ESP32,
- pin map i recovery path sa opisane i przetestowane przed pierwszym flash,
- bench test raport istnieje i pokazuje wyniki testow,
- wszystkie testy real_hardware z BENCH_TEST_CONTRACT maja status PASS albo NOT_APPLICABLE,
- symulacja nie zastapila testow real_hardware,
- reviewer moze przejrzec caly runtime bundle jako jeden PR z integrity review.
