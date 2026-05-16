# ZLECENIE GŁÓWNE 99 - Reviewer rotation D1 policy

## Cel

Zaprojektować minimalną politykę rotacji reviewerów dla decyzji KiCad i późniejszych approvali, aby ograniczyć ryzyko centralizacji decyzji.

## Kryteria odbioru

- Dokument wskazuje pola/tabelę D1 lub konfigurację env dla reviewerów i ról.
- Polityka rozróżnia: operator, reviewer techniczny, maintainer zatwierdzający, audytor.
- Wskazuje reguły anty-nadużyciowe: brak samo-zatwierdzania, jawny `reviewed_by`, powód decyzji, możliwość audytu.
- Nie wymaga wdrożenia ciężkiego systemu uprawnień w pierwszym kroku; ma być kompatybilna z `DISCORD_KICAD_REVIEWER_IDS`.

## Status

TODO — po Z94, przed rozszerzaniem automatyki approvali.
