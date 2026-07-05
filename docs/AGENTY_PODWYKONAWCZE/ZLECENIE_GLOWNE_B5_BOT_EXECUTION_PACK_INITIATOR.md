# ZLECENIE GŁÓWNE B5 - Bot execution_pack initiator (H2 roadmapy)

## Cel

Bot Discord/Telegram inicjuje `execution_pack` (Project 13) jako autonomiczne zadanie — fork-first, PR-first, review-first (`CANARY_PILOT_PACKET`). Brak nadpisywania katalogu produkcyjnego bez human review.

## Zakres

- Komenda bota `!execution-pack start <id>`:
  1. Generuje nowy `execution_pack` w nowym fork/branch (fork-first).
  2. Tworzy PR z wymaganym `reviewer` (człowiek wyznaczony).
  3. PR w trybie `CANARY` (preview deploy, nie merge do main).
  4. Status zapisany w D1 (`execution_packs` table): `started`, `reviewer`, `pack_id`, `fork_branch`, `pr_url`.
- Gatę: fork-first, PR-first, review-first (patrz `CANARY_PILOT_PACKET`).
- Rollback: zamknięcie PR bez merge (Closes status `closed`).
- Metryka: N PR/sprint + brak bezpośredniego merge bez review.

## Kryteria odbioru

- Bot **NIE** może merge'ować do main bez human review (gate review-first).
- Bot **NIE** może pisać do `recycled_part_master` bez osobnej synchronizacji (Z91).
- PR ma `reviewer` przypisany (D1 record).
- Status packa aktualizowany w D1 (started/closed/merged).
- Test integracyjny: `!execution-pack start` → fork → PR → zamknij PR (rollback).

## Blokery

- B4 (metryki) zalecane wcześniej — do health-check bota.
- `CANARY_PILOT_PACKET` document (jeśli istnieje — fleec led flow).

## Powiązania

- `cloudflare/src/discord_kicad_actions.js` (Z94) — wzorzec akcji Discord nad wspólnym modułem.
- `cloudflare/src/kicad_review.js` (Z90) — gate maintenera.
- `docs/ROADMAPA_AUTONOMICZNEJ_AUTOMATYZACJI_AI.md` (Z95) — kolejka autonomicznych zadań + B5 (H2).
- `PROJEKTY/13_baza_czesci_recykling/` — katalog docelowy.

## Status

OPEN (2026-07-05) — utworzone przez agenta jako S5 z `HANDOFF_..._PO_R1_R5_R7_R8.md`. Czeka na realizacje (ostatni w kolejności, po B1-B4).
