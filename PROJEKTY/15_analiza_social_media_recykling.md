# [PROJEKT 15] Automatyczna Analiza AI Polskich Sieci Społecznościowych i Portali Aukcyjnych dla Recyklingu

## Cel Projektu
Głównym celem projektu jest stworzenie inteligentnego systemu monitorującego polskie grupy społecznościowe (np. grupy "Oddam za darmo", "Śmieciarka jedzie") oraz portale aukcyjne (OLX, Allegro Lokalnie) w celu identyfikacji ofert darmowych lub bardzo tanich urządzeń elektronicznych oraz zgłoszeń indywidualnego zapotrzebowania na konkretne części.

## Projekt 15 jako warstwa resource scoutingu o wysokiej dzwigni

Ten projekt nie powinien byc traktowany jako poboczny dodatek do recyklingu. To jedna z warstw o najwyzszym potencjale, bo pozwala AI wykrywac i laczyc okazje zanim jeszcze trzeba budowac kosztowny hardware albo odpalac ciezsze wdrozenia.

Najwieksza wartosc nie zawsze lezy w pojedynczym ogloszeniu. Często powstaje dopiero wtedy, gdy system polaczy:

- ogloszenie `oddam za darmo`,
- ogloszenie `sprzedam tanio`,
- post `potrzebuje czesci` albo `szukam urzadzenia`,
- lokalizacje i czas odbioru,
- wiedze o potencjale odzysku, naprawy albo dalszego reuse.

To oznacza, ze analiza social media i ogloszen powinna byc traktowana jako pelnoprawny element warstwy `analizy potencjalu`, a nie tylko jako zrodlo leadow do katalogu.

## Kluczowe Funkcjonalności
1.  **Skanowanie Ofert:** Automatyczne pobieranie i analiza postów oraz ogłoszeń pod kątem słów kluczowych związanych z elektroniką i elektrośmieciami.
2.  **Matching Potrzeb:** System będzie łączyć osoby posiadające zbędny sprzęt z osobami, które zgłosiły zapotrzebowanie na konkretne podzespoły (np. matryca do laptopa, zasilacz).
3.  **Redukcja Marnotrawstwa:** Poprzez efektywne łączenie dawców i biorców, projekt realnie zmniejsza ilość elektrośmieci trafiających na wysypiska.
4.  **Integracja z Botem Telegram:**
    *   Użytkownicy bota `@straz_przyszlosci_bot` będą mogli zgłaszać swoje zapotrzebowanie na części.
    *   Bot będzie automatycznie rekomendował transakcje/odbiory między użytkownikami na podstawie zebranych danych.
5.  **Ocena Potencjału Relacyjnego:**
    *   System nie ocenia tylko pojedynczych ogloszen, ale rowniez potencjal wynikajacy z ich polaczenia.
    *   Najwyzszy priorytet powinny dostawac okazje, gdzie wystepuje jednoczesnie darmowa lub bardzo tania podaz, realny popyt, bliska logistyka i znana sciezka wykorzystania zasobu.
6.  **Wzbogacanie Bazy Wiedzy:**
    *   Automatyczne pobieranie danych katalogowych i specyfikacji technicznych części ze schematów dostępnych online.
    *   **Multimodalna Analiza Wideo:** System będzie analizował filmy z napraw sprzętu na YouTube. Wykorzystując model AI od Google (np. Gemini), system będzie generował stopklatki z rzutem na części elektroniczne i automatycznie rozpoznawał komponenty, wzbogacając bazę zamienników i rzadkich części.

## Architektura Danych
Baza danych części tworzona przez bota będzie centralnym punktem odniesienia, łączącym fizyczne przedmioty z ich cyfrowym śladem (schematy, stopklatki z napraw, parametry techniczne), ale docelowo powinna rowniez laczyc:

- sygnaly darmowej lub taniej podazy,
- sygnaly zapotrzebowania,
- potencjal odzysku i reuse,
- lokalizacje i koszty przejecia,
- rekomendacje co warto aktywowac najpierw.
