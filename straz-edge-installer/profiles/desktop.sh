#!/data/data/com.termux/files/usr/bin/bash
# profiles/desktop.sh — komputer sterowniczy z graficznym interfejsem (XFCE + polkit)
# Smartfon jako desktop Linux na monitorze (USB-C HDMI lub Pi Bridge), z Synaptic
# uruchamianym z menu i oknem uprawnień polkit. VS Code opcjonalnie w proot.

source "$(dirname "$0")/../lib/common.sh"
source "$(dirname "$0")/../lib/proot.sh"
source "$(dirname "$0")/../lib/packages.sh"
source "$(dirname "$0")/../lib/gpio_bridge.sh"

TOTAL_STEPS=11
set_total_steps $TOTAL_STEPS

run_desktop() {
  local gpu=$1
  echo -e "${BOLD}=== Profil: desktop (komputer sterowniczy + XFCE + polkit) ===${NC}"
  echo -e "${BOLD}    GPIO sterowane: USB-serial + Wi-Fi(HTTP/MQTT/WS) + BT${NC}"

  # 1. Termux: update + repo x11 / tur
  update_progress
  install_pkg x11-repo "x11-repo"
  install_pkg tur-repo "tur-repo"

  # 2. Termux-X11 + DE (XFCE4)
  update_progress
  install_pkg termux-x11-nightly "Termux-X11"
  install_pkg xorg-xrandr "XRandR"
  install_pkg xfce4 "XFCE4 Desktop"
  install_pkg xfce4-terminal "XFCE4 Terminal"
  install_pkg xfce4-whiskermenu-plugin "Whisker Menu"
  install_pkg thunar "Thunar"
  install_pkg mousepad "Mousepad"

  # 3. GPU (Turnip dla Adreno / Zink fallback)
  update_progress
  install_pkg mesa-zink "Mesa Zink"
  if [ "$gpu" = "freedreno" ]; then
    install_pkg mesa-vulkan-icd-freedreno "Turnip Adreno"
  fi
  install_pkg vulkan-loader-android "Vulkan Loader Android"
  install_pkg pulseaudio "PulseAudio"

  # 4. proot distro
  update_progress
  install_pkg proot-distro "proot-distro"
  install_pkg proot "proot"
  proot_install_distro

  # 5. User + sudo z hasłem
  update_progress
  proot_create_user_and_sudo

  # 6. Pakiety w proot (base + GPIO + MQTT + AI + control + desktop_proot + polkit)
  update_progress
  local pkgs
  pkgs=$(get_packages_for_profile desktop)
  proot_install_packages "$pkgs"

  # 7. polkit (okno uprawnień dla Synaptic/apt)
  update_progress
  proot_setup_polkit

  # 8. Grupy gpio + autostart agenta autoryzacji
  update_progress
  proot_setup_gpio_perm
  echo -e "${CYAN}[*] Autostart agenta polkit-gnome w sesji XFCE...${NC}"
  mkdir -p "$HOME/.config/autostart"
  cat > "$HOME/.config/autostart/polkit-gnome.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=PolicyKit Authentication Agent
Exec=/usr/lib/policykit-1-gnome/polkit-gnome-authentication-agent-1
X-GNOME-Autostart-enabled=true
NoDisplay=true
EOF
  echo -e "  ${GREEN}[+] Autostart polkit-gnome zapisany.${NC}"

  # 9. Skrypt start-proot.sh + start-x11.sh
  update_progress
  proot_write_start_script

  # start-x11.sh
  local out="$HOME/start-x11.sh"
  cat > "$out" <<X11EOF
#!/data/data/com.termux/files/usr/bin/bash
echo "[*] Start XFCE przez Termux-X11..."
source ~/.config/linux-gpu.sh 2>/dev/null || true
export USER="$PROOT_USERNAME"
export LOGNAME="$PROOT_USERNAME"
export HOSTNAME="straz-edge"
export HOST="straz-edge"
pkill -9 -f "termux.x11" 2>/dev/null
unset PULSE_SERVER
pulseaudio --kill 2>/dev/null; sleep 0.5
pulseaudio --start --exit-idle-time=-1; sleep 1
export PULSE_SERVER=127.0.0.1
termux-x11 :0 -ac &
sleep 3
export DISPLAY=:0
[ -f ~/proot-menu-sync.sh ] && bash ~/proot-menu-sync.sh "$PROOT_DISTRO" "$PROOT_USERNAME" >/dev/null 2>&1 &
echo "[*] Otwórz aplikację Termux-X11 aby zobaczyć desktop."
exec startxfce4
X11EOF
  chmod +x "$out"

  # linux-gpu.sh
  mkdir -p "$HOME/.config"
  cat > "$HOME/.config/linux-gpu.sh" <<GPUEOF
export MESA_NO_ERROR=1
export MESA_GL_VERSION_OVERRIDE=4.6
export MESA_GLES_VERSION_OVERRIDE=3.2
export GALLIUM_DRIVER=$([ "$gpu" = "freedreno" ] && echo "freedreno" || echo "zink")
export MESA_LOADER_DRIVER_OVERRIDE=$([ "$gpu" = "freedreno" ] && echo "freedreno" || echo "zink")
export TU_DEBUG=noconform
export MESA_VK_WSI_PRESENT_MODE=immediate
export ZINK_DESCRIPTORS=lazy
GPUEOF

  echo -e "  ${GREEN}[+] start-x11.sh + linux-gpu.sh utworzone.${NC}"

  # 10. Synaptic shortcut na pulpit (uruchamiany bez sudo — polkit zapyta)
  update_progress
  echo -e "${CYAN}[*] Integracja menu proot (Synaptic bez sudo w wrapperze)...${NC}"
  proot_exec '
    mkdir -p /usr/share/applications
    cat > /usr/share/applications/synaptic.desktop <<SYN
[Desktop Entry]
Name=Synaptic Package Manager
GenericName=Package Manager
Comment=Install, upgrade and remove software packages
Exec=synaptic-pkexec
Icon=synaptic
Terminal=false
Type=Application
Categories=PackageManager;System;Settings;
SYN
    # wrapper synaptic-pkexec: uruchamia przez pkexec (polkit zapyta o hasło)
    cat > /usr/local/bin/synaptic-pkexec <<PKEX
#!/bin/bash
exec pkexec --disable-internal-agent /usr/sbin/synaptic "\$@"
PKEX
    chmod +x /usr/local/bin/synaptic-pkexec
  ' 2>/dev/null
  echo -e "  ${GREEN}[+] Synaptic uruchamiany przez pkexec (okno uprawnień).${NC}"

  # 11. gpio-bridge examples (USB-serial, HTTP, MQTT, WS, BLE klienty)
  update_progress
  proot_install_gpio_examples

  echo ""
  echo -e "${GREEN}[ Profil desktop gotowy. ]${NC}"
  echo -e "${BOLD}Start X11:${NC}  bash ~/start-proot.sh && bash ~/start-x11.sh"
  echo -e "${BOLD}Synaptic z menu:${NC}  okno polkit poprosi o hasło root"
  echo -e "${BOLD}sudo apt:${NC}  w terminalu proot pyta o hasło usera"
  echo -e "${BOLD}Sterowanie GPIO:${NC}  gpio-usb /dev/ttyUSB0 set 12 1"
  echo -e "${BOLD}     (Wi-Fi):  ${NC}  gpio-http 192.168.4.1 set 12 1"
  echo -e "${BOLD}     (MQTT):   ${NC}  gpio-mqtt 127.0.0.1 esp32 node-1 12 1"
}
