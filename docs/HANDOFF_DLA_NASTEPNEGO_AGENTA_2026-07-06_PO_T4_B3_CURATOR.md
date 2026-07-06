# Handoff dla Następnego Agenta - po T4 (B3 curator sugestii KiCad→NSIP) - 2026-07-06

## Kontekst

Repo NSIP/Straż Przyszłości rozwija suwerenne, open-source automatyzacje AI + tani/upcyklingowany hardware. Projekt 13/KiCad/CERN służy jako baza do przyszłego projektowania hardware z części odzyskanych z elektrośmieci. Zasada trwała: **AI sugeruje, człowiek zatwierdza zmiany produkcyjne**.

## Odczytane przed pracą

- Handoff wejściowy: `docs/HANDOFF_DLA_NASTEPNEGO_AGENTA_2026-07-06_PO_T3_B2_VERIFIER.md`.
- Zlecenie priorytetowe: `docs/AGENTY_PODWYKONAWCZE/ZLECENIE_GLOWNE_B3_CURATOR_AI_NORMALIZATION.md`.
- Istniejący gate Z90: `cloudflare/src/kicad_review.js` (`suggestKicadLink`, blokada approve przez `reviewed_by=ai`).

## ZALECENIE TRWAŁE (cyberbezpieczeństwo)

1. AI może tworzyć tylko sugestie; approve/merge wymaga człowieka.
2. Nie pisać do `recycled_part_master` z poziomu importer/verifier/curator.
3. Nie wkładać sekretów do repo/env testów; payloady przekazywać jako JSON/argv.
4. Zachować fail-open dla brakującego DB tam, gdzie brak DB nie może zablokować providerów.
5. Utrzymywać event ledger dla każdego kroku automatyzacji.

## Co zrobiono w tej turze

### T4 — B3 Curator AI normalizacja — DONE (suggest-only)

Dodano cienką warstwę curatora nad Z90:

1. `cloudflare/src/kicad_curator.js`:
   - `runKicadCurator(env)` ładuje tylko rekordy `kicad_library_components.import_status='verified'`.
   - `curateKicadComponent(env, component)` szuka kandydata w `recycled_part_master` po `normalized_part_number`/`part_number`.
   - Tworzy wyłącznie link `review_status='suggested'` przez `suggestKicadLink`; nie wykonuje żadnych `UPDATE recycled_part_master`.
   - Buduje deterministyczną sugestię normalizacji: `package -> species`, `footprint library -> genus`, footprint/package -> `mounting` (`smd`/`tht`/`unknown`).
   - Powód sugestii jest JSON-em z policy `suggest_only_human_review_required` i normalizacją.
   - Idempotencja: ponowna sugestia tego samego master/component nie tworzy drugiego linku, tylko event duplicate_suggestion w ledgerze Z90.
2. `cloudflare/src/worker.js`:
   - scheduled pipeline działa teraz: B1 ingest → B2 verify → B3 curate i zwraca `{ ingest, verify, curate }`.
3. Testy:
   - `tests/kicad_curator_test.mjs` pokrywa: suggest-only, skip non-verified, skip bez master candidate, idempotencję duplicate suggestion, blokadę AI approve + human approve, deterministyczne normalizacje.

## Status backlogu po tej turze

### T1/B4 — DONE
Dashboard metryk D1 i komendy `/metrics`.

### T2/B1 — DONE
Scheduled KiCad importer staging + dedup + ingest events.

### T3/B2 — DONE
Deterministyczny verifier schema/dedup/OCR deferred + verify events.

### T4/B3 — DONE
Curator suggest-only KiCad→NSIP + normalizacja heuristic + Z90 ledger.

### T5/B5 — NEXT / PRIORYTET 1
Bot execution_pack initiator:
- `!execution-pack start <id>` → branch/PR CANARY/reviewer.
- Bot nie merge do main i nie pisze do `recycled_part_master`.
- Wykorzystać istniejące wzorce komend Discord/Telegram oraz gate maintenera.
- Zlecenie: `docs/AGENTY_PODWYKONAWCZE/ZLECENIE_GLOWNE_B5_BOT_EXECUTION_PACK_INITIATOR.md`.

### T6 — Hardening auto-deactivate providera >72h bez heartbeat — PRIORYTET 2
Dodać scheduled task oznaczający providera `inactive`, gdy `last_seen_at` jest starsze niż 72h. Testy mock D1. Uwaga: nie odcinać zdrowych providerów przez błędy D1.

### T7 — Poprawka B1 realnego upstream ingestion path — PRIORYTET 3
Worker nadal nie uruchamia Pythona/git. Dodać osobny CI/offline job albo endpoint/queue dla JSONL wygenerowanego przez `pipelines/import_cern_kicad_library.py`, zamiast większych payloadów w env.

### T8/T9 — Operator/tester
Realny checkout CERN i hardware/proot/BLE pozostają poza agentem bez operatora/sprzętu.

## Testy wykonane

```bash
node --test tests/kicad_curator_test.mjs tests/kicad_verifier_test.mjs tests/scheduled_kicad_importer_test.mjs tests/schema_migrations_test.mjs
node --check cloudflare/src/kicad_curator.js cloudflare/src/kicad_verifier.js cloudflare/src/scheduled_kicad_importer.js cloudflare/src/worker.js
node --test tests/*.mjs
python3 -m unittest tests.test_cern_kicad_importer
```

Wynik:
- `tests/*.mjs`: 265 PASS.
- `tests.test_cern_kicad_importer`: 5 PASS.

## Pliki kluczowe zmienione

- `cloudflare/src/kicad_curator.js` — B3 curator suggest-only.
- `cloudflare/src/worker.js` — scheduled pipeline B1 → B2 → B3.
- `tests/kicad_curator_test.mjs` — testy B3.

## Commit tej tury

- (ten commit) `feat(curator): T4 B3 KiCad suggest-only normalizer`.
