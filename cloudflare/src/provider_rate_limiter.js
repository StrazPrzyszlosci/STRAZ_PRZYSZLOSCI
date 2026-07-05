import { parsePositiveInteger } from "./base_utils.js";

/**
 * Provider rate limiter (token bucket per provider_id).
 * Uzupełnia global_rate_limiter.js — osobny limit per edge provider, tak aby
 * jeden węzeł nie zdominował dziennego budgetu. Współdzieli tabelę
 * telegram_chat_limits z prefiksem `pr:`.
 *
 * Klucz:  pr:{provider_id}:1m
 *
 * Fail-open po błędzie D1 (errors logowane, request przepuszczony) — providers
 * nie mogą zostać odcięci tylko dlatego, że limit-tabela uległa regresji.
 */

const WINDOW_MS = 60 * 1000;

async function runSql(db, sql) {
  const stmt = await db.prepare(sql);
  return await stmt.run();
}

async function getTableColumns(db, tableName) {
  const result = await db.prepare(`PRAGMA table_info(${tableName})`).all();
  return new Set((result?.results || []).map((row) => row.name));
}

async function ensureColumn(db, tableName, columnName, columnDefinition) {
  const columns = await getTableColumns(db, tableName);
  if (!columns.has(columnName)) {
    await runSql(db, `ALTER TABLE ${tableName} ADD COLUMN ${columnDefinition}`);
  }
}

export async function ensureProviderRateLimitSchema(db) {
  await runSql(
    db,
    `
    CREATE TABLE IF NOT EXISTS telegram_chat_limits (
      limit_key TEXT PRIMARY KEY,
      bucket_name TEXT NOT NULL,
      window_started_at TEXT NOT NULL,
      request_count INTEGER NOT NULL DEFAULT 0,
      last_request_at TEXT NOT NULL,
      platform TEXT NOT NULL DEFAULT 'telegram'
    )
    `
  );
  await ensureColumn(db, "telegram_chat_limits", "bucket_name", "bucket_name TEXT");
  await ensureColumn(db, "telegram_chat_limits", "window_started_at", "window_started_at TEXT");
  await ensureColumn(db, "telegram_chat_limits", "request_count", "request_count INTEGER NOT NULL DEFAULT 0");
  await ensureColumn(db, "telegram_chat_limits", "last_request_at", "last_request_at TEXT");
  await ensureColumn(db, "telegram_chat_limits", "platform", "platform TEXT NOT NULL DEFAULT 'telegram'");
}

/**
 * Sprawdza czy provider moze przetworzyc zapytanie w aktualnym oknie 1m.
 * @returns {{ allowed: true } | { allowed: false, reason: string, retry_after_seconds: number, limit: number, current: number }}
 */
export async function checkProviderRateLimit(env, providerId) {
  const db = env.DB;
  if (!db) return { allowed: true, reason: "no_db" };
  if (!providerId) return { allowed: true, reason: "no_provider_id" };

  const rawValue = env.PROVIDER_MAX_RPM;
  const parsedRaw = Number.parseInt(rawValue, 10);
  // 0 lub wartość ujemna = wyłączony limit (fail-open / allow-all).
  if (Number.isFinite(parsedRaw) && parsedRaw <= 0) return { allowed: true, reason: "disabled" };
  const maxPerProvider = parsePositiveInteger(rawValue, 30);

  try {
    return await checkProviderRateLimitWithDb(env, db, providerId, maxPerProvider);
  } catch (error) {
    console.error("[provider_rate_limiter] D1 check failed; allowing request:", error);
    return {
      allowed: true,
      reason: "db_error",
      error: error instanceof Error ? error.message : String(error),
    };
  }
}

async function checkProviderRateLimitWithDb(env, db, providerId, maxPerProvider) {
  await ensureProviderRateLimitSchema(db);

  const now = Date.now();
  const nowIso = new Date(now).toISOString();
  const limitKey = `pr:${providerId}:1m`;

  const result = await db
    .prepare(`SELECT window_started_at, request_count FROM telegram_chat_limits WHERE limit_key = ?`)
    .bind(limitKey)
    .first();

  let next = 1;
  let windowStartedAt = nowIso;
  if (result?.window_started_at) {
    const elapsed = now - Date.parse(result.window_started_at);
    if (!Number.isNaN(elapsed) && elapsed < WINDOW_MS) {
      next = Number(result.request_count || 0) + 1;
      windowStartedAt = result.window_started_at;
    }
  }

  if (next > maxPerProvider) {
    return {
      allowed: false,
      reason: "rate_limited_provider",
      retry_after_seconds: 60,
      limit: maxPerProvider,
      current: next - 1,
    };
  }

  await db
    .prepare(
      `INSERT INTO telegram_chat_limits (limit_key, bucket_name, window_started_at, request_count, last_request_at, platform)
       VALUES (?, ?, ?, ?, ?, ?)
       ON CONFLICT(limit_key) DO UPDATE SET
         bucket_name = excluded.bucket_name,
         window_started_at = excluded.window_started_at,
         request_count = excluded.request_count,
         last_request_at = excluded.last_request_at`
    )
    .bind(limitKey, "pr_provider_1m", windowStartedAt, next, nowIso, "provider")
    .run();

  return { allowed: true, current: next, limit: maxPerProvider };
}
