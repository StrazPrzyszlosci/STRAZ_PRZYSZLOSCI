# Handoff dla Następnego Agenta - po T43 - 2026-10-02 (podgląd kalibracji w bocie)

## Kontekst wejściowy

Po `PO_T42_DRAFT_PR_KALIBRACJI` (T1–T42 DONE). Wzięto wolne T43 (propozycja z handoffu PO_T42 §4):
claim `docs/AGENT_CLAIMS/T43-muse-4.md`, izolowany branch `codex/T43-calibration-preview-muse-4`.
Tożsamość: **muse-4** (dawniej muse-spark) — potwierdzona z operatorem; przyszłe claimy jako `*-muse-4.md`.

## Co zrobiono (muse-4)

### T43 — DONE (implementacja): `!calibration preview <policy_id>` (read-only)

- `cloudflare/src/execution_pack_initiator.js` (NOWA sekcja `T43 calibration preview START/END`;
  T42/T23 nietknięte; handler `handleCalibrationCommand` rozszerzony o gałąź preview + nowe usage):
  - `parseCalibrationPreviewCommand()` — ścisły parse (tylko `preview <policy>`, nic więcej);
  - `previewCalibration()` — polityka → korelacja T37 → sugestia T38 → tekst T40 (cap 1800);
    ZERO zapisów (brak packa, brak PR, brak HTTP), `no_suggestions` bez tworzenia czegokolwiek;
  - `formatCalibrationPreviewReply()` — podgląd + hint o `!calibration apply`.
- Komendy bota: BEZ ZMIAN w handlerach — istniejące case `calibration` (T42) już routują
  do `handleCalibrationCommand`, preview działa w Discordzie i Telegramie z automatu.
- `tests/calibration_preview_test.mjs` (NOWY, mój szkielet 4 testy: parse, read-only bez
  zapisów/HTTP, no_suggestions, handler+usage).

## Konwergencja z muse-2 (NIE nadpisywano — protokół §6)

Równoległy **muse-2** (claim `T43-preview-tests-muse-2.md`, branch `codex/MUSE2-T43-preview-tests`)
w tym samym drzewie, rozłącznie:
- naprawił 1 spróchniałą asercję usage w `tests/execution_pack_calibration_test.mjs:176`
  (usage rozszerzyłem o `preview` w implementacji; jego fix do mojego testu — przyjęty, nie ruszany);
- dopisał 2 testy do `tests/calibration_preview_test.mjs` (plik ma teraz 6/6 zielonych).
Oba pliki testowe od tego momentu WSPÓŁDZIELONE muse-4/muse-2 — dalsze edycje tylko w uzgodnieniu.

## Testy wykonane

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
# Ran 318 tests — OK

node --test tests/calibration_preview_test.mjs
# tests 6, pass 6, fail 0 (4 moje + 2 muse-2)

node --test tests/*.mjs (pełna)
# pass=385 fail=3 — WSZYSTKIE 3 CUDZE i w toku:
#   2× tests/agri_routes_test.mjs (muse-1, FIX cell-id-guard w toku — patrz niżej),
#   1× execution_pack_calibration_test.mjs:176 (naprawiane przez muse-2 w tej samej godzinie)

node --check cloudflare/src/execution_pack_initiator.js  # OK
python3 agentic_cells/validate_cell_manifest.py  # OK: 11 valid
python3 human_approval/validate_record.py  # OK
```

## Status backlogu

| Zadanie | Status | Opis |
|---|---|---|
| T1–T42 | DONE | Bez zmian. |
| T43 | DONE (impl. muse-4; testy współdzielone z muse-2) | Preview w bocie, zero zapisów. |
| agri-cell-id-guard (muse-1, in_progress) | W TOKU — NIE DOTYKAĆ | FIX krytyczny: kanoniczne `grow_cell_id` odrzucane przez `validateProviderId` → cała pętla agri 400. Pliki: `worker.js` (funkcja + swapy), `harvest_trends.js`, `agri_routes_test.mjs`. Tłumaczy 2 czerwone testy routów. |
| worker-route-tests (muse-1, in_progress) | W TOKU — NIE DOTYKAĆ | `tests/agri_routes_test.mjs` (nowy, untracked). |
| hardening | Prawie DONE | Guard wpięty w `scheduled()` + `/health` (7aa9c15); kod limitera/healthcheck czeka na commit autora; mój runbook zcommitowany. |
| T24 / Deploy | OPEN (operator) | Półka + `wrangler deploy`. PR #16 czeka na merge człowieka. |

## Następne zadania (propozycja)

1. Poczekać na muse-1 (cell-id guard to FIX P0 — odblokowuje ZIELONĄ suitę i całą pętlę agri).
2. Potem: review + merge PR #16, deploy, dane T24.
3. Wolne obszary bez claimów: brak — nie brać nowych zadań bez sprawdzenia `ls docs/AGENT_CLAIMS/`.

## Ryzyka

- Współdzielone drzewo: 3 agentów Muse (muse-1/muse-2/muse-4) + opencode-agent w jednym katalogu;
  claimy i tak powstają wstecz (po kodzie). Działa tylko dzięki markerom i nie-nadpisywaniu.
  Rekomendacja ponowiona: jeden agent = osobny worktree.
- Pełna suita mjs CZERWONA do czasu lądowania cell-id guard — nie pushować main przed zielenią.
- Branch T43 zawiera historię hardening (fork z tego brancha) — PR dopiero po zielonej suicie.

## Referencje zewnętrzne

Bez zmian.
