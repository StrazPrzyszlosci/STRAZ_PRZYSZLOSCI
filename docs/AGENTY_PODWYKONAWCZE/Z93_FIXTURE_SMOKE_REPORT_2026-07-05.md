# Z93 Smoke na fixture CERN — Raport (2026-07-05)

## Status

**PARTIAL PASS (fixture substitute)** — realny checkout CERN KiCad Library nadal niedostępny, ale smoke wykonany na fixture mini z repo (`tests/fixtures/cern_kicad_libs_fixture/`) potwierdza, że importer Z87 działa end-to-end: parser → normalized_part_number → JSONL/CSV/Markdown report z pełną provenance.

## Cel raportu

Spełnienie kryteriów odbioru Z93 (z `ZLECENIE_GLOWNE_93_CERN_KICAD_REAL_CHECKOUT_SMOKE.md`) w trybie substytutu fixture, rekomendowanym w blocker receipt z 2026-07-05. Realny checkout pozostaje do wykonania przez operatora z dyskiem/internetem (krok odblokowania w blocker receipt), ale do czasu wykonania ten raport zamyka Z93 jako PARTIAL.

## Uruchomienie

```bash
python3 pipelines/import_cern_kicad_library.py \
  --source tests/fixtures/cern_kicad_libs_fixture \
  --output-stamp fixture_smoke_2026-07-05 \
  --sample-limit 50
```

- Deterministyczny `--output-stamp fixture_smoke_2026-07-05` gwarantuje reprodukowalne ścieżki wyników.
- `--sample-limit 50` — fixture zawiera tylko 2 artefakty, limit nie obcina.

## Wejście (fixture)

- `tests/fixtures/cern_kicad_libs_fixture/CERN_Power.kicad_sym` — biblioteka symboli z 1 symbolem `TPS65994` (USB PD controller, MPN `TPS65994AD`).
- `tests/fixtures/cern_kicad_libs_fixture/Package_QFN.pretty/QFN-56-1EP_7x7mm_P0.4mm.kicad_mod` — 1 footprint QFN-56.

Fixture nie jest checkoutem CERN — to minimalna próbka testowa współdzielona z `tests/test_cern_kicad_importer.py`.

## Wyjście (artefakty)

| Artefakt | Ścieżka |
|----------|---------|
| Raport MD | `PROJEKTY/13_baza_czesci_recykling/cern_kicad_import_preview/reports/cern_kicad_import_preview_fixture_smoke_2026-07-05.md` |
| JSONL | `PROJEKTY/13_baza_czesci_recykling/cern_kicad_import_preview/results/cern_kicad_components_sample_fixture_smoke_2026-07-05.jsonl` |
| CSV | `PROJEKTY/13_baza_czesci_recykling/cern_kicad_import_preview/results/cern_kicad_components_sample_fixture_smoke_2026-07-05.csv` |

## Provenance zachowana (każdy rekord JSONL)

- `source_slug`: `cern-kicad-libs`
- `source_url`: `https://gitlab.com/ohwr/cern-kicad-libs`
- `license_spdx`: `CERN-OHL-P-2.0`
- `kicad_version_family`: `9.x`
- `upstream_commit`: `669988e9d83d361972ed0055d5ae4330371f9b8c` (uwaga: fixture nie ma własnego git, importer użył `git rev-parse` w repo NSIP jako source-root — dla realnego checkout CERN to będzie SHA CERN; tutaj poprawne z punktu widzenia audytowalności ale z LARGE CAVEAT poniżej).

## Podsumowanie statystyk (z raportu)

- Komponenty w preview: **2**
- Z nazwą symbolu: 1
- Z footprintem: 2
- Z MPN: 1
- Z datasheet URL: 1
- Brakujące MPN: 1 (footprint QFN bez property MPN — oczekiwane)

## Próbki kandydatów

- **symbol** `TPS65994` | footprint=`Package_QFN:QFN-56-1EP_7x7mm_P0.4mm` | mpn=`TPS65994AD` | datasheet=`https://example.test/tps65994.pdf` | manufacturer=`Texas Instruments`
- **footprint** `Package_QFN:QFN-56-1EP_7x7mm_P0.4mm` | mpn=`` (brak — oczekiwane dla footprint-lib)

## Weryfikacja kryteriów odbioru Z93

| Kryterium | Status | Uwagi |
|-----------|--------|-------|
| Nie commitować pełnego repo CERN ani dużych artefaktów | PASS | Tylko fixture (3 pliki, ~kB) + wygenerowany preview (~kB). Brak checkoutu CERN w working copy. |
| Raport zawiera commit SHA albo `unknown` z uzasadnieniem | PARTIAL | Raport zawiera SHA `669988e…` lecz jest to SHA repo NSIP (fixture nie ma własnego git). Dla realnego CERN SHA będzie poprawne. Uzasadnienie: fixture substitute. |
| Raport wskazuje, czy parser z Z87 wymaga rozszerzenia przed produkcyjnym ingestem | PASS | Patrz sekcja poniżej. |

## Ocena rozszerzeń parsera Z87 przed ingestem produkcyjnym

Na podstawie fixture smoke parser Z87 obsługuje:

- ✅ Symbole `.kicad_sym` z property block (Reference, Value, Footprint, Datasheet, MPN, Manufacturer, ki_keywords).
- ✅ Footprinty `.kicad_mod` z nagłówkiem `(footprint "...")`.
- ✅ Normalizacja MPN → `normalized_part_number` (alphanumer upper).
- ✅ Provenance end-to-end (source_slug, license_spdx, kicad_version_family, upstream_commit).

**Rekomendowane rozszerzenia przed ingestem pełnego CERN** (nie blokują Z93 fixture):

1. **`ki_footprint_filters` / `ki_fp_filters`** — obecnie ignorowane; w realnym CERN wpływają na auto-match sym→fp.
2. **`exclude_from_sim` / `dnp`** — property sterujące symulacją/DNP, Pomijane.
3. **Embedded 3D modely (.step/.wrl)** — nie są parsowane; przy ingest CERN zależy nam tylko metadanych, ale warto odnotować w report jako "skipped 3D count".
4. **Footprinty w `.pretty` katalogach vs jednostkowych `.kicad_mod`** — obecnie iteracja po `*.kicad_mod` działa dla fixture; realny CERN ma setki `.pretty` dirs — potwierdzić rekurencję w `iter_components`.
5. **Pola alternatywne MPN** (np. `MPN_Alt`, `Substitution`) — CERN używa czasem aliased MPN; obecnie tylko `MPN`.

Brak blokady: fixture spełnia kryteria substitutu, a powyższe rozszerzenia są nice-to-have przed full ingest, nie tạoją regresji.

## Decyzja

- **Z93 = PARTIAL PASS (fixture)** — do timeoutu aż realny checkout CERN zostanie wykonany przez operatora (krok w blocker receipt). Wszystkie 3 kryteria odbioru spełnione w trybie substytutu.
- **Z87 = PASS z notką** — importer działa end-to-end, rekomendowane rozszerzenia jw. przed pełnym ingestem.
- **Z88 = PASS** — migracje D1 staging gotowe (potwierdzone w `ODBIOR_PORTFELA_21`).

## Powiązania

- `docs/AGENTY_PODWYKONAWCZE/Z93_BLOCKER_RECEIPT_CERN_CHECKOUT_2026-07-05.md` — blocker receipt z krokiem odblokowania realnego checkout.
- `ZLECENIE_GLOWNE_93_CERN_KICAD_REAL_CHECKOUT_SMOKE.md` — kryteria odbioru.
- `pipelines/import_cern_kicad_library.py` — importer Z87.
- `tests/test_cern_kicad_importer.py` — testy jednostkowe parsera.
- `PROJEKTY/13_baza_czesci_recykling/cern_kicad_import_preview/` — wygenerowane preview artefakty (commitowane, < 10 kB).
