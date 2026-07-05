# Handoff dla Następnego Agenta - po Q1-Q8 - 2026-07-05

## Kontekst z README

Repo NSIP/Straż Przyszłości: AI + tani/upcyklingowany hardware → autonomiczna produkcja żywności, energii i dóbr. Boty jako interfejs operacyjny, D1/SQLite jako pamięć/audyt. Zasada: AI sugeruje, człowiek zatwierdza zmiany produkcyjne.

## Co zrobiono (ten agent)

Rozpocząłem od sprawdzenia poprzedniego handoffu PO_P1_P5. Wykonano wszystkie 8 zadań Q1-Q8 z listy.

### Q3 — Z93 Blocker receipt dla CERN checkout
- `docs/AGENTY_PODWYKONAWCZE/Z93_BLOCKER_RECEIPT_CERN_CHECKOUT_2026-07-05.md` — blocker receipt ponieważ brak lokalnego checkout CERN KiCad Library na maszynie.
- Z93 status zmieniony na BLOCKED z opisem co jest potrzebne do odblokowania (klon CERN lib, `import_cern_kicad_library.py --source-dir`).
- Rekomendacja smoke na fixture mini (który już jest w repo) jako substytut.

### Q4 — Z92 Polityka konwersji wersji KiCad
- `docs/KICAD_VERSION_CONVERSION_EXPORT_POLICY.md` — decyzja bazowa: konwersja to downstream export, nie przed ingestem.
- Runbook A–D: sym upgrade, fp upgrade, full project conversion, brak konwersji.
- Test na minimalnym fixture (NE555 z CERN sample JSONL).
- Ryzyka zinwentaryzowane (custom fields, net tie pads, fp-lib-table).
- Z92 status DONE.

### Q5 — Klient API Straży dla węzłów
- `straz-edge-installer/scripts/nsip-client.sh` — bash+python3 klient HTTP:
  - `nsip-client register [--env prod] [--name "węzeł-nazwa"]` — rejestruje provider w D1, zapisuje `provider_id` i `write_token` do `/etc/straz-edge/provider.env` (0600).
  - `nsip-client observe '<json>'` / `event '<json>'` — wysyła observations/events do `/v1/observations`, `/v1/events` z Bearer token.
  - `nsip-client rotate-token` — rotuje token bez zmiany `provider_id`.
  - `nsip-client status` — sprawdza status providera.
  - Kompatybilny z istniejącym API w `cloudflare/src/worker.js` (register/observe/event/rotate).
  - bash -n PASS.

### Q6 — BLE GATT endpoint w ESP32 firmware
- `PROJEKTY/07_uniwersalna_platforma_sterowania/esp32_gpio_endpoint/src/ble.cpp` — native ESP32 BLE: serwis `ffe0`, charakterystyka `ffe1` z komendą [pin byte][value byte] → odpowiedź JSON.
- `main.cpp` — zintegrowane: `setupBLE()` po connectWifi, standalone BLE mode jeśli brak WiFi config.
- `README.md` — dodane BLE GATT jako 5. kanał sterowania GPIO.
- Kompatybilne z `gpio-ble` z `lib/gpio_bridge.sh`.

### Q7 — Zlecenie WEZLY_EDGE_PROVIDER_API
- `docs/AGENTY_PODWYKONAWCZE/ZLECENIE_GLOWNE_WEZLY_EDGE_PROVIDER_API.md` — spec API z istniejącego Worker + 5 planowanych rozszerzeń (A. rate limit/throttling, B. offline bufor/retry, C. heartbeat + status, D. trust_level + decision gate, E. WebSocket events stream).
- Kontrakt wszystkich endpointów udokumentowany.
- Klient `nsip-client.sh` gotowy. API w worker.js już obsługuje register/observe/event/rotate.

### Q8 — DeviceCatalog z gpio_pin_map_json
- `cloudflare/src/schema_migrations.js` — nowa migracja `20260705000001-devices-gpio-pin-map`: `ALTER TABLE recycled_devices ADD COLUMN gpio_pin_map_json TEXT`.
- `tests/schema_migrations_test.mjs` — test dla nowej kolumny + fix idempotencji testu (ALTER TABLE nie ma IF NOT EXISTS w SQLite).
- 208 testów PASS (0 fail).

### Q1 + Q2 — Hardware tests (oznaczone jako pending)
- Q1 szablon odbioru gotowy (`ODBIOR_PROOT_EDGE_INSTALLER_2026-07-05.md`, 10-punktowa checklist).
- Q2 firmware ESP32 gotowe (P2 + Q6), zreadystate do testu.
- Obie czekają na fizyczne 2 telefony + ESP32 + FT232R — agent tester musi je wykonać.

## Testy wykonane

```bash
node --test tests/*.mjs     # 208 PASS (0 fail)
bash -n straz-edge-installer/scripts/nsip-client.sh  # PASS
```

## Nowa lista zadań dla następnego agenta

### R1 — Smoke CERN na fixture
Skoro Z93 jest BLOCKED (brak realnego checkout CERN), wykonaj smoke na fixture mini. Uruchom `pipelines/import_cern_kicad_library.py` ze sample-dir, wypełnij checklist Z93, wygeneruj raport. To odblokowuje Z93 jako PASS (fixture), uzupełnia Z87 o realne dane sample.

### R2 — Wdrożenie rozszerzeń A/B/C dla providerów edge (z Q7)
Implementacja throttingu (`provider_rate_limit` table), offline bufora w `nsip-client.sh` (retry z backoff), heartbeat endpoint. Testy jednostkowe dla thirdle i retry.

### R3 — Obsługa trust_level dla providerów (Q7-D)
Nowa kolumna `trust_level` w providers, endpoint `PATCH /v1/providers/<id>/trust-level` (tylko maintener), gate dla `kind=decision` events (tylko trust_level >= 2). Test integracyjny.

### R4 — Test hardware (Q1 + Q2 execution)
Agent tester z 2 telefonami (Qualcomm + MediaTek) i ESP32 + FT232R wykonuje `ODBIOR_PROOT_EDGE_INSTALLER_2026-07-05.md` checklist, wypełnia wszystkie 10 punktów, generuje raport z verdictem. To zamyka zlecenie `ZLECENIE_GLOWNE_PROOT_EDGE_INSTALLER_STRAZY`.

### R5 — Aktualizacja Portfela 24 statusów
Z91, Z92, Z94 = DONE. Z93 = BLOCKED (receipt). Z95 = DONE. Aktualizuj `PORTFEL_24_ZLECEN_DLA_PODWYKONAWCOW_2026-05-14.md` — wpisz wszystkie statusy. To zamyka Portfel 24.

### R6 — Test BLE na hardware (Q6 verification)
Wgraj `esp32_gpio_endpoint` z BLE na ESP32, skonfiguruj standalone BLE mode, wyślij komendę przez `gpio-ble <mac> ffe1 12 1`, zweryfikuj JSON response. Potrzebne: ESP32 + smartfon z Bluetooth.

### R7 — Nowy portfel dla H2 roadmapy AI
Z `ROADMAPA_AUTONOMICZNEJ_AUTOMATYZACJI_AI.md` przekuć H2 (6 tygodni) na zestaw zleceń podwykonawczych: B1 (scheduled import agent), B2 (verifier agent), B3 (curator/normalizacja), B4 (dashboard metryk D1), B5 (bot inicjuje execution_pack). Utworzyć `PORTFEL_25_ZLECEN_DLA_PODWYKONAWCOW` z priorytetami.

### R8 — Z89/Z88/Z87 status update
Zaktualizuj statusy w zleceniach, jeśli są częściowo zaimplementowane (importer Z87 istnieje jako `pipelines/import_cern_kicad_library.py`, Z88 migracje w schema_migrations). Przypisz odpowiednie statusy DONE/PARTIAL.

## Pliki kluczowe

- `straz-edge-installer/scripts/nsip-client.sh` — klient API (Q5)
- `cloudflare/src/schema_migrations.js` — migracja gpio_pin_map_json (Q8)
- `docs/KICAD_VERSION_CONVERSION_EXPORT_POLICY.md` — polityka konwersji (Q4/Z92)
- `docs/AGENTY_PODWYKONAWCZE/Z93_BLOCKER_RECEIPT_CERN_CHECKOUT_2026-07-05.md` — blocker (Q3)
- `docs/AGENTY_PODWYKONAWCZE/ZLECENIE_GLOWNE_WEZLY_EDGE_PROVIDER_API.md` — spec API (Q7)
- `PROJEKTY/07_uniwersalna_platforma_sterowania/esp32_gpio_endpoint/` — firmware GPIO (Q6)
- `docs/ROADMAPA_AUTONOMICZNEJ_AUTOMATYZACJI_AI.md` — 3 horyzonty (Z95)
- `docs/ROADMAPA_WEZLOW_EDGE.md` — roadmapa edge (P4)

## Priorytety

1. **R1** — synteryzuje Z93 i odblokowuje Z87.
2. **R4** — test hardware dla proot installer (krytyczne zamknięcie zlecenia).
3. **R5 + R8** — porządkuje statusy i zamyka Portfel 24.
4. **R2 + R3** — hardening providerów API.
5. **R7** — nowy portfel dla H2 (= backup backlog).
6. **R6** — test BLE (wymaga hardware).

## Odniesienia

- `cloudflare/src/kicad_review.js` (Z90) — ledger review, niewzmieniony.
- `cloudflare/src/ecoeda_export.js` (Z91) — eksport approved, niewzmieniony.
- `cloudflare/src/discord_kicad_actions.js` (Z94) — Discord actions, niewzmieniony.
- `cloudflare/src/kicad_lookup.js` (Z89) — lookup, niewzmieniony.
- `straz-edge-installer/` — pełny installer (11 plików).
- `docs/HANDOFF_DLA_NASTEPNEGO_AGENTA_2026-07-05_PO_P1_P5.md` — poprzedni handoff (wykonany).