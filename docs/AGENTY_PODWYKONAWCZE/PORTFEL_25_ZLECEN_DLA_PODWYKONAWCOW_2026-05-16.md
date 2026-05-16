# Portfel 25 Zleceń dla Podwykonawców - Audyt review, metryki i bezpieczna automatyzacja - 2026-05-16

## Cel portfela

Po Z94 domknąć operacyjny obieg KiCad review: audytowalność decyzji, metryki kolejki, smoke eksportu zatwierdzonych rekordów oraz politykę rotacji reviewerów. Równolegle przygotować najbezpieczniejszy MVP orkiestratora AI, zgodny z zasadą: AI sugeruje i raportuje, człowiek zatwierdza.

## Zadania do wykonania

| ID | Plik | Priorytet | Cel | Blokery |
|----|------|-----------|-----|---------|
| Z96 | `ZLECENIE_GLOWNE_96_KICAD_REVIEW_AUDIT_EXPORT.md` | high | Eksport/audit log decyzji KiCad review. | Z90, Z94 gotowe |
| Z97 | `ZLECENIE_GLOWNE_97_KICAD_REVIEW_QUEUE_SLA_METRICS.md` | high | Metryki kolejki KiCad review dla operatora. | Z90, Z94 gotowe |
| Z98 | `ZLECENIE_GLOWNE_98_ECOEDA_APPROVED_EXPORT_SMOKE.md` | high | Smoke eksportu tylko rekordów `approved`. | Z91 |
| Z99 | `ZLECENIE_GLOWNE_99_REVIEWER_ROTATION_D1_POLICY.md` | medium | Polityka reviewer roles i rotacji. | Z94 |
| Z100 | `ZLECENIE_GLOWNE_100_SAFE_AUTOMATION_ORCHESTRATOR_MVP.md` | medium | MVP bezpiecznego orkiestratora AI. | Z95 |

## Kolejność rekomendowana

1. Z91 z Portfela 24 — eksport approved provenance jest nadal najważniejszym downstream krokiem.
2. Z96 — audit export, żeby decyzje review były łatwe do sprawdzenia.
3. Z97 — metryki SLA kolejki review dla operatora.
4. Z98 — smoke eksportu po wdrożeniu Z91.
5. Z99 i Z100 — governance i automatyzacja bez ryzyka samodzielnych approvali.

## Definition of Done

- Żaden nowy mechanizm nie pozwala AI zatwierdzić `approved`.
- Każdy raport/eksport ma jawne provenance i ślad audytowy.
- Metryki są informacyjne i nie zmieniają danych.
- Orkiestrator MVP uruchamia tylko akcje odwracalne albo draftowe.
