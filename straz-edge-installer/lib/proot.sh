#!/data/data/com.termux/files/usr/bin/bash
# lib/proot.sh — setup kontenera proot z prawdziwym sudo + polkit + D-Bus
# Instalacja: proot-distro + debian/ubuntu, user z hasłem, sudo z AUTH_ADMIN, polkit GUI.

PROOT_DISTRO="${PROOT_DISTRO:-debian}"
PROOT_LABEL="${PROOT_LABEL:-Debian}"
PROOT_USERNAME="${PROOT_USERNAME:-straz}"
PROOT_USER_PASSWORD="${PROOT_USER_PASSWORD:-}"
PROOT_ROOT_PASSWORD="${PROOT_ROOT_PASSWORD:-}"
PROOT_ROOTFS="/data/data/com.termux/files/usr/var/lib/proot-distro/installed-rootfs/$PROOT_DISTRO"
PROOT_BIN="/data/data/com.termux/files/usr/bin/proot-distro"

proot_install_distro() {
  if [ -d "$PROOT_ROOTFS" ]; then
    echo -e "  ${CYAN}[skip] $PROOT_LABEL już zainstalowany.${NC}"
    return 0
  fi
  echo -e "${CYAN}[*] Instalowanie $PROOT_LABEL przez proot-distro...${NC}"
  if ! command -v "$PROOT_BIN" >/dev/null 2>&1; then
    install_pkg proot-distro "proot-distro"
  fi
  if ! "$PROOT_BIN" install "$PROOT_DISTRO"; then
    echo -e "${RED}[!] Instalacja $PROOT_LABEL nieudana. Sprawdź sieć i miejsce na dysku.${NC}"
    return 1
  fi
  echo -e "  ${GREEN}[+] $PROOT_LABEL gotowy.${NC}"
}

proot_exec() {
  # uruchom polecenie w proot jako root
  "$PROOT_BIN" login "$PROOT_DISTRO" -- bash -c "$1"
}

proot_exec_user() {
  # uruchom polecenie w proot jako user
  "$PROOT_BIN" login "$PROOT_DISTRO" --user "$PROOT_USERNAME" -- bash -lc "$1"
}

proot_create_user_and_sudo() {
  echo -e "${CYAN}[*] Tworzenie usera '$PROOT_USERNAME' z hasłem + sudo (AUTH)${NC}"
  [ -z "$PROOT_USER_PASSWORD" ] && PROOT_USER_PASSWORD=$(prompt_password "Hasło usera $PROOT_USERNAME")
  [ -z "$PROOT_ROOT_PASSWORD" ] && PROOT_ROOT_PASSWORD=$(prompt_password "Hasło root")

  proot_exec "
    # user (jeśli nie istnieje)
    if ! id '$PROOT_USERNAME' >/dev/null 2>&1; then
      useradd -m -s /bin/bash '$PROOT_USERNAME'
    fi
    echo '$PROOT_USERNAME:$PROOT_USER_PASSWORD' | chpasswd
    echo 'root:$PROOT_ROOT_PASSWORD' | chpasswd
    usermod -aG sudo '$PROOT_USERNAME' 2>/dev/null || true

    # sudo z hasłem (NIE NOPASSWD), ale !requiretty bo proot nie ma pełnego TTY
    mkdir -p /etc/sudoers.d
    cat > /etc/sudoers.d/straz-proot <<'SUDOERS'
Defaults !requiretty
$PROOT_USERNAME ALL=(ALL) ALL
SUDOERS
    chmod 0440 /etc/sudoers.d/straz-proot
    chmod u+s /usr/bin/sudo 2>/dev/null || true

    # domyślny shell prompt + aliasy
    cat >> /home/$PROOT_USERNAME/.bashrc <<'BASHRC'
export PS1='\[\033[01;32m\]$PROOT_USERNAME@straz\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ '
alias ll='ls -la'
alias update='sudo apt update && sudo apt upgrade -y'
alias install='sudo apt install -y'
BASHRC
    chown '$PROOT_USERNAME':'$PROOT_USERNAME' /home/$PROOT_USERNAME/.bashrc 2>/dev/null || true
  " 2>/dev/null
  echo -e "  ${GREEN}[+] User '$PROOT_USERNAME' gotowy z sudo (z hasłem).${NC}"
}

proot_install_packages() {
  # $1 — lista pakietów (spacja-separowane)
  local pkgs=$1
  echo -e "${CYAN}[*] Instalacja pakietów w proot: $pkgs${NC}"
  PROOT_ACTIVE=1 proot_exec "
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -y -q >/dev/null 2>&1
    apt-get install -y -q --no-install-recommends $pkgs
  " || {
    echo -e "  ${RED}[!] Instalacja pakietów nieudana: $pkgs${NC}"
    return 1
  }
  echo -e "  ${GREEN}[+] Pakiety zainstalowane: $pkgs${NC}"
}

proot_setup_polkit() {
  echo -e "${CYAN}[*] Konfiguracja polkit (okno uprawnień dla apt/Synaptic)${NC}"
  # policykit-1 + agent + reguła AUTH_ADMIN dla apt
  proot_install_packages "policykit-1 polkitd dbus"
  # agent GUI — wybór zależy od DE, tu gnome jako domyślny (lekki)
  proot_install_packages "policykit-1-gnome polkit-gnome-authentication-agent-1"

  proot_exec "
    mkdir -p /etc/polkit-1/rules.d
    cat > /etc/polkit-1/rules.d/49-straz-apt-auth.rules <<'POLKIT'
// apt wymaga autoryzacji admina (okno z hasłem), nie NOPASSWD
polkit.addRule(function(action, subject) {
    if (action.id.indexOf('org.debian.apt.') === 0 &&
        subject.isInGroup('sudo')) {
        return polkit.Result.AUTH_ADMIN;
    }
    return polkit.Result.NOT_HANDLED;
});
POLKIT
    chmod 0644 /etc/polkit-1/rules.d/49-straz-apt-auth.rules
  " 2>/dev/null
  echo -e "  ${GREEN}[+] polkit skonfigurowany (AUTH_ADMIN dla apt).${NC}"
}

proot_write_start_script() {
  # Generuje start-proot.sh z podniesieniem D-Bus + polkitd, potem su do usera
  local out="$HOME/start-proot.sh"
  cat > "$out" <<'PROOTEOF'
#!/data/data/com.termux/files/usr/bin/bash
PROOT_DISTRO="__PROOT_DISTRO__"
PROOT_USERNAME="__PROOT_USERNAME__"
PROOT_BIN="/data/data/com.termux/files/usr/bin/proot-distro"
TERMUX_TMP="${TMPDIR:-/data/data/com.termux/files/usr/tmp}"

echo ""
echo "============================================="
echo "  [*] Start $PROOT_DISTRO jako $PROOT_USERNAME"
echo "============================================="
echo ""

# Auto-install jeśli brak rootfs
ROOTFS_DIR="/data/data/com.termux/files/usr/var/lib/proot-distro/installed-rootfs/$PROOT_DISTRO"
if [ ! -d "$ROOTFS_DIR" ]; then
    echo "[!] $PROOT_DISTRO nie jest zainstalowany."
    read -p "    Zainstalować teraz? (Y/n): " _ans
    _ans=${_ans:-Y}
    if [[ "$_ans" =~ ^[Yy]$ ]]; then
        "$PROOT_BIN" install "$PROOT_DISTRO" || { echo "[!] Instalacja nieudana."; exit 1; }
    else
        echo "[!] Anulowano."; exit 1
    fi
fi

BINDS=""
[ -d "$TERMUX_TMP/.X11-unix" ] && BINDS="$BINDS --bind $TERMUX_TMP/.X11-unix:/tmp/.X11-unix"
[ -d "/dev/dri" ]              && BINDS="$BINDS --bind /dev/dri:/dev/dri"
[ -e "/dev/kgsl-3d0" ]         && BINDS="$BINDS --bind /dev/kgsl-3d0:/dev/kgsl-3d0"
# Bind GPIO/I2C/SPI urządzeń, jeśli Android je eksponuje (rzadkie; przez USB-serial częściej)
[ -d "/dev/i2c-0" ]            && BINDS="$BINDS --bind /dev/i2c-0:/dev/i2c-0"
[ -d "/dev/spidev0.0" ]        && BINDS="$BINDS --bind /dev/spidev0.0:/dev/spidev0.0"
# Tylko podkatalog NSIP z /sdcard
[ -d "/sdcard/NSIP" ]          && BINDS="$BINDS --bind /sdcard/NSIP:/nsip-data"
# Termux HOME dla wygody
BINDS="$BINDS --bind $HOME:/termux-home"

_RC=$(mktemp "$TERMUX_TMP/proot_rc.XXXX")
cat > "$_RC" <<'RCEOF'
export DISPLAY=:0
export MESA_NO_ERROR=1
export GALLIUM_DRIVER=zink
export XDG_RUNTIME_DIR=/tmp
export PS1='\[\033[01;32m\]straz@linux\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ '
echo ""
echo " User: $PROOT_USERNAME (sudo z hasłem) | GPU: ${GALLIUM_DRIVER}"
echo " Zarządzanie pakietami: sudo apt install <pkg> / Synaptic (okno uprawnień)"
echo " Wyjście: exit"
echo ""
RCEOF

# Najpierw podnieść D-Bus system bus + polkitd jako root, potem zrzucić do usera
exec "$PROOT_BIN" login "$PROOT_DISTRO" $BINDS --user root -- /bin/bash -c "
  mkdir -p /run/dbus /run/user 2>/dev/null
  dbus-daemon --system --fork 2>/dev/null || true
  /usr/lib/policykit-1/polkitd --no-debug 2>/dev/null &
  sleep 1
  exec su -l '$PROOT_USERNAME' -c 'bash --rcfile \$_RC'
" 2>/dev/null
rm -f "$_RC" 2>/dev/null
PROOTEOF

  # Podstaw zmienne
  sed -i "s|__PROOT_DISTRO__|$PROOT_DISTRO|g" "$out"
  sed -i "s|__PROOT_USERNAME__|$PROOT_USERNAME|g" "$out"
  # W RCEOF powyżej $PROOT_USERNAME rozwinie się — zabeić fakt, że chcemy literal:
  # poprawka: sed wstawia literalny $PROOT_USERNAME — to sed zadziała podwójnie.
  # Aby uniknąć: po utworzeniu substituuj marker:
  sed -i 's|\$PROOT_USERNAME (sudo|'"$PROOT_USERNAME"' (sudo|g' "$out"
  chmod +x "$out"
  echo -e "  ${GREEN}[+] Utworzono ~/start-proot.sh${NC}"
}

proot_setup_gpio_perm() {
  # Dodaj usera do grup mających dostęp do /dev/i2c-*, /dev/spidev*, /dev/gpiochip*
  proot_exec "
    groupadd -f i2c 2>/dev/null || true
    groupadd -f spi 2>/dev/null || true
    groupadd -f gpio 2>/dev/null || true
    groupadd -f dialout 2>/dev/null || true
    usermod -aG i2c,spi,gpio,dialout '$PROOT_USERNAME' 2>/dev/null || true
  " 2>/dev/null
  echo -e "  ${GREEN}[+] User dodany do grup i2c/spi/gpio/dialout.${NC}"
}
