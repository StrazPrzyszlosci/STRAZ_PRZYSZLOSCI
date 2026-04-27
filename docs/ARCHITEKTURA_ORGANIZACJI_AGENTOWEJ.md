# Architektura Organizacji Agentowej

## Cel dokumentu

Ten dokument opisuje docelowy kierunek rozwoju Straży Przyszłości jako **oddolnej organizacji agentowej AI**, której głównym motorem nie jest przypadkowe wdrażanie pojedynczych automatyzacji, lecz **analiza potencjału**, budowa kolejnych stopni prowadzących do celu i uruchamianie tylko tych procesów, które mają najlepszy stosunek efektu do wysiłku.

Uzupełnieniem tego dokumentu jest:

- [Plan Rozwoju Organizacji Agentowej](PLAN_ROZWOJU_ORGANIZACJI_AGENTOWEJ.md)
- [Encje i Workflowy Organizacji Agentowej](ENCJE_I_WORKFLOWY_ORGANIZACJI_AGENTOWEJ.md)
- [Instrukcja Rozwojowa Dla Agenta](INSTRUKCJA_ROZWOJOWA_DLA_AGENTA.md)
- [Review Rotation Governance](REVIEW_ROTATION_GOVERNANCE.md)

To nie jest wizja jednego bota ani jednego pipeline'u. Chodzi o budowę zorganizowanego ekosystemu:

- analizującego potencjał wielu obszarów,
- samodzielnie wykrywającego bariery dalszego rozwoju,
- tworzącego podcele, procesy i artefakty potrzebne do ich pokonania,
- angażującego ludzi i ich lokalnych agentów jako rozproszoną siatkę wykonawczą,
- utrzymującego ciągłą ocenę jakości, kosztu i skuteczności własnych działań.

## Założenie nadrzędne

Najpierw analizujemy potencjał, potem projektujemy drogę wdrożenia, a dopiero na końcu uruchamiamy automatyzację.

W praktyce oznacza to, że:

- około 90% pracy systemu powinno dotyczyć gromadzenia danych, RAG, analiz porównawczych, planowania, projektowania i optymalizacji,
- około 10% pracy powinno przechodzić do właściwego wdrożenia i uruchomienia procesów wykonawczych,
- system nie może rozszerzać się chaotycznie przez dokładanie kolejnych "fajnych agentów",
- każdy nowy kierunek musi najpierw przejść przez bramkę oceny potencjału.

Ważna zasada dodatkowa:

- automatyzacja nie może ograniczać się do zasobów wskazanych ręcznie z góry,
- system ma samodzielnie **szukać, rozpoznawać i klasyfikować zasoby**, które można przekształcić w kolejne zdolności działania.
- system musi również wykrywać **zjawiska niekorzystne dla ogółu**, takie jak nepotyzm, korupcja, zawłaszczenie wspólnych efektów pracy, omijanie jawnego review i niejawna centralizacja kontroli.

## Zewnętrzne repozytoria jako warstwa RAG

Zewnętrzne repozytoria linkowane z tego repozytorium należy traktować jako **otwartą warstwę RAG wzorców, architektur i gotowych klocków**.

Na etapie strategicznym źródłem kontekstu są przede wszystkim ich `README`, dokumentacja i publiczny opis działania. Ta warstwa służy do:

- rozpoznawania, jakie klasy problemów zostały już rozwiązane,
- identyfikowania gotowych modułów do adaptacji,
- porównywania alternatywnych ścieżek wdrożeniowych,
- tworzenia dossier potencjału dla nowych kierunków,
- zasilania agentów planujących, badawczych i onboardingowych wspólną bazą odniesień.

Ta warstwa nie jest automatycznie źródłem prawdy dla wdrożeń. Najpierw służy jako **RAG otwartych wzorców**, a dopiero później może przejść do etapu adaptacji kodu we własnym standardzie Straży Przyszłości.

Najważniejsze klastry tej warstwy to:

- orkiestracja i samodoskonalenie agentów: `LangGraph`, `ABSTRAL`, `GEPA`, `OpenEvolve`,
- terenowe i offline node'y wiedzy: `Project N.O.M.A.D.`,
- reuse elektroniki i CAD: `ecoEDA`, `Ki-nTree`, `KiCAD-MCP-Server`, `HydroTek`,
- sensoryka i produkcja żywności: `KnowFlow_AWM`, `IoT-WQMS`, `IoT-Water-Quality-Monitoring`, `atlas_scientific`, `Renke_DissolvedOxygen_Sensor`, `M5StickC_PH_sensor`,
- edge/mobile/mesh: `OpenBot`, `selfphone`, `mqtt-sensor-android`, `Sideband`, `MeshCore`, `Meshtastic`,
- przyszłe pola "dirty automation": `MushR`, `Polyformer`, `DetectAnimalsInRoads`, `Poultry_Bot`, `smart-waste-segregator`.

## Pięć warstw organizacji agentowej

### 1. Warstwa Analizy Potencjału

To jest rdzeń całego systemu.

Jej zadaniem jest tworzenie `PotentialDossier` dla każdego kierunku rozwoju. Takie dossier powinno odpowiadać na pytania:

- jaki problem społeczny lub gospodarczy dany kierunek rozwiązuje,
- jaki jest potencjał wpływu społecznego,
- jaki jest koszt wejścia i koszt utrzymania,
- jak łatwo zdobyć dane, sprzęt i kompetencje,
- czy istnieją już gotowe wzorce w zewnętrznych repozytoriach,
- jaki jest czas do pierwszego użytecznego rezultatu,
- czy kierunek nadaje się do pracy wolontariuszy z lokalnymi agentami.

Warstwa ta porównuje kierunki między sobą i utrzymuje ranking priorytetów rozwojowych.

Ta warstwa powinna również utrzymywać **resource scouting**, czyli aktywne wyszukiwanie zasobów możliwych do użycia przez inicjatywę.

Zasobem może być:

- elektrośmieć lub donor hardware,
- darmowa moc obliczeniowa,
- notebook Kaggle lub Colab możliwy do uruchomienia przez wolontariusza,
- gotowy kod open-source i jego README jako zasób intelektualny,
- dane terenowe, raporty i dokumentacja,
- ogloszenie `oddam za darmo`, oferta lokalna z odbiorem wlasnym albo post typu `smieciarka jedzie`,
- zgloszenie zapotrzebowania na czesc, modul, urzadzenie albo odbior sprzetu,
- wolne urządzenia, odpady produkcyjne i nadwyżki magazynowe,
- lokalna infrastruktura, energia, przestrzeń robocza i logistyka.

Najwieksza dzwignia tej warstwy nie zawsze lezy w pojedynczym zasobie. Często pojawia sie dopiero po polaczeniu kilku slabych sygnalow:

- darmowy albo bardzo tani zasob,
- konkretne lokalne zapotrzebowanie,
- bliska logistyka i niski koszt przejecia,
- znana sciezka reuse, naprawy albo dalszej automatyzacji.

Dlatego system powinien analizowac nie tylko obiekty, ale rowniez relacje miedzy podaza, popytem, lokalizacja, czasem i kosztem aktywacji zasobu.

Dlatego `PotentialDossier` powinno być powiązane nie tylko z problemem, ale też z klasami zasobów, które system sam wykrywa i ocenia.

### 2. Warstwa Drabiny Kompetencji

System nie powinien próbować przeskakiwać od wizji do pełnej autonomii jednym ruchem.

Musi budować sobie kolejne stopnie prowadzące do celu:

- wykrywać główne bariery,
- przekształcać bariery w podcele,
- rozpoznawać, jakich danych, umiejętności i narzędzi brakuje,
- tworzyć eksperymenty prowadzące do zmniejszenia niepewności,
- wybierać następny najrozsądniejszy krok zamiast największego kroku.

Ta warstwa odpowiada za byty takie jak:

- `CapabilityGap`,
- `Hypothesis`,
- `Experiment`,
- `ReadinessGate`.

### 3. Warstwa Wykonawcza Wolontariuszy i Agentów

Na obecnym etapie najrealistyczniejszym modelem nie jest "pełna autonomia chmurowa", tylko **rozproszona sieć ludzi nadzorujących lokalnych agentów AI**.

To powinno działać podobnie do modelu SETI lub rozproszonego open source:

- repozytorium publikuje dobrze opisane pakiety pracy,
- wolontariusz klonuje repozytorium,
- lokalny agent dostaje kontekst i wykonuje wycinek zadania,
- człowiek nadzoruje, uruchamia notebook lub skrypt, ocenia wynik i otwiera PR albo raport,
- wynik wraca do wspólnego systemu wiedzy.

Każdy `ExecutionPack` powinien zawierać:

- cel zadania,
- wejściowy kontekst i źródła RAG,
- sugerowany prompt dla agenta,
- oczekiwany artefakt,
- kryteria odbioru,
- docelowe miejsce publikacji: `Issue`, `PR`, raport, snapshot, notebook, eksport danych.

Jednym z najważniejszych typów `ExecutionPack` na obecnym etapie powinien być `KaggleNotebookPack`.

To pakiet pracy, w którym:

- repozytorium dostarcza gotowy notatnik lub szkielet notatnika do uruchomienia w `Kaggle`,
- lokalny agent wolontariusza instruuje go krok po kroku, jak pobrać notebook, ustawić sekrety i uruchomić zadanie,
- notebook korzysta z własnych darmowych zasobów obliczeniowych wolontariusza,
- wyniki są zapisywane do forka wolontariusza, a następnie trafiają do upstream przez `Pull Request`.

Ten model jest ważny, bo pozwala przekształcić rozproszoną społeczność w sieć realnych węzłów wykonawczych bez konieczności centralnego finansowania GPU lub chmury.

W praktyce `Kaggle` może być traktowane jako **darmowy dostawca zasobów obliczeniowych aktywowanych przez wolontariuszy**. To znaczy, że inicjatywa nie posiada tych zasobów centralnie, ale potrafi je uruchamiać przez dobrze przygotowane notebooki i execution packi dostarczane ludziom przez agentów.

## Model wolontariackich notatników Kaggle

W projektach badawczych i data-heavy Straż Przyszłości powinna świadomie wykorzystywać model:

```text
repo -> execution pack -> notebook Kaggle -> fork wolontariusza -> commit -> PR -> review -> merge
```

W tym modelu:

- agent repozytoryjny wybiera sensowny notebook do uruchomienia,
- przygotowuje instrukcję dla wolontariusza,
- wolontariusz uruchamia notebook na własnym koncie `Kaggle`,
- notebook pracuje na kluczach i darmowych limitach przypisanych do tego konta,
- wynik nie trafia bezpośrednio do głównego repozytorium, tylko najpierw do forka wolontariusza,
- upstream otrzymuje dopiero uporządkowany `PR` z artefaktami, logami i opisem przebiegu.

To jest praktyczny sposób, w jaki inicjatywa może korzystać z rozproszonej darmowej mocy obliczeniowej wolontariuszy bez budowy własnej kosztownej infrastruktury centralnej.

Najważniejsze zastosowania tego modelu to:

- autonomiczne notatniki discovery i enrichment dla `Project 13`,
- masowe przetwarzanie danych PDF, OCR i materiałów wideo,
- eksperymenty porównawcze dla analiz potencjału,
- batchowe generowanie snapshotów wiedzy i raportów porównawczych,
- przygotowywanie datasetów i artefaktów do kolejnych etapów review.

Docelowo należy myśleć nie o pojedynczych notebookach, lecz o **łańcuchach automatyzacji uruchamianych przez notebooki Kaggle**. Każdy etap łańcucha może być osobnym `ExecutionPack`, a rozproszeni wolontariusze mogą uruchamiać różne etapy na własnych darmowych zasobach.

## Zasady bezpieczeństwa dla notatników Kaggle

Ten model musi być jawnie **opt-in** i bezpieczny dla wolontariusza.

Dlatego obowiązują następujące zasady:

- wolontariusz sam decyduje, czy chce zużyć własny darmowy przydział `Kaggle`,
- notebook korzysta wyłącznie z sekretów ustawionych świadomie przez wolontariusza na jego koncie,
- repozytorium nie przechowuje ani nie publikuje prywatnych kluczy wolontariusza,
- preferowany jest zapis do własnego forka wolontariusza, a nie bezpośredni push do upstream,
- każdy `KaggleNotebookPack` powinien jasno mówić, jakie sekrety są potrzebne i do czego służą,
- notebook nie powinien wykonywać działań poza zadeklarowanym zakresem bez wiedzy wolontariusza,
- wynik obliczeń powinien być możliwy do zreviewowania przed otwarciem `PR`.

### 4. Warstwa Wdrożeniowa

Dopiero po przejściu przez analizę i review system powinien przechodzić do tworzenia procesów wykonawczych.

Na start najlepszym polem wdrożeniowym są istniejące klocki repo:

- `cloudflare/` jako warstwa wejścia, operator-assistant i ingress workflow,
- `PROJEKTY/13_baza_czesci_recykling/` jako pierwszy pełny loop `discovery -> queue -> catalog -> export -> PR`,
- `api/`, `schemas/`, `openapi/`, `adapters/` jako fundament dla rozproszonych providerów danych,
- `reports/` i snapshoty wiedzy jako warstwa pamięci uporządkowanej.

Warstwa wdrożeniowa nie może jednak kończyć się na software i dokumentach. Musi mieć również **wyjście do warstwy sprzętowej**:

- odzyskane smartfony, routery i moduły obliczeniowe jako edge compute,
- odzyskane części i podzespoły jako baza do budowy nowych urządzeń,
- urządzenia automatyzacji budowane z elektrośmieci jako narzędzia dalszego rozwoju systemu.

To oznacza, że docelowym wynikiem organizacji agentowej mogą być nie tylko raporty, katalogi i PR-y, ale również:

- sterowniki,
- węzły pomiarowe,
- bramki danych,
- stanowiska testowe,
- lekkie komputery robocze,
- urządzenia potrzebne do kolejnych procesów automatyzacji.

Najpełniej opisuje to kierunek:

- [17. Autonomiczne Przetwarzanie Elektrośmieci na Hardware Automatyzacji](../PROJEKTY/17_autonomiczne_przetwarzanie_elektrosmieci_na_hardware.md)

Wdrożenie musi pozostawać stopniowalne:

- `research`: tworzenie kandydatów i hipotez,
- `assist`: przygotowanie draftów, raportów, PR-ów i planów,
- `deploy`: tylko po przejściu bramek jakości i zatwierdzeniu człowieka.

### 5. Warstwa Samodoskonalenia

Dopiero po zbudowaniu stabilnych logów, benchmarków i metryk jakości można sensownie włączyć automatyczną optymalizację.

Rola frameworków zewnętrznych powinna być rozdzielona:

- `LangGraph` jako warstwa stanowej orkiestracji workflowów,
- `ABSTRAL` jako inspiracja do przeszukiwania topologii agentów i zestawów skilli,
- `GEPA` jako narzędzie do poprawy promptów, decyzji i policy routing,
- `OpenEvolve` jako narzędzie do ewolucji kodu, procedur i evaluatorów.

Te mechanizmy nie powinny sterować rdzeniem od pierwszego dnia. Najpierw system musi mieć:

- pełne logi przebiegów,
- ocenę artefaktów,
- jawne kryteria sukcesu,
- benchmarki i testy powtarzalności.

## Kanoniczny przebieg pracy

Docelowy przebieg organizacji agentowej powinien wyglądać tak:

```text
sygnal -> dossier potencjalu -> ranking -> bariera -> podcel -> execution pack ->
praca wolontariusza + lokalnego agenta -> artefakt -> review -> approval ->
promocja do wspolnej bazy wiedzy / PR / deployment -> ewaluacja -> poprawa procesu
```

Sygnałem może być:

- nowe repo zewnętrzne,
- nowy problem społeczny,
- nowa obserwacja terenowa,
- nowy zasób sprzętowy,
- nowy donor parts w katalogu,
- nowe ogloszenie `oddam za darmo` albo `sprzedam tanio`,
- nowe zgloszenie zapotrzebowania na czesc, modul albo urzadzenie,
- nowa koincydencja kilku sygnalow, ktore razem tworza okazje o wysokiej dzwigni,
- nowa możliwość uruchomienia darmowych zasobów obliczeniowych.

Docelowo system powinien nie tylko reagować na takie sygnały, ale również sam ich aktywnie szukać:

- skanować klasy odpadów, nadwyżek i wolnych urządzeń,
- skanowac grupy spolecznosciowe, portale ogloszeniowe, aukcje lokalne i sygnaly zapotrzebowania,
- rozpoznawać źródła darmowych lub tanich zasobów obliczeniowych,
- identyfikować gotowe otwarte narzędzia i architektury do adaptacji,
- laczyc darmowa podaz z realnym popytem i tania logistyka przejecia,
- porównywać, które zasoby najlepiej nadają się do budowy kolejnych zdolności automatyzacji.

## Minimalne byty, które trzeba dodać do systemu

Aby przejść od zbioru automatów do organizacji agentowej, potrzebny jest wspólny model danych i przebiegów:

- `PotentialDossier`
- `CapabilityGap`
- `Task`
- `Run`
- `Artifact`
- `Approval`
- `ExecutionPack`
- `ExperimentLog`
- `ResourceOffer`
- `DeploymentPlan`

Te byty nie muszą od razu mieć rozbudowanego UI. Wystarczy, żeby miały stabilną reprezentację w `D1`, `JSON`, `Markdown` lub `Issue/PR metadata`.

## Priorytet pierwszego wdrożenia

Najbardziej realistyczny pierwszy klin nie powinien być wybrany przypadkowo.

Kazdy projekt w repo powinien byc rozumiany jako narzedzie sluzace wyzszemu celowi organizacji.
Nie rozwijamy projektu tylko dlatego, ze juz istnieje lub ma aktywny kontekst.
Rozwijamy go wtedy, gdy:

- aktywuje nowy zasob,
- buduje reusable capability,
- wzmacnia wspolna pamiec i provenance,
- uruchamia wolontariacka warstwe wykonawcza,
- przybliza organizacje do realnego dzialania w swiecie fizycznym,
- poprawia governance i odpornosc na przechwycenie.

Jesli projekt przestaje spelniac te role albo blokuje sie na zewnetrznych zaleznosciach, organizacja powinna umiec przelaczyc energie na kolejny ruch portfelowy o wiekszej dzwigni.

Na obecnym etapie repo najmocniej wspiera dwa kierunki:

- **analizę potencjału i organizację pracy**, bo ma już onboarding, bundle wiedzy, bota, API i strukturę dokumentacyjną,
- **recykling i reuse elektroniki**, bo ma już działający zalążek pełnego łańcucha `discovery -> queue -> catalog -> export -> PR`.

Dlatego pierwszy etap powinien brzmieć:

1. zbudować `Straż OS`, czyli wspólny system pracy agentów,
2. użyć `Project 13` jako pierwszego poligonu produkcyjnego,
3. użyć toru providerów danych jako drugiego pilota dla świata fizycznego,
4. rozszerzyć katalog i reuse workflow na warstwę sprzętową i obliczeniową z elektrośmieci,
5. dopiero później uruchamiać cięższą warstwę CAD, robotyki i optymalizacji ewolucyjnej.

## Rola człowieka

W najbliższych etapach obowiązuje model **human-in-the-loop**.

Oznacza to, że AI może samodzielnie:

- zbierać dane i README,
- tworzyć dossier potencjału,
- porównywać kierunki,
- budować execution packi,
- przygotowywać drafty PR, raportów i notebooków,
- proponować przebudowę procesów.

Ale nie powinno samodzielnie bez zatwierdzenia człowieka:

- publikować finalnych decyzji strategicznych,
- sterować światem fizycznym,
- wykonywać działań kosztowych,
- promować niezweryfikowanych danych do kanonicznej bazy wiedzy,
- scalać krytycznych zmian infrastrukturalnych.

## Roadmapa

### Etap 1. Straż OS

Najpierw trzeba zbudować wspólny model pracy agentów:

- `task/run/artifact/approval`,
- provenance,
- review gates,
- separacja `research`, `assist`, `deploy`,
- porządek między ingress, pamięcią i orkiestracją.

### Etap 2. Silnik analizy potencjału

Następnie trzeba uruchomić ranking kierunków rozwoju:

- dossier potencjału,
- scoring,
- porównanie koszt/efekt,
- rekomendacja kolejnych pilotów.

### Etap 3. Sieć wolontariuszy z agentami

Repozytorium powinno zacząć publikować gotowe paczki pracy:

- notebooki do Kaggle/Colab,
- runbooki uruchomień,
- pakiety researchowe,
- pakiety kuracji danych,
- pakiety integracyjne do PR.

Szczególnie ważne powinny być tutaj:

- autonomiczne notebooki `Kaggle` do uruchomienia na kontach wolontariuszy,
- instrukcje dla lokalnych agentów, jak prowadzić wolontariusza przez uruchomienie,
- standard `fork -> commit -> PR`, który zamienia darmowe zasoby obliczeniowe społeczności w uporządkowany wkład do inicjatywy.

### Etap 4. Pierwszy pełny loop produkcyjny

`Project 13` powinien zostać doprowadzony do formy:

- kandydat,
- review-ready,
- katalog,
- eksport do downstream,
- draft PR,
- akceptacja,
- promocja do wspólnej bazy wiedzy.

### Etap 5. Drugi pilot świata fizycznego

Po ustabilizowaniu pierwszego loopa należy rozwinąć kierunek providerów danych i produkcji żywności:

- sensoryka,
- smartfon edge,
- centralne API,
- snapshoty wiedzy,
- rekomendacje dla procesów terenowych.

### Etap 6. Warstwa Hardware z Elektrośmieci

Po zbudowaniu stabilnego loopa danych i pierwszego pilota świata fizycznego trzeba rozszerzyć system o sprzęt budowany z odzysku:

- katalog modułów obliczeniowych i wykonawczych,
- kwalifikację odzyskanych urządzeń do dalszego użycia,
- projektowanie urządzeń reuse z części i modułów,
- budowę hardware potrzebnego do dalszych procesów automatyzacji.

Tu celem nie jest tylko "recykling", ale zamiana elektrośmieci w:

- edge compute,
- sterowniki,
- urządzenia pomiarowe,
- stanowiska testowe,
- sprzęt dla kolejnych łańcuchów automatyzacji.

### Etap 7. Samodoskonalenie

Dopiero wtedy należy włączyć pełniejszą optymalizację promptów, kodu i architektury agentów.

## Kryteria sukcesu

Organizacja agentowa działa poprawnie, gdy:

- analiza potencjału faktycznie steruje kolejnością prac,
- wolontariusz z lokalnym agentem może dostać gotowy execution pack i dowieźć użyteczny artefakt,
- artefakty mają ślad pochodzenia i przechodzą przez review,
- system potrafi zamieniać wyniki pracy w trwałe elementy wspólnej bazy wiedzy,
- kolejne procesy są uruchamiane dlatego, że przeszły ranking potencjału, a nie dlatego, że były najgłośniejszym pomysłem,
- optymalizacja dotyczy całych ścieżek działania, a nie tylko pojedynczych promptów.

Najważniejszym wynikiem nie jest liczba agentów, lecz zdolność organizacji do **systematycznego budowania kolejnych stopni prowadzących do realnych wdrożeń dla dobra wspólnego**.
