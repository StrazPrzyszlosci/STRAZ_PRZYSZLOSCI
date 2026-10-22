# LiteWeed — wzorzec referencyjny produktu roju

Źródło: Moeinnia H. i in., *LiteWeed: An affordable edge-AI robotic platform
for laser weed management in resource-constrained environments*, **Smart
Agricultural Technology 14 (2026) 102340**, doi:10.1016/j.atech.2026.102340
(Simon Fraser University, Additive Manufacturing Lab + Aga Khan University,
Arusha). PDF operatora: `main.pdf` (poza repo, 12 MB).

## Dlaczego to wzorzec dla roju

Teza artykułu = teza roju: *„skuteczne zwalczanie chwastów laserem osiąga
się przez inteligentną adaptację software'u, a nie eskalację drogiego
sprzętu"* — dosłownie „Intelekt wyprzedza Kapitał". LiteWeed pokazuje pełną
drabinę, którą rój ma zautomatyzować: baza części → projektowanie z dostępnych
komponentów → produkcja (druk/montaż) → pilot w polu → produkt poszerzający
zdolności (robot wykonuje usługę odchwaszczania bez chemii).

## Specyfikacja referencyjna

| Element | LiteWeed (paper) | Odpowiednik roju (z zasobów roju) |
|---|---|---|
| Compute + vision | Raspberry Pi 5 + Sony IMX708 + STM32 Nucleo (~100 CAD) | odzyskany smartfon (PROJEKTY/06) — apka Android zbudowana przez LLM, model obrazowy on-device |
| Detekcja | YOLOX-nano edge: mAP@0.5:0.95 = 0.32, latencja 118 ms na RPi5 | trenowanie/destylacja na darmowych API; inferencja lokalnie (on_device_model) |
| Podwozie | goBilda Recon, 4× DC motory z enkoderami | mechanika z odzysku (`mechanics_scrap`) — katalog w bazie części |
| Rama | custom 3D-print PLA, modułowa | drukarka 3D udostępniona przez człowieka (`3d_printer`) |
| Ramię celownika | 2-DoF arm, laser+kamera na wspólnej belce (decoupling od wibracji) | montaż na bench (`robot_arm` / manual) |
| Laser | dioda 12 V, 450 nm, 4 W optycznie; fokus 5–10 cm; ekspozycja ≤60 s dozowana per gatunek/rozmiar | **wariant roju: bez lasera — aktuation odchwaszczania zostaje bramkowana**; wariant mechaniczny/termiczny wyłącznie po review człowieka |
| Power | 12 V 30 Ah LiFePO4 + 30A BMS | odzyskane ogniwa z battery_swelling_check (charter: e_waste_ethics) |
| Dane | 10 820 augmentowanych obrazów treningowych | zbiór z pól/pilotów agri edge; augmentacja na darmowych API |
| Koszt | ≈ 500 CAD | cel roju: dążyć do ~0 PLN poprzez odzysk + udostępnione zdolności produkcyjne |
| Walidacja | cross-kontynentalna: Vancouver (CA) + Arusha (TZ), kukurydza | pilot agri roju (PASS/FAIL bandy z telemetrii) |
| Paradygmat | task-level semi-autonomia (realia małych gospodarstw) | autonomia polowa roju w granicach charter.json |
| Future work (paper) | pełna autonomia: GNSS + LiDAR + VIO, multi-sensor fusion | roadmapa roju po pierwszym produkcie |

## Mapowanie na łańcuch roju

1. **Zwiad/baza**: rekordy resource_scout (smartfony, mechanika, ogniwa,
   drukarki 3D, ramiona) + Łowca Części (YouTube→baza części) — klasy już
   w `selfopt_chain/capability_map.json` (`old_smartphones`,
   `mechanics_scrap`, `3d_printer`, `robot_arm`).
2. **Projektowanie**: dossier potencjału → BOM z bazy części → design pack
   (CAD/okreslenia jak rama PLA) — łańcuchy LLM na darmowych API.
3. **Produkcja**: basal przydziela zadania do udostępnionych zdolności
   (drukarka 3D → ramy/mocowania; ramię robota → montaż; bench → elektronika)
   z `charter.json` rule `safe_physical_boundaries` (e-stop, strefa robocza).
4. **Wdrożenie**: węzeł vision na starym smartfonie (`device_profile` /
   `on_device_model` — decyzja basal), platforma z odzysku; pilot w polu
   z telemetrią przez LoRa (deadmesh).
5. **Poszerzenie możliwości**: robot wykonuje usługę (odchwaszczanie =
   żywność + środowisko), a jego platforma staje się zasobem roju do
   kolejnych produktów — pętla rozbudowy.

## Zasady bezpieczeństwa (charter)

Wzorzec LiteWeed zawiera laser 4 W — **wersja roju startuje bez aktuation
ścinania**: najpierw wykrywanie + mapowanie chwastów (raport dla operatora),
a dopiero physical weeding (każda forma) po review człowieka zgodnie z
`charter.json` (rules: no_weapons analog — promień lasera to urządzenie
uszkadzające; `physical_actuation` pozostaje gated). Zmiany konstytucji
wyłącznie przez PR człowieka.
