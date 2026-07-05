#!/data/data/com.termux/files/usr/bin/bash
# scripts/install-vscode-proot.sh — VS Code INSTALL TYLKO W PROOT
# (Nie instaluj VS Code w Termuxie/TUR — działa gorzej niż w proot.)
# Uruchamia się po wykonaniu install.sh + start-proot.sh.
#
# Użycie: bash scripts/install-vscode-proot.sh [deep]
#   (bez arg)  — instancjuje proot z dostępem do apt i instaluje code-oss
#   deep        — instaluje pełny Microsoft VS Code z repo Microsoft (z validates GPG)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"
source "$SCRIPT_DIR/../lib/proot.sh"

PROOT_DISTRO="${PROOT_DISTRO:-debian}"
PROOT_USERNAME="${PROOT_USERNAME:-straz}"
PROOT_BIN="/data/data/com.termux/files/usr/bin/proot-distro"

mode=${1:-oss}

echo -e "${CYAN}[*] Instalacja VS Code w proot ($PROOT_DISTRO) — tryb: $mode${NC}"

if [ ! -d "/data/data/com.termux/files/usr/var/lib/proot-distro/installed-rootfs/$PROOT_DISTRO" ]; then
  echo -e "${RED}[!] $PROOT_DISTRO nie zainstalowany. Najpierw uruchom install.sh.${NC}"
  exit 1
fi

if [ "$mode" = "deep" ]; then
  # Pełny Microsoft VS Code (z repo, GPG key)
  proot_exec '
    apt-get install -y wget gpg ca-certificates
    wget -qO- https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > /usr/share/keyrings/microsoft-archive-keyring.gpg
    echo "deb [arch=arm64 signed-by=/usr/share/keyrings/microsoft-archive-keyring.gpg] https://packages.microsoft.com/repos/code stable main" \
      > /etc/apt/sources.list.d/vscode.list
    apt-get update
    apt-get install -y code
  ' || { echo -e "${RED}[!] Instalacja code (Microsoft) nieudana.${NC}"; exit 1; }
else
  # Open-source build (code-oss) — bez telemetrii, lekki
  proot_install_packages "code-oss gnupg" || { echo -e "${RED}[!] Instalacja code-oss nieudana.${NC}"; exit 1; }
fi

# Zapis wrapper menu-sync: VS Code w proot wymaga --no-sandbox (proot nie ma userns)
proot_exec "
  cat > /usr/share/applications/code.desktop <<EOF_DESKTOP
[Desktop Entry]
Name=VS Code
Comment=Visual Studio Code
Exec=/usr/local/bin/code-proot-launch %F
Icon=vscode
Type=Application
Categories=Development;IDE;
StartupWMClass=Code
EOF_DESKTOP

  cat > /usr/local/bin/code-proot-launch <<EOF_LAUNCH
#!/bin/bash
# Pod proot sandbox nie działa — --no-sandbox jest konieczny.
# --user-data-dir trzyma ustawienia w domu usera, nie w /root.
exec code-oss --no-sandbox --user-data-dir=\$HOME/.vscode \"\\\$@\"
EOF_LAUNCH
  chmod +x /usr/local/bin/code-proot-launch
" 2>/dev/null

echo -e "${GREEN}[+] VS Code zainstalowany w proot.${NC}"
echo -e "${BOLD}Uruchom:${NC}  bash ~/start-proot.sh  ->  code (albo menu XFCE)"
echo -e "${CYAN}    Wskazówka: ponownie zbuild listę menu proot do XFCE:${NC}"
echo -e "    bash ~/proot-menu-sync.sh $PROOT_DISTRO $PROOT_USERNAME"
