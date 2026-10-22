# selfopt_chain — łańcuch procesów samooptymalizujących się (T48)

Komórka realizuje kierunek operatora z 2026-10-19: **budować łańcuch procesów
samooptymalizujących się (GEPA, OpenEvolve, Abstral, LangGraph), wyłącznie na
darmowych modelach AI dostępnych przez API, z orkiestratorem/routerem, który
przydziela model o odpowiedniej jakości do odpowiedniego zadania — maksymalizacja
szybkości przy zachowaniu jakości.**

## Architektura

```
chain JSON ──► run_loop.py (orchestrator)
                 │
                 ├─► router.py ──► free_models.json (rejestr darmowych modeli)
                 │        polityka: privacy → wymagany tier → capabilities
                 │        → budżet RPM/RPD per run → min nadmiar tieru
                 │        → speed_class → zapas limitu. Deterministycznie.
                 │
                 ├─► graph.py (StateGraph w stylu LangGraph; API identyczne)
                 │        nodes zwracają częściowe dicty scalane do stanu;
                 │        conditional edges + limit kroków. Gdy zainstalowany
                 │        jest pakiet langgraph, adapters.py użyje prawdziwego.
                 │
                 ├─► engine.py: MockEngine (offline, deterministyczny) lub
                 │        FreeApiEngine (SELFOPT_NETWORK=1, tylko public,
                 │        sekrety z env: GEMINI_API_KEY, GROQ_API_KEY, ...)
                 │
                 ├─► tracer.py (Abstral-inspired): traces.jsonl → insights
                 │        (wąskie gardła, quality gap modeli, wolne kindy)
                 │
                 ├─► optimizers.py: GEPA-Pareto (prompty) + OpenEvolve
                 │        MAP-Elites (programy). Suggest-only.
                 │
                 └─► transport.py: koperty LoRa (semantyka mostu
                          Meshtastic↔MeshCore z remix-lora-bridge: P0/P1/P2,
                          dedup SHA-256, hop guard, TTL, retry, airtime,
                          chunking ≤200 B) → spool store-and-forward,
                          konsumowany przez zewnętrzny most (radio po stronie
                          mostu, pod bramką operatora).
```

## Użycie

```bash
python3 selfopt_chain/registry.py                       # walidacja rejestru
python3 selfopt_chain/run_loop.py --chain selfopt_chain/examples/chain_resource_triage.json
python3 selfopt_chain/run_loop.py --chain selfopt_chain/examples/chain_edge_advisory_lora.json
# tryb realny (wymaga sekretów w env i świadomej zgody na sieć):
SELFOPT_NETWORK=1 python3 selfopt_chain/run_loop.py --chain ... --engine free-api
```

## Rój i rdzeń decyzyjny basal (T50)

Wszystkie procesy repo działają jak **rój** realizujący usługi dla ludności.
Na obwodach roju decyduje **mały model decyzyjny w stylu basal** (tani, szybki;
semantyka zaadaptowana 1:1 z HYC/basal: choice → probabilities, ranking,
confidence, floor → defer → default, decisions.jsonl → kalibracja → GEPA):
**przydział dostępnego sprzętu do otwartych zapotrzebowań** (telefon →
obserwacja akwaponiki; selfhost → offline katalog części), **tryb wykonania**
(algorytm napisany pod sprzęt vs model on-device vs łańcuch LLM w chmurze),
**dobór zadań cyklu** i **strategia zarządzania** (inspiracja cezar:
speed_first / quality_first / load_balance / quota_preserve / energy_oze /
redundancy / queue_when_busy). LLM pozostaje warstwą strategii (procdev).

Każdy cykl orkiestratora zaczyna się planem roju (`swarm_plans/cycle_<n>.json`
+ `cycle_<n>_allocations.md`, suggest-only) i logiem decyzji
(`decisions.jsonl` — gotowy pod przyszłą kalibrację i pętlę GEPA).
Rdzeń wbudowany jest deterministyczny i offline; prawdziwy basal-serve
(Ollama) podpina się przez `SELFOPT_BASAL_URL`.

## Agent orkiestrator (rezydent, T49)

Uruchomiony orkiestrator **na żywo realizuje wizję repo**: automatycznie używa
darmowych modeli AI (router jakość↔szybkość + budżety) i rozwija procesy
zamiany dostępnych zasobów (np. elektrośmieci) w nowe zdolności systemu —
węzły sensoryczne, węzły selfhost, komunikację mesh, stanowiska bench —
które służą ludziom (żywność, energia, suwerenność cyfrowa).

Cykl: kill-switch → bramka quota (tylko free-api: `quota_snapshot` z
provider_quota_monitor musi być ok) → zbiór zadań (rekordy `resource_scout`,
inbox LoRa EDGE→HUB, bootstrap demo) → łańcuch AI per zasób →
**draft rozbudowy zdolności** w `scratch/selfopt/procdev_queue/` wg
`selfopt_chain/capability_map.json` (zasób → zdolność → PROJEKTY/komórki →
następny proces). Wszystko suggest-only: człowiek review'uje, nic nie jest
auto-zaaplikowane; budżety dobowe per model są persystowane.

```bash
# demonstracja offline (mock, jeden cykl):
python3 selfopt_chain/orchestrator.py --once
# daemon offline co 5 min:
python3 selfopt_chain/orchestrator.py --interval 300
# daemon na darmowych API (operator uzupełnia sekrety + quota_snapshot):
SELFOPT_NETWORK=1 GEMINI_API_KEY=... GROQ_API_KEY=... \
  python3 selfopt_chain/orchestrator.py --engine free-api --interval 300
# stop:
touch scratch/selfopt/KILL_SWITCH   # (albo SIGTERM)
```

Stan daemona (`scratch/selfopt/`): `orchestrator_state.json` (budżety, dedup),
`cycles/cycle_<n>.json` (receipty), `procdev_queue/*.md` (propozycje do review),
`runs/` (pełne ślady per zadanie), `stopped.json` (powód zatrzymania).

Artefakty runu (domyślnie `scratch/selfopt/<chain>_<ts>/`):
- `traces.jsonl` — pełny ślad wykonania (audit_trail),
- `run_receipt.json` — status, routing, budżety quota, `auto_applied: false`,
- `optimization_proposals.md` — propozycje (Abstral/GEPA/MAP-Elites) do review,
- `lora_spool/` — kolejka kopert do mostu (queue.jsonl + outbox/).

## Silniki zewnętrzne (opcjonalne)

Rdzeń działa bez zależności. Pakiety dostrajają metody, gdy są zainstalowane:
`pip install langgraph gepa openevolve` (wykrywanie w `adapters.py`; wybór
silnika zapisany w run_receipt). Abstral to metoda (paper), w pełni pokryta
natywnie przez `tracer.extract_insights`.

## Zasady bezpieczeństwa

- **Zero sieci domyślnie** — `FreeApiEngine` odmawia bez `SELFOPT_NETWORK=1`.
- Sekrety wyłącznie w zmiennych środowiskowych; rejestr przechowuje nazwy.
- Prywatne dane nigdy na publiczne API (privacy=private → tylko local_private).
- Limity darmowych tierów są seedami do weryfikacji przez operatora
  (`limits_verified=false`; patrz provider_quota_monitor).
- Optymalizacje są **suggest-only**: nic nie jest auto-zaaplikowane (konwencja T38);
  merge proponowanych zmian wyłącznie przez PR po review człowieka.
- Transport LoRa to staging (spool); nadawanie w eter należy do mostu
  i pozostaje pod human control point operatora.
