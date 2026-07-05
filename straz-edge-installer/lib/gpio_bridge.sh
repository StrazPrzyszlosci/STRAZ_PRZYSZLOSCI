#!/data/data/com.termux/files/usr/bin/bash
# lib/gpio_bridge.sh — biblioteka kliencka do sterowania GPIO na ESP32/MCU
# Smartfon (proot) wysyła komendy do endpointu GPIO na ESP32 przez:
#   1. USB-serial (UART)         — /dev/ttyUSB0
#   2. Wi-Fi HTTP REST API       — http://<esp32_ip>/gpio
#   3. Wi-Fi WebSocket           — ws://<esp32_ip>/ws
#   4. MQTT                       — topic esp32/<id>/gpio
#   5. Bluetooth Classic/BLE      — RFCOMM / GATT
#
# Biblioteki instalowane przez lib/packages.sh: libgpiod, pyserial, python3-bleak,
# python3-websockets, python3-asyncio-mqtt, python3-requests.

# Instaluje w proot zbiór przykładowych skryptów klienckich w /usr/local/bin/gpio-
proot_install_gpio_examples() {
  echo -e "${CYAN}[*] Instalacja przykładów gpio-bridge w /usr/local/bin...${NC}"
  proot_exec '
    mkdir -p /usr/local/bin /etc/straz-edge

    # --- gpio-usb: sterowanie przez UART (JSON-over-serial) ---
    cat > /usr/local/bin/gpio-usb <<GPIO_USB
#!/bin/bash
# gpio-usb <device> <action> <pin> [value]
# Przykład: gpio-usb /dev/ttyUSB0 set 12 1   (HIGH na pin12)
usage() { echo "Użycie: gpio-usb <dev> <get|set> <pin> [value]"; exit 1; }
[ $# -lt 3 ] && usage
DEV=$1; CMD=$2; PIN=$3; VAL=${4:-0}
python3 - <<PY
import serial, json, sys, time
dev, cmd, pin, val = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]) if len(sys.argv)>4 else 0
with serial.Serial(dev, 115200, timeout=2) as s:
    s.reset_input_buffer()
    payload = {"cmd": cmd, "pin": pin, "value": val}
    s.write((json.dumps(payload) + "\\n").encode())
    time.sleep(0.05)
    print(s.read_all().decode(errors="replace").strip())
PY
GPIO_USB
    chmod +x /usr/local/bin/gpio-usb

    # --- gpio-http: sterowanie przez HTTP REST API na ESP32 ---
    cat > /usr/local/bin/gpio-http <<GPIO_HTTP
#!/bin/bash
# gpio-http <esp32_ip> <action> <pin> [value]
# Wymaga firmware na ESP32 z endpointem: GET/POST /gpio?pin=N&value=V
usage() { echo "Użycie: gpio-http <ip> <get|set> <pin> [value]"; exit 1; }
[ $# -lt 3 ] && usage
IP=$1; CMD=$2; PIN=$3; VAL=${4:-0}
curl -s "http://$IP/gpio?cmd=$CMD&pin=$PIN&value=$VAL"
echo
GPIO_HTTP
    chmod +x /usr/local/bin/gpio-http

    # --- gpio-mqtt: publikuj komendę GPIO przez MQTT ---
    cat > /usr/local/bin/gpio-mqtt <<GPIO_MQTT
#!/bin/bash
# gpio-mqtt <broker> <topic_prefix> <esp32_id> <pin> [value]
usage() { echo "Użycie: gpio-mqtt <broker> <prefix> <esp32_id> <pin> [value]"; exit 1; }
[ $# -lt 4 ] && usage
BROKER=$1; PREFIX=$2; ID=$3; PIN=$4; VAL=${5:-0}
TOPIC="$PREFIX/$ID/gpio"
mosquitto_pub -h "$BROKER" -t "$TOPIC" -m "{\\"pin\\":$PIN,\\"value\\":$VAL}"
echo "Wysłano do $TOPIC: pin=$PIN value=$VAL"
GPIO_MQTT
    chmod +x /usr/local/bin/gpio-mqtt

    # --- gpio-ws: sterowanie przez WebSocket (async) ---
    cat > /usr/local/bin/gpio-ws <<GPIO_WS
#!/bin/bash
# gpio-ws <ws_url> <pin> [value]
URL=$1; PIN=$2; VAL=${3:-0}
python3 - <<PY
import asyncio, websockets, json, sys
url, pin, val = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
async def run():
    async with websockets.connect(url) as ws:
        await ws.send(json.dumps({"pin": pin, "value": val}))
        resp = await ws.recv()
        print(resp)
asyncio.run(run())
PY
GPIO_WS
    chmod +x /usr/local/bin/gpio-ws

    # --- gpio-ble: sterowanie przez Bluetooth LE (GATT) ---
    cat > /usr/local/bin/gpio-ble <<GPIO_BLE
#!/bin/bash
# gpio-ble <mac> <char_uuid> <pin> [value]
MAC=$1; UUID=$2; PIN=$3; VAL=${4:-0}
python3 - <<PY
import asyncio, sys
from bleak import BleakClient
mac, uuid, pin, val = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]) if len(sys.argv)>4 else 0
async def run():
    async with BleakClient(mac) as c:
        data = bytes([pin, val])
        await c.write_gatt_char(uuid, data)
        print("OK", pin, val)
asyncio.run(run())
PY
GPIO_BLE
    chmod +x /usr/local/bin/gpio-ble

    # --- Konfiguracja domyślna (placeholder do edycji) ---
    cat > /etc/straz-edge/gpio-bridge.env <<ENV
# Konfiguracja endpointu GPIO — zedytuj pod swój ESP32
GPIO_BRIDGE_MODE=usb          # usb|http|mqtt|ws|ble
GPIO_USB_DEVICE=/dev/ttyUSB0
GPIO_HTTP_IP=192.168.4.1
GPIO_MQTT_BROKER=127.0.0.1
GPIO_MQTT_PREFIX=esp32
GPIO_WS_URL=ws://192.168.4.1/ws
GPIO_BLE_MAC=AA:BB:CC:DD:EE:FF
GPIO_BLE_UUID=0000ffe1-0000-1000-8000-00805f9b34fb
ENV
  ' 2>/dev/null
  echo -e "  ${GREEN}[+] gpio-bridge examples zainstalowane (/usr/local/bin/gpio-*).${NC}"
  echo -e "  ${CYAN}    Konfiguracja: /etc/straz-edge/gpio-bridge.env${NC}"
  echo -e "  ${CYAN}    Użycie: gpio-usb /dev/ttyUSB0 set 12 1${NC}"
  echo -e "  ${CYAN}           gpio-http 192.168.4.1 set 12 1${NC}"
}
