# ZLECENIE GŁÓWNE 106 - KiCad audit operator preview

## Cel

Dodać bezpieczny preview audytu KiCad review dla operatora Discord/Telegram, który pokazuje ostatnie decyzje i provenance bez generowania pełnego pliku release.

## Kryteria odbioru

- Preview używa `listKicadReviewAuditEvents()` albo `buildKicadReviewAuditCsvFromDb()`.
- Dostęp jest ograniczony do maintainerów/operatorów.
- Odpowiedź pokazuje minimum: ostatni status, reviewer, reason, źródło i licencję.
- Test obejmuje brak uprawnień i poprawny preview maintainera.

## Status

DONE — wykonane w tej sesji. Odbiór: `ODBIOR_PORTFELA_27_ZADANIE_106_2026-05-16.md`.
