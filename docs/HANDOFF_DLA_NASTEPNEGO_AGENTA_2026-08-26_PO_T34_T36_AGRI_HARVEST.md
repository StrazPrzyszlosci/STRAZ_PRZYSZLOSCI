# Handoff dla Następnego Agenta - po T34 T35 T36 - 2026-08-26 (cykl 4)

## Kontekst wejściowy

Przeczytano ostatni handoff: `docs/HANDOFF_DLA_NASTEPNEGO_AGENTA_2026-08-26_PO_T31_T33_AGRI_OPS.md` (T31–T33 DONE). Priorytety wejściowe: T34 (`/agri-metrics` w bocie, P1), T35 (budżet per instancja, P2), T36 (harvest ledger, P3). Operator powtórzył cykl czwarty raz.

## Co zrobiono

### T34 — DONE: `/agri-metrics` w bocie (Discord + Telegram)

- `agri_metrics.js`: `formatAgriMetricsReply(snapshot)` — PL dashboard (top-5 dni telemetrii avg/min/max + top-5 użyć autopilota), twarde cięcie <1800 znaków (Discord 2000 / Telegram 4096), bezpieczne fallbacki dla null/no_db.
- Discord: case `"agri-metrics"|"agri_metrics"` w discord_api_handler.js (wzorem B4 `metrics`).
- Telegram: branch `command === "agri-metrics" || "agri_metrics"` w telegram_issues.js ze status `command_agri_metrics`.
- `tests/agri_metrics_test.mjs` — +1 test formattera (null/no_db/empty/full).

### T35 — DONE: Budżet autopilota per instancja komórki

- `agri_evaluate.js`: klucz użycia rozszerzony do `policy_id|grow_cell_id|day` (`usageKey()`); `getUsedToday`/`incrementUsedToday` przyjmują instancję; `runAgriEvaluate(..., {instanceGrowCellId})`.
- Worker `/v1/agri/evaluate`: opcjonalne `payload.instance_grow_cell_id` — instancja raportująca autoryzuje się **własnym** tokenem providera i ma własny dzienny budżet; bez pola domyślnie grow_cell_id z polityki (back-compat).
- `agri_metrics.js`: `groupAutopilotUsage()` parsuje nowe klucze 3-częściowe i legacy 2-częściowe (`grow_cell_id: null`).
- Testy: izolacja budżetów A/B na jednej polityce (T35) + parsowanie kluczy (agri_metrics).

### T36 — DONE: Harvest ledger — pętla uczenia plon↔telemetria

- Migracje D1: `20260826000013-harvest-records` (UNIQUE dedup checksum), `20260826000014-harvest-records-dedup-index`, `20260826000015-harvest-records-cell-index`.
- `cloudflare/src/harvest_ledger.js`: kontrakt JSON (crop_profile, mass_g ∈ (0, 1e6], harvested_at ISO max +5 min skew; opcjonalne quality_note/source); dedup SHA-256(cell|crop|ts|mass); audit ledger `harvest_audit_events`; agregat miesięczny `harvest_<cell>_<YYYY-MM>` (SUM mass_g) w automation_metrics window='monthly' — widoczny dla dashboardu T32/B4.
- Endpoint `POST /v1/agri/harvest?provider_id=` (auth tokenem providera; duplikat → 409).
- `tests/harvest_ledger_test.mjs` — 5 testów (kontrakt, checksum, duplikat, agregat, fail-open).

## Testy wykonane

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
# Ran 318 tests in ~3.4s — OK (bez zmian; tura w 100% JS)

# mjs: wszystkie tests/*.mjs
# pass=322 fail=0 (było 314, +8: formatter 1, per-instance budget 1+1, harvest 5)

node --check cloudflare/src/{worker,harvest_ledger,agri_evaluate,discord_api_handler,telegram_issues}.js  # SYNTAX OK
```

## Status backlogu

| Zadanie | Status | Opis |
|---|---|---|
| T1–T33 | DONE | Patrz handoffy PO_T21_T26 / PO_T27_T30 / PO_T31_T33. |
| T34 | DONE (ta tura) | `!agri-metrics` / `/agri-metrics` w Discordzie i Telegramie. |
| T35 | DONE (ta tura) | Budżet autopilota per (policy_id, grow_cell_id, day) z back-compat metryk. |
| T36 | DONE (ta tura) | Harvest ledger + agregat miesięczny w automation_metrics. |
| T24 | ODOCZONE | Fizyczny operator: checkout CERN S1, hardware S6, pilot półki. |
| T37 | NEXT / P1 | Korelacja plon↔telemetria: endpoint/raport „które pasma dawały najlepszy plon" (JOIN harvest_records × sensor_readings_staging po cell+miesiąc). |
| T38 | OPEN / P2 | Sugestia kalibracji polityk z korelacji (suggest-only patch do seed_policy.json przez PR, bez auto-zastosowania). |
| T39 | OPEN / P3 | Onboarding grow-agenta: komenda `!grow-agent setup <cell>` generująca gotową linię poleceń (bez tokenu w reply). |
| API/worker hardening | OPEN | background-rate-limity, floating-ip healthchecks, secret-rotation. |

## Następne zadania

### T37 — PRIORYTET 1: Raport korelacji plon↔warunki

SQL: średnie dzienne czujników (staging) w miesiącu zbioru vs mass_g z harvest_records per (cell, month). Wynik jako JSON + sekcja w `/v1/agri/metrics` albo osobny endpoint admin-only. To pierwszy moment, w którym system odpowie na pytanie „przy jakich warunkach rosło najlepiej".

### T38 — PRIORYTET 2: Kalibracja polityk suggest-only

Na bazie T37 wygenerować propozycję zmiany pasm (diff JSON) jako draft-PR przez execution-pack flow (B5/T23/T30) — człowiek mergeuje; autopilot nigdy nie zmienia własnych progów samodzielnie.

### T39 — PRIORYTET 3: Setup grow-agenta z bota

Komenda drukująca gotową komendę uruchomienia agenta (T28) dla wskazanej komórki — bez tokenu w odpowiedzi (token tylko przez istniejący flow rejestracji).

## Kierunki rozwoju (po 4 cyklach)

1. **System odpowiada już na wszystkie pytania operacyjne** (metryki, zdarzenia, budżety, wersje polityk, plony). Otwarta pozostaje pętla uczenia: T37 (korelacja) → T38 (kalibracja przez PR) to naturalna kolejność; potem dopiero sensowne jest skalowanie liczby komórek.
2. **Fizyczny pilot to jedyne krytyczne blokadę wartości**: cała infrastruktura agri (7 modułów workerowych + agent edge + 2 komórki) czeka na pierwszą prawdziwą półkę i realne odczyty (T24-operator). Bez danych treningowych korelacja T37 będzie fikcją.
3. **Commit debt rośnie**: cztery tury (T21–T36) w jednym working tree. Rekomendacja operatorowi: podzielić na 4 commity tematyczne (ingestion/stream, agri-loop, ops-retencja, harvest) przed deployem Workera.
4. **Deploy Workera odblokuje cron**: retencja T31 i scheduled KiCad chain działają dopiero po `wrangler deploy`; przy pierwszym deploju zweryfikować ROW_NUMBER pruning na produkcyjnym D1.
5. **Referencje zewnętrzne**: bez zmian (KnowFlow/IoT-WQMS na progi; esp-claw; deadmesh; project-nomad).

## Zasady (konwencja bez zmian)

1. `PO_T<n>_T<m>_<OPIS>.md`, pipeline liniowy, ≤5 wykonanych zadań na turę.
2. Nowa komórka ⇒ manifest + aktualizacje map oczekiwanych (CI pilnuje).
3. Testy obowiązkowe z liczbami: Python discover (**318**) + `tests/*.mjs` (**322 pass / 0 fail**).
4. High-risk/biologia = actuation gate; bot nigdy nie merge'uje; sekrety tylko env.
5. Nowe tabele zawsze z dedup checksum + audit eventem + agregatem do automation_metrics (wzorzec T29/T36).

## Ryzyka

- **Zbiorczy commit (T21–T36)** — patrz kierunek 3; review rośnie liniowo z każdą turą.
- Klucze budżetu zmieniły format (`policy|day` → `policy|cell|day`) — stare wpisy w produkcji będą liczone jako legacy (grow_cell_id=null) aż wygasną retencją; nie wymaga migracji.
- `harvest_records` bez retencji — małe wolumeny, ale dodać do prune gdy pojawią się dziesiątki tysięcy wpisów (jednorazowy DELETE jak T31).
- Komenda `/agri-metrics` nie ma per-user rate limitu poza globalnym Z85 — obserwować po deployu.

## Referencje zewnętrzne

Bez zmian: `KnowFlow/KnowFlow_AWM` + `pkErbynn/IoT-WQMS` (progi jakości wody), `espressif/esp-claw` (edge runtime), `gnarzilla/deadmesh` (LoRa), `Crosstalk-Solutions/project-nomad` (offline-first).
