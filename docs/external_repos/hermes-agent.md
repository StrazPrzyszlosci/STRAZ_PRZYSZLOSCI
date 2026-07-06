# Hermes Agent jako inspiracja dla Straży Przyszłości

Źródło: <https://github.com/nousresearch/hermes-agent>

## Dlaczego warto śledzić ten projekt

Hermes Agent jest użyteczny jako wzorzec operacyjny dla repozytorium Straży Przyszłości, bo łączy kilka elementów potrzebnych w docelowej, wieloogniwowej automatyzacji:

- jeden agent dostępny przez CLI oraz komunikatory,
- pamięć i uczenie się z poprzednich zadań,
- system umiejętności/skills jako proceduralna pamięć organizacji,
- harmonogramy cron i zadania cykliczne,
- delegowanie pracy do subagentów,
- możliwość pracy na różnych backendach wykonawczych,
- ślad rozmów, narzędzi, plików i decyzji, który można mapować na audytowalny model `task -> run -> artifact -> review -> approval`.

Nie należy kopiować Hermesa bezpośrednio do runtime krytycznego fizycznie. W Straży Przyszłości może być warstwą inspiracji i opcjonalnym agentem budującym repo, natomiast działania w świecie fizycznym muszą przechodzić przez bramki review, testy i zatwierdzenia człowieka.

## Mapowanie na architekturę Straży Przyszłości

| Wzorzec z Hermes Agent | Adaptacja w Straży Przyszłości |
| --- | --- |
| Skills / procedural memory | `ExecutionPackSkill`: małe, wersjonowane procedury pracy dla agentów i wolontariuszy. |
| Cron scheduler | Cykliczne audyty: metryki providerów, importy katalogów, walidacja queue, monitoring edge node. |
| Messaging gateway | Jeden interfejs dla Telegram/Discord/WhatsApp do zgłoszeń, review i nadzoru. |
| Subagents | Rozdzielone ogniwa: scout, verifier, curator, safety reviewer, hardware reviewer. |
| Terminal backends | Bezpieczne profile wykonawcze: local-only, container, read-only, staging, hardware-lab. |
| Conversation/session search | Pamięć organizacji: handoffy, decyzje, raporty testów, powody odrzuceń. |
| Self-improvement loop | Tylko w sandboxie: propozycje poprawy promptów, procedur i skryptów po benchmarku. |

## Rekomendowana rola w repo

1. **Hermes jako builder repo** — agent uruchamiany na VPS/Termux/desktopie, który cyklicznie czyta handoffy, generuje execution packi i otwiera PR-y.
2. **Hermes jako operator komunikatorów** — brama do małych zadań: „sprawdź czujnik”, „opisz część”, „wygeneruj raport akwaponiki”.
3. **Hermes jako warstwa pamięci proceduralnej** — każde powtarzalne zadanie powinno kończyć się propozycją skill/runbooka, ale merge wymaga review.
4. **Hermes jako inspiracja audytowa** — każdy run powinien zapisywać: wejścia, narzędzia, wersje, outputy, ryzyka, decyzje i osobę zatwierdzającą.

## Minimalny bezpieczny pilotaż

- Nie podłączać od razu do przekaźników, pomp, grzałek, mechaniki ani dozowania chemii.
- Zacząć od trybu `suggest-only`: agent analizuje dane i proponuje działania.
- Dla edge i urządzeń low-power generować tylko artefakty: konfiguracje, firmware bundles, checklisty flashowania i bench-test reports.
- Dopiero po przejściu testów można dopuścić automatyczne działania niskiego ryzyka, np. powiadomienia, backupy, etykietowanie danych.

## Ścieżki zadań dla Straży Przyszłości

- `HermesRepoScout`: cyklicznie sprawdza zewnętrzne repozytoria i aktualizuje karty inspiracji.
- `HermesHandoffBuilder`: po każdej turze przygotowuje następne zadania i bramki odbioru.
- `HermesExecutionPackGenerator`: tworzy paczki pracy dla odzysku elektrośmieci, smartfonów-edge i upraw hydro/akwaponicznych.
- `HermesAuditReviewer`: porównuje outputy automatyzacji z celami Straży Przyszłości i wykrywa brak provenance.
- `HermesEdgeOnboarding`: wzorowany na flasherach MeshCore/Meshtastic, prowadzi operatora przez wykrycie urządzenia, wybór profilu, flash, test i rejestrację w katalogu.

