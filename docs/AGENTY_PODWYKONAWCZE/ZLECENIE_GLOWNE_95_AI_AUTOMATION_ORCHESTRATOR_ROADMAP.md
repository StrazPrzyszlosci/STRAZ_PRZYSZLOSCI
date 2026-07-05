# ZLECENIE GŁÓWNE 95 - Roadmap autonomicznej automatyzacji AI

## Cel

Przekuć obecne repo w kontrolowany system autonomicznej automatyzacji AI: boty jako interfejs, D1/SQLite jako pamięć operacyjna, execution packs jako zadania, review ledger jako bezpiecznik.

## Zakres

- Zmapować przepływy: ingest -> staging -> AI suggestion -> human review -> export/release.
- Zdefiniować role agentów: importer, verifier, curator, reviewer, exporter, operator.
- Ustalić minimalne metryki: coverage danych, false positive rate dopasowań, czas do review, liczba rekordów zaakceptowanych.
- Zaproponować kolejkę autonomicznych zadań, które bot Discord/Telegram może inicjować bez ryzyka nadpisania danych.

## Kryteria odbioru

- Dokument roadmapy zawiera 3 horyzonty: 2 tygodnie, 6 tygodni, 3 miesiące.
- Każdy krok ma gate bezpieczeństwa i rollback.
- Rekomendacje są zgodne z zasadą: AI sugeruje, człowiek zatwierdza zmiany produkcyjne.

## Status

DONE (2026-07-05) — `docs/ROADMAPA_AUTONOMICZNEJ_AUTOMATYZACJI_AI.md` z 3 horyzontami (2tyg/6tyg/3mies), każdy krok ma gate, rollback i metrykę. Role agentów: importer/verifier/curator/reviewer/exporter/operator. Węzły edge (smartfony/proot) uwzględnione w H3 jako providery w D1.
