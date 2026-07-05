# Handoff dla Następnego Agenta - po P1-P5 - 2026-07-05

## Kontekst z README

Repo NSIP/Straż Przyszłości: AI + tani/upcyklingowany hardware wspierają autonomiczną produkcję żywności, energii i dóbr. Kluczowe: niskokosztowość, wolontariat, boty jako interfejs operacyjny, D1/SQLite jako pamięć/audyt, zasada "AI sugeruje, człowiek zatwierdza".

## Co zrobiono (ten agent)

### P2 — ESP32 GPIO endpoint firmware
PROJEKTY/07_uniwersalna_platforma_sterowania/esp32_gpio_endpoint/:
- `src/main.cpp` — Arduino: GPIO przez HTTP REST (`GET/POST /gpio`), MQTT (topic `esp32/<id>/gpio`), WebSocket (`ws://ip:81/ws`), JSON-over-serial przez UART 115200.
- Konfiguracja WiFi/MQTT przez SerialJSON (bez hardcoded SSID), trzymana w Preferences (NVS).
- 16 bezpiecznych pinów OUTPUT (bez strapping 0/2/12/15).
- `platformio.ini` z deps (ArduinoJson, PubSubClient, WebSocketsServer).
- `README.md` — pinmap, konwencja endpointów, test z smartfonem.
- Kompatybilne z klientami `gpio-usb`, `gpio-http`, `gpio-mqtt`, `gpio-ws` z `straz-edge-installer/`.

### P3-Z91 — Eksport ecoEDA z provenance CERN
- `cloudflare/src/ecoeda_export.js` — `listApprovedKicadLinks`, `buildEcoedaCsv`, `buildEcoedaJson`, `exportApprovedEcoeda`.
- Eksportuje TYLKO linki z `review_status='approved'` (Z90/Z94 gate).
- CSV: core pola ecoEDA + opcjonalne provenance (CERN-Source-Slug, CERN-License-SPDX, CERN-Upstream-Commit, NSIP-Reviewed-By itd.). Flaga `include_provenance` do kontrolowania.
- JSON: obiekt ze schematem, provenanc pod kluczem `provenance`.
- `tests/ecoeda_export_test.mjs` — 9 testów PASS (mock D1 jak w kicad_review_test.mjs).
- Z91 status zmieniony DONE.

### P3-Z95 — Roadmapa autonomicznej automatyzacji AI
`docs/ROADMAPA_AUTONOMICZNEJ_AUTOMATYZACJI_AI.md`:
- 3 horyzonty (2tyg/6tyg/3mies), każdy krok z gate, rollback i metryką.
- Role agentów: importer/verifier/curator/reviewer/exporter/operator.
- Metryki minimalne: coverage, false-positive, P50 czas do review, rollback success rate.
- H1 pętla KiCad (ingest->staging->review->export) — gotowa z Z90+Z91+Z94.
- H2 rozszerzenie na OLX/YouTube/datasheety + metryki D1 + execution_packs.
- H3 węzły edge jako providery w D1, auto-rollback, self-healing ingest, quarterly integrity review.
- Bezpieczne/niebezpieczne akcje bota zdefiniowane (bot NIE może approved/ push/ nadpisać master).
- Z95 status DONE.

### P4 — Roadmapa węzłów edge
`docs/ROADMAPA_WEZLOW_EDGE.md`:
- Model: smartfon (proot, straz-edge-installer) → provider_id w D1 → write_token → observations/events → API Straży.
- 3 typy danych z węzła: observation (pasywne), event (decyzyjne), decision (z reviewed_by).
- Profil `node-nsip` = provider sterownikowy; `gateway` = provider danych; `desktop` = operator.
- Gate: events z `kind=decision` wymagają `reviewed_by`; anomalie → throttling.
- Cykliczny lifecycle węzła: install → register → observations → maintainer trust → GPIO sterowanie → offline bufor → integrity review.
- Ryzyka: Phantom Killer, bateria, SSID, MQTT anonymous.

### P5 — Termux:Boot auto-wznowienie
- `straz-edge-installer/scripts/start-straz-boot.sh` — auto-podnosi proot po restarcie telefonu przez Termux:Boot, `termux-wake-lock`, Phantom Killer check, log do `~/.straz-edge/boot.log`.
- `straz-edge-installer/install.sh` — nowa flaga `--enable-boot` kopiuje skrypt do `~/.termux/boot/`.
- bash -n PASS.

### P1 — Szablon odbioru installer proot edge
`docs/AGENTY_PODWYKONAWCZE/ODBIOR_PROOT_EDGE_INSTALLER_2026-07-05.md`:
- 10-punktowa checklist odbioru: 2 realne telefony (Qualcomm + MediaTek), sudo z hasłem, polkit okno dla Synaptic, gpio-usb/http/mqtt z ESP32, idempotentność, Phantom Killer, brak glibc-repo.
- Stan: PENDING (czeka na wykonanie przez agenta testera z hardware).

### Inne
- `.gitignore` — dodano `.kilo/`.
- Statusy updated: Z91→DONE, Z95→DONE.

## Testy (wszystkie PASS)

```bash
node --test tests/*.mjs     # 207 PASS (ecoeda 9 + discord_kicad 10 + kicad_review 3 + reszta 185)
bash -n straz-edge-installer/*.sh straz-edge-installer/lib/*.sh straz-edge-installer/profiles/*.sh straz-edge-installer/scripts/*.sh  # 9 PASS
```

## Nowa lista zadań dla następnego agenta

### Q1 — Odbiór hardware (P1 execution)
Wykonaj `ODBIOR_PROOT_EDGE_INSTALLER_2026-07-05.md` na 2 realnych telefonach (Qualcomm Adreno + MediaTek). Wymagane: USB-OTG + ESP32 z firmware `esp32_gpio_endpoint` + FT232R. Wypełnij checklistę, dodaj migawki logów, zmień status PENDING→PASS, do commitu z artefaktem.

### Q2 — Test ESP32 GPIO endpoint firmware
Wgraj `esp32_gpio_endpoint` na ESP32, skonfiguruj WiFi/MQTT przez SerialJSON, zweryfikuj wszystkie 4 kanały (USB-serial/HTTP/MQTT/WS) z komendami `gpio-usb/http/mqtt/ws` z smartfona. Raport z verdictem w `PROJEKTY/07_uniwersalna_platforma_sterowania/esp32_gpio_endpoint/docs/test_report.md`.

### Q3 — Z93 smoke importera CERN
`docs/AGENTY_PODWYKONAWCZE/ZLECENIE_GLOWNE_93_CERN_KICAD_REAL_CHECKOUT_SMOKE.md` — smoke importera na realnym checkout/archiwum CERN albo blocker receipt jeśli brak dostępu. Powiązany z Z87 (dry-run importer) + Z88 (staging migrations).

### Q4 — Z92 polityka konwersji KiCad
`docs/AGENTY_PODWYKONAWCZE/ZLECENIE_GLOWNE_92_KICAD_VERSION_CONVERSION_EXPORT_POLICY.md` (low) — polityka konwersji KiCad jako etap eksportu.

### Q5 — Klient API Straży dla węzłów
Implementacja `straz-register`, `straz-observe`, `straz-event` w `straz-edge-installer/scripts/` (zgodnie z `docs/ROADMAPA_WEZLOW_EDGE.md`). Kontrakt: jednorazowa rejestracja przez `/v1/providers/register`, observations/events do `/v1/events`, token w `/etc/straz-edge/provider.env` (chmod 0600). Zależny od endpóntu API — jeśli nie istnieje, zostaw placeholder.

### Q6 — BLE GATT endpoint w ESP32 firmware
Rozszerzyć `esp32_gpio_endpoint/src/main.cpp` o BLE serwer z GATT charakterystyką dla GPIO (komendy `set`/`get`), kompatybilne z `gpio-ble` z `lib/gpio_bridge.sh`.

### Q7 — Roadmapa edge do zlecenia
Przekształć `docs/ROADMAPA_WEZLOW_EDGE.md` w `ZLECENIE_GLOWNE_WEZLY_EDGE_PROVIDER_API.md` w `docs/AGENTY_PODWYKONAWCZE/` z konkretnym spec API (endpoints, schematy, rotacja tokenów, throttling).

### Q8 — DeviceCatalog z GPIO-mapped urządzeniami
W katalogu urządzeń w D1 (`recycled_device_submissions`) dodać kolumnę `gpio_pin_map_json` — pinmap dla urządzeń, które mają GPIO endpoint (ESP32, Raspberry Pi zero, etc.). Powiązanie z `profile_template` z Z15. Nowa migracja D1 + test.

## Priorytety

1. **Q1** + **Q2** — testy hardware (niezbędne do zamknięcia proot installer + ESP32 firmware).
2. **Q3** — smoke CERN (Tor A, ostatnie z Portfela 24).
3. **Q5** — klient API Straży (wiązanie węzłów z centralą).
4. **Q7** + **Q8** — standaryzacja edge+D1.
5. **Q4** + **Q6** — niski priorytet.

## Pliki kluczowe

- `straz-edge-installer/` — pełny installer (11 plików).
- `docs/ROADMAPA_AUTONOMICZNEJ_AUTOMATYZACJI_AI.md` — Z95 roadmapa (3 horyzonty).
- `docs/ROADMAPA_WEZLOW_EDGE.md` — P4 roadmapa edge.
- `cloudflare/src/ecoeda_export.js` + `tests/ecoeda_export_test.mjs` — Z91.
- `PROJEKTY/07_uniwersalna_platforma_sterowania/esp32_gpio_endpoint/` — P2 firmware.
- `docs/AGENTY_PODWYKONAWCZE/ODBIOR_PROOT_EDGE_INSTALLER_2026-07-05.md` — P1 szablon odbioru (do wykonania).

## Odniesienia

- `docs/REKOMENDACJE_AUTONOMICZNEJ_AUTOMATYZACJI_AI_2026-05-14.md` — ścieżki bazowe, zachowana spójność.
- `cloudflare/src/kicad_review.js` (Z90) — ledger review, niewzmieniony.
- `cloudflare/src/kicad_lookup.js` (Z89) — lookup, niewzmieniony.
- `cloudflare/src/discord_kicad_actions.js` (Z94) — Discord actions, niewzmieniony.