# Portfel 06 Zlecen Dla Podwykonawcow 2026-04-23

Ten dokument jest kolejnym portfelem prac po poprzednim pakiecie `01-10`.

To jest portfel **wewnetrznych** zadan dla agentow-podwykonawcow operatora repo.
Nie jest to lista przydzialow dla nowych wolontariuszy.

Ma sluzyc nie do "wypelnienia dokumentow", tylko do domkniecia najwazniejszych luk po obecnym stanie repo:

- realnego verification,
- pierwszego publicznego pilota,
- fundamentow pod warstwe `Blueprint.am` i `ESP-Claw`.

## Kolejnosc pracy

Najpierw dawaj zadania z priorytetu `A`, potem `B`, potem `C`.

## Portfel

1. `A` - `ZLECENIE_GLOWNE_11_PROJECT13_VERIFICATION_REAL_EXECUTION_SURFACE.md`
   - zaleznosci: obecny `pack-project13-kaggle-verification-01`
   - odbior: acceptance criteria z pliku zadania
2. `A` - `ZLECENIE_GLOWNE_12_PROJECT13_PUBLIC_VOLUNTEER_PILOT_PACKET.md`
   - zaleznosci: `PUBLIC_VOLUNTEER_RUN_READINESS.md`, `RUNBOOK.md`, governance `08`
   - odbior: acceptance criteria z pliku zadania
3. `A` - `ZLECENIE_GLOWNE_13_PROJECT13_PILOT_REVIEW_ASSIGNMENT_AND_APPROVAL.md`
   - zaleznosci: `REVIEW_ROTATION_GOVERNANCE.md`, `PUBLIC_VOLUNTEER_RUN_READINESS.md`
   - odbior: acceptance criteria z pliku zadania
4. `B` - `ZLECENIE_GLOWNE_14_BLUEPRINT_DESIGN_BRIEF_TEMPLATE.md`
   - zaleznosci: `PLAN_PACKOW_BLUEPRINT_ESP_CLAW.md`
   - odbior: acceptance criteria z pliku zadania
5. `B` - `ZLECENIE_GLOWNE_15_ESP32_RECOVERED_BOARD_PROFILE_TEMPLATE.md`
   - zaleznosci: `PLAN_PACKOW_BLUEPRINT_ESP_CLAW.md`
   - odbior: acceptance criteria z pliku zadania
6. `C` - `ZLECENIE_GLOWNE_16_BLUEPRINT_AND_ESP_RUNTIME_PACK_SKELETONS.md`
   - zaleznosci: wyniki `14` i `15` sa pomocne, ale nieobowiazkowe
   - odbior: acceptance criteria z pliku zadania

## Zasada dla glownego agenta

Glowny agent:

- nie wykonuje tych zadan za podwykonawce, jesli wynik juz zostal zlecony,
- najpierw sprawdza, czy sa wyniki zadan `11-16`,
- odbiera je wzgledem acceptance criteria,
- wpisuje do kolejnego handoffu, co zostalo przyjete, co wymaga poprawek i ktore zlecenia nadal sa otwarte.

Brak odbioru tych zadan w nastepnej sesji bedzie oznaczal utrate ciaglosci pracy, wiec to jest obowiazek, nie opcja.
