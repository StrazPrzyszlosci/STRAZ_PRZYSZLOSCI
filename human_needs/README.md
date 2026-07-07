# human_needs

Lekka komorka intake potrzeb i problemow ludzkich/inicjatyw. Celem jest zbieranie sygnalow potrzeb, mapowanie ich na PotentialDossier / resource_scout / model_resource_selector, ale bez automatycznego wyboru wykonania fizycznego.

## Pliki

- `intake_schema.json` - kontrakt `HumanNeedIntake`.
- `validate_records.py` - walidator bez zewnetrznych zaleznosci.
- `seed_needs.json` - przykladowe zgloszenia.

## Zasady bezpieczenstwa

- Prywatne dane kontaktowe (`submitted_by.contact_note`) NIE moga bycz exposed pod `visibility_scope.level == public` (walidator blokuje).
- `energy_constraints.preferred_class == high_energy_requires_oze_or_justification` wymaga `oze_required=true` (no greenwash).
- Rekomendacja automatyzacji NIE moze pre-selekcjonowac wykonania fizycznego - `expected_outcome` blokowany jezeli zawiera `install`/`actuate`/`deploy`/`trigger_production` gdy `origin.chosen_from_recommendation == true`.
- Modul NIE laczy sie z hardware. Realizuje tylko format i walidacje intake.

## Uruchomienie

```bash
python3 human_needs/validate_records.py
python3 human_needs/validate_records.py sciezka/do/needs.json
```
