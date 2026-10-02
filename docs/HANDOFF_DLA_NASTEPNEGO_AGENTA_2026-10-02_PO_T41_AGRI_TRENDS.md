# Handoff dla Następnego Agenta - po T41 - 2026-10-02 (tura równoległa)

## Kontekst wejściowy

Przeczytano ostatni handoff: `docs/HANDOFF_DLA_NASTEPNEGO_AGENTA_2026-08-26_PO_T37_T39_AGRI_LEARNING.md` (T1–T39 DONE, T24 odroczone). Priorytet wejściowy: T40 (P1). Na starcie tury wykryto, że **osobny agent (claim `docs/AGENT_CLAIMS/T40-muse-spark.md`, branch `codex/T40-wizualizacja-diff-kalibracji`) już realizuje T40 w tym samym drzewie** — zgodnie z nowym `AGENTS.md` nie dotykano jego plików ani bloku. Zamiast tego zrealizowano **T41 (P2)** na rozłącznym obszarze plików.

Dodatkowo w tej turze: utworzono `AGENTS.md` + `docs/AGENT_CLAIMS/` (protokół anty-kolizyjny, commit `f8f2fe0` — wylądował na gałęzi T40, bo drzewo jest na niej przełączone).

## Co zrobiono

### T41 — DONE: Trendy plonów (serie sezonowe + regresja per crop_profile)

- `cloudflare/src/agri_harvest_trends.js` (NOWY, read-only, zero zapisów do D1):
  - `linearRegression()` — najmniejsze kwadraty, null przy <2 punktów / zerowej wariancji x;
  - `buildMonthlySeries()` — SUM mass_g per (crop_profile, YYYY-MM), fail-open na brudnych wierszach, profile ze spacjami bezpieczne (zagnieżdżone Mapy);
  - `cutSeriesToWindow()` + `normalizeMonthsBack()` — okno N miesięcy względem NAJNOWSZEGO miesiąca w danych (deterministyczne, bez time-bombów zegarowych — lekcja z time-bomba `test_expiry_report`, którego padnięcie wykryto i które naprawił agent T40);
  - `computeHarvestTrends(env, providerId)` — serie + regresja per profil + `direction` (rising/falling/stable/unknown) + note "trend != gwarancja" (kontynuacja zasady T37).
- Route `GET /v1/agri/harvest/trends?provider_id=&months=` — **blok T41 w `cloudflare/src/worker.js` z markerami** (rejon harvest POST, z dala od bloku T40), provider-auth wzorem T36.
- `tests/agri_harvest_trends_test.mjs` — 7 testów (regresja, kierunki, grupowanie, okna z przełomem roku, mock-DB multi-crop, pusty ledger/no_db, helper trendów).

## Testy wykonane

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
# Ran 318 tests — OK (wcześniejszy 1 fail time-bomba naprawiony w working tree przez agenta T40)

node --test tests/*.mjs
# pass=347 fail=0 (było 333: +7 T40 agenta równoległego, +7 T41 ta tura)

node --check cloudflare/src/{worker,agri_harvest_trends}.js  # SYNTAX OK
python3 agentic_cells/validate_cell_manifest.py  # OK: 11 manifest(s) valid
python3 human_approval/validate_record.py  # OK
```

## Status backlogu

| Zadanie | Status | Opis |
|---|---|---|
| T1–T39 | DONE | Bez zmian. |
| T40 | IN PROGRESS (inny agent) | Wizualizacja diff kalibracji — claim T40-muse-spark; NIE DOTYKAĆ. |
| T41 | DONE (ta tura) | Trendy plonów per crop_profile; moduł+testy zcommitowane, route w working tree. |
| T24 | ODROCZONE | Fizyczny operator (CERN S1, hardware S6, pilot półki) — warunek wartości T37/T38/T41. |
| T42 | OPEN / P1 | Draft-PR z kalibracją przez execution_pack flow (`!calibration apply`, no_auto_merge). |
| API/worker hardening | OPEN / P2 | background-rate-limity, floating-IP healthcheck, secret-rotation runbook. |

## Następne zadania

### T42 — PRIORYTET 1: Automatyczny draft-PR z kalibracją

Obszar wg `AGENTS.md` §2: `execution_pack_initiator.js` + komendy bota + nowy test. Wejście gotowe: T38 (sugestia) + T40 (wizualizacja, po wylądowaniu) + T41 (trendy). Trigger wyłącznie manualny, `no_auto_merge + no_direct_push` bez zmian.

### Operacyjne — PRIORYTET 0 (przed T42): uporządkować drzewo

`cloudflare/src/worker.js` w working tree zawiera DWA bloki (T40 + T41) + fix testu — żaden nie jest commitowany. Rekomendacja: gdy agent T40 skończy, jeden wspólny commit `worker.js` (oba bloki) albo dwa commity selektywne po linijkach; testy T40+T41 już zcommitowane osobno. Gałąź `codex/T40-...` tymczasowo hostuje też commit koordynacyjny `f8f2fe0` — do przesunięcia na `main` przy najbliższym merge.

## Kierunki rozwoju

1. **Pętla uczenia kompletna na sucho**: T37 korelacja → T38 sugestia → T40 wizualizacja → T41 trendy → T42 draft-PR. Po T42 system sam proponuje i wizualizuje kalibracje; człowiek tylko merge'uje. Dalej już tylko dane (T24) i deploy.
2. **Deploy Workera** pozostaje progiem jakości (cron retencji T31, ROW_NUMBER pruning na realnym D1, pierwsze produkcyjne `automation_metrics`).
3. **Protokół AGENTS.md działa**: wykryto kolizję T40 przed kodem (claim-first), drugi agent przestrzega markerów bloków. Dowód w tej turze.

## Zasady (konwencja bez zmian)

1. Handoff liniowy `PO_T<n>_T<m>_<OPIS>.md`, ≤5 zadań na turę (ta tura celowo 1 zadanie — tura równoległa).
2. Claim-first: `docs/AGENT_CLAIMS/T<NN>-<nazwa>.md`; cudze claimy i bloki nietykalne.
3. Testy z liczbami: Python **318 OK** + mjs (obecnie **347 pass / 0 fail**).
4. High-risk/biologia = actuation gate; `physical_actuation` zabroniona; kalibracja suggest-only do ludzkiego merge'a.
5. Sekrety tylko env; tokeny nigdy w reply (placeholder `<TOKEN_Z_REJESTRACJI>`).

## Ryzyka

- **Współdzielone drzewo bez podziału na worktree**: dwa niescommitowane bloki w jednym `worker.js` — przy nieuważnym `git add -A` / `git stash` łatwo pomieszać autorstwo. Tymczasowo: commitować wyłącznie własne ścieżki (`git add <plik>`).
- **Gałąź T40 hostuje obce commity** (koordynacyjny + T41) — przed PR do main wydzielić lub zmerge'ować świadomie z operatorem.
- **Trendy bez danych** (jak T37): endpoint zwróci pustą serię z instrukcją aż T24 dostarczy realne zbiory; regresja wymaga ≥2 miesięcy danych.
- Seed approvals: `validate_record.py` OK, ale historia T21 uczy — pilnować expiry przed każdą turą.

## Referencje zewnętrzne

Bez zmian: `KnowFlow/KnowFlow_AWM` + `pkErbynn/IoT-WQMS`, `espressif/esp-claw`, `gnarzilla/deadmesh`, `Crosstalk-Solutions/project-nomad`.
