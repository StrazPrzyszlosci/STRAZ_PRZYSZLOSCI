# Przykłady Gotowego Kodu i Otwartych Wzorców

## Cel dokumentu

Ten dokument zbiera przykłady repozytoriów i projektów, które pokazują, że **kod, wzorce architektoniczne i otwarte modele współpracy już istnieją**. Zadaniem Straży Przyszłości nie jest wymyślanie wszystkiego od zera, lecz mądre rozpoznawanie, adaptacja i rozwijanie gotowych rozwiązań we własnym, wspólnym standardzie.

To ważne również z punktu widzenia onboardingu. Nowa osoba nie musi mieć od razu własnego urządzenia pomiarowego, sterownika, czujników ani dostępu do stawu, żeby wnieść realny wkład. Jeżeli dane będą dostarczane przez providerów i społeczność przez wspólne API, to równie ważna staje się praca nad:

- architekturą danych,
- adapterami i kontraktami API,
- walidacją jakości danych,
- analizą przypadków,
- dokumentacją i porządkowaniem wiedzy,
- modelami rekomendacyjnymi,
- kuracją gotowego kodu do adaptacji.

## Przykład referencyjny: openSenseMap

### Linki

- Repozytorium GitHub: [sensebox/openSenseMap](https://github.com/sensebox/openSenseMap)
- Strona projektu: [openSenseMap](https://sensebox.github.io/en/osem)
- FAQ i dokumentacja API: [openSenseMap FAQ](https://docs.sensebox.de/docs/misc/opensensemap/faq/)
- Film YouTube powiązany z repo: [openSenseMap na YouTube](https://www.youtube.com/watch?v=I8ZeT6hzjKQ)

### Dlaczego to jest ważny przykład dla Straży Przyszłości

`openSenseMap` jest bardzo dobrym wzorcem dla naszego myślenia o systemie opartym na danych dostarczanych przez API. To nie jest tylko projekt sprzętowy. To model, w którym:

- istnieje otwarta platforma do gromadzenia i eksploracji danych sensorycznych,
- dane mogą być wysyłane przez różne urządzenia i zewnętrzne aplikacje,
- społeczność może dokładać własne dane badawcze,
- warstwa API staje się wspólnym językiem współpracy,
- wartość projektu rośnie nie tylko dzięki hardware, ale też dzięki interpretacji, analizie i ponownemu wykorzystaniu danych.

To jest bardzo bliskie kierunkowi Straży Przyszłości, gdzie wspólne API ma stać się warstwą integrującą społecznościowe i partnerskie źródła danych, a repozytorium ma przechowywać standard, logikę, dokumentację i wiedzę opracowaną.

### Najważniejsza lekcja dla nowych Strażników

Nie trzeba mieć własnego urządzenia pomiarowego ani sterownika, żeby wejść do projektu i budować jego architekturę.

Jeżeli providerzy, partnerzy i społeczność dostarczają dane przez API, to inni Strażnicy mogą równolegle pracować nad:

- projektowaniem wspólnego schematu danych,
- adapterami i walidacją,
- klasyfikacją zdarzeń,
- modelami i rekomendacjami,
- dashboardami i raportami,
- dokumentacją przypadków,
- porządkowaniem backlogu i ścieżek wejścia dla kolejnych osób.

To jest pełnoprawny wkład intelektualny. W praktyce często właśnie taka praca przesądza o tym, czy z luźnego zestawu odczytów da się zbudować trwały dorobek techniczny.

### Co możemy z tego adaptować

Z `openSenseMap` warto czerpać przede wszystkim:

- sposób myślenia o otwartym ekosystemie danych,
- wzorzec, w którym API jest wspólną warstwą wejścia dla wielu źródeł,
- model społecznościowego dokładania danych badawczych,
- sposób pokazywania, że sprzęt i analiza danych są częścią jednego systemu,
- argumentację, że otwarta baza danych i otwarte standardy przyciągają współtwórców.

Nie chodzi o przejęcie całej architektury jako naszego rdzenia. Chodzi o wykorzystanie tego przykładu jako dowodu, że:

- otwarta warstwa danych może działać realnie,
- społeczność potrafi zasilać wspólny system,
- repozytorium może stać się miejscem kumulacji wiedzy, a nie tylko kodu.

## Jak używać takich przykładów w repozytorium Straży Przyszłości

Każdy taki przykład powinien odpowiadać na trzy pytania:

1. Co już działa i jaki problem rozwiązuje?
2. Co z tego da się zaadaptować do standardu Straży Przyszłości?
3. Jakie zadania mogą z tego wyniknąć dla nowych Strażników?

Jeżeli odpowiedź na te trzy pytania jest jasna, przykład nie jest ciekawostką, tylko realnym zasobem strategicznym.

## ecoEDA: Recykling E-Waste w KiCadzie

### Linki
- Repozytorium GitHub: [humancomputerintegration/ecoEDA](https://github.com/humancomputerintegration/ecoEDA/tree/main)
- Publikacja naukowa: [ecoEDA: Recycling E-Waste during Electronics Design](https://doi.org/10.1145/3586183.3606745)
- Wideo demonstracyjne: [YouTube - ecoEDA](https://youtu.be/XYMRXMVBfNg)

### Analiza Strategiczna

1. **Co już działa i jaki problem rozwiązuje?**
   ecoEDA rozwiązuje problem marnotrawstwa komponentów elektronicznych, które lądują na wysypiskach, mimo że są sprawne. Narzędzie integryje się z KiCadem i podpowiada projektantowi użycie części z recyklingu, generując tzw. "Bill of Teardowns" (BoT) – listę urządzeń, które należy pozyskać i rozmontować, by zbudować dany projekt.

2. **Co z tego da się zaadaptować do standardu Straży Przyszłości?**
   Przede wszystkim paradygmat projektowania "pod recykling". Zamiast BOMu opartego na zakupach, model BoT uczy nas budować z tego, co już mamy w narodowym zasobie elektrośmieci. Mechanizm subcircuit suggestions pozwala na zastępowanie nowoczesnych, drogich układów kaskadami prostszych elementów z odzysku.

3. **Jakie zadania mogą z tego wyniknąć dla nowych Strażników?**
   - Tworzenie otwartych baz danych urządzeń (inwentaryzacja popularnych w Polsce "złomów").
   - Rozwijanie i dostosowywanie skryptów ecoEDA do polskich realiów.
   - Integracja baz ecoEDA z projektami rolniczymi Straży.

## Ki-nTree: Automatyzacja Inwentaryzacji i Baz Części

### Linki
- Repozytorium GitHub: [sparkmicro/Ki-nTree](https://github.com/sparkmicro/Ki-nTree)
- Dokumentacja InvenTree: [InvenTree Documentation](https://docs.inventree.org/)
- Wideo demonstracyjne: [YouTube - Ki-nTree](https://www.youtube.com/watch?v=YeWBqOCb4pw)

### Analiza Strategiczna

1. **Co już działa i jaki problem rozwiązuje?**
   Ki-nTree automatyzuje proces dodawania nowych komponentów do bazy inwentaryzacyjnej InvenTree oraz tworzenia symboli i footprintów w KiCadzie. Rozwiązuje problem "żmudnej tabelki" – zamiast ręcznie wpisywać dane z PDF-ów, narzędzie zaciąga dane (noty katalogowe, parametry) i tworzy gotowe rekordy w kilka sekund.

2. **Co z tego da się zaadaptować do standardu Straży Przyszłości?**
   Wykorzystujemy Ki-nTree jako **silnik bazy danych dla AI**. Zamiast pisać własny system inwentaryzacji e-odpadów, używamy InvenTree jako backendu, a Ki-nTree jako adaptera. Naszym wkładem jest dopisanie modułu AI (wizja komputerowa/OCR), który rozpoznaje chip na śmieciach i "podaje" go do Ki-nTree.

3. **Jakie zadania mogą z tego wyniknąć dla nowych Strażników?**
   - Konfiguracja i hostowanie instancji InvenTree dla społeczności.
   - Rozwijanie modułu OCR, który automatycznie wyciąga symbole układów ze zdjęć i przekazuje je do API Ki-nTree.
   - Tworzenie adapterów dla specyficznych "rodzin" e-śmieci (np. bazy zamienników dla zasilaczy czy routerów).

## KiCAD-MCP-Server: Autonomiczne Projektowanie z Ai

### Linki
- Repozytorium GitHub: [mixelpixx/KiCAD-MCP-Server](https://github.com/mixelpixx/KiCAD-MCP-Server)
- Dokumentacja MCP: [Model Context Protocol](https://modelcontextprotocol.io/)

### Analiza Strategiczna

1. **Co już działa i jaki problem rozwiązuje?**
   Ten serwer MCP pozwala modelom językowym (Claude) na bezpośrednie sterowanie KiCadem (122 narzędzia w 16 kategoriach). Rozwiązuje problem progu wejścia w zaawansowane projektowanie PCB – Ai potrafi samo rysować schematy, układać piny i robić routing na podstawie opisu w języku naturalnym.

2. **Co z tego da się zaadaptować do standardu Straży Przyszłości?**
   To kluczowy element naszej wizji "Intelekt wyprzedza Kapitał". Wykorzystujemy ten kod jako most umożliwiający Ai projektowanie urządzeń na potrzeby Straży (np. czujników IoT, sterowników maszyn) z minimalnym zaangażowaniem wykwalifikowanych inżynierów.

3. **Jakie zadania mogą z tego wyniknąć dla nowych Strażników?**
   - Optymalizacja promptów inżynierskich dla Claude'a.
   - Testowanie i łatanie serwera MCP (szczególnie w środowisku Linux).
   - **MISJA SPECJALNA:** Integracja KiCAD-MCP z bibliotekami ecoEDA, by Ai autonomicznie projektowało PCB wyłącznie z części z recyklingu.
