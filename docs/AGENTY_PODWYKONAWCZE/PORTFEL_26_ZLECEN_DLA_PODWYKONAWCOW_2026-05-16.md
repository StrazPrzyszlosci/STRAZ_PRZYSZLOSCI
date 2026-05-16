# Portfel 26 Zleceń dla Podwykonawców - Operator export, release receipt i domknięcie pętli KiCad - 2026-05-16

## Cel portfela

Po Z91 przejść od samego helpera eksportu do bezpiecznej obsługi operatorskiej: preview eksportu approved, receipt release, przyciski z wyników lookupu, dry-run synchronizacji master oraz runbook provenance. Wszystko nadal respektuje zasadę: AI sugeruje i raportuje, człowiek zatwierdza.

## Zadania do wykonania

| ID | Plik | Priorytet | Cel | Blokery |
|----|------|-----------|-----|---------|
| Z101 | `ZLECENIE_GLOWNE_101_KICAD_APPROVED_EXPORT_OPERATOR_COMMAND.md` | high | Operator command/endpoint dla preview eksportu approved. | Z91 |
| Z102 | `ZLECENIE_GLOWNE_102_KICAD_EXPORT_RELEASE_RECEIPT.md` | high | Receipt JSON/Markdown dla eksportu approved provenance. | Z91, Z96 |
| Z103 | `ZLECENIE_GLOWNE_103_KICAD_REVIEW_BUTTONS_FROM_LOOKUP_RESULTS.md` | medium | Przyciski `Wyślij do review` bezpośrednio z lookup results. | Z94 |
| Z104 | `ZLECENIE_GLOWNE_104_APPROVED_KICAD_MASTER_SYNC_DRY_RUN.md` | medium | Dry-run synchronizacji zatwierdzonych KiCad pól do master. | Z91, Z96 |
| Z105 | `ZLECENIE_GLOWNE_105_CERN_PROVENANCE_DOCS_AND_RUNBOOK.md` | medium | Runbook pełnej pętli CERN -> review -> export. | Z91 |

## Kolejność rekomendowana

1. Z96/Z97 z Portfela 25 — audit export i metryki kolejki.
2. Z101 — operator preview eksportu approved.
3. Z102 — release receipt do każdego eksportu.
4. Z103 — dopięcie przycisków review z wyników lookupu.
5. Z104/Z105 — dry-run sync i runbook dla maintainerów.

## Definition of Done

- Żadna akcja nie publikuje ani nie synchronizuje danych produkcyjnych bez jawnego kroku maintenera.
- Każdy eksport ma status filter `approved` i jawne provenance.
- UI jest wygodne, ale nie omija ledgeru review.
- Runbook jasno odróżnia sugestię AI, decyzję człowieka, eksport i synchronizację master.
