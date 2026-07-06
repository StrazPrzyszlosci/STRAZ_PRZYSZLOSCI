# Handoff dla Następnego Agenta - po T3 (B2 deterministyczny verifier KiCad) - 2026-07-06

## Kontekst repo i cel strategiczny

Repo NSIP/Straż Przyszłości buduje open-source, niskokosztowe automatyzacje oparte o AI, tanie/upcyklingowane hardware i suwerenną bazę danych. Projekt 13/KiCad/CERN jest jednym z fundamentów dla przyszłego projektowania hardware z części odzyskanych z elektrośmieci. Zasada trwała: **AI sugeruje, człowiek zatwierdza zmiany produkcyjne**.

## Odczytane przed pracą

- `README.md` — cele repo: AI + tani hardware, automatyzacja dla wspólnego dobra, suwerenność danych, Projekt 13 jako baza części z recyklingu i docelowy fundament projektowania hardware.
- Ostatnie commity: `92bd764` (B1 scheduled importer), `bd27366` (B4 metryki), `133a3b4` (handoff S1-S5/T1-T9).
- Handoff wejściowy: `docs/HANDOFF_DLA_NASTEPNEGO_AGENTA_2026-07-06_PO_T2_B1_IMPORTER.md`.
- Zlecenie priorytetowe: `docs/AGENTY_PODWYKONAWCZE/ZLECENIE_GLOWNE_B2_VERIFIER_AGENT_SCHEMA_DEDUP_OCR.md`.

## ZALECENIE TRWAŁE (cyberbezpieczeństwo)

1. Brak injection przez bash interpolation; payloady przez argv/JSON.
2. Brak sekretów w repo, biała-lista env, HTTPS-only w prod.
3. AI NIGDY `approved`; `reviewed_by=ai` dla approve pozostaje blokowane.
4. `trust_level >= 2` dla `kind=decision`.
5. D1/rate-limit fail-open tam, gdzie brak DB nie może odciąć providerów.
6. Tokeny rotowalne, provider_id stały.
7. Skrypty z tokenami muszą mieć testy cyber; verifier B2 nie korzysta z tokenów ani AI.

## Co zrobiono w tej turze

### T3 — B2 Verifier agent deterministyczny — DONE

Dodano deterministyczny verifier dla rekordów `kicad_library_components` w statusie `staged`:

1. Nowy moduł `cloudflare/src/kicad_verifier.js`:
   - `runKicadVerifier(env)` ładuje batch `staged` i procesuje wszystkie rekordy.
   - `verifyKicadComponent(env, row)` ustawia status: `verified`, `needs_more_data`, `duplicate`, `needs_ocr`.
   - Schema-diff sprawdza wymagane pola: `symbol_name` lub `footprint_name`, `mpn` lub `normalized_part_number`, `license_spdx`, `upstream_commit`, opcjonalnie `schema_version='v1'`.
   - Dedup sprawdza `normalized_part_number + upstream_commit` w staging.
   - OCR deferred: wykrywa skan PDF deterministycznie z `datasheet_url` + `raw_metadata_json` i kolejkuje do `kicad_ocr_queue` bez blokowania pętli.
   - Każde przejście statusu zapisuje event `kind='verify'` w `kicad_library_events`.
   - Brak AI, brak zapisu do `recycled_part_master`, brak zapisu do `recycled_part_kicad_links`.
2. `cloudflare/src/worker.js`:
   - scheduled cron po B1 ingest uruchamia B2 verifier i zwraca `{ ingest, verify }`.
3. `cloudflare/src/schema_migrations.js`:
   - dodano `verify_note`, `verified_at` do `kicad_library_components`.
   - rozszerzono `kicad_library_events` o `component_id`, `previous_status`, `next_status`, `reason`.
   - dodano `kicad_ocr_queue` + indeks `idx_kicad_ocr_queue_status_created`.
4. Testy:
   - `tests/kicad_verifier_test.mjs` pokrywa `verified`, `needs_more_data`, `duplicate`, `needs_ocr`, eventy, OCR queue, fail-open bez DB i deterministic internals.
   - `tests/schema_migrations_test.mjs` rozszerzony o migracje B2.

## Status backlogu po tej turze

### T1/B4 — DONE
Dashboard metryk D1 i komendy `/metrics`.

### T2/B1 — DONE
Scheduled KiCad importer staging + dedup + ingest events.

### T3/B2 — DONE
Deterministyczny verifier schema/dedup/OCR deferred + verify events.

### T4/B3 — NEXT / PRIORYTET 1
Curator AI normalizacja:
- AI może tylko sugerować dopasowanie KiCad→NSIP jako `suggested` w `recycled_part_kicad_links`.
- AI nigdy `approved`; approve tylko człowiek/maintainer.
- Nie nadpisywać `recycled_part_master`.
- Używać tylko rekordów `verified`, ignorować `needs_more_data`, `needs_ocr`, `duplicate`.
- Test integracyjny: curator suggestion → maintainer approve przez istniejące gate'y Z90.
- Zlecenie: `docs/AGENTY_PODWYKONAWCZE/ZLECENIE_GLOWNE_B3_CURATOR_AI_NORMALIZATION.md`.

### T5/B5 — PRIORYTET 2
Bot execution_pack initiator:
- `!execution-pack start <id>` → branch/PR CANARY/reviewer.
- Bot nie merge do main i nie pisze do `recycled_part_master`.

### T6 — Hardening auto-deactivate providera >72h bez heartbeat
OPEN. Można zrobić równolegle po B3 albo przed B5.

### T7 — Poprawka B1 realnego upstream ingestion path
Komentarz architektoniczny z poprzedniego PR pozostaje ważny: Worker nie uruchamia Pythona/git. Dla pełnego B1 warto dodać osobny CI/offline job albo endpoint/queue dla JSONL wygenerowanego przez `pipelines/import_cern_kicad_library.py`, zamiast trzymać większe dane w env.

### T8/T9 — Operator/tester
Realny checkout CERN i hardware/proot/BLE pozostają poza agentem bez operatora/sprzętu.

## Testy wykonane

```bash
node --test tests/kicad_verifier_test.mjs tests/scheduled_kicad_importer_test.mjs tests/schema_migrations_test.mjs
node --check cloudflare/src/kicad_verifier.js cloudflare/src/scheduled_kicad_importer.js cloudflare/src/worker.js
node --test tests/*.mjs
python3 -m unittest tests.test_cern_kicad_importer
```

Wynik:
- `tests/*.mjs`: 259 PASS.
- `tests.test_cern_kicad_importer`: 5 PASS.

## Pliki kluczowe zmienione

- `cloudflare/src/kicad_verifier.js` — nowy verifier B2.
- `cloudflare/src/worker.js` — scheduled pipeline B1 ingest → B2 verify.
- `cloudflare/src/schema_migrations.js` — migracje B2 status/event/OCR queue.
- `tests/kicad_verifier_test.mjs` — testy B2.
- `tests/schema_migrations_test.mjs` — asercje migracji B2.

## Commit tej tury

- (ten commit) `feat(verifier): T3 B2 deterministic KiCad verifier`.
