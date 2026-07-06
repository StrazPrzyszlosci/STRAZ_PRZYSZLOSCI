# Hermes Agent — możliwości odpalenia dla Straży Przyszłości (2026-07-06)

## Wniosek operacyjny

Hermes może być pierwszym stale pracującym agentem inicjatywy, ale na start powinien działać jako **repo-builder / scout / handoff-builder**, nie jako operator świata fizycznego. Najlepsze pierwsze miejsce uruchomienia to tani VPS albo mała VM, a drugi tor to Termux/odzyskany telefon jako lekki gateway. Prywatne dane i lokalne logi powinny iść do self-host node, a publiczne niskiego ryzyka zadania można kierować do darmowych providerów.

## Co potwierdzono z bieżących źródeł

- Hermes Agent deklaruje self-improvement loop: tworzenie i poprawianie skills, pamięć, przeszukiwanie sesji oraz model użytkownika.
- Hermes ma gateway komunikatorów, cron, subagentów i backendy terminalowe: local, Docker, SSH, Singularity, Modal i Daytona.
- Hermes może działać na tanim VPS, GPU clusterze albo serverless/persistent środowiskach.
- Google Gemini API limity są per projekt i obejmują RPM, TPM oraz RPD; aktywne limity trzeba sprawdzać w AI Studio.
- Google AI Studio/Gemini API ma darmowy start i część modeli z darmowymi tokenami, ale free tier może używać danych do ulepszania produktów.
- NVIDIA NIM free tier ma limity zależne od modelu, use-case i obciążenia; forum NVIDIA wskazuje, że nie ma oficjalnego obejścia ani gwarantowanego podniesienia limitu tego samego free tieru.

## Gdzie odpalić pierwsze Hermesy

| Miejsce | Rola | Dlaczego | Ryzyko | Decyzja |
| --- | --- | --- | --- | --- |
| Tani VPS / cloud VM | `HermesRepoBuilder`, `HermesHandoffBuilder`, cron | działa stale, tani, łatwy backup | sekrety i token GitHub | najlepszy pierwszy pilot |
| Termux na odzyskanym telefonie | gateway/operator, lekkie scouty | zgodne z reuse elektrośmieci | bateria, storage, stabilność | dobry drugi pilot |
| Odzyskany mini PC + OZE | private/local worker | prywatne dane, lokalne modele | energia, awarie sprzętu | po energy ledger |
| Modal/Daytona/serverless | burst jobs | hibernacja, koszt gdy idle | vendor lock-in, sekrety | tylko jako opcja testowa |
| GPU cluster | ciężkie batch/vision | wydajność | koszt i energia | nie na start, wymaga uzasadnienia |

## Minimalny łańcuch pracy od teraz

1. `HermesProviderQuotaMonitor` — co godzinę zapisuje snapshot limitów i dostępnych providerów.
2. `HermesRepoScout` — zbiera zasoby/repozytoria i tworzy rekordy `resource_scout`.
3. `HermesHandoffBuilder` — czyta ostatni handoff i proponuje kolejne małe zadania.
4. `HermesExecutionPackGenerator` — generuje draft packa, test i rollback.
5. `HermesAuditReviewer` — sprawdza provenance, ryzyka, brak sekretnych danych i brak fizycznego wykonania.

## Provider routing

- Google AI Studio/Gemini: mocniejsze multimodalne i reasoning tasks, gdy aktywne limity projektu pozwalają.
- NVIDIA NIM: fallback albo równoległy tekstowy worker; zakładać dynamiczny limit, nie twarde 40 RPM bez pomiaru.
- Self-host recovered node: prywatne dane, lokalne logi, offline RAG, małe modele wyspecjalizowane.
- Każdy run zapisuje `model_route.json` i `quota_snapshot.json`.

## Co dodano w repo

- `agent_runtime_plans/hermes_pilot/provider_matrix.json` — macierz providerów i reguły routingu.
- `agent_runtime_plans/hermes_pilot/pilot_plan.json` — plan pilota Hermesa jako repo-builder/scout/handoff-builder.
- `agent_runtime_plans/hermes_pilot/validate_pilot.py` — walidator blokujący plan bez review gates, artifactów i blokad fizycznego wykonania.

## Następny praktyczny krok

Nie instalować jeszcze Hermesa z sekretami produkcyjnymi. Najpierw uruchomić pilota na forku lub osobnym repo-tokenie z minimalnym zakresem:

```bash
python3 agent_runtime_plans/hermes_pilot/validate_pilot.py
```

Potem operator może przygotować VPS/Termux i dodać tylko testowe sekrety: `GEMINI_API_KEY`, `NVIDIA_API_KEY`, `GITHUB_PAT` ograniczony do forka.
