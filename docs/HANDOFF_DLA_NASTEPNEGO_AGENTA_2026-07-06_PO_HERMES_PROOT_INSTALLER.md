# Handoff dla Następnego Agenta - po Hermes proot installer - 2026-07-06

## Kontekst

Użytkownik doprecyzował, że potrzebny jest **instalator Hermes Agenta w proot Termux**, w pełni skonfigurowany pod pracę dla Straży Przyszłości. Ta iteracja realizuje H1 z poprzedniego handoffu: dry-run installer packet + runbook + testy, bez zapisywania sekretów i bez uruchamiania działań wysokiego ryzyka.

## Co zrobiono

### H1 — DONE: Hermes dry-run/proot installer packet

Dodano:

- `straz-edge-installer/scripts/install-hermes-agent-proot.sh`,
- `straz-edge-installer/scripts/RUNBOOK_HERMES_AGENT_PROOT.md`,
- `tests/test_hermes_proot_installer.py`.

Instalator ma domyślny tryb `--dry-run`, który:

- nie instaluje pakietów,
- nie klonuje repozytorium,
- nie wymaga sekretów,
- wypisuje plan instalacji i wymagane artefakty.

Tryb `--install` dla Termux/proot:

- sprawdza obecność `proot-distro` i distro `debian`/`ubuntu`,
- instaluje narzędzia w proot: `git`, `python3`, `python3-venv`, `python3-pip`, `nodejs`, `npm`, `ripgrep`, `jq`, `sqlite3`, `openssh-client`,
- klonuje `https://github.com/NousResearch/hermes-agent.git`,
- tworzy `/etc/straz-hermes/hermes.env.example`,
- tworzy `/opt/straz/bin/straz-hermes-runner`,
- przygotowuje artefakty runu: `run_receipt.json`, `model_route.json`, `quota_snapshot.json`.

### Secret hygiene i blokady

Instalator **nie zapisuje prawdziwych sekretów**. Tworzy tylko template z placeholderami:

- `GEMINI_API_KEY=__SET_BY_OPERATOR__`,
- `NVIDIA_API_KEY=__SET_BY_OPERATOR__`,
- `GITHUB_PAT=__SET_BY_OPERATOR_MINIMAL_FORK_SCOPE__`.

Domyślne blokady:

- `physical_actuation`,
- `auto_merge`,
- `direct_push_main`,
- `secret_printing`,
- `unbounded_spend`.

### Aktualizacja planu pilota

Zaktualizowano `agent_runtime_plans/hermes_pilot/pilot_plan.json` o `installer_packet` wskazujący:

- ścieżkę instalatora,
- runbook,
- domyślny tryb `dry-run`,
- targety `termux_proot_debian` i `termux_proot_ubuntu`.

## Testy wykonane

```bash
python3 -m unittest tests.test_hermes_proot_installer
python3 agent_runtime_plans/hermes_pilot/validate_pilot.py
python3 -m unittest discover -s tests -p 'test_*.py'
```

## Następne zadania

### H2 — PRIORYTET 1: Provider quota monitor cell

Dodać komórkę `provider_quota_monitor`:

- czyta `agent_runtime_plans/hermes_pilot/provider_matrix.json`,
- tworzy `quota_snapshot.json`,
- odróżnia snapshot ręczny od automatycznego,
- blokuje agent chain, jeśli quota jest nieznana,
- nie zakłada stałego NVIDIA 40 RPM bez pomiaru.

Acceptance criteria:

- Brak quota snapshot blokuje uruchomienie agent chain.
- Snapshot ma pola: provider, model, rpm, tpm/rpd jeśli znane, source, checked_at, status.
- Test blokuje snapshot bez `source` i `checked_at`.

### H3 — PRIORYTET 2: Hermes first work queue

Dodać pierwszą kolejkę prac dla Hermesa:

- `repo_scout_daily`,
- `handoff_builder_after_commit`,
- `resource_scout_triage`,
- `execution_pack_draft_generator`,
- `audit_reviewer_before_pr`.

Acceptance criteria:

- Każde zadanie ma input, output, model route, artifact requirements i human control point.
- Żadne zadanie nie ma prawa auto-merge ani direct push.
- Kolejka daje się uruchomić w trybie dry-run bez sekretów.

### H4 — PRIORYTET 3: Human approval UI/command stub

Dodać minimalny format komendy/rekordu approval:

- kto zatwierdza,
- co zatwierdza,
- zakres,
- czas,
- ryzyka,
- expiry,
- rollback.

Acceptance criteria:

- Approval wygasa.
- Approval dla kodu nie zatwierdza fizycznego działania.
- Approval dla providerów nie zatwierdza zwiększania kosztów bez ledgeru.

### H5 — PRIORYTET 4: Termux Boot service stub

Dodać bezpieczny stub startu przez Termux:Boot:

- uruchamia tylko `straz-hermes-runner` w trybie kontrolnym,
- zapisuje receipt,
- nie startuje prawdziwych providerów bez `hermes.env` i approval,
- ma rollback przez usunięcie jednego pliku boot script.

## Ryzyka

- Instalator `--install` używa sieci i `apt`; testy uruchamiają tylko `--dry-run`.
- Nie uruchamiać z szerokim tokenem GitHub.
- Nie wklejać sekretów do repo ani handoffów.
- Nie podłączać Hermesa do fizycznego sterowania; to repo-builder/scout/handoff-builder.
