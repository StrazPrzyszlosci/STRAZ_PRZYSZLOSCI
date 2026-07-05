# Odbiór Proot Edge Installer — 2026-07-05

## Kontekst

Zlecenie `ZLECENIE_GLOWNE_PROOT_EDGE_INSTALLER_STRAZY.md` — komputer sterowniczy na starym smartfonie z proot, Synaptic z oknem uprawnień, pakiety GPIO/MQTT/AI/wireless/USB, gpio-bridge klienci.

## Zakres odbioru

Implementacja w `straz-edge-installer/` (install.sh, lib/, profiles/, scripts/). Testy na realnym hardware jeszcze nie wykonane — ten dokument definiuje kryteria dla agenta wykonującego test.

## Checklist odbioru

### 1. Profilowane wykonanie na realnym telefonie

- [ ] `bash install.sh --profile node-nsip` wykonuje się end-to-end na Qualcomm Adreno (freedreno GPU).
- [ ] `bash install.sh --profile node-nsip` wykonuje się na MediaTek (zink fallback).
- [ ] `bash install.sh --profile desktop` wykonuje się end-to-end, XFCE startuje przez Termux-X11.
- [ ] `bash install.sh --profile gateway` — broker mosquitto startuje.

### 2. Proot działa jako user z sudo

- [ ] `bash ~/start-proot.sh` wchodzi do powłoki jako user.
- [ ] `sudo apt install sl` pyta o hasło usera (profil desktop), **nie** wyświetla `NOPASSWD`.
- [ ] W profilu node-nsip: `sudo apt install sl` działa (NOPASSWD akceptowalne).

### 3. Synaptic z oknem uprawnień (desktop)

- [ ] Synaptic uruchomiony z menu XFCE (po `proot-menu-sync.sh`) pokazuje okno polkit z prośbą o hasło root.
- [ ] `pkexec apt update` w proot (`start-proot.sh`) pokazuje okno polkit.
- [ ] `dbus-send --print-reply --dest=org.freedesktop.DBus /org/freedesktop/DBus org.freedesktop.DBus.ListNames` działa wewnątrz proot — potwierdza system bus.

### 4. GPIO bridge — sterowanie przez USB-serial

- [ ] ESP32 z firmware `esp32_gpio_endpoint` podłączony przez USB-OTG + FT232R.
- [ ] `gpio-usb /dev/ttyUSB0 set 12 1` ustawia pin 12 na wysoki poziom (multimetr/LED potwierdza).
- [ ] `gpio-usb /dev/ttyUSB0 get 12` zwraca `{"pin":12,"value":1}`.

### 5. GPIO bridge — sterowanie przez Wi-Fi

- [ ] ESP32 podłączony do tej samej sieci Wi-Fi co smartfon.
- [ ] `gpio-http <esp32_ip> set 13 0` ustawia pin 13 na niski (potwierdzone).
- [ ] `curl http://<esp32_ip>/info` zwraca prawidłowy JSON z device_id i safe_pins.

### 6. GPIO bridge — sterowanie przez MQTT

- [ ] Profil gateway: mosquitto broker działa lokalnie.
- [ ] `gpio-mqtt 127.0.0.1 esp32 esp32-test 12 1` ustawia pin 12 na wysoki.
- [ ] `mosquitto_sub -h 127.0.0.1 -t esp32/esp32-test/gpio/ack` odbiera potwierdzenie.

### 7. Idempotentność

- [ ] Drugie uruchomienie `bash install.sh --profile node-nsip` nie reinstaluje już zainstalowanych pakietów/baz (zostają `[skip]`).
- [ ] Bez markerów `.done-*`, diff w plikach (zapisywane przez `diff -r` przed/po) — zero zmian w krytycznych plikach systemowych.
- [ ] `/etc/sudoers.d/straz-proot` nie zmodyfikowany, `/etc/polkit-1/rules.d/49-straz-apt-auth.rules` niezmienny.

### 8. Phantom Process Killer

- [ ] Po wykonaniu `RUNBOOK_PHANTOM_PROCESS_KILLER.md` (adb z PC) smartfon nie ubiją proot przez >10 minut.
- [ ] `adb shell device_config get activity_manager max_phantom_processes` zwraca `2147483647`.

### 9. Brak glibc-repo, brak VS Code z TUR

- [ ] Po wykonaniu `install.sh` dla dowolnego profilu: `pkg list-installed` nie pokazuje `glibc-repo`, `glibc`, `code-oss` (z TUR).
- [ ] `bash scripts/install-vscode-proot.sh` instaluje VS Code w proot (nie w Termux) — `code` działa w proot (--no-sandbox).

### 10. Artefakty dla odbioru

- [ ] Migawka logów instalacji: `cp /sdcard/NSIP/install-<data>.log /tmp/straż-edge-odbior.log` i załącz do commitu witryny z odbioru.
- [ ] Screenshoty: XFCE desktop (desktop), okno polkit.
- [ ] Potwierdzenie `node --test tests/ecoeda_export_test.mjs tests/discord_kicad_actions_test.mjs tests/kicad_review_test.mjs` — wszystkie PASS.

## Verdict odbioru

| ID | Zakres | Status | Uwagi |
|----|--------|--------|-------|
| Proot Edge Installer | Installer + GPIO bridge + polkit + ESP32 firmware | PENDING | Potrzebuje testów na hardware (Qualcomm + MediaTek) |

Po wykonaniu checklist: zmień PENDING na PASS (z datą i nazwą agenta testera).

## Decyzja odbiorowa

Implementacja jest gotowa do testu na hardware. Bez testu odbiór nie zamknięty. Agent tester musi użyć 2 telefonów (Qualcomm + MediaTek) i ESP32 z firmware `esp32_gpio_endpoint`.