# Portfel 24 Zleceń dla Podwykonawców - Review UI, eksport i autonomizacja operacyjna - 2026-05-14

## Cel portfela

Po wdrożeniu ledgeru review zbudować warstwę operacyjną: akcje Discord, eksport ecoEDA z provenance, smoke realnego CERN oraz roadmapę autonomicznych agentów.

## Zadania do wykonania

| ID | Plik | Priorytet | Cel | Blokery |
|----|------|-----------|-----|---------|
| Z94 | `ZLECENIE_GLOWNE_94_DISCORD_KICAD_REVIEW_ACTIONS.md` | high | Discord UI/actions dla review KiCad. | Z90 gotowe |
| Z91 | `ZLECENIE_GLOWNE_91_ECOEDA_EXPORT_WITH_CERN_PROVENANCE.md` | high | Eksport ecoEDA/NSIP z provenance CERN dla statusów `approved`. | Z90 gotowe |
| Z93 | `ZLECENIE_GLOWNE_93_CERN_KICAD_REAL_CHECKOUT_SMOKE.md` | medium | Smoke importera na realnym checkout/archiwum CERN albo blocker receipt. | Dostęp do danych |
| Z95 | `ZLECENIE_GLOWNE_95_AI_AUTOMATION_ORCHESTRATOR_ROADMAP.md` | medium | Roadmap autonomicznej automatyzacji AI. | README + obecne moduły |
| Z92 | `ZLECENIE_GLOWNE_92_KICAD_VERSION_CONVERSION_EXPORT_POLICY.md` | low | Polityka konwersji KiCad jako etap eksportu. | Z87 gotowe |

## Kolejność rekomendowana

1. Z94 — Discord jako konsola review maintainerów.
2. Z91 — eksport tylko zatwierdzonych linków.
3. Z93 — smoke realnego CERN bez commitowania pełnego repo.
4. Z95 — mapa autonomicznych agentów i gate'ów.
5. Z92 — konwersja jako downstream export policy.

## Definition of Done

- Akcje Discord używają `kicad_review.js`, nie duplikują logiki.
- Eksport nie łamie obecnego `ecoEDA_inventory.csv`.
- Smoke CERN ma blocker receipt, jeśli brak checkoutu.
- Roadmapa autonomizacji wskazuje gate, rollback i metryki.
