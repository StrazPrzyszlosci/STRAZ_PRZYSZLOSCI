import { parsePositiveInteger } from "./base_utils.js";

/**
 * Global API rate limiter.
 * Protects against DDoS and API abuse at the gateway level.
 * Checks: per-IP, per-API-key, per-project.
 *
 * Uses the same telegram_chat_limits table with prefixed keys:
 *   - gl:ip:{ip}:{window}     (per IP, per min)
 *   - gl:key:{apiKey}:{window} (per API key, per min)
 *   - gl:proj:{project}:{window} (per project, per min)
 */

const WINDOW_MS = 60 * 1000; // 1-minute sliding window

function getClientIp(request) {
  // Cloudflare sets CF-Connecting-IP; fallback to X-Forwarded-For
  return (
    request.headers.get("CF-Connecting-IP") ||
    request.headers.get("X-Forwarded-For") ||
    "unknown"
  );
}

function getApiKey(request) {
  return request.headers.get("X-Provider-Token") || "anonymous";
}

function getProject(env) {
  return env.DEPLOYMENT_ENVIRONMENT || "default";
}

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

export async function ensureGlobalRateLimitSchema(db) {
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

export async function checkGlobalRateLimit(request, env) {
  const db = env.DB;
  if (!db) return { allowed: true, reason: "no_db" };

  try {
    return await checkGlobalRateLimitWithDb(request, env, db);
  } catch (error) {
    console.error("[global_rate_limiter] D1 check failed; allowing request:", error);
    return {
      allowed: true,
      reason: "db_error",
      error: error instanceof Error ? error.message : String(error),
    };
  }
}

async function checkGlobalRateLimitWithDb(request, env, db) {
  await ensureGlobalRateLimitSchema(db);

  const now = Date.now();
  const nowIso = new Date(now).toISOString();

  // Configurable limits (all per minute)
  const maxPerIp = parsePositiveInteger(env.API_MAX_RPM_PER_IP, 60);
  const maxPerKey = parsePositiveInteger(env.API_MAX_RPM_PER_API_KEY, 120);
  const maxPerProject = parsePositiveInteger(env.API_MAX_RPM_PER_PROJECT, 600);

  const ip = getClientIp(request);
  const apiKey = getApiKey(request);
  const project = getProject(env);

  // Per-IP bucket
  const ipLimitKey = `gl:ip:${ip}:1m`;
  const ipResult = await db
    .prepare(`SELECT window_started_at, request_count FROM telegram_chat_limits WHERE limit_key = ?`)
    .bind(ipLimitKey)
    .first();

  let ipNext = 1;
  let ipWindowStartedAt = nowIso;
  if (ipResult?.window_started_at) {
    const elapsed = now - Date.parse(ipResult.window_started_at);
    if (!Number.isNaN(elapsed) && elapsed < WINDOW_MS) {
      ipNext = Number(ipResult.request_count || 0) + 1;
      ipWindowStartedAt = ipResult.window_started_at;
    }
  }

  if (ipNext > maxPerIp) {
    return { allowed: false, reason: "rate_limited_ip", retry_after_seconds: 60 };
  }

  // Per-API-key bucket
  const keyLimitKey = `gl:key:${apiKey}:1m`;
  const keyResult = await db
    .prepare(`SELECT window_started_at, request_count FROM telegram_chat_limits WHERE limit_key = ?`)
    .bind(keyLimitKey)
    .first();

  let keyNext = 1;
  let keyWindowStartedAt = nowIso;
  if (keyResult?.window_started_at) {
    const elapsed = now - Date.parse(keyResult.window_started_at);
    if (!Number.isNaN(elapsed) && elapsed < WINDOW_MS) {
      keyNext = Number(keyResult.request_count || 0) + 1;
      keyWindowStartedAt = keyResult.window_started_at;
    }
  }

  if (keyNext > maxPerKey) {
    return { allowed: false, reason: "rate_limited_api_key", retry_after_seconds: 60 };
  }

  // Per-project bucket
  const projLimitKey = `gl:proj:${project}:1m`;
  const projResult = await db
    .prepare(`SELECT window_started_at, request_count FROM telegram_chat_limits WHERE limit_key = ?`)
    .bind(projLimitKey)
    .first();

  let projNext = 1;
  let projWindowStartedAt = nowIso;
  if (projResult?.window_started_at) {
    const elapsed = now - Date.parse(projResult.window_started_at);
    if (!Number.isNaN(elapsed) && elapsed < WINDOW_MS) {
      projNext = Number(projResult.request_count || 0) + 1;
      projWindowStartedAt = projResult.window_started_at;
    }
  }

  if (projNext > maxPerProject) {
    return { allowed: false, reason: "rate_limited_project", retry_after_seconds: 60 };
  }

  // Record usage (upsert all three buckets)
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
    .bind(ipLimitKey, "gl_ip_1m", ipWindowStartedAt, ipNext, nowIso, "global")
    .run();

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
    .bind(keyLimitKey, "gl_key_1m", keyWindowStartedAt, keyNext, nowIso, "global")
    .run();

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
    .bind(projLimitKey, "gl_proj_1m", projWindowStartedAt, projNext, nowIso, "global")
    .run();

  return { allowed: true };
}
