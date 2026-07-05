# Portfel 25 Zleceń dla Podwykonawców - H2 Roadmapa Autonomizacji AI - 2026-07-05

## Cel portfela

Przekuć Horyzont 2 (6 tygodni) z `ROADMAPA_AUTONOMICZNEJ_AUTOMATYZACJI_AI.md` (Z95) na konkretne zlecenia podwykonawców: importer harmonogramowany, verifier deterministyczny, curator AI, dashboard metryk D1, oraz bot inicjujący `execution_pack`. Każde zadanie zachowuje zasadę **AI sugeruje, człowiek zatwierdza zmiany produkcyjne**.

Zamyka Horyzont 2 roadmapy, otwierając drogę do H3 (węzły edge jako providery — Patrz Portfel 26 TBD).

## Zadania do wykonania

| ID | Plik zlecenia | Priorytet | Cel | Gate | Rollback | Metryka | Blokery |
|----|---------------|-----------|-----|------|----------|---------|---------|
| B1 | `ZLECENIE_GLOWNE_B1_IMPORTER_AGENT_SCHEDULED.md` | high | Harmonogramowany agent `importer` — pull CERN/składniki do staging D1 wg cron. | read-only upstream; brak zapisu do `kicad_library_components` bez dedup | drop staging table, reingest | coverage % encji z provenance | A2 curator gotowy (H1) |
| B2 | `ZLECENIE_GLOWNE_B2_VERIFIER_AGENT_SCHEMA_DEDUP_OCR.md` | high | Agent `verifier` — schema-diff, dedup, OCR deferred. Fail → `needs_more_data` + event. | deterministyczny; nie nadpisuje master | re-verify z backupem | false-positive ratio | Z88 migracje gotowe |
| B3 | `ZLECENIE_GLOWNE_B3_CURATOR_AI_NORMALIZATION.md` | medium | Agent `curator` — AI normalizacja (species/genus/mounting) → sugestie `suggested`. | sugestia tylko; nie nadpisuje `recycled_part_master` | event `next_status=suggested` | coverage normalizacji | B2 gotowy |
| B4 | `ZLECENIE_GLOWNE_B4_D1_AUTOMATION_METRICS_DASHBOARD.md` | medium | Tabela `automation_metrics` + dashboard metryk w D1 (coverage, false-positive, P50 review, rollback success). | metryki read-only dla agenta | drop metryki, regen z events | same metryki | — |
| B5 | `ZLECENIE_GLOWNE_B5_BOT_EXECUTION_PACK_INITIATOR.md` | medium | Bot dyscord/Telegram inicjuje `execution_pack` (Project 13) jako autonomiczne zadanie bez nadpisywania katalogu. | fork-first, PR-first, review-first (`CANARY_PILOT_PACKET`) | zamknięcie PR bez merge | N PR/sprint | B4 metryki |

## Kolejność rekomendowana

1. **B4** — metryki jako prerequisit health-check botów (niezależne od reszty).
2. **B1** — importer harmonogramowany zamka pętlę ingest dla H2.
3. **B2** — verifier deterministyczny wspiera B1 i B3.
4. **B3** — curator zależy od B2 (tylko verified rekordy idą do AI sugestii).
5. **B5** — bot inicjuje execution_pack z metrykami z B4 (ostatni, potrzebuje wszystkich wcześniejszych).

## Gate Horyzontu 2 (z roadmapy)

Wszystkie 5 metryk minimalnych mierzone automatycznie; bot może inicjować `execution_pack` bez ryzyka modyfikacji `recycled_part_master`; regresje KiCad posortowane w <72h.

## Rollback H2 (z roadmapy)

Jeśli false-positive ratio >30% przez 3 dni: curator przechodzi w tryb `suggest-only-audit` (sugeruje, ale wymaga potwierdzenia drugiego maintenera). Wstrzymać ingest nowych źródeł, audyt 50 ostatnich events.

## Definition of Done dla Portfela 25

- B1: `cron`/`schedule` picka z D1 → staging table, dedup przed insert, event per ingest.
- B2: schema-diff raport + dedup checksum + OCR deferred status nienadpisujący `recycled_part_master`.
- B3: AI sugestie tylko z `next_status=suggested`, zero zapisów do master bez human review.
- B4: `automation_metrics` table + 5 metryk minimalnych obliczanych z `kicad_review_events`.
- B5: bot inicjuje `execution_pack` jako PR (fork-first), gate `reviewer` + `CANARY`, brak bezpośredniego zapisu do katalogu.
- Wszystkieagent AI quaternion: **nigdy** `approved` bez maintenera (wymuszone w `kicad_review.js`).

## Metryki minimalne (wymagane w B4)

| Metryka | Cel | Bramka |
|---------|-----|--------|
| coverage danych | % encji z consistent provenance | >80% przed eksportem |
| false-positive dopasowań | odrzucone / zatwierdzone | <30% (powyżej = pauza curatora) |
| czas do review P50 | `suggested` → `approved`/`rejected` | <72h |
| liczba zaakceptowanych / sprint | | rosnąca |
| rollback success rate | % rollbacków bez utraty danych | 100% |

## Architektura bazowa (już gotowa z H1 / Portfel 21-24)

- `cloudflare/src/kicad_review.js` (Z90) — review ledger, blokada `reviewed_by=ai` approve.
- `cloudflare/src/ecoeda_export.js` (Z91) — eksport tylko `approved`.
- `cloudflare/src/discord_kicad_actions.js` (Z94) — bot cienka warstwa nad `kicad_review.js`.
- `cloudflare/src/kicad_lookup.js` (Z89) — wspólny lookup.
- `cloudflare/src/schema_migrations.js` (Z88) — staging tables: `kicad_library_sources`, `kicad_library_components`, `recycled_part_kicad_links`.
- `pipelines/import_cern_kicad_library.py` (Z87) — dry-run importer (B1 przekształci w harmonogramowany production ingest z zachowaniem provenance).
- `docs/KICAD_VERSION_CONVERSION_EXPORT_POLICY.md` (Z92) — polityka konwersji (B5 musi respektować).

## Powiązania

- `docs/ROADMAPA_AUTONOMICZNEJ_AUTOMATYZACJI_AI.md` (Z95) — roadmapa nadrzędna (H2 = ten portfel).
- `docs/REKOMENDACJE_AUTONOMICZNEJ_AUTOMATYZACJI_AI_2026-05-14.md` — ścieżki bazowe 1-5.
- `docs/REVIEW_ROTATION_GOVERNANCE.md` — integrity review, rotacja reviewerów.
- `docs/CANARY_PILOT_PACKET.md` (jeśli istnieje) — tryb canary dla execution_pack.
- `PROJEKTY/13_baza_czesci_recykling/` — katalog docelowy execution_packów.

## Status

OPEN (2026-07-05) — utworzony przez agenta jako R7 z `HANDOFF_DLA_NASTEPNEGO_AGENTA_2026-07-05_PO_Q1_Q8.md`. Brak zrealizowanych zadań — wszystkie B1-B5 pending.

## Przekazanie

Portfel 25 wchodzi po zamkniętym Portfelu 24 (Z87–Z95 ujednolicone statusy DONE/PARTIAL PASS). Po zrealizowaniu B1-B5 następuje gate H2 i przejście do H3 roadmapy (węzły edge jako providery) — planowane jako Portfel 26 (TBD przez następnego agenta po gate H2).
