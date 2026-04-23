# Zadanie 09: D1 SQLite Query Cookbook

## 1. Cel wykonawczy

- Przygotowac cookbook zapytan i lookupow dla warstwy D1/SQLite po tym, jak podwykonawca z zadania 01 dowiezl sync encji.

## 2. Wyzszy cel organizacji

- To zadanie zamienia sama baze i sync na realne narzedzie operacyjne dla maintainerow i agentow. Bez cookbooka baza istnieje, ale nikt nie wie, jak z niej korzystać operacyjnie.

## 3. Read First

- `docs/INSTRUKCJA_ROZWOJOWA_DLA_AGENTA.md`
- `docs/HANDOFF_DLA_NASTEPNEGO_AGENTA_2026-04-22.md`
- `docs/MAPOWANIE_ENCJI_ORGANIZACJI_DO_D1_I_SQLITE.md`
- wynik zadania 01 (`pipelines/sync_organization_entities_to_sqlite.py`, `pipelines/MINI_HANDOFF_SYNC_ORGANIZATION_ENTITIES.md`)
- `cloudflare/migrations/0012_organization_agent_entities.sql`

## 4. Write Scope

- `docs/D1_SQLITE_QUERY_COOKBOOK.md`
- `pipelines/org_lookup.py`
- `docs/AGENTY_PODWYKONAWCZE/ZADANIE_09_D1_SQLITE_QUERY_COOKBOOK.md`
- `docs/AGENTY_PODWYKONAWCZE/MINI_HANDOFF_ZADANIE_09.md`

## 5. Out Of Scope

- Zmiany w migracji `0012`
- Zmiany w skrypcie sync (`pipelines/sync_organization_entities_to_sqlite.py`)
- Zmiany w sample records
- Zmiany strategiczne poza swoim taskiem

## 6. Deliverables

- dokument cookbooka z przykladowymi zapytaniami (`docs/D1_SQLITE_QUERY_COOKBOOK.md`)
- lekki helper do uruchamiania najwazniejszych lookupow (`pipelines/org_lookup.py`)
- mini-handoff z lista najbardziej przydatnych query

## 7. Acceptance Criteria

- cookbook pokazuje, jak pytac o stan encji, packow, runow i approval
- query sa zgodne z realna migracja `0012`
- dokument przydaje sie glownego agentowi przy odbiorze i portfelowym review
- helper dziala na lokalnej bazie SQLite z wyniku zadania 01

## 8. Walidacja

- lokalne odpalenie query na bazie z zadania 01
- `python3 -m py_compile pipelines/org_lookup.py`
- `git diff --check`

## 9. Blokery i eskalacja

- Zadanie zalezy od wyniku 01. Sync istnieje i dziala — blocker nie wystapil.
- Jesli migracja 0012 uleglaby zmianie, cookbook musi byc zaktualizowany. Nie wymyslaj fikcyjnych kolumn.

## 10. Mini-handoff

Zapisz:

- jakie query dodales,
- do czego sluza,
- od czego zalezy ich poprawne dzialanie.
