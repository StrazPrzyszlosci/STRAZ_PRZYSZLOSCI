# Jak interpretuję docelową automatyzację repozytorium Straży Przyszłości

## Krótka interpretacja

Nie interpretuję tego repo jako zwykłej aplikacji ani jako jednego bota. Interpretuję je jako **system operacyjny organizacji**, który ma zamieniać rozproszone sygnały, odpady, wiedzę i pracę ludzi w bezpieczne, audytowalne łańcuchy tworzenia realnej wartości społecznej: żywności, odzyskanych części, narzędzi, sensorów, sterowników i lokalnych usług.

Najważniejsze nie jest samo „AI”, tylko **łańcuch odpowiedzialności**:

```text
obserwacja -> hipoteza -> mały skrypt -> artefakt -> test -> review -> zatwierdzenie -> wdrożenie -> telemetryczny feedback -> poprawa procesu
```

AI ma przyspieszać rozpoznawanie okazji, pisanie skryptów, analizę danych, przygotowanie projektów i prowadzenie operatorów. Nie ma samodzielnie decydować o działaniach fizycznych, które mogą zaszkodzić ludziom, zwierzętom, żywności, wodzie, instalacjom lub środowisku.

## Co jest „pełnym celem” repo

Pełny cel widzę jako połączenie pięciu fabryk:

1. **Fabryka wiedzy** — zbiera dokumentację, zewnętrzne repozytoria, handoffy, wyniki testów, katalogi części i decyzje review.
2. **Fabryka skryptów automatyzacji** — produkuje małe, czytelne i testowalne automaty: importery, weryfikatory, kuratory, flasher wizardy, raportery, scouty.
3. **Fabryka odzysku sprzętu** — zamienia elektrośmieci i stare smartfony w sensory, bramki, panele operatora, sterowniki lub węzły agentowe.
4. **Fabryka biologiczno-żywnościowa** — wspiera hydroponikę, akwaponikę i hodowlę grzybów przez obserwację, rekomendacje i kontrolę jakości, ale z bramkami bezpieczeństwa.
5. **Fabryka samodoskonalenia** — mierzy skuteczność procesów i proponuje poprawki promptów, procedur, testów i workflowów.

Te fabryki muszą być spięte jedną logiką audytu, a nie luźną kolekcją pomysłów.

## Docelowe warstwy automatyzacji

| Warstwa | Rola | Przykłady artefaktów | Domyślne ograniczenie |
| --- | --- | --- | --- |
| Sygnały | Wykrywa zasoby, potrzeby i anomalie | zgłoszenia, zdjęcia, pomiary, linki, oferty „oddam” | provenance wymagane |
| Scouting | Ocenia potencjał i koszt aktywacji | `PotentialDossier`, ranking, karta repo | read-only/suggest-only |
| Execution pack | Rozbija pracę na mały kontrakt | prompt, skrypt, input/output, testy | review wymagane |
| Verifier | Sprawdza jakość i spójność | raport walidacji, lista defektów | nie promuje danych sam |
| Curator | Przygotowuje sugestie do katalogu/projektu | staging, diff, decision packet | human approval |
| Safety reviewer | Szuka ryzyk fizycznych i społecznych | hazard list, rollback, blocked actions | blokuje deployment |
| Deployment pack | Opisuje powtarzalne wdrożenie | profile, firmware, runbook, bench report | tylko po approval |
| Telemetry | Mierzy skutki i awarie | metryki, heartbeat, incident log | brak ukrytych działań |
| Optimizer | Proponuje ulepszenia procesu | benchmark, wariant promptu, patch | sandbox + review |

## Jak ma wyglądać łańcuch dla śmieci

1. Scout znajduje elektrośmieć, odpad, część lub darmowy zasób.
2. System ocenia: lokalizacja, koszt odbioru, ryzyko, potencjalne części, popyt społeczny.
3. Operator demontuje lub fotografuje elementy według checklisty.
4. AI/OCR proponuje części i możliwe zastosowania.
5. Verifier odrzuca halucynacje i niepewne MPN.
6. Curator przygotowuje wpisy do katalogu części i projekty reuse.
7. Human reviewer zatwierdza wpis lub zleca dodatkowe zdjęcia/testy.
8. Zatwierdzona część trafia do projektu: sensor, sterownik, obudowa, bramka, panel, stanowisko testowe.
9. System zapisuje, co realnie zadziałało, i poprawia następne instrukcje.

## Jak ma wyglądać łańcuch dla żywności

1. Smartfon, kamera lub sensor zbiera obserwacje systemu akwaponicznego/hydroponicznego/grzybowego.
2. Agent tworzy raport: trendy, ryzyka, brakujące pomiary, możliwe przyczyny.
3. Rekomendacja jest `suggest-only`, jeżeli dotyczy karmienia, chemii, wody, pomp, grzałek lub dobrostanu zwierząt.
4. Operator zatwierdza działanie albo prosi o więcej danych.
5. Po działaniu system zapisuje rezultat i uczy się, które rekomendacje były trafne.

## Jak ma wyglądać ścieżka smartfonów-edge

Stary smartfon powinien być traktowany jak tani komputer z kamerą, baterią, Wi-Fi/Bluetooth, ekranem i czujnikami. Docelowy wizard powinien działać podobnie do flasherów MeshCore/Meshtastic:

```text
podłącz / uruchom Termux -> wykryj możliwości -> wybierz profil -> zainstaluj zależności -> uruchom test -> zapisz receipt -> zarejestruj node -> pokaż rollback
```

Pierwsze profile powinny działać bez ryzyka fizycznego: obserwacja, katalogowanie, raportowanie, panel operatora, bridge do API. Sterowanie pompami, przekaźnikami lub dozowaniem musi być osobnym etapem z review.

## Co oznacza „samooptymalizacja”

Samooptymalizacja nie oznacza, że agent sam siebie bez kontroli przepina do produkcji. Oznacza:

- mierzenie jakości workflowów,
- wykrywanie powtarzalnych błędów,
- proponowanie lepszych promptów, testów i skryptów,
- porównywanie wariantów na benchmarkach,
- tworzenie PR-ów z uzasadnieniem,
- zachowanie pełnego śladu decyzji.

Promocja do kanonicznego procesu wymaga review człowieka i zielonych testów.

## Zasada graniczna

Jeżeli automatyzacja dotyka świata fizycznego, żywności, wody, zwierząt, ludzi, instalacji elektrycznych, radiowych albo mechaniki, domyślny tryb to:

```text
observe -> explain -> suggest -> wait for human approval
```

Dopiero po osobnym wdrożeniu, testach i rollbacku można rozważać częściową autonomię w wąskim, niskiego ryzyka zakresie.

## Najkrótszy wzorzec wykonawczy: potencjał -> zamysł -> projekt -> wykonanie -> optymalizacja

Dla mnie najważniejszy mechanizm repo to pętla wykorzystywania potencjału:

1. **Potencjał** — wykryj darmowy lub tani zasób, np. elektrośmieci, smartfony, zasilacze, kamery, routery, przewody, lokalną przestrzeń, dane lub wiedzę.
2. **Zamysł** — zamień zasób w intencję produktu: np. smartfon jako obserwator akwaponiki, kamera USB jako kontrola wzrostu grzybni, zasilacz jako element stanowiska testowego.
3. **Projekt** — wygeneruj BOM, schemat, profil urządzenia, runbook montażu, bench-test i rollback.
4. **Wykonanie** — uruchom tylko mały execution pack z audytem i review gate.
5. **Optymalizacja** — zmierz koszt, czas, błędy, realny efekt i popraw następny run.

Nowy katalog `potential_pipeline/` zapisuje tę pętlę jako dane i deterministyczny generator planu, zaczynając od dossier `ewaste_to_food_edge_devices`.
