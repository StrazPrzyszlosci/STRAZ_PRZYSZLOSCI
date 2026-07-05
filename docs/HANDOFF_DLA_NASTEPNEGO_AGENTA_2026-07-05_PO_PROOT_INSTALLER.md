# Handoff dla Następnego Agenta - po Proot Edge Installer - 2026-07-05

## Kontekst z README

Repo służy budowie oddolnej, open-source'owej infrastruktury NSIP/Straż Przyszłości: AI + tani/upcyklingowany hardware mają wspierać autonomiczną produkcję żywności, energii i dóbr. Kluczowe: niskokosztowość, wolontariat, boty jako interfejs operacyjny, D1/SQLite jako pamięć/audyt, zasada „AI sugeruje, człowiek zatwierdza".

## Co zrobiono (ten agent)

### Tor A (z poprzedniego handoffu PO_Z94) — kontynuacja
Po Z94 nie wznowiono Tor A; zamiast tego wykonano Tor B (proot), który był priorytetem polecenia maintenera.

### Tor B — Proot Edge Installer (ZAKOŃCZONE)

**Główny cel:** stare smartfony jako **komputery sterownicze na Linuksie** przez Termux + proot — sterowanie infrastrukturą NSIP przez endpoint GPIO na ESP32/MCU, komunikacją bezprzewodową (Wi-Fi/BT) lub USB-serial.

**Implementacja — `straz-edge-installer/`:**
- `install.sh` — główny, 3 profile (`node-nsip|desktop|gateway`), wybór distro (debian/ubuntu/kali), walidacja username, warning baterii, wskazówki Phantom Killer.
- `lib/common.sh` — `install_pkg` z raportowaniem exit code (fix luki #1 z analizy), spinner, walidacja username, idempotentność (markery `~/.straz-edge/.done-*`).
- `lib/proot.sh` — user + sudo **z hasłem** (nie NOPASSWD), polkit (D-Bus system bus + polkitd + reguła `AUTH_ADMIN` dla apt), `start-proot.sh` podnosi daemon jako root → `su -l user`, grupy i2c/spi/gpio/dialout, reguły udev dla USB-serial (FTDI/CH341/CP210/STM).
- `lib/packages.sh` — listy pakietów według filarów (base, GPIO/I2C/SPI/UART, wireless, USB-bridge, MQTT, AI, sieć, system, control, desktop_proot, reports, vscode).
- `lib/gpio_bridge.sh` — gotowe skrypty klienty sterowania GPIO na ESP32:
  - `gpio-usb` (UART JSON-over-serial),
  - `gpio-http` (Wi-Fi REST),
  - `gpio-mqtt` (MQTT pub),
  - `gpio-ws` (WebSocket async),
  - `gpio-ble` (BLE GATT przez `bleak`),
  - konfig `/etc/straz-edge/gpio-bridge.env`.
- `profiles/node-nsip.sh` — headless komputer sterowniczy (8 kroków).
- `profiles/desktop.sh` — XFCE + Termux-X11 + polkit + **Synaptic przez `pkexec` (okno uprawnień)** (11 kroków).
- `profiles/gateway.sh` — bramka MQTT (6 kroków).
- `scripts/RUNBOOK_PHANTOM_PROCESS_KILLER.md` — runbook Android 13+.
- `scripts/install-vscode-proot.sh` — VS Code TYLKO w proot (`code-oss` lub pełny MS).
- `README.md` — pełna dokumentacja.

**Walidacja:** `bash -n` na wszystkich 8 skryptach — PASS.

**Zweryfikowano z poprzednim handoffu:**
- cel główny (komputer sterowniczy, nie desktop na telefonie) — zrealizowany w profilach,
- prawdziwe sudo z hasłem + polkit (okno uprawnień) — zrealizowane (desktop),
- VS Code tylko w proot — zrealizowane (`scripts/install-vscode-proot.sh`),
- brak `glibc-repo`, brak VS Code z TUR — zrealizowane,
- komunikacja bezprzewodowa + USB z endpointem GPIO — zrealizowane (`lib/gpio_bridge.sh`, `PKG_WIRELESS`, `PKG_USB`),
- pakiety do sterowania GPIO — zrealizowane (`PKG_GPIO`, `PKG_CONTROL`).

### Dokumentacja
- `docs/PROOT_LINUX_NA_SMARTFONACH_ANALIZA_SKRYPTOW.md` — analiza (z poprzedniej sesji) + nowa sekcja "Prawdziwe sudo i okno uprawnień w proot".
- `docs/AGENTY_PODWYKONAWCZE/ZLECENIE_GLOWNE_PROOT_EDGE_INSTALLER_STRAZY.md` — zlecenie z pełną listą rekomendowanych pakietów według filarów + kontrakt endpointu GPIO na ESP32.

## Decyzje

- **3 profile**, domyślny dla węzłów NSIP: `node-nsip` (headless). `desktop` operatora, `gateway` bramka.
- **sudo z hasłem + polkit** w desktop; `NOPASSWD` tylko headless (brak operatora).
- **GPIO sterowane przez endpoint na ESP32**, nie bezpośrednio na smartfonie (Android nie eksponuje gpiochip). Kanały: USB-serial, HTTP, MQTT, WebSocket, BLE.
- **Bind `/sdcard`** ograniczony do `/sdcard/NSIP` (nie cała pamięć).
- **Idempotentność** przez markery `~/.straz-edge/.done-*`.
- **Bez `glibc-repo`/`glibc`** — proot ma własne glibc.
- **VS Code tylko w proot** (potwierdzone przez maintainera w poprzedniej sesji).

## Testy wykonane

```bash
# Syntax check (bash -n) — wszystkie 8 skryptów PASS:
bash -n straz-edge-installer/install.sh
bash -n straz-edge-installer/lib/{common,proot,packages,gpio_bridge}.sh
bash -n straz-edge-installer/profiles/{node-nsip,desktop,gateway}.sh
bash -n straz-edge-installer/scripts/install-vscode-proot.sh
```

Testy na realnym hardware **jeszcze nie wykonane** — patrz lista zadań dla następnego agenta.

## Najlepszy następny krok — lista zadań dla następnego agenta

### Zadanie P1 — Odbiór i test na realnym sprzęcie
`docs/AGENTY_PODWYKONAWCZE/ODBIOR_PROOT_EDGE_INSTALLER_2026-07-05.md` z kryteriami:
1. Test `--profile node-nsip` na realnym telefonie (Qualcomm Adreno preferowany).
2. Test `--profile desktop` na realnym telefonie + monitor (Synaptic z menu pokazuje okno polkit).
3. Weryfikacja `gpio-usb`, `gpio-http`, `gpio-mqtt` z dzielonym firmware ESP32 (endpoint JSON).
4. Wykonanie `RUNBOOK_PHANTOM_PROCESS_KILLER` — proot przeżywa >10 min.
5. Idempotentność — drugie uruchomienie `install.sh` nie psuje, raport z diff.
6. Migawka `/sdcard/NSIP/install-<data>.log` jako artefakt odbioru.

### Zadanie P2 — Firmware ESP32 GPIO endpoint (NOWE)
`docs/AGENTY_PODWYKONAWCZE/ZLECENIE_ESP32_GPIO_ENDPOINT_FIRMWARE.md` — firmware ESP32, który eksponuje endpoint GPIO kompatybilny z `gpio-usb`/`gpio-http`/`gpio-mqtt`/`gpio-ws` z instalatora:
- HTTP REST `/gpio?cmd=set&pin=N&value=V`,
- MQTT topic `esp32/<id>/gpio`,
- JSON-over-serial przez UART,
- WebSocket `ws://.../ws`,
- BLE GATT char.
Kryteria: działa z `gpio-usb`, `gpio-http`, `gpio-mqtt`; dokumentacja pinout; built-in test self-diagnostyka.

### Zadanie P3 — Tor A portfel KaCad/eksport (kontynuacja z PO_Z94)
Powrót do Portfela 24:
- **Z91** — eksport ecoEDA/NSIP z provenance CERN **tylko dla statusów `approved`**.
- **Z93** — smoke importera na realnym checkout CERN albo blocker receipt.
- **Z95** — roadmapa autonomicznej automatyzacji AI (gate, rollback, metryki).
- **Z92** (low) — polityka konwersji KiCad jako etap eksportu.

### Zadanie P4 — Roadmapa węzłów edge (NOWE, z Z95 pokejowane)
`docs/REKOMENDACJE_AUTONOMICZNEJ_AUTOMATYZACJI_AI_2026-05-14.md` rozbudować o warstwę edge: jak `straz-edge-installer` współgra z `ARCHITEKTURA_EDGE_SMARTFONY_CLOUD.md` (provider registration, write_token, observations/events). Model: każde smartfon-węzeł = provider w D1. Mapped do `MAPOWANIE_ENCJI_ORGANIZACJI_DO_D1_I_SQLITE.md`.

### Zadanie P5 — Auto-wznowienie Termux:Boot
Skrypt `~/.termux/boot/start-straz.sh` auto-podnosi `start-proot.sh` po restarcie telefonu; `termux-wake-lock`. Dodać jako opcjonalny krok w `install.sh` (flaga `--enable-boot`).

### Zadanie P6 — Test MPEG/zasięg
Weryfikacja Bluetooth stack (`bluez`, `python3-bleak`) na realnym telefonie — parowanie z ESP32-BLE, sent komend GPIO przez GATT.

## Priorytety (rekomendowane)

1. **P1** (odbiór installer na hardware) — bez tego zlecenie nie zamknięte.
2. **P2** (ESP32 firmware) — decouples węzeł od possessornowych runtime testów.
3. **P3** (Tor A KaCad) — powrót do głównego backlogu repo.
4. **P4** (roadmapa edge) — ustandaryzuje sposób integracji węzłów smartfonowych z centralą.
5. **P5** + **P6** — hardening węzła.

## Pliki kluczowe

- `straz-edge-installer/install.sh` — główny installer.
- `straz-edge-installer/lib/{common,proot,packages,gpio_bridge}.sh` — biblioteki.
- `straz-edge-installer/profiles/{node-nsip,desktop,gateway}.sh` — profile.
- `straz-edge-installer/scripts/{RUNBOOK_PHANTOM_PROCESS_KILLER.md,install-vscode-proot.sh}`.
- `straz-edge-installer/README.md` — dokumentacja instalatora.
- `docs/PROOT_LINUX_NA_SMARTFONACH_ANALIZA_SKRYPTOW.md` — analiza + sekcja sudo/polkit.
- `docs/AGENTY_PODWYKONAWCZE/ZLECENIE_GLOWNE_PROOT_EDGE_INSTALLER_STRAZY.md` — zlecenie + pełna lista pakietów.
- `docs/AGENTY_PODWYKONAWCZE/ODBIOR_PORTFELA_24_ZADANIE_94_2026-07-05.md` — odbiór Z94.

## Odniesienia do README/context

- Komputery sterownicze na starych smartfonach wspierają filar "upcyklingowany hardware".
- proot + GPIO/MQTT/wireless realizuje wzorzec bramek danych z `ARCHITEKTURA_EDGE_SMARTFONY_CLOUD.md`.
- `gpio-bridge` przygotowuje grunwei under `PROJEKTY/07_uniwersalna_platforma_sterowania.md` (USB/UART sterowanie aktuatorami).
- Synaptic z polkit (okno uprawnień) realizuje cel maintenera: w proot zachowanie jak w desktopowym Linuxie.
