# Security Audit: Discord Bot vs Telegram Bot

## Raport z audytu bezpieczeństwa - 2026-05-06

### 1. Discord Bot (`discord_bot.mjs`)

#### Znalezione luki bezpieczeństwa:

1. **Brak walidacji Content-Type dla załączników** (WYSOKIE RYZYKO)
   - Załączniki są przekazywane do workera bez sprawdzenia rzeczywistego typu MIME
   - Odpowiedzialność za walidację jest zrzucona na worker, ale bot jej nie wymusza
   - Możliwość przesłania pliku innego typu niż deklarowany w `attachment.contentType`

2. **Brak rate limitingu / anty-spam** (ŚREDNIE RYZYKO)
   - Brak ograniczenia liczby żądań per użytkownik na poziomie bota
   - Każda wiadomość jest natychmiast przekazywana do workera
   - Potencjalna możliwość DoS poprzez masowe wysyłanie wiadomości

3. **Brak sanityzacji tekstu wejściowego** (ŚREDNIE RYZYKO)
   - `message.content` jest przekazywane bez sanityzacji HTML/JSX
   - W Discord embed description content (discord_utils.mjs:58) nie jest sanityzowany przed wstawieniem do embed
   - Potencjalne XSS w kontekście embedów jeśli worker zwraca nieprzefiltrowany tekst

4. **Brak obsługi signed interactions** (NISKIE RYZYKO)
   - W webhook handlerze nie ma weryfikacji signature Discorda (brak `X-Signature-Ed25519`)
   - W kodzie pośrednim discord_bot.mjs nie ma potrzeby tego sprawdzać (pośrednik), ale w Cloudflare worker (`discord_api_handler.js`) brakuje tego walidowania
   - To tylko lokalny pośrednik, ale warto dodać w dokumentacji

5. **Brak max rozmiaru załącznika** (ŚREDNIE RYZYKO)
   - Brak limitu rozmiaru dla `attachment.url` który jest przekazywany forwardem do workera
   - Potencjalna możliwość DoS przez bardzo duże pliki

#### Porównanie z Telegrama:

| Funkcja bezpieczeństwa | Discord Bot | Telegram Bot |
|----------------------|-------------|--------------|
| Rate limiting | ❌ Brak | ✅ Jest (`TELEGRAM_MIN_INTERVAL_SECONDS`) |
| Sanityzacja inputu | ❌ Brak | ✅ Jest (`sanitizeUserInput`) |
| Walidacja Content-Type | ❌ Brak | ✅ Jest (sprawdzanie `mime_type`) |
| Secret token weryfikacja | ✅ Jest (`X-Discord-Bot-Secret`) | ✅ Jest (`X-Telegram-Bot-Api-Secret-Token`) |
| Max rozmiar załącznika | ❌ Brak | ✅ Wymuszany przez Telegram API |
| Ed25519 signature | ❌ Brak | N/D (webhook secret zamiast) |
| Throttling per użytkownik | ❌ Brak | ✅ Jest (`telegram_issue_throttle` w DB) |

---

### 2. Telegram Bot (`telegram_issues.js`, `telegram_ai.js`)

#### Znalezione luki bezpieczeństwa:

1. **Timing attack przy secret token** (NISKIE RYZYKO)
   - `verifyTelegramSecretToken` używa zwykłego porównania stringów `===`
   - Zalecane: użyć `crypto.timingSafeEqual` do porównywania sekretów

2. **Brak limitu rozmiaru payloadu webhook** (ŚREDNIE RYZYKO)
   - Brak sprawdzania `Content-Length` lub maksymalnego rozmiaru body
   - Bardzo duży payload webhook (np. 50MB zdjęcie) może przeciążyć workera

3. **Niejawne chainowanie promisów przy fetch** (NISKIE RYZYKO)
   - `fetchTelegramFileAsBase64` nie ma timeout - może zawisnąć w przypadku braku odpowiedzi
   - Zalecane: dodać `AbortController` z timeout

4. **Brak HSTS / Strict-Transport-Security w odpowiedziach** (NISKIE RYZYKO)
   - W Cloudflare worker (`worker.js`) brakujeheader `Strict-Transport-Security`
   - `access-control-allow-origin: *` może być zbyt szerokie w produkcji

---

### 3. Cloudflare Worker (`worker.js`)

#### Wspólne luki dla Discord i Telegram:

1. **CORS z `access-control-allow-origin: *`** (WYSOKIE RYZYKO)
   ```javascript
   "access-control-allow-origin": "*"
   ```
   - Jest globalnie włączone dla WSZYSTKICH odpowiedzi z API
   - Powinno być ograniczone do znanych originów lub wyłączone w produkcji
   - Dev/staging OK, prod NIE

2. **Brak Content Security Policy (CSP)** (ŚREDNIE RYZYKO)
   - Brak CSP headers w HTTP response
   - Jeśli kiedykolwiek dodajesz web UI, to będzie problem

3. **Błąd w imporcie `generateRecommendation`** (ŚREDNIE RYZYKO - potencjalny crash)
   ```javascript
   import { generateRecommendation } from "./recommendation.js";
   ```
   - Import istnieje ale nie wszystkie używane funkcje z recommendation.js zostały zweryfikowane
   - Potencjalny `TypeError` przy obsłudze production traffic

---

### 4. Worker Backupu (`pipelines/split_d1_backup.py`)

#### Błąd workera:

Analiza kodu `split_d1_backup.py`:

```python
def split_sql(input_file, public_output, private_output):
    ...
    table_match = re.search(r'(?:CREATE TABLE|INSERT INTO|CREATE INDEX|DROP TABLE|DELETE FROM) "?([a-zA-Z0-9_]+)"?', line)
```

**Błąd: `KeyError` przy nieistniejącym matchowaniu**

Gdy `table_match` nie znajdzie pasującego wzorca, `table_match.group(1)` rzuci `AttributeError: 'NoneType' object has no attribute 'group'`.

Jednak kod obsługuje to częściowo (lines 40-43):
```python
if not current_table or (current_table not in PUBLIC_TABLES and current_table not in PRIVATE_TABLES):
    public_lines.append(line)
    private_lines.append(line)
    continue
```

Więc ta część nie powinna crashować dzięki `if not current_table`.

Ale prawdziwy problem: **brak obsługi dla `ALTER TABLE` i innych instrukcji SQL**, które używają nazw tabel bez żadnego z matchowanych prefiksów. Dodatkowo:

- Brak transaction wrapping w exportowanym SQL
- Nie ma `PRAGMA foreign_keys = OFF;` przed importem
- Potencjalna utrata foreign key constraints przy splitowaniu

---

## Podsumowanie priorytetów naprawczych

| Priorytet | Luka | Plik | Sugerowana naprawa |
|-----------|------|------|-------------------|
| Wysoki | CORS `*` w produkcji | `worker.js` | Ograniczyć CORS do znanych originów lub env var |
| Wysoki | Brak walidacji Content-Type Discord | `discord_bot.mjs` | Walidacja rzeczywistego typu pliku |
| Średni | Brak rate limiting Discord | `discord_bot.mjs` | Dodać lokalny rate limit per user_id |
| Średni | Brak sanityzacji inputu Discord | `discord_bot.mjs` | Sanityzacja przy forwardowaniu |
| Średni | Brak limitu rozmiaru payloadu Telegram | `telegram_issues.js` | Sprawdzać Content-Length lub limit body |
| Średni | Obsługa błędu split_d1_backup | `split_d1_backup.py` | Obsługa `ALTER TABLE`, transakcje, FK |
| Niski | Timing attack w Telegram | `telegram_issues.js` | Użyć `crypto.timingSafeEqual` |
| Niski | Brak HSTS w odpowiedziach | `worker.js` | Dodać Strict-Transport-Security |
