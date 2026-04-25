# Mini-Handoff Zadanie 21

## Co zostalo zrobione

Utworzono schema baseline i walidator dla design brief packa `pack-project13-blueprint-design-01`:

- JSON schema baseline `design_brief.schema.json` z 16 polami wymaganymi i 14 opcjonalnymi
- Python walidator `validate_design_brief.py` parsujacy markdown tables i sprawdzajacy required fields, enum constraints, placeholder rejection
- Aktualizacja `manifest.json` z sekcja `brief_validation` dokumentujaca metode, komendy i kontrakt
- Aktualizacja `RUNBOOK.md` z instrukcja walidacji briefu przed startem packa

## Jakie pliki dotknieto

- `PROJEKTY/13_baza_czesci_recykling/schemas/design_brief.schema.json` (nowy)
- `PROJEKTY/13_baza_czesci_recykling/scripts/validate_design_brief.py` (nowy)
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-blueprint-design-01/manifest.json` (zmieniony)
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-blueprint-design-01/RUNBOOK.md` (zmieniony)

## Jak walidowac sample brief

```bash
python3 PROJEKTY/13_baza_czesci_recykling/scripts/validate_design_brief.py PROJEKTY/13_baza_czesci_recykling/docs/SAMPLE_DESIGN_BRIEF_WIFI_TEMP_SENSOR.md
```

Wynik: `PASS` — sample brief spelnia wymagania schema baseline.

Dodatkowe komendy walidacyjne wykonane:
- `python3 -m py_compile` — brak bledow skladni
- `git diff --check` — brak bledow whitespace
- parsowanie `manifest.json` — poprawny JSON

## Jakie walidator sprawdza

1. Obecnosc i niepustosc 16 pol `[WYMAGANE]` z szablonu
2. Enum constraints: `operating_environment` (5 wartosci), `reuse_priority` (2 wartosci)
3. Odrzucenie placeholderow: `__DO_UZUPELNIENIA__`, `TBD`, `TODO` na wymaganych polach
4. Wsparcie dla wejscia markdown (parsowanie tabel) i JSON (bezposrednia walidacja schema)

## Czego nadal brakuje przed execution surface `blueprint-design-01`

- Sam execution surface (`generate_blueprint.py`) nie istnieje — pack jest nadal `draft`
- Walidator nie sprawdza `part_slug` wzgledem `data/parts_master.jsonl` — to zalezy od decyzji, czy walidacja katalogu ma byc automatyczna czy reczna (patrz mini-handoff zadania 14)
- Gestosc `parts_master.jsonl` jest nadal zbyt mala (4 rekordy) dla realnego BOM
- Nie dodano formalnego `jsonschema` jako hard dependency — walidator dziala z i bez tej biblioteki (fallback do manualnej sprawdki required fields)
- Pola w sekcji 6 (Reuse parts) nie sa walidowane bo sa w formacie tabeli listowej, a nie pojedynczych pol — wymagalnosc tych sekcji jest konceptualna (czy brief w ogole ma czesci reuse), a nie per-wiersz
