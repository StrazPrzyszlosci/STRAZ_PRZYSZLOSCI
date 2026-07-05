# Handoff dla Następnego Agenta - po R1+R5+R7+R8 - 2026-07-05

## Kontekst z README

Repo NSIP/Straż Przyszłości: AI + tani/upcyklingowany hardware → autonomiczna produkcja żywności, energii i dóbr. Boty jako interfejs operacyjny, D1/SQLite jako pamięć/audyt. Zasada: **AI sugeruje, człowiek zatwierdza zmiany produkcyjne**.

## Co zrobiono (ten agent)

Rozpocząłem od odczytu poprzedniego handoffu `PO_Q1_Q8` (commit 669988e). Wykonałem priorytetowe zadania z listy R1-R8: R1 (smoke CERN fixture), R5 + R8 (zamknięcie Portfela 24), R7 (nowy Portfel 25 dla H2 roadmapy). R2, R3, R4, R6 pozostają dla następnego agenta (hardware / API hardening).

### R1 — Z93 Smoke na fixture CERN (PARTIAL PASS)
- `docs/AGENTY_PODWYKONAWCZE/Z93_FIXTURE_SMOKE_REPORT_2026-07-05.md` — pełny raport smoke z fixture mini.
- Uruchomiono `pipelines/import_cern_kicad_library.py --source tests/fixtures/cern_kicad_libs_fixture --output-stamp fixture_smoke_2026-07-05 --sample-limit 50`.
- Wynik: 2 komponenty (1 sym `TPS65994` + 1 footprint QFN-56), pełna provenance (`source_slug`, `license_spdx`, `kicad_version_family`, `upstream_commit`).
- Artefakty preview committable (< 10 kB): JSONL + CSV + MD.
- Weryfikacja 3 kryteriów odbioru Z93: 2 PASS, 1 PARTIAL (SHA to NSIP repo, nie CERN — fixture substitute).
- Rekomendacje rozszerzeń parsera Z87 przed full ingest: `ki_fp_filters`, `dnp`, 3D models, `.pretty` dirs rekurencja, `MPN_Alt`.
- Status Z93 zmieniony: `BLOCKED` → `PARTIAL PASS (fixture substitute)` w `ZLECENIE_GLOWNE_93`.
- Realny checkout CERN nadal pozostaje open follow-up dla operatora (krok w `Z93_BLOCKER_RECEIPT_CERN_CHECKOUT_2026-07-05.md`).

### R5 + R8 — Zamknięcie Portfela 24 (Z87–Z95)
- `docs/AGENTY_PODWYKONAWCZE/PORTFEL_24_ZLECEN_DLA_PODWYKONAWCOW_2026-05-14.md` — tabela statusów ujednolicona dla **wszystkich 9 zadań** Z87–Z95:
  - Z87 DONE (Odbiór 21 + potwierdzone R1 fixture smoke).
  - Z88 DONE (Odbiór 21 — migracje staging).
  - Z89 DONE (Odbiór 22 — `kicad_lookup.js`).
  - Z90 DONE (Odbiór 23 — `kicad_review.js`).
  - Z91 DONE (`ecoeda_export.js` + 9 testów).
  - Z92 DONE (`KICAD_VERSION_CONVERSION_EXPORT_POLICY.md`).
  - Z93 PARTIAL PASS (fixture substitute — to zlecenie).
  - Z94 DONE (`discord_kicad_actions.js` + 10 testów).
  - Z95 DONE (`ROADMAPA_AUTONOMICZNEJ_AUTOMATYZACJI_AI.md`).
- Definition of Done Portfela 24 weryfikowane dla wszystkich 4 punktów: PASS.
- **Portfel 24 ZAMKNIĘTY.**

### R7 — Nowy Portfel 25 dla H2 roadmapy autonomizacji AI
- `docs/AGENTY_PODWYKONAWCZE/PORTFEL_25_ZLECEN_DLA_PODWYKONAWCOW_2026-07-05.md` — przekuwa Horyzont 2 (6 tygodni) z `ROADMAPA_AUTONOMICZNEJ_AUTOMATYZACJI_AI.md` na 5 zleceń:
  - **B1** Importer agent harmonicemowany (cron → staging D1, dedup before insert).
  - **B2** Verifier agent deterministyczny (schema-diff + dedup + OCR deferred).
  - **B3** Curator AI normalizacja (sugestie `suggested`, zero zapisów do master).
  - **B4** Dashboard metryk D1 (`automation_metrics` table, 5 metryk minimalnych).
  - **B5** Bot inicjuje `execution_pack` (fork-first, PR-first, CANARY, review-first).
- Każde zlecenie ma gate + rollback + metrykę (spójne z H2 z roadmapy).
- Kolejność: B4 → B1 → B2 → B3 → B5.
- Definition of Done ujednolicona, metryki minimalne tablicowane.

### R2, R3 — Hardening providerów edge (ODROCZONE)
Nie wykonane w tej turze — to kod (rate limit table, offline bufor w `nsip-client.sh`, heartbeat, `trust_level`). Wymaga implementacji w `cloudflare/src/worker.js` + `nsip-client.sh` + testów. Przeniesione do nowej listy (S2, S3 poniżej).

### R4 — Testy hardware proot installer (ODROCZONE)
Wymaga 2 telefonów (Qualcomm + MediaTek) + ESP32 + FT232R. Szablon odbioru gotowy (`ODBIOR_PROOT_EDGE_INSTALLER_2026-07-05.md`). Oczekiwanie na agenta tester z hardware.

### R6 — Test BLE na ESP32 hardware (ODROCZONE)
Firmware gotowy (`ble.cpp`), wymaga ESP32 + smartfon z Bluetooth. Test komendy `gpio-ble <mac> ffe1 12 1`.

## Testy wykonane

```bash
node --test tests/*.mjs     # 208 PASS (0 fail) — bez zmian od Q8
python3 pipelines/import_cern_kicad_library.py --source tests/fixtures/cern_kicad_libs_fixture --output-stamp fixture_smoke_2026-07-05 --sample-limit 50  # R1 smoke: 2 komponenty
```

## Nowa lista zadań dla następnego agenta

### S1 — Realny checkout CERN dla pełnego PASS Z93 (operator)
Klonuj `https://gitlab.com/ohwr/cern-kicad-libs` poza working copy (np. `/tmp/cern-kicad-lib`), uruchom `pipelines/import_cern_kicad_library.py --source /tmp/cern-kicad-lib --sample-limit 200`, wypełnij checklist z `Z93_FIXTURE_SMOKE_REPORT_2026-07-05.md` z realnym SHA CERN. To promuje Z93 z PARTIAL PASS → DONE. Wymaga dysk/internet, nie blokuje innych zadań.

### S2 — Rozszerzenia providerów edge A/B/C (z Q7, transfer z R2)
Implementacja w `cloudflare/src/worker.js`:
- **A. Rate limit/throttling** — nowa tabela `provider_rate_limit` + middleware sprawdzający token bucket per `provider_id`.
- **B. Offline bufor w `nsip-client.sh`** — retry z exponential backoff, spool pending observations/events do pliku gdy brak sieci, flush przy reconnect.
- **C. Heartbeat + status** — nowy endpoint `POST /v1/providers/<id>/heartbeat`, agent `nsip-client.sh heartbeat` co N sekund.
Testy jednostkowe (`tests/*.mjs`) dla throttlingu i retry. Aktualizacja `ZLECENIE_GLOWNE_WEZLY_EDGE_PROVIDER_API.md` o zaimplementowane rozszerzenia.

### S3 — Trust level dla providerów (z Q7-D, transfer z R3)
- Nowa kolumna `trust_level INTEGER DEFAULT 0` w providers (migracja w `schema_migrations.js`).
- Endpoint `PATCH /v1/providers/<id>/trust-level` (tylko maintainer — sprawdzić `isMaintainer()` z `discord_kicad_actions.js` jako wzorzec).
- Gate dla `kind=decision` events: tylko `trust_level >= 2` może wysywać decision events; else `403`.
- Test integracyjny w `tests/*.mjs`.

### S4 — Rozszerzenia parsera Z87 (z R1 rekomendacji)
W `pipelines/import_cern_kicad_library.py`:
- Parse `ki_footprint_filters` / `ki_fp_filters` → zapis do `raw_metadata_json` lub nowa kolumna.
- Obsługa `exclude_from_sim` / `dnp` properties.
- Rekurencja po `.pretty` dirs (potwierdzenie, nie tylko jednostkowych `.kicad_mod`).
- Obsługa alternatywnych pól MPN (`MPN_Alt`, `Substitution`).
- Test rozszerzony w `tests/test_cern_kicad_importer.py`.
Niewykonanie nie blokuje H2, ale podnosi coverage przy pełnym ingest.

### S5 — Zlecenia B1-B5 z Portfela 25 (H2 roadmapa)
To główny backlog kolejnego agenta kodowego. Utworzyć pliki `ZLECENIE_GLOWNE_B1_*.md` … `B5_*.md` (jeśli brak), następnie implementować w kolejności B4 → B1 → B2 → B3 → B5 z gate H2 i metrykami. Patrz `PORTFEL_25_ZLECEN_DLA_PODWYKONAWCOW_2026-07-05.md`.

### S6 — Testy hardware (transfer z R4 + R6)
Agent tester z 2 telefonami (Qualcomm + MediaTek) + ESP32 + FT232R:
- `ODBIOR_PROOT_EDGE_INSTALLER_2026-07-05.md` (10-punktowa checklist).
- Test BLE: wgraj firmware `esp32_gpio_endpoint` z `ble.cpp`, komenda `gpio-ble <mac> ffe1 12 1`, JSON response.

## Pliki kluczowe (nowe w tej turze)

- `docs/AGENTY_PODWYKONAWCZE/Z93_FIXTURE_SMOKE_REPORT_2026-07-05.md` — raport smoke R1.
- `docs/AGENTY_PODWYKONAWCZE/PORTFEL_24_ZLECEN_DLA_PODWYKONAWCOW_2026-05-14.md` — ZAMKNIĘTY (statusy Z87–Z95).
- `docs/AGENTY_PODWYKONAWCZE/PORTFEL_25_ZLECEN_DLA_PODWYKONAWCOW_2026-07-05.md` — nowy portfel H2 (B1–B5).
- `PROJEKTY/13_baza_czesci_recykling/cern_kicad_import_preview/` — artefakty smoke R1 (JSONL + CSV + MD).

## Pliki kluczowe (dziedziczone)

- `cloudflare/src/worker.js` — API provider/observations/events (rozszerzenia S2/S3 tu).
- `cloudflare/src/kicad_review.js` (Z90), `ecoeda_export.js` (Z91), `discord_kicad_actions.js` (Z94), `kicad_lookup.js` (Z89).
- `cloudflare/src/schema_migrations.js` (Z88 + gpio_pin_map_json Q8) — tu migracje S3 i B4.
- `pipelines/import_cern_kicad_library.py` (Z87) — tu S4 i B1.
- `straz-edge-installer/scripts/nsip-client.sh` (Q5) — tu S2-B (offline bufor).
- `PROJEKTY/07_uniwersalna_platforma_sterowania/esp32_gpio_endpoint/` (P2 + Q6) — tu S6 BLE test.
- `docs/ROADMAPA_AUTONOMICZNEJ_AUTOMATYZACJI_AI.md` (Z95) — roadmapa nadrzędna.
- `docs/AGENTY_PODWYKONAWCZE/ZLECENIE_GLOWNE_WEZLY_EDGE_PROVIDER_API.md` (Q7) — spec provider API.
- `docs/AGENTY_PODWYKONAWCZE/Z93_BLOCKER_RECEIPT_CERN_CHECKOUT_2026-07-05.md` — krok odblokowania realnego checkout.
- `docs/KICAD_VERSION_CONVERSION_EXPORT_POLICY.md` (Z92) — polityka konwersji (S4 i B5 respektują).

## Priorytety

1. **S5** — realizacja Portfela 25 (H2 roadmapa, główny backlog, 5 podzadań).
2. **S2 + S3** — hardening API providerów (kod, bez hardware).
3. **S4** — rozszerzenia parsera Z87 (podnosi coverage przy ingest).
4. **S1** — realny checkout CERN (operator, podnosi Z93 do DONE; nieblokujące).
5. **S6** — testy hardware (wymaga 2 telefonów + ESP32, tester).

## Commit'y

- `91b0395` feat(cern): R1 Z93 smoke na fixture + raport (PARTIAL PASS substytut) — Z87 potwierdzone end-to-end
- (ten commit) docs: R5+R8 zamkniecie Portfela 24 (Z87-Z95) + R7 Portfel 25 (H2 roadmapa B1-B5)

## Odniesienia

- `docs/HANDOFF_DLA_NASTEPNEGO_AGENTA_2026-07-05_PO_Q1_Q8.md` — poprzedni handoff (R1-R8 task list, wykonany R1/R5/R7/R8).
- `docs/HANDOFF_DLA_NASTEPNEGO_AGENTA_2026-07-05_PO_P1_P5.md` — handoff jeszcze wcześniejszy (P1-P5 + Q1-Q8 task list).

## Uwagi

- Status 208 testów niezmieniony (R1/R5/R7 to documentacja + smoke, nie kod Cloudflare).
- `bash -n straz-edge-installer/scripts/nsip-client.sh` nadal PASS (nie modyfikowano).
- Portfel 24 ZAMKNIĘTY. Jedyny open follow-up: realny checkout CERN (S1, operator).
- Następny portfel (Portfel 26) pojawi się po gate H2 z realizacji Portfela 25 — będzie dotyczył H3 (węzły edge jako providery, automatyczny rollback, self-healing).
- `.kilo/` pozostaje w `.gitignore` (config wewnętrzny Kilo).
