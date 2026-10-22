# Handoff dla Następnego Agenta — po T51 (samokalibracja roju + konstytucja + drabina produkcji) — 2026-10-21

## Kontekst wejściowy

Przeczytano: `AGENTS.md`, handoff `PO_T50_ROJ_BASAL`, claimy (T45–T47 zajęte).
PR #18 (T48) i #19 (T49) **zmergowane**; PR #20 (T50) **open** — T51 jest
stackowany na #20, więc do jego merge PR #21 pokazuje commity T50+T51.

Kierunek operatora (2026-10-21, wieczór):

1. „Kontynuuj budowę automatyzacji roju."
2. Korekta wizji: rój po pierwsze **bada zasoby i buduje bazę części**
   (w tym z YouTube — Łowca Części), potem **projektuje produkty z dostępnych
   części**, potem **produkuje** części/produkty/sterowniki z odzysku,
   korzystając ze zdolności udostępnionych przez ludzi (ramię robota,
   drukarka 3D); wdraża projekty w rzeczywistości, buduje możliwości,
   się ulepsza, a produkty poszerzają możliwości roju.
3. Przykład-referencja: **LiteWeed** (robot odchwaszczający; vision na starym
   smartfonie w apce Android stworzonej przez LLM, platforma z odzysku).
   Artykuł: Smart Agricultural Technology 14 (2026) 102340,
   doi:10.1016/j.atech.2026.102340 (PDF: `main.pdf` — rozkodowany;
   ScienceDirect blokuje boty, zapisany plik to strona weryfikacyjna).
4. **„To ma chodzić bez nadzoru człowieka, ale ma respektować wszystkie
   prawa ludzkie itd."** — autonomia polowa + twarde granice praw człowieka.
5. Uwaga operatora po przeglądzie: rozpoznawanie twarzy w testach to
   **test negatywny konstytucji** (blocklista ma odrzucać takie misje) —
   w repo NIE ma żadnego kodu biometrycznego/surveillance.

Claim: `docs/AGENT_CLAIMS/T51-kilo-roj-samokalibracja.md` (in_progress → done).
Branch: `codex/T51-roj-samokalibracja-kilo` (stack na T50/PR #20).

## Co zrobiono — T51

1. **`selfopt_chain/calibrate.py`** — pętla samodoskonalenia decyzji
   (wzór basal-calibrate z HYC/basal):
   - `annotate` — etykieta decyzji (operator), `decisions.jsonl`+`labels.jsonl`;
   - `fit_temperatures` — deterministyczny fit temperatur confidence per typ
     pytania: dobra-zdeferowana → wyostrzenie; zła-niezdeferowana → spłaszczenie;
     ograniczenie [0.3, 3.0]; zapis `CALIBRATION.selfopt.json`
     (format lustrzany do CALIBRATION.custom.json basala);
   - `propose` — propozycja ewolucji strategii (GEPA-style, suggest-only MD:
     statystyki strategii + accepted/rejected → sugestie korekt stałych).
2. **`swarm.py`**: `BasalDecisionCore(temperatures=...)` — kalibracja
   automatycznie podmienia seedy; **`charter.json` + `charter_check`** —
   konstytucja roju (dozwolone klasy misji; zakazane tematy: broń,
   inwigilacja, monitoring osób, rozpoznawanie twarzy — dopasowanie
   substring na rdzeniach słów z tolerancją polskich odmian); naruszenie
   **blokuje przydział** w `plan_cycle` (`reason: charter_violation`).
   Konstytucji nie zmienia rój — tylko człowiek przez PR.
3. **Drabina produkcji**: `HARDWARE_KINDS` += `3d_printer`, `robot_arm`,
   `mechanics_scrap` (zdolności: additive_manufacturing/assembly/mechanics);
   `capability_map.json` += wpisy produkcyjne + produkty wzorca LiteWeed;
   `demand_from_need` += reguły słów produkcyjnych (druk, montaż, ramię
   robota, odchwaszczanie → mechanics+assembly+vision).
4. **`docs/LITEWEED_WZORZEC_REFERENCYJNY.md`** — zdekodowany artykuł (BOM
   ≈500 CAD, YOLOX-nano mAP 0.32/118 ms na RPi5, laser 4 W 450 nm, goBilda,
   LiFePO4, walidacja Vancouver+Arusha) + mapowanie kolumn na odpowiedniki
   roju (smartfon zamiast RPi5; mechanika z odzysku; drukarka/ramię od
   ludzi) + zasada: wersja roju startuje bez aktuation ścinania.
5. **Feedback z pola**: `collect_feedback` — wiadomości LoRa
   `{"feedback": {...}}` w `--inbox-dir` stają się etykietami `source: field`
   (dedup); `orchestrator` co cykl: feedback → labels → **autokalibracja**
   → rdzeń z dopasowanymi temperaturami; `receipt["field_feedback"]`,
   `receipt["calibration"]`.

## Weryfikacja (liczby obowiązkowe)

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
# Ran 447 tests — OK  ✅ (T50: 425 + 22 nowe test_selfopt_calibrate.py)
node --test tests/*.mjs
# tests 378, pass 378, fail 0  ✅ (JS nietknięty)
python3 agentic_cells/validate_cell_manifest.py    # OK: 12 manifest(s) valid  ✅
# smoke: cykl offline działa; kalibracja applied=false bez etykiet (poprawnie),
# pętla feedback→labels→fit potwierdzona testami integracyjnymi  ✅
```

## Następne zadania (propozycje T52+, ≤5 na turę)

1. **T52 łańcuch bazy części**: integracja `pipelines/yt_parts_extractor.py`
   (Łowca) + katalog części z PROJEKTY/13 jako źródło `Demands`
   (design-pack: „co zbudować z dostępnych części") i jako ograniczenie
   przydziałów produkcyjnych (BOM-check: części dostępne → druk/montaż).
2. **T53 drabina autonomii**: poziomy polowe (observe → suggest → act)
   w konstytucji; poziom „act" warunkowany jakością kalibracji
   (min. n etykiet, accuracy prog) — formalizacja „bez nadzoru".
3. **T54 pierwszy realny run free-api** (wciąż czeka na sekrety operatora +
   quota_snapshot; potwierdza też realne confidence decyzji basala).
4. **T55 consumer spoola w moście LoRa** (remix-lora-bridge) + żywy inbox
   EDGE→HUB (feedback już przygotowany po stronie huba).
5. **T56 metryki roju**: defer-rate/accepted-rate per strategia →
   `automation_metrics` (nowa tabela D1 ⇒ konwencja §5.6: dedup checksum +
   audit event) — koordynacja z właścicielem worker.js.

## Ryzyka

- Fit temperatur v1 jest heurystyczny (kierunkowy, nie MLE jak
  basal-calibrate) — wystarczający do uruchomienia pętli; docelowo pełny fit
  po zebraniu ≥59 etykiet (wzór basala).
- Charter blokuje nadmiernie (celowo); odzyskanie zapotrzebowania wymaga
  ręcznej decyzji człowieka — to zamierzone.
- Stack na PR #20: po merge #20 PR #21 pokaże tylko T51.
- LiteWeed z laserem 4 W: wersja roju bez aktuation; każda forma fizycznego
  niszczenia chwastów = osobny PR + review bezpieczeństwa (charter:
  safe_physical_boundaries).
