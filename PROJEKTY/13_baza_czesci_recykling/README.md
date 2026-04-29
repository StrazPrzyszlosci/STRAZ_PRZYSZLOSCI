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

Pre-flight check (uruchom przed pierwszym runem):

```bash
python3 PROJEKTY/13_baza_czesci_recykling/scripts/preflight_check.py
```

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

Skrypt wykonuje `rebuild`, generuje `last_run_summary.md`, zapisuje kanoniczny rekord `Run`, zapisuje `last_pack_run_context.json` z metadanymi do dopiecia `Artifact` i przygotowuje follow-up do dopiecia `Artifact` po otwarciu PR.

Helper do dopiecia `Artifact` po utworzeniu PR (domyslnie korzysta z `last_pack_run_context.json`):

```bash
python3 PROJEKTY/13_baza_czesci_recykling/scripts/attach_pr_artifact_record.py --pr-url https://github.com/StrazPrzyszlosci/STRAZ_PRZYSZLOSCI/pull/<numer>
```

Nie musisz podawac `--run-id` ani `--fork-owner` - helper automatycznie uzyje metadanych z `last_pack_run_context.json`.

Alternatywnie z jawnym `run-id` lub `fork-owner`:

```bash
python3 PROJEKTY/13_baza_czesci_recykling/scripts/attach_pr_artifact_record.py --run-id <run-id> --pr-url https://github.com/StrazPrzyszlosci/STRAZ_PRZYSZLOSCI/pull/<numer>
python3 PROJEKTY/13_baza_czesci_recykling/scripts/attach_pr_artifact_record.py --fork-owner <login> --pr-url https://github.com/StrazPrzyszlosci/STRAZ_PRZYSZLOSCI/pull/<numer>
```

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
- [Wolontariusze: gotowe przydzialy](../../docs/WOLONTARIUSZE_GOTOWE_PRZYDZIALY.md)

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

Mapa tych packow i ich handoff points jest utrzymywana tutaj:

- `PROJEKTY/13_baza_czesci_recykling/execution_packs/CHAIN_MAP.md`

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

## Kolejne packi w tym samym lancuchu

Poza pierwszym packiem `enrichment` projekt ma cztery kolejne packi:

- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-kaggle-verification-01/manifest.json`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-curation-01/manifest.json`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-catalog-export-01/manifest.json`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-benchmark-comparison-01/manifest.json`

Ich role sa rozdzielone celowo:

- `verification` ma obnizac ryzyko falszywych trafien i zostawiac disagreement log,
- `curation` ma formalizowac decyzje o przyjeciu kandydatow do kanonicznego katalogu z audit trail,
- `export` ma przebudowywac downstream artefakty dopiero z reviewowanego katalogu GitHub-first,
- `benchmark-comparison` ma porownywac prompty, modele i workflowy na tej samej probce danych.

Mapa zaleznosci miedzy packami znajduje sie tutaj:

- `PROJEKTY/13_baza_czesci_recykling/execution_packs/CHAIN_MAP.md`

## Planowane rozszerzenie po katalogu reuse

Po ustabilizowaniu obecnego lancucha planowane sa dwa kolejne packi:

- `pack-project13-blueprint-design-01` jako warstwa `Inzyniera AI`, ktora zamienia brief funkcjonalny i katalog reuse parts w review-ready BOM, schemat logiczny i instrukcje montazu,
- `pack-project13-esp-runtime-01` jako warstwa runtime odzyskanego hardware'u `ESP32`, ktora zamienia zatwierdzony projekt w pin map, runtime profile, skrypty i bench-ready bundle.

Minimalny plan ich operacjonalizacji znajduje sie tutaj:

- `PROJEKTY/13_baza_czesci_recykling/docs/PLAN_PACKOW_BLUEPRINT_ESP_CLAW.md`

## Jak ustawic sekrety (klucze API i tokeny)

Ten projekt wymaga trzech sekretow. Wolontariusz nie musi szukac instrukcji po internecie — ponizej znajdziesz wszystko w jednym miejscu.

Plik `.env.example` w katalogu tego projektu zawiera gotowy szablon z opisem kazdego klucza. Skopiuj go i uzupelnij:

```bash
cp PROJEKTY/13_baza_czesci_recykling/.env.example PROJEKTY/13_baza_czesci_recykling/.env
```

### 1. `GITHUB_PAT` — token pushu do forka

1. Wejdz na https://github.com/settings/tokens?type=beta (Fine-grained tokens).
2. Kliknij **Generate new token**.
3. Nadaj nazwe, np. `kaggle-pack-push`.
4. W **Repository access** wybierz **Only select repositories** i wskaz swoj fork.
5. W **Permissions > Repository permissions** ustaw **Contents: Read and write**.
6. Wygeneruj token i wklej do `.env` oraz do `Kaggle Secrets`.

Alternatywa (legacy): https://github.com/settings/tokens ze scope `repo`.

### 2. `YOUTUBE_API_KEY` — klucz do YouTube Data API v3

1. Wejdz na https://console.cloud.google.com/.
2. Utworz projekt (lub wybierz istniejacy).
3. Przejdz do **APIs & Services > Library** i wlacz **YouTube Data API v3**.
4. Przejdz do **APIs & Services > Credentials** i kliknij **Create Credentials > API key**.
5. Skopiuj klucz. Opcjonalnie ogranicz go do samego YouTube Data API v3 (**Restrict key**).

Uwaga: darmowa quota wynosi ok. 10 000 jednostek/dobe; jeden search kosztuje 100 jednostek.

### 3. `GEMINI_API_KEY` — klucz do Gemini API (analiza multimodalna, OCR)

1. Wejdz na https://aistudio.google.com/apikey.
2. Zaloguj sie kontem Google.
3. Kliknij **Create API key** albo **Get API key**.
4. Wybierz projekt Google Cloud (lub utworz nowy).
5. Skopiuj klucz.

Uwaga: darmowy tier ma limity requests/min i tokens/min — patrz https://ai.google.dev/pricing.

### Przeniesienie sekretow do Kaggle Secrets

Te same wartosci z `.env` musisz dodac rowniez w UI Kaggle:

1. Otworz swoj notebook na Kaggle.
2. W pasku bocznym kliknij ikone klucza (**Add-ons > Secrets**).
3. Dodaj trzy sekrety o nazwach dokladnie `GITHUB_PAT`, `YOUTUBE_API_KEY`, `GEMINI_API_KEY`.
4. Wartosci musza byc identyczne jak w Twoim lokalnym pliku `.env`.
5. Notebook odczyta je automatycznie przez `kaggle_secrets.UserSecretClient()`.

Szczegoly krok po kroku znajdziesz w `RUNBOOK.md` krok 3.

### Decyzje wymagajace potwierdzenia operatora

- **Weryfikacja scope `GITHUB_PAT`** — pre-flight skrypt sprawdza format tokenu, ale scope (`contents:write` albo `repo`) trzeba potwierdzic recznie na https://github.com/settings/types. Instrukcja w `VOLUNTEER_PREFLIGHT_CHECKLIST.md` sekcja 2.
- **Limity quota YouTube i Gemini** — quota nie da sie sprawdzic offline. Wolontariusz musi recznie potwierdzic dostepnosc quota w Google Cloud Console i na https://ai.google.dev/pricing. Instrukcja w `VOLUNTEER_PREFLIGHT_CHECKLIST.md` sekcje 3 i 4.

## Pre-flight check przed pierwszym runem

Zanim odpalisz notebook — lokalnie albo na Kaggle — uruchom pre-flight:

```bash
python3 PROJEKTY/13_baza_czesci_recykling/scripts/preflight_check.py
```

Skrypt sprawdzi, czy masz `.env`, obecnosc sekretow, pliki projektu i czy notebook parsuje sie poprawnie. Nie sprawdzi scope tokenu ani quota — to musisz potwierdzic recznie.

Szczegolowa checklist reczna: `PROJEKTY/13_baza_czesci_recykling/docs/VOLUNTEER_PREFLIGHT_CHECKLIST.md`.

## Canary pilot

Pierwszy wolontariusz nie robi zwyklego publicznego runu — robi **controlled canary**. Sekwencja (przed sesja, w trakcie, po sesji), stop conditions i escalation points sa opisane w:

- `PROJEKTY/13_baza_czesci_recykling/docs/CANARY_PILOT_PACKET.md`
- Decyzja maintainera `go / no-go`: `PROJEKTY/13_baza_czesci_recykling/docs/CANARY_GO_LIVE_OPERATOR_PACKET.md`
- Retro template: `PROJEKTY/13_baza_czesci_recykling/docs/CANARY_RETRO_TEMPLATE.md`

Dopiero po canary i retro otwieramy run dla szerszego krgu wolontariuszy.

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
