# 01. Inteligentna Akwakultura (Smart Fish Farming)

## Opis Projektu
Koncepcja "Smart Fish Farming" opiera się na stworzeniu w pełni autonomicznych systemów hodowli ryb, w których ludzka praca jest wspierana przez Sztuczną Inteligencję oraz Internet Rzeczy (IoT). System ten ma na celu zapewnienie stabilnego i wydajnego źródła żywności przy minimalnym nakładzie pracy i zasobów.

### Kluczowe funkcjonalności:
- **Pełna autonomia i monitoring:** Czujniki IoT na bieżąco badają jakość wody (poziom pH, tlenu, amoniaku) i błyskawicznie reagują na zagrożenia.
- **Optymalizacja zasobów:** Algorytmy AI analizują wiek, rozmiar i zachowanie ryb, precyzyjnie dawkując pokarm, co eliminuje marnotrawstwo.
- **Bezpieczeństwo i ekologia:** Wczesne wykrywanie chorób oraz inteligentne zarządzanie wodą i energią (zasilanie OZE).

## Wizja Straży Przyszłości
Właśnie tego typu skalowalne, bezobsługowe rozwiązania są jednym z głównych celów **Narodowych Sił Intelektualnych Polski**. Naszym celem jest zaprojektowanie i uruchomienie całkowicie autonomicznych węzłów produkcji żywności, które będą tworzyć technologiczną "gospodarkę bis". Wygenerowane w ten sposób nadwyżki i tania żywność mają docelowo zasilać fundusz **Bezwarunkowego Dochodu Podstawowego (UBI)**.

## Minimalne API `v1` dla pilotażu stawu hodowlanego

Pierwsza wersja interfejsu powinna być minimalistyczna i skupiona na dwóch rzeczach:

1. monitoringu jakości i przepływu wody,
2. odbieraniu wyników lokalnej analizy zachowania ryb.

Jeżeli Strażnicy Przyszłości mają rzeczywiście dostarczać dane do wspólnego systemu, to ten kontrakt musi być obsługiwany przez **działający serwer**, a nie tylko dokumentację. Dlatego minimalna architektura projektu zakłada punkt rejestracji providerów i żywe endpointy HTTP, przez które węzły terenowe, stare smartfony, gospodarstwa i partnerzy zewnętrzni będą mogli włączać się do wspólnej warstwy wiedzy.

Na tym etapie nie zakładamy przesyłania ciągłego strumienia wideo przez publiczne API. Byłoby to zbyt ciężkie infrastrukturalnie, kosztowne energetycznie i trudne do utrzymania w warunkach społecznościowych oraz terenowych.

### Publiczne ścieżki API

Minimalna powierzchnia API dla projektu:

```text
POST /v1/providers/register
POST /v1/observations
POST /v1/events
POST /v1/recommendations/fish-pond
GET /v1/providers/{provider_id}/status
```

### Punkt rejestracji providerów

Endpoint `POST /v1/providers/register` jest potrzebny po to, aby każdy provider mógł jawnie zgłosić się do systemu z informacją:

- kim jest,
- jakie typy danych obsługuje,
- czy działa jako firma, gospodarstwo, provider społecznościowy lub stary smartfon,
- czy wspiera monitoring jakości wody, przepływu i edge vision.

To ważne, ponieważ w naszym modelu providerem może zostać każdy, a nie tylko duży partner zewnętrzny.

### Zakres `POST /v1/observations`

Ten endpoint przyjmuje podstawowe pomiary stawu. W pierwszej wersji powinien obsługiwać:

```text
pond_id
measurement_time
water_temperature
dissolved_oxygen
pH
optional ammonia
optional flow_rate
```

To jest rdzeń minimalnego monitoringu, który pozwala:

- wykrywać ryzyko przyduchy,
- sygnalizować pogorszenie jakości wody,
- porównywać stan stawu między pomiarami i providerami,
- budować wspólną bazę wiedzy w repozytorium.

### Zakres `POST /v1/events`

Ten endpoint powinien przyjmować zdarzenia z analizy lokalnej i z warstwy terenowej, na przykład:

- `fish_behavior_summary`
- `water_quality_alert`
- `flow_anomaly`
- `manual_inspection_note`
- `edge_vision_low_confidence`

To właśnie tutaj powinny trafiać wyniki analizy obrazu ryb wykonywanej lokalnie na urządzeniu brzegowym.

### Zakres `POST /v1/recommendations/fish-pond`

Ten endpoint powinien zwracać wynik analityczny w ujednoliconej postaci:

```text
risk_level
recommendation
confidence
reason_codes
provider_id
schema_version
```

Wynik ma służyć budowie bazy wiedzy, porównywaniu przypadków i dokumentowaniu sytuacji w stawie. Nie jest to kanał zdalnego sterowania urządzeniami.

## Analiza obrazu ryb: podejście `edge-first`

Najbardziej sensowny model dla tego projektu to analiza obrazowa wykonywana lokalnie, blisko kamery, a nie przesyłanie surowego obrazu do centralnego API.

### Dlaczego nie surowe wideo w `v1`

Ciągłe przesyłanie wideo ze stawu jest na tym etapie karkołomne, ponieważ:

- wymaga dużej przepustowości i stabilnego łącza,
- szybko zużywa energię na urządzeniu terenowym,
- komplikuje archiwizację i przegląd materiału,
- utrudnia udział społeczności korzystającej z tanich i starych urządzeń,
- daje dużo danych o niskiej wartości, jeśli nie ma wcześniej selekcji zdarzeń.

### Zalecany model działania

Wersja minimalna powinna działać tak:

1. kamera lub stary smartfon obserwuje wybrany fragment stawu,
2. lokalny moduł robi analizę na małej liczbie klatek lub krótkich oknach czasowych,
3. urządzenie wylicza wskaźniki zachowania ryb,
4. do API trafia tylko wynik analizy, a nie pełny materiał wideo.

### Jakie wyniki analizy obrazu warto wysyłać

W pierwszej wersji warto wysyłać tylko lekkie metryki i flagi, na przykład:

- poziom aktywności ryb,
- wykrycie nietypowego skupiania się przy powierzchni,
- sygnał możliwego łapania powietrza,
- anomalię ruchu lub nagły spadek aktywności,
- liczbę wykrytych martwych lub nieruchomych obiektów, jeśli model daje radę,
- poziom pewności wyniku.

Takie wyniki są wystarczające, by zasilać wspólny model wiedzy i porównywać przypadki między stawami.

## Stare smartfony jako urządzenia brzegowe

Stare smartfony są tu bardzo ciekawym kandydatem, ale tylko przy dobrze dobranym zakresie zadań. Najbardziej realistyczny scenariusz to:

- prosty model skwantyzowany,
- analiza co kilka sekund lub na ograniczonej liczbie klatek,
- praca na wycinku obrazu zamiast pełnej rozdzielczości,
- wysyłka jedynie wyników liczbowych i zdarzeń,
- opcjonalny zapis bardzo krótkich klipów tylko przy wykryciu anomalii.

Na starszym urządzeniu trzeba unikać:

- ciągłej analizy pełnego wideo w wysokiej rozdzielczości,
- ciągłego uploadu nagrań,
- zbyt ciężkich modeli wymagających nowoczesnego NPU lub GPU.

## Inteligentne podejście do wideo

Jeśli kiedyś wideo ma wejść do projektu, to nie jako domyślny strumień do API, lecz jako mechanizm wyjątków:

- zapis krótkiego klipu tylko przy wykryciu anomalii,
- lokalny bufor kołowy nadpisujący stare nagrania,
- wysyłka wyłącznie miniatury, metadanych albo referencji do lokalnego pliku,
- ręczne lub okresowe zgrywanie materiału do analizy badawczej.

To pozwala zachować użyteczny materiał dowodowy bez zamieniania całego systemu w ciężką platformę wideo.

## Artefakty techniczne w repozytorium

Dla tego projektu warstwa minimalnej integracji powinna być utrzymywana jako:

- [`schemas/fish_pond_v1.yaml`](../schemas/fish_pond_v1.yaml)
- [`openapi/fish_pond_api_v1.yaml`](../openapi/fish_pond_api_v1.yaml)
- [`api/server.py`](../api/server.py)
- [`api/README.md`](../api/README.md)
- [`data/sample/fish_pond_observation.json`](../data/sample/fish_pond_observation.json)
- [`data/sample/fish_behavior_event.json`](../data/sample/fish_behavior_event.json)
- [`data/sample/fish_pond_recommendation.json`](../data/sample/fish_pond_recommendation.json)

## Najrozsądniejsza ścieżka wdrożenia

1. Najpierw uruchomić stabilny monitoring jakości i przepływu wody.
2. Następnie dodać lekką analizę zachowania ryb na urządzeniu brzegowym.
3. Dopiero później rozważać anomaliowe klipy wideo jako materiał pomocniczy.

Taka kolejność daje największą szansę na działający system, który realnie zasili bazę wiedzy Straży Przyszłości i Narodowych Sił Intelektualnych.

## Repozytoria do adaptacji i dalszej pracy Strażników Przyszłości

Najważniejsza wiadomość dla pasjonatów jest prosta: **kod już istnieje**. Nie musimy zaczynać od zera. Naszym zadaniem jest wyszukiwanie, rozumienie, łączenie i adaptacja gotowych rozwiązań do warunków polskich, do realnych stawów hodowlanych oraz do wspólnego API Straży Przyszłości.

Poniższe repozytoria są szczególnie cenne, bo mogą przyspieszyć budowę monitoringu jakości wody, lekkich węzłów terenowych i warstwy edge dla akwakultury:

### 1. Gotowe systemy monitoringu jakości wody

- **KnowFlow_AWM**  
  Link: [https://github.com/KnowFlow/KnowFlow_AWM](https://github.com/KnowFlow/KnowFlow_AWM)  
  Bardzo wartościowy punkt startowy dla otwartego monitoringu jakości wody. Obejmuje pomiary takich parametrów jak temperatura, pH i dissolved oxygen. To świetny materiał do adaptacji dla osób, które chcą zrozumieć architekturę całego urządzenia i firmware.

- **IoT-WQMS**  
  Link: [https://github.com/pkErbynn/IoT-WQMS](https://github.com/pkErbynn/IoT-WQMS)  
  Dobry przykład kompletnego przepływu: czujniki, mikrokontroler, backend, baza danych, dashboard i alerty. Repo może być szczególnie cenne dla tych, którzy chcą budować pełny tor `pomiar -> przesył -> analiza -> wizualizacja`.

- **IoT-Water-Quality-Monitoring**  
  Link: [https://github.com/JuliaSteiwer/IoT-Water-Quality-Monitoring](https://github.com/JuliaSteiwer/IoT-Water-Quality-Monitoring)  
  Bardzo ciekawy projekt dla rozproszonych węzłów pomiarowych. Zawiera wątki związane z LoRaWAN, deep sleep i wieloma parametrami jakości wody, w tym pH i dissolved oxygen. To może być skarb dla osób myślących o czujnikach terenowych o niskim poborze energii.

### 2. Klocki do budowy własnych węzłów i driverów sensorów

- **atlas_scientific**  
  Link: [https://github.com/jvsalo/atlas_scientific](https://github.com/jvsalo/atlas_scientific)  
  Zestaw narzędzi CLI do obsługi czujników Atlas Scientific dla pH, EC i dissolved oxygen. Bardzo wartościowy dla osób, które chcą budować stabilny pomiar na Raspberry Pi lub innym lekkim węźle Linuxowym.

- **Renke_DissolvedOxygen_Sensor**  
  Link: [https://github.com/bartzdev/Renke_DissolvedOxygen_Sensor](https://github.com/bartzdev/Renke_DissolvedOxygen_Sensor)  
  Konkretny klocek do priorytetowego dla nas parametru, czyli natlenienia. Jeśli ktoś chce zająć się przede wszystkim warstwą `dissolved oxygen`, to tu jest bardzo dobry materiał startowy pod ESP32 i urządzenia terenowe.

- **M5StickC_PH_sensor**  
  Link: [https://github.com/McOrts/M5StickC_PH_sensor](https://github.com/McOrts/M5StickC_PH_sensor)  
  Prosty i bardzo praktyczny przykład pod pH na ESP32. Może być szczególnie interesujący dla tych, którzy chcą szybko zbudować tani moduł pomiarowy lub przetestować odczyt pH bez wchodzenia od razu w duży system.

- **Open-Water-Level**  
  Link: [https://github.com/COAST-Lab/Open-Water-Level](https://github.com/COAST-Lab/Open-Water-Level)  
  To nie jest system stricte do chemii wody, ale może być bardzo cenny dla poziomu wody, ubytków i kontekstu przepływu. Dla części stawów i kanałów doprowadzających taki komponent może być niezwykle ważny.

### 3. Projekty pokrewne, z których można brać wzorce modułowości

- **Aquareo**  
  Link: [https://github.com/fnandes/aquareo](https://github.com/fnandes/aquareo)  
  Projekt akwaryjny, ale bardzo wartościowy jako przykład modułowej architektury na ESP32. Pokazuje, jak budować monitoring parametrów wody i lekkie komponenty terenowe bez zamykania się w jednym ciężkim systemie.

## Jak Strażnicy Przyszłości powinni z tego korzystać

Te repozytoria nie mają być traktowane jako gotowy „produkt końcowy”, tylko jako **surowiec strategiczny** dla Narodowych Sił Intelektualnych.

## Trzy repozytoria priorytetowe do realnego reuse

Jeżeli mamy zacząć od najbardziej użytecznych źródeł kodu, to na ten moment najlepsza trójka wygląda tak:

### 1. KnowFlow_AWM

Link: [https://github.com/KnowFlow/KnowFlow_AWM](https://github.com/KnowFlow/KnowFlow_AWM)

To jest najlepszy kandydat do przejęcia wzorców sprzętowych i firmware dla podstawowego monitoringu jakości wody.

Co warto z niego adaptować:

- architekturę urządzenia pomiarowego,
- obsługę czujników temperatury, pH i dissolved oxygen,
- logikę cyklicznego odczytu parametrów,
- podejście do modułowości sensorów i późniejszej rozbudowy,
- wzorce dla węzłów terenowych budowanych przez społeczność.

Do czego u nas to pasuje:

- do `POST /v1/observations`,
- do budowy społecznościowych węzłów pomiarowych,
- do pierwszych eksperymentów z natlenieniem i pH w realnym stawie.

### 2. IoT-WQMS

Link: [https://github.com/pkErbynn/IoT-WQMS](https://github.com/pkErbynn/IoT-WQMS)

To jest najlepszy kandydat do przejęcia wzorców pełnego przepływu danych od sensora do backendu.

Co warto z niego adaptować:

- logikę przesyłania danych z mikrokontrolera do serwera,
- strukturę prostego backendu i przechowywania obserwacji,
- wzorce alertów i wizualizacji wyników,
- pomysł na prosty tor `pomiar -> zapis -> analiza -> odczyt wyniku`.

Do czego u nas to pasuje:

- do `openapi/fish_pond_api_v1.yaml`,
- do budowy `adapters/provider_template/`,
- do późniejszego `pipelines/demo/` i prostego dashboardu lub eksportu danych.

### 3. IoT-Water-Quality-Monitoring

Link: [https://github.com/JuliaSteiwer/IoT-Water-Quality-Monitoring](https://github.com/JuliaSteiwer/IoT-Water-Quality-Monitoring)

To jest najlepszy kandydat do przejęcia wzorców dla rozproszonych i energooszczędnych węzłów danych.

Co warto z niego adaptować:

- wzorce komunikacji dla czujników pracujących daleko od infrastruktury,
- podejście do niskiego poboru energii i pracy okresowej,
- logikę rozproszonego zbierania pomiarów,
- pomysły na stacje terenowe, które nie muszą mieć stałego Wi-Fi.

Do czego u nas to pasuje:

- do stawów oddalonych od zabudowań,
- do społecznościowych instalacji DIY,
- do budowy tanich węzłów z ESP32, LoRa i ewentualnie starym smartfonem jako bramką danych.

## Co konkretnie powinniśmy z tych repo wyciągać

Najlepsza ścieżka pracy nie polega na kopiowaniu całych cudzych systemów. Lepiej wyciągać z nich tylko to, co wzmacnia nasz własny standard.

Z repozytoriów zewnętrznych warto przejmować:

- sterowniki i biblioteki do sensorów,
- przykłady kalibracji czujników,
- struktury odczytu i próbkowania danych,
- lekkie wzorce transmisji HTTP, MQTT albo LoRa,
- rozwiązania dla pracy w terenie i przy słabym zasilaniu,
- wzorce zapisu lokalnego przy chwilowej utracie łączności.

Nie powinniśmy bezrefleksyjnie przejmować:

- całej obcej architektury backendowej jako naszego rdzenia,
- cudzych modeli danych jako formatu nadrzędnego,
- zamkniętych zależności sprzętowych lub usługowych,
- logiki, która związałaby nas z jednym dostawcą albo jedną platformą.

## Jak to przełożyć na zadania dla społeczności

Każdy zainteresowany Strażnik Przyszłości może wejść w ten projekt jedną z trzech ścieżek:

### Ścieżka 1: sensory i elektronika

- testowanie sterowników pH, DO, temperatury i przepływu,
- porównywanie jakości odczytów,
- dokumentowanie kalibracji i stabilności pomiarów,
- budowa węzłów terenowych na ESP32 lub Raspberry Pi.

### Ścieżka 2: integracja i API

- mapowanie danych z cudzych repo do naszego schematu `fish_pond_v1`,
- tworzenie adapterów providerów,
- dopracowanie payloadów dla `observations` i `events`,
- budowa prostych mostów dla importu danych z istniejących systemów.

### Ścieżka 3: edge i analiza zachowania ryb

- szukanie lekkich modeli pod stare smartfony,
- testowanie analizy obrazu na małej liczbie klatek,
- zamiana obrazu na lekkie wyniki analityczne,
- budowa warstwy `fish_behavior_summary`, bez pchania surowego wideo do API.

Najbardziej wartościowe działania społeczności to:

- analiza, które fragmenty kodu są stabilne i warte przejęcia,
- mapowanie gotowych sterowników i formatów danych do naszego wspólnego API,
- dokumentowanie kalibracji czujników pH, DO, temperatury, amoniaku i przepływu,
- przygotowanie lekkich wersji dla ESP32, Raspberry Pi i starych smartfonów,
- wyciąganie z obcych repo tego, co uniwersalne, bez uzależniania się od ich całej architektury.

## Ważny przekaz dla pasjonatów

Jeżeli interesuje Cię elektronika, IoT, sensory, ESP32, Raspberry Pi, stare smartfony, akwakultura albo analiza obrazu w terenie, to ten obszar jest prawdopodobnie jednym z największych skarbów całego repozytorium.

Tutaj naprawdę nie chodzi o „wymyślanie wszystkiego od nowa”. Chodzi o to, żeby:

- znaleźć gotowy kod,
- zrozumieć go,
- dopracować go do naszych warunków,
- opisać go porządnie,
- a potem przekształcić w trwały dorobek Straży Przyszłości.

**Kod już jest. Potrzeba tylko ludzi, którzy potrafią go twórczo zaadaptować.**

## Backlog Issues dla Strażników Przyszłości

Poniżej znajduje się pierwszy operacyjny backlog dla tego projektu. Każdy z tych punktów można zamienić w osobne Issue na GitHubie.

### `issue:aq-01` Adaptacja odczytu dissolved oxygen dla ESP32

- Przeanalizować repo `Renke_DissolvedOxygen_Sensor`.
- Sprawdzić, jak najlepiej mapować odczyt do pola `dissolved_oxygen_mg_l`.
- Udokumentować wymagania sprzętowe, konwertery i kalibrację.

### `issue:aq-02` Adaptacja odczytu pH dla taniego węzła pomiarowego

- Przeanalizować repo `M5StickC_PH_sensor` oraz rozwiązania Atlas Scientific.
- Porównać stabilność i koszt wariantów pH.
- Opisać minimalny tor `czujnik -> odczyt -> normalize()`.

### `issue:aq-03` Węzeł terenowy jakości wody na ESP32

- Połączyć odczyt temperatury, pH i DO w jednym lekkim firmware.
- Zaprojektować format danych zgodny z `fish_pond_v1`.
- Przygotować referencyjny adapter lub eksport JSON.

### `issue:aq-04` Provider społecznościowy oparty o stary smartfon

- Opisać architekturę, w której stary smartfon działa jako bramka danych.
- Sprawdzić komunikację z ESP32 przez Wi-Fi, Bluetooth lub USB OTG.
- Zdefiniować minimalny proces buforowania i wysyłki danych do API.

### `issue:aq-05` Walidacja jakości danych pomiarowych

- Rozszerzyć reguły walidacji o zakresy ostrzegawcze i diagnostyczne.
- Rozróżnić dane `measured`, `estimated` i `simulated`.
- Dodać czytelne komunikaty dla błędnych jednostek i niepełnych pomiarów.

### `issue:aq-06` Reguły rekomendacyjne dla ryzyka przyduchy

- Doprecyzować progi dla `dissolved_oxygen`, `pH`, temperatury i amoniaku.
- Dodać więcej `reason_codes`.
- Porównać zachowanie modelu dla kilku przykładowych scenariuszy stawu.

### `issue:aq-07` Edge-first analiza zachowania ryb

- Poszukać lekkich modeli możliwych do uruchomienia na starych smartfonach.
- Ograniczyć wynik do prostych metryk: aktywność, zachowanie przy powierzchni, anomalie.
- Zasilić endpoint `POST /v1/events` zamiast przesyłać pełne wideo.

### `issue:aq-08` Anomaliowe klipy wideo jako materiał pomocniczy

- Zbadać lokalny bufor kołowy dla krótkich klipów.
- Opracować zasady zapisu tylko przy wykryciu anomalii.
- Nie dopuszczać ciągłego przesyłania strumienia wideo do publicznego API.

### `issue:aq-09` Import danych z zewnętrznego providera do wspólnego schematu

- Rozwinąć `adapters/provider_a/` jako wzorzec realnej integracji.
- Pokazać mapowanie natywnego payloadu providera do `SensorObservation`.
- Udowodnić, że model daje ten sam wynik niezależnie od dostawcy.

### `issue:aq-10` Demo end-to-end dla repozytorium

- Utrzymać działający przepływ `sample data -> adapter -> model -> recommendation`.
- Dodać instrukcję uruchomienia dla nowych współtwórców.
- Użyć tego demo jako punktu wejścia dla nowych Strażników Przyszłości.

### `issue:aq-11` Checklist kalibracji czujników

- Przygotować checklistę dla pH, DO, temperatury i opcjonalnie amoniaku.
- Opisać częstotliwość kalibracji i typowe błędy.
- Związać dokumentację kalibracyjną z jakością danych w repo.

### `issue:aq-12` Dokumentacja przeglądu repozytoriów do adaptacji

- Rozpisać, które moduły z `KnowFlow_AWM`, `IoT-WQMS` i `IoT-Water-Quality-Monitoring` są warte przejęcia.
- Odróżnić elementy przydatne od tych, które nie pasują do naszego standardu.
- Zostawić jasne notatki dla kolejnych osób wchodzących do projektu.

## Inspiracje i źródła:
- [Wideo: Smart Fish Farming](https://www.youtube.com/watch?v=N84PUuxThP4)
- [Projekt Open Source: IFishFarm (GitHub)](https://github.com/HussamElden/IFishFarm)

---
*Intelekt wyprzedza kapitał!*
