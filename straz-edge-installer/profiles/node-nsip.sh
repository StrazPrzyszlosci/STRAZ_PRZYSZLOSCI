#!/data/data/com.termux/files/usr/bin/bash
# profiles/node-nsip.sh — węzeł NSIP headless: komputer sterowniczy na proot
# Cel: smartfon steruje infrastrukturą (pompami, czujnikami, aktuatorami) przez
# USB-serial/USB-I2C do ESP32/MCU, MQTT do centrali, agenty NSIP w proot.
# Brak DE — mniejsza powierzchnia ataku, niższe zużycie energii.

source "$(dirname "$0")/../lib/common.sh"
source "$(dirname "$0")/../lib/proot.sh"
source "$(dirname "$0")/../lib/packages.sh"
source "$(dirname "$0")/../lib/gpio_bridge.sh"

TOTAL_STEPS=8
set_total_steps $TOTAL_STEPS

run_node_nsip() {
  echo -e "${BOLD}=== Profil: node-nsip (komputer sterowniczy headless) ===${NC}"
  echo -e "${BOLD}    GPIO sterowane: USB-serial + Wi-Fi(HTTP/MQTT/WS) + BT${NC}"

  # 1. Termux base (proot-distro)
  update_progress
  install_pkg proot-distro "proot-distro"
  install_pkg proot "proot"

  # 2. proot distro
  update_progress
  proot_install_distro

  # 3. User + sudo z hasłem (NOPASSWD NIE — operator wpisuje hasło)
  update_progress
  proot_create_user_and_sudo

  # 4. Pakiety z lib/packages.sh (base + GPIO + MQTT + AI + control + net + sys)
  update_progress
  local pkgs
  pkgs=$(get_packages_for_profile node-nsip)
  proot_install_packages "$pkgs"

  # 5. Grupy i2c/spi/gpio/dialout + reguły udev dla USB-serial
  update_progress
  proot_setup_gpio_perm
  # Reguły udev dla typowych konwerterów USB-serial (STM, FTDI, ch34x, cp210x)
  echo -e "${CYAN}[*] Reguły udev dla USB-serial (FTDI/CH341/CP210/STM)...${NC}"
  proot_exec '
    mkdir -p /etc/udev/rules.d
    cat > /etc/udev/rules.d/99-usb-serial.rules <<RULES
# Powszechne konwertery USB-serial dostępne dla grupy dialout
SUBSYSTEM=="tty", ATTRS{idVendor}=="0403", MODE="0666", GROUP="dialout"  # FTDI
SUBSYSTEM=="tty", ATTRS{idVendor}=="1a86", MODE="0666", GROUP="dialout"  # CH341
SUBSYSTEM=="tty", ATTRS{idVendor}=="10c4", MODE="0666", GROUP="dialout"  # CP210x
SUBSYSTEM=="tty", ATTRS{idVendor}=="0483", MODE="0666", GROUP="dialout"  # STM USB CDC
SUBSYSTEM=="usb", ATTRS{idVendor}=="1a86", ATTRS{idProduct}=="5512", MODE="0666", GROUP="i2c"  # CH341 I2C
RULES
    chmod 0644 /etc/udev/rules.d/99-usb-serial.rules
  ' 2>/dev/null
  echo -e "  ${GREEN}[+] Reguły udev gotowe (dialout/i2c).${NC}"

  # 6. Agent/bufor NSIP — placeholder (realna integracja w osobnym zleceniu)
  update_progress
  echo -e "${CYAN}[*] Setup katalogu bufora NSIP w /sdcard/NSIP...${NC}"
  mkdir -p /sdcard/NSIP/observations /sdcard/NSIP/events /sdcard/NSIP/logs 2>/dev/null || \
    echo -e "  ${YELLOW}[!] Nie udało się utworzyć /sdcard/NSIP — sprawdź uprawnienia Storage.${NC}"
  proot_exec '
    mkdir -p /nsip-data/observations /nsip-data/events /nsip-data/logs 2>/dev/null || true
    # Przykładowy system observatora w /usr/local/bin/nsip-collector
    cat > /usr/local/bin/nsip-collector <<COLLECTOR
#!/bin/bash
# Przykładowy kolektor obserwacji NSIP. Produkuje wiadomość JSON do bufora.
OUT=/nsip-data/observations/\$(date +%Y%m%d-%H%M%S)-\$RANDOM.json
TS=\$(date -u +%FT%TZ)
HOST=\$(hostname)
TMP=\${TMPDIR:-/tmp}/cpu-\$\$.txt
cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null | head -1 > "\$TMP" || true
echo "{\"timestamp\":\"\$TS\",\"host\":\"\$HOST\",\"thermal\":\"\$(cat \$TMP 2>/dev/null)\"}" > "\$OUT"
rm -f "\$TMP"
COLLECTOR
    chmod +x /usr/local/bin/nsip-collector
  ' 2>/dev/null
  echo -e "  ${GREEN}[+] nsip-collector (placeholder) zainstalowany.${NC}"

  # 7. Skrypt startowy proot
  update_progress
  proot_write_start_script

  # 8. gpio-bridge examples (USB-serial, HTTP, MQTT, WS, BLE klienty)
  update_progress
  proot_install_gpio_examples

  echo ""
  echo -e "${GREEN}[ Profil node-nsip gotowy. ]${NC}"
  echo -e "${BOLD}Start:${NC}  bash ~/start-proot.sh"
  echo -e "${BOLD}Zarządzanie pakietami:${NC}  sudo apt install <pkg>"
  echo -e "${BOLD}Test GPIO/serial:${NC}  python3 -c 'import serial; print(serial.__version__)'"
  echo -e "${BOLD}Sterowanie GPIO:${NC}  gpio-usb /dev/ttyUSB0 set 12 1"
  echo -e "${BOLD}     (Wi-Fi):  ${NC}  gpio-http 192.168.4.1 set 12 1"
  echo -e "${BOLD}     (MQTT):  ${NC}  gpio-mqtt 127.0.0.1 esp32 node-1 12 1"
}
