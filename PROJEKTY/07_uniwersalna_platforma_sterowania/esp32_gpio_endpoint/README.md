# ESP32 GPIO Endpoint Firmware

Firmware ESP32 eksponujący endpoint GPIO kompatybilny z klientami z [`straz-edge-installer/lib/gpio_bridge.sh`](../../../straz-edge-installer/lib/gpio_bridge.sh).

## Obsługiwane kanały

| Kanał | Klient (smartfon/proot) | Firmware |
|-------|--------------------------|----------|
| USB-serial (UART) | `gpio-usb /dev/ttyUSB0 set 12 1` | JSON-over-serial @115200 |
| Wi-Fi HTTP REST | `gpio-http <ip> set 12 1` | `GET/POST /gpio?cmd=set&pin=12&value=1` |
| MQTT | `gpio-mqtt <broker> esp32 <id> 12 1` | topic `esp32/<id>/gpio`, ack `.../ack` |
| WebSocket | `gpio-ws ws://<ip>:81/ws 12 1` | `ws://<ip>:81/ws` |

## Pinmap (bezpieczne piny OUTPUT)

ESP32 ma strapping piny 0/2/12/15 — omijamy. Dostępne do sterowania:

```
4, 5, 13, 14, 16, 17, 18, 19, 21, 22, 23, 25, 26, 27, 32, 33
```

Silnika/ustawienia **nie** steruje pinami: 0, 2, 12, 15, 34-39 (tylko wejście).

## Konfiguracja WiFi/MQTT przez Serial

Brak hardcoded SSID — konfiguracja przez JSON na Serial:

```bash
# W PlatformIO Monitor (pio device monitor) — wpisz jeden wiersz:
{"wifi_ssid":"TwojaSiec","wifi_pass":"haslo","mqtt_broker":"192.168.1.10","device_id":"esp32-pompa"}
```

Po zapisie urządzenie restartuje się i łączy z WiFi. IP wypisuje na Serial jako `{"ok":true,"ip":"192.168.x.x"}`.

## Build / wgranie

```bash
cd PROJEKTY/07_uniwersalna_platforma_sterowania/esp32_gpio_endpoint
pio run -t upload              # flash na ESP32 przez USB
pio device monitor            # monitor serial (115200)
```

## Test z smartfonem

Po `start-proot.sh` w straz-edge-installer:

```bash
# Przez USB-OTG → ESP32:
gpio-usb /dev/ttyUSB0 set 12 1

# Przez Wi-Fi (IP z Serialu):
gpio-http 192.168.x.x set 12 1
gpio-mqtt 192.168.1.10 esp32 esp32-pompa 12 1
gpio-ws ws://192.168.x.x:81/ws 12 1
```

## Samodiagnostyka

`curl http://<ip>/info` →
```json
{"device":"esp32-pompa","safe_pins":[4,5,13,...,33],"endpoints":["/gpio","/info","ws://ip:81"]}
```

## Bezpieczeństwo

- Brak autoryzacji na endpointach (MQTT `allow_anonymous true` w gateway). **Nie wystawiaj na publiczny internet** — węzeł w sieci LAN/lokalnej.
- Piny strapping chronione przed zapisem — `applyGpio` odrzuca niebezpieczne.
- Konfiguracja WiFi/MQTT trzymana w `Preferences` (NVS) — nie commituj SSID do firmware.

## Status

- Impl: Arduino + ArduinoJson + PubSubClient + WebSocketsServer.
- TODO: BLE GATT (`gpio-ble`) — kolejny kanał; testy na hardware; MQTT TLS.
