# Portfel 22 Zleceń dla Podwykonawców - KiCad lookup, review i smoke realnego CERN - 2026-05-14

## Cel portfela

Kontynuować po Z87-Z88: podłączyć staging KiCad do botów, dodać human review ledger, utrzymać zgodność ecoEDA i wykonać smoke na realnym checkout/archiwum CERN, jeśli operator udostępni dane wejściowe.

## Zadania do wykonania

| ID | Plik | Priorytet | Cel | Blokery |
|----|------|-----------|-----|---------|
| Z89 | `ZLECENIE_GLOWNE_89_DISCORD_TELEGRAM_KICAD_LOOKUP.md` | high | Wspólny lookup KiCad dla Discord/Telegram. | Z88 gotowe |
| Z90 | `ZLECENIE_GLOWNE_90_KICAD_HUMAN_REVIEW_LEDGER.md` | high | Human review ledger dla linków CERN -> NSIP. | Z89 |
| Z91 | `ZLECENIE_GLOWNE_91_ECOEDA_EXPORT_WITH_CERN_PROVENANCE.md` | medium | Eksport ecoEDA/NSIP z provenance CERN. | Z90 |
| Z92 | `ZLECENIE_GLOWNE_92_KICAD_VERSION_CONVERSION_EXPORT_POLICY.md` | low | Polityka konwersji wersji KiCad jako etap eksportu. | Z87 gotowe |
| Z93 | `ZLECENIE_GLOWNE_93_CERN_KICAD_REAL_CHECKOUT_SMOKE.md` | medium | Smoke importera na realnym checkout/archiwum CERN albo blocker receipt. | Dostęp do checkout/archiwum |

## Kolejność rekomendowana

1. Z89 — najpierw wspólna funkcja lookup bez oddzielnej logiki Discord.
2. Z90 — review ledger zanim AI zacznie uzupełniać pola master.
3. Z93 — równolegle, gdy dostępny jest checkout/archiwum CERN.
4. Z91 — eksport ecoEDA po zatwierdzonym ledgerze.
5. Z92 — polityka konwersji jako dokument/runbook downstream.

## Zasady bezpieczeństwa danych

- Lookup może sugerować, ale nie może zatwierdzać dopasowań bez człowieka.
- Nie commitować pełnego repo CERN ani dużych wyników smoke.
- Eksport ecoEDA ma być kompatybilny wstecznie.
- Każda odpowiedź bota o danych CERN musi pokazywać źródło/provenance i status review.
