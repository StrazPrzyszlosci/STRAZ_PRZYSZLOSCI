# 06. Upcykling Smartfonów jako Sterowników (Edge Computing)

## Opis Projektu
Projekt zakłada wykorzystanie "elektrośmieci" w postaci starych smartfonów jako zaawansowanych sterowników i węzłów obliczeniowych (Edge Computing). Nawet starsze urządzenia posiadają komponenty o ogromnym potencjale: wydajne procesory, pamięć, baterię (UPS), WiFi, Bluetooth oraz bogaty zestaw czujników (akcelerometry, żyroskopy, barometry), GPS, wysokiej jakości mikrofony i kamery.

## Tryby pracy i Energooszczędność
Smartfon może pełnić rolę sterownika w dwóch kluczowych modelach:
1. **Interaktywny panel (z ekranem):** Wykorzystanie ekranu dotykowego jako terminala sterującego, wizualizującego dane z czujników lub stanu urządzenia w czasie rzeczywistym.
2. **Praca bez ekranu (Headless):** Usunięcie lub wyłączenie ekranu w celu drastycznego obniżenia zużycia energii, co czyni telefon realnym konkurentem dla Arduino i ESP w zastosowaniach niskomocowych.

## Wykorzystanie potencjału sprzętowego
- **Sensoryka:** Monitoring warunków środowiskowych (temperatura, światło - przez czujnik oświetlenia, wilgotność), wykrywanie drgań czy precyzyjna lokalizacja GPS.
- **Wizja i Audio:** Wykorzystanie kamery do inspekcji wizualnej (np. stan wzrostu roślin) oraz mikrofonu do detekcji anomalii akustycznych (np. nieprawidłowa praca silników/pomp).

## Aspekty Techniczne
- **Komunikacja:** Wykorzystanie standardu USB OTG oraz konwerterów USB-UART (np. chip FT232R) do bezpośredniego sterowania elektroniką wykonawczą.
- **Zasilanie:** Inteligentne zarządzanie ładowaniem, aby zapobiegać degradacji i puchnięciu baterii przy ciągłej pracy pod zasilaczem.
- **Oprogramowanie i Firmware:**
  - **[lk2nd](https://github.com/nphuracm/obsolete-lk2nd):** Customowy bootloader dla urządzeń Qualcomm, ułatwiający uruchamianie alternatywnych systemów i debugowanie.
  - **[selfphone](https://github.com/monobogdan/selfphone):** Eksperymentalny projekt budowy lekkiego firmware/UI dla starszych chipsetów (MediaTek/Spreadtrum).
  - **[postmarketOS](https://postmarketos.org/):** Prawdziwy Linux dla telefonów, idealny do stworzenia stabilnego terminala lub serwera embedded.

## Zastosowanie w Straży Przyszłości
Dążymy do stworzenia narodowego frameworku, który pozwoli na masowe wykorzystanie starych urządzeń do sterowania infrastrukturą autonomiczną:
- Zarządzanie pompami wody i oświetleniem w węzłach produkcji żywności.
- Monitoring wizyjny (wykorzystanie wbudowanej kamery) z lokalną analizą obrazu przez AI.
- Centralne sterowniki dla systemów off-grid i magazynów energii.

## Inspiracje:
- [Wideo: Smartfon potężniejszy niż Arduino](https://www.youtube.com/watch?v=iobvVl8jZ5o)
- [Projekt "Stary smartfon jako mikrokontroler"](https://github.com/KrzyZuch/STRAZ_PRZYSZLOSCI/)

---
*Intelekt wyprzedza kapitał!*
