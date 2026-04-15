# 14. Autonomiczne Projektowanie 3D i CAD (MCP)

## Wizja: Fabryka w formie czatu

Projekt 14 to kolejny krok w procesie budowy **Autonomicznych Systemów R+D**. Naszym celem jest usunięcie bariery wejścia w zaawansowaną inżynierię mechaniczną poprzez wykorzystanie agentów AI do bezpośredniej manipulacji oprogramowaniem CAD.

Zamiast ręcznie rysować bryły w programach projektowych, Strażnik Przyszłości opisuje potrzebny element, a AI – korzystając z protokołu MCP (Model Context Protocol) – projektuje go, waliduje i przygotowuje do produkcji.

## Łańcuch narzędziowy (Toolchain)

System opiera się na synergii trzech potężnych technologii:

1.  **Claude 4.6 Sonnet (Orkiestrator):** Pełni rolę głównego inżyniera. Analizuje prompt użytkownika, decyduje o strategii modelowania i pisze skrypty w Pythonie dla FreeCAD. Dzięki swoim zdolnościom do rozumowania (reasoning), potrafi iteracyjnie poprawiać błędy geometrii i ograniczeń API.
2.  **Gemma 3 lub inny model (Edge/Local R+D):** Wykorzystywana jako lokalna instancja AI (na brzegu sieci) do szybkich obliczeń pomocniczych, walidacji parametrów wytrzymałościowych oraz generowania powtarzalnych skryptów modelowania w scenariuszach, gdzie wymagana jest suwerenność danych i niska latencja.
3.  **FreeCAD (Silnik Open-Source):** Wybrany jako fundament ze względu na potężne API Pythona i brak uzależnienia od licencji chmurowych wielkich korporacji (jak Autodesk czy SolidWorks).

## Proces Autonomicznego Projektowania

1.  **Prompt:** "Zaprojektuj wspornik pod silnik NEMA17 o grubości 5mm, z otworem centrującym i czterema otworami montażowymi 3.5mm."
2.  **Kodowanie:** AI generuje skrypt `model.py` wykorzystujący moduł PartDesign we FreeCAD.
3.  **Iteracja MCP:** Jeśli API FreeCAD zwróci błąd (np. błąd wiązań szkicu), Claude/Gemma czytają logi, analizują przyczynę i modyfikują skrypt aż do wygenerowania poprawnej bryły.
4.  **Eksport:** Automatyczne generowanie pliku `.STEP` oraz `G-code` na drukarkę 3D lub frezarkę CNC.

## Cel Strategiczny: Ucieczka przed Monopolem

Większość profesjonalnych narzędzi CAD przechodzi na model subskrypcyjny i chmurowy, co w dobie pełnej automatyzacji czyni produkcję zależną od kapitału i decyzji zagranicznych korporacji. **Projekt 14 przywraca suwerenność technologiczną**, budując "intelektualną fabrykę" opartą na darmowych, otwartych narzędziach zintegrowanych z najnowocześniejszymi modelami AI.

---
**Zobacz inspirację wideo:** [Claude 3.7 projektuje w FreeCAD przez MCP](https://www.youtube.com/watch?v=HQDMvA-gN1c)
