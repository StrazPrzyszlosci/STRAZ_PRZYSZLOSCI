# Handoff dla Następnego Agenta - po T7 (regresje + Hermes Agent + wizja łańcuchów) - 2026-07-06

## Kontekst wejściowy

Przeczytano ostatni handoff: `docs/HANDOFF_DLA_NASTEPNEGO_AGENTA_2026-07-06_PO_T6_PROVIDER_LIFECYCLE.md`.

Ostatnie commity przed pracą:

- `4158af6` Merge PR #13,
- `0a1685a` `feat(provider): T6 auto-deactivate inactive providers`,
- `9116c41` Merge PR #12,
- `8a66e04` Merge PR #11,
- `e1ba918` `feat(curator): T4 B3 KiCad suggest-only normalizer`.

Priorytet wejściowy T7: naprawić istniejące regresje `python3 -m unittest discover -s tests -p 'test_*.py'`.

## Co zrobiono

### T7 — DONE: naprawa regresji Telegram/Python

1. `cloudflare/src/telegram_ai.js`:
   - `buildPartMasterDetailReply` stał się asynchroniczny i pokazuje przykładowych dawców przy rekordach master z `donor_count > 0`.
   - Odpowiedź AI dla pytań o część używa frazy „lokalnej bazy części reuse”, dzięki czemu istniejący test i mock provider trafiają w właściwy przepływ odpowiedzi.

2. `PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py`:
   - dodano wspólne `write_pending_human_approval_list(review_queue)`, żeby `pending_human_approval_list.json` nie zostawał stary po przebudowie queue,
   - `review-queue` synchronizuje teraz listę pending razem z `curation_review_queue.jsonl`,
   - `list-pending` zapisuje pustą/spójną listę także wtedy, gdy pendingów brak.

3. Odświeżono artefakty:
   - `curation_review_queue.jsonl`,
   - `pending_human_approval_list.json`,
   - `export_gate_packet.json`.

### Hermes Agent — DONE: dołączony jako inspiracja referencyjna

Nie vendorowano kodu Hermes Agent do repo. Dodano bezpieczniejszy tryb referencyjny:

- `docs/external_repos/hermes-agent.md` — karta inspiracji, mapowanie wzorców na Straż Przyszłości i minimalny bezpieczny pilotaż,
- `docs/external_repos/registry.json` — rejestr zewnętrznych repozytoriów, obecnie z `hermes-agent`,
- `docs/WIZJA_WIELOOGNIWOWEJ_AUTOMATYZACJI_SAMOOPTYMALIZUJACEJ.md` — wizja wieloogniwowego systemu dla odzysku odpadów, żywności, smartfonów-edge, mesh i audytowalnych skryptów AI.

Hermes Agent sprawdzono przez `git clone --depth 1 https://github.com/nousresearch/hermes-agent /tmp/hermes-agent` i odczyt README. Najważniejsze wzorce do adaptacji: skills, memory, cron, messaging gateway, subagents, backendy terminalowe i audytowalny loop pracy.

## Testy wykonane

```bash
python3 PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py review-queue
python3 PROJEKTY/13_baza_czesci_recykling/scripts/curate_candidates.py export-gate
node --test cloudflare/tests/telegram_ai.test.mjs
python3 -m unittest discover -s tests -p 'test_*.py'
```

Wynik:

- Telegram AI Node suite: PASS, 32/32.
- Python unittest discover: PASS, 193/193.
- Export gate pozostaje merytorycznie BLOCKED, bo istnieje 5 kandydatów `pending_human_approval` i brak human approval — to poprawny stan governance, nie awaria testu.

## Następne zadania

### T8 — PRIORYTET 1: Realny upstream ingestion path dla B1

Worker nie uruchamia Pythona/git. Dodać CI/offline job albo endpoint/queue dla JSONL wygenerowanego przez `pipelines/import_cern_kicad_library.py`.

Acceptance:

- jest jawny kontrakt pliku/endpointu ingestion,
- jest test dedupe + audit event,
- import nie promuje danych do katalogu bez verifier/curator/review.

### T9 — PRIORYTET 2: Edge flasher wizard dla smartfonów i low-power node

Rozpocząć scaffold `edge-flasher` inspirowany MeshCore/Meshtastic flasher:

- wykrycie urządzenia/profilu,
- wybór profilu `phone-sensor-gateway`, `phone-aquaponics-observer`, `phone-recycle-bench`, `phone-mesh-console`,
- generowanie `device_profile.json`, `install_receipt.json`, `bench_test_report.md`, `rollback.md`,
- zero fizycznej kontroli bez human approval.

### T10 — PRIORYTET 3: Hermes-style execution skill registry

Dodać mały rejestr `ExecutionPackSkill`:

- id, cel, wejścia, wyjścia, ryzyka, testy, reviewer roles,
- pierwsze skille: `RepoScout`, `HandoffBuilder`, `AuditReviewer`, `EdgeOnboarding`, `AquaponicsObserver`.

### T11 — PRIORYTET 4: GitHub App/offline branch flow dla B5

Rozwinąć B5 z D1/draft PR surface do pełnego operator-safe flow: offline/CI branch creation, GitHub webhook status updates `started/closed/merged`, rollback test start → PR → close bez merge.

### T12 — PRIORYTET 5: WebSocket/events stream dla edge H3

Po stabilizacji H2 dodać `/v1/ws/events?provider_id=<id>` albo polling-safe stream dla rekomendacji/alarmów do węzłów edge.

## Zasady dla następnego agenta

- Nie omijać human approval dla działań fizycznych.
- Zewnętrzne repozytoria traktować jako źródła wzorców/RAG, nie jako bezpośredni runtime krytyczny.
- Każdy nowy automatyczny skrypt musi mieć audit trail i tryb suggest-only lub dry-run.
- Po zmianie artefaktów queue zawsze odświeżać powiązane packet/list JSON, żeby nie wracały regresje spójności.
