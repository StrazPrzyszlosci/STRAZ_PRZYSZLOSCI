# Portfel 20 Zleceń dla Podwykonawców - Discord + CERN KiCad + NSIP - 2026-05-14

## Cel portfela

Przejście od zabezpieczeń API do integracji profesjonalnych bibliotek KiCad z bazą części NSIP oraz dopracowania bota Discord jako wspólnego interfejsu do zapytań, review i akceptacji dopasowań.

## Zadania zamknięte w bieżącej sesji

| ID | Cel | Status |
|----|-----|--------|
| Z81 | Content-Security-Policy dla API JSON | PASS |
| Z82 | Permissions-Policy dla API JSON | PASS |
| Z83 | Wspólna funkcja sprawdzania Content-Length dla webhooków | PASS |

## Nowe zadania rekomendowane

| ID | Priorytet | Zadanie | Oczekiwany rezultat |
|----|-----------|---------|---------------------|
| Z87 | high | Dry-run importer CERN KiCad Library | `pipelines/import_cern_kicad_library.py` parsuje lokalny checkout lub archiwum repo i generuje staging JSONL/CSV + raport jakości bez zapisu do D1. |
| Z88 | high | Migracje D1/SQLite dla staging KiCad | Tabele `kicad_library_sources`, `kicad_library_components`, `recycled_part_kicad_links` z indeksami po `normalized_part_number`, `mpn`, `symbol_name`, `footprint_name`. |
| Z89 | high | Lookup KiCad w botach Discord/Telegram | Wspólna funkcja lookup: najpierw `recycled_part_master`, potem staging CERN, z odpowiedzią o źródle, licencji i pewności dopasowania. |
| Z90 | medium | Human review dla linkowania CERN -> NSIP | Przyciski Discord/Telegram do statusów `suggested`, `approved`, `rejected`; brak automatycznego nadpisywania ecoEDA bez zatwierdzenia. |
| Z91 | medium | Eksport ecoEDA/NSIP z polami provenance | Eksport zachowuje dotychczasową kompatybilność ecoEDA i dodaje opcjonalne pola źródła CERN. |
| Z92 | low | Konwersja KiCad jako etap eksportu | Wrapper/runbook dla KiCad Version Converter lub `kicad-cli`, używany tylko gdy użytkownik wymaga innej wersji projektu. |

## Rekomendacja kolejności

1. Z87 — importer dry-run i raport rzeczywistego kształtu danych.
2. Z88 — dopiero po raporcie dodać migracje tabel.
3. Z89 — podłączyć lookup do bota Discord i utrzymać zgodność z Telegramem.
4. Z90 — dodać review/approval ledger.
5. Z91/Z92 — eksport i konwersja wersji jako warstwa downstream.

## Decyzja o konwersji CERN KiCad Library

Nie konwertować całej biblioteki przed integracją z bazą. Importować źródłowe KiCad 9.x do staging/provenance i zachować raw path + commit SHA. Konwersji używać dopiero dla eksportu projektów lub kompatybilności KiCad 10/legacy.
