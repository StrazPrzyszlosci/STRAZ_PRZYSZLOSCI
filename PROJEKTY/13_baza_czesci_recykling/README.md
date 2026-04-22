# [PROJEKT 13] GitHub-First Baza Czesci z Recyklingu

Ten projekt zamienia elektroodpady w publicznie dostepny katalog czesci dla AI, KiCada i spolecznosci. Jest to zarazem **pierwszy pilot szerszego resource scoutingu**, w ktorym automatyzacja uczy sie rozpoznawac zasoby, oceniac ich potencjal i przekladac je na kolejne zdolnosci wykonawcze. Glowna zasada jest prosta:

- `GitHub` przechowuje kanoniczna, kuratorowana baze wiedzy o urzadzeniach-dawcach, czesciach kanonicznych i relacjach donorowych.
- `Cloudflare D1` sluzy tylko jako operacyjny indeks do szybkich lookupow w Telegramie i przyszlych rekomendacji AI.
- `ecoEDA`, `Ki-nTree` i `KiCAD-MCP-Server` sa zasilane z tego samego katalogu zrodlowego.

## Zweryfikowane zalozenia

Plan jest zgodny z realnymi rolami zewnetrznych projektow:

- [`ecoEDA`](https://github.com/humancomputerintegration/ecoEDA) nie jest baza danych magazynowej. To narzedzie do KiCada, ktore generuje biblioteke z pliku `.csv`, a potem robi sugestie reuse i `Bill of Teardowns`.
- [`Ki-nTree`](https://github.com/sparkmicro/Ki-nTree) automatyzuje tworzenie czesci dla `KiCad` i `InvenTree`, korzysta z konfiguracji kategorii i mapowania parametrow, ale nie utrzymuje sam z siebie katalogu "urzadzenie -> odzyskiwane czesci".
- [`KiCAD-MCP-Server`](https://github.com/mixelpixx/KiCAD-MCP-Server) daje narzedzia MCP i zasoby projektowe dla KiCada, ale nie ma natywnego feedu z czesciami z elektroodpadow. Dlatego rekomendacje reuse trzeba podpiac jako osobny zasob albo dodatkowe narzedzie.

Wniosek: najczystsza architektura to osobny katalog donorow i czesci w tym repo, a dopiero z niego eksport do `ecoEDA`, `Ki-nTree` i warstwy MCP.

## Architektura

Przeplyw danych:

1. `Telegram / OCR / scraping forow / PDF / teardowny` dostarczaja surowe sygnaly.
2. **Automatyczne Wzbogacanie AI (Project 13/15)**: Uruchomienie agenta `pipelines/yt_parts_extractor.py`, który analizuje filmy z napraw (YouTube) i zasila bazę zweryfikowanymi częściami.
- **Dwuetapowa Weryfikacja**: Każda część musi zostać "zauważona" w kontekście filmu, a następnie "potwierdzona" na stopklatce przez niezależny model OCR (Gemma).

### Narzędzia Agentyczne

W folderze `pipelines/` znajduje się skrypt `yt_parts_extractor.py`, który realizuje proces:
1. **Analiza Multimodalna**: Pełny film trafia do Gemma 4.
2. **Precyzyjne Timestampty**: AI wskazuje momenty wystąpienia części.
3. **Weryfikacja Wizualna**: Gemma 4 31B analizuje stopklatki w celu potwierdzenia numerów seryjnych.
4. **Kolejka Społeczności**: Niepewne trafienia są publikowane z linkiem czasowym do YouTube dla ludzkiej weryfikacji.

3. Sygnaly trafiaja do kolejki kuracji i sa porzadkowane do katalogu w `data/devices.jsonl`, `data/parts_master.jsonl` oraz `data/device_parts.jsonl`.
4. Skrypt budujacy generuje artefakty:
   - `data/inventory.csv` dla `ecoEDA`
   - `data/recycled_parts_seed.sql` do zasilenia `Cloudflare D1`
   - `data/mcp_reuse_catalog.json` jako zasob do lookupow reuse po stronie MCP
   - `data/inventree_import.jsonl` jako eksport do `Ki-nTree` / `InvenTree`
5. `Cloudflare Worker` korzysta z D1 do szybkich odpowiedzi bota i logowania zgloszen.
6. `Ki-nTree` podbiera z katalogu dane o czesciach i mapuje je do KiCad/InvenTree.
7. `KiCAD-MCP-Server` moze czytac `mcp_reuse_catalog.json` albo przyszle narzedzie `query_recycled_parts`.

## Dlaczego GitHub jako source of truth

To jest wymagane nie tylko organizacyjnie, ale i technicznie:

- katalog jest publiczny, przegladalny i wersjonowany,
- zmiany mozna recenzowac przez commit / PR zamiast przepisywac dane w ciszy do prywatnej bazy,
- eksport do `ecoEDA` i D1 da sie odtworzyc z jednego zrodla,
- spolecznosc moze dokladac rekordy urzadzen i czesci bez dostepu operatorskiego do chmury.

## Project 13 jako pilot resource scoutingu

Elektroodpady nie powinny byc traktowane jako jedyny docelowy zasob calej inicjatywy. W tym projekcie sa one po prostu pierwsza dobrze rozpoznana klasa zasobow, na ktorej da sie zbudowac praktyczny loop:

- wykrywanie zasobu,
- ocena potencjalu,
- ekstrakcja wiedzy i czesci,
- kuracja katalogu,
- eksport do kolejnych procesow automatyzacji.

Jesli ten loop zadziala dla elektroodpadow, ten sam wzorzec mozna rozszerzac na inne klasy zasobow:

- darmowe zasoby obliczeniowe uruchamiane przez wolontariuszy,
- gotowe moduly i donor hardware,
- dane terenowe i dokumentacje techniczne,
- lokalne nadwyzki materialowe lub energetyczne.

W tym sensie `Project 13` jest nie tylko baza czesci, ale takze zalazkiem warstwy, w ktorej AI uczy sie **samodzielnie szukac zasobow** i porownywac, ktore z nich najlepiej oplaca sie uruchamiac.

## Struktura projektu

- `data/devices.jsonl`: kanoniczny katalog urzadzen-dawcow
- `data/parts_master.jsonl`: kanoniczny katalog czesci niezaleznych od donorow
- `data/device_parts.jsonl`: kanoniczny katalog relacji czesc -> donor
- `data/inventory.csv`: wygenerowany eksport zgodny z `ecoEDA`
- `data/recycled_parts_seed.sql`: wygenerowany seed dla `Cloudflare D1`
- `data/mcp_reuse_catalog.json`: wygenerowany katalog lookupow dla MCP
- `data/inventree_import.jsonl`: wygenerowany eksport zgodny z `Ki-nTree` / `InvenTree`
- `schemas/`: schematy rekordow katalogu
- `scripts/build_catalog_artifacts.py`: generator artefaktow z danych GitHub
- `docs/`: opis przeplywu scrapingu i kontraktu integracyjnego

## Komendy

Walidacja katalogu:

```bash
python3 PROJEKTY/13_baza_czesci_recykling/scripts/build_catalog_artifacts.py validate
```

Przebudowa wszystkich artefaktow:

```bash
python3 PROJEKTY/13_baza_czesci_recykling/scripts/build_catalog_artifacts.py export-all
```

Tylko eksport `ecoEDA`:

```bash
python3 PROJEKTY/13_baza_czesci_recykling/scripts/build_catalog_artifacts.py export-ecoeda
```

Raport markdown po runie Kaggle:

```bash
python3 PROJEKTY/13_baza_czesci_recykling/scripts/summarize_kaggle_run.py
```

Generator kanonicznych rekordow `Run` i `Artifact` po wykonaniu packa:

```bash
python3 PROJEKTY/13_baza_czesci_recykling/scripts/create_execution_records.py --help
```

Orkiestrator finalizacji realnego runu packa `Kaggle`:

```bash
python3 PROJEKTY/13_baza_czesci_recykling/scripts/finalize_execution_pack_run.py --fork-owner <twoj-login-github> --git-mode push
```

Skrypt wykonuje `rebuild`, generuje `last_run_summary.md`, zapisuje kanoniczny rekord `Run` i przygotowuje follow-up do dopiecia `Artifact` po otwarciu PR.

Deterministyczna odbudowa `inventree_import.jsonl` i `ecoEDA_inventory.csv` z `autonomous_test/results/test_db.jsonl`:

```bash
python3 PROJEKTY/13_baza_czesci_recykling/scripts/rebuild_autonomous_outputs.py
```

Skrypt zapisuje tez audit trail odrzuconych rekordow do `autonomous_test/reports/rebuild_autonomous_outputs_skipped.jsonl`.

Lokalny dry-run execution packa bez odpalania prawdziwego Kaggle runu:

```bash
python3 PROJEKTY/13_baza_czesci_recykling/scripts/dry_run_execution_pack.py
```

Tylko seed do D1:

```bash
python3 PROJEKTY/13_baza_czesci_recykling/scripts/build_catalog_artifacts.py export-d1-sql
```

Synchronizacja kolejki `queued` z Telegram/D1 do katalogu GitHub-first (dry-run):

```bash
python3 pipelines/sync_recycled_queue.py --remote --limit 25
```

Zapis zmian + przebudowa artefaktow + aktualizacja statusow D1:

```bash
python3 pipelines/sync_recycled_queue.py --remote --apply --sync-d1-status
```

Automatyczny branch + commit + push + PR:

```bash
python3 pipelines/sync_recycled_queue.py --remote --apply --git-mode pr --push --create-pr --sync-d1-status
```

## Model wolontariackich notatnikow Kaggle

Ten projekt nadaje sie bardzo dobrze do modelu rozproszonego uruchamiania notatnikow przez wolontariuszy.

Szczegolowy opis tego modelu znajduje sie tutaj:

- [Model Wolontariackich Notebookow Kaggle](docs/MODEL_WOLONTARIACKICH_NOTEBOOKOW_KAGGLE.md)

Docelowy przebieg powinien wygladac tak:

1. repozytorium publikuje autonomiczny notatnik `Kaggle` albo jego szkielet,
2. lokalny agent wolontariusza instruuje go, jak pobrac notebook i ustawic sekrety,
3. wolontariusz uruchamia notebook na swoim koncie `Kaggle`,
4. notebook wykorzystuje jego darmowe limity obliczeniowe do discovery lub enrichment,
5. wyniki sa zapisywane do forka wolontariusza,
6. z forka powstaje `PR` do glownego repozytorium,
7. dopiero po review dane przechodza do wspolnej bazy wiedzy.

To pozwala budowac realna moc obliczeniowa inicjatywy bez centralnego budzetu na GPU.

Mozemy tez traktowac `Kaggle` szerzej: nie tylko jako miejsce jednego notebooka, ale jako **darmowego dostawce zasobow dla wolontariuszy**, przez ktory beda uruchamiane cale lancuchy automatyzacji.

To rowniez jest forma `resource scoutingu`: system nie tylko przetwarza juz znane elektroodpady, ale wykrywa i aktywuje rozproszone zasoby obliczeniowe spolecznosci wtedy, gdy sa potrzebne do kolejnych etapow discovery, enrichment i kuracji.

W praktyce oznacza to, ze:

- repozytorium przygotowuje `execution packi` i notebooki dla kolejnych etapow pracy,
- agent wolontariusza prowadzi go przez uruchomienie,
- wolontariusz dostarcza inicjatywie swoj darmowy przydzial obliczeniowy,
- wynik wraca do wspolnego systemu przez fork i `PR`.

Najbardziej naturalne zastosowania tego modelu w `Project 13` to:

- autonomiczny low-cost hunting filmow i timestampow,
- OCR i weryfikacja stopklatek,
- batchowe wzbogacanie danych o datasheety,
- generowanie kandydatow do kolejki kuracji,
- eksperymenty porownawcze na roznych promptach i workflowach.

Docelowo te zadania powinny byc grupowane w osobne lancuchy:

- `discovery chain`,
- `verification chain`,
- `enrichment chain`,
- `curation chain`,
- `export chain`.

## Pierwszy realny execution pack

Pierwszy realny `KaggleNotebookPack` dla `Project 13` jest utrzymywany tutaj:

- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-kaggle-enrichment-01/manifest.json`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-kaggle-enrichment-01/RUNBOOK.md`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-kaggle-enrichment-01/PR_TEMPLATE.md`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-kaggle-enrichment-01/REVIEW_CHECKLIST.md`

Ten pack spina:

- realny notebook `youtube-databaseparts.ipynb`,
- wymagane sekrety i zasady bezpieczenstwa,
- branch na forku wolontariusza zamiast pushu do upstream,
- raport runu `autonomous_test/reports/last_run_summary.md`,
- raport rebuild i log odrzuconych rekordow dla outputow review-ready,
- automatyczne zapisanie kanonicznego `Run` record przy finalizacji notebooka,
- review-ready PR do glownego repozytorium.

## Zasady bezpieczenstwa dla notatnikow Kaggle

Ten model musi pozostac jawnie dobrowolny i bezpieczny:

- wolontariusz sam decyduje, czy chce zuzyc wlasny darmowy przydzial `Kaggle`,
- potrzebne sekrety powinny byc ustawiane na jego koncie jako `Kaggle Secrets`,
- notebook nie powinien dostawac wiekszego zakresu dostepu, niz potrzebuje,
- preferowany jest zapis do forka wolontariusza, nie bezposrednio do upstream,
- artefakty powinny byc reviewowane przed promocja do katalogu kanonicznego.

## Rekomendacje projektowe

- Marketplace i grupy spolecznosciowe warto traktowac jako strumien sygnalow, nie jako kanoniczna baze wiedzy. Do GitHub najlepiej zapisywac rekordy znormalizowane, a nie surowe ogloszenia.
- Zdjecia, OCR i wpisy z Telegrama powinny najpierw trafic do kolejki kuracji. Dopiero po potwierdzeniu warto dopisywac je do katalogu zrodlowego w repo.
- `ecoEDA` powinna dostawac wygenerowany `inventory.csv`, a nie recznie edytowany plik.
- `Ki-nTree` najlepiej traktowac jako warstwe publikacji danych o czesciach do `KiCad` i `InvenTree`, a nie jako miejsce kuracji wiedzy o donorach.
- `KiCAD-MCP-Server` powinien dostac lekki, deterministyczny zasob reuse, zamiast bezposrednio czytac rozproszone fora, PDF-y i marketplace'y.
- **Automatyczne Wzbogacanie (AI Agent):** Baza nie powinna polegać wyłącznie na zgłoszeniach użytkowników. Agent AI musi periodycznie "odpytywać" internet o każdy model w bazie, wyciągając listy części ze schematów i filmów naprawczych, co drastycznie zwiększy gęstość danych bez angażowania ludzi.
- **Autonomiczne notebooki Kaggle:** discovery i enrichment powinny miec wariant `execution pack`, w ktorym wolontariusz uruchamia gotowy notebook na swoim koncie `Kaggle`, a wynik wraca do inicjatywy przez fork i `PR`.

## Kolejny etap

Po dopieciu katalogu GitHub-first nastepny logiczny krok to automatyczna kuracja i wzbogacanie:

1. zdjecie / model / numer czesci w Telegramie,
2. zapis do kolejki w D1,
3. **AI Periodic Enrichment:** agent skanuje schematy, fora i filmy YT dla danego modelu,
4. review i scalanie danych,
5. commit lub PR do katalogu w GitHub,
6. regeneracja `ecoEDA`, D1 i zasobu MCP z jednego polecenia.
