# ZLECENIE GŁÓWNE 102 - KiCad export release receipt

## Cel

Dodać lekki receipt JSON/Markdown dla każdego eksportu KiCad approved provenance, żeby operator mógł audytować kiedy, z jakiej bazy i z jakim limitem wygenerowano plik.

## Kryteria odbioru

- Receipt zawiera timestamp, row_count, status_filter=`approved`, source tables, requester/reviewer context oraz hash CSV.
- Receipt nie zawiera sekretów ani pełnych prywatnych tokenów.
- Test potwierdza stabilny hash dla znanego fixture i brak rekordów nie-approved.
- Receipt jest dodatkiem do eksportu, nie zastępuje human review ledger.

## Status

TODO — zależy od Z91 i najlepiej Z96.
