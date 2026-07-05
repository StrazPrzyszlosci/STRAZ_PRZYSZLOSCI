#!/data/data/com.termux/files/usr/bin/bash
# start-straz-boot.sh — auto-podniesienie węzła po restarcie telefonu.
# Przeznaczony do ~/.termux/boot/start-straz-boot.sh (Termux:Boot).
# Wymaga aplikacji Termux:Boot z F-Droid.

set -u

TIMESTAMP=$(date -u +%FT%TZ)
LOG="$HOME/.straz-edge/boot.log"

log_msg() {
  echo "[$TIMESTAMP] $1" >> "$LOG" 2>/dev/null
  # opcjonalnie do logcat
  termux-toast "$1" 2>/dev/null || true
}

log_msg "Boot: start węzła Straż Edge"

# wake-lock: CPU nie śpi
if command -v termux-wake-lock >/dev/null 2>&1; then
  termux-wake-lock węzeł-straz 2>/dev/null || true
  log_msg "wake-lock aktywowany"
fi

# Sprawdź Phantom Killer (Android 13+) — ostrzeżenie jeśli nadal domyślny
PID_MAX=$(/system/bin/device_config get activity_manager max_phantom_processes 2>/dev/null || echo "unknown")
if [ "$PID_MAX" != "2147483647" ] && [ "$PID_MAX" != "unknown" ]; then
  log_msg "OSTRZEŻENIE: max_phantom_processes = $PID_MAX (oczekiwane: 2147483647). Proot może paść z signal 9. Wykonaj RUNBOOK_PHANTOM_PROCESS_KILLER.md."
fi

# Podnieś proot
if [ -f "$HOME/start-proot.sh" ]; then
  log_msg "start-proot.sh wykryty — uruchamianie..."
  nohup bash "$HOME/start-proot.sh" >> "$HOME/.straz-edge/proot.log" 2>&1 &
  sleep 2
  log_msg "proot sesja w toku (PID: $!)"
else
  log_msg "BŁAD: start-proot.sh nie znaleziony. Uruchom install.sh najpierw."
fi

# Jeśli profil desktop, opcjonalnie podnieś VNC/X11 (zależy jakie setup)
if [ -f "$HOME/start-x11.sh" ]; then
  sleep 5   # proot potrzebuje dłuższego startu
  nohup bash "$HOME/start-x11.sh" >> "$HOME/.straz-edge/x11.log" 2>&1 &
  log_msg "start-x11.sh w tle"
elif [ -f "$HOME/start-vnc.sh" ]; then
  sleep 5
  nohup bash "$HOME/start-vnc.sh" >> "$HOME/.straz-edge/vnc.log" 2>&1 &
  log_msg "start-vnc.sh w tle"
fi

log_msg "Boot zakończony"