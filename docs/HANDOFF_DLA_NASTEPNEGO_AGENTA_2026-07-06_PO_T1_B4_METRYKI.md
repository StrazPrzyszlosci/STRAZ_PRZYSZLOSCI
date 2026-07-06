# Handoff dla Następnego Agenta - po T1 (B4 metryki D1) - 2026-07-06

## Kontekst z README

Repo NSIP/Straż Przyszłości: AI + tani/upcyklingowany hardware → autonomiczna produkcja żywności, energii i dóbr. Boty jako interfejs operacyjny, D1/SQLite jako pamięć/audyt. Zasada: **AI sugeruje, człowiek zatwierdza zmiany produkcyjne**.

## ZALECENIE TRWAŁE (cyberbezpieczeństwo programistyczne)

Każde kolejne zadanie musi spełniać zasady cyberbezpieczeństwa (zapisane dla wszystkich kolejnych agentów):

1. **Brak injection przez bash interpolation** — payloady, nazwy, tokeny przekazywane przez `python3 - <args> <<'PY'...` (argv), NIE przez string interpolation `'$payload'`.
2. **Biała-lista kluczy env** — `load_env` odczytuje tylko dozwolone klucze (anti-injection via `provider.env`), obcina cudzysłowy.
3. **https-only w prod** — tokeny w plain HTTP = podsłuch; API URL muszą być `https://` w `NSIP_PROVIDER_ENV=prod`.
4. **chmod 0600 plik z sekretem** — `provider.env`, spool files z tokenem w metadata.
5. **chmod 0700 katalog z sekretem** — spool dir, `~/.config/straz-edge/`.
6. **Fail-open po błędzie D1** — błąd limit-tabeli nie odcią providerów (rate limiter allow-all).
7. **AI NIGDY approve** — `kicad_review.js` blokuje `reviewed_by=ai` dla `approved` (Z90, nienaruszalne).
8. **Tokeny rotowalne, ale provider_id niezmienny** — historia audytowalna.
9. **`trust_level >= 2` dla `kind=decision`** — gate przed autonomicznym sterowaniem (S3).
10. **Brak commita sekretów** — `.gitignore` wyklucza provider.env, spool dir, preview artifacts.
11. **Testy cyber** — każdy skrypt z tokenem musi mieć test injection, https-gate, perms, fail-open.

## Co zrobiono (ten agent)

Rozpocząłem od odczytu handoffu `PO_S1_S2_S3_S4_S5` (commit 133a3b4). Zastałem 5 niezcommitowanych plików (3 zmodyfikowane + 2 nieśledzone) będących **częściową realizacją T1 (B4 Dashboard metryk D1)** — pierwszego priorytetu z poprzedniej listy. Dokończyłem T1 w pełni wg kryteriów odbioru z `ZLECENIE_GLOWNE_B4_*.md`.

### T1 — Implementacja B4 (Dashboard metryk D1) — ZAKOŃCZONE

**Zastałem (niezcommitowane od poprzedniego agenta):**
- `cloudflare/src/automation_metrics.js` — `computeAutomationMetrics(env)` obliczająca 5 metryk minimalnych z `kicad_review_events` + `kicad_library_components` (read-only SELECT), `persistAutomationMetricsSnapshot` (rezultat zarezerwowany dla przyszłego harmonogramu), `percentile`, `hoursBetween`, `ensureAutomationMetricsSchema`.
- `cloudflare/src/schema_migrations.js` — 2 migracje idempotentne: `automation_metrics` tabela + `idx_automation_metrics_key_measured`.
- `cloudflare/src/worker.js` — endpoint `GET /v1/metrics` z maintainer-only auth (`X-Trust-Editor-Secret`), read-only.
- `tests/automation_metrics_test.mjs` — 13 testów.
- `tests/schema_migrations_test.mjs` — asercja obecności migracji B4.

**Naprawiłem / dodałem (ten agent):**
1. **Naprawa mock D1** (`tests/automation_metrics_test.mjs`): refaktor z dotychczasowego dispatch tylko przez `.bind().first()` na dispatch zarówno przez bezpośrednie `.first()`/`.all()`/`.run()` jak i przez `.bind(...).first()` — implementacja wołała SELECT bez `.bind()` dla zapytań bezparametrowych. 4 testy przeszły z fail na pass.
2. **Naprawa `assert.closeTo`**: `node:assert/strict` nie ma `closeTo`; zastąpione `assert.ok(Math.abs(...) < 0.1, ...)` zgodnie ze wzorcem z `tests/discord_rate_limiter_load_test.mjs`.
3. **Komendy bota `!metrics` / `/metrics`** (kryterium odbioru B4, którego brakowało):
   - `cloudflare/src/automation_metrics.js` — `formatAutomationMetricsReply(snapshot)` formatujący 5 metryk jako czytelny tekst dashboardu (brak sekretów, fail-open na `null`/`error=no_db`).
   - `cloudflare/src/discord_api_handler.js` — `case "metrics"` → `computeAutomationMetrics` + `formatAutomationMetricsReply`.
   - `cloudflare/src/telegram_issues.js` — `else if (command === "metrics")` w `processCommandMessage` → reply przez `sendTelegramReply`.
4. **3 nowe testy** dla `formatAutomationMetricsReply` (null, error=no_db, pełny snapshot z 5 metrykami + asercja braku wycieku sekretów: PROVIDER_TRUST_EDITOR_SECRET / write_token).

**Cyber:**
- `GET /v1/metrics` maintainer-only (`X-Trust-Editor-Secret`) — nie eksponuje acceptance rates / false-positive dla anonimów (mocniejsze niż minimum "read-only dla agentów" z B4).
- `computeAutomationMetrics` 100% read-only (SELECT), brak AI, deterministyczna.
- `persistAutomationMetricsSnapshot` (INSERT) NIE jest podpięta z endpointu ani komendy — wyłącznie zarezerwowana dla przyszłego harmonogramu (T2/T7). Komenda `/metrics` i endpoint są turowo read-only wg "metryki nie write przez agentów".
- Błędy poszczególnych metryk łapane osobno (fail-open per-metric) — błąd jednej metryki nie odcią pozostałych.
- `bash -n nsip-client.sh` PASS (brak regresji w cyber-hardeningu edge).

### Status wcześniejszych zadań (z poprzedniego handoff)

- **S1 (realny checkout CERN)** — ODOCZONE dla operatora (nieblokujące).
- **S2/S2-B/S3/S4/S5** — DONE (poprzedni agent, commity 309ec98/42b6618/b8c224a/cb99701).
- **S6 (testy hardware)** — ODOCZONE dla testera.
- **T1 (B4)** — DONE (ten agent).
- **T2-T9** — OPEN (patrz poniższa nowa lista).

## Testy wykonane

```bash
node --test tests/*.mjs                                            # 247 PASS (0 fail) — +17 vs 230 (T1)
node --test tests/automation_metrics_test.mjs                     # 16 PASS (13 + 3reply)
python3 -m unittest tests.test_cern_kicad_importer                # 5 PASS
node --check cloudflare/src/{automation_metrics,worker,discord_api_handler,telegram_issues}.js  # SYNTAX OK
bash -n straz-edge-installer/scripts/nsip-client.sh               # PASS (no warnings)
```

## Nowa lista zadań dla następnego agenta

> Kolejność = priorytety Roadmapy H2 (B1→B2→B3→B5), po nich hardening (T7) i infra (T6). T8/T9 są poza agentem (operator/tester).

### T1 — Implementacja B1 (Importer agent harmonogramowany) — PRIORYTET 1
Pierwsze w kolejności (B4 już gotowy jako health-check). Cron/scheduled task w `cloudflare/src/worker.js` (`scheduled()` handler) uruchamia `pipelines/import_cern_kicad_library.py` z `dedup` checksum (hash `source_slug + upstream_commit + symbol_name + footprint_name + mpn`). Write tylko do `kicad_library_components` z statusem `staged`. Event per ingest (`/v1/events`, `kind=ingest`). Cyber: read-only upstream, brak zapisu do `recycled_part_master`. Po zakończeniu ingest → opcjonalnie wywołać `persistAutomationMetricsSnapshot` (T1 z poprzedniej listy udostępnia tę funkcję, ale mechanizm triggera harmonicogramu jest do zaprojektowania). Patrz `ZLECENIE_GLOWNE_B1_*.md`.

### T2 — Implementacja B2 (Verifier agent) — PRIORYTET 2
Po B1. Schema-diff, dedup, OCR deferred (`needs_more_data`). KAŻDE przejście statusu → event. Deterministyczny (zero AI, zero false-positive). Cyber: NIE pisze do `recycled_part_master`. Testy mjs z mock D1 (wzorzec z `automation_metrics_test.mjs`). Patrz `ZLECENIE_GLOWNE_B2_*.md`.

### T3 — Implementacja B3 (Curator AI normalizacja) — PRIORYTET 3
Po B2. AI sugeruje dopasowanie KiCad→NSIP jako `suggested` w `recycled_part_kicad_links` (Z90). Cyber: AI NIGDY `approved` (wymuszczone w `kicad_review.js`, `reviewed_by=ai` zablokowane — zasada nienaruszalna #7). `recycled_part_master` NIE nadpisany przez curatora. Test integracyjny curator→maintainer approve. Patrz `ZLECENIE_GLOWNE_B3_*.md`.

### T4 — Implementacja B5 (Bot execution_pack initiator) — PRIORYTET 4
Po B1-B3 (potrzebuje metryk z B4 + ingest z B1 + verify z B2 + curator z B3). `!execution-pack start <id>` → fork → PR (CANARY) → reviewer wyznaczony. Cyber: bot NIE merge do main bez human review, NIE pisze do `recycled_part_master` (Z91). PR/repo branch protection. Test integracyjny. Patrz `ZLECENIE_GLOWNE_B5_*.md`.

### T5 — Auto-deactivate providera >72h bez heartbeat (z C) — PRIORYTET 5
`heartbeat` aktualizuje `last_seen_at`, ale auto-deactivate po >72h nie zaimplementowane. Dodatkowy `scheduled()` task w `worker.js` oznaczający `provider_status='inactive'` gdy `last_seen_at` < now-72h. Test mjs (mock D1 z `last_seen_at` w przeszłości). Cyber: deactivated provider NIE przyjmuje observations/events (rate-limit + auth check w `worker.js`). Wykorzystać ten sam pattern `else if` w routerze co inne gate'y (np. `trust_level` gate). Patrz `HANDOFF_..._PO_S1_S2_S3_S4_S5.md` sekcja T7.

### T6 — E (WebSocket events stream dla węzłów edge) — OPEN, dla H3
`/v1/ws/events?provider_id=<id>` — push z centrali do węzłów (rekomendacje, alarmy), bez polling. Wskazane w H3 (węzły jako providery). Cyber: uwierzytelnienie przez `write_token` (rotate), TLS websocket, rate-limit dziedziczy z S2-A. Po gate H2 z Portfela 25.

### T7 — Realny checkout CERN dla Z93 (operator) — ODOCZONE
Klon `https://gitlab.com/ohwr/cern-kicad-libs` poza working copy, re-run importera z `--source` i realnym SHA CERN, wypełnij checklist z `Z93_FIXTURE_SMOKE_REPORT_2026-07-05.md`. Promuje Z93 PARTIAL → DONE. Nieblokujące.

### T8 — Testy hardware proot installer + BLE (agent tester) — ODOCZONE
`ODBIOR_PROOT_EDGE_INSTALLER_2026-07-05.md` (10-punktowa checklist) + BLE test (`gpio-ble <mac> ffe1 12 1`). Wymaga 2 telefonów (Qualcomm + MediaTek) + ESP32 + FT232R.

## Pliki kluczowe (nowe w tej turze)

- `cloudflare/src/automation_metrics.js` — `computeAutomationMetrics` (5 metryk read-only), `persistAutomationMetricsSnapshot`, `formatAutomationMetricsReply`, migracja IF NOT EXISTS, percentile/hoursBetween.
- `cloudflare/src/worker.js:564` — `GET /v1/metrics` (maintainer-only `X-Trust-Editor-Secret`, read-only snapshot).
- `cloudflare/src/schema_migrations.js:212` — migracje `20260706000001-automation-metrics` + `20260706000002-automation-metrics-index`.
- `cloudflare/src/discord_api_handler.js:265` — `case "metrics"` → `formatAutomationMetricsReply`.
- `cloudflare/src/telegram_issues.js:1612` — `else if (command === "metrics")` → `sendTelegramReply(formatAutomationMetricsReply)`.

## Pliki kluczowe (dziedziczone)

- `cloudflare/src/kicad_review.js` (Z90), `ecoeda_export.js` (Z91), `discord_kicad_actions.js` (Z94), `kicad_lookup.js` (Z89).
- `cloudflare/src/schema_migrations.js` (Z88 + gpio_pin_map_json Q8 + automation_metrics T1).
- `cloudflare/src/provider_rate_limiter.js` (S2-A), `cloudflare/src/security_headers.js` (S2-C/S3).
- `straz-edge-installer/scripts/nsip-client.sh` (S2-B offline bufor + cyber hardening).
- `pipelines/import_cern_kicad_library.py` (S4 / Z87 rozszerzenia parsera).
- `docs/ROADMAPA_AUTONOMICZNEJ_AUTOMATYZACJI_AI.md` (Z95), `docs/KICAD_VERSION_CONVERSION_EXPORT_POLICY.md` (Z92).
- `docs/AGENTY_PODWYKONAWCZE/PORTFEL_25_ZLECEN_DLA_PODWYKONAWCOW_2026-07-05.md` — portfel H2 (B1-B5).
- `docs/AGENTY_PODWYKONAWCZE/Z93_FIXTURE_SMOKE_REPORT_2026-07-05.md` — fixture smoke (R1).

## Priorytety

1. **T1 → T2 → T3 → T4** — realizacja Portfela 25 (H2 roadmapa) w kolejności B1→B2→B3→B5. Główny backlog. B4 (Dashboard metryk) ZAKOŃCZONE.
2. **T5** — auto-deactivate providera (hardening C).
3. **T6** — WebSocket stream (dla H3, po gate H2).
4. **T7** — realny CERN (operator, nieblokujące).
5. **T8** — testy hardware (tester, nieblokujące).

## Commit'y (ta tura)

- (ten commit) feat(metrics): T1 B4 — automation_metrics (compute+persist+reply), migracja D1, `GET /v1/metrics`, komendy `/metrics` (Discord + Telegram), 16 testów.
  - + docs: handoff PO_T1_B4_METRYKI z nowa lista T1-T8.

## Odniesienia

- `docs/HANDOFF_DLA_NASTEPNEGO_AGENTA_2026-07-05_PO_S1_S2_S3_S4_S5.md` — poprzedni handoff (T1-T9, ten agent zrealizował T1).
- `docs/HANDOFF_DLA_NASTEPNEGO_AGENTA_2026-07-05_PO_R1_R5_R7_R8.md` — jeszcze wcześniejszy (S1-S6 zrealizowane w tamtej turze).
- `docs/AGENTY_PODWYKONAWCZE/ZLECENIE_GLOWNE_B4_D1_AUTOMATION_METRICS_DASHBOARD.md` — zlecenie B4 (ZAKOŃCZONE).

## Uwagi

- Status **247 testów mjs + 5 python** — bez regresji (wzrost z 230 → +17 dla T1).
- `bash -n nsip-client.sh` PASS (bez ostrzeżeń, cyber hardening edge nienaruszony).
- T1 wcześniejszej listy = B4. W tej turze numeracja zmienia się na T1=B1, T2=B2, T3=B3, T4=B5, T5=auto-deactivate, T6=WebSocket, T7=CERN (operator), T8=hardware (tester) — żeby nie mieszać starych oznaczeń "S".
- Portfel 24 ZAMKNIĘTY. Portfel 25 OPEN — B4 ZAKOŃCZONE, B1-B3 + B5 pozostają (T1-T4 tej listy).
- `persistAutomationMetricsSnapshot` udostępniona ale **nie podpięta** — T1 (B1) następnego agenta powinno rozważyć trigger z harmonygogramu (np. po ingest write-write do `automation_metrics` jako historyczny snapshot). Nie jest to obowiązkowe dla B1 (B2 będzie korzystać z metryk live).
- Cyberbezpieczeństwo: patrz sekcja ZALECENIE TRWAŁE na górze — dotyczy wszystkich kolejnych agentów.
- `.kilo/` pozostaje w `.gitignore`.
