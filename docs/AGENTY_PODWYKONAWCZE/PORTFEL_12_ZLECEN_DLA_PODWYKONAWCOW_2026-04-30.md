# Portfel 12 Zlecen Dla Podwykonawcow 2026-04-30

Ten portfel powstaje po odbiorze zadan `41-45`.

Nie sluzy do ponownego opisywania tych samych blockerow OCR. Po audycie verification ma `0 disputed` i curation ma `0 deferred`.

## Kolejnosc pracy

Najpierw zadania wymagajace realnego reviewera albo hardware. Jesli tych zasobow nie ma, zapisz krotki blocker receipt i nie produkuj kolejnego packetu.

## Portfel

1. `A` - `ZLECENIE_GLOWNE_47_PROJECT13_CURATION_REAL_HUMAN_REVIEW_14_PENDING_AND_LEDGER_CLOSEOUT.md`
   - zaleznosci: odbior `41-45`, prawdziwy reviewer/maintainer
   - odbior: `record-review` dla `14` pending albo krotki blocker receipt
2. `A` - `ZLECENIE_GLOWNE_46_PROJECT13_ESP_RUNTIME_REAL_HARDWARE_BENCH_RUN_AND_GATE_UPDATE.md`
   - zaleznosci: fizyczna plytka, zasilanie, miernik/operator
   - odbior: realny bench receipt albo blocker receipt bez fikcyjnych pomiarow
3. `B` - `ZLECENIE_GLOWNE_48_PROJECT13_EXPORT_GATE_OPEN_APPLY_EXPORT_RELEASE_AFTER_REVIEW.md`
   - zaleznosci: `47`, `export-gate OPEN`
   - odbior: release receipt tylko przy `OPEN`, inaczej blocker receipt
4. `B` - `ZLECENIE_GLOWNE_50_PROJECT13_VERIFICATION_OCR_PARSER_REGRESSION_AND_STALE_PACKET_GUARD.md`
   - zaleznosci: poprawka z audytu `42`
   - odbior: test regresyjny bez API/network i pusty `ocr-selector` przy `0 deferred`
5. `C` - `ZLECENIE_GLOWNE_49_PROJECT13_CANARY_MAINTAINER_SIGNOFF_C1_C5_OR_NO_GO_REFRESH.md`
   - zaleznosci: maintainer, CODEOWNERS loginy, branch protection evidence, realny wolontariusz
   - odbior: maintainer-signed GO/NO-GO albo jawny agent NO-GO blocker receipt

## Stan bazowy

- Verification: `26 confirmed`, `0 disputed`, `56 rejected`
- Curation: `26 accept`, `0 defer`, `56 reject`
- Review queue: `14 pending_human_approval`, `12 auto_approved`, `56 auto_rejected`
- Export gate: `BLOCKED`
- Canary: `NO-GO blocker receipt`, brak podpisu maintainera
- ESP runtime: real hardware bench nadal nie wykonany

## Zasada dla glownego agenta

- Nie uruchamiaj `apply` ani `export-all`, jesli `export-gate` nie jest `OPEN`.
- Nie wpisuj `reviewed_by`, jesli prawdziwa osoba nie podjela decyzji.
- Nie wolaj OCR ponownie dla zamknietych cases bez nowego powodu dowodowego.
- Nie traktuj agentowego NO-GO jako podpisu maintainera.
- Po zakonczeniu portfela przygotuj odbior `12` i kolejny handoff.
