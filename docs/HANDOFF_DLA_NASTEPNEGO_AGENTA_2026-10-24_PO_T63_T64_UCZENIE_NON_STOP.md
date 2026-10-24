# Handoff — po T63/T64 (uczenie z wyników + pełne uruchomienie non-stop) — 2026-10-24

## T63 — metryki skuteczności (DONE)

- `metrics.py` rozszerzony o stronę ewolucji: **zwalidowane artefakty/100 wywołań
  producenta**, udział pozytywnych review, duplikaty prób (targets z attempts>1),
  avg latencja producenta, opublikowane propozycje, wywołania na opublikowaną
  propozycję + **jawna lista missing_data** (braki ujawniane, nie maskowane).
- Odbiór w `tests/test_selfopt_learning.py` (7 testów): etykieta zmienia
  kalibrację TYLKO swojego typu decyzji; wyostrożona kalibracja czyni następną
  decyzję pewną; **idempotencja fitu** (ponowne przetworzenie tych samych etykiet
  = ten sam wynik); restart zachowuje CALIBRATION; provenance etykiet
  (append_label wymaga istniejącej decyzji); puste stany = jawne None, nie zero.
- Brak `labels.jsonl` = jawnie raportowany (blocked: `missing_runtime:labels.jsonl`
  widoczny w batchach). Transport ≠ jakość decyzji (utrzymane z T59/T60).

## T64 — pełne uruchomienie non-stop (DONE, usługi aktywne)

Trwałe jednostki systemd **user** (pliki w `tools/systemd/` w repo + aktywne w
`~/.config/systemd/user/`), `loginctl enable-linger` = przeżywają reboot/wylogowanie:

| Jednostka | Rola | Stan (2026-10-24 04:51) |
|---|---|---|
| `straz-ollama.service` | inferencja lokalna pico | active (running), enabled |
| `straz-basal.service` | decydent :8000 (basal-omni-pico, kalibracja HYC) | active, enabled, Wants=ollama |
| `straz-omniroute.service` | gateway darmowych LLM :20128, izolowany 127.0.0.1 | active, enabled |
| `straz-swarm-evolution.service` | **daemon ewolucji non-stop** | active (running), enabled, Wants=basal+omniroute+ollama |

Właściwości daemona roju:
- **Watchdog przez bounded run**: `--max-seconds 3000` + `Restart=always`
  (RestartSec=60, StartLimitBurst=5/10min = ograniczony backoff) — każda porcja
  na odebranym commicie, po rotacji wznawia z tego samego stanu i **współdzielonego
  ledgera** (quota_ledger w codex-swarm-recommendations — niezerowany).
- **Kill switch**: `ExecStartPre` nie pozwala wystartować, gdy
  `scratch/selfopt/continuous-live/KILL_SWITCH` istnieje; usunięcie + restart = wznowienie.
- **Pojedyncza instancja** na stanie (systemd) — zero duplikatów procesów.
- Stan: `scratch/selfopt/continuous-live/` (continuous-live; świeży — pilotowa
  historia zachowana w t60-live).
- `--executor auto` (basal decyduje; override usunięty z usługi — był tylko
  narzędziem pilota), `--turns 16` (hermes potrzebuje więcej tur dla zadań
  proposal), `--pause 120`.

## Soak (obserwacja live, 22+ min)

- 6+ batchy: strategia LLM **co batch** (`llm:cohere/north-mini-code:free`),
  pre-check akceptacji działa (daemon_exit → `acceptance_already_passing`,
  nie reproducowany), pętla prób z backoff działa, daemon active cały czas.
- Uczciwie: taski handoffowe (non-patch) przy hermes/16-turach wciąż częściej
  kończą `needs_fixes` („ran out of steps") niż produktem — to jest dokładnie
  pętla, którą T62 pokazała jako zbieżną dla zadań patch (PR #32). Proponowane
  dalsze kroki: (a) T61 — kwalifikacja większej puli darmowych modeli do ról
  (produktywniejszy hermes), (b) przypisanie handoff-tasków do direct_patch
  gdy mają kontrakty, (c) etykiety operatora (labels.jsonl) dla kalibracji.
- **Resumption nie dubluje**: store TERMINAL (ready) i pre-check akceptacji
  gwarantują brak reprodukcji gotowych wersji (potwierdzone: daemon_exit
  pomijany we wszystkich batchach continuous).

## Pełny stan roju (2026-10-24)

- PR #31 (T60) i PR #32 (ewolucja: deferred_selection, autorstwa roju) — czekają
  na Twój review/merge. PR #32 to pełny cykl T62: Cohere wytworzył, walidacja
  izolowana (baseline-FAIL/candidate-PASS/regresja-558-PASS), recenzent NVIDIA
  pass, hash zweryfikowany, draft PR.
- Regresja: **565 Python OK / 378 JS pass / 12 manifestów / approvals ważne**.
- Claimy: T60 done, T62 done (w claimie T60-glm53), T63 done, T64 done.
- Następne wg Twojego handoffu: T61 (kwalifikacja puli darmowych modeli do ról,
  11 modeli czeka), T62-cele kolejne z evolution_targets, etykiety (kalibracja
  czeka na prawdziwe dane), human review PR #31/#32.

## Sterowanie (operator)

```bash
systemctl --user status straz-swarm-evolution   # stan daemona
journalctl --user -u straz-swarm-evolution -f  # log na żywo
touch .kilo/worktrees/glm53-swarm/scratch/selfopt/continuous-live/KILL_SWITCH  # stop
systemctl --user stop straz-swarm-evolution    # twarde zatrzymanie
# wznowienie: rm KILL_SWITCH && systemctl --user start straz-swarm-evolution
python3 selfopt_chain/metrics.py --state-dir scratch/selfopt/continuous-live  # metryki
```
