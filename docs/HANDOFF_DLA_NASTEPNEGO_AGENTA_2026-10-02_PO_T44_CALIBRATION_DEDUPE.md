# Handoff dla Następnego Agenta - po T44 - 2026-10-02 (dedupe kalibracji, muse-4)

## Kontekst wejściowy

Po PO_T43 (T1–T43 DONE). Znaleziono duplikację ~30 linii w moim obszarze:
`startCalibrationPack` (T42) i `previewCalibration` (T43) powielały pipeline
polityka → korelacja T37 → sugestia T38. Claim `T44-muse-4.md`, praca w IZOLOWANYM
worktree `.kilo/worktrees/muse-4`, branch `codex/T44-calibration-dedupe-muse-4`
(lekcja z edit-warów: zero pracy we współdzielonym drzewie).

## Co zrobiono (T44 — DONE)

- `execution_pack_initiator.js`: NOWY eksport `resolveCalibrationSuggestion(env, policyId, options)`
  (polityka z DB lub `options.policy`, korelacja lub `options.correlation`, progi z options;
  błędy jako Error z tekstem do reply). Obie funkcje go używają — zachowanie IDENTYCZNE
  (te same komunikaty, te same ścieżki no_suggestions).
- Testy: +1 test resolvera w `calibration_preview_test.mjs` (pipeline + 2 ścieżki błędów);
  naprawa spróchniałej asercji usage w `execution_pack_calibration_test.mjs:176`
  (niezależnie naprawiona też przez muse-2 we współdzielonym drzewie — zbieżność, nie konflikt).

## Testy (worktree muse-4, snapshot PO_T43)

```bash
python3 -m unittest discover -s tests -p 'test_*.py'  # Ran 318 — OK
node --test tests/*.mjs                               # 384 pass / 0 fail
node --check cloudflare/src/execution_pack_initiator.js  # OK
```

## Status / następne

- T44 DONE. Do review z operatorem (mały diff, mechaniczny).
- OSTRZEŻENIE: ten branch forkowany z PO_T43 — NIE zawiera późniejszych hardening/cell-guard;
  mergować REBASEM na aktualny main po zielonej suicie, nie direct.
- Wolne: brak (muse-1/muse-2 w toku na swoich claimach; T24+deploy u operatora).

## Ryzyka

- Brak. Izolowany worktree = zero kolizji w tej turze. Rekomendacja dla wszystkich:
  jeden agent = jeden worktree (AGENTS.md §4 już to mówi — egzekwować).
