// === BLE GATT endpoint (dodaj do main.cpp obok WiFi) ===
// Char UUID: 0000ffe1-0000-1000-8000-00805f9b34fb (kompatybilny z gpio-ble z lib/gpio_bridge.sh)
// Komenda: bajt [pin] [value] (pierwszy bajt = pin 0-99, drugi = value 0-1)
// Odpowiedź: JSON {"pin":N,"value":V} zwracana przez wartość charakterystyki.
// BLE device name = device_id z Preferences (np. "esp32-pompa").

#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLECharacteristic.h>
#include <BLEAdvertising.h>

#define BLE_SERVICE_UUID    "0000ffe0-0000-1000-8000-00805f9b34fb"
#define BLE_CHAR_GPIO_UUID  "0000ffe1-0000-1000-8000-00805f9b34fb"

BLEServer* bleServer = nullptr;
BLECharacteristic* gpioChar = nullptr;
bool bleReady = false;

void setupBLE() {
  if (deviceId.length() == 0) return;
  String name = deviceId;
  if (name.length() > 15) name = name.substring(0, 15);

  BLEDevice::init(name.c_str());
  bleServer = BLEDevice::createServer();
  BLEService* service = bleServer->createService(BLE_SERVICE_UUID);
  gpioChar = service->createCharacteristic(
    BLE_CHAR_GPIO_UUID,
    BLECharacteristic::PROPERTY_READ |
    BLECharacteristic::PROPERTY_WRITE
  );

  gpioChar->setCallbacks(new class : public BLECharacteristicCallbacks {
    void onWrite(BLECharacteristic* chr) override {
      std::string data = chr->getValue();
      if (data.length() < 2) {
        chr->setValue("{\"error\":\"bad format (need 2 bytes: pin value)\"}");
        return;
      }
      uint8_t pin = (uint8_t)data[0];
      uint8_t val = (uint8_t)data[1];
      String cmd = data.length() >= 3 && (char)data[0] == 'g' ? "get" : (val == 0 || val == 1 ? "set" : "get");
      if (cmd == "set") val = val > 0 ? 1 : 0;
      String out = handleCommand(cmd.c_str(), pin, val);
      chr->setValue(out.c_str());
      if (mqtt.connected()) {
        mqtt.publish((mqttTopic + "/ack").c_str(), out.c_str());
      }
    }
    void onRead(BLECharacteristic* chr) override {
      chr->setValue("{\"ready\":true,\"device\":\"" + deviceId + "\"}");
    }
  });

  service->start();
  BLEAdvertising* adv = BLEDevice::getAdvertising();
  adv->addServiceUUID(BLE_SERVICE_UUID);
  adv->setScanResponse(true);
  adv->start();
  bleReady = true;
  Serial.println("{\"ok\":true,\"ble\":\"started\",\"name\":\"" + name + "\",\"uuid\":\"" BLE_CHAR_GPIO_UUID "\"}");
}