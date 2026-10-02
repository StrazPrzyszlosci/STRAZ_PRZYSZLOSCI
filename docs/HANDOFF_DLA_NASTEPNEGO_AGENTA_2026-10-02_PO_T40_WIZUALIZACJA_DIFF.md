# Handoff dla Następnego Agenta - po T40 - 2026-10-02 (wizualizacja diff kalibracji)

## Kontekst wejściowy

Przeczytano ostatni handoff: `docs/HANDOFF_DLA_NASTEPNEGO_AGENTA_2026-08-26_PO_T37_T39_AGRI_LEARNING.md` (T1–T39 DONE, T24 odroczone).
Priorytety wejściowe: T40 (diff kalibracji, P1), T41 (trendy plonów, P2), T42 (draft-PR, P3).
Obowiązuje `AGENTS.md` (anty-kolizja, claim-first) + `docs/AGENT_CLAIMS/README.md`.

## Co zrobiono

### T40 — DONE (wspólnie, patrz § Kolizja): wizualizacja diff kalibracji

- `cloudflare/src/agri_calibration_view.js` (NOWY, pure view, zero zapisów do D1):
  `formatDelta`, `formatBandSpan`, `formatBandDiffLine`,
  `renderCalibrationDiffText` (tekst PL <1800 znaków, Discord/Telegram),
  `renderCalibrationDiffMarkdown` (tabela MD do body PR),
  `buildCalibrationReview` / `buildCalibrationView` (bundle suggest-only, `auto_applied: false`).
- `tests/agri_calibration_view_test.mjs` (NOWY, 6 testów: delty, linie diff, tekst z bramkami,
  pusty wynik, tabela MD, bundle suggest-only).
- `cloudflare/src/worker.js` — WŁASNY BLOK `// === T40 calibration view START/END ===`:
  `GET /v1/agri/calibration-view` (admin-only `X-Trust-Editor-Secret`; ładuje politykę po
  `policy_id` lub `grow_cell_id`, liczy korelację T37 + sugestię T38, zwraca
  `{ suggestion, view (znormalizowane text/markdown), pull_request_body }`).
  Normalizacja kształtu view (text/review_text, markdown/review_markdown) — patrz § Kolizja.
- ODCZYT: `cloudflare/src/agri_calibration.js` (T38, bez modyfikacji).

### Błąd znaleziony i stan naprawy (analiza repo)

- `tests/test_expiry_report.py::test_main_exit_codes` był time-bombem: fixture kotwiczyły do
  `NOW=2026-08-26`, a `main()` liczy względem wall-clock — po 2026-09-15 gałąź "warn_only"
  stawała się expired (exit 1 zamiast 0) i cała suita Python padała (318 run, 1 fail).
  FIX (minimalny, w worktree w trakcie tury — autorstwo drugiego agenta, NIE nadpisywany):
  `warn_expires` liczone od `datetime.now(timezone.utc)+20d`. Po fixie: **318 OK**.
  UWAGA: gałęzie ok/expired w tym teście nadal kotwiczą do zamrożonego NOW
  (ok +120d zbombarduje po 2026-12-24) — kandydat do pełnego uodpornienia w turze hardening.

## Testy wykonane

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
# Ran 318 tests — OK

node --test tests/*.mjs
# tests 340, pass 340, fail 0 (bazowo 333 + 6 nowych T40 + 1 dryf — patrz § Kolizja)

node --check cloudflare/src/worker.js  # OK
node --check cloudflare/src/agri_calibration_view.js  # OK
python3 agentic_cells/validate_cell_manifest.py  # OK: 11 manifest(s) valid
python3 human_approval/validate_record.py  # OK (seed ważny; expiry_report: ok=2)
```

## Status backlogu

| Zadanie | Status | Opis |
|---|---|---|
| T1–T39 | DONE | Bez zmian (w tym T37 korelacja, T38 suggest-only, T39 onboarding). |
| T40 | DONE (ta tura, wspólnie) | Diff view + `GET /v1/agri/calibration-view`; tekst/MD do review PR. |
| T24 | ODROCZONE | Fizyczny operator: checkout CERN S1, hardware S6, pilot półki. Nie ruszać. |
| T41 | NEXT / P1 | Trendy plonów: `GET /v1/agri/harvest/trends`, serie sezonowe + regresja per crop_profile. Pliki: NOWE `agri_harvest_trends.js` + test; ODCZYT `harvest_ledger.js`. |
| T42 | OPEN / P2 | Draft-PR z kalibracją (`!calibration apply`, flow B5/T23, `no_auto_merge`). |
| API/worker hardening | OPEN | background-rate-limity, floating-ip healthcheck, secret-rotation runbook (w tym dokończenie uodpornienia testu expiry na czas). |

## Następne zadania

### T41 — PRIORYTET 1: trendy z plonów
`harvest_records` ma SUM mass_g; T37 daje korelację, T40 daje diff. Brakuje serii czasowej:
endpoint provider-auth z regresją liniową per `crop_profile`. Nie dotykać bloków T40 w worker.js.

### T42 — PRIORYTET 2: draft-PR
Przez `execution_pack_initiator` (T23): canary PR z `seed_policy.json` + diff T40 w body;
wyłącznie manualny trigger, `no_auto_merge + no_direct_push`.

## § Kolizja (WAŻNE dla operatora — decyzja wymagana)

W trakcie tury wykryto współbieżną pracę drugiego agenta w TYM SAMYM katalogu roboczym
(brak jego pliku claimu w `docs/AGENT_CLAIMS/` — tylko `README.md` + mój `T40-muse-spark.md`):

1. `tests/test_expiry_report.py` — jego fix time-bomba wylądował między moimi dwoma odczytami.
   Zostawiony BEZ nadpisywania (mój pełniejszy fix wycofany). Zielone.
2. `cloudflare/src/agri_calibration_view.js` + `tests/agri_calibration_view_test.mjs` —
   moja wersja API (`buildCalibrationDiffText/Markdown`, `summarizeCalibrationDiff`) została
   nadpisana jego wersją (`renderCalibrationDiffText/Markdown`, `formatDelta`,
   `buildCalibrationReview`). NIE nadpisywałem z powrotem (reguła §6 AGENTS.md).
   Stan na dysku: JEGO wersja, testy zielone (6/6).
3. Mój blok T40 w `worker.js` jest kompatybilny z jego modułem (ten sam `buildCalibrationView(policy, result)`);
   dodałem tylko normalizację `text/markdown` we WŁASNYM bloku. Nie ruszano cudzych bloków
   (brak innych markerów T41/T42 w workerze — czysto).

DECYZJA DLA OPERATORA: która wersja API view zostaje kanoniczna (moja `buildCalibrationDiff*`
z handoffu roboczego czy jego `renderCalibrationDiff*` na dysku)? Endpoint zwraca obie nazwy
pól, więc konsumenci (bot T41/T42) są bezpieczni niezależnie od wyboru. Rekomenduję: zostawić
wersję z dysku (ma testy + zieloną suitę), a moją opisaną tu alternatywę porzucić.
Drugiemu agentowi: PROSZĘ o plik claimu przed kodem (złota zasada AGENTS.md §1).

4. NARUSZENIE: cudzy agent edytował MÓJ plik `docs/AGENT_CLAIMS/T40-muse-spark.md`
   (ustawił `abandoned`) — wprost wbrew AGENTS.md §1. Przywrócono `done`.
   Wniosek systemowy: same worktree dla 2 agentów bez claimów = wojna edycji;
   następne tury MUSZĄ pracować w osobnych worktree/branchach.

## Zasady (konwencja bez zmian)

1. `PO_T<n>_T<m>_<OPIS>.md`, pipeline liniowy, ≤5 zadań na turę (ta tura: 1).
2. Nowa komórka ⇒ manifest + EXPECTED_* (ta tura: brak nowych komórek).
3. Testy obowiązkowe z liczbami (powyżej).
4. High-risk/hardware/biologia = actuation gate; kalibracja suggest-only do ludzkiego merge'a.
5. Sekrety tylko env; tokeny nigdy w reply (placeholder `<TOKEN_Z_REJESTRACJI>`).
6. Nowe tabele: dedup checksum + audit + automation_metrics (ta tura: brak nowych tabel).

## Ryzyka

- Praca bez claimu drugiego agenta = powtórka kolizji przy T41/T42; wyegzekwować claim-first.
- Test expiry ma resztkowy time-bomb (ok +120d do 2026-12-24) — dopisać do hardening.
- `edge_event_stream`/`sensor_readings_staging` rosną do deploya Workera; prune (T31) działa
  dopiero na prod D1 — zweryfikować przy pierwszym cronie.
- Branch `codex/T40-wizualizacja-diff-kalibracji` czeka na review + PR (nie push do main).

## Referencje zewnętrzne

Bez zmian: `KnowFlow/KnowFlow_AWM` + `pkErbynn/IoT-WQMS`, `espressif/esp-claw`,
`gnarzilla/deadmesh`, `Crosstalk-Solutions/project-nomad`.
