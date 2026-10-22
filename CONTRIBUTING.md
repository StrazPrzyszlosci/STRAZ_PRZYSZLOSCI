# Jak zaangażować się w projekt (Poradnik i instrukcja obsługi)

Witamy w repozytorium **NARODOWYCH SIŁ INTELEKTUALNYCH**! Dziękujemy, że chcesz dołączyć do wspólnego wysiłku. Ten dokument ma na celu pomóc Ci w postawieniu pierwszych kroków – od zgłoszenia pomysłu do poprawnego scommitowania zmian.

Niezależnie od tego, czy pracujesz w IT, analizie danych, marketingu, czy zajmujesz się zarządzaniem – każda pomoc jest cenna.

## 1. Dołączenie do dyskusji (Dla wszystkich)

Nawet jeśli nie potrafisz programować, możesz aktywnie uczestniczyć w *"Burzy mózgów, analizie i planowaniu"*! 

**Jak to zrobić?**
1. Otwórz zakładkę **Issues** (Problemy/Zgłoszenia) w głównym menu repozytorium. **To serce naszego projektu – tutaj ma się roić jak w ulu!**
2. Masz pytanie? Pomysł? Widzisz błąd? **Wal śmiało do Issues!**
3. Przejrzyj otwarte tematy. Jeśli widzisz coś, na czym się znasz – zostaw komentarz. Twoja opinia jest częścią naszej wspólnej pracy.

### Co jeśli nie widzisz zadania dla siebie?
Repozytorium ma być żywym organizmem. Jeśli masz pytanie, genialny pomysł lub po prostu chcesz się przywitać i zapytać, gdzie możesz się przydać:
1. Kliknij **"New Issue"**.
2. **Wal śmiało z każdym pytaniem i pomysłem!** Chcemy, żeby w sekcji Issues roiło się od pytań, burzy mózgów i technicznych dyskusji.
3. Koordynatorzy i inni pasjonaci odpowiedzą Ci błyskawicznie, dopasowując zadanie do Twojego unikalnego potencjału.

---

## 2. Wnoszenie zmian (Fork & Pull Request)

Jeśli chcesz wnieść konkretny wkład do repozytorium (np. dodać kod, artykuł, instrukcję), postępuj zgodnie z modelem współtworzenia open source (tzw. "Fork & Pull Request").

### Krok po kroku: Jak to zrobić?

#### A. Stworzenie własnej kopii (Fork)
Wejdź na stronę naszego repozytorium: https://github.com/StrazPrzyszlosci/STRAZ_PRZYSZLOSCI i w prawym górnym rogu kliknij przycisk **"Fork"**. Zostanie utworzona kopia tego projektu na Twoim własnym koncie GitHub.

#### B. Pobranie plików na swój komputer (Clone)
Otwórz terminal (konsolę) na swoim komputerze i wpisz:
```bash
git clone https://github.com/TWOJA_NAZWA_UZYTKOWNIKA/STRAZ_PRZYSZLOSCI.git
cd STRAZ_PRZYSZLOSCI
```

#### C. Tworzenie gałęzi dla nowej funkcji (Branch)
Nigdy nie wprowadzaj zmian bezpośrednio na głównej gałęzi `main`. Zawsze twórz osobną gałąź na swoje poprawki:
```bash
git checkout -b nazwa-twojego-pomyslu
```

#### D. Wprowadzanie i zapisywanie zmian (Commit)
Zrób zmiany w plikach (napisz kod, poprawki itp.). Kiedy skończysz, zapisz je w historii u siebie lokalnie:
```bash
git add .
git commit -m "Krótki i zwięzły opis tego, co zmieniłeś"
```

#### E. Wysyłanie zmian na serwer (Push)
Wypchnij swoje zmiany do swojego forka na GitHubie:
```bash
git push origin nazwa-twojego-pomyslu
```

#### F. Zgłoszenie zmian do głównego projektu (Pull Request)
1. Wróć na stronę GitHuba, na swoje sforkowane repozytorium.
2. Zobaczysz tam zielony przycisk z napisem **"Compare & pull request"**. Kliknij go!
3. Opisz, co wprowadziłeś swoimi zmianami i dlaczego warto je akceptować. Następnie zatwierdź stworzenie Pull Requesta (PR).
4. Administracja lub inni twórcy przejrzą Twoje zmiany, mogą dodać swoje uwagi. Potem zostaną one połączone z głównym projektem!

## 3. Złote zasady naszego repozytorium
* **Bądźmy konstruktywni:** Oceniamy pomysły i kod, nie ludzi. Odnosimy się do siebie z szacunkiem i z dbałością o kulturę języka.
* **Intelekt ponad wszystko:** Zanim napiszesz komentarz lub kod, dobrze przemyśl jego cel. Wspólnie poszukujemy logiki i precyzji.
* **Nazewnictwo:** Nazywaj gałęzie i commity jasno, określając, co one robią (np. `dodanie-skryptu-analizy-rynku`).
* **Zademonstruj rozwiązanie:** Jeśli znajdziesz w kodzie problem, w miarę możliwości zaproponuj od razu rozwiązanie.

## 4. SZYBKI START (Fast Track) - Nie czekaj na akceptację!

Jeśli chcesz zacząć DZISIAJ:
1. Przejdź do **[Ankiety Kompetencyjnej (REKRUTACJA_ANKIETA.md)](REKRUTACJA_ANKIETA.md)**.
2. Wybierz jedną z **"Szybkich Ścieżek"** (sekcja na końcu ankiety).
3. Wykonaj zadanie (np. research, poprawka w markdown, mały skrypt).
4. Prześlij Pull Request zgodnie z instrukcją powyżej.

To najlepszy sposób, abyśmy Cię zauważyli i od razu włączyli do strategicznych prac.

## 5. Checklista Opiekuna Projektu

W miarę rozwoju inicjatywy, do struktury NARODOWYCH SIŁ INTELEKTUALNYCH będą wybierani **Opiekunowie** poszczególnych składowych lub całych wyodrębnionych projektów. Będą oni wyłaniani wyłącznie spośród najbardziej zaangażowanych twórców, a wybór na tę funkcję będzie najwyższym wyrazem uznania i nobilitacją. Jeśli marzy Ci się ta rola, potraktuj poniższą checklistę jako kompas codziennej pracy – bo u nas liczą się wyłącznie dokonania, kompetencje i idea, a bycie liderem to zaszczyt.

### Checklista kandydata na Opiekuna Projektu

- [ ] Wykazuję się **największą pracą i realnymi dokonaniami na rzecz repozytorium** – widocznymi w Issues, Pull Requestach, dokumentach, analizach i kodzie.
- [ ] Jestem wśród **najbardziej zaangażowanych twórców** – działam regularnie i konsekwentnie, zamiast czekać, aż ktoś inny zrobi to za mnie.
- [ ] Pracuję na rzecz **WSPÓLNEGO DOBRA** – mój wkład służy całości, a nie tylko mojej promocji.
- [ ] Trzymam się **Złotych zasad** (sekcja 3) i dbam o kulturę języka w każdej dyskusji.
- [ ] Pomagam nowym osobom postawić pierwsze kroki – od odpowiedzi w Issues po wsparcie przy pierwszym Pull Requeście.
- [ ] Pamiętam, że **Intelekt wyprzedza Kapitał** – najcenniejszy wkład to bezcenny, realny wysiłek intelektualny.

### Wzór dobrego Issue

Dobry Issue to nie zgłoszenie do urzędu, lecz zaproszenie do wspólnej pracy. Zanim klikniesz **"New Issue"**, ułóż myśl według prostego schematu (gotowe szablony zgłoszeń znajdziesz też w folderze `.github/ISSUE_TEMPLATE` naszego repozytorium):

```text
**Kontekst:** <twój-krótki-opis-sytuacji-i-dlaczego-to-ważne-dla-projektu>
**Proponowane rozwiązanie:** <twój-pomysł – pamiętaj o zasadzie "Zademonstruj rozwiązanie">
**Czego potrzebujesz:** <jakiej-pomocy-wiedzy-lub-decyzji-oczekujesz-od-współtwórców>
```

### Wzór dobrego Pull Requesta

Zanim wyślesz Pull Request, sprawdź go tak, jakby czytał go ktoś, kto dopiero dołączył do NARODOWEGO WYSIŁKU INTELEKTUALNEGO:

```text
**Opis:** <co-zmieniasz-i-dlaczego – czytelnik ma to zrozumieć bez zaglądania w pliki>
**Zakres:** mały i spójny – jedna zmiana, jeden cel; duże pomysły dziel na kolejne etapy
**Złote zasady:** <jasne-nazwy-gałęzi-i-commitów, konstruktywny opis, przemyślany cel zmiany>
```

### Nazewnictwo gałęzi dla treści niesoftware'owych

Zasada **Nazewnictwo** z sekcji 3 obowiązuje nie tylko programistów! Artykuły i dokumenty to pełnoprawne zmiany w repozytorium, więc tworzymy dla nich osobne, jasno nazwane gałęzie:

* kod (jak w przykładzie z sekcji 3): `dodanie-skryptu-analizy-rynku`
* artykuł: `artykul-automatyzacja-produkcji-zywnosci`
* artykuł: `artykul-recykling-elektrosmieci`
* dokument: `dokument-instrukcja-fork-i-pull-request`
* dokument: `dokument-checklista-opiekuna-projektu`

Nazywaj gałęzie tak, aby każdy współtwórca – bez zadawania pytań – wiedział, co w nich powstaje.

## 6. Przegląd zmian (review)

Przeglądanie cudzych Pull Requestów i Issues to nie urzędowa formalność, lecz kolejna forma wkładu w **WSPÓLNE DOBRO**. Przypomnij sobie kolejność z sekcji 1 i 2: najpierw Issues – *„serce naszego projektu"* – karmią burzę mózgów i analizę, w kolejnym etapie zmiana trafia do osobnej gałęzi i Pull Requesta, inni twórcy przeglądają ją i komentują, a na końcu dopracowana zmiana zostaje połączona z głównym projektem i zaczyna służyć wszystkim. Każdy merytoryczny komentarz w tym procesie to cenny wkład w **NARODOWY WYSIŁEK INTELEKTUALNY**. Kompas jest ten sam, co w całym repozytorium – **Złote zasady** (sekcja 3): *„Oceniamy pomysły i kod, nie ludzi"*, a w tym samym duchu pisze zintegrowany pilotaż automatyzacji produkcji żywności ([PROJEKTY/25_pilot_automatyzacji_zywnosci.md](PROJEKTY/25_pilot_automatyzacji_zywnosci.md)): *„Oceniamy pomysły i kod, nie ludzi — a liczy się wyłącznie dokonanie."* Jeżeli recenzujesz – działasz na rzecz WSPÓLNEGO DOBRA. Jeżeli Twoja zmiana jest recenzowana – możesz być spokojny: dyskutujemy tu o pomysłach i kodzie, nigdy o ludziach.

### Co sprawdzić przed zatwierdzeniem Pull Requesta lub Issue

Zanim zatwierdzisz cudzą zmianę, przejdź po kolei poniższe punkty – są odbiciem wzorów z sekcji 5:

* **Czytelność opisu:** autor opisał, co zmienia i dlaczego – tak, aby zrozumiał to czytelnik bez zaglądania w pliki (wzór dobrego Pull Requesta z sekcji 5).
* **Mały i spójny zakres:** jedna zmiana, jeden cel; jeśli zgłoszenie ciągnie za sobą kilka wielkich tematów naraz, życzliwie zaproponuj podzielenie ich na kolejne etapy – dokładnie tak, jak radzi wzór z sekcji 5.
* **Poprawność linków:** każdy link w opisie i treści prowadzi do pliku lub folderu, który REALNIE istnieje w repozytorium. Otwórz go przed zatwierdzeniem – martwy link łatwo przeoczyć, a naprawia się go jedną drobną poprawką opisu.
* **Zgodność z nazewnictwem gałęzi z sekcji 5:** w Pull Requeście sprawdź, czy nazwa gałęzi mówi jasno, co w niej powstaje – dla kodu, artykułów i dokumentów (np. `artykul-...`, `dokument-...`) – tak aby każdy współtwórca, bez zadawania pytań, wiedział, co w niej powstaje.

### Jak pisać recenzję życzliwie i konkretnie

* **Odnosimy się do zmiany, nie do osoby.** Zamiast oceniać autora, opisz, co dany fragment kodu lub dokumentu robi, czego brakuje albo co można uprościć. Oceniamy pomysły i kod – nie ludzi (sekcja 3).
* **Proponujemy zamiast rozkazywać.** Zamiast „zmień to" napisz „co powiesz na..." albo „rozważ, czy...". To wprost zasada **Zademonstruj rozwiązanie** z sekcji 3: jeśli wskazujesz problem, zaproponuj od razu rozwiązanie.
* **Przemyśl cel komentarza, zanim go napiszesz.** Wspólnie poszukujemy logiki i precyzji (sekcja 3) – komentarz, który nic nie wnosi do zmiany, przestaje być wkładem, a zaczyna być szumem.
* Dbaj o kulturę języka tak samo, jak w każdej innej dyskusji w repozytorium.

### Gdy zmiana czeka na decyzję Opiekuna

W miarę rozwoju inicjatywy decyzje o kierunku zmian należą do **Opiekunów** – wyłanianych wyłącznie spośród najbardziej zaangażowanych twórców (sekcja 5). Jeśli Twoja zmiana albo Twoja recenzja czeka na ich decyzję:

* Zachowaj cierpliwość – nie ponaglaj i nie podważaj decyzji w komentarzach; dyskusja służy merytoryce, a nie presji.
* Pomóż dyskretnie w dyskusji: odpowiadaj na pytania, dodawaj analizę i kontekst, wspieraj nowych współtwórców przy ich pierwszym Pull Requeście – dokładnie tak, jak zachęca checklista Opiekuna z sekcji 5.
* Pamiętaj, że cierpliwa, merytoryczna pomoc też jest dokonaniem. U nas liczą się wyłącznie dokonania, a **Intelekt wyprzedza Kapitał** – najcenniejszy wkład to bezcenny, realny wysiłek intelektualny.

### Gotowe szablony zgłoszeń

Nie musisz zaczynać od pustej strony. Folder `.github/ISSUE_TEMPLATE` naszego repozytorium (ten sam, który wskazuje sekcja 5) zawiera gotowe szablony zgłoszeń:

* [Nowy Strażnik](.github/ISSUE_TEMPLATE/nowy_straznik.md)
* [Pomysł / propozycja rozwiązania](.github/ISSUE_TEMPLATE/pomysl_rozwiazanie.md)
* [Zastrzeżenie / uwaga / ryzyko](.github/ISSUE_TEMPLATE/zastrzezenie_uwaga.md)
* [Provider danych / węzeł pomiarowy](.github/ISSUE_TEMPLATE/provider_danych.md)
* [Utrata dostępu providera](.github/ISSUE_TEMPLATE/utrata_dostepu_providera.md)
* [Volunteer Problem Report](.github/ISSUE_TEMPLATE/volunteer_problem_report.md)

Pull Requesty natomiast opisuj według wzoru **„Wzór dobrego Pull Requesta"** z sekcji 5: najpierw krótki opis, potem mały i spójny zakres, a na końcu odwołanie do Złotych zasad.

---

Cieszymy się, że chcesz z nami wspólnie pracować nad systemem budującym WSPÓLNE DOBRO NARODOWE!

---

## 7. Od pomysłu do pilotażu (wzorzec 25–29)

Pilotaże [25. Zintegrowany Pilotaż Automatyzacji Produkcji Żywności](PROJEKTY/25_pilot_automatyzacji_zywnosci.md), [26. Koncepcyjny Pilotaż AI w Medycynie](PROJEKTY/26_pilot_ai_w_medycynie.md), [27. Koncepcyjny Pilotaż Sieci Energetycznej](PROJEKTY/27_pilot_sieci_energetycznej.md), [28. Koncepcyjny Pilotaż Logistyki Sąsiedzkiej](PROJEKTY/28_pilot_logistyki_sasiadzkiej.md) i [29. Koncepcyjny Pilotaż Planowania Przestrzennego i Rozwoju](PROJEKTY/29_pilot_planowania_przestrzennego.md) zaczynają się od tych samych słów: *„Pilotaż nie zaczyna od zera"*. Wszystkie powstają w oparciu o jeden, powtarzalny szkielet — **wspólny wzorzec warstw: warstwa sensoryczno-sterująca / decyzyjna AI na krawędzi / pętla nauki z telemetrią** — a każdy z nich jest, jak sami piszą, *„produktem burzy mózgów, analizy i planowania — precyzyjną koncepcją, która powstaje intelektem, nie budżetem"*. Poniżej znajdziesz tę samą ścieżkę przetłumaczoną na język współtworzenia z sekcji 1–6: od Twojego pierwszego zgłoszenia w Issues, przez napisanie koncepcji pilotażu, po Pull Request, przegląd i integrację z głównym projektem.

### Krok 1: Zgłoś pomysł w Issues (szablony z `.github/ISSUE_TEMPLATE`)

Zacznij dokładnie tak, jak każe sekcja 1: Issues to *„serce naszego projektu"*. Zanim klikniesz **"New Issue"**, wybierz gotowy szablon z folderu `.github/ISSUE_TEMPLATE` (pełną listę szablonów z linkami znajdziesz w sekcji 6) i ułóż zgłoszenie według **Wzoru dobrego Issue** z sekcji 5: **Kontekst**, **Proponowane rozwiązanie**, **Czego potrzebujesz**. Pamiętaj o zasadzie **Zademonstruj rozwiązanie** z sekcji 3 — a pytania i zastrzeżenia innych współtwórców traktuj jako darmową analizę, nie przeszkodę. Wspólna burza mózgów w dyskusji to dokładnie ten etap, dzięki któremu pilotaże 25–29 mogły powstać intelektem, nie budżetem.

### Krok 2: Napisz koncepcję pilotażu według wspólnego wzorca warstw

Gdy dyskusja dojrzeje, w późniejszym etapie zapisz koncepcję jako dokument projektu w folderze `PROJEKTY/` — i prowadź czytelnika przez te same trzy warstwy, które spajają pilotaże 25–29:

* **Warstwa sensoryczno-sterująca:** co węzeł mierzy i czym steruje. W pilotażach warstwa ta opiera się na fundamentach zebranych w repozytorium — Home Assistant jako lokalny mózg automatyzacji, ESPHome do firmware'u czujników i elementów wykonawczych, MQTT jako lekki protokół komunikacji urządzeń IoT — a sprzęt bierze z odzysku: stare smartfony pełnią rolę węzłów sterujących, bramek danych i kamer inspekcyjnych. W zależności od dziedziny ta warstwa zmienia nazwę: w [25](PROJEKTY/25_pilot_automatyzacji_zywnosci.md) to „warstwa sensoryczna i sterowanie", w [26](PROJEKTY/26_pilot_ai_w_medycynie.md) i [28](PROJEKTY/28_pilot_logistyki_sasiadzkiej.md) „sensoryczno-komunikacyjna", w [29](PROJEKTY/29_pilot_planowania_przestrzennego.md) „danych wejściowych" — dobierz więc sensorystkę do swojej dziedziny, zachowując wspólny szkielet.
* **Warstwa decyzyjna AI na krawędzi:** analiza wykonywana lokalnie, blisko czujników i danych, bez uzależnienia od zewnętrznych chmur, a wynik w ujednoliconej postaci rekomendacji (poziom ryzyka, rekomendacja, poziom pewności, kody przyczyn). Pamiętaj o zasadzie, którą pilotaże 26–29 zapisują wprost: **rekomendacja jest zawsze wejściem do decyzji człowieka, nigdy jej zamiennikiem** — decyzja końcowa zawsze pozostaje po stronie człowieka, a według [29](PROJEKTY/29_pilot_planowania_przestrzennego.md) obowiązuje wzorzec **„Rekomendacje, nie Nakazy"**.
* **Pętla nauki z telemetrią:** najpierw węzeł zbiera obserwacje i zdarzenia, następnie warstwa decyzyjna porównuje je z dotychczasową wiedzą, w kolejnym etapie koryguje sterowanie lub rekomendacje, a na końcu zapisuje wniosek do wspólnej bazy wiedzy. Trzymaj się konwencji „edge-first" z pilotaży: surowe odczyty pozostają poza repozytorium, a do repo wraca wyłącznie wiedza opracowana — snapshoty, raporty zbiorcze, udokumentowane przypadki i otwarte, wspólne profile w formatach JSON/YAML.

Dwie rady prosto z pilotaży 25–29. Po pierwsze: **nie zaczynaj od zera** — każdy z tych dokumentów najpierw wylicza zalążki już istniejące w repozytorium, na których buduje; zrób to samo i powołuj się wyłącznie na realne pliki (sekcja 6 przypomina: każdy link ma prowadzić do pliku, który REALNIE istnieje). Po drugie: **pełnoprawny wkład jest możliwy także bez własnego sprzętu** — projektowanie schematów, analiza organizacji pracy i dokumentacja to praca intelektualna tej samej rangi.

### Krok 3: Wyślij Pull Request

Dojrzałą koncepcję — dokładnie tak, jak opisują to pilotaże: *„dojrzałe zmiany — rozszerzenia koncepcji, dokumentacja, profile wiedzy, adaptery — trafiają do plików poprzez Pull Requesty"* — wnieś modelem **Fork & Pull Request** z sekcji 2. Nadaj gałęzi nazwę według sekcji 5 (dla dokumentu koncepcji naturalna będzie forma `dokument-...`), a opis Pull Requesta ułóż według **Wzoru dobrego Pull Requesta** z sekcji 5: najpierw **Opis** (czytelnik ma zrozumieć bez zaglądania w pliki), potem mały i spójny **Zakres** — jedna zmiana, jeden cel, a duże pomysły podzielone na kolejne etapy — na końcu odwołanie do **Złotych zasad**.

### Krok 4: Przegląd zmian (review)

Twój Pull Request przejdzie przez proces opisany w **sekcji 6 „Przegląd zmian (review)"**: recenzenci sprawdzą czytelność opisu, mały i spójny zakres, poprawność linków oraz zgodność nazwy gałęzi z nazewnictwem z sekcji 5. Recenzje u nas oceniają pomysły i kod, nie ludzi — więc i Ty przyjmuj uwagi w tym samym duchu: **Zademonstruj rozwiązanie**, popraw, podziękuj. Jeśli zmiana czeka na decyzję **Opiekuna**, zachowaj cierpliwość — dyskusja służy merytoryce, a nie presji (sekcja 6).

### Krok 5: Integracja z głównym projektem przez Opiekuna

Po pozytywnym przeglądzie dopracowana zmiana zostaje — jak opisują sekcje 2 i 6 — połączona z głównym projektem. Decyzje o kierunku zmian należą do **Opiekunów**, wyłanianych wyłącznie spośród najbardziej zaangażowanych twórców (sekcja 5); to Opiekun w późniejszym etapie integruje przyjęty dokument pilotażu z całością repozytorium, w tym z [README](README.md), z którego pilotaże 25–29 czerpią definicje swoich osi rozwoju. Od tej chwili Twoja koncepcja staje się wzorcem do powielenia w fazie skalowania — a dzięki pętli nauki z telemetrią każdy kolejny węzeł rozpoczyna pracę z dorobkiem poprzedników. To jest ta sama droga, którą pilotaże 25–29 prowadzą do fazy finansowania **Dochodu Gwarantowanego**: nadwyżki wypracowane przez system wracają do **WSPÓLNEGO DOBRA NARODOWEGO**. Twój pomysł, doprowadzony od zgłoszenia w Issues do zintegrowanego pilotażu, jest cząstką tego **NARODOWEGO WYSIŁKU INTELEKTUALNEGO**.

---

### Wzorzec w praktyce: pilotaże 30 i 31

Wzorzec opisany w tym rozdziale nie jest tylko instrukcją — dwa najnowsze pilotaże pokazują go w praktyce, a każdy z nich przesuwa jego granice w inną stronę. [Koncepcyjny Pilotaż Finansowania Inicjatywy](PROJEKTY/31_pilot_finansowania_inicjatywy.md) jest pilotażem czysto procesowym i udowadnia, że wspólny szkielet działa również poza sprzętem: zamiast czujników źródłem danych są inne projekty repozytorium. Jego **warstwa danych wejściowych** spisuje potrzeby projektów i realny stan ich prac, **warstwa decyzyjna AI** dopasowuje kryteria zaczerpnięte z dokumentów inicjatywy i uszeregowuje projekty, a wynik analizy trafia do **weryfikacji przez ludzi** — decyzja zawsze należy do człowieka i społeczności. Cykl zamyka **pętla nauki z wyników decyzji**: podjęte rozstrzygnięcia i ich uzasadnienia wracają do wspólnej bazy wiedzy i w kolejnym obiegu korygują kryteria. Wzorzec rekomendacji z sekcji 7 obowiązuje tu bez zmian — rekomendacja jest wejściem do decyzji człowieka, nigdy jej zamiennikiem; zmienia się wyłącznie to, co analiza czyta: nie odczyty z czujników, lecz spisane potrzeby i dokonania projektów.

[Koncepcyjny Pilotaż Gospodarki Zasobami Strategicznymi](PROJEKTY/30_pilot_gospodarki_zasobami.md) dowodzi tego samego na gruncie zasobowym — w służbie wody, surowców i ziemi. Jego **warstwa sensoryczno-rejestracyjna** łączy pomiar zużycia z rejestracją zasobów materialnych, **warstwa decyzyjna AI wspierająca alokację zasobów** analizuje te dane lokalnie, na krawędzi, i proponuje racjonalne kierunki gospodarowania, a **pętla nauki z telemetrii** zestawia przyjęte rekomendacje z realnym zużyciem i zapisuje wnioski do wspólnej bazy wiedzy — dzięki czemu każdy kolejny węzeł rozpoczyna pracę z dorobkiem poprzedników. A ponieważ pilotaż nie jest wyspą, sekcja „Zależności od pozostałych osi i pilotaży" prowadzi spięcie w cztery strony: Żywność, Energia, Logistykę i Planowanie przestrzenne — dorobek tej osi wzmacnia sąsiednie, a te zasilają ją własnymi danymi i telemetrią.

Wniosek dla współtwórcy jest wzorcotwórczy. Ta sama droga z kroków 1–5 — od zgłoszenia w Issues, przez koncepcję spisaną według wspólnego wzorca warstw, Pull Request i przegląd, po decyzję Opiekuna i integrację z całością — służy zarówno pilotażom sprzętowym, jak i procesowym; zmienia się jedynie tłumaczenie warstw na język dziedziny, gdy sensorystyka staje się procesem albo rejestracją zasobów, a telemetria — udokumentowanymi efektami. Jeśli nie masz własnego sprzętu, nic nie stoi na przeszkodzie: projektowanie procesu, analiza i dokumentacja to wkład intelektualny pełnej rangi, a liczy się wyłącznie dokonanie. Właśnie tak działa zasada **Intelekt wyprzedza Kapitał** — pilotaże, sprzętowe i procesowe, powstają intelektem, nie budżetem — a każdy z nich, poprowadzony tą samą drogą aż do fazy finansowania **Dochodu Gwarantowanego**, jest cząstką **NARODOWEGO WYSIŁKU INTELEKTUALNEGO** pracującego na rzecz **WSPÓLNEGO DOBRA NARODOWEGO**.

---

### Wzorzec w praktyce: pilotaże poprzeczne 32 i 33

Ta sama droga dowodzi swojej siły także wtedy, gdy wzorzec nie dopisuje nowej dziedziny, lecz łączy te, które już istnieją — najpierw przy spięciu osi, a w kolejnym etapie przy utrzymaniu w ruchu tego, co spięcie uruchomiło. [Koncepcyjny Pilotaż Węzła Zintegrowanego](PROJEKTY/32_pilot_wezla_zintegrowanego.md) jest koncepcją pierwszego pilotażu poprzecznego — spięciem, które łączy w jednym, wspólnym węźle wzorce pilotaży 25, 27 i 30: **węzeł produkcji żywności**, **zasilany energią** oraz **zarządzany zasobami**. Warstwy nie są tu nowe — to te same warstwy, które tamte pilotaże wypracowały osobno na swoich osiach; nowością jest ich wspólne życie w jednym węźle. Dokument zaczyna dokładnie tak, jak każe wzorzec: *„Pilotaż nie zaczyna od zera"* — wylicza zalążki już istniejące w repozytorium, a jako motywację podaje zaproszenie z sekcji **„Synergie osi"** [Mapy drogowej](ROADMAPA.md), na które pilotaże gospodarki zasobami i finansowania odpowiedziały jako pierwsze; jest więc kolejną odpowiedzią na to samo zaproszenie. Kolejność pozostaje względna: najpierw pilotaże osiowe potwierdzają swoje wzorce, w kolejnym etapie węzeł zintegrowany spina je w jednej realizacji, a przed skalowaniem następuje powielanie węzłów i dołączanie kolejnych spięć osi. Zasada decyzji człowieka obowiązuje bez zmian — **rekomendacja jest zawsze wejściem do decyzji człowieka, nigdy jej zamiennikiem**, a decyzja końcowa pozostaje po stronie człowieka-gospodarza węzła oraz społeczności. Cykl zamyka **pętla nauki ze wspólną telemetrią**: węzeł zbiera obserwacje ze wszystkich swoich warstw, porównuje je z dotychczasową wiedzą i koryguje sterowanie oraz rekomendacje, a wypracowany wniosek wraca do wspólnej bazy wiedzy — do repozytorium trafia wyłącznie wiedza opracowana, dzięki czemu każdy kolejny węzeł rozpoczyna pracę z dorobkiem poprzedników.

[Koncepcyjny Pilotaż Warsztatu Serwisowego Węzłów](PROJEKTY/33_pilot_warsztat_serwisowy.md) dowodzi tego samego przy utrzymaniu w ruchu — i wyrasta wprost z poprzedniego pilotażu: jego motywacją jest sekcja „Zależności od pozostałych osi i pilotaży" pilotażu zintegrowanego, a zwłaszcza jej podsekcja o elektronice i sterownikach z odzysku. Ten pilotaż nie buduje kolejnego węzła, lecz odpowiada za dalsze życie węzłów, których elektronika powstaje z odzysku: to wspólny wzorzec zaplecza utrzymaniowego, domykający cykl życia węzłów — od budowy z odzysku, przez pracę i usterkę, po naprawę częścią z odzysku — z pytaniem **kto utrzyma rosnący park węzłów w ruchu**. Spięcie projektów 06, 12, 17 i 13 również zaczyna od zalążków: sterowniki z odzysku, reuse elektroniki, pętla odzysku z jawnym etapem testowania i kwalifikacji oraz wersjonowana baza części-dawców są wyliczone wprost jako punkty startu istniejące w repozytorium. Kolejność jest znowu względna: najpierw węzły pracują według swoich wzorców i budują telemetrię, w późniejszym etapie rosnący park potrzebuje zaplecza serwisowego, a przed skalowaniem warsztat musi mieć gotowe wzorce diagnostyki, kwalifikacji odzysku i wspólnej bazy części. Zasada decyzji człowieka przenosi się na stół serwisowy: **rekomendacja serwisowa AI jest zawsze wejściem do decyzji człowieka-serwisanta, nigdy jej zamiennikiem** — diagnoza i naprawa pozostają odpowiedzialnością ludzi, których AI wspiera wiedzą zgromadzoną we wspólnej bazie. Cykl zamyka **pętla nauki warsztatu**: usterki, wyniki diagnoz i wykonane naprawy prowadzą do korekty procedur serwisowych, a udokumentowane przypadki napraw wracają do wspólnej bazy wiedzy, dzięki czemu każdy kolejny warsztat i każdy kolejny węzeł rozpoczyna pracę z dorobkiem poprzedników.

Wniosek dla współtwórcy pozostaje wzorcotwórczy także po stronie poprzecznej. Ta sama droga z kroków 1–5 — od zgłoszenia w Issues, przez koncepcję spisaną według wspólnego wzorca warstw, Pull Request i przegląd, po decyzję Opiekuna i integrację z całością — służy zarówno łączeniu osi w jednym węźle, jak i utrzymaniu ich dorobku w ruchu; zmienia się jedynie tłumaczenie warstw na język dziedziny, gdy warstwy wypracowane osobno na poszczególnych osiach zaczynają pracować razem, a następnie razem z nimi pracuje zaplecze serwisowe. Pełnoprawny wkład jest możliwy także bez własnego sprzętu: projektowanie schematów, analiza przypadków i dokumentacja to praca intelektualna tej samej rangi — tak oba pilotaże poprzeczne piszą o współtworzeniu, przypominając, że oceniamy pomysły i kod, nie ludzi, a liczy się wyłącznie dokonanie. A ponieważ — jak stanowi sekcja **„Synergie osi"** [Mapy drogowej](ROADMAPA.md) — **Intelekt wyprzedza Kapitał**, a najmocniej działa wtedy, gdy łączy to, co już wspólnie zaprojektowaliśmy, każdy pilotaż poprzeczny poprowadzony tą samą drogą jest cząstką **NARODOWEGO WYSIŁKU INTELEKTUALNEGO** pracującego na rzecz **WSPÓLNEGO DOBRA NARODOWEGO**.
