# Portfel 24 Zleceń dla Podwykonawców - Review UI, eksport i autonomizacja operacyjna - 2026-05-14

## Cel portfela

Po wdrożeniu ledgeru review zbudować warstwę operacyjną: akcje Discord, eksport ecoEDA z provenance, smoke realnego CERN oraz roadmapę autonomicznych agentów.

## Portfel nadrzędny

Portfel 24 zamyka łańcuch Z87–Z95 poprzedzony Portfelami 21–23 (Z87–Z90). Statusy ujednolicone poniżej.

| ID | Plik | Priorytet | Cel | Blokery | Status |
|----|------|-----------|-----|---------|--------|
| Z87 | `ZLECENIE_GLOWNE_87_CERN_KICAD_DRY_RUN_IMPORTER.md` | high | Dry-run importer CERN KiCad do staging. | — | **DONE** 2026-05-14 (`ODBIOR_PORTFELA_21`) + potwierdzone R1 fixture smoke 2026-07-05 — `pipelines/import_cern_kicad_library.py`hetto, parser sym+footprint, JSONL/CSV/MD. |
| Z88 | `ZLECENIE_GLOWNE_88_KICAD_STAGING_MIGRATIONS.md` | high | Migracje D1/SQLite staging KiCad. | — | **DONE** 2026-05-14 (`ODBIOR_PORTFELA_21`) — tabele `kicad_library_sources`, `kicad_library_components`, `recycled_part_kicad_links` + indeksy. |
| Z89 | `ZLECENIE_GLOWNE_89_KICAD_LOOKUP_DISCORD_TELEGRAM.md` | high | Wspólny lookup KiCad dla Discord/Telegram. | — | **DONE** 2026-05-14 (`ODBIOR_PORTFELA_22`) — `cloudflare/src/kicad_lookup.js`. |
| Z90 | `ZLECENIE_GLOWNE_90_KICAD_HUMAN_REVIEW_LEDGER.md` | high | Human review ledger KiCad → NSIP. | Z89 | **DONE** 2026-05-14 (`ODBIOR_PORTFELA_23`) — `cloudflare/src/kicad_review.js` migracja `kicad_review_events`, blokada `reviewed_by=ai` approve. |
| Z91 | `ZLECENIE_GLOWNE_91_ECOEDA_EXPORT_WITH_CERN_PROVENANCE.md` | high | Eksport ecoEDA/NSIP z provenance CERN dla statusów `approved`. | Z90 | **DONE** 2026-07-05 — `cloudflare/src/ecoeda_export.js`, 9 testów PASS. |
| Z92 | `ZLECENIE_GLOWNE_92_KICAD_VERSION_CONVERSION_EXPORT_POLICY.md` | low | Polityka konwersji KiCad jako etap eksportu. | Z87 | **DONE** 2026-07-05 — `docs/KICAD_VERSION_CONVERSION_EXPORT_POLICY.md`, runbook A–D, fixture test. |
| Z93 | `ZLECENIE_GLOWNE_93_CERN_KICAD_REAL_CHECKOUT_SMOKE.md` | medium | Smoke importera na realnym checkout/archiwum CERN albo blocker receipt. | Dostęp do danych | **PARTIAL PASS** 2026-07-05 — smoke na fixture mini (`Z93_FIXTURE_SMOKE_REPORT_2026-07-05.md`); realny checkout CERN nadal wymagany operatora. |
| Z94 | `ZLECENIE_GLOWNE_94_DISCORD_KICAD_REVIEW_ACTIONS.md` | high | Discord UI/actions dla review KiCad. | Z90 | **DONE** 2026-07-05 (`ODBIOR_PORTFELA_24`) — `cloudflare/src/discord_kicad_actions.js` + 10 testów PASS. |
| Z95 | `ZLECENIE_GLOWNE_95_AI_AUTOMATION_ORCHESTRATOR_ROADMAP.md` | medium | Roadmap autonomicznej automatyzacji AI. | — | **DONE** 2026-07-05 — `docs/ROADMAPA_AUTONOMICZNEJ_AUTOMATYZACJI_AI.md` (3 horyzonty, gate, rollback, metryki). |

## Kolejność rekomendowana

1. Z94 — Discord jako konsola review maintenerów.
2. Z91 — eksport tylko zatwierdzonych linków.
3. Z93 — smoke realnego CERN bez commitowania pełnego repo.
4. Z95 — mapa autonomicznych agentów i gate'ów.
5. Z92 — konwersja jako downstream export policy.

## Definition of Done

- Akcje Discord używają `kicad_review.js`, nie duplikują logiki. **PASS** (Z94).
- Eksport nie łamie obecnego `ecoEDA_inventory.csv`. **PASS** (Z91).
- Smoke CERN ma blocker receipt, jeśli brak checkoutu. **PASS** (Z93 — blocker receipt + fixture substitute).
- Roadmapa autonomizacji wskazuje gate, rollback i metryki. **PASS** (Z95).

## Zamknięcie portfela

Wszystkie 9 zadań (Z87–Z95) ma status DONE lub PARTIAL PASS. Portfel 24 **ZAMKNIĘTY**. Jedyny open follow-up: realny checkout CERN dla pełnego PASS Z93 (operator z dyskiem/internetem). Następny portfel (Patrz sekcja przekazanie): `PORTFEL_25_ZLECEN_DLA_PODWYKONAWCOW_2026-07-05.md` (H2 roadmapy autonomizacji).
