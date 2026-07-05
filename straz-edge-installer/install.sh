#!/data/data/com.termux/files/usr/bin/bash
# ============================================================
#  Straż Edge Installer — Linux na starym smartfonie przez proot
#  Komputer sterowniczy dla projektów Straży Przyszłości
#
#  Profile:
#    node-nsip  — headless, sterowanie GPIO (USB/Wi-Fi/BT) + agenty NSIP
#    desktop    — XFCE + Synaptic z oknem uprawnień (polkit) + GPIO
#    gateway    — bramka danych (MQTT broker + bufor do API Straży)
#
#  Użycie:
#    bash install.sh                 # interaktywny wybór profilu
#    bash install.sh --profile node-nsip
#    bash install.sh --profile desktop
#    bash install.sh --profile gateway
# ============================================================

set -u

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

PROFILE=""
PROOT_DISTRO_DEFAULT="debian"
DESKIP_PHANTOM_WARNING=0
ENABLE_BOOT=0

print_banner() {
  cat <<'BANNER'
   ╔══════════════════════════════════════════╗
   ║   Straż Edge Installer                    ║
   ║   Linux na starym smartfonie przez proot  ║
   ╚══════════════════════════════════════════╝
BANNER
}

print_help() {
  cat <<'EOF'
Straż Edge Installer

Użycie:
  bash install.sh [opcja]

Opcje:
  --profile <nazwa>   Wybierz profil bez interakcji:
                         node-nsip  (headless, GPIO sterowniczy)
                         desktop    (XFCE + Synaptic + polkit)
                         gateway    (bramka danych MQTT/API)
  --distro <nazwa>    Wybierz dystrybucję proot: debian (domyślnie), ubuntu, kali
  --enable-boot     Skopiuj skrypt auto-wznowienia do ~/.termux/boot/ (Termux:Boot)
      --help              Ten ekran

Profil domyślny dla węzłów NSIP: node-nsip (lekki, sterowania GPIO przez
USB-serial/Wi-Fi(HTTP,MQTT,WebSocket)/Bluetooth, brak DE).
EOF
}

parse_args() {
  while [ $# -gt 0 ]; do
    case "$1" in
      --profile) PROFILE="$2"; shift 2;;
      --profile=*) PROFILE="${1#*=}"; shift;;
      --distro) PROOT_DISTRO_DEFAULT="$2"; shift 2;;
      --distro=*) PROOT_DISTRO_DEFAULT="${1#*=}"; shift;;
      --help|-h) print_help; exit 0;;
      --enble-boot) ENABLE_BOOT=1; shift;;
      *) echo -e "${RED}[!] Nieznana opcja: $1${NC}"; print_help; exit 1;;
    esac
  done
}

prompt_profile() {
  echo -e "${CYAN}Wybierz profil instalacji:${NC}"
  echo -e "  ${BOLD}1) node-nsip${NC}  — headless, komputer sterowniczy (GPIO przez USB/Wi-Fi/BT). Zalecany."
  echo -e "  ${BOLD}2) desktop${NC}    — XFCE + Synaptic z oknem uprawnień (polkit), dla operatora z monitorem."
  echo -e "  ${BOLD}3) gateway${NC}    — bramka danych MQTT, lekka."
  echo ""
  local choice
  while true; do
    read -rp "Wybierz (1-3) [default: 1]: " choice
    choice=${choice:-1}
    case "$choice" in
      1) PROFILE=node-nsip; break;;
      2) PROFILE=desktop; break;;
      3) PROFILE=gateway; break;;
      *) echo "Wpisz 1, 2 albo 3.";;
    esac
  done
  echo -e "${GREEN}[+] Wybrano profil: $PROFILE${NC}"
}

main() {
  parse_args "$@"
  print_banner

  # Wymagania (w Termux)
  if [ ! -d "/data/data/com.termux" ]; then
    echo -e "${RED}[!] Skrypt musi być uruchomiony w Termuxie, nie w proot ani na PC.${NC}"
    exit 1
  fi

  check_battery_and_warn

  # Phantom Killer — wstępne ostrzeżenie
  echo -e "${YELLOW}[!] WAŻNE: Android 13+ ubija proot (signal 9).${NC}"
  echo -e "${YELLOW}    Po instalacji wykonaj RUNBOOK_PHANTOM_PROCESS_KILLER.md${NC}"
  echo -e "${YELLOW}    (adb shell device_config put activity_manager max_phantom_processes 2147483647)${NC}"
  echo ""

  # Wybór profilu jeśli nie podano
  if [ -z "$PROFILE" ]; then
    prompt_profile
  fi
  case "$PROFILE" in
    node-nsip|desktop|gateway) ;;
    *) echo -e "${RED}[!] Nieznany profil: $PROFILE${NC}"; exit 1;;
  esac

  # Reszta konfiguracji (username, distro)
  export PROOT_DISTRO="$PROOT_DISTRO_DEFAULT"
  case "$PROOT_DISTRO" in
    debian) export PROOT_LABEL="Debian 12";;
    ubuntu) export PROOT_LABEL="Ubuntu 22.04";;
    kali)   export PROOT_LABEL="Kali Linux";;
    *) echo -e "${RED}[!] Nieobsługiwana distro: $PROOT_DISTRO (użyj debian/ubuntu/kali)${NC}"; exit 1;;
  esac

  echo -e "${CYAN}[*] Distro proot: $PROOT_LABEL${NC}"

  # Username
  export PROOT_USERNAME
  PROOT_USERNAME=$(prompt_username straz)

  # Start odpowiedniego profilu
  echo ""
  case "$PROFILE" in
    node-nsip)
      source "$SCRIPT_DIR/profiles/node-nsip.sh"
      run_node_nsip
      ;;
    desktop)
      local gpu
      gpu=$(detect_gpu)
      echo -e "${CYAN}[*] GPU: $gpu${NC}"
      source "$SCRIPT_DIR/profiles/desktop.sh"
      run_desktop "$gpu"
      ;;
    gateway)
      source "$SCRIPT_DIR/profiles/gateway.sh"
      run_gateway
      ;;
  esac

  # Postinstall wskazówki
  echo ""
  echo -e "${BOLD}=== POSTINSTALACJA ===${NC}"
  echo -e "  1. Wykonaj ${BOLD}RUNBOOK_PHANTOM_PROCESS_KILLER${NC} (adb z PC):"
  echo -e "     adb shell \"/system/bin/device_config put activity_manager max_phantom_processes 2147483647\""
  echo -e "  2. Włącz Termux: Battery → Bez ograniczeń (Ustawienia aplikacji)"
  echo -e "  3. Opcjonalnie: VS Code w proot:"
  echo -e "     bash $SCRIPT_DIR/scripts/install-vscode-proot.sh"
  echo -e "  4. Start: ${BOLD}bash ~/start-proot.sh${NC}"
  echo ""
  if [ "$ENABLE_BOOT" != "0" ]; then
    echo -e "${CYAN}[*] Kopiowanie skryptu auto-wznowienia do ~/.termux/boot/...${NC}"
    mkdir -p "$HOME/.termux/boot"
    cp "$SCRIPT_DIR/scripts/start-straz-boot.sh" "$HOME/.termux/boot/start-straz-boot.sh" 2>/dev/null && \
      echo -e "  ${GREEN}[+] ~/.termux/boot/start-straz-boot.sh gotowy.${NC}" || \
      echo -e "  ${RED}[!] Nie udało się skopiować.${NC}"
    echo -e "  ${BOLD}   Wymagane: zainstaluj Termux:Boot z F-Droid.${NC}"
  fi
  echo ""
  echo -e "${GREEN}[ Gotowe. Inteligencja przewaada kapitał! ]${NC}"
}

main "$@"
