# CLAIM T53 — kilo-audit-fixes (domknięcie pętli roju wg audytu T48–T52)
- Zadanie: T53 (P0: kontekst między węzłami łańcucha — review widzi draft; accounting per-wywołanie bez podwójnego odejmowania + quota gate dla omniroute + tury Hermesa; privacy end-to-end z fail-closed + styl local; SecurityGate fail-closed przy zero artefaktów + redakcja klucza. P1: unikalne question_type decyzji + kumulacja kalibracji; dedup ewolucji między cyklami + przeplatanie źródeł; status degraded + retry/fallback węzła; charter word-boundary + pokrycie procdev)
- Status: abandoned-duplicate (2026-10-23: wykryto równoległą, PEŁNIEJSZĄ implementację audytu w PR #26 [T53-codex-recommendations, KrzyZuch] + PR #27 [T58-stable-evolution] — wspólny ledger, should_stop per węzeł, idempotentna kalibracja, sandbox OS, metryki, pilot. Zgodnie z AGENTS.md §6 nie pcham duplikatu; lokalne commity zostają jako referencja; ewentualne unikalne drobiazki przeniosę PO merge #26/#27 w osobnym PR. Decyzja: operator.)
- Start: 2026-10-23
- Branch/worktree: codex/T53-audit-fixes-kilo / .kilo/worktrees/kilo-selfopt
- Dotknięte pliki: WŁASNE (T48–T52): `selfopt_chain/{run_loop,orchestrator,swarm,engine,calibrate,evolver,hermes_worker,charter}.py` + testy selfopt; ADDytywnie `AGENTS.md` (odświeżenie statusów T40–T42 wg audytu — do review operatora); handoff + ten claim
- Zakaz: konfiguracja Kilo operatora (dyrektywa 2026-10-23: nie ruszać), worker.js/agri/robot (cudze claimy)
- Źródło: audyt operatora z 2026-10-23 (§5.1–5.8, §8 P0/P1)
