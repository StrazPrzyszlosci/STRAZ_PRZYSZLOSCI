# Pack Project13 Catalog Export 01

To jest pack dla `export chain` w `Project 13`.

Jego celem nie jest discovery ani OCR.
Jego celem jest mechaniczna, review-ready przebudowa downstream artefaktow z kanonicznego katalogu GitHub-first.

## Zakres

- execution mode: `local_agent`
- status: `smoke_tested`
- docelowy output: `pull_request`

## Rola w lancuchu

```text
reviewed catalog -> export pack -> downstream artifacts -> PR -> review
```

Pack buduje:

- `inventory.csv` dla `ecoEDA`
- `recycled_parts_seed.sql` dla `Cloudflare D1`
- `mcp_reuse_catalog.json`
- `inventree_import.jsonl`

Lokalny smoke-run przeszedl:

- `validate` i `export-all` dzialaja bez bledow,
- pipeline jest deterministyczny i idempotentny,
- status packa zostal podniesiony do `smoke_tested`, ale realny diff downstream nadal zalezy od kolejnego merge po curation.

## Najwazniejsza roznica wzgledem packa enrichment

- `enrichment` pracuje na sygnalach i kandydackich rekordach
- `export` pracuje dopiero na kanonicznym katalogu po review
- `export` nie powinien byc uruchamiany na surowych wynikach Kaggle bez etapu kuracji

## Wejscie dla kolejnego agenta

Zacznij od:

1. `manifest.json`
2. `RUNBOOK.md`
3. `REVIEW_CHECKLIST.md`
4. `../CHAIN_MAP.md`
