# ZLECENIE GŁÓWNE 89 - Lookup KiCad w botach Discord i Telegram

## Cel

Dodać wspólną warstwę lookup KiCad dla Discord i Telegram, aby użytkownik mógł zapytać o symbol/footprint i otrzymać odpowiedź ze źródłem oraz statusem dopasowania.

## Przepływ

1. Szukaj w `recycled_part_master`.
2. Jeśli brakuje footprintu/symbolu albo brak rekordu, szukaj w `kicad_library_components`.
3. Zwróć: part number, symbol, footprint, źródło, licencja, confidence, review status.
4. Dla niepewnych dopasowań pokaż przycisk/akcję wysłania do review.

## Kryteria odbioru

- Wspólna funkcja używana przez obie platformy.
- Discord nie dostaje osobnej logiki biznesowej względem Telegrama.
- Odpowiedzi mieszczą się w limitach Discord i Telegram.

## Status

TODO — zależy od Z88.
