# Handoff dla Następnego Agenta - odbiór Portfela 20 i start Portfela 21 - 2026-05-14

## Co zrobiono w tej sesji

1. Odebrano poprzednie zadania Z81-Z83 i plan CERN KiCad.
2. Wykryto słabość odbiorową: dwa testy 413 replikowały lokalnie starą logikę zamiast importować funkcje produkcyjne.
3. Poprawiono testy tak, aby sprawdzały realny kod:
   - `tests/discord_api_handler_413_and_timing_safe_test.mjs` importuje `timingSafeEqualString()` oraz `checkDiscordPayloadSize()` z kodu produkcyjnego.
   - `tests/telegram_issues_413_test.mjs` importuje `checkTelegramPayloadSize()` z kodu produkcyjnego.
4. Dodano dokument odbioru: `docs/AGENTY_PODWYKONAWCZE/ODBIOR_PORTFELA_20_ZADAN_Z81_Z83_2026-05-14.md`.
5. Rozpisano zadania Z87-Z92 jako osobne zlecenia główne.
6. Utworzono następny portfel: `docs/AGENTY_PODWYKONAWCZE/PORTFEL_21_ZLECEN_DLA_PODWYKONAWCOW_2026-05-14.md`.

## Testy wykonane

```bash
node --test tests/discord_api_handler_413_and_timing_safe_test.mjs tests/telegram_issues_413_test.mjs tests/payload_size_shared_test.mjs tests/worker_security_headers_test.mjs
```

Wynik: 45 testów PASS, 0 FAIL.

## Stan decyzji CERN KiCad

Decyzja pozostaje bez zmian: nie konwertować całej biblioteki CERN przed importem. Najpierw staging/provenance i dry-run importer. Konwersja KiCad Version Converter albo `kicad-cli` dopiero jako etap eksportu lub kompatybilności projektu.

## Najlepszy następny krok

Zacząć od Z87: `pipelines/import_cern_kicad_library.py` w trybie dry-run z mini-fixture. Nie pobierać pełnej biblioteki w teście. Raport dry-run ma odpowiedzieć, jakie pola realnie da się sparsować i jakie są kandydaty do dopasowania z `recycled_part_master`.

## Pliki zmienione/dodane

- `tests/discord_api_handler_413_and_timing_safe_test.mjs`
- `tests/telegram_issues_413_test.mjs`
- `docs/AGENTY_PODWYKONAWCZE/ODBIOR_PORTFELA_20_ZADAN_Z81_Z83_2026-05-14.md`
- `docs/AGENTY_PODWYKONAWCZE/ZLECENIE_GLOWNE_87_CERN_KICAD_DRY_RUN_IMPORTER.md`
- `docs/AGENTY_PODWYKONAWCZE/ZLECENIE_GLOWNE_88_KICAD_STAGING_MIGRATIONS.md`
- `docs/AGENTY_PODWYKONAWCZE/ZLECENIE_GLOWNE_89_DISCORD_TELEGRAM_KICAD_LOOKUP.md`
- `docs/AGENTY_PODWYKONAWCZE/ZLECENIE_GLOWNE_90_KICAD_HUMAN_REVIEW_LEDGER.md`
- `docs/AGENTY_PODWYKONAWCZE/ZLECENIE_GLOWNE_91_ECOEDA_EXPORT_WITH_CERN_PROVENANCE.md`
- `docs/AGENTY_PODWYKONAWCZE/ZLECENIE_GLOWNE_92_KICAD_VERSION_CONVERSION_EXPORT_POLICY.md`
- `docs/AGENTY_PODWYKONAWCZE/PORTFEL_21_ZLECEN_DLA_PODWYKONAWCOW_2026-05-14.md`
