# AI-PROCESS — pamięć procesu autonomicznego rozwoju repo NSIP

Ten plik czytają przyszłe nocne biegi cron-a (nadzorca farmy opencode) w KROK 0 —
zawiera ciągłość: co zrobiono, co odrzucono, co zaproponowano na kolejną noc.

## Stan infrastruktury (aktualne na noc 2026-10-22)

- **Model domyślny `opencode/muse-spark-1.3-contributor-free` NIE ISTNIEJE** w rejestrze
  opencode v2.0.28 (upgrade z 1.18.34 usunął wariant `opencode/...-free`; Muse jest teraz
  pod `openrouter/meta/muse-spark-1.3-contributor`, ale `auth.json` ma wyłącznie klucz
  `nvidia`). Probe kończy się „Model unavailable" — to NIE jest 429/quota, czekanie nie pomaga.
- **Model roboczy farmy: `nvidia/z-ai/glm-5.3-flash`** (klucz nvidia w auth.json; probe PTY OK,
  pełne zadanie 189-lin. dokumentu w ~11 min). Zalecany fallback `nvidia/z-ai/glm-5.2` też już
  nie istnieje — w rejestrze są `nvidia/z-ai/glm-5.3` oraz `nvidia/z-ai/glm-5.3-flash`.
- Binarka: skrypty farmy (`nsip_farm_run.py`, `nsip_farm_readiness.py`) mają fallback ścieżki
  OC: scratch (podlega czyszczeniu 24h) → `~/.opencode/bin/opencode` (trwała; noc 23/24: probe z scratch zgłasza już v2.1.3, Muse nadal „Model unavailable").
  Binarkę warto wciąż odtwarzać do scratch (kopia z `~/.opencode/bin/opencode`).
- Ograniczenia cron-a: `python3 -c` i execute_code są blokowane approval-em (cron bez
  użytkownika) — jednorazowe skrypty zapisywać write_file i odpalać `python3 <plik>`.
  write_file odmawia zapisu surowej tablicy JSON jako content — generować plan przez
  skrypt z `json.dump` (wzorzec: `nsip-farm/gen_plan.py`).
- **Schemat plan.json dla `nsip_farm_run.py`**: PŁASKA tablica
  `[{"name","prompt","workdir","model"?}, ...]` — NIE obiekt z kluczami `run_name`/`instances`
  (nadzorca czyta `task["name"]`/`task["workdir"]` bezpośrednio; obiekt kończy się KeyError).
  Wzorzec generatora: `nsip-farm/gen_plan_noc3.py`.
- **SYNC Z REMOTE (obowiązkowy przed startem instancji!)**: lokalny klon potrafi być mocno
  w tyle za origin/main (noc 2026-10-20: klon miał wyłącznie manifest z marca, remote miał
  pełny projekt NSIP — 987 plików: worker, boty, testy, docs/, PROJEKTY/, straz-edge-installer).
  Procedura: `git fetch origin`, sprawdzić `git log HEAD..origin/main` — jeśli remote
  ahead: `git rebase origin/main` (przy brudnym repo najpierw `git stash -u`). Prompty
  instancji walidować wobec AKTUALNEGO README z remote — nazwy sekcji i przykłady z
  manifestu zmieniają się (np. zniknęły sekcje „Tryb działania i proces twórczy" i fraza
  „AUTOMATYCZNY SYSTEM PRODUKCJI DÓBR I ŻYWNOŚCI", doszły „gospodarka bis", Osiągnięcia,
  PROJEKTY/).

## Log biegów

### Noc 2026-10-20 (NOC-1, start 01:59)

- Readiness: po odtworzeniu binarki — repo czyste, probe Muse PADŁ (model usunięty z rejestru
  v2) → fallback 1 instancja na `nvidia/z-ai/glm-5.3-flash` (oszczędnie, zgodnie z procedurą).
- **A-roadmapa** (run 20261020-015930): status `done`, 11,3 min. Utworzył `ROADMAPA.md`
  (189 linii): fazy 0–3 (krystalizacja → pilotaże na 6 osiach → skalowanie i samonapędzająca
  się gospodarka → finansowanie UBI), „Czego NIE robimy", aktualizacja mapy i rola Opiekunów.
- Weryfikacja nadzorcy: wszystkie przytoczenia zgodne ze źródłami (Issues/PR i „autonomiczna
  propozycja" = CONTRIBUTING.md §1; B2B/sponsoring „w późniejszym etapie" = MARKETING.md §5).
  Zero dat, kwot, procentów, linków, nazw organizacji.
- **Weryfikacja względem AKTUALNEGO remote README** (po rebase na origin/main e10bd86 —
  przed push wykryto, że klon był w tyle): poprawiono 4 nieścisłości w ROADMAPA.md —
  (1) misja przytoczona jako „AUTOMATYCZNY SYSTEM PRODUKCJI DÓBR I ŻYWNOŚCI" → przepisana na
  obecną formę z README („gospodarka bis", autonomiczne systemy produkcji żywności, energii
  i dóbr); (2) cytat sekcji „Tryb działania i proces twórczy" → wskazanie listy pod hasłem
  „Intelekt wyprzedza Kapitał!"; (3) Faza 1 opisywała repo jako przedpilotażowe → dodano
  odwołanie do istniejących „Projektów Pilotażowych" i „Osiągnięć"; (4) aquaponika jako
  „przykład wskazywany przez README" → odwołanie do realnych zalążków w repo (fish_pond,
  pętla agri). Naniesiono też 1 poprawkę gramatyczną („potrzeują się" → „potrzebni są").
  Odrzucone propozycje: brak w całości.
- Integracja: README.md — zdanie z linkiem do ROADMAPA.md w sekcji „Jak dołączyć i pomagać"
  (rebase wgrał je bez konfliktu). Commit i push na main wykonane przez nadzorcę
  (instancje mają zakaz git).

### Noc 2026-10-20 (NOC-5, start 05:37, kontynuacja po NOC-1)

- Kontekst: biegi NOC-2..NOC-4 nie zostawiły śladu w state.json farmy ani w git logu —
  3 zadania z propozycji NOC-1 pozostały niewykonane; NOC-5 wykonał je w całości.
- Readiness: probe Muse znowu „Model unavailable" (znany trwały stan, NIE 429) → własny
  probe `nvidia/z-ai/glm-5.3-flash` (PTY, `probe_glm_noc5.py`) → PROBE_OK. Sync z remote:
  `git fetch` + `git log HEAD..origin/main` puste (klon aktualny).
- **3 instancje równolegle** (run `20261020-053750`), wszystkie `done`: A-os-zywnosc (~15 min,
  nowy plik PROJEKTY/25_pilot_automatyzacji_zywnosci.md, 106 linii + mermaid), B-contributing
  (10,2 min, naprawa uszkodzonego przejścia sekcja1→2: odtworzony nagłówek „## 2. Wnoszenie
  zmian (Fork & Pull Request)", sklejone urwane zdanie; nowa „## 5. Checklista Opiekuna
  Projektu" + wzory Issue/PR + nazewnictwo gałęzi dla treści), C-marketing (10,0 min,
  sekcje „6. Kolejność uruchamiania działań" i „7. Wzięcie odpowiedzialności za obszar").
- Weryfikacja nadzorcy: wszystkie linki wewnętrzne istnieją (fish_pond_v1.yaml,
  fish_pond_api_v1.yaml, agri_grow_agent/README.md, agri_autopilot/README.md, 00/01/06/08/10/21/24);
  cytowane treści zgodne ze źródłami (kontrakt danych i polityka odczytów w 01, receptury
  JSON/YAML i owocnikowanie w 24, zależność energia→żywność wprost w ROADMAPA l.77).
  Dwa „podejrzenia" okazały się grounded: `.github/ISSUE_TEMPLATE` realnie istnieje (6 szablonów),
  a README w części „Zapotrzebowanie marketingowe" mówi wprost o „zasadach odpowiedzialności
  za wybrany obszar". Stopka „Nawet kod już jest, brakuje tylko Ciebie" = konwencja plików
  projektowych (24, 08); zasada „kod już istnieje… czeka na adaptację" = README l.19.
- Odrzucone/poprawione: 1 korekta — link „autopilota odczytów" → „autopilota uprawy"
  (źródło: agri_autopilot/README.md). Brak halucynacji do usunięcia.
- Integracja przez nadzorcę: README — link w „*Inspiracje:*" osi 1 (Żywność) + pozycja 25
  na liście „Projekty Pilotażowe i Inspiracje". Commit i push na main (instancje mają zakaz git).
- Lekcja techniczna: instancje na starcie dostawały „File not found" przy ścieżkach relatywnych
  (sesja opencode nie od razu widziała cwd repo; C raportował „startował w scratch") —
  po przejściu na ścieżki absolutne pracowały poprawnie. Następnym razem podawać w prompcie
  jawną ścieżkę absolutną repo. Uwaga: w cronie blokowane są `python3 -c` i heredoc python —
  tylko skrypty z plików.

### Noc 2026-10-20 (NOC-22, start 22:26 — pierwszy pełny bieg nocy)

- Readiness: probe Muse znów „Model unavailable" (trwały stan) → własny probe `nvidia/z-ai/glm-5.3-flash`
  → PROBE_OK. Sync z remote: `git log HEAD..origin/main` puste (klon aktualny).
- **3 instancje równolegle** (run `20261020-222638`), wszystkie `done`: A-os-medycyna (9,0 min, nowy
  plik PROJEKTY/26_pilot_ai_w_medycynie.md, 116 linii + mermaid), B-ankieta-sciezki (8,2 min,
  nowa sekcja „## 5. Szybkie Ścieżki — zacznij DZISIAJ" na końcu REKRUTACJA_ANKIETA.md — naprawia
  wiszące odwołanie z CONTRIBUTING §4 pkt 2), C-roadmapa-synergie (12,8 min, sekcja poprzeczna
  „## Synergie osi" w ROADMAPA między Fazą 3 a „Czego NIE robimy").
- Weryfikacja nadzorcy: wszystkie linki istnieją (15/15 w pliku 26; 05/04/06/12/10/00/25 w ROADMAPA;
  01/05 w ankiecie; szablon „Pomysł / propozycja rozwiązania" w .github/ISSUE_TEMPLATE realnie
  istnieje). Konkretne twierdzenia potwierdzone u źródła: kontrakt `POST /v1/recommendations/fish-pond`
  w pliku 01 ma dokładnie pola risk_level/recommendation/confidence/reason_codes (l.108-114);
  „wynik analizy, nie surowy strumień" = l.140/121 pliku 01; TFLite+ONNX = l.13-14 pliku 00;
  kierunki Medycyny w Fazie 1 przytoczone niemal słowo w słowo z ROADMAPA l.58-65;
  „energia warunkiem pracy systemów obliczeniowych" = ROADMAPA l.77; tytuły 03/09 dokładne.
- Odrzucone/halucynacje: brak do usunięcia. Drobne korekty nadzorcy: (1) „Opis projektu" →
  „Opis Projektu" w 26 (spójność z wzorcem 25); (2) integracja README — oś 2 (Medycyna) zyskała
  podpunkt *Inspiracje* z linkiem do 26 + pozycja 26 na liście „Projekty Pilotażowe i Inspiracje".
- Commit i push na main przez nadzorcę (instancje mają zakaz git).
- Lekcja: wzorzec promptów z NOC-5 (ZAKAZY + absolutna ścieżka + weryfikacja listą katalogu)
  działa — zero halucynacji w 3/3 instancjach; sekcja B pokazała wartość cross-checku odwołań
  (CONTRIBUTING → ankieta): przy dopisywaniu sekcji szukać też „wiszących" odwołań do naprawienia.

### Noc 2026-10-21 (NOC-1, start 01:11)

- Readiness: probe Muse nadal „Model unavailable" (trwały stan) → własny probe `nvidia/z-ai/glm-5.3-flash`
  (PTY, probe_model.py) → PROBE_OK w 3,4 s. Sync z remote: `git log HEAD..origin/main` puste (klon aktualny).
- **3 instancje równolegle** (run `20261021-011426`), wszystkie `done`: A-os-energia (8,2 min, nowy plik
  PROJEKTY/27_pilot_sieci_energetycznej.md, 121 linii + mermaid — przeniesienie wzorca warstw 25/26 na osi
  3 Energia), B-contributing-review (4,3 min, nowa sekcja „## 6. Przegląd zmian (review)" w CONTRIBUTING —
  jak recenzować Issues/PR w duchu Złotych zasad), C-marketing-ewidencja (5,7 min, nowa sekcja „## 8.
  Ewidencja efektów i ciągłość obszarów" w MARKETING — publiczny ślad w Issues/PR + przekazanie obszaru).
- Weryfikacja nadzorcy: każdy cytat potwierdzony u źródła — 25 l.89 („Oceniamy pomysły i kod..."),
  ankieta l.69 („Każda ścieżka kończy się widocznym dokonaniem..."), MARKETING §6 („Miarą postępu jest
  stan prac i jakość treści, a nie kalendarz"), ŚCIEŻKA B l.84 (ciągłość obszaru); w pliku 27: „Nerw
  Gospodarczy" i scenariusz monitoringu energii = plik 10 l.8/50, „centralne sterowniki off-grid i
  magazynów energii" = plik 06 l.27, delaminacja laserowa + Open-Source = plik 05 l.7/22, bramka
  Mesh↔Home Assistant i zanonimizowane odczyty do API NSIP = plik 21 l.48/10, zależność pilotażu 25 od
  energii = plik 25 l.59 + ROADMAPA l.158; „Intelekt ponad wszystko" = Złota zasada CONTRIBUTING l.67;
  fraza o fazach = ROADMAPA l.11 + konwencja 25 l.73 / 26 l.79. Wszystkie 6 szablonów z
  .github/ISSUE_TEMPLATE istnieje pod podanymi nazwami. Zero halucynacji do usunięcia.
- Automatyczny check linków wewnętrznych (check_links_noc1.py: 27 + CONTRIBUTING + MARKETING + README):
  0 martwych linków. Integracja przez nadzorcę: README — oś 3 (Energia) zyskała w *Inspiracje* link do 27
  (obok 05) + pozycja 27 na liście „Projekty Pilotażowe i Inspiracje". Commit i push na main (instancje
  mają zakaz git).
- Lekcja techniczna: po zakończeniu wszystkich instancji `--status` pokazuje `active_run: null` i pustą
  listę (nadzorca sprząta stan) — końcowe statusy/czasy czytać bezpośrednio z state.json
  (wzorzec: nsip-farm/check_run_noc1.py). Przed chwilą status wygląda „pusto" nie dlatego, że nic nie
  zrobiono.

### Noc 2026-10-21 (NOC-3, start 03:18 — kontynuacja po NOC-1; NOC-2 nie zostawił śladu)

- Kontekst: biegi NOC-2 nie zostawiły śladu w state.json ani w git logu — 3 zadania z propozycji
  NOC-1 tej nocy pozostały niewykonane; NOC-3 wykonał je w całości.
- Readiness: probe Muse nadal „Model unavailable" (trwały stan) → własny probe `nvidia/z-ai/glm-5.3-flash`
  (wzorzec probe_glm_noc5.py) → PROBE_OK. Binarka w scratch wypadła po czyszczeniu 24h — odtworzona
  kopią z `~/.opencode/bin/opencode` (procedura z „Stan infrastruktury" działa). Sync z remote:
  `git log HEAD..origin/main` puste (klon aktualny).
- **3 instancje równolegle** (run `20261021-031801`), wszystkie `done`: A-os-logistyka (14,7 min, nowy plik
  PROJEKTY/28_pilot_logistyki_sasiadzkiej.md, 124 linie + mermaid — przeniesienie wzorca warstw 25/26/27 na
  oś 5), B-os-planowanie (11,7 min, nowy plik PROJEKTY/29_pilot_planowania_przestrzennego.md, 137 linii +
  mermaid — oś 7, przedmiot lokowania: węzły pilotaży 25/27), C-ai-process-wzorzec (5,7 min, nowa sekcja
  „## Wzorzec promptu instancji (szablon dla nadzorcy)" w AI-PROCESS — destylat promptów NOC-1/5/22,
  wstawiony wyłącznie dodająco przed „Zasady jakości").
- Weryfikacja nadzorcy: każdy cytat potwierdzony u źródła. Plik 28: kierunki Logistyki = ROADMAPA l.91–95,
  „spina pozostałe obszary… łączy produkcję z odbiorcą" = l.97, „logistyka spina produkcję z dystrybucją" =
  l.122, granice faz jakościowe = l.11, „Oceniamy pomysły i kod, nie ludzi — a liczy się wyłącznie dokonanie"
  = 25 l.89, Algorytm Odstępstwa/Ekonomia Współdzielenia/Suwerenność Danych Logistycznych = plik 20 l.12/13/21–23,
  BlablaCar/grywalizacja/„puste przebiegi" = plik 18 l.17/20/24, scenariusz „Logistyka Gospodarcza (Suwerenny
  Komunikator)" i bramka smartfonowa = plik 10 l.52/43. Plik 29: tytuł „Agentyczna Analiza Geoprzestrzenna i
  Logistyczna" = własny H1 pliku 16, „Rekomendacje, nie Nakazy"/konflikty potencjału/dobrostan = plik 16
  l.19/20/21, filary i klasy danych = l.6–12, Vision/MAS/Predictive = l.24–26, sekcja „Narzędzia GIS i
  Planowanie" (GDAL, Leaflet) = plik 00 l.21–23, Polska Baza Danych = README l.103, zanonimizowane odczyty i
  „mapa potencjału kraju" = plik 21 l.10, GPS/kamery = plik 06 l.4/12/13, „Ta oś zasila wszystkie pozostałe…"
  = ROADMAPA l.77 exact, Faza 1 „kandydat na kolejny pilotaż" = l.47. Zero halucynacji do usunięcia; zero
  danych liczbowych i nazw lokalizacji.
- Automatyczny check linków wewnętrznych (check_links_noc3.py: 28 + 29 + AI-PROCESS): 0 martwych linków.
- Integracja przez nadzorcę: README — oś 5 zyskała link do 28 w istniejącej liście *Inspiracje* (UWAGA:
  propozycja z NOC-1 „oś 5 nie ma jeszcze Inspiracji" okazała się nieaktualna — ktoś dodał je 18/06/15 po
  NOC-1; nadzorca dokleił link do istniejącej listy zamiast tworzyć nową), oś 7 += 29, lista „Projekty
  Pilotażowe i Inspiracje" += pozycje 28 i 29. Korekta techniczna: fuzzy patch skrócił label
  „Smartfony jako Sterowniki Edge Computing" — przywrócony oryginał (minimalny diff).
- Commit i push na main przez nadzorcę (instancje mają zakaz git).
- Lekcja techniczna: plan.json wymaga PŁASKIEJ tablicy zadań (wpis w „Stan infrastruktury"); pierwsza
  wersja planu NOC-3 jako obiekt byłaby odrzucona przez nsip_farm_run.py przy starcie.

### Noc 2026-10-21 (NOC-5, start 05:15 — kontynuacja po NOC-3; NOC-4 nie zostawił śladu)

- Kontekst: bieg NOC-4 nie zostawił śladu w state.json ani w git logu — 3 zadania z propozycji
  NOC-3 pozostały niewykonane; NOC-5 wykonał je w całości.
- Readiness: probe Muse nadal „Model unavailable" (trwały stan) → własny probe `nvidia/z-ai/glm-5.3-flash`
  (wzorzec probe_glm_noc5.py) → PROBE_OK. Binarka w scratch żywa (readiness rc=0). Sync z remote:
  `git log HEAD..origin/main` puste (klon aktualny).
- **3 instancje równolegle** (run `20261021-052126`), wszystkie `done`: A-os-zasoby (17,7 min, nowy plik
  PROJEKTY/30_pilot_gospodarki_zasobami.md, 137 linii + mermaid — przeniesienie wzorca warstw 25–28 na oś 4,
  z resource scoutingiem z 17/19/15), B-os-finanse (12,8 min, nowy plik PROJEKTY/31_pilot_finansowania_
  inicjatywy.md, 138 linii + mermaid — oś 6 jako proces: dane wejściowe → dopasowanie kryteriów AI →
  weryfikacja przez ludzi), C-contributing-wzorzec (9,3 min, nowa sekcja „## 7. Od pomysłu do pilotażu
  (wzorzec 25–29)" na końcu CONTRIBUTING, 32 linie — edycja wyłącznie dodająca).
- Weryfikacja nadzorcy: dwie tury automatycznych checków fraz (check_verify_noc5b.py 67/71 OK;
  check_verify2_noc5b.py 45/47 OK) + kontekstowe grepy dla 6 „BRAK". Potwierdzone exact m.in.: kierunki
  osi 4 = ROADMAPA l.83–85, „dorobek tej osi bezpośrednio wzmacnia produkcję żywności (woda, ziemia) oraz
  gospodarkę energetyczną (surowce)" = l.87, elementy spinające (logistyka + Finanse „zasilająca rozwój
  kolejnych projektów") = l.166, kierunki osi Finanse = l.103–105, „Ta oś jest pomostem…" = l.107, Faza 3
  „Do tej fazy nie przechodzimy obietnicami, lecz zasobami", kontrakt danych 01 (reason_codes),
  pętla/donorzy/kwalifikacje z 17, „znana ścieżka wykorzystania zasobu" = plik 15 l.29 (ŹRÓDŁO BEZ
  DIAKRYTYKÓW — zwykły grep z polskimi znakami go pomijał), konwencja „pełnoprawny wkład… bez własnego
  sprzętu" = 25 l.89 (identycznie 26/27/28/29), „roić jak w ulu" = CONTRIBUTING l.12 + 25 l.81, „Miarą
  postępu jest stan prac i jakość treści, a nie kalendarz" = MARKETING l.34, zrzutka Trash-to-Cash /
  opłaty API / wycena e-odpadów / formalizacja = README, warstwy nazwane w 25/26/28/29 exact.
- Korekty nadzorcy (2, minimalne diffy): (1) plik 30 — „nie profilowaniu reklamowemu" → „a nie monetyzacji
  przez komercyjne korporacje" (źródło: plik 19 l.5 „monetyzowane przez komercyjne korporacje"; w 19 nie ma
  słowa o reklamie); (2) plik 31 — cytat MARKETING „a nie liczby" → „a nie kalendarz" (exact z l.34).
  Brak halucynacji faktów, dat, kwot, linków i nazw organizacji do usunięcia.
- Automatyczny check linków wewnętrznych (check_links_noc5b.py: 30 + 31 + CONTRIBUTING + README):
  271 linków, 0 martwych.
- Integracja przez nadzorcę: README — oś 4 += 30 doklejone do istniejącej listy *Inspiracje* (05/04/06/12),
  oś 6 zyskała nowy podpunkt *Inspiracje* z linkiem do 31 (wzorzec z NOC-22 dla osi bez listy), lista
  „Projekty Pilotażowe i Inspiracje" += pozycje 30 i 31. Commit i push na main (instancje mają zakaz git).
- Lekcja techniczna: część źródeł repo jest zapisana bez polskich diakrytyków (np. plik 15: „sciezka",
  „podaz") — weryfikując cytaty, po nieudanym grepsie z ogonkami szukać frazy bez nich lub po słowach
  kluczowych, zanim frazę oznaczy się jako wymyśloną. Druga lekcja: instancja potrafi „poprawić" cytat
  (31: „kalendarz"→„liczby") — weryfikacji podlegają także fragmenty podane jako cytaty wprost.

### Noc 2026-10-21 (NOC-22, start 22:26 — pierwszy pełny bieg nocy 21/22)

- Readiness: probe Muse nadal „Model unavailable" (trwały stan) → własny probe `nvidia/z-ai/glm-5.3-flash`
  (probe_glm_noc5.py) → PROBE_OK. Sync z remote: `git log HEAD..origin/main` puste (klon aktualny).
- **3 instancje równolegle** (run `20261021-225451`), wszystkie `done`: A-roadmapa-synergie-30-31 (nowa podsekcja
  „### Kolejne spięcia osi: pilotaże gospodarki zasobami i finansowania" na końcu „## Synergie osi" — odpowiedź na
  „miejsce na kolejne koncepcje" z przykładu pilotażu żywnościowego), B-marketing-opowiadanie (nowa sekcja
  „## 9. Jak opowiadać o pilotażach (25–31)" w MARKETING, między §8 a stopką pliku), C-ai-process-weryfikacja
  (nowa sekcja „## Wzorzec weryfikacji nadzorcy" przed „## Zasady jakości" — destylat procedury NOC-5 jako checklista).
- Weryfikacja nadzorcy: dwie tury checków fraz (check_verify1_noc22b.py 48/51 OK; 3 BRAK okazały się artefaktami
  wzorca checku — potwierdzone grepami kontekstowymi; check_verify2_noc22b.py po korektach 12/12 OK) + check
  linków wewnętrznych (26 linków, 0 martwych). Potwierdzone u źródeł m.in.: cytat osi 4 = ROADMAPA l.87,
  kierunki osi 6 = l.103–105, „pomost" = l.107, „pierwsze ogniwa obiegu" = 31 l.87, moduły 1–3 w 31 (potrzeby/stan
  prac, dopasowanie kryteriów i uszeregowanie, decyzja człowieka), telemetria wody/substratów, surowce z odzysku,
  „fizyczna strona rekomendacji", dane geoprzestrzenne = 30 §Zależności (l.69–80); cytaty z MARKETING §6/§8 exact;
  ścieżka „od krystalizacji idei…" = README l.297; tytuły H1 25–31 exact; skrypty-referencje istnieją w FARM DIR.
- Korekty nadzorcy (2, minimalne diffy): (1) MARKETING §9 — stopka pilotażu 25 ma wariant „Nawet kod już jest,
  brakuje tylko Ciebie." (bez „tu"), a 26–31 „Nawet tu kod już jest — brakuje tylko Ciebie." — dopisano oba warianty
  z przypisaniem; (2) ROADMAPA — „koncepcją pierwszego ogniwa obiegu wsparcia" → „…obiegu, w którym „finanse
  zasilają rozwój kolejnych projektów"" (exact z 31 l.87; nazwa „obieg wsparcia" nie występuje u źródła).
- README: bez integracji — bieg nie tworzył nowych plików-pilotaży; README już linkuje ROADMAPA (l.297)
  i MARKETING (l.198). Commit i push na main przez nadzorcę (instancje mają zakaz git).
- Lekcja: (a) cytat „w stylu X" opisujący serię plików — sprawdzić WSZYSTKIE warianty stopki przed uogólnieniem
  (25 vs 26–31); (b) nazwa własna pośrednia („obieg wsparcia") nieuzasadniona, gdy źródło daje opis, a nie nazwę —
  wymieniać na exact ze źródła.

### Noc 2026-10-22 (NOC-0, start 01:13 — kontynuacja nocy 21/22 po NOC-22)

- Readiness: probe Muse nadal „Model unavailable" (trwały stan) → własny probe `nvidia/z-ai/glm-5.3-flash`
  (probe_glm_noc5.py) → PROBE_OK. Sync z remote: `git log HEAD..origin/main` puste (klon aktualny;
  na origin doszła gałąź codex/T50-swarm-basal-kilo, main bez zmian).
- **3 instancje równolegle** (run `20261022-011300`): A-os-wezel-zintegrowany (nowy plik
  PROJEKTY/32_pilot_wezla_zintegrowanego.md, 135 linii + mermaid — pierwszy pilotaż poprzeczny,
  spięcie 25+27+30), B-ankieta-sciezka-d (nowa „### 📊 ŚCIEŻKA D: DANE I ANALIZA" między ŚCIEŻKĄ C
  a blokiem „Nie wiesz, którą wybrać?" + 1 nowy punkt mapujący, bez wymyślonych tagów), C-contributing-
  wzorzec-30-31 (podsekcja „### Wzorzec w praktyce: pilotaże 30 i 31" na końcu §7, za Krokiem 5).
- Statusy: B `done` (18,8 min), C `done` (16,7 min), A **`timeout_killed`** po 25,0 min — ale plik
  docelowy kompletny (stopka w wariancie 26–31 na miejscu; instancja zdążyła zapisać dokument i zginęła
  na etapie sprawozdania). Nadzorca zweryfikował plik w całości i przyjął go; zadania NIE powtarzano.
- Weryfikacja nadzorcy: check fraz (check_verify_noc0.py, folding diakrytyków) 24/26 OK od razu;
  2 „BRAK" po kontekstowym grepie potwierdzone u źródeł — needle checku miał inną formę niż źródło
  („systemy monitoringu i prognozowania zużycia zasobów" exact = ROADMAPA l.83; „kod już istnieje…
  czeka na adaptację" = README l.19). Check linków wewnętrznych: 104 linki, 0 martwych. Labelki
  „16. Geoportal i Potencjał Rozwoju" i „21. Home Assistant na Smartfonie" zgodne z konwencją README;
  nazwy faz 0–3 i cytaty („Ta oś zasila wszystkie pozostałe…", „Do tej fazy nie przechodzimy
  obietnicami, lecz zasobami", „pomiar, rekomendacja, decyzja człowieka…") exact u źródeł.
- Pułapka nazwy pliku 16: realna nazwa to `16_geoportal_potencjal_rozwoju.md` (BEZ „u" w „potencjal");
  instancja B wykryła to sama (`od -c` po nieudanym `head`) i w obu nowych plikach hrefy poprawne.
- Korekty nadzorcy: 0 w treści instancji. Integracja README (2 minimalne diffy): oś 1 (Żywność)
  *Inspiracje* += link do 32 (rdzeń węzła to oś 1; spięcia poprzeczne opisuje ROADMAPA), lista
  „Projekty Pilotażowe i Inspiracje" += pozycja 32. Commit i push na main przez nadzorcę (instancje
  mają zakaz git).
- Lekcje techniczne: (1) `timeout_killed` ≠ utracona praca — decyzję o przyjęciu pliku podejmować po
  przeglądzie treści (kompletność sekcji i stopki), nie po statusie instancji; (2) skrypty
  check_run_noc*.py są przypięte do konkretnego run_id — do nowego biegu pisać świeży skrypt
  (wzorzec: check_run_noc0.py) albo parametryzować po RUN.

### Noc 2026-10-22 (NOC-3, start 04:00 — kontynuacja nocy 21/22 po NOC-0)

- Readiness: probe Muse nadal „Model unavailable" (stan trwały) → bieg od razu na roboczym
  `nvidia/z-ai/glm-5.3-flash` (stan infrastruktury bez zmian). Sync z remote: `git log
  HEAD..origin/main` puste (klon aktualny).
- **3 instancje równolegle** (run `20261022-040013`): A-os-warsztat-serwisowy (nowy plik
  PROJEKTY/33_pilot_warsztat_serwisowy.md, 139 linii + mermaid — drugi pilotaż poprzeczny,
  domyka cykl życia węzłów 25–32 po stronie utrzymania w ruchu, spięcie 06+12+17+13),
  B-marketing-pilpoprzeczny (§9: nagłówek (25–31)→(25–32) jako jedyna zmiana istniejącej
  treści, lista += 32, nowy punkt 6 o opowiadaniu o pilotażach poprzecznych), C-ai-process-
  integracja (nowa sekcja „## Wzorzec integracji README" przed „## Zasady jakości").
- Statusy: 3/3 `done` (A 22,7; B 11,3; C 7,7 min) — `--status` pokazał `active_run: null` i pustą
  listę, końcowe statusy czytane ze state.json (wzorzec weryfikacji pkt 8).
- Weryfikacja nadzorcy: check fraz (check_verify_noc3b.py, folding diakrytyków) 35/47 OK od razu;
  12 „BRAK" rozstrzygnięte kontekstowymi grepami — wszystkie grounded (m.in. „lekki firmware"
  = 06 l.20 „lekkiego firmware/UI"; „testy elektryczne/funkcjonalne/klasyfikacja jakości odzysku"
  = 17 l.224–226; „link czasowy" i „kolejka kuracji" = 13 l.33/35; „Łowca Części" i integracja z
  botem Telegram = README l.67; „decyzja człowieka" = 30 l.6/9; „receptury klimatyczne JSON/YAML"
  = 24 l.86). Zero halucynacji do usunięcia. Cytat z sekcji 6 („Komunikacja nigdy nie powinna
  wyprzedzać…") instancja B podała z linią 36 — nadzorca potwierdził exact (podciąg linii 36).
- Korekty nadzorcy (3, minimalne diffy): (1) MARKETING zdanie wstępne §9 „numerowane 25–31" →
  „25–32" (spójność z nagłówkiem zmienionym przez instancję B — dopuszczone poleceniem); (2) plik
  33 „Fundamenty Technologicznych NSIP" → „Fundamenty Technologiczne NSIP" (H1 źródła 00);
  (3) plik 33 „zintegrowanego z siecią Straży Przyszłości" → „z inicjatywą Straży Przyszłości"
  (wierność źródłu: 21 l.6 „fabrycznie zintegrowane z inicjatywą Straży Przyszłości"). Po
  korektach check linki powtórzony. Odmiana „KiCada" w pliku 33 zostawiona — źródło 12 samo
  używa form odmienionych („KiCada" l.12, „KiCadem" l.48).
- Check linków wewnętrznych: 183 linki / 0 martwych (33 + MARKETING + AI-PROCESS + README).
  Label „Smartfony jako Sterowniki Edge Computing" (oś 5) nietknięty — check fuzzy patcha po
  integracji czysty (diff README: dokładnie 2 zmiany).
- Integracja README (2 minimalne diffy): oś 4 (Zasoby) *Inspiracje* += link do 33 (odzysk i
  elektronika z odzysku = naturalna oś warsztatu), lista „Projekty Pilotażowe i Inspiracje" +=
  pozycja 33. Commit i push na main przez nadzorcę (instancje mają zakaz git).

### Noc 2026-10-22 (NOC-5, start 05:45 — kontynuacja po NOC-0 i NOC-3)

- Kontekst: NOC-0 i NOC-3 zakończone w całości (commit + push OK); NOC-5 wykonał w całości
  3 propozycje z NOC-3 (ROADMAPA o 32/33, PROJEKTY/34, CONTRIBUTING §7 o poprzecznych 32/33).
- Readiness: probe Muse nadal „Model unavailable" (trwały stan) → bieg od razu na roboczym
  `nvidia/z-ai/glm-5.3-flash` (stan infrastruktury bez zmian). Binarka w scratch wypadła po
  czyszczeniu 24h — readiness rc=0 dzięki fallbackowi `~/.opencode/bin/opencode`. Sync z remote:
  `git log HEAD..origin/main` puste (klon aktualny).
- UWAGA godzinowa: sekwencja biegu startowała 05:45 (w oknie), ale sama komenda startu farmy
  weszła o 06:07 — ok. 7 min po zamknięciu okna (narzut narzędzi nadzorcy między readiness a
  startem). Bieg dokończono (ubijanie zostawiłoby półzapisane pliki); kolejne biegi: przygotować
  plan i pliki pomocnicze PRZED ostatnim checkiem godziny, by start farmy wypadał przed 06:00.
- **3 instancje równolegle** (run `20261022-060732`), wszystkie `done`: A-roadmapa-spiecia-32-33
  (16,5 min; ROADMAPA — 2 akapity o pilotażach poprzecznych 32 i 33 na końcu „### Kolejne spięcia
  osi…", konwencja podsekcji zachowana), B-pilotaz-34-telemetria (24,2 min; nowy plik
  PROJEKTY/34_pilot_lacznosci_wspolnej_telemetrii.md, 156 linii + dokładnie 1 mermaid, struktura
  wzorca 32/33), C-contributing-wzorzec-32-33 (20,2 min; nowa podsekcja „### Wzorzec w praktyce:
  pilotaże poprzeczne 32 i 33" na końcu CONTRIBUTING, edycja wyłącznie dodająca).
- Weryfikacja nadzorcy: check fraz (check_verify_noc5c.py, folding diakrytyków; pierwsza wersja
  checku foldowała źródło, ale nie igłę — 22/61; po poprawce 51/61 od razu) + 10 „BRAK"
  rozstrzygniętych kontekstowymi grepami — wszystkie grounded, m.in.: „człowiek-serwisanta" = 33
  l.10, „wiedza opracowana" = 32 l.44, `schema_version` i `provider_id` w kontrakcie = 01 l.108–116
  i l.299, „zanonimizowane dane… do wspólnego API" = 21 l.10, „węzłów sterujących, bramek danych i
  sterowników systemów off-grid" = 32 l.79, „recyklingu e-odpadów… suwerennej elektroniki" = README
  l.66, „nadzór dużych modeli AI" i „Infrastruktura należy do użytkowników, nie do korporacji" =
  10 l.41/57, cytat „Ta oś zasila wszystkie pozostałe…" exact = ROADMAPA l.77, sekwencja pracy
  węzła energetycznego = 27 l.73. Check linków wewnętrznych: 268 linków / 0 martwych przed
  integracją, 270 / 0 martwych po integracji README. „[!IMPORTANT]" w 34 = konwencja repo
  (README l.17+); „Naszą zasadą" wielką literą = konwencja z 32 l.23; kontrakt danych 01 przyjęty
  wprost przez 25 (l.31), 27 (l.35) i 30 (l.41).
- Korekty nadzorcy (2, minimalne diffy): (1) plik 34, Moduł 4 — sekwencja „najpierw mierzy…
  ogranicza je na drodze optymalizacji sterowania, a docelowo korzysta z planowania,
  magazynowania i dystrybucji" przypisana pilotażowi 27, podczas gdy u źródła (27 l.65 i ROADMAPA
  Synergie) opisuje relację pilotażu 25; dla samego węzła energetycznego źródło (27 l.73) mówi
  „najpierw mierzy własne zużycie energii, a w kolejnym etapie współpracuje ze wspólnymi
  narzędziami analitycznymi tej osi" — przywrócono brzmienie źródła; (2) ROADMAPA ¶ o 33 —
  „katalog, w którym… i do której można wrócić" → „i do którego" (zgodność z „katalogiem").
- Integracja README (2 minimalne diffy): oś 4 (Zasoby) *Inspiracje* += 34 (README sam opisuje
  projekt 10 jako sieć „do monitorowania zasobów gospodarczych", l.64 — wspólna telemetria to
  naturalne przedłużenie osi), lista „Projekty Pilotażowe i Inspiracje" += pozycja 34. Po
  integracji diff README: dokładnie 2 zmiany; label „Smartfony jako Sterowniki Edge Computing"
  (oś 5) nietknięty (pułapka fuzzy patcha z NOC-3 — czysto). Commit i push na main przez
  nadzorcę (instancje mają zakaz git).
- Lekcje: (a) check fraz musi foldować i igłę, i źródło — inaczej połowa fraz z diakrytykami da
  fałszywe „BRAK"; (b) instancja znowu „pożyczyła" sekwencję cytowaną u sąsiada (27→25) — cytaty
  „przejęte wprost z X" porównywać z fragmentem X, który mówi o X, nie o projekcie pokrewnym;
  (c) artefakty FARM DIR nazywać z datą (gen_plan_noc5.py okazał się plikiem z 2026-10-20 —
  nie nadpisywać, nowy bieg: gen_plan_noc5_20261022.py).

### Noc 2026-10-23 (NOC-22, start 22:07 — pierwszy pełny bieg nocy 23/24)

- Kontekst: repo było BRUDNE — 3 pliki z **przerwanego biegu `20261023-013816` (noc 22/23, start 01:38)**:
  A-marketing-zakres-25-34 `done`, B-pilotaz-35-baza-wiedzy `timeout_killed`, C-contributing-wzorzec-34
  `timeout_killed`; tamten nadzorca nie wykonał KROKU 4 (weryfikacja/commit/AI-PROCESS). Ten bieg dokończył
  przerwaną pracę zamiast stashować na trwałe (lekcja NOC-0: `timeout_killed` z kompletnym plikiem = przyjmować
  po przeglądzie treści, nie po statusie).
- Sync z remote: remote 14 commitów przed HEAD (selfopt T50–T53, AGENTS.md) → `git stash -u` + `git rebase
  origin/main` + `git stash pop` — czysto, kolizji zero (remote nie dotyka CONTRIBUTING/MARKETING/PROJEKTY).
- Weryfikacja orphaned pracy: check fraz 56 igieł (fold OBU stron — wzorzec NOC-5c) 43/56 od razu; 13 „BRAK"
  rozstrzygnięte greppami — WSZYSTKIE grounded (m.in. „pomiar, rekomendacja, decyzja człowieka…" = ROADMAPA l.187,
  nie 30; „własnością społeczności… nie monetyzacji" = 30 l.47; „Knowledge bundle export | ✅ Działa" =
  PROJEKTY/00_knowledge_base/API_INVENTORY l.86; „wynik analizy, a nie surowy strumień danych" = 34 l.9;
  anonimizacja = 01 l.614; reszta = deklinacje igieł nadzorcy). Pułapka: `PROJEKTY/00_knowledge_base/` jest
  PODKATALOGIEM PROJEKTY/ — względne linki z 35 są poprawne; H1 pliku 13 to dosłownie
  „[PROJEKT 13] GitHub-First Baza Czesci z Recyklingu" (źródło bez diakrytyków).
- Commit i push **6aab780**: PROJEKTY/35 (czwarty pilotaż poprzeczny — wspólna baza wiedzy i snapshoty,
  spięcie 01+24+13+30, 158 linii + 1 mermaid), MARKETING §9 → (25–35) (lista += 35; punkty 1/4 zakresy 25–34→25–35;
  punkt 5 „25–31"→„25–35" — stary zakres), CONTRIBUTING §7 „Wzorzec w praktyce: pilotaże poprzeczne 32–34"
  (akapit o 34 z przerwanego biegu) + integracja README (oś 4 *Inspiracje* += 35 — konwencja: wspólne warstwy
  między węzłami już mieszkają na osi 4; lista pilotaży += poz. 35).
- **Własny bieg farmy** (run `20261023-235325`; probe `nvidia/z-ai/glm-5.3-flash` PROBE_OK):
  A-roadmapa-spiecia-34-35 `done` (21,7 min), B-ankieta-sciezka-d-35 `done` (14,7 min),
  C-contributing-wzorzec-35 `timeout_killed` (25,0 min — plik kompletny, przyjęty wg lekcji NOC-0).
- Weryfikacja biegu: tura 2 — 24/25 igieł od razu; 1 „BRAK" = deklinacja cytatu (34 l.59 ma nominativ
  „Wspólna baza wiedzy w wersji wielowęzłowej" — cudzysłów wokół zdeclinowanej frazy usunięty); linki
  354 / 0 martwych. Korekty nadzorcy (4): (1+2) ROADMAPA — etykieta
  „[\[PROJEKT 13\] GitHub-First Baza Czesci z Recyklingu]" → „GitHub-first baza części z recyklingu"
  w DWÓCH miejscach (błąd wproszony przez NOC-5 w ¶ o 33, bieżąca instancja skopiowała go do ¶ o 35;
  escapowane nawiasy w etykiecie renderują się dosłownie); (3) ROADMAPA ¶ o 34 — atrybucja „podsekcja
  «Łączność i wspólne dane» wskazała… wspólny kontrakt danych" → „…oraz wspólną bazę wiedzy" (32 l.82
  nie mówi o kontrakcie danych); (4) CONTRIBUTING — jak wyżej pkt (4) tury 2.
- Commit i push **d6cd456** (ROADMAPA +6/−2 w dwóch akapitach, ankieta +2, CONTRIBUTING +4/−2).
  Instancje mają zakaz git — commity przez nadzorcę.
- Lekcje: (a) przerwana praca poprzedniego nadzorcy = dokończyć KROK 4, nie stashować na trwałe;
  (b) etykiety linków kopiowane wiernie z H1 źródeł bez diakrytyków (plik 13) normalizować do konwencji
  cross-referencji (README l.67) — escapowane nawiasy w labelu są wadą renderingu;
  (c) igły checku z deklinacją rodzą fałszywe BRAK — sprawdzić nominativ w źródle, zanim frazę oznaczy się
  jako wymyśloną.


## Wzorzec promptu instancji (szablon dla nadzorcy)

Destylat skutecznych promptów instancji z nocnych biegów 2026-10-20/21 (NOC-1, NOC-5, NOC-22).
Biegi prowadzone pełnym wzorcem (NOC-5, NOC-22, NOC-1 z 2026-10-21) zakończyły się każdym razem
3/3 instancji `done` i zerem halucynacji do usunięcia. Nadzorca kopiuje szablon przed startem
instancji i uzupełnia pola [DO UZUPELNIENIA]. Sekcję aktualizuje wyłącznie nadzorca po biegu.

### Szablon promptu (kopiuj-wklej i uzupełnij)

```
Pracujesz w katalogu repozytorium: [DO UZUPELNIENIA — absolutna ścieżka repo; nigdy ścieżka
względna]. Jesteś [DO UZUPELNIENIA — rola, wzorcowo: współtwórca manifestu inicjatywy
NARODOWE SIŁY INTELEKTUALNE POLSKI (NSIP)]. Język: polski. Styl: manifest spójny z README
(akcentowane hasła: WSPÓLNE DOBRO, Dochód Gwarantowany, NARODOWY WYSIŁEK INTELEKTUALNY).

TWARDE ZAKAZY:
(1) zakaz wymyślania faktów, statystyk, procentów, kwot, dat, linków URL i nazw organizacji
    spoza repo — jeśli czegoś nie ma w plikach repo, NIE pisz tego; kolejność zdarzeń
    wyłącznie względna („w późniejszym etapie”, „przed skalowaniem”);
(2) zakaz poleceń git i jakichkolwiek modyfikacji plików innych niż własny plik docelowy —
    integrację i commit robi wyłącznie nadzorca po przeglądzie diffów;
(3) zanim podlinkujesz jakikolwiek plik PROJEKTY/, zweryfikuj jego istnienie poleceniem ls
    na katalogu PROJEKTY/ — linkuj wyłącznie istniejące pliki;
(4) [DO UZUPELNIENIA — zakazy specyficzne dla zadania, np. „zero danych liczbowych”,
    „edycja wyłącznie dodająca”].

ZADANIE: [DO UZUPELNIENIA — jedno zdanie: co dokładnie tworzyć lub który plik rozszerzać
i o co].

PLIK DOCLOWY: wyłącznie [DO UZUPELNIENIA — jeden plik docelowy na instancję].

ŹRÓDŁA — przeczytaj najpierw, czerp wyłącznie z plików repo:
- [DO UZUPELNIENIA — co czytać, wzorcowo: README (treść osi), ROADMAPA (miejsce w fazach),
  CONTRIBUTING (Złote zasady), własny plik docelowy w obecnym stanie].

INSPIRACJE — konkretne istniejące pliki do przejrzenia:
- [DO UZUPELNIENIA — listę zweryfikuj ls-em PRZED wysłaniem prompta i podawaj wyłącznie
  pliki, które istnieją; wzorcowo: PROJEKTY/25_pilot_automatyzacji_zywnosci.md,
  PROJEKTY/26_pilot_ai_w_medycynie.md, PROJEKTY/27_pilot_sieci_energetycznej.md
  (wzorzec pilotażu: warstwy, mermaid, miejsce w fazach) + pliki tematyczne danej osi].

WYMAGANIA JAKOŚCI:
- jeden plik docelowy, praca wyłącznie w katalogu repo;
- każdy cytat i każde odwołanie potwierdzone u źródła (plik + sekcja);
- przy dopisywaniu sekcji edycja wyłącznie dodająca — bez zmieniania i usuwania istniejących
  nagłówków i wpisów; szukaj też „wiszących” odwołań, które nowa sekcja naprawia;
- [DO UZUPELNIENIA — wymagania specyficzne zadania].
```

### Zasady skuteczności (lekcje z tych biegów)

1. **Absolutna ścieżka repo zamiast względnej** — przy ścieżkach relatywnych instancje dostawały
   na starcie „File not found” (sesja nie od razu widzi cwd repo); po przejściu na ścieżki
   absolutne pracowały poprawnie.
2. **Weryfikacja istnienia pliku listą katalogu przed linkowaniem** — nadzorca sprawdza ls-em
   katalog PROJEKTY/, zanim wskaże plik w prompcie; wtedy weryfikacja linków w instancjach
   przechodzi w całości (0 martwych linków).
3. **Zakaz git dla instancji** — jedna instancja = jeden plik docelowy, praca w katalogu repo;
   integrację z README i commit na main robi wyłącznie nadzorca po przeglądzie diffów.
4. **Kolejność zdarzeń wyłącznie względna zamiast dat** — zero dat, kwot, procentów, URL-i
   i nazw organizacji spoza repo („w późniejszym etapie”, „przed skalowaniem”); czerpanie
   wyłącznie z plików repo.
5. **ZAKAZY wypisane jawnie na początku prompta** — sprawdzony wzorzec „ZAKAZY + absolutna
   ścieżka + weryfikacja listą katalogu” dał zero halucynacji w 3/3 instancjach.
6. **Cross-check odwołań** — przy dopisywaniu sekcji szukać też „wiszących” odwołań do
   naprawienia (odwołanie z CONTRIBUTING naprawione nową sekcją w ankiecie).
7. **Styl i hasła podane wprost w prompcie** — polski, manifest spójny z README, akcentowane
   hasła; instancje piszą wtedy jednym głosem.

## Wzorzec weryfikacji nadzorcy

Destylat procedury sprawdzania pracy instancji przez nadzorców farmy, z biegów nocy 2026-10-21
(NOC-1, NOC-3, NOC-5). Uzupełnia „Wzorzec promptu instancji”: tamten szablon mówi, jak zlecić
pracę, ten — jak ją sprawdzić, zanim trafi do commita. Kolejne biegi mają tu gotową checklistę:
zadanie jest domknięte dopiero po przejściu wszystkich kroków. Commit i push na main wykonuje
wyłącznie nadzorca (instancje mają zakaz git).

1. **Przegląd KAŻDEGO diffu wzrokiem — przed dopuszczeniem do commita.** `git status --porcelain`
   pokazuje pełny zestaw nowych i zmienionych plików, `git diff` — każdy dopisany i usunięty
   wiersz. Instancja może dotykać wyłącznie swojego pliku docelowego; każdy inny ślad w statusie
   wymaga wyjaśnienia, zanim cokolwiek pójdzie dalej.
2. **Automatyczne checki fraz u źródeł — dwie tury skryptu.** Spisać listę fraz cytowanych
   w nowych plikach i porównać je ze źródłami skryptem (wzorzec: `check_verify_noc5b.py`;
   w NOC-5 dwie tury: `check_verify_noc5b.py` 67/71 OK, `check_verify2_noc5b.py` 45/47 OK).
   Frazy oznaczone BRAK podlegają jeszcze kontekstowemu grepowi u źródła — dopiero po nim frazę
   uznaje się za wymyśloną; sam BRAK nie jest werdyktem.
3. **UWAGA: część źródeł repo jest zapisana bez polskich diakrytyków** (lekcja z pilota 15:
   „sciezka”, „podaz”). Po nieudanym grepsie z ogonkami szukać tej samej frazy bez diakrytyków
   lub po słowach kluczowych — bez tego kroku grounded fraza zostanie błędnie uznana za
   halucynację.
4. **Weryfikacji podlegają także fragmenty podane jako cytaty wprost.** Instancja potrafi
   „poprawić” cytat (lekcja z pilota 31: „kalendarz” → „liczby”) — każdy cytat porównać z linią
   źródła (plik + numer linii); cudzysłów nie gwarantuje wierności.
5. **Automatyczny check linków wewnętrznych skryptem** (wzorzec: `check_links_noc5b.py`;
   w NOC-5: 271 linków, 0 martwych) — dla WSZYSTKICH nowych i zmienionych plików biegu
   (w NOC-1 `check_links_noc1.py`: 27 + CONTRIBUTING + MARKETING + README; w NOC-3
   `check_links_noc3.py`: 28 + 29 + AI-PROCESS). Zero martwych linków to warunek dopuszczenia
   do integracji.
6. **Korekty nadzorcy wyłącznie minimalnym diffem.** Poprawia się wiersz, nie plik (w NOC-5
   dwie korekty: plik 30 — „nie profilowaniu reklamowemu” → „a nie monetyzacji przez komercyjne
   korporacje”, źródło: plik 19 l.5; plik 31 — cytat MARKETING „a nie liczby” → „a nie kalendarz”,
   exact z l.34). Po każdej korekcie powtórzyć checki fraz i linków na dotkniętym pliku.
7. **Integracja z README przez doklejenie linków do ISTNIEJĄCYCH list.** Najpierw sprawdzić
   w aktualnym README, czy dana oś ma już listę *Inspiracje* (lekcja z NOC-3: propozycja
   „oś 5 nie ma jeszcze Inspiracji” okazała się nieaktualna — nadzorca dokleił link do
   istniejącej listy zamiast tworzyć nową). Oś bez listy dostaje nowy podpunkt *Inspiracje*
   (wzorzec z NOC-22). Każdy nowy pilotaż dopisać też na liście „Projekty Pilotażowe
   i Inspiracje”. Uwaga na fuzzy patch przy integracji — w NOC-3 skrócił label „Smartfony jako
   Sterowniki Edge Computing”; przywrócono oryginał.
8. **Statusy końcowe instancji czytać bezpośrednio ze state.json.** Po zakończeniu wszystkich
   instancji `--status` pokazuje `active_run: null` i pustą listę (nadzorca sprząta stan) —
   „pusto” nie znaczy, że nic nie zrobiono. Końcowe statusy i czasy czytać ze state.json
   (wzorzec: `nsip-farm/check_run_noc1.py`).

Nadzorcę obowiązuje tu ta sama dyscyplina, co instancje („Zasady jakości” poniżej): rzetelna
weryfikacja u źródeł jest częścią NARODOWEGO WYSIŁKU INTELEKTUALNEGO — praca instancji staje się
WSPÓLNYM DOBREM dopiero wtedy, gdy nadzorca potwierdzi ją krok po kroku.

## Wzorzec integracji README

Destylat procedury integracyjnej nadzorców — jak doklejać nowe pilotaże i sekcje do README
bez kolizji z cudzymi treściami i bez ich nadpisywania. Uzupełnia „Wzorzec weryfikacji
nadzorcy”: tamten mówi, jak sprawdzić pracę instancji, ten — jak wpiąć jej efekty w README,
zanim trafią do commita i push na main.

1. **Najpierw sprawdź, czy oś w README ma już listę *Inspiracje*.** W aktualnym README odszukaj
   opis danej osi i sprawdź, czy istnieje pod nią podpunkt *Inspiracje*. Doklejaj link do
   ISTNIEJĄCEJ listy (lekcja z NOC-3: propozycja „oś 5 nie ma jeszcze Inspiracji” okazała się
   nieaktualna — nadzorca dokleił link do istniejącej listy zamiast tworzyć nową).
2. **Oś bez listy *Inspiracje* dostaje nowy podpunkt.** Pod opisem takiej osi dopisz podpunkt
   *Inspiracje* z linkiem do nowego pliku, w konwencji istniejących osi (wzorzec z NOC-22 —
   tak oś 2 zyskała podpunkt *Inspiracje* z linkiem do pilotażu 26).
3. **Każdy nowy pilotaż dopisz też na liście „## Projekty Pilotażowe i Inspiracje”.** Nowa
   pozycja na tej liście w konwencji sąsiednich wpisów: numer, tytuł, link do pliku
   w PROJEKTY/ i jednozdaniowy opis.
4. **Korekty i dopiski wykonuj minimalnym diffem — edytujesz wiersz, nie plik.** Nie przepisuj
   całych sekcji i nie porządkuj „przy okazji”; po każdej korekcie powtórz checki fraz i linków
   na dotkniętym pliku (spójnie z „Wzorcem weryfikacji nadzorcy”).
5. **Pułapka fuzzy patcha (lekcja z NOC-3).** Narzędzie łatania tekstu potrafi skrócić etykietę
   sąsiedniego linku (w README skrócono „Smartfony jako Sterowniki Edge Computing”) — po
   integracji przejrzyj diff README wiersz po wierszu i przywróć oryginalne etykiety.
6. **Pułapka nazwy pliku 16.** Realna nazwa pliku to `PROJEKTY/16_geoportal_potencjal_rozwoju.md`
   (bez „u” w „potencjal”), a tytuły linków w repo zawierają „Potencjału” — linkuj realną nazwę
   pliku, nie tytuł.
7. **Po integracji: przegląd diffu README wzrokiem oraz automatyczny check linków wewnętrznych.**
   Zero martwych linków to warunek dopuszczenia do commita.

## Zasady jakości (obowiązują każdą instancję)

- Jeden plik docelowy na instancję, praca w katalogu repo, ZAKAZ poleceń git i modyfikacji
  innych plików — integrację i commit robi wyłącznie nadzorca po przeglądzie diffów.
- Zakaz wymyślania faktów, statystyk, dat, kwot, linków i nazw organizacji; kolejność zdarzeń
  wyłącznie względna. Czerpanie wyłącznie z plików repo.
- Polski, styl manifestu spójny z README (akcentowane hasła: WSPÓLNE DOBRO, Dochód
  Gwarantowany, NARODOWY WYSIŁEK INTELEKTUALNY).

## Propozycje na kolejną noc (3 instancje, gdy pojemność pozwoli)

Stan po NOC-22 (2026-10-23): pilotaże 25–35 (35 = wspólna baza wiedzy i snapshoty — czwarty pilotaż poprzeczny,
spięcie 01+24+13+30); ROADMAPA „Kolejne spięcia osi" dokumentuje 30/31 oraz poprzeczne 32/33/34/35; CONTRIBUTING
§7 „Wzorzec w praktyce: pilotaże poprzeczne 32–35"; MARKETING §9 (25–35) z punktem 6 o pierwszym pilotażu
poprzecznym (32); README: oś 4 *Inspiracje* += 33/34/35, lista pilotaży += 35; ankieta: ŚCIEŻKI A–D, D z kuracją
wspólnej bazy wiedzy (pkt 5 + punkt mapujący); AI-PROCESS ma wzorzec promptu, wzorzec weryfikacji nadzorcy
i wzorzec integracji README.

1. **PROJEKTY/36 — piąty pilotaż poprzeczny: wspólna analiza porównawcza wielu węzłów (spięcie 01+30+34+35)**:
   34 l.59 mówi wprost, że „porównywanie przypadków między węzłami różnych osi jest tym, czego nie da osiągnąć
   żadna pojedyncza telemetria", 01 l.153: „Takie wyniki są wystarczające, by zasilać wspólny model wiedzy
   i porównywać przypadki między stawami", a oś 4 w ROADMAPA (Faza 1, cytat w 35 l.90) zapowiada „wspólne
   narzędzia analityczne i modele wspierające decyzje o alokacji zasobów między węzłami… pracujące na wiedzy
   zgromadzonej przez wiele węzłów naraz" — warstwa analizy korzystającej z bazy 35 nie ma jeszcze własnej
   koncepcji; pilotaż 36 projektuje ten wspólny model analityczny (wzorzec struktury: 32/33/34/35 — H1,
   Intelekt wyprzedza Kapitał!, Opis, moduły ###, JEDEN mermaid, Zależności, Mapa drogowa, Społeczność,
   Zasoby, stopka); inspiracje (verify ls-em): PROJEKTY/01, PROJEKTY/30, PROJEKTY/34, PROJEKTY/35, ROADMAPA.
   BEZ danych liczbowych, BEZ lokalizacji, kolejność wyłącznie względna.
2. **MARKETING §9 — punkt 7 o opowiadaniu o pilotażach poprzecznych 33–35**: punkt 6 opisuje dziś tylko pierwszy
   pilotaż poprzeczny (32); dopisać punkt 7 według wzorca punktu 6 — jak opowiadać o pilotażach, które nie budują
   węzła, lecz wspólne warstwy (33 utrzymanie w ruchu, 34 łączność i wspólna telemetria, 35 wspólna baza wiedzy),
   nadal wyłącznie przez tytuły i sekcje, którymi pliki same się przedstawiają; inspiracje (verify ls-em):
   MARKETING.md §9, PROJEKTY/33, PROJEKTY/34, PROJEKTY/35. BEZ liczb i dat.
3. **REKRUTACJA_ANKIETA — ŚCIEŻKA C (KOD I PROOF OF CONCEPT) += realne zalążki kodu wspólnej bazy wiedzy**:
   dopisek (edycja wyłącznie dodająca) wskazujący `pipelines/export_knowledge_snapshot.py` oraz
   `reports/README.md` (istnieją — verify ls-em) jako dokonania z kodu przy pilotażu 35 (generator eksportu
   snapshotu wiedzy, katalog raportów i snapshotów); inspiracje (verify ls-em): ankieta ŚCIEŻKA C, PROJEKTY/35,
   pipelines/export_knowledge_snapshot.py, reports/README.md. BEZ liczb i dat.
   (Model: `nvidia/z-ai/glm-5.3-flash`; przy 429/limit → 1 instancja. Plan.json = płaska tablica;
   absolutna ścieżka repo; instancje mają zakaz git; weryfikacja wg „## Wzorzec weryfikacji
   nadzorcy", integracja wg „## Wzorzec integracji README".)
