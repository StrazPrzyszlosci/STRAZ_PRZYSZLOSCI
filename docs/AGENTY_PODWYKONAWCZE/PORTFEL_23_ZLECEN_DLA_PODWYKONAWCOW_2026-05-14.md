# Portfel 23 Zleceń dla Podwykonawców - KiCad review i autonomizacja AI - 2026-05-14

## Cel portfela

Po uruchomieniu wspólnego lookupu KiCad/NSIP zbudować bezpieczną warstwę review oraz przygotować roadmapę autonomicznej automatyzacji AI dla repo.

## Zadania do wykonania

| ID | Plik | Priorytet | Cel | Blokery |
|----|------|-----------|-----|---------|
| Z90 | `ZLECENIE_GLOWNE_90_KICAD_HUMAN_REVIEW_LEDGER.md` | high | Human review ledger dla linków CERN -> NSIP. | Z89 gotowe |
| Z94 | `ZLECENIE_GLOWNE_94_DISCORD_KICAD_REVIEW_ACTIONS.md` | high | Przyciski/akcje Discord dla review KiCad. | Z90 |
| Z91 | `ZLECENIE_GLOWNE_91_ECOEDA_EXPORT_WITH_CERN_PROVENANCE.md` | medium | Eksport ecoEDA/NSIP z provenance CERN. | Z90 |
| Z93 | `ZLECENIE_GLOWNE_93_CERN_KICAD_REAL_CHECKOUT_SMOKE.md` | medium | Smoke importera na realnym checkout/archiwum CERN albo blocker receipt. | Dostęp do danych |
| Z95 | `ZLECENIE_GLOWNE_95_AI_AUTOMATION_ORCHESTRATOR_ROADMAP.md` | medium | Roadmap autonomicznej automatyzacji AI z gate'ami bezpieczeństwa. | Brak |
| Z92 | `ZLECENIE_GLOWNE_92_KICAD_VERSION_CONVERSION_EXPORT_POLICY.md` | low | Polityka konwersji wersji KiCad jako etap eksportu. | Z87 gotowe |

## Kolejność rekomendowana

1. Z90 — ledger review przed akcjami bota.
2. Z94 — UI/akcje Discord po gotowym ledgerze.
3. Z91 — eksport ecoEDA dopiero po statusach `approved`.
4. Z93 — smoke realnego CERN, jeśli dostępny checkout/archiwum.
5. Z95 — równolegle spiąć roadmapę autonomizacji.
6. Z92 — domknąć politykę konwersji downstream.

## Definition of Done

- Żadna ścieżka AI nie zatwierdza sama linku CERN -> NSIP.
- Discord i Telegram korzystają ze wspólnych funkcji lookup/review.
- Eksport ecoEDA pozostaje kompatybilny wstecznie.
- Roadmapa autonomizacji wskazuje konkretne, mierzalne kroki i rollback.
