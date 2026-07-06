# Handoff dla Następnego Agenta - po T5 (B5 bot execution_pack initiator) - 2026-07-06

## Kontekst inicjatywy

Repo NSIP/Straż Przyszłości nie jest pojedynczym Projektem 13. To większa inicjatywa łącząca agentową organizację pracy, reusable memory/provenance, boty operacyjne, D1/SQLite jako audytowalną pamięć, dane providerów oraz docelowo tani/upcyklingowany hardware dla autonomicznych automatyzacji. Projekt 13/KiCad/CERN jest obecnie pilotem pętli `discovery -> staging -> verification -> curation -> human review -> canary/PR`, która ma później zasilać projektowanie i budowę sprzętu z odzyskanych części.

Zasada trwała: **AI/bot może przygotować sugestię, staging, branch albo PR, ale człowiek zatwierdza merge, produkcyjną synchronizację i wszystkie krytyczne decyzje.**

## Odczytane przed pracą

- Handoff wejściowy: `docs/HANDOFF_DLA_NASTEPNEGO_AGENTA_2026-07-06_PO_T4_B3_CURATOR.md`.
- Zlecenie priorytetowe: `docs/AGENTY_PODWYKONAWCZE/ZLECENIE_GLOWNE_B5_BOT_EXECUTION_PACK_INITIATOR.md`.
- Wzorce botów: `cloudflare/src/discord_api_handler.js`, `cloudflare/src/telegram_issues.js`, `cloudflare/src/discord_kicad_actions.js`.
- Wzorce D1/migracji: `cloudflare/src/schema_migrations.js`, `tests/schema_migrations_test.mjs`.

## Co zrobiono w tej turze

### T5 — B5 Bot execution_pack initiator — DONE (canary/review-first)

Dodano wspólną warstwę inicjowania execution packów przez boty Discord/Telegram:

1. `cloudflare/src/execution_pack_initiator.js`:
   - parsuje komendę `!execution-pack start <pack_id> <reviewer>` oraz aliasy `!execution_pack` i `!pack`,
   - waliduje `pack_id` allowlistą znaków i blokuje identyfikatory ścieżkowe,
   - wymaga jawnego reviewera z komendy albo `EXECUTION_PACK_DEFAULT_REVIEWER`,
   - generuje branch `canary/execution-pack/<pack_id>/<timestamp>`,
   - przygotowuje body `CANARY_PILOT_PACKET` z gate: brak merge przez bota, human review required, brak write do `recycled_part_master`,
   - w trybie `EXECUTION_PACK_DRY_RUN=1|true` zwraca bezpieczny testowy URL PR,
   - przy realnym tokenie GitHub tworzy draft PR przez GitHub API, bez sekretów w reply,
   - zapisuje status do D1 tabeli `execution_packs` jako `started`.
2. `cloudflare/src/discord_api_handler.js`:
   - dodano obsługę komend `!execution-pack`, `!execution_pack`, `!pack`.
3. `cloudflare/src/telegram_issues.js`:
   - dodano tę samą obsługę komend dla Telegrama.
4. `cloudflare/src/schema_migrations.js`:
   - dodano tabelę `execution_packs` i indeks `idx_execution_packs_pack_status`.
5. Testy:
   - `tests/execution_pack_initiator_test.mjs` sprawdza parser, D1 write, reviewer gate, blokadę ścieżek, reply i brak SQL dotykającego `recycled_part_master`,
   - `tests/schema_migrations_test.mjs` ma asercje migracji B5.

## Ważne ograniczenia i decyzje

- Bot nadal **nie wykonuje prawdziwego fork/push branch** w Workerze. Worker tworzy D1 record i opcjonalnie draft PR, jeśli operator dostarczy gotowy branch/head oraz token. Realne przygotowanie brancha/forka powinno trafić do osobnego CI/offline joba albo GitHub App flow.
- Brak automatycznego merge. To celowe: `CANARY` i human reviewer są obowiązkowym gate.
- Brak zapisu do `recycled_part_master` z B5. Ta warstwa inicjuje pracę, a nie synchronizuje katalog produkcyjny.

## Testy wykonane

```bash
node --test tests/execution_pack_initiator_test.mjs tests/schema_migrations_test.mjs tests/discord_api_handler_413_and_timing_safe_test.mjs tests/telegram_issues_413_test.mjs
node --test tests/*.mjs
node --check cloudflare/src/execution_pack_initiator.js cloudflare/src/discord_api_handler.js cloudflare/src/telegram_issues.js cloudflare/src/schema_migrations.js
```

Wynik:

- Celowane testy B5 + regresje Discord/Telegram 413: PASS.
- `tests/*.mjs`: 271 PASS.
- `node --check`: PASS.

## Status backlogu po tej turze

### T1/B4 — DONE
Dashboard metryk D1 i komendy `/metrics`.

### T2/B1 — DONE
Scheduled KiCad importer staging + dedup + ingest events.

### T3/B2 — DONE
Deterministyczny verifier schema/dedup/OCR deferred + verify events.

### T4/B3 — DONE
Curator suggest-only KiCad→NSIP + normalizacja heuristic + Z90 ledger.

### T5/B5 — DONE
Bot execution_pack initiator: canary branch/PR proposal, reviewer gate, D1 status, Discord/Telegram commands.

### T6 — NEXT / PRIORYTET 1: Hardening auto-deactivate providera >72h bez heartbeat

Dodać scheduled task oznaczający providera `inactive`, gdy `last_seen_at` jest starsze niż 72h. Kryteria:

- fail-open przy błędzie/braku D1,
- nie dezaktywować zdrowych providerów,
- deactivated/inactive provider nie powinien przyjmować observations/events,
- testy mjs z mock D1,
- dodać event/audit, jeśli istnieje pasujący ledger providerów.

### T7 — PRIORYTET 2: Realny upstream ingestion path dla B1

Worker nie uruchamia Pythona/git. Dodać osobny CI/offline job albo endpoint/queue dla JSONL wygenerowanego przez `pipelines/import_cern_kicad_library.py`, zamiast trzymać większe payloady w env.

### T8 — PRIORYTET 3: B5 follow-up GitHub App/offline branch flow

Rozwinąć obecny B5 z D1/draft PR surface do pełnego operator-safe flow:

- osobny offline/CI runner tworzy branch z `CANARY_PILOT_PACKET`,
- Worker zapisuje request i statusy (`started/closed/merged`),
- webhook GitHub aktualizuje `execution_packs.pr_url/status`,
- test integracyjny rollback: start → PR → close bez merge.

### T9 — Operator/tester

Realny checkout CERN i hardware/proot/BLE pozostają poza agentem bez operatora/sprzętu.

## Pliki kluczowe zmienione

- `cloudflare/src/execution_pack_initiator.js` — nowy moduł B5.
- `cloudflare/src/discord_api_handler.js` — komenda Discord.
- `cloudflare/src/telegram_issues.js` — komenda Telegram.
- `cloudflare/src/schema_migrations.js` — tabela `execution_packs`.
- `tests/execution_pack_initiator_test.mjs` — testy B5.
- `tests/schema_migrations_test.mjs` — asercje migracji B5.

## Commit tej tury

- (ten commit) `feat(bot): T5 B5 execution pack canary initiator`.
