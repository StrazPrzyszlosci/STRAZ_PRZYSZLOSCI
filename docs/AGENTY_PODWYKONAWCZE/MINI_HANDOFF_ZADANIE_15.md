# Mini-Handoff Zadanie 15

## Co zostalo zrobione

Utworzono `ESP32 recovered board profile template` i przykladowy wypelniony profile:

- `PROJEKTY/13_baza_czesci_recykling/docs/ESP32_RECOVERED_BOARD_PROFILE_TEMPLATE.md`
- `PROJEKTY/13_baza_czesci_recykling/docs/SAMPLE_ESP32_BOARD_PROFILE_DEVKITC_V4.md`

## Jakie pliki dotknieto

- `PROJEKTY/13_baza_czesci_recykling/docs/ESP32_RECOVERED_BOARD_PROFILE_TEMPLATE.md` (nowy)
- `PROJEKTY/13_baza_czesci_recykling/docs/SAMPLE_ESP32_BOARD_PROFILE_DEVKITC_V4.md` (nowy)

## Ktore pola sa nienegocjowalne dla runtime

Pola krytyczne dla bezpieczenstwa runtime — bez nich profil nie moze byc uznany za flash-ready:

- `board_id` — unikalna identyfikacja w katalogu
- `board_variant` — wariant MCU musi byc jawnie nazwany, a nie abstrakcyjne "ESP32"
- `input_voltage` i `operating_voltage` — bledne zasilanie = fizyczne uszkodzenie
- `flash_method` i `boot_mode_entry` — bez tego nie da sie flashowac
- `recovery_after_brick` — bez jawnej sciezki odzysku nie wolno flashowac
- `antenna_condition` — uszkodzona antena = brak Wi-Fi = brak runtime komunikacji
- `safety_notes` — wymagane dla Wariantu B governance (hardware runtime)
- `damaged_pins` — uzywane uszkodzone piny = niestabilny runtime

## Co zweryfikowano

- spojnosc z `PLAN_PACKOW_BLUEPRINT_ESP_CLAW.md`: input contract z sekcji "Pack 2" pokrywa sie z polami szablonu (zatwierdzony design dossier, profil odzyskanej plytki, lista peryferiow i pinow, constraints bezpieczenstwa)
- template rozroznia pola `[POMIERZONE]`, `[DOMNIEMANE]` i `[BRAKUJACE]` — spelnia acceptance criterion
- sample profile dla DevKitC-V4 wypelnia wszystkie sekcje z realnymi wartosciami, a pola brakujace sa jawnie oznaczone
- `git diff --check`: brak bledow whitespace

## Czego nadal brakuje przed pierwszym skeletonem packa

- brak formalnego schema JSON dla board profile (zgodnie z blockerem: najpierw dobry markdown template, nie zly schema contract)
- brak bench test contract — szablon opisuje wejscie, ale nie definiuje, jak testowac plytke przed runtime
- brak polityki "kiedy simulated vs real hardware" — kiedy profile moze byc uzywany do symulacji, a kiedy do realnego flashowania
- pola `[BRAKUJACE]` w sample profile (power consumption, eeprom, firmware constraints) musza byc uzupelnione przez bench test
- brak automatycznej walidacji `board_id` unikalnosci — na teraz reczna kontrola przez review
- pack `esp-runtime-01` potrzebuje ostrzejszego modelu governance (Wariant B z `REVIEW_ROTATION_GOVERNANCE.md`) — to trzeba dopisac do skeletonu packa
