# Portfel 21 Zleceń dla Podwykonawców - Discord bot + CERN KiCad wykonanie - 2026-05-14

## Cel portfela

Przejść z decyzji architektonicznej do pierwszej implementacji integracji CERN KiCad Library: dry-run importer, staging schema, lookup dla botów i review ledger.

## Zadania do wykonania

| ID | Plik | Priorytet | Cel | Blokery |
|----|------|-----------|-----|---------|
| Z87 | `ZLECENIE_GLOWNE_87_CERN_KICAD_DRY_RUN_IMPORTER.md` | high | Importer dry-run dla CERN KiCad Library bez zapisu do D1. | Brak |
| Z88 | `ZLECENIE_GLOWNE_88_KICAD_STAGING_MIGRATIONS.md` | high | Migracje D1/SQLite dla staging/provenance KiCad. | Z87 raport |
| Z89 | `ZLECENIE_GLOWNE_89_DISCORD_TELEGRAM_KICAD_LOOKUP.md` | high | Wspólny lookup KiCad dla Discord/Telegram. | Z88 |
| Z90 | `ZLECENIE_GLOWNE_90_KICAD_HUMAN_REVIEW_LEDGER.md` | medium | Human review ledger dla linków CERN -> NSIP. | Z89 |
| Z91 | `ZLECENIE_GLOWNE_91_ECOEDA_EXPORT_WITH_CERN_PROVENANCE.md` | medium | Eksport ecoEDA/NSIP z provenance CERN bez regresji. | Z90 |
| Z92 | `ZLECENIE_GLOWNE_92_KICAD_VERSION_CONVERSION_EXPORT_POLICY.md` | low | Polityka konwersji wersji KiCad jako etap eksportu. | Z87 |

## Kolejność rekomendowana

1. Z87 — tylko dry-run i mini-fixture, bez pełnego repo w testach.
2. Z88 — tabele staging dopiero po poznaniu realnych pól z Z87.
3. Z89 — najpierw funkcja wspólna, potem cienkie integracje Discord/Telegram.
4. Z90 — ledger i review przed jakimkolwiek automatycznym uzupełnianiem rekordów.
5. Z91 — eksport ecoEDA jako kompatybilność wsteczna.
6. Z92 — konwersja KiCad dopiero dla projektów wyjściowych.

## Zasady bezpieczeństwa danych

- Nie nadpisywać istniejących pól `recycled_part_master` bez ledgeru.
- Nie pobierać pełnej biblioteki CERN w testach CI.
- Każdy rekord z CERN musi mieć provenance i informację o licencji.
- Bot Discord nie może mieć oddzielnej prawdy biznesowej względem Telegrama.

## Definition of Done portfela

- Wszystkie zadania mają testy lub raport dry-run.
- Handoff zawiera decyzję, wyniki testów i najlepszy następny krok.
- Dokumentacja mówi jednoznacznie: konwersja KiCad jest etapem eksportu, nie warunkiem ingestu.
