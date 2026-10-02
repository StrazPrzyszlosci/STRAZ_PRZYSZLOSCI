# AGENTS.md — koordynacja agentów kodujących (anty-kolizja)

Na tym repozytorium pracuje równolegle 3+ agentów kodujących.
Cel pliku: **zero kolizji, zero powielonej pracy, zero nadpisanych commitów.**
Repo jest fundamentem autonomicznych procesów robotycznych działających bez udziału człowieka, na rzecz społeczeństwa — stabilność `main` ma pierwszeństwo przed szybkością.

## 1. Złota zasada: NAJPIERW CLAIM, POTEM KOD

Żaden agent nie pisze kodu zadania, dopóki go nie zarezerwował:

1. `git pull --rebase` (lub sync worktree) + przeczytaj najnowszy handoff w `docs/HANDOFF_DLA_NASTEPNEGO_AGENTA_*` (sortuj po dacie w nazwie).
2. Sprawdź zajętość: `ls docs/AGENT_CLAIMS/` — jeśli istnieje plik `T<NN>-*.md` ze statusem `in_progress`, zadanie jest zajęte. Nie ruszaj go.
3. Zarezerwuj tworząc **NOWY plik** `docs/AGENT_CLAIMS/T<NN>-<twoja-nazwa>.md` (nigdy nie edytuj cudzego pliku claimu — to eliminuje wyścig o rejestr):

```markdown
# CLAIM T40 — <twoja-nazwa>
- Zadanie: T40 (wizualizacja diff kalibracji)
- Status: in_progress | done | abandoned
- Start: 2026-10-02
- Branch/worktree: <nazwa>
- Dotknięte pliki: <lista z tabeli w §2>
```

4. Pracuj wyłącznie w swoim branchu/worktree. Po zakończeniu: status `done` we własnym claimie + handoff wg §5 + PR (nigdy push do `main`).

## 2. Podział zadań na rozłączne obszary (stan na 2026-10-02)

T1–T39 DONE (zweryfikowane w `cloudflare/src/worker.js`). T24 (fizyczny operator: CERN S1, hardware S6, pilot półki) jest **odroczone — żaden agent kodujący go nie rusza**.

| Zadanie | Status | Właściciel obszaru plików (TYLKO te pliki) |
|---|---|---|
| T40 wizualizacja diff kalibracji (stare→nowe pasmo, tekst/MD do review PR) | OPEN | NOWE: `cloudflare/src/agri_calibration_view.js`, `tests/agri_calibration_view_test.mjs`; ODCZYT: `cloudflare/src/agri_calibration.js` |
| T41 trendy plonów (`GET /v1/agri/harvest/trends`, serie sezonowe + regresja per crop_profile) | OPEN | NOWE: `cloudflare/src/agri_harvest_trends.js`, `tests/agri_harvest_trends_test.mjs`; ODCZYT: `cloudflare/src/harvest_ledger.js` |
| T42 draft-PR z kalibracją (`!calibration apply`, flow B5/T23, `no_auto_merge`) | OPEN | `cloudflare/src/execution_pack_initiator.js`, komendy w `discord_api_handler.js` / `telegram_issues.js`, NOWY test `tests/execution_pack_calibration_test.mjs` |
| API/worker hardening (rate-limity tła, floating-IP healthcheck, secret-rotation runbook) | OPEN | NOWE pliki w `cloudflare/src/` + `docs/`; bez ruszania logiki agri |

## 3. Pliki współdzielone (worker.js, handlery bota) — reguła bloków

Trzej agenci (T40/T41/T42) mogą musieć dodać routy w `cloudflare/src/worker.js`:

- Każdy dokleja **własny blok** oznaczony markerami, np. `// === T41 harvest trends START ===` … `// === T41 harvest trends END ===`.
- **Zakaz edycji i usuwania cudzego bloku.** Konflikt markera = stop, wpis w handoffie, pytanie do operatora.
- Nowe endpointy admin-only: `X-Trust-Editor-Secret`; provider-auth: token providera. Webhooki zawsze HMAC + timing-safe.

## 4. Branche i worktree

- Jeden agent = jeden branch `codex/T<NN>-<opis>` lub własny worktree (przykład: `.kilo/worktrees/sugar-barnyard`).
- Przed startem: `git worktree list` + `git status` — nie wchodź na cudzy worktree/branch.
- `main` jest chroniony: tylko PR po review człowieka (bot nigdy nie merge'uje — `no_auto_merge`, `no_direct_push`).

## 5. Konwencje tur (z handoffów, obowiązują wszystkich)

1. Handoff: `docs/HANDOFF_DLA_NASTEPNEGO_AGENTA_<YYYY-MM-DD>_PO_T<n>_T<m>_<OPIS>.md`; pipeline liniowy, T monotonicznie, **≤5 zadań na turę**.
2. Nowa komórka ⇒ manifest w `agentic_cells/seed_cell_manifests.json` + aktualizacja `EXPECTED_CELL_IDS`/`EXPECTED_DIRS` (CI T25 blokuje).
3. Testy obowiązkowe z liczbami w handoffie: Python `python3 -m unittest discover -s tests -p 'test_*.py'` (bazowo **318 OK**) + `tests/*.mjs` (bazowo **333 pass / 0 fail**) + `node --check` dotkniętych plików + `python3 agentic_cells/validate_cell_manifest.py`.
4. High-risk / hardware / biologia = actuation gate; `physical_actuation` zabroniona; kalibracja wyłącznie suggest-only (T38) aż człowiek zmerge'uje PR.
5. Sekrety tylko w env Workera; tokeny nigdy w reply bota (wzór T39: placeholder `<TOKEN_Z_REJESTRACJI>`).
6. Każda nowa tabela D1: dedup checksum + audit event + (jeśli agregowalna) wpis w `automation_metrics`.

## 6. Gdy coś idzie nie tak

- Zadanie zablokowane >1 tury: ustaw we własnym claimie `abandoned` z powodem — zadanie wraca do puli OPEN.
- Podejrzenie kolizji (ten sam plik w dwóch claimach `in_progress`): nie koduj, dopisz sekcję do swojego handoffu i czekaj na decyzję operatora.
- Lekcja z 2026-10-02 (edit-war T40 w jednym drzewie): dwóch agentów w TYM SAMYM worktree bez claimów kończy nadpisywaniem sobie plików. Dlatego: (a) claim-first bez wyjątków, (b) NIGDY nie edytuj cudzego pliku claimu (nawet statusu), (c) nie nadpisuj cudzego modułu "lepszą wersją" — spór o API rozstrzyga operator w handoffie, kod z testami na dysku zostaje.
- Seed approvals wygasają — przed turą uruchom `python3 human_approval/validate_record.py`; przy expiry <30 dni dopisz ostrzeżenie do handoffu (lekcja z T21).
