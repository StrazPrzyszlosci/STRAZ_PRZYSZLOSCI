# Handoff dla Następnego Agenta — po T41 / guard / hardening — 2026-10-02 (muse-1)

## Kontekst wejściowy

Prace poza handoffem (decyzja operatora: analiza wolna). Punkt startu: handoff
`PO_T37_T39` (T1–T39 DONE). W międzyczasie inni agenci domknęli T40/T42/T43
i hardening tła. Ten dokument scala wkład muse-1 z 2026-10-02.

## Co zrobiono (muse-1, 4 commity + koordynacja)

1. **`AGENTS.md` + `docs/AGENT_CLAIMS/`** — protokół anty-kolizyjny (claim-first,
   rozłączne obszary, markery bloków). Działa: wykryto kolizję T40 przed kodem,
   zero nadpisań od tego momentu. Dopisano lekcję edit-war T40 (§6).
2. **T41 trendy plonów** (`agri_harvest_trends.js`, 7 testów): serie sezonowe
   SUM(mass_g) + regresja liniowa per crop_profile, `GET /v1/agri/harvest/trends`
   (provider-auth, read-only, okno względem najnowszych danych — bez time-bombów).
3. **FIX krytyczny: `ensureAgriCellAllowed`** (worker.js) — kanoniczne
   grow_cell_id nie przechodziły `validateProviderId` (brak segmentu env), więc
   CAŁA pętla agri + rejestracja komórek zwracały 400. Strict-ID bez zmian
   (gating env + `ForbiddenError` nietknięte); fallback tylko dla komórek
   z `agri_grow_policies`. Ograniczenie: wspólne D1 = brak izolacji env komórek.
4. **Testy fetch-level routów** (`tests/agri_routes_test.mjs`, 9 testów) —
   pierwszy test routingu Workera (wcześniej 0 pokrycia; `node --check` nie
   łapie ReferenceError). Trendy/korelacja/calibration-view/rejestracja/403.
5. **CI: bramka testów w `deploy_worker.yml`** — deploy leciał bez testów;
   teraz job `test` (Python + mjs + `node --check`) przed migracjami D1.
6. **`docs/RUNBOOK_ROTACJI_SEKRETOW.md`** — inwentaryzacja 9 sekretów z kodu
   + procedura make-before-break + tryb awaryjny + dziennik.
7. **Fix resztkowego time-bomba** `test_main_exit_codes` (ok +120d → real now).
8. Format trunk `agri_harvest_trends.js` (czyste formatowanie).

## Testy (stan na ten handoff)

```bash
python3 -m unittest discover -s tests -p 'test_*.py'  # Ran 318 — OK
node --test tests/*.mjs                               # 378 pass / 0 fail
node --check cloudflare/src/*.js                      # OK wszystkie
python3 agentic_cells/validate_cell_manifest.py       # 11 valid
python3 human_approval/validate_record.py             # OK (expiry za 89 dni)
```

## Zweryfikowane, nie ruszane (analiza)

- Bot NIGDY nie merge'uje (tylko komentarze + PATCH close) — w kodzie.
- Spór API T40 rozstrzygnięty w kodzie (worker normalizuje text/markdown).
- `/v1/ws/events` ma token-auth (bez format-gate — działał cały czas).
- Dwie maszynerie migracji (dir + rejestr runtime) — worker aplikuje rejestr
  przy starcie z retry; prod dostaje tabele agri. Dług, działa.
- Komendy bota fail-safe (try/catch → reply + usage).
- Duplikat `fetchTelegramFileAsBase64` już skonsolidowany (Z71 done).
- Hermes = deskryptory zadań pod model-routing; quota snapshot ALL STALE
  (2026-07-07) → łańcuch AI zablokowany; cron dla Hermesa bez sensu przed
  odblokowaniem (decyzja operatora, nie kod).

## Backlog: nie ma wolnych zadań kodowych

T40–T43 DONE, hardening (limiter/healthcheck/guard/runbook/CI/secrets-doc)
DONE. T24 odroczone (fizyka). Zostały wyłącznie decyzje operatorskie (§ niżej).

## Decyzje operatora (kolejność)

1. **Rozdziel D1 per env** (wrangler.toml: jeden database_id wszędzie) —
   demo/prod mieszają metryki; gating komórek bez tego pozorny.
2. **Odśwież quota_snapshot** (4 wpisy stale od 07-07) — inaczej łańcuch AI stoi.
3. **Sprawdź cron na prod** (`[triggers]` tylko top-level — czy scheduled()
   w ogóle odpala się w env prod?).
4. **Seed approvals** (expiry 31.12.2026, ~89 dni) — renewal + minutnik.
5. **PR gałęzi → main** (review człowieka; bot nie merge'uje).
6. **Jeden agent = osobny worktree** (współdzielony checkout to prochownia).
7. Opcjonalnie: try/catch per krok w `scheduled()` (blok hardening — ich agent),
   mismatch polityka/komórka w evaluate, komendy operatorskie w /start.

## Zasady bez zmian

Claim-first (`docs/AGENT_CLAIMS/`), cudze bloki/claimy nietykalne, testy
z liczbami, actuation gate, sekrety tylko env, kalibracja suggest-only.
