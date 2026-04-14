# [PROJEKT 12] Autonomiczne Projektowanie PCB z Recyklingu i Inwentaryzacja e-Śmieci

Ten dokument opisuje strategię i narzędzia budujące system suwerennej produkcji elektroniki w oparciu o recykling elektrośmieci oraz Sztuczną Inteligencję.

## I. Filar 1: ecoEDA – Inteligentny Recykling Komponentów
Narzędzie **ecoEDA** to wtyczka do programu KiCad, która analizuje lokalny inwentarz odzyskanych części i sugeruje ich użycie zamiast kupowania nowych komponentów.

- **Bill of Teardowns (BoT):** System generuje instrukcję, jakie konkretnie urządzenia (np. stary router, dekoder) należy rozmontować, aby uzyskać części do nowego projektu.
- **Różne typy dopasowań:** Sugeruje zamienniki o zbliżonych parametrach lub obudowach.

## II. Filar 2: KiCAD-MCP-Server – Autonomia Projektowa z AI
**KiCAD-MCP-Server** pozwala modelom językowym (np. Claude) na bezpośrednią ingerencję w pliki projektowe KiCada za pomocą protokołu MCP.

- AI potrafi projektować schematy, układać elementy i wykonywać routing na podstawie opisu w języku naturalnym.
- Pozwala to na realizację wizji „Intelekt wyprzedza Kapitał” – algorytm zastępuje kosztowny proces inżynieryjny.

## III. Filar 3: Ki-nTree + InvenTree – Silnik Inwentaryzacji e-Śmieci
System **InvenTree** (baza inwentarzowa) połączony z narzędziem **Ki-nTree** zapewnia AI „widzialność” zasobów.

- **Automatyczne Katalogowanie:** Ki-nTree zaciąga noty katalogowe (PDF), parametry i symbole części w kilka sekund.
- **Integracja AI:** Moduł OCR rozpoznaje chip na starej płycie i tworzy rekord w bazie przez API. Skatalogowany „wylut” jest od razu dostępny jako symbol dla AI projektującego nową PCB.

---

## Treści i Założenia

Automatyzacja inwentaryzacji elektrośmieci przez AI wymaga solidnej bazy danych. Zamiast pisać ją od zera, wykorzystujemy kod open-source. Ki-nTree świetnie łączy części z magazynem InvenTree i KiCadem, co stanowi silnik dla naszej Sztucznej Inteligencji. 

Docelowo rozwijamy moduł AI, który po zeskanowaniu starej płyty ze śmieci sam rozpozna części i je skataloguje. AI potrzebuje bazy danych, z którą się komunikuje – InvenTree zapewnia stabilny backend. Kod na dodawanie części do wirtualnego magazynu i programu projektowego już istnieje. Ki-nTree robi to w kilka sekund. Następnym krokiem jest integracja modułów rozpoznawania obrazu / OCR układów, które automatycznie przekażą symbole wylutowanych części do skryptu, a ten zaciągnie PDF-y z notami katalogowymi i posegreguje zasoby.

Prezentacja ecoEDA – narzędzia open-source integrującego się z programem KiCad, które w czasie rzeczywistym podpowiada, jak użyć komponentów (lub całych obwodów) ze starych urządzeń – zepsutych telefonów, odkurzaczy czy zabawek. Zamiast standardowej listy materiałowej (BOM), system generuje instrukcję pozyskania części z konkretnych elektrośmieci.

---

## Zasoby i Repozytoria

*   **ecoEDA (Recykling):** [humancomputerintegration/ecoEDA](https://github.com/humancomputerintegration/ecoEDA/tree/main)
*   **KiCAD-MCP-Server (Automatyzacja AI):** [mixelpixx/KiCAD-MCP-Server](https://github.com/mixelpixx/KiCAD-MCP-Server)
*   **Ki-nTree (Inwentaryzacja):** [sparkmicro/Ki-nTree](https://github.com/sparkmicro/Ki-nTree)
*   **InvenTree (Baza):** [InvenTree Documentation](https://docs.inventree.org/)

**Materiały Wideo:**
*   [ecoEDA - Recykling w KiCad](https://www.youtube.com/watch?v=XYMRXMVBfNg)
*   [KiCAD AI - Projektowanie z MCP](https://www.youtube.com/watch?v=C9n7eC16u-Y)
*   [Ki-nTree - Budowa Bazy Części](https://www.youtube.com/watch?v=YeWBqOCb4pw)

---
*Intelekt wyprzedza kapitał!*
