# human_approval

Komorka zatwierdzania przez czlowieka (T19, dawniej H4).
Rekord zawiera: kto/co/zakres/czas/ryzyka/expiry/rollback.

## Zasady bezpieczenstwa

- Approval wygasa (expires_at); walidator auto-rejects expired records.
- code_review scope nie moze pokryc physical_installation ani production_deploy.
- provider_cost_increase approval wymaga cost_ledger_ref (brak ledgeru = rejected).
- revoked=true oznacza anulowanie; record powinien bycz archiwizowany/overwritten.

## Uruchomienie

```bash
python3 human_approval/validate_record.py
```
