# CLAIM T43-preview-tests — muse-2
- Zadanie: T43 (blok preview już w kodzie) — naprawa spróchniałej asercji usage w teście
  T42 (fail 1/7: usage rozszerzono o `preview`, test sprawdza stary tekst) + pokrycie
  testowe `!calibration preview` (0 testów dotąd)
- Status: done
- Wynik: FIX 1 linijka `tests/execution_pack_calibration_test.mjs:176`
  (stale usage → akceptuje rozszerzony tekst z `preview`; fix przyjęty przez muse-4
  w handoffie PO_T43). Duplikat mojego rewrite'u `calibration_preview_test.mjs`
  wycofany (`git checkout`) — obowiązuje wersja muse-4 (4/4 zielone).
- Start: 2026-10-02
- Branch/worktree: codex/MUSE2-T43-preview-tests
- Dotknięte pliki: FIX 1 linijka `tests/execution_pack_calibration_test.mjs:176`;
  NOWY `tests/calibration_preview_test.mjs`; ODCZYT `execution_pack_initiator.js`
  (bloków T42/T43 w źródle NIE ruszam; `worker.js`, bot-handlery, testy muse-1 — nietknięte)
- Kolizje: brak claimu na ten obszar (muse-1 robi route-testy w osobnym pliku — nie dotykam)
