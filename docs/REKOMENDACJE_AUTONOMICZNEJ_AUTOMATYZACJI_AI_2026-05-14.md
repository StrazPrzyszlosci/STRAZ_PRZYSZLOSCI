# Rekomendacje rozwoju autonomicznej automatyzacji AI - 2026-05-14

## Do czego ma służyć repo

Repo powinno działać jako operacyjny system budowania bazy wiedzy NSIP i automatyzacji projektów reuse/hardware:

1. Boty Discord/Telegram są interfejsem dla operatorów, wolontariuszy i maintainerów.
2. Cloudflare Worker + D1/SQLite to warstwa API, pamięci operacyjnej i audytu.
3. Pipeline'y i execution packi wykonują ingest, walidację, kurację i eksport.
4. AI sugeruje klasyfikację, dopasowania i kolejne kroki, ale zmiany produkcyjne przechodzą przez review ledger.

## Najlepsze ścieżki rozwoju

### Ścieżka 1 — najpierw kontrolowany loop danych

Największy zwrot da domknięcie pętli: `ingest -> staging -> lookup -> human review -> export`. Dla CERN KiCad oznacza to: dry-run importer, staging tables, wspólny lookup, review ledger i eksport ecoEDA/NSIP. Bez tego AI będzie generować sugestie, których nie da się bezpiecznie zatwierdzić ani cofnąć.

### Ścieżka 2 — bot Discord jako centrum operacyjne

Discord powinien stać się konsolą operacyjną: wyszukiwanie części, inicjowanie review, zatwierdzanie linków, uruchamianie dry-runów i publikowanie raportów. Telegram może pozostać kompatybilnym kanałem terenowym, ale logika biznesowa musi być wspólna.

### Ścieżka 3 — autonomous agents tylko z gate'ami

Autonomiczne AI powinno działać w rolach:

- importer: pobiera/stage'uje dane,
- verifier: sprawdza spójność i źródła,
- curator: proponuje dopasowania,
- reviewer assistant: przygotowuje decyzję dla człowieka,
- exporter: generuje paczki ecoEDA/NSIP po zatwierdzeniu.

Każdy agent może pisać tylko do staging/raportów, a produkcyjne zmiany wymagają ledgeru i statusu `approved`.

### Ścieżka 4 — metryki przed skalowaniem

Przed masowym importem CERN lub dużych zbiorów elektrośmieci trzeba mierzyć:

- procent rekordów z MPN,
- procent rekordów z footprintem,
- confidence dopasowań,
- odsetek odrzuceń w review,
- czas od sugestii do zatwierdzenia,
- liczbę eksportów bez regresji ecoEDA.

### Ścieżka 5 — konwersja KiCad jako eksport, nie ingest

Nie konwertować pełnej biblioteki KiCad przed importem. Trzymać raw provenance i używać konwersji tylko wtedy, gdy generowany projekt ma trafić do konkretnej wersji KiCad lub do zewnętrznego użytkownika.

## Rekomendowany najbliższy sprint

1. Z90: human review ledger.
2. Z94: akcje Discord do review.
3. Z91: eksport ecoEDA/NSIP z provenance.
4. Z93: smoke na realnym checkout CERN albo blocker receipt.
5. Z95: pełna roadmapa autonomicznej automatyzacji AI z metrykami i rollbackiem.
