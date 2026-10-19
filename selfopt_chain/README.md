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
