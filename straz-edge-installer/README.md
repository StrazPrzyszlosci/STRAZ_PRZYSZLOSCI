# Straż Edge Installer

Linux na starym smartfonie przez Termux + proot — **komputer sterowniczy** dla projektów Straży Przyszłości. Smartfon steruje infrastrukturą (pompami, czujnikami, aktuatorami) przez endpoint GPIO na ESP32/MCU — USB-serial lub Wi-Fi (HTTP/MQTT/WebSocket) albo Bluetooth.

## Cel

Nie budujemy „desktopa na telefonie”. Stare smartfony stają się **węzłami sterującymi NSIP** na pełnoprawnym Linuksie (proot), z dostępem do GPIO, I2C, SPI, UART, MQTT, AI edge. Termux to tylko warstwa startowa — proot jest operacyjnym środowiskiem.

Powiązane dokumenty:
- [../docs/ARCHITEKTURA_EDGE_SMARTFONY_CLOUD.md](../docs/ARCHITEKTURA_EDGE_SMARTFONY_CLOUD.md)
- [../docs/PROOT_LINUX_NA_SMARTFONACH_ANALIZA_SKRYPTOW.md](../docs/PROOT_LINUX_NA_SMARTFONACH_ANALIZA_SKRYPTOW.md)
- [../PROJEKTY/06_smartfony_jako_sterowniki.md](../PROJEKTY/06_smartfony_jako_sterowniki.md)

## Wymagania

- Android (ARM64), Termux z F-Droid (NIE Play Store)
- Profil `desktop` dodatkowo: aplikacja Termux-X11 (nightly)
- ~3 GB wolnego miejsca (proot rootfs + pakiety)
- Podłączona ładowarka zalecana przy instalacji

## Szybki start (w Termuxie)

```bash
git clone <repo> straz-edge-installer
cd straz-edge-installer

# Interaktywnie (zapyta o profil, username, hasła):
bash install.sh

# Bez interakcji:
bash install.sh --profile node-nsip    # headless, GPIO sterowniczy (zalecany)
bash install.sh --profile desktop      # XFCE + Synaptic + polkit
bash install.sh --profile gateway      # bramka MQTT
bash install.sh --profile node-nsip --distro ubuntu
```

## Profile

### `node-nsip` (zalecany dla węzłów NSIP)
Headless komputer sterowniczy. Instaluje:
- proot Debian/Ubuntu, usera z `sudo` (z hasłem, nie NOPASSWD),
- GPIO: `libgpiod`, `i2c-tools`, `spi-tools`, `pyserial`, `python3-smbus`, `python3-spidev`,
- Komunikacja bezprzewodowa: `bluez`, `python3-bleak` (BLE), `python3-websockets`, `avahi`,
- USB-bridge: `usbutils`, `python3-usb`, `python3-pyftdi` (FT232R/CH341/CP210x),
- MQTT: `mosquitto-clients`, `python3-paho-mqtt`,
- AI edge: Python + numpy/pandas/ONNX-runtime,
- Sterowanie GPIO: gotowe skrypty `gpio-usb`, `gpio-http`, `gpio-mqtt`, `gpio-ws`, `gpio-ble` w `/usr/local/bin`,
- Bufor obserwacji NSIP: `/sdcard/NSIP` (bind do `/nsip-data` w proot).

### `desktop`
Dodatkowo `node-nsip` + XFCE4, Termux-X11, polkit (okno uprawnień dla Synaptic/apt), Synaptic przez `pkexec` (uruchamiany z menu bez `sudo` — polkit pyta o hasło roota), PulseAudio. Dla operatora z monitorem (USB-C HDMI albo Pi Bridge).

### `gateway`
Bramka danych: lokalny broker mosquitto (`127.0.0.1:1883`), odbiera pomiary od ESP32, buforuje do `/sdcard/NSIP`, wysyła do centrali. Brak GPIO sterowniczego.

## Sterowanie GPIO

Smartfon steruje GPIO na ESP32/MCU przez kilka kanałów (po uruchomieniu `bash ~/start-proot.sh`):

| Kanał | Skrypt | Przykład |
|-------|--------|----------|
| USB-serial (UART) | `gpio-usb` | `gpio-usb /dev/ttyUSB0 set 12 1` |
| Wi-Fi HTTP REST | `gpio-http` | `gpio-http 192.168.4.1 set 12 1` |
| MQTT | `gpio-mqtt` | `gpio-mqtt 127.0.0.1 esp32 node-1 12 1` |
| WebSocket | `gpio-ws` | `gpio-ws ws://192.168.4.1/ws 12 1` |
| Bluetooth LE | `gpio-ble` | `gpio-ble AA:BB:CC:DD:EE:FF <uuid> 12 1` |

Konfiguracja: `/etc/straz-edge/gpio-bridge.env` (ustal domyślny kanał + parametry).

ESP32 powinien eksponować endpoint JSON. Przykładowy kontrakt (HTTP):
```
GET  /gpio?cmd=get&pin=12          → {"pin":12,"value":1}
POST /gpio?cmd=set&pin=12&value=0  → {"ok":true,"pin":12,"value":0}
```

## Prawdziwe sudo i okno uprawnień (profil desktop)

W proot masz pełne `sudo` z hasłem — jak w desktopowym Linuxie:
- Terminal: `sudo apt install <pkg>` pyta o hasło usera.
- Synaptic z menu: uruchamiany przez `pkexec` (polkit pokazuje okno z prośbą o hasło root).
- Skrypty proot to tylko cienka warstwa — polityka w `/etc/sudoers.d/straz-proot` i `/etc/polkit-1/rules.d/49-straz-apt-auth.rules`.

Konfiguracja polkit: D-Bus system bus + `polkitd` podnoszone w `start-proot.sh` jako root, potem `su -l <user>`.

## Post-instalacja (OBOWIĄZKOWE)

Android 13+ ubija proot (`signal 9`). Wykonaj raz z PC przez ADB:

```bash
adb shell "/system/bin/device_config put activity_manager max_phantom_processes 2147483647"
```

Pełny runbook: [scripts/RUNBOOK_PHANTOM_PROCESS_KILLER.md](scripts/RUNBOOK_PHANTOM_PROCESS_KILLER.md).

Dodatkowo: Ustawienia → aplikacja Termux → Bateria → **Bez ograniczeń**.

## VS Code (opcjonalnie, TYLKO w proot)

Nie instaluj VS Code w Termuxie/TUR — działa gorzej. Po instalacji:

```bash
bash scripts/install-vscode-proot.sh        # code-oss (lekki, bez telemetrii)
bash scripts/install-vscode-proot.sh deep   # pełny Microsoft VS Code z repo
```

## Idempotentność

Skrypty honorują markery w `~/.straz-edge/.done-*` — ponowne uruchomienie nie psuje instalacji. Można bezpiecznie uruchomić `bash install.sh` drugi raz.

## Struktura

```
straz-edge-installer/
├── install.sh              # główny: wybór profilu, konfiguracja
├── lib/
│   ├── common.sh           # spinner, install_pkg z rc, walidacja
│   ├── proot.sh            # user + sudo + polkit + D-Bus
│   ├── packages.sh         # listy pakietów według filarów
│   └── gpio_bridge.sh      # gpio-usb/http/mqtt/ws/ble klienci
├── profiles/
│   ├── node-nsip.sh        # headless, GPIO sterowniczy
│   ├── desktop.sh          # XFCE + polkit + Synaptic
│   └── gateway.sh          # bramka MQTT
└── scripts/
    ├── install-vscode-proot.sh
    └── RUNBOOK_PHANTOM_PROCESS_KILLER.md
```

## Szczegóły bezpieczeństwa

- `sudo` z hasłem ( profil desktop), `NOPASSWD: ALL` tylko headless (`node-nsip/gateway`).
- Bind `/sdcard` ograniczony do `/sdcard/NSIP` (nie cała pamięć).
- `termux-x11 :0 -ac` — na smartfonie jednoużytkownikowym akceptowalne; profil desktop operatora.
- polkit reguła `AUTH_ADMIN` dla `org.debian.apt.*` wymusza okno z hasłem — jak desktop Linux.
- User dodany do grup `i2c`, `spi`, `gpio`, `dialout` w proot.

## Status

- **Impl. gotowa:** modułar instalator z 3 profilami, full pakietów GPIO/MQTT/AI/wireless/USB, gpio-bridge examples, polkit, runbook Phantom Killer, VS Code w proot.
- **Do weryfikacji:** test na 2 realnych telefonach (Qualcomm Adreno + MediaTek), integracja z realnym ESP32 (firmware z endpointem GPIO), auto-wznowienie przez Termux:Boot.
