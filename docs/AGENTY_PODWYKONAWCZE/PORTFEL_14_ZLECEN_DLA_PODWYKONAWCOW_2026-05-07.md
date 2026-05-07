# Portfel 14 Zlecen Dla Podwykonawcow - Zadania 60-66

## Cel portfela

Domknac security hardening botow Discord i Telegram po audycie 2026-05-06 oraz przygotowac infrastrukture na finalne domkniecie Project 13.

## Zadania

| ID | Plik | Cel |
|----|------|-----|
| 60 | `ZLECENIE_GLOWNE_60_DISCORD_BOT_SECURITY_TEST_SUITE.md` | Testy jednostkowe dla `sanitizeDiscordInput()` i `checkRateLimit()` plus testy regresyjne dla walidacji zalacznikow |
| 61 | `ZLECENIE_GLOWNE_61_DISCORD_BOT_ED25519_INTEGRATION_TESTS.md` | Testy integracyjne Ed25519 signature verification w Discord handlerze (mock signed request) |
| 62 | `ZLECENIE_GLOWNE_62_DISCORD_RATE_LIMITER_LOAD_TEST.md` | Load test rate limitera Discorda: symulacja 10k+ uzytkownikow, weryfikacja cleanup mechanizmu |
| 63 | `ZLECENIE_GLOWNE_63_TELEGRAM_FETCH_TIMEOUT.md` | Dodac AbortController z timeout do `fetchTelegramFileAsBase64()` i innych fetch calls |
| 64 | `ZLECENIE_GLOWNE_64_TELEGRAM_WEBHOOK_CONTENT_LENGTH_LIMIT.md` | Dodac sprawdzanie Content-Length w Telegram webhook handlerze przed parsowaniem JSON |
| 65 | `ZLECENIE_GLOWNE_65_SPLIT_D1_BACKUP_END_TO_END_TEST.md` | Przetestowac `split_d1_backup.py` na pelnym D1 export: ALTER TABLE, FK, transakcje, edge cases |
| 66 | `ZLECENIE_GLOWNE_66_PROJECT13_HUMAN_REVIEW_FINAL_CLOSEOUT.md` | Zamknac z54: skompletowac brakujace human approvals, wypelnic `human_review_ledger.jsonl`, otworzyc export gate |

## Zasada portfela

Testy musza byc odtwarzalne bez zewnetrznych API. Ed25519 testy moga uzywac wygenerowanych kluczy testowych. Load testy moga uzywac sztucznego obciazenia w pamieci. Nie wpisywac placeholderow jako realnych decyzji.

## Pliki do utworzenia

- `docs/AGENTY_PODWYKONAWCZE/ZLECENIE_GLOWNE_60_DISCORD_BOT_SECURITY_TEST_SUITE.md`
- `docs/AGENTY_PODWYKONAWCZE/ZLECENIE_GLOWNE_61_DISCORD_BOT_ED25519_INTEGRATION_TESTS.md`
- `docs/AGENTY_PODWYKONAWCZE/ZLECENIE_GLOWNE_62_DISCORD_RATE_LIMITER_LOAD_TEST.md`
- `docs/AGENTY_PODWYKONAWCZE/ZLECENIE_GLOWNE_63_TELEGRAM_FETCH_TIMEOUT.md`
- `docs/AGENTY_PODWYKONAWCZE/ZLECENIE_GLOWNE_64_TELEGRAM_WEBHOOK_CONTENT_LENGTH_LIMIT.md`
- `docs/AGENTY_PODWYKONAWCZE/ZLECENIE_GLOWNE_65_SPLIT_D1_BACKUP_END_TO_END_TEST.md`
- `docs/AGENTY_PODWYKONAWCZE/ZLECENIE_GLOWNE_66_PROJECT13_HUMAN_REVIEW_FINAL_CLOSEOUT.md`