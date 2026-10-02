# Runbook rotacji sekretów (hardening, T-backlog z PO_T37_T39)

Cel: żaden sekret nie żyje wiecznie. Ten runbook mówi KTO, CO i JAK rotuje,
zanim sekret wycieknie lub wygaśnie. Sekrety żyją wyłącznie w env Workera
(`npx wrangler secret put …` z katalogu `cloudflare/`); NIGDY w repo, reply
bota ani handoffie.

## 1. Inwentaryzacja sekretów (stan na 2026-10-02, z kodu `cloudflare/src/`)

| Sekret (env) | Do czego | Gdzie używany |
|---|---|---|
| `PROVIDER_TRUST_EDITOR_SECRET` | admin-auth (`X-Trust-Editor-Secret`) | `worker.js` (trust-level, agri admin) |
| Tokeny providerów (D1, per `provider_id`) | auth komórek/providerów | endpointy provider-auth |
| `GITHUB_TOKEN` / `EXECUTION_PACK_GITHUB_TOKEN` | PR/issues przez API | `execution_pack_initiator.js`, `github_issues.js`, boty |
| `GITHUB_WEBHOOK_SECRET` | HMAC webhooka PR | `worker.js` (`/v1/integrations/github/webhook`) |
| `TELEGRAM_BOT_TOKEN` | bot Telegram | `telegram_*.js` |
| `TELEGRAM_WEBHOOK_SECRET_TOKEN` | secret webhooka Telegram | `worker.js` |
| `DISCORD_BOT_SECRET` | podpisywanie interakcji Discord | `discord_api_handler.js` |
| `GEMINI_API_KEY` / `NVIDIA_API_KEY` | dostawcy AI | `ai_providers.js`, `telegram_ai.js` |
| `WHATSAPP_APP_SECRET` / `WHATSAPP_VERIFY_TOKEN` | kanał WhatsApp | `github_issues.js` |

`DISCORD_PUBLIC_KEY` to klucz publiczny (nie sekret), ale rotuje się razem z `DISCORD_BOT_SECRET`.

## 2. Procedura standardowa (każdy sekret z §1)

1. Wygeneruj nową wartość u dostawcy (GitHub settings / BotFather / Discord portal / konsola AI).
2. `cd cloudflare && npx wrangler secret put <NAZWA_ENV>` — wklej NOWĄ wartość.
3. `npx wrangler deploy` — propagacja na edge (sekrety wchodzą z deployem).
4. Zweryfikuj kanał: testowe wywołanie endpointu/bota (np. `GET /v1/agri/metrics` dla `PROVIDER_TRUST_EDITOR_SECRET`).
5. Dopiero po zielonej weryfikacji: unieważnij STARĄ wartość u dostawcy.
6. Dopisz wpis do tabeli §4 (data, kto, co, powód).

Zasada `make-before-break`: nowa wartość musi działać, zanim stara zginie.
Wyjątek: podejrzenie wycieku → sekcja 3 (najpierw kill, potem naprawa).

## 3. Procedura awaryjna (wyciek / sekret w repo / w logach)

1. Unieważnij sekret NATYCHMIAST u dostawcy (nie czekaj na deploy).
2. Wstaw nową wartość (`wrangler secret put` + `deploy`) — usługa wraca.
3. Sprawdź klucze pochodne: tokeny providerów + `GITHUB_WEBHOOK_SECRET` + `TELEGRAM_WEBHOOK_SECRET_TOKEN` (atakujący mógł je podejrzeć ruchem).
4. Zrotuj tokeny providerów endpointem `POST /v1/providers/{provider_id}/tokens/rotate` (istnieje — patrz `cloudflare/README.md`).
5. Wpisz incydent do §4 z powodem `wyciek`, powiadom operatora (kanał ludzki, nie bot).

## 4. Harmonogram i dziennik

| Data | Kto | Sekret | Powód |
|---|---|---|---|
| | | | |

- Rotacja planowa: co **90 dni** (minutnik operatora; przy expiry providerów — razem z `human_approval/expiry_report.py`).
- Rotacja na żądanie: każde podejrzenie wycieku, odejście osoby z dostępem, zmiana dostawcy.

## 5. Czego NIE robić

- Nie trzymać sekretów w `wrangler.toml`, `.dev.vars` w repo ani w handoffach.
- Nie wysyłać sekretów botem (Discord/Telegram) — obowiązuje wzór T39: placeholder `<TOKEN_Z_REJESTRACJI>`.
- Nie rotować "na żywca" bez kroku 4 z §2 (ryzyko blackoutu autopilota/agri).
