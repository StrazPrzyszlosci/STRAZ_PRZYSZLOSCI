# CLAIM T50 — kilo-swarm-basal (rój z rdzeniem decyzyjnym basal)
- Zadanie: T50 (warstwa roju w selfopt_chain: mały model decyzyjny w stylu basal podejmujący wiele decyzji przydziału zasobów — sprzęt (telefony, ESP, selfhost) do otwartych zapotrzebowań, wybór trybu wykonania (algorytm pod sprzęt vs model on-device vs łańcuch LLM), wybór strategii zarząwania cyklem (inspiracja cezar: kolejka, warianty, load-balance); LLM pozostaje warstwą strategii)
- Status: done (PR: codex/T50-swarm-basal-kilo; weryfikacja: Python 425 OK, Node 378/0, manifesty 12 OK; szczegóły w docs/HANDOFF_DLA_NASTEPNEGO_AGENTA_2026-10-21_PO_T50_ROJ_BASAL.md)
- Start: 2026-10-21
- Branch/worktree: codex/T50-swarm-basal-kilo (baza: origin/main 6b23e6f, zawiera T48+T49) / .kilo/worktrees/kilo-selfopt
- Dotknięte pliki: NOWE `selfopt_chain/swarm.py`, `tests/test_selfopt_swarm.py`; WŁASNE (T48/T49): `selfopt_chain/orchestrator.py` (integracja planu roju), `selfopt_chain/README.md`; handoff + ten claim
- Zakaz ruszania: worker.js, schema_migrations.js, agri_*, robot_* (T45–T47), hardening, cudze claimy; zewnętrzne repozytoria basal (HYC) i cezar tylko ODCZYT (adaptacja semantyki do standardu repo)
- Kierunek operatora (2026-10-21): rój wykorzystuje zasoby oceniane przez małe modele decyzyjne; na obwodach roju „ministerownicy"; przydział dostępnego sprzętu = decyzja modelu decyzyjnego (basal), LLM robi strategię; basal ma podejmować bardzo wiele decyzji (routing LLM to tylko jeden z domainów); rój musi mieć wiele strategii zarządzania (cezar); rój realizuje usługi dla ludności opisane w repo
- Semantyka basal zaadaptowana 1:1 z /media/magazyn/home/teresa/Dokumenty/HYC/basal (router.py: choice → probabilities, ranking, confidence, floor 0.55, defer → default, decisions.jsonl → kalibracja → GEPA)
