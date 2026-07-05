# Roadmapa Węzłów Edge — smartfon jako provider w D1

## Kontekst

Stare smartfony jako **komputery sterownicze na Linuksie** przez proot (patrz `straz-edge-installer/` i `docs/PROOT_LINUX_NA_SMARTFONACH_ANALIZA_SKRYPTOW.md`) stają się providerami danych w centralnej warstwie API Straży. Każdy smartfon-węzeł to jeden `provider_id` w D1, wysyłający observations/events przez `write_token`.

Bazuje na `docs/ARCHITEKTURA_EDGE_SMARTFONY_CLOUD.md` (sieć rozproszonych węzłów edge) oraz `docs/MAPOWANIE_ENCJI_ORGANIZACJI_DO_D1_I_SQLITE.md`.

## Model

```
smartfon (proot) → klienci NSIP (agenty, gpio-bridge) →API Straży →D1
   provider_id       write_token (rotacja)            observations/events/smoki
```

- Smartfon `rejestruje się` jako provider przez `/v1/providers/register` (jeden raz), otrzymuje `provider_id`.
- Pobiera `write_token` (rotacja bez zmiany `provider_id`).
- Wysyła `observations` (pomiary) i `events` (zmiany stanu, decyzje, alerty).
- Centrala zwraca `recommendations` (legko/co nastąpi, akcje sugerowane).
- Węzeł może być graficzny (`profiles/desktop`, operator) albo headless (`profiles/node-nsip`, sterownik).

## Dane sterownikowe vs obserwacyjne

| Rodzaj | Sposób trafia do centrali | Przykład |
|--------|------------------------------|---------|
| **Observation** (pasywna) | `POST /v1/events` z `kind=observation` | temperatura stawu, rpm pompy, state GPIO |
| **Event** (decyzyjna) | `POST /v1/events` z `kind=event` | "pump_on_maintainer_approved", "gpio_set 12 1 by gpio-mqtt" |
| **Decision timestamp** | `kind=decision` z `reviewed_by` | "maintener-01 zatwierdził gpio 12=1 na 13:32" |

Wszystkie trzy to event ledger — to samo co `kicad_review_events` (Z90), tylko dla warstwy edge.

## Profil `node-nsip` jako provider

`straz-edge-installer/profiles/node-nsip.sh` instaluje:
- `python3-paho-mqtt` — lokalny broker ESP32 → smartfon,
- `python3-requests`, `python3-yaml` — klient API Straży,
- `gpio-bridge` (`gpio-usb/http/mqtt/ws/ble`) — sterowanie GPIO na ESP32,
- bufor `/nsip-data` (= `/sdcard/NSIP`) dla offline-first.

Kontrakt klienta API (do zaimplementowania w `straz-edge-installer/scripts/`):
```bash
# Rejestracja (jednorazowo):
straz-register [--name "stary-s3"] [--env prod] → zapisuje provider_id, token w /etc/straz-edge/provider.env
# Wysłanie obserwacji:
straz-observe '{"kind":"observation","metric":"temp","value":24.1,"unit":"C"}'
straz-event '{"kind":"event","type":"pump_on","gpio_pin":12,"reason":"maintainer_approved"}'
```

## Profile `gateway` a `node-nsip`

- `gateway` — bramka **danych** (lokalny mosquitto, bufor, przekaz do API). Brak sterowania GPIO.
- `node-nsip` — bramka **sterownikowa** (klient gpio-bridge + API). Steruje aktuatorami.
- `desktop` — `node-nsip` + interfejs operatora (XFCE).

## Gate i rollback (z H3 roadmapy AI)

- **Gate:** węzeł może wysyłać observations bez limitu; events z `kind=decision` wymagają `reviewed_by` (maintener albo zatwierdzony przez `automation` agenta z `executions_pack`).
- **Rollback:** jeśli węzeł zacznie wysyłać anomalie (np. 100 events/min), centrala throttluje `write_token` i oznacza provider `rate_limited`. Operator widzi status przez `/v1/providers/<id>/status`.
- **Bezpieczeństwo:** `write_token` nie commituje się w repo; trzymany w `/etc/straz-edge/provider.env` (0600) na smartfonie; rotacja przez API bez zmiany `provider_id`.

## Estyma cykl życia węzła

```
1. Wolontariusz instaluje straz-edge-installer --profile node-nsip
2. Rejestracja jako provider (jawny `provider_id`, env)
3. Pierwsza observation auto-wysyłana przez collector
4. Maintener widzi provider w D1, ustawia trust_level
5. Węzeł steruje GPIO przez ESP32 (gpio-bridge), decyzje z reviewed_by
6. Offline → bufor /sdcard/NSIP → retry z backoff
7. Kwartalnie: integrity review (z REVIEW_ROTATION_GOVERNANCE.md)
```

## Metryki (rozdz. Roadmap AI H3)

- N providerów aktywnych / dobę (heartbeat).
- % providerów z `rate_limited` / `blocked`.
- P50 latencji observation → event ledger.
- N gpio-set events z `reviewed_by` / bez.
- Utrata danych offline (% retry success).

## Wąskie gardła / ryzyka

- **Phantom Process Killer** (Android 13+) — patrz `straz-edge-installer/scripts/RUNBOOK_PHANTOM_PROCESS_KILLER.md`. Bez fixu provider pada po kilku minutach.
- **Bateria** — węzeł headless musi `termux-wake-lock` + optymalizacja WiFi sleep.
- **SSID/WiFi** — konfiguracja przez SerialJSON (ESP32) albo `provider.env`. Brak hardcoded.
- **MQTT `allow_anonymous true`** w profilu gateway — w sieci LAN ok, ale nie na publiczny internet.

## Najlepszy następny krok

Implementacja `straz-register` / `straz-observe` / `straz-event` klientów w `straz-edge-installer/scripts/` + endpoint `/v1/events` w centrali (jeśli nie jeszcze istnieje — sprawdzić `cloudflare/src/worker.js`). Patrz handoff P5-P6.
