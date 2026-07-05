# ZLECENIE GŁÓWNE — Proot Edge Installer Straży (komputer sterowniczy na starym smartfonie)

## Cel

Stare smartfony jako **komputery sterownicze na Linuksie** przez Termux + proot. Smartfon steruje infrastrukturą NSIP (pompami, czujnikami, aktuatorami) przez endpoint GPIO na ESP32/MCU — USB-serial (UART) **lub** Wi-Fi (HTTP/MQTT/WebSocket) **lub** Bluetooth. Instalator ma zainstalować od razu proot, Synaptic (z oknem uprawnień), oraz pakiety potrzebne do sterowania GPIO/I2C/SPI/UART.

## Powiązania

- [../PROOT_LINUX_NA_SMARTFONACH_ANALIZA_SKRYPTOW.md](../PROOT_LINUX_NA_SMARTFONACH_ANALIZA_SKRYPTOW.md)
- [../../straz-edge-installer/](../../straz-edge-installer/) — gotowy installer
- [../../PROJEKTY/06_smartfony_jako_sterowniki.md](../../PROJEKTY/06_smartfony_jako_sterowniki.md)

## Status

DONE (2026-07-05) — implementacja w `straz-edge-installer/`. Wykonane przez bieżącego agenta. Odbiór: utworzyć `ODBIOR_PROOT_EDGE_INSTALLER_2026-07-05.md` po testach na realnym hardware.

## Co zaimplementowano

`straz-edge-installer/`:
- `install.sh` — wybór profilu (`--profile node-nsip|desktop|gateway`), wybór distro (debian/ubuntu/kali), walidacja username, warning baterii, runbook Phantom Killer.
- `lib/common.sh` — `install_pkg` z raportowaniem exit code, spinner, `validate_username`, `prompt_username`/`prompt_password`, `check_battery_and_warn`, `detect_gpu`, idempotentność markery.
- `lib/proot.sh` — `proot_install_distro`, `proot_create_user_and_sudo` (sudo z hasłem, `!requiretty`, `NOPASSWD` usuwane), `proot_setup_polkit` (D-Bus system bus + polkitd + reguła `AUTH_ADMIN` dla apt), `proot_write_start_script` (podnoszenie daemonów jako root → `su -l user`), `proot_setup_gpio_perm` (grupy i2c/spi/gpio/dialout).
- `lib/packages.sh` — listy pakietów według filarów (patrz niżej).
- `lib/gpio_bridge.sh` — skrypty klienty sterowania GPIO: `gpio-usb`, `gpio-http`, `gpio-mqtt`, `gpio-ws`, `gpio-ble`, konfig `/etc/straz-edge/gpio-bridge.env`, reguły udev dla USB-serial (FTDI/CH341/CP210/STM).
- `profiles/node-nsip.sh` — headless, 8 kroków, GPIO sterowniczy + wireless + USB + MQTT + AI.
- `profiles/desktop.sh` — XFCE + Termux-X11 + polkit + Synaptic przez `pkexec`, 11 kroków.
- `profiles/gateway.sh` — bramka MQTT, 6 kroków.
- `scripts/RUNBOOK_PHANTOM_PROCESS_KILLER.md` — runbook Android 13+.
- `scripts/install-vscode-proot.sh` — VS Code TYLKO w proot (`code-oss` lub pełny Microsoft).
- `README.md` — pełna dokumentacja.

## Kryteria odbioru

1. `install.sh --profile node-nsip` działa end-to-end na realnym telefonie, proot odpala jako user z `sudo` (pyta o hasło).
2. ` développment.sh --profile desktop` uruchamia XFCE, Synaptic z menu pokazuje okno polkit.
3. `gpio-usb /dev/ttyUSB0 set 12 1` steruje pinem na ESP32 (firmware z endpointem JSON).
4. `gpio-http 192.168.4.1 set 12 1` steruje przez Wi-Fi.
5. `gpio-mqtt 127.0.0.1 esp32 node-1 12 1` steruje przez MQTT.
6. Idempotentność — ponowne uruchomienie `install.sh` nie psuje.
7. Runbook Phantom Killer wykonany — proot przeżywa >10 min.
8. Brak `glibc-repo`, brak VS Code z TUR.
9. Test na 2 telefonach: Qualcomm Adreno (freedreno) + MediaTek (zink fallback).

## Rekomendowana lista pakietów (jedna lista dla Straży)

Zorganizowana przez filary w `lib/packages.sh`. Pełna lista poniżej.

### Base (wszystkie profile)
`sudo curl wget git htop nano less ca-certificates gnupg locales tzdata bash-completion man-db unzip zip rsync sqlite3 cron anacron tmux`

### GPIO / I2C / SPI / UART (sterowanie z poziomu Linuxa)
`libgpiod2 libgpiod-dev i2c-tools spi-tools python3-libgpiod python3-smbus python3-spidev pyserial python3-serial setserial minicom picocom`

### Komunikacja bezprzewodowa (Wi-Fi/BT)
`bluez bluez-tools python3-dbus python3-bleak python3-pybluez rfkill python3-requests python3-websockets python3-aiohttp python3-asyncio-mqtt avahi avahi-utils`

### Sterowniki USB (serial/I2C/SPI bridge)
`usbutils udev python3-usb python3-pyftdi python3-pylibftdi libftdi-dev libftdi1`

### MQTT / IoT
`mosquitto mosquitto-clients python3-paho-mqtt libmosquitto-dev libpaho-mqtt-dev`

### AI / ML edge (lekki)
`python3 python3-pip python3-venv python3-numpy python3-pandas python3-requests python3-yaml python3-jinja2`

### Sieć / węzeł
`openssh-client openssh-server iproute2 iputils-ping dnsutils network-manager net-tools traceroute tcpdump nmap wireguard-tools curl`

### System / utrzymanie
`logrotate rsyslog udev systemd-sysv dbus policykit-1`

### Pomoce sterownicze (GPIO endpoint)
`python3-pyftdi python3-adafruit-blinka python3-rpi-lgpio python3-periphery python3-serial python3-can python3-websockets python3-asyncio-mqtt`

### Desktop (profil desktop, w proot)
`synaptic gdebi policykit-1-gnome polkit-gnome-authentication-agent-1 gnome-keyring seahorse network-manager-gnome`

### Raporty / wizualizacja
`python3-matplotlib python3-pillow graphviz plantuml`

### VS Code (opcjonalnie, TYLKO w proot)
`code-oss gnupg` (lub pełny `code` z repo Microsoft — `scripts/install-vscode-proot.sh deep`)

## Endpoint GPIO na ESP32 (kontrakt)

Installer dostarcza klienty. ESP32 musi eksponować endpoint JSON — jeden z:

**HTTP REST:**
```
GET  /gpio?cmd=get&pin=12            → {"pin":12,"value":1}
POST /gpio?cmd=set&pin=12&value=0    → {"ok":true,"pin":12,"value":0}
```

**Serial (UART, JSON-over-serial):**
```
TX: {"cmd":"set","pin":12,"value":1}\n
RX: {"pin":12,"value":1}\n
```

**MQTT:**
```
topic: esp32/<id>/gpio
payload: {"pin":12,"value":1}
```

Firmware ESP32 z tymi endpointami — osobne zlecenie (np. `ZLECENIE_ESP32_GPIO_ENDPOINT_FIRMWARE`).

## Decyzje bezpieczeństwa

- `sudo` z hasłem + polkit (desktop); `NOPASSWD: all` tylko headless.
- Bind `/sdcard` ograniczony do `/sdcard/NSIP`.
- Bez `glibc-repo`, bez VS Code z TUR.
- User w grupach `i2c,spi,gpio,dialout`; reguły udev dla USB-serial.
- polkit reguła `AUTH_ADMIN` dla `org.debian.apt.*` — okno uprawnień jak na desktopowym Linuxie.

## Najlepszy następny krok

Utworzyć `ZLECENIE_ESP32_GPIO_ENDPOINT_FIRMWARE` — firmware ESP32 z endpointem HTTP+MQTT+serial do sterowania GPIO, kompatybilny z `gpio-usb`/`gpio-http`/`gpio-mqtt` z tego instalatora.
