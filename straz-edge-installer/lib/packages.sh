#!/data/data/com.termux/files/usr/bin/bash
# lib/packages.sh — rekomendowane pakiety dla projektów Straży Przyszłości
# Organizowane według filarów: base, GPIO/I2C/SPI, MQTT/networking, AI/edukacja,
# sterownicy/sensory, GPIO/I2C/SPI dostępne z poziomu smartfona przez USB-serial/peripheral.

# ===== BASE (wszystkie profile) =====
PKG_BASE="sudo curl wget git htop nano less ca-certificates gnupg locales tzdata \
  bash-completion man-db unzip zip rsync sqlite3 cron anacron tmux"

# ===== GPIO / I2C / SPI / UART z poziomu Linuxa =====
# Smartfon steruje przez: USB-serial (FT232R/CH341/CP210x) -> UART do ESP32/MCU,
# albo przez USB-I2C/SPI bridge (CH341 i2c, FT2232H), ALBO bezprzewodowo
# (Wi-Fi/BT) do ESP32 eksponującego endpoint GPIO (HTTP API / MQTT / serial-over-WS).
PKG_GPIO="libgpiod2 libgpiod-dev i2c-tools spi-tools python3-libgpiod \
  python3-smbus python3-spidev pyserial python3-serial \
  setserial minicom picocom"

# ===== Komunikacja bezprzewodowa (Wi-Fi/BT) =====
# Smartfon <-> ESP32 po Wi-Fi (HTTP REST, WebSocket, MQTT) lub Bluetooth Classic/BLE.
PKG_WIRELESS="bluez bluez-tools python3-dbus python3-bleak python3-pybluez \
  rfkill python3-requests python3-websockets python3-aiohttp \
  python3-asyncio-mqtt avahi avahi-utils"

# ===== Sterowniki USB (serial/I2C/SPI bridge) =====
# Przez USB-OTG: FT232R (UART), CH341 (UART + I2C), CP210x (UART), FT2232H (JTAG/I2C/SPI),
# STM32 USB CDC (UART), oraz usbutils do diagnostyki.
PKG_USB="usbutils udev python3-usb python3-pyftdi python3-pylibftdi \
  libftdi-dev libftdi1"

# ===== MQTT / sieci / IoT =====
PKG_MQTT="mosquitto mosquitto-clients python3-paho-mqtt \
  libmosquitto-dev libpaho-mqtt-dev"

# ===== AI / ML / edge (lekki, proot) =====
# Python + biblioteki. torch/transformers zbyt ciężkie dla starych smartfonów;
# rekomendujemy ONNX Runtime + tflite-runtime (lekki) + ekuigrantsku tinygrad.
PKG_AI="python3 python3-pip python3-venv python3-numpy python3-pandas \
  python3-requests python3-yaml python3-jinja2"

# ===== Sensoryka / odczyt czujników =====
# Biblioteki do typowych czujników hydroponika/akwakultura.
PKG_SENSORS="python3-smbus i2c-tools python3-pip"

# ===== Networking dla węzła =====
PKG_NET="openssh-client openssh-server iproute2 iputils-ping dnsutils \
  network-manager net-tools traceroute tcpdump nmap \
  wireguard-tools curl"

# ===== System / utrzymanie =====
PKG_SYS="logrotate rsyslog udev systemd-sysv dbus policykit-1"

# ===== Desktop (pakiety środowiska graficznego) =====
# Te instalacyjne są w Termux (TUR/x11-repo) nie w proot, listowane osobno.
PKG_DESKTOP_PROOT="synaptic gdebi policykit-1-gnome polkit-gnome-authentication-agent-1 \
  gnome-keyring seahorse network-manager-gnome"

# ===== VS Code w proot (opcjonalnie) =====
# code = Microsoft VS Code; code-oss = open-source build (bez telemetrii).
PKG_VSCODE_PROOT="code-oss gnupg"

# ===== Pomoce sterownicze (GPIO endpoint) =====
# periphery = lekka lib do gpio/i2c/spi/uart/pwm na Linuxie.
# python3-can = CAN bus (perywania sterowników automatyzacji).
# python3-adafruit-blinka = abstrakcja GPIO z CircuitPython dla MCP/SBC.
PKG_CONTROL="python3-pyftdi python3-adafruit-blinka python3-rpi-lgpio \
  python3-periphery python3-serial python3-can \
  python3-websockets python3-asyncio-mqtt"

# ===== Animacja edukacyja / raporty =====
PKG_REPORTS="python3-matplotlib python3-pillow graphviz plantuml"

# Funkcja zwracająca listę pakietów dla profilu (spacja-separowane stringi)
get_packages_for_profile() {
  local profile=$1
  case "$profile" in
    node-nsip)
      echo "$PKG_BASE $PKG_GPIO $PKG_WIRELESS $PKG_USB $PKG_MQTT $PKG_AI \
            $PKG_NET $PKG_SYS $PKG_CONTROL $PKG_REPORTS"
      ;;
    gateway)
      echo "$PKG_BASE $PKG_WIRELESS $PKG_USB $PKG_MQTT $PKG_NET $PKG_SYS \
            python3 python3-pip python3-paho-mqtt python3-serial \
            python3-bleak python3-websockets mosquitto"
      ;;
    desktop)
      echo "$PKG_BASE $PKG_GPIO $PKG_WIRELESS $PKG_USB $PKG_MQTT $PKG_AI \
            $PKG_NET $PKG_SYS $PKG_CONTROL $PKG_DESKTOP_PROOT $PKG_REPORTS"
      ;;
    *)
      echo "$PKG_BASE $PKG_GPIO $PKG_WIRELESS $PKG_USB $PKG_MQTT $PKG_AI"
      ;;
  esac
}
