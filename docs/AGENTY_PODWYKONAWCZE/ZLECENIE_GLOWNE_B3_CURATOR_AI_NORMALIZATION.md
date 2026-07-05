# ZLECENIE GŁÓWNE B3 - Curator AI normalizacja (H2 roadmapy)

## Cel

Agent `curator` — AI sugeruje normalizację (species/genus/mounting) dla `verified` rekordów jako `suggested`. Sugestia tylko; nie nadpisuje `recycled_part_master` bez human review (Z90 ledger).

## Zakres

- Dla każdego rekordu w `kicad_library_components` ze statusem `verified`:
  1. AI sugestia dopasowania KiCad → NSIP `recycled_part_master` (match MPN/footprint/keywords).
  2. Wstawienie do `recycled_part_kicad_links` ze statusem `suggested` (Z90, cienka warstwa nad `kicad_review.js`).
  3. Sugestia normalizacji (package → species, mount → mounting, footprint → genus).
- Gate: **sugestia tylko** — event `next_status=suggested` nie zapisuje do `recycled_part_master`.
- Rollback: event `next_status=suggested` można odrzucić / needs_more_data przez maintenera.
- Metryka: coverage normalizacji (% rekordów z sugestią / verified) oraz false-positive ratio (cel <30%).

## Kryteria odbioru

- Curator wstawia tylko `suggested` w `recycled_part_kicad_links` (Z90).
- AI **nigdy** nie ustawia `approved` (wymuszane w `kicad_review.js` — `reviewed_by=ai` zablokowane dla approve).
- Każda sugestia zapisana w `kicad_review_events` (kind `suggest`).
- `recycled_part_master` NIE nadpisany przez curatora.
- Test integracyjny: curator → suggest → maintener approve → `approved` (Z90/Test Z91).

## Blokery

- B2 (verifier) zalecane wcześniej — curator operuje tylko na `verified` rekordach.
- Z90 (`kicad_review.js`) — DONE (fundament ledgeru).

## Powiązania

- `cloudflare/src/kicad_review.js` (Z90) — `suggestKicadLink`, blokada `reviewed_by=ai`.
- `cloudflare/src/kicad_lookup.js` (Z89) — lookup KiCad/NSIP.
- `docs/ROADMAPA_AUTONOMICZNEJ_AUTOMATYZACJI_AI.md` (Z95) — H2 krok B3.

## Status

OPEN (2026-07-05) — utworzone przez agenta jako S5 z `HANDOFF_..._PO_R1_R5_R7_R8.md`. Czeka na realizacje (po B2).
