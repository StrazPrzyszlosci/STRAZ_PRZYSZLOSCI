# Architektura integracji CERN KiCad Library z bazą NSIP / botem Discord

Data: 2026-05-14

## Decyzja wykonawcza

Nie trzeba najpierw konwertować całej biblioteki CERN KiCad Library narzędziem KiCad Version Converter, aby zintegrować ją z bazą bota. Najbezpieczniejszy wariant to ingest źródeł KiCad 9.x do osobnych tabel staging/provenance, normalizacja metadanych i dopiero późniejsze linkowanie do `recycled_part_master` oraz warstwy ecoEDA.

Konwersję wersji KiCad należy traktować jako etap eksportu lub kompatybilności projektów, nie jako warunek importu danych do NSIP. Narzędzia typu NextPCB KiCad Version Converter są przydatne, gdy trzeba otworzyć lub przekazać projekt między wersjami KiCad, ale nie powinny być pierwszym krokiem masowego importu biblioteki do bazy wiedzy.

## Uzasadnienie

- Aktualna baza NSIP ma już pola kompatybilne z KiCad/ecoEDA: `kicad_symbol`, `kicad_footprint`, `kicad_reference`, `parameters`, `datasheet_url` oraz `package` w `recycled_part_master`.
- Biblioteka CERN jest profesjonalnym źródłem symboli i footprintów, więc powinna wejść do NSIP jako źródło referencyjne z pełnym provenance: repo URL, commit SHA, ścieżka pliku, typ artefaktu, licencja, wersja KiCad i data ingestu.
- Masowa konwersja przed importem grozi utratą informacji źródłowej i utrudnia późniejszy diff po aktualizacjach upstream.
- Bot Discord i Telegram powinny korzystać z tej samej warstwy zapytań: najpierw szukanie w NSIP/recycled, potem lookup w `kicad_library_components`, potem sugestia linkowania do istniejącego rekordu lub utworzenia nowego rekordu master.

## Proponowany model danych

### Tabele staging/provenance

1. `kicad_library_sources`
   - `id`
   - `source_slug` (`cern-kicad-libs`)
   - `source_url`
   - `license_spdx` (`CERN-OHL-P-2.0` dla wariantu permissive)
   - `upstream_commit`
   - `kicad_version_family` (`9.x`)
   - `ingested_at`
   - `raw_manifest_json`

2. `kicad_library_components`
   - `id`
   - `source_id`
   - `library_name`
   - `symbol_name`
   - `footprint_name`
   - `reference_prefix`
   - `description`
   - `keywords`
   - `manufacturer`
   - `mpn`
   - `datasheet_url`
   - `package`
   - `normalized_part_number`
   - `raw_symbol_path`
   - `raw_footprint_path`
   - `raw_metadata_json`

3. `recycled_part_kicad_links`
   - `id`
   - `master_part_id`
   - `kicad_component_id`
   - `match_type` (`exact_mpn`, `normalized_part_number`, `manual`, `ai_suggested`)
   - `confidence`
   - `review_status` (`suggested`, `approved`, `rejected`)
   - `reviewed_by`
   - `created_at`
   - `reviewed_at`

## Integracja z botem Discord

Minimalny przepływ UX:

1. Użytkownik pyta: `!part TPS65994` albo wybiera przycisk „Szukaj w Katalogu”.
2. Bot sprawdza `recycled_part_master`.
3. Jeśli brak lub brak footprintu, bot sprawdza `kicad_library_components`.
4. Bot zwraca krótką odpowiedź: część, symbol, footprint, źródło, pewność dopasowania i status licencji.
5. Jeśli dopasowanie jest niepewne, bot dodaje przyciski: `Zaproponuj link`, `Wyślij do review`, `Odrzuć`.
6. Po akceptacji człowieka bot zapisuje link w `recycled_part_kicad_links` i może uzupełnić pola `kicad_symbol`, `kicad_footprint`, `kicad_reference` w `recycled_part_master`.

## KiCad Version Converter — kiedy używać

Używać dopiero wtedy, gdy:

- generujemy projekt KiCad dla użytkownika w wersji innej niż źródłowa;
- importujemy stare projekty KiCad 5/6/7 do nowego workflow;
- klient lub wolontariusz musi otworzyć plik w starszej wersji KiCad;
- test eksportu pokazuje realny konflikt formatów.

Nie używać jako pierwszego kroku do bazy, bo NSIP potrzebuje metadanych, indeksów, provenance i kontroli jakości, a nie tylko plików po transformacji wersji.

## Rekomendowany następny krok

Najlepszy następny krok: przygotować mały, audytowalny importer `pipelines/import_cern_kicad_library.py` w trybie dry-run, który pobierze albo przyjmie lokalny checkout repo CERN, sparsuje ograniczoną próbkę symboli/footprintów, zapisze CSV/JSONL staging oraz wygeneruje raport: liczba komponentów, pola wykryte, braki metadanych, kandydaci do dopasowania z `recycled_part_master`.

Dopiero po takim raporcie należy dodawać migracje D1/SQLite i komendy bota, ponieważ wtedy znamy realny kształt danych z repo, a nie tylko deklarowany format.

## Ryzyka i blokady

- Licencja CERN OHL Permissive musi być przenoszona w provenance i pokazywana w eksporcie.
- Wiele symboli/footprintów może nie mieć jednoznacznego MPN; dopasowanie automatyczne musi mieć status `suggested`, nie `approved`.
- KiCad 10.x może zmienić format lub wymagania walidacyjne; zachowujemy `kicad_version_family` i raw path, aby później odtworzyć konwersję.
- Nie wolno nadpisywać istniejących pól ecoEDA/NSIP bez ledgeru decyzji człowieka.
