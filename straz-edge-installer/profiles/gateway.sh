#!/data/data/com.termux/files/usr/bin/bash
# profiles/gateway.sh — bramka danych NSIP (headless, lekka)
# Smartfon jako bramka dla czujników ESP32/lokalnych do centrali: odbiera pomiary
# przez MQTT/HTTP/serial, buforuje, wysyła do API Straży. Brak GPIO sterowniczego.

source "$(dirname "$0")/../lib/common.sh"
source "$(dirname "$0")/../lib/proot.sh"
source "$(dirname "$0")/../lib/packages.sh"

TOTAL_STEPS=6
set_total_steps $TOTAL_STEPS

run_gateway() {
  echo -e "${BOLD}=== Profil: gateway (bramka danych NSIP headless) ===${NC}"

  # 1. Termux base
  update_progress
  install_pkg proot-distro "proot-distro"
  install_pkg proot "proot"

  # 2. proot distro
  update_progress
  proot_install_distro

  # 3. User + sudo
  update_progress
  proot_create_user_and_sudo

  # 4. Pakiety: MQTT + wireless + USB + net + base
  update_progress
  local pkgs
  pkgs=$(get_packages_for_profile gateway)
  proot_install_packages "$pkgs"

  # 5. mosquitto konfig (lokalny broker, listener na 1883)
  update_progress
  proot_exec '
    cat > /etc/mosquitto/conf.d/straz-edge.conf <<MOSQ
listener 1883
allow_anonymous true
persistence true
persistence_location /var/lib/mosquitto/
log_dest file /var/log/mosquitto/mosquitto.log
MOSQ
    mkdir -p /var/lib/mosquitto /var/log/mosquitto
    chown -R mosquitto:mosquitto /var/lib/mosquitto /var/log/mosquitto 2>/dev/null || true
  ' 2>/dev/null
  mkdir -p /sdcard/NSIP/observations /sdcard/NSIP/events 2>/dev/null || true
  echo -e "  ${GREEN}[+] mosquitto skonfigurowany (lokalny broker na :1883).${NC}"

  # 6. Skrypt startowy
  update_progress
  proot_write_start_script

  echo ""
  echo -e "${GREEN}[ Profil gateway gotowy. ]${NC}"
  echo -e "${BOLD}Start:${NC}  bash ~/start-proot.sh"
  echo -e "${BOLD}Broker MQTT:${NC}  lokalny 127.0.0.1:1883 (allow_anonymous)"
  echo -e "${BOLD}Bufor:${NC}  /nsip-data/observations/ (=/sdcard/NSIP)"
}
