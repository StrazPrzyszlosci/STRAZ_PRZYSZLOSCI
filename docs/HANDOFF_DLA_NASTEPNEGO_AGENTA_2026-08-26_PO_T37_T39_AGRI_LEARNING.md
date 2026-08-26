# Handoff dla Następnego Agenta - po T37 T38 T39 - 2026-08-26 (cykl 5)

## Kontekst wejściowy

Przeczytano ostatni handoff: `docs/HANDOFF_DLA_NASTEPNEGO_AGENTA_2026-08-26_PO_T34_T36_AGRI_HARVEST.md` (T34–T36 DONE). Priorytety wejściowe: T37 (korelacja plon↔telemetria, P1), T38 (kalibracja suggest-only, P2), T39 (onboarding grow-agenta z bota, P3). Operator powtórzył cykl piąty raz.

## Co zrobiono

### T37 — DONE: Korelacja plon↔warunki

- `cloudflare/src/agri_correlation.js`: `pearsonR()` (czysta funkcja, z zerowym wariancja → null), `alignMonthlySeries()` (miesięczne średnie czujników z telemetry staging × sumy plonu z harvest_records, wspólne miesiące), `computeGrowCorrelation(env, providerId, {monthsBack})`.
- Endpoint `GET /v1/agri/correlation?provider_id=&months=N` (auth tokenem providera). Read-only — niczego nie zmienia.
- Wynik zawiera `note`: "korelacja != przyczynowość" — przypomnienie dla konsumenta.

### T38 — DONE: Suggest-only kalibracja pasm

- `cloudflare/src/agri_calibration.js`: `suggestBandAdjustments(policy, correlation, {minMonths, minAbsR, stepPercent})` — kierunek: r>0 → podnieś górne krawędzie, r<0 → obniż dolne; clamp invariants; pomijanie przy |r| poniżej progu lub za małej liczbie miesięcy; `buildCalibrationPrBody()` — markdown z bramkami bezpieczeństwa do draft-PR przez flow B5/T23/T30.
- Endpoint `POST /v1/agri/calibration-suggest` (admin-only, X-Trust-Editor-Secret); zwraca JSON + body PR. **NIGDY nie zapisuje do D1 ani nie aplikuje zmian** (boiler-plate w reply wyraźnie to mówi).
- Testy: kierunek + progi + pomijanie + brak auto-apply.

### T39 — DONE: Onboarding grow-agenta z bota

- `cloudflare/src/agri_grow_agent_setup.js`: `parseGrowAgentSetupCommand()` (aliasy `grow-agent`/`grow_agent`, normalizacja lowercase), `validateGrowCellId()` (regex), `buildGrowAgentSetupReply()` (instrukcja PL: rejestracja, env, polecenie, kill switch; **token wyłącznie jako placeholder `<TOKEN_Z_REJESTRACJI>`**), `handleGrowAgentCommand()`.
- Discord: case `"grow-agent"|"grow_agent"` w `discord_api_handler.js`.
- Telegram: branch w `telegram_issues.js` ze status `command_grow_agent_setup`.

## Testy wykonane

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
# Ran 318 tests in ~3.1s — OK (bez zmian; tura w 100% JS)

# mjs: wszystkie tests/*.mjs
# pass=333 fail=0 (było 322, +11: T37+T38 6, T39 5)

node --check cloudflare/src/{worker,discord_api_handler,telegram_issues,agri_grow_agent_setup}.js  # SYNTAX OK
```

## Status backlogu

| Zadanie | Status | Opis |
|---|---|---|
| T1–T36 | DONE | Patrz handoffy PO_T21_T26 / PO_T27_T30 / PO_T31_T33 / PO_T34_T36. |
| T37 | DONE (ta tura) | Korelacja plon↔telemetria: monthly means × harvest, Pearson r, read-only. |
| T38 | DONE (ta tura) | Suggest-only kalibracja pasm z body PR; bramki bezpieczeństwa; zero auto-apply. |
| T39 | DONE (ta tura) | `!grow-agent setup <cell>` w Discord+Telegram z placeholderem tokenu. |
| T24 | ODOCZONE | Fizyczny operator: checkout CERN S1, hardware S6, pilot półki. |
| T40 | NEXT / P1 | WebUI/manualna kalibracja: wizualizacja różnic pasm (diff HTML/MD) do review PR bezpośrednio z `/v1/agri/calibration-suggest`. |
| T41 | OPEN / P2 | Raport trendów z plonów: `harvest_<cell>` AUC sezonowy, regresja liniowa per crop_profile. |
| T42 | OPEN / P3 | Webhook do EXECUTION_PACK_GITHUB_REPO: automatyczny draft-PR z kalibracją (po zatwierdzeniu przez maintainera). |
| API/worker hardening | OPEN | background-rate-limity, floating-ip healthchecks, secret-rotation. |

## Następne zadania

### T40 — PRIORYTET 1: Wizualizacja diff do review

`/v1/agri/calibration-suggest` zwraca już body PR; kolejnym krokiem jest czytelne zestawienie stare→nowe pasmo w formacie tekstowym i podlinkowanie do flow execution-pack (B5/T23) — operator wybiera jednym kliknięciem w Discordzie.

### T41 — PRIORYTET 2: Trendy z plonów

Tabela `harvest_records` ma SUM mass_g agregat; T37 daje korelację. Brakuje wizualizacji czasowej: `/v1/agri/harvest/trends?provider_id=&months=N` (auth provider) z sezonowymi seriami i regresją liniową per crop_profile.

### T42 — PRIORYTET 3: Automatyczny draft-PR

Przez `execution_pack_initiator` flow (T23) — wygenerowanie canary PR z plikiem `seed_policy.json` uaktualnionym o propozycje T38; utrzymane `no_auto_merge + no_direct_push`. Wyłącznie po manualnym triggrze (`!calibration apply <policy>`).

## Kierunki rozwoju (po 5 cyklach)

1. **Pętla uczenia jest domknięta technicznie**: T37 korelacja, T38 kalibracja, T39 onboarding agenta. **Brakuje jedynie danych** — T24 operator z prawdziwą półką. To jedyne krytyczne zadanie operatora; reszta to iteracja.
2. **Commit debt zamknięty** — poprzednie tury wylądowały w 4 commitach tematycznych (worker-ingestion, agri-loop, agri-ops, agri-learning) + 1 commit docs. Recomenduje się **nie** scalać ich w main aż do `wrangler deploy` i pierwszego produkcyjnego crona retencji.
3. **Deploy Workera jest naturalnym progiem jakości**: przed nim nie da się walidować zachowania scheduled() z ROW_NUMBER pruningu na realnym D1; po nim pojawią się realne metryki `automation_metrics` z produkcji i dopiero wtedy T37/T38 będą operować na prawdziwych danych.
4. **Bezpieczeństwo operacyjne** wciąż niski priorytet, ale to trzy proste zadania (healthcheck floating-IP, rate-limit tła, runbook rotacji sekretów) — rozważyć razem z T42 PR.
5. **Referencje zewnętrzne**: bez zmian.

## Zasady (konwencja bez zmian)

1. `PO_T<n>_T<m>_<OPIS>.md`, pipeline liniowy, ≤5 wykonanych zadań na turę.
2. Nowa komórka ⇒ manifest + aktualizacje map.
3. Testy obowiązkowe z liczbami: Python discover (**318**) + `tests/*.mjs` (**333 pass / 0 fail**).
4. High-risk/biologia = actuation gate; bot nigdy nie merge'uje; sekrety tylko env.
5. Każda nowa tabela z dedup + audit + (jeśli agregowalna) w automation_metrics.

## Ryzyka

- **Dane treningowe** — T37/T18/T41 operują na miesiącach telemetrii+plonu. Bez realnej półki (T24) wykresy będą puste; pierwsze sensowne wyniki dopiero po 2-3 miesiącach danych.
- **Kalibracja suggest-only wymaga review** — łatwo zignorować "correlation != causation" i zmergować PR. T40 (wizualizacja) ma to złagodzić; do tego czasu maintainer musi czytać body PR uważnie.
- **Repozytorium ma 5 commitów tematycznych w jednym pushu** — review PR jest większy niż zwykle; docelowo zalecane PR per commit.

## Referencje zewnętrzne

Bez zmian: `KnowFlow/KnowFlow_AWM` + `pkErbynn/IoT-WQMS`, `espressif/esp-claw`, `gnarzilla/deadmesh`, `Crosstalk-Solutions/project-nomad`.
