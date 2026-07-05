#!/data/data/com.termux/files/usr/bin/bash
# lib/common.sh — wspólne funkcje instalatora Straż Edge
# Idempotentne, z raportowaniem exit code, bez tłumienia błędów.

# Kolory ( tylko jeśli stdout to TTY )
if [ -t 1 ]; then
  RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
  BLUE='\033[0;34m'; CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'
else
  RED=''; GREEN=''; YELLOW=''; BLUE=''; CYAN=''; BOLD=''; NC=''
fi

CURRENT_STEP=0
TOTAL_STEPS=0

set_total_steps() { TOTAL_STEPS="$1"; }

update_progress() {
  CURRENT_STEP=$((CURRENT_STEP + 1))
  local percent=$((CURRENT_STEP * 100 / TOTAL_STEPS))
  local filled=$((percent / 5))
  local empty=$((20 - filled))
  local bar="${GREEN}"
  local i
  for ((i=0; i<filled; i++)); do bar+="*"; done
  bar+="${NC}"
  for ((i=0; i<empty; i++)); do bar+="-"; done
  echo ""
  echo -e "${BOLD}--- Step ${CURRENT_STEP}/${TOTAL_STEPS} ${bar} ${percent}% ---${NC}"
}

spinner() {
  local pid=$1; local msg=$2
  local spin='-\|/'; local i=0
  while kill -0 "$pid" 2>/dev/null; do
    i=$(( (i+1) % 4 ))
    printf "\r  [*] %s %s   " "$msg" "${spin:$i:1}"
    sleep 0.1
  done
  wait "$pid"
  local rc=$?
  if [ $rc -eq 0 ]; then
    printf "\r  [+] %-60s\n" "$msg"
  else
    printf "\r  ${RED}[!] %s (rc=%d)${NC}\n" "$msg" "$rc"
  fi
  return $rc
}

# install_pkg: instaluje pakiet Termux lub proot, zależnie od trybu.
#   install_pkg <pkg> [name]
# Raportuje exit code; nie tłumi outputu w log (zapis do /tmp-install.log).
install_pkg() {
  local pkg=$1
  local name=${2:-$pkg}
  local log="/tmp/install-${pkg//\//_}.log"
  # Wybierz menedżer: wewnątrz proot użyj apt-get; w Termux użyj pkg
  local mgr
  if [ -n "$PROOT_ACTIVE" ] && command -v apt-get >/dev/null 2>&1; then
    mgr="apt-get"
    (DEBIAN_FRONTEND=noninteractive apt-get install -y \
        -o Dpkg::Options::="--force-confold" "$pkg" > "$log" 2>&1) &
  elif command -v pkg >/dev/null 2>&1; then
    mgr="pkg"
    (pkg install -y "$pkg" > "$log" 2>&1) &
  else
    echo -e "  ${RED}[!] Brak menedżera pakietów (pkg/apt-get).${NC}"
    return 127
  fi
  spinner $! "Installing $name ($mgr)"
  local rc=$?
  if [ $rc -ne 0 ]; then
    echo -e "  ${RED}[!] $pkg FAILED. Log: $log${NC}"
    # W trybie nieinteraktywnym nie przerywamy; jeśli pakiet krytyczny — caller sprawdza.
  fi
  return $rc
}

assert_cmd_or_pkg() {
  local cmd=$1; local pkg=${2:-$1}
  if ! command -v "$cmd" >/dev/null 2>&1; then
    install_pkg "$pkg"
  fi
}

validate_username() {
  local name=$1
  if [[ ! "$name" =~ ^[a-z_][a-z0-9_-]*$ ]]; then
    echo -e "${RED}[!] Nieprawidłowa nazwa usera: '$name'.${NC}" >&2
    echo -e "${RED}    Dozwolone: małe litery, cyfry, _, -. Max 32 znaki.${NC}" >&2
    return 1
  fi
  if [ "${#name}" -gt 32 ]; then
    echo -e "${RED}[!] Nazwa usera za długa (max 32).${NC}" >&2
    return 1
  fi
  return 0
}

prompt_username() {
  local default=${1:-straz}
  local name
  while true; do
    read -rp "Nazwa usera w proot [default: $default]: " name
    name=${name:-$default}
    if validate_username "$name"; then
      echo "$name"
      return 0
    fi
  done
}

prompt_password() {
  local prompt=$1
  local pw
  while true; do
    read -rsp "$prompt: " pw
    echo
    if [ -z "$pw" ]; then
      echo -e "${RED}[!] Hasło nie może być puste.${NC}" >&2
      continue
    fi
    local pw2
    read -rsp "Potwierdź: " pw2
    echo
    if [ "$pw" != "$pw2" ]; then
      echo -e "${RED}[!] Hasła się różnią. Jeszcze raz.${NC}" >&2
      continue
    fi
    echo "$pw"
    return 0
  done
}

check_battery_and_warn() {
  local batt
  batt=$(cat /sys/class/power_supply/battery/capacity 2>/dev/null || echo "?")
  local plugged
  plugged=$(cat /sys/class/power_supply/battery/online 2>/dev/null || echo "0")
  echo -e "${CYAN}[*] Bateria: ${batt}%${NC}"
  if [ "${plugged:-0}" != "1" ] && [ "${batt:-100}" -lt 50 ] 2>/dev/null; then
    echo -e "${YELLOW}[!] Bateria < 50% i nie podłączone ładowarki.${NC}"
    echo -e "${YELLOW}    Instalacja może potrwać 10-30 min. Proszę podłączyć ładowarkę.${NC}"
    read -rp "Kontynuować? (y/N): " ans
    [[ "$ans" =~ ^[Yy]$ ]] || exit 1
  fi
}

detect_gpu() {
  local gpu
  gpu=$(getprop ro.hardware.egl 2>/dev/null || echo "")
  local brand
  brand=$(getprop ro.product.brand 2>/dev/null || echo "")
  if [[ "$gpu" == *"adreno"* ]] || \
     [[ "$brand" =~ [Ss]amsung|[Oo]ne[Pp]lus|[Xx]iaomi|[Rr]edmi|[Pp]oco|[Mm]oto|motorola ]]; then
    echo "freedreno"
  else
    echo "zink"
  fi
}

ensure_idempotent_marker() {
  # $1 — unikalny klucz kroku. Jeśli już wykonany, pomiń.
  local key=$1
  local marker="$HOME/.straz-edge/.done-${key}"
  if [ -f "$marker" ]; then
    echo -e "  ${CYAN}[skip] $key już wykonany.${NC}"
    return 0   # pomiń (caller powinien honorować)
  fi
  return 1     # wykonaj
}

mark_done() {
  local key=$1
  mkdir -p "$HOME/.straz-edge"
  touch "$HOME/.straz-edge/.done-${key}"
}
