# 07. Uniwersalna Platforma Sterowania (Sensory i Aktuatory)

## **Intelekt wyprzedza Kapitał!**

### Nobilitacja Twórcy
Ten projekt powstał dzięki wnikliwej analizie i udostępnieniu zasobów przez **Marka Sumę** ([@mareksuma1985](https://github.com/mareksuma1985)), twórcę projektu **PhoneUAV-server**. Marek przekazał tę wiedzę bezpośrednio na rzecz naszej inicjatywy, za co otrzymuje najwyższe wyrazy uznania. Jego praca nad sterowaniem dwiema tonami elektroniki i lotnictwem za pomocą smartfona to fundamentalny przykład **przewagi intelektu nad kapitałem**.

---

## Koncepcja: Kod jako Surowiec Strategiczny

W **NARODOWYCH SIŁACH INTELEKTUALNYCH** wychodzimy z założenia, że nie musimy odkrywać koła na nowo. Pozyskiwanie, katalogowanie i opisywanie tak zaawansowanych repozytoriów jak `PhoneUAV-server` to realna praca na rzecz wspólnego dobra. Dzięki temu przyszli twórcy – wspierani przez AI – nie muszą pisać systemów od zera, lecz mogą adaptować gotowe, sprawdzone moduły do nowych zastosowań (np. w akwakulturze, automatyzacji farm czy logistycznym Edge Computing).

## Analiza Techniczna (Deep Dive w kod)

Repozytorium [PhoneUAV-server](https://github.com/mareksuma1985/PhoneUAV-server) dostarcza gotowych rozwiązań dla dwóch krytycznych obszarów:

### 1. Pozyskiwanie Danych (Sensory Telefonu)
Smartfon to potężny zestaw czujników. Poniższe fragmenty kodu pokazują, jak w profesjonalny sposób odczytywać dane potrzebne do stabilizacji i pozycjonowania dowolnej maszyny:

**Przykład: Odczyt Akcelerometru (`Accelerometer.java`)**
Kod filtruje szumy i pozwala na obrót wektora przyśpieszenia względem orientacji urządzenia, co jest kluczowe, gdy telefon nie jest zamontowany idealnie poziomo:
```java
// Filtracja zmian poniżej progu czułości
if (deltaX < 0.01) deltaX = 0;

// Obrót wektora wokół osi Z (Wikipedia: Rotation Matrix)
accVectorVehicle = rotateAroundZ(accVectorDevice, main.device_orientation[2]);

// Obliczanie kątów Roll i Pitch
angle_roll = Math.toDegrees(Math.atan2((double) accVectorVehicle[0], (double) accVectorVehicle[2]));
angle_pitch = Math.toDegrees(Math.atan2((double) accVectorVehicle[1], (double) accVectorVehicle[2]));
```

### 2. Sterowanie Fizyczne (USB i Aktuatory)
Największą wartością jest kod pozwalający smartfonowi na "wyjście na zewnątrz". Dzięki kontrolerom USB (np. CH340), telefon może bezpośrednio sterować serwomechanizmami i silnikami.

**Przykład: Sterowanie serwami przez USB (`CH340comm.java`)**
Kod buduje ramkę danych dla kontrolera serw (np. USC-16) i przesyła ją przez USB OTG:
```java
public void SetPositionArray(int[] channels, int width, int time) {
    String message = "";
    for (int i = 0; i < channels.length; i++) {
        // Składanie komendy dla kontrolera (np. #1P1500T100)
        message += "#" + Math.abs(channels[i]) + "P" + width;
    }
    message += "T" + time;
    this.write(message); // Przesył przez sterownik CH34x
}
```

## Potencjał Adaptacji i Wykorzystanie AI

Dzięki temu, że te kody są dostępne w naszym repozytorium jako "surowiec", modele AI mogą je natychmiastowo przekształcić w:
-   **Autonomiczne pompy w akwakulturze:** Wykorzystanie sensora ciśnienia do monitorowania poziomu wody i sterowanie zaworami przez USB.
-   **Robotykę polową:** GPS i magnetometr służą do nawigacji, a kod sterowania serwami porusza mechanizmem siewnika.
-   **Monitoring wizyjny:** Adaptacja kodu `Camera2API.java` do inteligentnego rozpoznawania obrazu na krawędzi sieci (Edge AI).

---

### Zasoby referencyjne:
- **Repozytorium źródłowe:** [https://github.com/mareksuma1985/PhoneUAV-server](https://github.com/mareksuma1985/PhoneUAV-server)
- **Autor:** Marek Suma ([bezzalogowe.pl](http://bezzalogowe.pl))

---
*Intelekt wyprzedza Kapitał!*
