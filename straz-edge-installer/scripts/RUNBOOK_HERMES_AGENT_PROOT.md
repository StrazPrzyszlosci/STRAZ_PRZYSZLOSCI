# RUNBOOK: Hermes Agent w Termux proot dla Straży Przyszłości

## Cel

Uruchomić Hermes Agent jako stale pracującego `repo-builder / scout / handoff-builder`
dla Straży Przyszłości na tanim lub odzyskanym urządzeniu, bez auto-merge, bez
direct push do `main`, bez drukowania sekretów i bez fizycznego sterowania.

## Docelowe role

- `HermesRepoScout` — wyszukuje zasoby, repozytoria i inspiracje.
- `HermesHandoffBuilder` — czyta handoffy i proponuje kolejne zadania.
- `HermesExecutionPackGenerator` — tworzy drafty paczek pracy.
- `HermesAuditReviewer` — sprawdza provenance, ryzyka i brak prywatnych danych.
- `HermesProviderQuotaMonitor` — zapisuje `quota_snapshot.json`.

## Wymagania

1. Termux z F-Droid.
2. Zainstalowany proot przez `straz-edge-installer/install.sh`.
3. Distro `debian` albo `ubuntu` w `proot-distro`.
4. Osobny `GITHUB_PAT` ograniczony do forka lub staging repo.
5. Klucze providerów dodawane ręcznie po instalacji:
   - `GEMINI_API_KEY`,
   - `NVIDIA_API_KEY`,
   - opcjonalnie `SELFHOST_AI_BASE_URL`.

## Dry-run bez sekretów

```bash
bash straz-edge-installer/scripts/install-hermes-agent-proot.sh --dry-run
```

Dry-run nie instaluje pakietów, nie klonuje repozytorium i nie zapisuje sekretów.

## Instalacja w proot

```bash
bash straz-edge-installer/scripts/install-hermes-agent-proot.sh --install --distro debian --user straz
```

Instalator:

- doinstaluje narzędzia: `git`, `python3`, `nodejs`, `npm`, `rg`, `jq`, `sqlite3`,
- sklonuje `https://github.com/NousResearch/hermes-agent.git`,
- utworzy `/etc/straz-hermes/hermes.env.example`,
- utworzy `/opt/straz/bin/straz-hermes-runner`,
- ustawi artefakty runu w `/opt/straz/logs`.

## Konfiguracja sekretów

W proot:

```bash
sudo cp /etc/straz-hermes/hermes.env.example /etc/straz-hermes/hermes.env
sudo nano /etc/straz-hermes/hermes.env
```

Nie commituj `hermes.env`. Nie wklejaj sekretów do handoffów, issue ani PR.

## Pierwsze uruchomienie kontrolne

W proot:

```bash
/opt/straz/bin/straz-hermes-runner
cat /opt/straz/logs/run_receipt.json
cat /opt/straz/logs/model_route.json
cat /opt/straz/logs/quota_snapshot.json
```

Dopiero po review można podłączyć prawdziwe zadania Hermesa.

## Rollback

W proot:

```bash
sudo rm -rf /opt/straz/hermes-agent /opt/straz/bin/straz-hermes-runner /etc/straz-hermes
```

Jeżeli usuwasz całe distro:

```bash
proot-distro remove debian
```

## Zasady bezpieczeństwa

- Token GitHub tylko do forka/staging repo.
- Brak `auto_merge` i brak `direct_push_main`.
- Brak fizycznego sterowania przez Hermesa.
- Każdy run zapisuje `run_receipt.json`, `model_route.json`, `quota_snapshot.json`.
- NVIDIA NIM i Google AI Studio wymagają bieżącego snapshotu quota; nie zakładać stałego limitu.
