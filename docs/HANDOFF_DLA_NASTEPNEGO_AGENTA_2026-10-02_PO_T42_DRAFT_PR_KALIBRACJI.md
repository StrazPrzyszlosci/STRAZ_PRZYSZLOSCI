# Handoff dla Następnego Agenta - po T42 - 2026-10-02 (draft-PR z kalibracją)

## Kontekst wejściowy

Przeczytano: `docs/HANDOFF_DLA_NASTEPNEGO_AGENTA_2026-10-02_PO_T41_AGRI_TRENDS.md`
(T1–T41 DONE, T24 odroczone). T42 było wolne (brak claimu) — zarezerwowano
`docs/AGENT_CLAIMS/T42-muse-spark.md` przed kodem, zgodnie z `AGENTS.md` §1.
Równolegle inny agent domyka hardening (rate-limity tła, floating-IP) — inne pliki, brak kolizji.

## Co zrobiono

### T42 — DONE: automatyczny draft-PR z kalibracją (manualny trigger, suggest-only)

- `cloudflare/src/execution_pack_initiator.js` (sekcja `T42 calibration draft-PR START/END`,
  reszta pliku NIETKNIĘTA; jedna wstecznie zgodna linijka: opcjonalny `request.title` w PR):
  - `parseCalibrationApplyCommand()` — `!calibration apply <policy_id> [reviewer]`;
  - `calibrationPackId()` — id `calibration-<polityka>-<stamp>` ważne dla ledgera (≤120 znaków);
  - `buildCalibrationSeedPolicyPatch()` — czysty patch proponowanych pasm do `seed_policy.json`
    (do ręcznego naniesienia, zero auto-apply);
  - `startCalibrationPack()` — polityka → korelacja T37 → sugestia T38 → wpis `started`
    w `execution_packs` + DRAFT PR (dry_run / GitHub `draft:true`); przy pustej sugestii zwraca
    `no_suggestions` BEZ tworzenia packa i PR;
  - `formatCalibrationApplyReply()` / `handleCalibrationCommand()` — reply PL z bramkami,
    błędy jako tekst (bot nigdy nie rzuca).
- Komendy bota (tylko NOWE case/branch, cudzych nie ruszano):
  - Discord `discord_api_handler.js`: `calibration` / `calibration_apply` → `handleCalibrationCommand`;
  - Telegram `telegram_issues.js`: branch `calibration` ze statusem `command_calibration_apply`.
- `tests/execution_pack_calibration_test.mjs` — 7 testów: parse, format pack_id, patch builder,
  dry_run bez HTTP i bez sekretów w reply, GitHub draftpayload (`draft:true`, brak `/merge`,
  `seed_policy.json` + `no_auto_merge` w body), `no_suggestions`, nieznana polityka/usage.

## Testy wykonane

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
# Ran 318 tests — OK

node --test tests/*.mjs
# pass=354 fail=0 (było 347: +7 T42)

node --check cloudflare/src/{execution_pack_initiator,discord_api_handler,telegram_issues}.js  # OK
python3 agentic_cells/validate_cell_manifest.py  # OK: 11 manifest(s) valid
python3 human_approval/validate_record.py  # OK
```

Commity tej tury (małe, często): initiator → komendy bota → testy → docs.

## Status backlogu

| Zadanie | Status | Opis |
|---|---|---|
| T1–T42 | DONE | Pętla uczenia kompletna: T37 korelacja → T38 sugestia → T40 diff → T41 trendy → T42 draft-PR. |
| T24 | ODROCZONE | Fizyczny operator (CERN S1, hardware S6, pilot półki). Nie ruszać. |
| API/worker hardening | W TOKU (inny agent) | Secret-rotation DONE, expiry DONE; otwarte: background-rate-limity, floating-IP healthcheck. |
| Deploy Workera | OPEN (operator) | `wrangler deploy` + cron retencji; ROW_NUMBER pruning do weryfikacji na prod D1. |

## Następne zadania

1. **Hardening**: dokończyć rate-limity tła + floating-IP healthcheck (obszar innego agenta — nie wchodzić bez claimu).
2. **Deploy**: po zielonym main operator robi `wrangler deploy`, pierwszy cron, realne `automation_metrics`.
3. **Dane (T24)**: pierwszy pilot półki → 2–3 miesiące telemetrii+plonów → T37/T41/T38/T42 na żywych danych.
4. Ewentualne T43+: komenda `!calibration` z podglądem diff T40 w bocie (osobny claim).

## Zasady (konwencja bez zmian)

1. Handoff liniowy, ≤5 zadań na turę (ta tura: 1).
2. Claim-first; cudze pliki i bloki nietykalne (tu: dotknięto wyłącznie obszaru T42 z `AGENTS.md` §2).
3. Testy z liczbami (powyżej). 4. Actuation gate; kalibracja suggest-only do ludzkiego merge'a.
5. Sekrety tylko env; tokeny nigdy w reply (test asercjonuje brak wycieku).

## Ryzyka

- Draft-PR bez tokenu GitHub kończy się placeholderem (`no_token`) — operator/offline job
  tworzy PR ręcznie; body z patchem jest w ledgerze i reply.
- `execution_packs` rośnie o wpisy `calibration-*` — webhook T30 syncuje ich statusy jak zwykłe packi.
- Gałąź `codex/T40-wizualizacja-diff-kalibracji` hostuje commity T40+T41+T42+hardening —
  przed PR do main scalić świadomie z operatorem (osobne PR-y per obszar albo jeden squashed).

## Referencje zewnętrzne

Bez zmian: `KnowFlow/KnowFlow_AWM` + `pkErbynn/IoT-WQMS`, `espressif/esp-claw`,
`gnarzilla/deadmesh`, `Crosstalk-Solutions/project-nomad`.
