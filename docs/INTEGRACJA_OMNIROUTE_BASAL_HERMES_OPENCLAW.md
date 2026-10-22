# Integracja: OmniRoute + basal-serve + Hermes/OpenClaw (T52)

Architektura wg dyrektyw operatora (2026-10-22): **basal (mały model decyzyjny)
decyduje** (zadania, strategie, równoległość, jakość), **OmniRoute przydziela
darmowe LLM** (warstwa wykonawcza, aliasy `auto*`), **LLM wykonują pracę
intelektualną**, **Hermes/OpenClaw headless** dają narzędzia do pracy nad
repo/kodem OSS, **GEPA/OpenEvolve/ABSTRAL** optymalizują, wszystko w
**izolacji na komputerze operatora** i w granicach `charter.json`.

## Komponenty

| Rola | Komponent | Stan na tej maszynie |
|---|---|---|
| Decyzje | `selfopt_chain/swarm.py` (basal core; `SELFOPT_BASAL_URL` → prawdziwy basal-serve, fallback wbudowany) | rdzeń wbudowany działa; basal-serve opcjonalny |
| Gateway darmowych LLM | OmniRoute (375 providerów, 150+ free; upstream: github.com/cheaper-inference/OmniRoute) | **do instalacji przez operatora** |
| Wykonanie LLM | `selfopt_chain/omniroute.py` (FreeOnlyPolicy: walidacja aliasu przed + realnego modelu po odpowiedzi) | adapter gotowy |
| Worker headless | Hermes CLI (`--oneshot --query-file --format stream-json --safe-mode --worktree --in DIR --run-budget --max-turns`) | **zainstalowany** (`~/.local/bin/hermes`) |
| Worker headless (alt.) | OpenClaw | do instalacji; adapter沿用 hermes_worker (ścieżka w roadmapie) |
| Samoewolucja repo | `selfopt_chain/evolver.py` (`--evolve`): handoffy/proposals/celowniki → PR-drafty w `evolution_queue/` | działa offline (mock-lane) |

## Uzbrojenie (krok po kroku)

```bash
# 1) OmniRoute (upstream install wg docs projektu) + włącz STRICT_ZERO_COST
#    (domyślnie WYŁĄCZONY upstream — nasz FreeOnlyPolicy egzekwuje zero-cost
#    niezależnie, walidując realny model po każdej odpowiedzi)
omniroute  # wystartować gateway — dashboard/API wg upstream (default: http://localhost:20128, API /v1)

# 2) basal-serve (opcjonalnie, najnowszy basal przez Ollama):
basal-serve --model <basal-latest> --mode ollama --ollama-model <basal-tag> --port 8000

# 3) Daemon roju (offline, ewolucja repo w trybie mock):
python3 selfopt_chain/orchestrator.py --evolve --interval 300

# 4) Daemon UZBROJONY (realne darmowe LLM + decyzje basal-serve + Hermes headless):
export SELFOPT_NETWORK=1            # zgoda na sieć (tylko publiczne dane)
export SELFOPT_OMNIROUTE_URL=http://127.0.0.1:20128/v1
export SELFOPT_BASAL_URL=http://127.0.0.1:8000
export SELFOPT_HERMES=1             # zezwól workerom Hermes na run
python3 selfopt_chain/orchestrator.py --engine omniroute --evolve --interval 300

# 5) Stop: touch scratch/selfopt/KILL_SWITCH (lub SIGTERM)
```

## Zmienne środowiskowe

| Zmienna | Domyślnie | Znaczenie |
|---|---|---|
| `SELFOPT_NETWORK` | (puste) | `1` = zgoda na realne wywołania API |
| `SELFOPT_OMNIROUTE_URL` | `http://127.0.0.1:20128/v1` | adres gatewayu OmniRoute |
| `SELFOPT_BASAL_URL` | (puste) | adres basal-serve (decyzje remote z fallbackiem) |
| `SELFOPT_HERMES` | (puste) | `1` = worker Hermes może wykonywać run |
| sekrety providerów | (env operatora) | NIGDY nie przechodzą do env workerów (whitelistka scrub) |

## Izolacja na komputerze operatora

1. Każdy run workera w osobnym sandboxu: `scratch/selfopt/hermes_sandbox/<id>`
   + flagi natywne Hermes: `--safe-mode`, `--worktree`, `--in <sandbox>`,
   `--run-budget`, `--max-turns`.
2. Środowisko workerów scrubowane (whitelistka `PATH/HOME/...`) — zero
   sekretów API w env workera.
3. **Kwarantanna**: wszystko co worker wyprodukuje →
   `scratch/selfopt/hermes_quarantine/<id>/`; do repo wchodzi wyłącznie przez
   SecurityGate (`hermes_worker.SecurityGate`: sekrety, destrukcja, exfiltracja
   env, physical_actuation, network w testach, licencje copyleft → review)
   i PR człowieka (`no_auto_merge`, `no_direct_push`).

## FREE-ONLY (STRICT zero-cost)

- alias `auto*` lub model z `free_models.json` — dozwolone; cokolwiek innego
  odrzucone PRZED wywołaniem;
- **realny model z odpowiedzi OmniRoute weryfikowany PO** — naruszenie =
  porażka zadania (`free_only_violation`), nigdy płatny fallback;
- brak darmowego modelu = kolejka/odroczenie/lokalnie — nie eskalacja kosztu.

## Równoległość subagentów (basal decyduje)

- `--subagent-mode auto` (default): basal wybiera `single` (oszczędnie),
  `wide` (N zadań równolegle na różne modele — duży backlog) lub
  `deep` (szybki słaby model pisze → duży model sprawdza — zadania krytyczne;
  dyrektywa operatora z 2026-10-22).
