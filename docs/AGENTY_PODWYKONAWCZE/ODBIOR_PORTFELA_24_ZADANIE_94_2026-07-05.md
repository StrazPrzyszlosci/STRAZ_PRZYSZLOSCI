# Odbiór Zadania 94 - Discord KiCad review actions - 2026-07-05

## Zakres odbioru

Wykonano Z94: przyciski/akcje Discord dla kolejki review KiCad, jako cienka warstwa nad wspólnym modułem `kicad_review.js`.

## Wynik odbioru

| ID | Zakres | Status | Uwagi odbioru |
|----|--------|--------|---------------|
| Z94 | Discord KiCad review actions | PASS | Dodano `cloudflare/src/discord_kicad_actions.js`, integrację w `discord_api_handler.js`, testy `tests/discord_kicad_actions_test.mjs`. |

## Co zaimplementowano

1. `cloudflare/src/discord_kicad_actions.js`:
   - `handleKicadReviewCommand()` — komenda `!kicad` zwraca kolejkę pending + przyciski "Zatwierdz".
   - `handleKicadReviewAction()` — obsługa callbacków `kicad_review_approve` / `kicad_review_reject` / `kicad_review_more_data`.
   - `buildKicadReviewQueueButtons()` — generuje przyciski Discord (max 5) z wartościami `kicad_review_approve:<master_part_id>:<kicad_component_id>`.
   - `isMaintainer()` — walidacja po `KICAD_REVIEW_MAINTAINER_IDS` (user_id / username) i `KICAD_REVIEW_MAINTAINER_ROLES` (role Discord).
2. `cloudflare/src/discord_api_handler.js`:
   - Import `handleKicadReviewCommand`, `handleKicadReviewAction`.
   - Komenda `!kicad` / `!kicad_review` w `handleCommand`.
   - Wczesne rozgałęzienie w `handleDiscordCallback` dla `kicad_review_*` przed switchem.
   - `parseDiscordBody` przekazuje `body.roles` dla sprawdzania ról maintenera.
3. `tests/discord_kicad_actions_test.mjs` — 10 testów (mock D1 jak w `kicad_review_test.mjs`).

## Co zweryfikowano (kryteria odbioru Z94)

- **Brak oddzielnej logiki biznesowej Discord:** wszystkie akcje wywołują `listPendingKicadReviewLinks`, `buildKicadReviewQueueReply`, `recordKicadReviewDecision` z `kicad_review.js`. Žadna duplikacja SQL/ledgeru.
- **Tylko uprawniony maintainer może zatwierdzać:** `isMaintainer()` blokuje approve dla nieautoryzowanych; reject/needs_more_data dostępne dla każdego (nie wymagaGate człowieka — to modyfikacja statusu, nie promocja).
- **Każda akcja zapisuje `reviewed_by`, `reviewed_at`, `reason` i poprzedni status:** zapewnia to `recordKicadReviewDecision` -> `recordReviewEvent` (z Z90). Discord dodaje tylko identity `discord:<username>#<user_id>` w `reviewed_by`.
- **AI cannot approve:** `recordKicadReviewDecision` (Z90) bloka `reviewed_by=ai` dla approved; Discord nie omija tej blokady.

## Decyzje bezpieczeństwa

- Maintainer definicja przez env `KICAD_REVIEW_MAINTAINER_IDS` (lista user_id/username) i/lub `KICAD_REVIEW_MAINTAINER_ROLES` (lista ról Discord). Brak hardkodowanych uprawnień.
- Approve wymaga maintenera; reject i needs_more_data nie — bo to nie promuje linku do produkcyjnego eksportu.
- `reviewed_by` zawsze z prefixem `discord:` dla audytowalności źródła decyzji.

## Testy odbiorowe

```bash
node --check cloudflare/src/discord_kicad_actions.js
node --check cloudflare/src/discord_api_handler.js
node --test tests/discord_kicad_actions_test.mjs
node --test tests/*.mjs
```

Wynik: 198 testów PASS (0 fail), w tym 10 nowych dla Z94.

## Środowisko (do ustawienia w secrets Cloudflare)

- `KICAD_REVIEW_MAINTAINER_IDS` — lista user_id lub username Discord maintenerów (np. `123456, alice`).
- `KICAD_REVIEW_MAINTAINER_ROLES` — lista ról Discord uprawnionych do approve (np. `kicad-maintainer, reviewer`).
- Discord webhook musi przekazywać `roles` w body, by sprawdzenie ról działało.

## Decyzja odbiorowa

Z94 jest odebrane. Kolejka review KiCad jest teraz dostępna z konsoli Discord przez `!kicad` i przyciski, bez duplikacji logiki ledgeru.
