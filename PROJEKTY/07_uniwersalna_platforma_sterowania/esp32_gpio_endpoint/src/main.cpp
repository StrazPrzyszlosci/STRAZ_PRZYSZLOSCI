// ESP32 GPIO Endpoint — Straż Edge węzeł sterowniczy
//
// Kompatybilne z klientami z straz-edge-installer/lib/gpio_bridge.sh:
//   - gpio-usb    : JSON-over-serial przez UART0 (115200)
//   - gpio-http   : REST  GET/POST /gpio?cmd=set&pin=N&value=V
//   - gpio-mqtt   : topic esp32/<id>/gpio  {"pin":N,"value":V}
//   - gpio-ws     : WebSocket ws://<ip>/ws  {"pin":N,"value":V}
//
// Pinout: piny 0-19 sterowalne jako OUTPUT (patrz PINMAP na dole).
// Bezpieczeństwo: brak WiFi hardcoded — konfiguracja przez SerialJSON.

#include <Arduino.h>
#include <ArduinoJson.h>
#include <WiFi.h>
#include <WebServer.h>
#include <WebSocketsServer.h>
#include <PubSubClient.h>
#include <Preferences.h>

#define UART_BAUD 115200
#define HTTP_PORT 80
#define WS_PORT 81

// Piny bezpieczne do sterowania (bez strapping 0/2/12/15 w trybie output).
// Patrz pinmap w README.
const int SAFE_PINS[] = {4, 5, 13, 14, 16, 17, 18, 19, 21, 22, 23, 25, 26, 27, 32, 33};
const int SAFE_PIN_COUNT = sizeof(SAFE_PINS) / sizeof(SAFE_PINS[0]);

WebServer http(HTTP_PORT);
WebSocketsServer ws(WS_PORT);
WiFiClient net;
PubSubClient mqtt(net);
Preferences prefs;

String mqttTopic = "esp32/gpio";
String deviceId = "esp32-default";

bool isPinSafe(int pin) {
  for (int i = 0; i < SAFE_PIN_COUNT; i++) {
    if (SAFE_PINS[i] == pin) return true;
  }
  return false;
}

int applyGpio(int pin, int value) {
  if (!isPinSafe(pin)) return -1;
  pinMode(pin, OUTPUT);
  digitalWrite(pin, value ? HIGH : LOW);
  return value;
}

int readGpio(int pin) {
  if (!isPinSafe(pin)) return -1;
  pinMode(pin, OUTPUT);
  return digitalRead(pin) == HIGH ? 1 : 0;
}

// ----- odpowiedź JSON na komendę -----
String handleCommand(const char* cmd, int pin, int value) {
  StaticJsonDocument<200> doc;
  doc["pin"] = pin;
  if (String(cmd) == "set") {
    int v = applyGpio(pin, value);
    if (v < 0) {
      doc["error"] = "unsafe pin";
    } else {
      doc["value"] = v;
    }
  } else if (String(cmd) == "get") {
    int v = readGpio(pin);
    if (v < 0) {
      doc["error"] = "unsafe pin";
    } else {
      doc["value"] = v;
    }
  } else {
    doc["error"] = "unknown cmd (use get|set)";
  }
  String out;
  serializeJson(doc, out);
  return out;
}

// ----- HTTP REST -----
void handleHttpGpio() {
  String cmd = http.arg("cmd");
  String sp = http.arg("pin");
  String sv = http.arg("value");
  if (cmd.length() == 0 || sp.length() == 0) {
    http.send(400, "application/json", "{\"error\":\"cmd and pin required\"}");
    return;
  }
  int pin = sp.toInt();
  int value = sv.toInt();
  String out = handleCommand(cmd.c_str(), pin, value);
  http.send(200, "application/json", out);
}

void handleHttpInfo() {
  String pins = "";
  for (int i = 0; i < SAFE_PIN_COUNT; i++) {
    pins += String(SAFE_PINS[i]);
    if (i < SAFE_PIN_COUNT - 1) pins += ",";
  }
  String out = "{\"device\":\"" + deviceId + "\",\"safe_pins\":[" + pins + "],\"endpoints\":[\"/gpio\",\"/info\",\"ws://ip:81\"]}";
  http.send(200, "application/json", out);
}

// ----- WebSocket -----
void onWsEvent(uint8_t num, WStype_t type, uint8_t* payload, size_t length) {
  if (type != WStype_TEXT) return;
  StaticJsonDocument<200> doc;
  DeserializationError err = deserializeJson(doc, payload, length);
  if (err) {
    ws.sendTXT(num, "{\"error\":\"invalid json\"}");
    return;
  }
  const char* cmd = doc["cmd"] ? doc["cmd"] : "set";
  int pin = doc["pin"] | 0;
  int value = doc["value"] | 0;
  String out = handleCommand(cmd, pin, value);
  ws.sendTXT(num, out);
}

// ----- MQTT -----
void onMqttMessage(char* topic, byte* payload, unsigned int len) {
  StaticJsonDocument<200> doc;
  DeserializationError err = deserializeJson(doc, payload, len);
  if (err) return;
  const char* cmd = doc["cmd"] ? doc["cmd"] : "set";
  int pin = doc["pin"] | 0;
  int value = doc["value"] | 0;
  String out = handleCommand(cmd, pin, value);
  mqtt.publish((String(topic) + "/ack").c_str(), out.c_str());
}

// ----- Serial JSON -----
void handleSerial() {
  if (!Serial.available()) return;
  String line = Serial.readStringUntil('\n');
  line.trim();
  if (line.length() == 0) return;
  StaticJsonDocument<200> doc;
  DeserializationError err = deserializeJson(doc, line);
  if (err) {
    Serial.println("{\"error\":\"invalid json\"}");
    return;
  }
  // Komenda config: ustaw WiFi / mqtt
  if (doc.containsKey("wifi_ssid")) {
    prefs.begin("straz", false);
    prefs.putString("ssid", doc["wifi_ssid"].as<String>());
    prefs.putString("pass", doc["wifi_pass"].as<String>());
    prefs.putString("mqtt", doc["mqtt_broker"].as<String>());
    prefs.putString("id", doc["device_id"].as<String>());
    prefs.end();
    Serial.println("{\"ok\":true,\"msg\":\"config saved, rebooting...\"}");
    delay(300);
    ESP.restart();
    return;
  }
  const char* cmd = doc["cmd"] ? doc["cmd"] : "set";
  int pin = doc["pin"] | 0;
  int value = doc["value"] | 0;
  String out = handleCommand(cmd, pin, value);
  Serial.println(out);
}

// ----- WiFi connect -----
void connectWifi() {
  prefs.begin("straz", true);
  String ssid = prefs.getString("ssid", "");
  String pass = prefs.getString("pass", "");
  String mqttBroker = prefs.getString("mqtt", "");
  deviceId = prefs.getString("id", "esp32-default");
  prefs.end();
  if (ssid.length() == 0) {
    Serial.println("{\"msg\":\"no WiFi config — send JSON: {\\\"wifi_ssid\\\":\\\"...\\\",\\\"wifi_pass\\\":\\\"...\\\",\\\"mqtt_broker\\\":\\\"...\\\",\\\"device_id\\\":\\\"esp32-<id>\\\"}\"}");
    return;
  }
  Serial.println("{\"msg\":\"connecting WiFi\",\"ssid\":\"" + ssid + "\"}");
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid.c_str(), pass.c_str());
  int tries = 0;
  while (WiFi.status() != WL_CONNECTED && tries < 30) {
    delay(500); tries++;
  }
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("{\"error\":\"wifi connect failed\"}");
    return;
  }
  Serial.print("{\"ok\":true,\"ip\":\"");
  Serial.print(WiFi.localIP());
  Serial.println("\"}");
  http.on("/gpio", handleHttpGpio);
  http.on("/info", handleHttpInfo);
  http.begin();
  ws.begin();
  ws.onEvent(onWsEvent);
  if (mqttBroker.length() > 0) {
    mqtt.setServer(mqttBroker.c_str(), 1883);
    mqtt.setCallback(onMqttMessage);
    mqttTopic = "esp32/" + deviceId + "/gpio";
    if (mqtt.connect(deviceId.c_str())) {
      mqtt.subscribe(mqttTopic.c_str());
      Serial.println("{\"ok\":true,\"mqtt\":\"connected\",\"topic\":\"" + mqttTopic + "\"}");
    }
  }
}

void setup() {
  Serial.begin(UART_BAUD);
  connectWifi();
}

void loop() {
  handleSerial();
  http.handleClient();
  ws.loop();
  if (mqtt.connected()) {
    mqtt.loop();
  } else {
    // próba reconnect co 10s
    static unsigned long last = 0;
    if (millis() - last > 10000) {
      last = millis();
      if (mqtt.connect(deviceId.c_str())) {
        mqtt.subscribe(mqttTopic.c_str());
      }
    }
  }
}
