# Mini-Handoff: Zadanie 09 — D1 SQLite Query Cookbook

## Co zostalo zrobione

1. **Stworzono cookbook query**: `docs/D1_SQLITE_QUERY_COOKBOOK.md` z 40+ zapytaniami SQL pokrywajacymi wszystkie 11 tabel organizacji:
   - Zasoby (ResourceRecord): aktywne zasoby, po rodzaju, o wysokiej dzwigni, czekajace na review
   - Dossiers (PotentialDossier): po priorytecie, gotowe na pilot, po domenie, niskopriorytetowe
   - Luki zdolnosci (CapabilityGap): otwarte luki, blokujace dossier, gotowe na pack, podsumowanie po typie
   - Eksperymenty (Experiment): powiazane z luka, po statusie, gotowe do uruchomienia, lancuch luka->eksperyment
   - Execution Packi: po statusie, powiazane z tematem (polimorficzne), gotowe dla wolontariusza, z linkage do zasobow, podsumowanie po trybie
   - Zadania (Task): dla packa, po statusie, wolontariackie czekajace na wykonawce
   - Runy: po statusie, z czasem trwania, czekajace na review, nieudane, podsumowanie po srodowisku
   - Artefakty: czekajace na review, dla runu, po statusie review, zaakceptowane, z pelnym provenance
   - Integrity Risk Assessments: ostatnie, dla tematu, wysokie/krytyczne ryzyka, podsumowanie po poziomie
   - Approvals: ostatnie decyzje, dla artefaktu, odrzucone, podsumowanie po decyzji
   - Readiness Gates: dla tematu, niespelnione, podsumowanie po rodzaju
   - Zapytania transwersalne: pelny lancuch dossier->run, artefakt->approval->integrity, dashboard portfela, zasoby powiazane z dossier, blokady organizacji
   - Query diagnostyczne: spis tabel z liczbami, ostatnia aktualizacja, sprawdzenie FK

2. **Stworzono lekki helper**: `pipelines/org_lookup.py` z 8 komendami lookup:
   - `status-summary` — liczba rekordow we wszystkich tabelach
   - `pack-ready` — packi gotowe do uruchomienia
   - `review-queue` — artefakty czekajace na review
   - `blocked` — zablokowane elementy (gaps, failed runs, failed gates)
   - `full-chain` — pelny lancuch dossier->gap->experiment->pack->task->run
   - `integrity-high` — wysokie/krytyczne ryzyka integrity
   - `recent-approvals` — ostatnie decyzje approval
   - `fk-check` — sprawdzenie integralnosci kluczy obcych

3. **Stworzono plik zadania**: `docs/AGENTY_PODWYKONAWCZE/ZADANIE_09_D1_SQLITE_QUERY_COOKBOOK.md`

## Jakie pliki dotknieto

### Nowe
- `docs/D1_SQLITE_QUERY_COOKBOOK.md`
- `pipelines/org_lookup.py`
- `docs/AGENTY_PODWYKONAWCZE/ZADANIE_09_D1_SQLITE_QUERY_COOKBOOK.md`
- `docs/AGENTY_PODWYKONAWCZE/MINI_HANDOFF_ZADANIE_09.md`

## Co zweryfikowano

- `python3 -m py_compile pipelines/org_lookup.py` — OK
- Lokalne odpalenie helpera na bazie z zadania 01 — patrz sekcja walidacji ponizej
- `git diff --check` — OK
- Wszystkie query sa zgodne z kolumnami z migracji `0012_organization_agent_entities.sql`

## Najbardziej przydatne query

| Lookup | Kiedy uzywac |
|--------|-------------|
| `status-summary` | Szybki przeglad: ile rekordow w kazdej tabeli |
| `pack-ready` | Ktore packi mozna przydzielac wolontariuszom |
| `review-queue` | Co czeka na review maintainera |
| `blocked` | Co blokuje organizacje |
| `full-chain` | Pelny lancuch decyzyjny od dossier do runa |
| `fk-check` | Diagnostyka integralnosci bazy |

## Od czego zalezy poprawne dzialanie

- Baza musi byc zsynchronizowana przez `pipelines/sync_organization_entities_to_sqlite.py`
- Migracja `0012` musi byc zastosowana (helper nie aplikuje migracji sam)
- Query opieraja sie na kolumnach z migracji `0012`; jesli migracja sie zmieni, cookbook trzeba zaktualizowac
- Query z `json_extract()` wymagaja SQLite 3.9+ z włączonym JSON1

## Co zostalo otwarte

- **Wariant D1**: helper dziala tylko na lokalnym SQLite; nie ma wariantu dla Cloudflare D1 API (wrangler d1 execute)
- **Wiecej lookupow**: mozna dodac lookupy specyficzne dla portfela (np. porownanie projektow, ranking dzwigni)
- **Dashboard**: cookbook jest tekstowy; docelowo mozna zbudowac prosty dashboard HTML z najwazniejszymi query
- **Walidacja schematu**: query zakladaja strukture migracji 0012; nie ma automatycznego testu sprawdzajacego zgodnosc cookbooka z migracja
