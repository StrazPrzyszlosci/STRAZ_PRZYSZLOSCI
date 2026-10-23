# Rejestr rezerwacji zadań (claims) — jeden plik na zadanie na agenta.

Zasady w `AGENTS.md` §1. Nie edytuj cudzych plików.
Wzorzec nazwy: `T<NN>-<twoja-nazwa>.md` (np. `T40-moj-agent.md`).

T40–T42 ukończone. Aktualne rezerwacje sprawdzaj poleceniem `python3 tools/agent_claims.py check --all-worktrees`.

Nowa rezerwacja: `python3 tools/agent_claims.py reserve --task TNN --owner nazwa --writes src/nowy_modul.py tests/test_nowy_modul.py`. Rezerwacja jest atomowa pomiędzy worktree; nie edytuj cudzego claimu. Starsze claimy bez metadanych zakresu są sprawdzane po numerze zadania; dodanie zakresu należy do ich właścicieli.
Odroczone (nie ruszać): T24.
