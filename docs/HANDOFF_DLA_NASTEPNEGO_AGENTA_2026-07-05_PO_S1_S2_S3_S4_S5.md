# Handoff dla Następnego Agenta - po S1(nt) S2 S3 S4 S5 - 2026-07-05

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
10. **Brak commita sekretów** — `.gitignore` wyklucza prote.env, spool dir, preview artifacts.
11. **Testy cyber** — każdy skrypt z tokenem musi mieć test injection, https-gate, perms, fail-open.

## Co zrobiono (ten agent)

Rozpocząłem od odczytu handoffu `PO_R1_R5_R7_R8` (commit 5d992f1). Wykonałem zadania S1-S6 z priorytetem kod (bez hardware): S2 (rate limit + heartbeat), S2-B (offline bufor + cyber hardening), S3 (trust_level + decision gate), S4 (rozszerzenia parsera Z87), S5 (zlecenia B1-B5), aktualizację API spec. S1 (realny CERN) i S6 (hardware) pozostają dla operatora/testera.

### S2 — Hardening API providerów edge (A/B/C, commit 309ec98)
- `cloudflare/src/provider_rate_limiter.js` — token bucket per `provider_id` (PROVIDER_MAX_RPM default 30, fail-open, disabled when ≤0). 8 testów PASS.
- `cloudflare/src/worker.js`:
  - Rate-limit check w `/v1/observations`, `/v1/events`, `/v1/providers/<id>/heartbeat` → `429` + `Retry-After`.
  - `POST /v1/providers/<id>/heartbeat` — updateProviderSeen + `trust_level` echo.
  - `PATCH /v1/providers/<id>/trust-level` — `X-Trust-Editor-Secret` maintainer-only, `validateTrustLevel` 0-10.
  - `kind=decision` events gate: `trust_level >= PROVIDER_DECISION_TRUST_LEVEL` (default 2) → `403`.
  - `validateEvent` akceptuje pole `kind` (default `telemetry`).
  - `ensureProviderTrustLevelColumn`: `ALTER TABLE providers ADD COLUMN trust_level INTEGER NOT NULL DEFAULT 0`.
- `cloudflare/src/security_headers.js`: `PATCH` w allow-methods, `x-trust-editor-secret` w allow-headers, `jsonResponse` `extraHeaders` (Retry-After).
- `tests/provider_trust_level_test.mjs` — 8 testów helperów (validateTrustLevel, getProviderTrustLevel, decision gate).
- `tests/worker_security_headers_test.mjs` — aktualizacja PATCH + nowe testy (extraHeaders, allow-headers).
- 230 testów mjs PASS.

### S2-B — Offline bufor + cyber hardening (commit 42b6618)
- `straz-edge-installer/scripts/nsip-client.sh`:
  - `post_or_spool` — błąd sieci (NETERR) → spool do `${SPOOL_DIR}/*.jsonl` (chmod 0600, dir 0700). Błąd HTTP (HTTPERR 4xx/5xx) → no spool.
  - `try_post` — python rozróżnia SENT/HTTPERR/NETERR przez exit code (0/1/2).
  - `flush` — exponential backoff (2^(n-1)s, max 16s), drop po `SPOOL_MAX_RETRIES`.
  - `heartbeat [interval]` (min 5s) — pętla flush + POST heartbeat.
  - `load_env`/`load_env_partial` — biała-lista kluczy + obcinanie cudzysłowów (anti-injection).
  - **prod wymaga https://** (token w plain HTTP = podsłuch).
  - `register`/`observe`/`event` — python argv (anti-apostrof injection).
  - `rotate` — python regex (anti-sed-injection).
  - `status` — python urllib + Bearer.
  - Fix bash gotcha `if cmd; then fi` zeruje `$?` (rc capture poza `if`).
- 8 cyber-testów PASS (prod https-gate, NETERR spool, spool perm 0600, HTTPERR no-spool, injection, help).

### S3 — Trust level dla providerów (commit 309ec98 — wspólnie z S2)
- Patrz S2 — migracja `trust_level` w `schema_migrations.js?` (dynamicznie przez `ensureProviderTrustLevelColumn` w `worker.js`), `PATCH /v1/providers/<id>/trust-level`, gate `kind=decision`.

### S4 — Rozszerzenia parsera Z87 (commit b8c224a)
- `pipelines/import_cern_kicad_library.py`:
  - MPN fallback chain: `MPN > Manufacturer Part Number > MPN_Alt > Substitution`.
  - `raw_metadata_json` zawiera `ki_fp_filters`, `dnp`, `exclude_from_sim`, `mpn_alt`, `substitution`.
  - `package` preferuje jawne `Package` property, fallback `ki_fp_filters`.
  - `.pretty` dirs rekurencja: `rglob(*.kicad_mod)` łapie `.pretty/*.kicad_mod` (potwierdzone).
- `tests/test_cern_kicad_importer.py`: nowy test `test_iter_components_uses_mpn_alt_fallback`, asercje `ki_fp_filters`/`dnp`/`exclude_from_sim`.
- 230 mjs PASS + 5 python PASS.

### S5 — Zlecenia B1-B5 + aktualizacja API spec (commit cb99701)
- `ZLECENIE_GLOWNE_B1_IMPORTER_AGENT_SCHEDULED.md` — cron pull + dedup checksum + staging.
- `ZLECENIE_GLOWNE_B2_VERIFIER_AGENT_SCHEMA_DEDUP_OCR.md` — schema-diff + dedup + OCR deferred.
- `ZLECENIE_GLOWNE_B3_CURATOR_AI_NORMALIZATION.md` — sugestie `suggested`, zero zapisów do master.
- `ZLECENIE_GLOWNE_B4_D1_AUTOMATION_METRICS_DASHBOARD.md` — `automation_metrics` + 5 metryk minimalnych.
- `ZLECENIE_GLOWNE_B5_BOT_EXECUTION_PACK_INITIATOR.md` — fork-first PR-first review-first (CANARY).
- `ZLECENIE_GLOWNE_WEZLY_EDGE_PROVIDER_API.md` — rozszerzenia A/B/C/D oznaczone DONE (commits refs), E OPEN.

### S1 — Realny checkout CERN (ODROCZONE — operator)
Wymaga klonu CERN KiCad Library lokalnie. Fixture smoke PARTIAL PASS (portfel 4 Z93). Nie blokuje innych zadań.

### S6 — Testy hardware (ODROCZONE — tester)
Wymaga 2 telefonów (Qualcomm + MediaTek) + ESP32 + FT232R. Szablon odbioru `ODBIOR_PROOT_EDGE_INSTALLER_2026-07-05.md` gotowy. BLE test w `PROJEKTY/07_.../esp32_gpio_endpoint/`.

## Testy wykonane

```bash
node --test tests/*.mjs      # 230 PASS (0 fail)
python3 -m unittest tests.test_cern_kicad_importer   # 5 PASS
bash -n straz-edge-installer/scripts/nsip-client.sh  # PASS (no warnings)
bash /tmp/kilo/nsip-cyber-test.sh                    # 8 PASS (cyber hardening)
```

## Nowa lista zadań dla następnego agenta

### T1 — Implementacja B4 (Dashboard metryk D1) — PRIORYTET 1
Pierwsze w kolejności (wymagane przez B1/B5 jako health-check). Migracja `automation_metrics` + `compute_automation_metrics(env)` + endpoint `GET /v1/metrics` + komenda bota `!metrics`. Patrz `ZLECENIE_GLOWNE_B4_*.md`. Cyber: metryki read-only dla agentów, mierzone z `kicad_review_events` (nienadpisywane). Testy mjs z mock D1.

### T2 — Implementacja B1 (Importer agent harmonogramowany) — PRIORYTET 2
Po B4. Cron/schedule uruchamia `pipelines/import_cern_kicad_library.py` z `dedup` checksum (hash `source_slug + upstream_commit + symbol_name + footprint_name + mpn`). Write tylko do `kicad_library_components` z statusem `staged`. Event per ingest. Cyber: read-only upstream, brak zapisu do `recycled_part_master`. Patrz `ZLECENIE_GLOWNE_B1_*.md`.

### T3 — Implementacja B2 (Verifier agent) — PRIORYTET 3
Po B1. Schema-diff, dedup, OCR deferred (`needs_more_data`). KAŻDE przejście statusu → event. Deterministyczny (zero AI, zero false-positive). Cyber: NIE pisze do `recycled_part_master`. Testy. Patrz `ZLECENIE_GLOWNE_B2_*.md`.

### T4 — Implementacja B3 (Curator AI normalizacja) — PRIORYTET 4
Po B2. AI sugeruje dopasowanie KiCad→NSIP jako `suggested` w `recycled_part_kicad_links` (Z90). Cyber: AI NIGDY `approved` (wymuszczone w `kicad_review.js`, `reviewed_by=ai` zablokowane). `recycled_part_master` NIE nadpisany przez curatora. Test integracyjny curator→maintener approve. Patrz `ZLECENIE_GLOWNE_B3_*.md`.

### T5 — Implementacja B5 (Bot execution_pack initiator) — PRIORYTET 5
Po B1-B4 (potrzebuje metryk z B4). `!execution-pack start <id>` → fork → PR (CANARY) → reviewer wyznaczony. Cyber: bot NIE merge do main bez human review, NIE pisze do `recycled_part_master` (Z91). PR/repo branch protection. Test integracyjny. Patrz `ZLECENIE_GLOWNE_B5_*.md`.

### T6 — E (WebSocket events stream dla węzłów edge) — OPEN, dla H3
`/v1/ws/events?provider_id=<id>` — push z centrali do węgłów (rekomendacje, alarmy), bez polling. Wskazane w H3 (węzły jako providery). Cyber: uwierzytelnienie przez `write_token` (rotate), TLS websocket, rate-limit dziedziczy z S2-A.

### T7 — Auto-deactivate providera >72h bez heartbeat (z C)
`heartbeat` aktualizuje `last_seen_at`, ale auto-deactivate po >72h (zropy z roadmapy) nie zaimplementowane. Dodatkowy cron/scheduled task w `worker.js` który oznacza `provider_status='inactive'` gdy `last_seen_at` < now-72h. Test mjs. Cyber: deactivated provider nie przyjmuje observations/events (rate-limit + auth check).

### T8 — Realny checkout CERN dla Z93 (operator)
Klon `https://gitlab.com/ohwr/cern-kicad-libs` poza working copy, re-run importera z `--source` i realnym SHA CERN, wypełnij checklist z `Z93_FIXTURE_SMOKE_REPORT_2026-07-05.md`. Promuje Z93 PARTIAL → DONE. Nieblokujące.

### T9 — Testy hardware proot installer + BLE (agent tester)
`ODBIOR_PROOT_EDGE_INSTALLER_2026-07-05.md` (10-punktowa checklist) + BLE test (`gpio-ble <mac> ffe1 12 1`). Wymaga 2 telefonów (Qualcomm + MediaTek) + ESP32 + FT232R.

## Pliki kluczowe (nowe w tej turze)

- `cloudflare/src/provider_rate_limiter.js` — S2-A token bucket per provider.
- `cloudflare/src/worker.js` — heartbeat, trust-level PATCH, decision gate, rate limit (S2/S3).
- `cloudflare/src/security_headers.js` — PATCH CORS, extraHeaders, x-trust-editor-secret.
- `straz-edge-installer/scripts/nsip-client.sh` — offline bufor, heartbeat, flush, cyber hardening (S2-B).
- `pipelines/import_cern_kicad_library.py` — MPN_Alt, ki_fp_filters, dnp, exclude_from_sim (S4).
- `tests/provider_rate_limiter_test.mjs`, `tests/provider_trust_level_test.mjs` — nowe testy (16 łącznie).
- `tests/test_cern_kicad_importer.py` — rozszerzony fixture + MPN_Alt test (S4).
- `docs/AGENTY_PODWYKONAWCZE/ZLECENIE_GLOWNE_B{1..5}_*.md` — 5 zleceń H2 (S5).
- `docs/AGENTY_PODWYKONAWCZE/ZLECENIE_GLOWNE_WEZLY_EDGE_PROVIDER_API.md` — A/B/C/D DONE, E OPEN.

## Pliki kluczowe (dziedziczone)

- `cloudflare/src/kicad_review.js` (Z90), `ecoeda_export.js` (Z91), `discord_kicad_actions.js` (Z94), `kicad_lookup.js` (Z89).
- `cloudflare/src/schema_migrations.js` (Z88 + gpio_pin_map_json Q8).
- `docs/ROADMAPA_AUTONOMICZNEJ_AUTOMATYZACJI_AI.md` (Z95), `docs/KICAD_VERSION_CONVERSION_EXPORT_POLICY.md` (Z92).
- `docs/AGENTY_PODWYKONAWCZE/PORTFEL_25_ZLECEN_DLA_PODWYKONAWCOW_2026-07-05.md` — portfel H2 (B1-B5).
- `docs/AGENTY_PODWYKONAWCZE/Z93_FIXTURE_SMOKE_REPORT_2026-07-05.md` — fixture smoke (R1).

## Priorytety

1. **T1 → T2 → T3 → T4 → T5** — realizacja Portfelu 25 (H2 roadmapa) w kolejności B4→B1→B2→B3→B5. Główny backlog.
2. **T7** — auto-deactivate providera (hardening C).
3. **T6** — WebSocket stream (dla H3).
4. **T8** — realny CERN (operator).
5. **T9** — testy hardware (tester).

## Commit'y (ta tura)

- `309ec98` feat(edge): S2-A rate limit + S2-C heartbeat + S3 trust_level (gate decision events)
- `42b6618` feat(edge): S2-B offline bufor/retry + cyber hardening nsip-client
- `b8c224a` feat(cern): S4 rozszerzenia parsera Z87 (ki_fp_filters, dnp, MPN_Alt fallback)
- `cb99701` docs: S5 pliki zlecen B1-B5 + aktualizacja edge API spec
- (ten commit) docs: handoff PO_S1_S2_S3_S4_S5 z lista T1-T9

## Odniesienia

- `docs/HANDOFF_DLA_NASTEPNEGO_AGENTA_2026-07-05_PO_R1_R5_R7_R8.md` — poprzedni handoff (S1-S6, wykonany S2/S3/S4/S5).
- `docs/HANDOFF_DLA_NASTEPNEGO_AGENTA_2026-07-05_PO_Q1_Q8.md` — jeszcze wcześniejszy.

## Uwagi

- Status 230 testów mjs + 5 python — bez regressionów.
- `bash -n nsip-client.sh` PASS (bez ostrzeżeń o unterminated here-doc — naprawione).
- Cyberbezpieczeństwo: patrz sekcja ZALECENIE TRWAŁE na górze — dotyczy wszystkich kolejnych agentów.
- Portfel 24 ZAMKNIĘTY. Portfel 25 OPEN (B1-B5 zlecenia utworzone, T1-T5 to ich realizacja).
- Następny portfel (Portfel 26) pojawi się po gate H2 z realizacji Portfela 25 — H3 (węzły edge jako providery, self-healing, auto-rollback, integrity review).
- `.kilo/` pozostaje w `.gitignore`.
