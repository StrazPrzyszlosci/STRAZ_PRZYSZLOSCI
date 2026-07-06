# Handoff dla Następnego Agenta - po Hermes Pilot Plan - 2026-07-06

## Kontekst

Użytkownik pyta, gdzie realnie odpalić agentów typu Hermes, żeby już pracowali dla inicjatywy. Wskazał dostępne ścieżki: NVIDIA NIM z limitami około 40 RPM, Google AI Studio z mocniejszymi modelami oraz self-host/darmowe zasoby. Ta iteracja nie instaluje Hermesa z sekretami, tylko tworzy review-gated plan pilota i macierz providerów, żeby można było uruchomić pierwszego stale działającego agenta bez ryzyka sekretnych kosztów lub fizycznego wykonania.

## Źródła sprawdzone online

- GitHub `NousResearch/hermes-agent` — Hermes ma self-improvement loop, skills, memory, cron, subagents, gateway komunikatorów i wiele backendów terminalowych.
- Google AI docs — Gemini API rate limits są mierzone m.in. RPM/TPM/RPD, stosowane per projekt i zależne od modelu/tieru; aktywne limity trzeba sprawdzać w AI Studio.
- Google AI pricing — AI Studio/Gemini API ma free start i modele z darmowymi tokenami, ale free tier może używać contentu do ulepszania produktów.
- NVIDIA Developer Forums — free tier NIM ma limity zależne od modelu/use-case/obciążenia; nie ma oficjalnego obejścia ani gwarantowanego podniesienia limitu w tym samym free tierze.

## Co zrobiono

### Hermes pilot — DONE: plan uruchomienia pierwszego stale działającego agenta

Dodano `docs/HERMES_AGENT_MOZLIWOSCI_I_PILOT_2026-07-06.md` z odpowiedzią operacyjną:

- pierwszy Hermes powinien działać jako `repo-builder / scout / handoff-builder`,
- najlepszy pierwszy target: tani VPS / mała VM,
- drugi target: Termux na odzyskanym telefonie jako gateway/operator,
- trzeci target: odzyskany mini PC z OZE jako private local worker,
- GPU/serverless tylko jako opcje późniejsze, z uzasadnieniem kosztu/energii.

### Provider matrix — DONE

Dodano `agent_runtime_plans/hermes_pilot/provider_matrix.json`:

- `google_ai_studio_free` jako primary reasoning/multimodal,
- `nvidia_nim_free` jako fallback/parallel text worker,
- `selfhost_recovered_node` jako private low-power worker.

Macierz zawiera:

- nazwę sekretu,
- rolę providera,
- kandydatów modeli,
- politykę quota,
- notatkę prywatności,
- tryby dozwolone,
- tryby zablokowane.

### Pilot plan — DONE

Dodano `agent_runtime_plans/hermes_pilot/pilot_plan.json`:

- runtime targets: VPS/VM, Termux/recovered phone, selfhost recovered PC/OZE,
- initial cells: `HermesRepoScout`, `HermesHandoffBuilder`, `HermesExecutionPackGenerator`, `HermesAuditReviewer`, `HermesProviderQuotaMonitor`,
- wymagane sekrety: `GEMINI_API_KEY`, `NVIDIA_API_KEY`, `GITHUB_PAT`,
- wymagane artefakty każdego runu: `run_receipt.json`, `model_route.json`, `quota_snapshot.json`, `git_diff.patch`, `handoff_or_pr.md`,
- human control points i blokady: brak direct push do main, brak auto-merge, brak secret printing, brak physical actuation, brak unbounded spend.

### Walidator i testy — DONE

Dodano `agent_runtime_plans/hermes_pilot/validate_pilot.py` i `tests/test_hermes_pilot_plan.py`.

Walidator blokuje plan, jeśli:

- status nie jest `draft_review_required`,
- provider nie blokuje `physical_actuation`,
- brakuje quota/privacy policy,
- brakuje audit artifactów,
- brakuje blokad `direct push to main`, `auto-merge`, `secret printing`, `physical actuation`, `unbounded spend`.

## Testy wykonane

```bash
python3 -m unittest tests.test_hermes_pilot_plan
python3 -m unittest discover -s tests -p 'test_*.py'
```

## Następne zadania

### H1 — PRIORYTET 1: Hermes dry-run installer packet

Dodać pack instalacyjny dla operatora:

- target VPS/Termux/selfhost,
- preflight bez sekretów,
- check `python`, `node`, `git`, `rg`, dostęp do forka,
- instrukcja minimalnego `GITHUB_PAT` tylko do forka,
- receipt z wersjami narzędzi.

Acceptance criteria:

- Pack nie zapisuje sekretów do repo.
- Test sprawdza, że `.env` nie jest wymagany do dry-run.
- Test sprawdza obecność rollback i secret hygiene checklist.

### H2 — PRIORYTET 2: Provider quota monitor cell

Dodać komórkę `provider_quota_monitor`:

- czyta konfigurację providerów,
- zapisuje ręczny/automatyczny snapshot limitów,
- blokuje planner, jeśli quota nieznana albo przekroczona,
- tworzy `quota_snapshot.json`.

Acceptance criteria:

- Brak quota snapshot blokuje uruchomienie agent chain.
- NVIDIA NIM nie może zakładać gwarantowanego 40 RPM bez pomiaru.
- Google AI Studio wymaga odwołania do aktywnych limitów projektu.

### H3 — PRIORYTET 3: Hermes first work queue

Dodać pierwszą kolejkę prac dla Hermesa:

- `repo_scout_daily`,
- `handoff_builder_after_commit`,
- `resource_scout_triage`,
- `execution_pack_draft_generator`,
- `audit_reviewer_before_pr`.

Acceptance criteria:

- Każde zadanie ma input, output, model route, artifact requirements i human control point.
- Żadne zadanie nie ma prawa auto-merge ani direct push.

### H4 — PRIORYTET 4: Human approval UI/command stub

Dodać minimalny format komendy/rekordu approval:

- kto zatwierdza,
- co zatwierdza,
- zakres,
- czas,
- ryzyka,
- expiry,
- rollback.

Acceptance criteria:

- Approval wygasa.
- Approval dla kodu nie zatwierdza fizycznego działania.
- Approval dla providerów nie zatwierdza zwiększania kosztów bez ledgeru.

## Ryzyka

- Nie odpalać Hermesa z szerokim tokenem GitHub ani sekretem produkcyjnym.
- Nie łączyć od razu z hardware actuation.
- Nie traktować limitu NVIDIA 40 RPM jako gwarantowanego; mierzyć i zapisywać snapshot.
- Nie wysyłać prywatnych danych do free hosted modeli bez polityki i zgody.
