# 10. Łączność Mesh i LoRa w Gospodarce (MeshCore, Reticulum, Meshtastic)

## **Intelekt wyprzedza Kapitał!**

## Opis Projektu
Projekt zakłada budowę suwerennej, odpornej na awarie infrastruktury komunikacyjnej opartej na sieciach kratowych (Mesh). Fundamentem są **wbudowane systemy łączności smartfonów z odzysku** (GSM, LTE/4G, Wi-Fi, Bluetooth), które uzupełniamy technologią LoRa dla uzyskania ekstremalnych zasięgów. Wykorzystujemy "elektrośmieci" jako uniwersalne mosty komunikacyjne (Gateways), które mogą inteligentnie przełączać się między siecią komórkową a darmowymi sieciami Mesh w zależności od dostępności sygnału i kosztów.

W "Straży Przyszłości" sieć Mesh służy jako **Nerw Gospodarczy**, przesyłając dane z sensorów rolnych, informując o stanie sieci energetycznej oraz zabezpieczając komunikację bez polegania wyłącznie na zewnętrznych dostawcach.

## Filary Technologiczne i Gotowy Kod

### 1. Reticulum Network Stack (RNS) – Suwerenny Stos Sieciowy
Reticulum to najbardziej elastyczny i odporny stos sieciowy dla zdecentralizowanej komunikacji, zaprojektowany dla warunków wysokich opóźnień i niskiej przepustowości.
- **[Sideband](https://github.com/markqvist/Sideband):** Gotowy komunikator graficzny do bezpiecznej wymiany raportów technicznych i logistycznych.
- **RNode:** Wykorzystujemy firmware RNode dla modułów LoRa, co pozwala na budowę sieci o zasięgu od kilometrów do tysięcy kilometrów (przez bramki).
- **LXMF:** Protokół wiadomości (end-to-end encrypted) dla komunikacji maszyna-maszyna i człowiek-człowiek.
- **Zastosowanie:** Bezpieczny "pipe" dla danych SCADA i nadzorowania magazynów energii (Projekt 05) w miejscach bez zasięgu komórkowego.

### 2. p2panda (Panda) – Synchronizacja P2P Offline-First
Nowoczesny protokół P2P, będący alternatywą dla SSB, z lepszym wsparciem dla wielu urządzeń jednego użytkownika.
- **Charakterystyka:** Wykorzystuje logi (append-only logs) i mechanizmy przyczynowości (causality).
- **Zalety:** Idealny do budowania aplikacji, które synchronizują się same, gdy tylko urządzenia znajdą się w zasięgu.
- **Zastosowanie:** Zdecentralizowane bazy danych, kolaboratywne aplikacje rolnicze i synchronizacja danych IoT w rozproszonych węzłach.

### 3. vossbol / tinySSB – "Plotkowa" Replikacja Danych
Specjalnie okrojona wersja protokołu **Secure Scuttlebutt (SSB)** pod niską przepustowość LoRa.
- **[vossbol](https://github.com/tschudin/vossbol):** Implementacja umożliwiająca replikację danych (gossip protocol) nawet przy minimalnej przepustowości.
- **Zalety:** Każdy użytkownik ma swój dziennik zdarzeń, który jest replikowany między znajomymi; system jest ekstremalnie odporny na brak stałego połączenia.
- **Zastosowanie:** Rozproszona replikacja danych sensorowych i głosowych w izolowanych lokalizacjach.

### 4. Meshtastic – Gotowe Moduły Sterowania i Telemetrii
Najpopularniejsza platforma LoRa Mesh, oferująca gotowe funkcjonalności bez potrzeby pisania kodu od zera:
- **[Remote Hardware Module](https://meshtastic.org/docs/configuration/modules/remote-hardware/):** Zdalne sterowanie pinami GPIO (np. pompy nawadniające w Projekcie 01/08).
- **[Telemetry Module](https://meshtastic.org/docs/configuration/modules/telemetry/):** Automatyczne przesyłanie danych z czujników środowiskowych (Projekt 09).
- **Integracja Python:** Wykorzystanie [Meshtastic Python API](https://github.com/meshtastic/python) do zaawansowanej automatyzacji.

### 5. Łączność Hybrydowa i Bramki (Deadmesh & Disaster Radio)
Wykorzystujemy pełen stos komunikacyjny smartfonów oraz dedykowane mosty:
- **[Deadmesh](https://github.com/gnarzilla/deadmesh):** Pomost Internet-over-LoRa. Pozwala urządzeniom w sieci Meshtastic na dostęp do usług internetowych (HTTP, DNS, Email) przez bramkę. Umożliwia to nadzór dużych modeli AI (Cloud) nad lokalnymi automatyzacjami (Edge).
- **[Disaster Radio](https://github.com/sudomesh/disaster-radio):** Wykorzystuje protokół **LoRaLayer2** dla komunikacji w sytuacjach kryzysowych.
- **GSM/LTE/4G + Wi-Fi Aware:** Smartfon z odzysku służy jako brama (Gateway), zbierająca dane z lokalnej sieci Mesh i przesyłająca je dalej, gdy tylko pojawi się zasięg komórkowy.
- **[Briar](https://github.com/briar/briar):** Bezpieczna komunikacja P2P przez Bluetooth i Wi-Fi.
- **[MeshCore Firmware](https://github.com/meshcore-dev/MeshCore):** Energooszczędne zarządzanie modułami radiowymi.


## Implementacja Gospodarcza (Scenariusze PoC)

1. **Efektywność Energetyczna i Grid Health:** Wykorzystanie sieci Mesh do monitorowania stanu transformatorów i magazynów energii (OZE). W przypadku wykrycia awarii przez sensory, system przesyła zapytanie przez sieć Mesh o dostępność energii w sąsiednich mikrosieciach lub informuje operatora o dokładnej lokalizacji usterki bez użycia Internetu.
2. **Monitoring Gatunkowy i Inwentarski:** Smartfony na obrożach (Projekt 09) działają jako ruchome węzły (repeatery), dynamicznie budując zasięg sieci Mesh tam, gdzie przebywa stado. Pozwala to na pełny monitoring wizyjny (Sentinel) klatek/zagród w głębi pola.
3. **Logistyka Gospodarcza (Suwerenny Komunikator):** Wymiana informacji o zapotrzebowaniu na paliwo, paszę czy gotowość produktów do odbioru, z pełnym szyfrowaniem end-to-end, niezależnie od awarii globalnych platform komunikacyjnych.

## Dlaczego LoRa Mesh?
- **Koszty:** Brak opłat za przesył danych (brak kart SIM).
- **Zasięg:** Od kilku do kilkunastu kilometrów na jednym skoku (hop), z możliwością nieskończonego przedłużania przez kolejne węzły.
- **Suwerenność:** Infrastruktura należy do użytkowników, nie do korporacji.

---
*Intelekt wyprzedza Kapitał!*
