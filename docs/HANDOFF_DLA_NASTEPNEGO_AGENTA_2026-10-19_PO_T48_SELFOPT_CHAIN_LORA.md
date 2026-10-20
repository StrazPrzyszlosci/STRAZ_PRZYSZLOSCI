# Handoff dla Następnego Agenta — po T48 (selfopt_chain) — 2026-10-19

## Kontekst wejściowy

Przeczytano: `AGENTS.md`, `AGENT_CLAIMS/README.md`, najnowsze handoffy
(`WERYFIKACJA_JAKOSCI_PO_T43`, `PO_T43_CALIBRATION_PREVIEW`), claimy w
`docs/AGENT_CLAIMS/` (T43–T47 zajęte → wzięto NOWE zadanie T48).
Kierunek od operatora (2026-10-19, dwie wiadomości):

1. „Cały zamysł tego repo: budować łańcuch procesów samooptymalizujących się
   za pomocą GEPA, OpenEvolve, Abstral, LangGraph — zacznij to robić."
2. „Łańcuch ma korzystać z darmowych modeli AI przez API i mieć
   orkiestrator/router, który przydziela modele o odpowiedniej jakości do
   odpowiednich zadań, żeby zwiększyć szybkość przy zachowaniu jakości."
3. Klasy łączności LoRa wskazane przez operatora (read-only):
   `/media/magazyn/home/teresa/Dokumenty/HYC/remix-lora-bridge`
   (most Meshtastic↔MeshCore, Kotlin) oraz `/home/krzysiek/Dokumenty/MESHTASTIC ROUTER`
   (Adaptive Relay, symulator + port firmware 2.8.2).

Claim: `docs/AGENT_CLAIMS/T48-kilo-selfopt-router.md` (in_progress → done).
Branch: `codex/T48-selfopt-chain-kilo` (worktree `.kilo/worktrees/kilo-selfopt`),
zrebasowany na `origin/main` po merge PR #16/#17. Zero edycji plików innych claimów;
zero zmian w worker.js / schema_migrations.js / agri_* / robot_* / hardening.

## Co zrobiono — NOWA komórka `selfopt_chain` (T48)

Nowy, samodzielny moduł Python (stdlib-only, offline, suggest-only) realizujący
pętlę samooptymalizacji w architekturze z README §4 i
docs/GRAF_LANCUCHA_AUTOMATYZACJI.md (FAZA 5: Ewolucja):

- `selfopt_chain/free_models.json` + `registry.py` — rejestr 13 darmowych
  modeli przez API (providerzy zgodni z
  `agent_runtime_plans/hermes_pilot/provider_matrix.json`: google_ai_studio_free,
  nvidia_nim_free, selfhost_recovered_node + groq/cerebras/mistral/openrouter/
  github_models free). Walidator odrzuca płatne klasy kosztu, wycieki sekretów
  (secret_env musi być UPPER_SNAKE_CASE nazwą zmiennej, nie wartością), złe
  privacy i limity bez notatek. Limity RPM/RPD = SEEDY (`limits_verified=false`)
  do weryfikacji operatora — spójnie z provider_quota_monitor.
- `selfopt_chain/router.py` — orkiestrator/router: privacy → wymagany tier dla
  kind (classify=1 … vision_extract=5) → capabilities → budżet RPM/RPD per run
  (QuotaLedger) → blokada providera ze quota_snapshot (stale/missing) →
  sortowanie: zadania publiczne preferują hosted free API, potem minimalny
  nadmiar tieru (nie marnujemy mocnych modeli), potem speed_class, potem zapas
  RPD. W pełni deterministyczne; każda decyzja z audytem (chosen,
  alternatives, rejected, blocked_reason).
- `selfopt_chain/graph.py` — StateGraph w stylu LangGraph (identyczne API:
  add_node/add_edge/add_conditional_edges/set_entry_point/compile/invoke),
  z limitem kroków. `adapters.py` wykrywa prawdziwe pakiety
  (langgraph/gepa/openevolve) — bez nich biega implementacja wbudowana;
  wybór silnika zapisany w run_receipt.
- `selfopt_chain/engine.py` — MockEngine (deterministyczny offline; classify
  rozpoznaje ALARM wg słów kluczowych mostu) + FreeApiEngine: **zero sieci
  domyślnie** ( SELFOPT_NETWORK=1 ), tylko zadania publiczne, sekrety z env,
  style openai_chat/google_gemini, timeouty, tokeny nigdy w logach.
- `selfopt_chain/tracer.py` — pełny ślad wykonania (JSONL) + summarize +
  extract_insights w duchu Abstral (wąskie gardło węzła wg udziału latencji,
  quality-gap modelu wg ok_rate, wolne kindy) → propozycje patchy skillów.
- `selfopt_chain/optimizers.py` — GEPA-Pareto (front dominacji
  quality/latency/cost + refleksja scalająca feedback) i OpenEvolve MAP-Elites
  (nisza (kind, complexity), akceptacja tylko przy przewadze fitness).
  Oba **suggest-only** (`auto_apply=false`, konwencja T38).
- `selfopt_chain/transport.py` — klasy łączności LoRa zaadaptowane z
  remix-lora-bridge: priorytety P0/P1/P2 (słowa kluczowe !SOS/!ALERT/...),
  deduplicationHash SHA-256→16hex (ten sam wzór co BridgeEngine), hop-guard
  ([HUB→EDGE]/[EDGE→HUB]), TTL 30 min, maxRetries P0=5/3, stany
  QUEUED/TRANSMITTING/DELIVERED/EXPIRED/FAILED, airtime EU868
  (0.35s + 14ms/bajt), chunking ≤200 B safe-UTF-8, tx_plan (okno TX 5s,
  guard 0.8s, P0 pierwsze). **Spool store-and-forward** (queue.jsonl +
  outbox/<id>.json) = interfejs dla mostu; komórka NIGDY nie nadaje w eter.
  Zgodnie z instrukcją adaptive-relay: zero zmian protokołu po stronie mesh.
- `selfopt_chain/run_loop.py` — CLI orkiestratora: ładuje i waliduje łańcuch
  (pipeline lub graf z conditional), routuje zadania, zbiera ślady, emituje
  `traces.jsonl`, `run_receipt.json` (auto_applied=false, budżety quota,
  routing, status), `optimization_proposals.md` (insights + GEPA + MAP-Elites
  do review człowieka) oraz `lora_spool/` dla węzłów dispatch.
- Przykłady: `examples/chain_resource_triage.json` (triage zasobów) i
  `examples/chain_edge_advisory_lora.json` (telemetria edge → classify ALARM
  → escalate → dispatch P1 do mostu — wzorzec deadmesh).

## Weryfikacja (liczby obowiązkowe)

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
# Ran 378 tests — OK  ✅ (baza 318 + 60 nowych: test_selfopt_chain.py + test_selfopt_transport.py)
node --test tests/*.mjs
# tests 378, pass 378, fail 0  ✅ (JS nietknięty; stary fail T42 naprawiony w PR #17)
python3 agentic_cells/validate_cell_manifest.py   # OK: 12 manifest(s) valid  ✅
python3 selfopt_chain/registry.py                 # OK: 13 darmowych modeli  ✅
python3 human_approval/validate_record.py        # OK; expiry 2026-12-31 (72 dni, brak ostrzeżenia)  ✅
```

Nowa komórka ⇒ manifest w `agentic_cells/seed_cell_manifests.json` +
`EXPECTED_CELL_IDS`/`EXPECTED_DIRS` zaktualizowane (konwencja §5.2).
Zero nowych tabel D1 (§5.6 nie dotyczy — brak zmian w workerze).

## Status backlogu

| Zadanie | Status | Uwagi |
|---|---|---|
| T48 selfopt_chain | DONE (PR czeka na review) | Suggest-only; merge tylko przez PR. |
| T43–T47 | zajęte (muse-2/muse-4/kilo-robotyka) | nie ruszać |
| Hardening | wg claimów muse-spark/opencode | nie ruszać |

## Następne zadania (propozycje T49+, ≤5 na turę)

1. **T49 consumer spoola w moście**: drobny watcher w remix-lora-bridge
   (Kotlin, BridgeEngine) czytający `lora_spool/outbox/*.json` →
   sendTextMessage przez istniejący RadioScheduler (radio nadal pod bramką
   operatora; tamten projekt poza tym repo — koordynacja z operatorem).
2. **T50 smoke free-api na sekretach operatora**: pierwszy realny run
   `--engine free-api` (SELFOPT_NETWORK=1 + GEMINI_API_KEY/GROQ_API_KEY),
   uzupełnienie `limits_verified` w rejestrze i quota_snapshot (provider_quota_monitor).
3. **T51 loop domknięcia**: odpowiedzi EDGE (inbox spool) jako nowe zadania
   łańcucha (samodoskonalenie na danych z pola) + propozycje GEPA/MAP-Elites
   z `optimization_proposals.md` jako draft-PR przez `execution_pack_initiator`.
4. **T52 aggregacja**: `automation_metrics` wpis dla selfopt_chain
   (insights/run, routing mix tierów) — gdy będzie >0 realnych runów.

## Ryzyka i ostrzeżenia

- Limity darmowych tierów w `free_models.json` to SEEDY — przed pierwszym
  realnym runem operator weryfikuje limity w konsolach providerów
  (spójnie z notatkami provider_quota_monitor; NIM 40 RPM nie gwarantowane).
- FreeApiEngine niewidoczny w CI (SELFOPT_NETWORK nieustawione) — celowe;
  happy-path testowany przez mock urllib (offline).
- Transport LoRa to staging: nadawanie w eter robi most (remix-lora-bridge)
  albo relay — nie ta komórka. Hop-guard chroni przed pętlą, dedup przed
  dublami, TTL przed starymi alarmami.
- LangGraph/gepa/openevolve są OPCJONALNE (lazy import) — instalacja
  nie zmienia wyników testów, tylko wzbogaca silniki (engines_detected w
  run_receipt mówi prawdę, który był użyty).

## Referencje zewnętrzne

- remix-lora-bridge (BridgeEngine.kt, RadioScheduler.kt) — semantyka mostu.
- MESHTASTIC ROUTER (AGENT-INSTRUCTIONS-ADAPTIVE-RELAY.md) — zasada „v1 port
  100% lokalny, bez zmian protokołu" zachowana w transport.py.
- README §4 (GEPA/OpenEvolve/Abstral/LangGraph) i
  docs/GRAF_LANCUCHA_AUTOMATYZACJI.md (FAZA 5) — realizowane przez T48.
