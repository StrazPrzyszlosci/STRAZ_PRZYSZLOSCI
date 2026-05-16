# Portfel 27 Zleceń dla Podwykonawców - Operacjonalizacja audytu KiCad i release receipts - 2026-05-16

## Cel portfela

Po Z96 dopiąć audyt do pracy operatora i przygotować bezpieczne release receipts dla eksportów. Celem jest pełna widoczność decyzji bez przyznawania AI prawa do zatwierdzania lub synchronizacji danych produkcyjnych.

## Zadania do wykonania

| ID | Plik | Priorytet | Cel | Blokery |
|----|------|-----------|-----|---------|
| Z106 | `ZLECENIE_GLOWNE_106_KICAD_AUDIT_OPERATOR_PREVIEW.md` | high | Preview audytu dla operatora bota. | Z96 |
| Z107 | `ZLECENIE_GLOWNE_107_KICAD_REVIEW_METRICS_OPERATOR_REPLY.md` | high | Odpowiedź operatorska dla metryk KiCad review. | Z97 |
| Z108 | `ZLECENIE_GLOWNE_108_KICAD_EXPORT_HASH_RECEIPT_HELPER.md` | high | Hash i receipt JSON dla eksportów approved/audit. | Z91, Z96 |
| Z109 | `ZLECENIE_GLOWNE_109_KICAD_REVIEW_LEDGER_PAGINATION.md` | medium | Limit/offset/cursor dla kolejki i audytu. | Z96, Z97 |
| Z110 | `ZLECENIE_GLOWNE_110_KICAD_REVIEW_INTEGRITY_CHECKLIST.md` | medium | Checklist integrity dla pętli KiCad. | Z96 |

## Kolejność rekomendowana

1. Z97 z Portfela 25 — najpierw metryki kolejki.
2. Z108 — receipt/hash, bo przyda się dla Z101/Z102.
3. Z106/Z107 — odpowiedzi operatorskie w botach.
4. Z109 — paginacja, jeśli kolejka urośnie.
5. Z110 — integrity checklist przed dalszą automatyzacją.

## Definition of Done

- Audyt i metryki są read-only.
- Receipt ma hash i jawne źródła danych.
- UI operatora nie omija `kicad_review_events`.
- Checklist wzmacnia zasadę: AI sugeruje, człowiek zatwierdza.
