# CLAIM T51 — kilo-roj-samokalibracja (pętla samodoskonalenia decyzji roju)
- Zadanie: T51 (domknięcie pętli uczenia roju: etykiety decyzji basala z feedbacku operatora i terenu (LoRa inbox) → kalibracja temperatur confidence (wzór basal-calibrate) → rdzeń decyzyjny używa dopasowanych temperatur; ewolucja strategii zarządzania generuje propozycje GEPA-style — suggest-only)
- Status: done (PR: codex/T51-roj-samokalibracja-kilo; weryfikacja: Python 447 OK, Node 378/0, manifesty 12 OK; szczegóły w docs/HANDOFF_DLA_NASTEPNEGO_AGENTA_2026-10-21_PO_T51_SAMOKALIBRACJA_CHARTER.md)
- Start: 2026-10-21
- Branch/worktree: codex/T51-roj-samokalibracja-kilo (stack na T50, PR #20 open) / .kilo/worktrees/kilo-selfopt
- Dotknięte pliki: NOWE `selfopt_chain/calibrate.py`, `tests/test_selfopt_calibrate.py`; WŁASNE (T48–T50): `selfopt_chain/swarm.py` (temperatury kalibrowane w BasalDecisionCore), `selfopt_chain/orchestrator.py` (feedback→labels, autokalibracja cyklu, CLI), `selfopt_chain/README.md`; handoff + ten claim
- Zakaz ruszania: worker.js, schema_migrations.js, agri_*, robot_* (T45–T47), hardening, cudze claimy; HYC/basal tylko ODCZYT (wzór decisions.jsonl + annotate + CALIBRATION format)
- Kierunek operatora (2026-10-21): „kontynuuj budowę automatyzacji roju" — rój sam się doskonali na własnych decyzjach (decisions.jsonl zbierane od T50)
