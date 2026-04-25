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

Contract definiuje 17 testow w 5 kategoriach (zasilanie, flashowanie, GPIO, siec, storage). Kazdy test ma kategorie `real_hardware`, `simulated` albo `either`.

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

PLACEHOLDER — execution surface nie istnieje jeszcze. Pack jest w statusie `draft`.

Docelowo:

```bash
python3 PROJEKTY/13_baza_czesci_recykling/scripts/generate_esp_runtime.py --dossier <dossier_path> --board-profile <board_id>
```

Bench test:

```bash
python3 PROJEKTY/13_baza_czesci_recykling/scripts/bench_test_esp_runtime.py --board-id <board_id>
```

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