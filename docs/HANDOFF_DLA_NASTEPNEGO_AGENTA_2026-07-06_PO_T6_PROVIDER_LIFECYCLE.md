# Handoff dla Następnego Agenta - po T6 (provider lifecycle auto-deactivate) - 2026-07-06

## Kontekst inicjatywy

Straż Przyszłości / NSIP to wielowarstwowe repo inicjatywy, nie pojedynczy projekt. Aktualny kod łączy:

- onboardingi i boty dla ludzi oraz operatorów,
- API providerów danych i edge-node lifecycle,
- Project 13 jako pilot odzysku części i pętli KiCad/CERN → staging → verifier → curator → human review,
- dokumenty strategiczne dla automatyzacji, sprzętu z elektrośmieci, mesh/LoRa, smartfonów jako edge compute, CAD/PCB i kolejnych projektów fizycznych,
- pamięć organizacji w D1/SQLite, raportach, handoffach i execution packach.

Zasada trwała: automaty i AI przygotowują staging/sugestie/statusy, ale człowiek zatwierdza merge, approve, deployment i działania w świecie fizycznym.

## Odczytane przed pracą

- Handoff wejściowy: `docs/HANDOFF_DLA_NASTEPNEGO_AGENTA_2026-07-06_PO_T5_B5_EXECUTION_PACK_BOT.md`.
- Priorytet z handoffu: T6 — auto-deactivate providera po >72h bez heartbeat.
- Kluczowy kod: `cloudflare/src/worker.js`, `tests/provider_rate_limiter_test.mjs`, `tests/provider_trust_level_test.mjs`, `cloudflare/src/schema_migrations.js`.

## Co zrobiono w tej turze

### T6 — Provider lifecycle auto-deactivate — DONE

Dodano lifecycle hardening dla providerów danych / edge node:

1. `cloudflare/src/worker.js`:
   - dodano `provider_status` jako runtime-compatible kolumnę obok `trust_level`,
   - dodano `provider_lifecycle_events` jako audyt zmian statusu,
   - dodano `autoDeactivateInactiveProviders(env, options)`, który oznacza jako `inactive` providerów z `last_seen_at` starszym niż 72h,
   - scheduled cron Workera uruchamia teraz provider lifecycle przed B1/B2/B3 pipeline,
   - `requireProviderToken` blokuje inactive providerów dla observations/events/recommendations,
   - heartbeat i token rotation mogą przejść z `allowInactive: true`, żeby provider mógł wrócić przez heartbeat/rotację zamiast trwale utknąć,
   - `updateProviderSeen` ustawia `provider_status='active'`, więc heartbeat/udany ingest reaktywuje providera,
   - endpoint statusu providera zwraca teraz realny `provider_status` zamiast zawsze `ok`.
2. `tests/provider_lifecycle_test.mjs`:
   - pokrywa auto-deactivate tylko starych aktywnych providerów,
   - potwierdza event lifecycle,
   - potwierdza fail-open przy braku D1 i błędzie D1,
   - potwierdza semantykę `isProviderActive`.

## Testy wykonane

```bash
node --test tests/provider_lifecycle_test.mjs tests/provider_trust_level_test.mjs tests/provider_rate_limiter_test.mjs tests/schema_migrations_test.mjs
node --test tests/*.mjs
node --check cloudflare/src/worker.js
python3 -m unittest discover -s tests -p 'test_*.py'
```

Wynik:

- Targeted Node tests: PASS.
- `node --test tests/*.mjs`: 276 PASS.
- `node --check cloudflare/src/worker.js`: PASS.
- Python unittest discover: FAIL na istniejących regresjach niezwiązanych z T6:
  - `test_cloudflare_ai_node_suite.CloudflareAiNodeSuite.test_node_suite` → `cloudflare/tests/telegram_ai.test.mjs` ma 2 failing assertions dotyczące donor-device text (`Arduino Compatible Uno Clone`),
  - `test_curation_pipeline_regression_z51.TestReviewQueueConsistency.test_pending_list_matches_queue` → mismatch pending queue/list.

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
Bot execution_pack initiator: CANARY proposal, reviewer gate, D1 status, Discord/Telegram commands.

### T6 — DONE
Provider lifecycle auto-deactivate po >72h bez heartbeat + inactive gate dla ingest endpoints.

### T7 — NEXT / PRIORYTET 1: Naprawić istniejące Python/Telegram regresje

Najpierw naprawić czerwony `python3 -m unittest discover -s tests -p 'test_*.py'`, bo to blokuje uczciwy status całego repo:

- `cloudflare/tests/telegram_ai.test.mjs` oczekuje donor-device text dla części `ATMEGA328P-PU`; obecny reply pokazuje licznik znalezionych urządzeń, ale nie wypisuje nazwy donora.
- `test_curation_pipeline_regression_z51.py` ma mismatch między pending queue i list-pending IDs.

### T8 — PRIORYTET 2: Realny upstream ingestion path dla B1

Worker nie uruchamia Pythona/git. Dodać CI/offline job albo endpoint/queue dla JSONL wygenerowanego przez `pipelines/import_cern_kicad_library.py`.

### T9 — PRIORYTET 3: B5 follow-up GitHub App/offline branch flow

Rozwinąć B5 z D1/draft PR surface do pełnego operator-safe flow: offline/CI branch creation, GitHub webhook status updates `started/closed/merged`, test rollback start → PR → close bez merge.

### T10 — PRIORYTET 4: WebSocket/events stream dla edge H3

Po stabilizacji H2 dodać `/v1/ws/events?provider_id=<id>` albo alternatywny queue/polling-safe stream dla rekomendacji/alarmów do węzłów edge.

## Pliki kluczowe zmienione

- `cloudflare/src/worker.js` — provider lifecycle, inactive gate, scheduled auto-deactivate.
- `tests/provider_lifecycle_test.mjs` — testy T6.
- `docs/HANDOFF_DLA_NASTEPNEGO_AGENTA_2026-07-06_PO_T6_PROVIDER_LIFECYCLE.md` — ten handoff.

## Commit tej tury

- (ten commit) `feat(provider): T6 auto-deactivate inactive providers`.
