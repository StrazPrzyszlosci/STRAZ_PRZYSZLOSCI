# Cloudflare Workers: wariant wdrożeniowy `v1`

Ten katalog zawiera wariant wdrożeniowy dla centralnego API pilotażu stawu hodowlanego oparty o **Cloudflare Workers** i **D1**.

## Po co ten wariant

Ten wariant ma umożliwić szybkie wystawienie publicznego API dla providerów danych bez konieczności utrzymywania klasycznego serwera od pierwszego dnia.

To szczególnie dobrze pasuje do modelu:

- stary smartfon lub ESP32 zbiera dane,
- provider rejestruje się w centralnym API,
- obserwacje i zdarzenia trafiają do wspólnej warstwy operacyjnej,
- repozytorium przechowuje wiedzę i standard, a nie surowy strumień danych.

## Co zawiera katalog

- `wrangler.toml` — konfiguracja Worker'a,
- `src/worker.js` — implementacja endpointów API,
- `src/github_issues.js` — most `WhatsApp -> GitHub Issues`,
- `src/telegram_issues.js` — most `Telegram -> GitHub Issues`,
- `src/telegram_ai.js` — warstwa AI dla rozmowy, onboardingu i moderacji zgłoszeń Telegram,
- `src/generated_knowledge_bundle.js` — wygenerowany bundle publicznej wiedzy z repozytorium,
- `src/recommendation.js` — lekka logika rekomendacyjna,
- `migrations/0001_init.sql` — inicjalizacja bazy D1,
- `migrations/0003_telegram_ai.sql` — pamięć rozmowy, limity i audyt moderacji Telegram AI,
- `provider_smoke_test.py` — smoke test publicznego endpointu po wdrożeniu.
- `telegram_issue_smoke_test.py` — smoke test mostu `Telegram -> GitHub Issues`.
- `whatsapp_issue_smoke_test.py` — smoke test mostu `WhatsApp -> GitHub Issues`.

## Obsługiwane endpointy

```text
POST /v1/providers/register
POST /v1/providers/{provider_id}/tokens/rotate
POST /v1/observations
POST /v1/events
POST /v1/recommendations/fish-pond
GET /v1/providers/{provider_id}/status
POST /integrations/telegram/webhook
POST /integrations/telegram/webhook/{secret_path}
GET /integrations/whatsapp/webhook
POST /integrations/whatsapp/webhook
```

## Most `Telegram -> GitHub Issues`

To jest rekomendowany szybszy wariant uruchomienia kanału mobilnego, gdy nie chcesz od razu przechodzić przez konfigurację `WhatsApp Business Platform`.

Model jest prosty:

1. tworzysz bota przez `@BotFather`,
2. ustawiasz webhook do Worker'a,
3. użytkownik wysyła `Pomysl:` albo `Uwaga:`,
4. Worker zamienia to na `Issue`.

Szczegóły:

- [`docs/ARCHITEKTURA_MOSTU_TELEGRAM_GITHUB_ISSUES.md`](../docs/ARCHITEKTURA_MOSTU_TELEGRAM_GITHUB_ISSUES.md)
- [`docs/RUNBOOK_URUCHOMIENIA_TELEGRAM_ISSUES.md`](../docs/RUNBOOK_URUCHOMIENIA_TELEGRAM_ISSUES.md)

## Telegram AI: rozmowa, onboarding i moderacja zgłoszeń

Warstwa Telegram nie musi już działać wyłącznie jako prosty prefiksowy most do `Issues`.

Po włączeniu `TELEGRAM_AI_ENABLED` bot obsługuje trzy osobne tryby:

1. zwykłą rozmowę AI na podstawie publicznej wiedzy z repozytorium,
2. onboarding, który kieruje ludzi do odpowiednich materiałów i pierwszych zadań,
3. moderację i lekką redakcję zgłoszeń `Pomysl:` oraz `Uwaga:` przed utworzeniem `GitHub Issue`.

Najważniejsza zasada pozostaje bez zmian:

- `GitHub Issues` nie są onboardingiem,
- onboarding ma kierować ludzi do odpowiednich zadań,
- tylko wiadomości z prefiksem `Pomysl:` albo `Uwaga:` mogą wejść w tor tworzenia Issue.

AI korzysta wyłącznie z kuratorowanego bundle wiedzy z publicznej allowlisty plików repozytorium. Bundle jest generowany skryptem:

```bash
python3 pipelines/export_chatbot_knowledge_bundle.py
```

Wygenerowane artefakty:

- `data/chatbot/telegram_knowledge_bundle_v1.json`
- `cloudflare/src/generated_knowledge_bundle.js`

Domyślna kolejność providerów:

- primary: `AI Studio` przez `GEMINI_API_KEY`,
- fallback: `NVIDIA NIM` przez `NVIDIA_API_KEY`.

## Most `WhatsApp -> GitHub Issues`

Ten wariant może również pełnić rolę lekkiej bramki dla mobilnych zgłoszeń:

- `Pomysl: ...`
- `Uwaga: ...`
- `zastrzezenie: ...`

Model jest celowo prosty:

1. wiadomość trafia na numer `WhatsApp Business Platform`,
2. Meta wywołuje webhook Worker'a,
3. Worker rozpoznaje typ zgłoszenia,
4. Worker tworzy `Issue` w repozytorium Straży Przyszłości.

To nie jest kanał do przesyłania danych pomiarowych providera. Służy tylko do szybkiego zapisu pomysłów, uwag i ryzyk do backlogu repozytorium.

Wersja `v1` obsługuje wyłącznie wiadomości tekstowe. To dobrze pasuje do wpisywania lub dyktowania treści na smartfonie. Nie obsługujemy jeszcze automatycznej transkrypcji notatek głosowych.

Szczegóły architektoniczne opisuje dokument:

- [`docs/ARCHITEKTURA_MOSTU_WHATSAPP_GITHUB_ISSUES.md`](../docs/ARCHITEKTURA_MOSTU_WHATSAPP_GITHUB_ISSUES.md)
- [`docs/RUNBOOK_URUCHOMIENIA_WHATSAPP_ISSUES.md`](../docs/RUNBOOK_URUCHOMIENIA_WHATSAPP_ISSUES.md)

## Autoryzacja providera

Po rejestracji provider otrzymuje jednorazowo `write_token`.

Ten token należy przekazywać w nagłówku:

```text
X-Provider-Token
```

Token jest wymagany dla:

- `POST /v1/providers/{provider_id}/tokens/rotate`
- `POST /v1/observations`
- `POST /v1/events`
- `POST /v1/recommendations/fish-pond`

## Konfiguracja mostu `WhatsApp -> GitHub Issues`

Zmienne środowiskowe `v1`:

- `WHATSAPP_ISSUES_ENABLED` — włącza webhook do tworzenia `Issues`,
- `WHATSAPP_ISSUES_DRY_RUN` — tryb testowy bez realnego zapisu do GitHub,
- `WHATSAPP_ALLOWED_SENDERS` — opcjonalna lista numerów testowych rozdzielona przecinkami,
- `WHATSAPP_IDEA_LABEL` — opcjonalna etykieta dla pomysłów,
- `WHATSAPP_FEEDBACK_LABEL` — opcjonalna etykieta dla uwag,
- `WHATSAPP_CHANNEL_LABEL` — opcjonalna etykieta kanału, np. `whatsapp`,
- `GITHUB_REPO_OWNER` i `GITHUB_REPO_NAME` — repo docelowe.

Sekrety:

- `GITHUB_TOKEN` — token z prawem do tworzenia `Issues`,
- `WHATSAPP_VERIFY_TOKEN` — token weryfikacji webhooka,
- opcjonalnie `WHATSAPP_APP_SECRET` — do weryfikacji podpisu `X-Hub-Signature-256`.

Przykładowe komendy:

```bash
npx wrangler secret put GITHUB_TOKEN
npx wrangler secret put WHATSAPP_VERIFY_TOKEN
npx wrangler secret put WHATSAPP_APP_SECRET
```

W bezpiecznej wersji startowej rekomendowane jest:

- `WHATSAPP_ISSUES_ENABLED = "false"` dopóki nie ma pełnej konfiguracji,
- `WHATSAPP_ISSUES_DRY_RUN = "true"` dla pierwszych testów webhooka.

## Konfiguracja mostu `Telegram -> GitHub Issues`

Zmienne środowiskowe `v1`:

- `TELEGRAM_ISSUES_ENABLED`
- `TELEGRAM_ISSUES_DRY_RUN`
- `TELEGRAM_ALLOWED_CHAT_IDS`
- `TELEGRAM_MIN_INTERVAL_SECONDS`
- `TELEGRAM_WEBHOOK_SECRET_TOKEN`
- `TELEGRAM_WEBHOOK_PATH_SEGMENT`
- `TELEGRAM_IDEA_LABEL`
- `TELEGRAM_FEEDBACK_LABEL`
- `TELEGRAM_CHANNEL_LABEL`
- `TELEGRAM_AI_ENABLED`
- `TELEGRAM_AI_PRIMARY_PROVIDER`
- `TELEGRAM_AI_FALLBACK_PROVIDER`
- `TELEGRAM_AI_GOOGLE_MODEL`
- `TELEGRAM_AI_NVIDIA_MODEL`
- `TELEGRAM_AI_TIMEOUT_MS`
- `TELEGRAM_AI_MAX_OUTPUT_TOKENS`
- `TELEGRAM_AI_TEMPERATURE`
- `TELEGRAM_AI_MAX_REPLY_CHARS`
- `TELEGRAM_AI_REQUESTS_PER_5_MIN`
- `TELEGRAM_AI_REQUESTS_PER_DAY`
- `TELEGRAM_AI_MEMORY_MESSAGES`
- `TELEGRAM_AI_MEMORY_RETENTION_DAYS`

W bezpiecznej wersji startowej rekomendowane jest:

- `TELEGRAM_ISSUES_ENABLED = "true"` dopiero po wdrożeniu webhooka,
- `TELEGRAM_ISSUES_DRY_RUN = "true"` dla pierwszych testów,
- `TELEGRAM_AI_ENABLED = "false"` do czasu wgrania kluczy i przejścia testów,
- używanie zarówno sekretnego segmentu ścieżki, jak i `TELEGRAM_WEBHOOK_SECRET_TOKEN`.
- `TELEGRAM_MIN_INTERVAL_SECONDS = "60"` dla lekkiej ochrony przed spamem z jednego czatu albo użytkownika.

## Jak założyć numer WhatsApp

Praktyczna instrukcja krok po kroku znajduje się tutaj:

- [`docs/RUNBOOK_URUCHOMIENIA_WHATSAPP_ISSUES.md`](../docs/RUNBOOK_URUCHOMIENIA_WHATSAPP_ISSUES.md)

Najkrócej:

1. załóż aplikację w `Meta App Dashboard`,
2. wybierz use case `Connect with customers through WhatsApp`,
3. uruchom numer testowy albo dodaj własny numer,
4. dla własnego numeru wykonaj rejestrację `PHONE_NUMBER_ID/register`,
5. ustaw webhook na:

```text
https://<twoj-worker>.workers.dev/integrations/whatsapp/webhook
```

Powtórna rejestracja tego samego `provider_id` nie służy do odnowienia dostępu. Worker zwraca w takiej sytuacji `409`, a prawidłową ścieżką jest rotacja tokenu.

## Jak wdrożyć

Pełny proces operatorski jest opisany w:

- [`docs/RUNBOOK_WDROZENIA_CLOUDFLARE_D1.md`](../docs/RUNBOOK_WDROZENIA_CLOUDFLARE_D1.md)

Najkrótsza ścieżka wygląda tak:

```bash
npx wrangler d1 create fish-pond-v1 --location=weur
npx wrangler d1 migrations list DB --remote
npx wrangler d1 migrations apply DB --remote
npx wrangler deploy
python3 cloudflare/provider_smoke_test.py https://fish-pond-api-v1.<twoj-subdomain>.workers.dev --provider-environment preview
python3 cloudflare/telegram_issue_smoke_test.py https://fish-pond-api-v1.<twoj-subdomain>.workers.dev --message "Pomysl: test webhooka Telegram do Issues"
python3 cloudflare/whatsapp_issue_smoke_test.py https://fish-pond-api-v1.<twoj-subdomain>.workers.dev --message "Pomysl: test webhooka WhatsApp do Issues"
```

## Polityka środowisk providera

Worker może ograniczać, jakie `provider_id` są dopuszczone w danym środowisku przez:

- `DEPLOYMENT_ENVIRONMENT`
- `ALLOWED_PROVIDER_ENVIRONMENTS`

Przykładowa polityka:

- `preview` przyjmuje `demo,preview`
- `staging` przyjmuje `staging`
- `prod` przyjmuje `prod`

Dlatego smoke test powinien używać environment zgodnego z aktywną konfiguracją Worker'a.

## Uwaga architektoniczna

To jest warstwa operacyjna. Surowe bieżące dane providerów trafiają tutaj, a nie do repozytorium. Repozytorium pozostaje miejscem dla:

- schematów,
- adapterów,
- modeli,
- sample data,
- dokumentacji,
- wiedzy opracowanej.

## Eksport wiedzy

Zgromadzone dane operacyjne powinny być okresowo przekształcane w snapshoty wiedzy, anonimizowane raporty i przypadki opisane w repozytorium, a nie kopiowane tam w postaci pełnych dumpów.

## Utrata tokenu

W wersji `v1` odzyskiwanie dostępu bez aktualnego tokenu nie jest jeszcze zautomatyzowane. To celowo minimalny model bezpieczeństwa.

Jeżeli provider ma ważny token, powinien obrócić go przez:

```text
POST /v1/providers/{provider_id}/tokens/rotate
```

Szczegóły procesu organizacyjnego są opisane w:

- [`docs/RUNBOOK_ODZYSKIWANIA_DOSTEPU_PROVIDERA.md`](../docs/RUNBOOK_ODZYSKIWANIA_DOSTEPU_PROVIDERA.md)

## Pierwszy publiczny deployment

Pierwsze środowisko publiczne nie powinno być uznane za gotowe tylko dlatego, że `wrangler deploy` zakończył się bez błędu. Warunkiem wejścia w pracę z realnymi providerami jest przejście smoke testu end-to-end.

To samo dotyczy mostu komunikatorowego. Najpierw trzeba przejść:

1. weryfikację webhooka,
2. test `dry-run`,
3. próbę utworzenia testowego `Issue`,
4. dopiero potem wejść w realne przyjmowanie wiadomości z kanału publicznego.
