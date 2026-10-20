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

---

Cieszymy się, że chcesz z nami wspólnie pracować nad systemem budującym WSPÓLNE DOBRO NARODOWE!
