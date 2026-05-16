# ZLECENIE GŁÓWNE 109 - KiCad review ledger pagination

## Cel

Dodać paginację albo cursor dla listy pending i audit export, aby operator mógł przeglądać większą kolejkę bez przeciążania odpowiedzi bota.

## Kryteria odbioru

- Limit ma bezpieczny zakres i domyślną wartość.
- Cursor/offset nie pozwala na SQL injection.
- Test obejmuje limit, offset i przekroczenie maksymalnego limitu.
- Dokumentacja wskazuje, że pełne eksporty powinny iść przez receipt, nie przez długą wiadomość bota.

## Status

TODO — zależy od Z96/Z97.
