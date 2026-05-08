import { parsePositiveInteger } from "./base_utils.js";

/**
 * Per-model rate limit configuration.
 * These are applied IN ADDITION to the global per-chat rate limits in telegram_ai.js.
 */

/**
 * Default per-model rate limits.
 * These match the limits shared in session (2026-05-08):
 * - Gemma 4 31B (nvidia):
 *     15 req/min, unlimited req/day, 1500 tokens/min
 * - Gemini 3.1 Flash Lite (google):
 *     15 req/min, 250K tokens/day, 500 tokens/min
 */
export const DEFAULT_MODEL_LIMITS = {
  "google/gemma-4-31b-it": {
    rpm: 15,          // requests per 5-minute window (averaged per-minute → per-5min = 75)
    rpd: null,        // unlimited per day
    tpd: null,        // tokens per day not enforced for this model
    tpm: 1500,        // tokens per minute (output tokens ≈ maxReplyChars / 4)
  },
  "gemini-3.1-flash-lite-preview": {
    rpm: 15,          // requests per 5-minute window (averaged per-minute → per-5min = 75)
    rpd: 250000,      // tokens per day (not requests!) - we approximate as ~250K token-budget per day
    tpd: 250000,      // tokens per day (tracks output token usage against this budget)
    tpm: 500,         // tokens per minute (rate limiting for token throughput)
  },
};

/**
 * Parse a model name, handling both full ("google/gemma-4-31b-it")
 * and short ("gemini-3.1-flash-lite-preview") identifiers.
 */
function normalizeModelName(model) {
  if (!model || typeof model !== "string") return "unknown";
  const normalized = model.trim().toLowerCase();
  if (normalized.includes("gemma")) {
    // Gemma 4 31B falls under the NVIDIA "other models" tier
    return "google/gemma-4-31b-it";
  }
  if (normalized.includes("gemini") || normalized.includes("flash-lite")) {
    return "gemini-3.1-flash-lite-preview";
  }
  return "unknown";
}

/**
 * Build per-model buckets from env overrides.
 * Env var keys:
 *   GOOGLE_GEMMA_RPM, GOOGLE_GEMMA_RPD, GOOGLE_GEMMA_TPD, GOOGLE_GEMMA_TPM
 *   FLASH_LITE_RPM, FLASH_LITE_RPD, FLASH_LITE_TPD, FLASH_LITE_TPM
 */
function getModelBucketsFromEnv(env, modelKey) {
  if (modelKey === "google/gemma-4-31b-it") {
    const rpm = parsePositiveInteger(env.GOOGLE_GEMMA_RPM, DEFAULT_MODEL_LIMITS[modelKey].rpm);
    const rpd = env.GOOGLE_GEMMA_RPD ? parsePositiveInteger(env.GOOGLE_GEMMA_RPD, null) : DEFAULT_MODEL_LIMITS[modelKey].rpd;
    const tpd = env.GOOGLE_GEMMA_TPD ? parsePositiveInteger(env.GOOGLE_GEMMA_TPD, null) : DEFAULT_MODEL_LIMITS[modelKey].tpd;
    const tpm = parsePositiveInteger(env.GOOGLE_GEMMA_TPM, DEFAULT_MODEL_LIMITS[modelKey].tpm);
    return { rpm, rpd: rpd || null, tpd: tpd || null, tpm: tpd || null };
  }
  if (modelKey === "gemini-3.1-flash-lite-preview") {
    const rpm = parsePositiveInteger(env.FLASH_LITE_RPM, DEFAULT_MODEL_LIMITS[modelKey].rpm);
    const rpd = env.FLASH_LITE_RPD ? parsePositiveInteger(env.FLASH_LITE_RPD, null) : DEFAULT_MODEL_LIMITS[modelKey].rpd;
    const tpd = env.FLASH_LITE_TPD ? parsePositiveInteger(env.FLASH_LITE_TPD, null) : DEFAULT_MODEL_LIMITS[modelKey].tpd;
    const tpm = parsePositiveInteger(env.FLASH_LITE_TPM, DEFAULT_MODEL_LIMITS[modelKey].tpm);
    return { rpm, rpd: rpd || null, tpd: tpd || null, tpm };
  }
  return null;
}

/**
 * Check per-model rate limit.
 * Returns { allowed: true } or { allowed: false, bucket, retry_after_seconds }.
 *
 * Does NOT track usage (just checks time-window counts against D1).
 */
export async function checkModelRateLimit(env, db, model, platform = "telegram") {
  const modelKey = normalizeModelName(model);
  if (!modelKey || modelKey === "unknown") {
    return { allowed: true, reason: "unknown_model" };
  }

  const buckets = getModelBucketsFromEnv(env, modelKey);
  if (!buckets) {
    return { allowed: true, reason: "no_limits" };
  }

  const now = Date.now();
  const nowIso = new Date(now).toISOString();
  const prefix = `${platform}:model:${modelKey}`;

  // RPM (5-minute window)
  if (buckets.rpm !== null) {
    const rpmLimit = buckets.rpm; // requests per minute, but we apply per 5min window to be practical
    const windowMs = 5 * 60 * 1000; // 5 minutes
    const limitKey = `${prefix}:5m`;
    const row = await db.prepare(
      `SELECT window_started_at, request_count FROM telegram_chat_limits WHERE limit_key = ?`
    ).bind(limitKey).first();

    let nextCount = 1;
    let windowStartedAt = nowIso;
    if (row?.window_started_at) {
      const elapsed = now - Date.parse(row.window_started_at);
      if (!Number.isNaN(elapsed) && elapsed < windowMs) {
        nextCount = Number(row.request_count || 0) + 1;
        windowStartedAt = row.window_started_at;
      }
    }

    if (nextCount > rpmLimit) {
      const retryAfterSeconds = Math.max(1, Math.ceil((Date.parse(windowStartedAt) + windowMs - now) / 1000));
      return { allowed: false, bucket: "model_5m", retry_after_seconds: retryAfterSeconds };
    }
  }

  // RPD (24-hour window)
  if (buckets.rpd !== null) {
    const windowMs = 24 * 60 * 60 * 1000;
    const limitKey = `${prefix}:1d`;
    const row = await db.prepare(
      `SELECT window_started_at, request_count FROM telegram_chat_limits WHERE limit_key = ?`
    ).bind(limitKey).first();

    let nextCount = 1;
    let windowStartedAt = nowIso;
    if (row?.window_started_at) {
      const elapsed = now - Date.parse(row.window_started_at);
      if (!Number.isNaN(elapsed) && elapsed < windowMs) {
        nextCount = Number(row.request_count || 0) + 1;
        windowStartedAt = row.window_started_at;
      }
    }

    if (nextCount > buckets.rpd) {
      const retryAfterSeconds = Math.max(1, Math.ceil((Date.parse(windowStartedAt) + windowMs - now) / 1000));
      return { allowed: false, bucket: "model_1d", retry_after_seconds: retryAfterSeconds };
    }
  }

  return { allowed: true, reason: "within_limits" };
}

/**
 * Record a model request in the rate limiter.
 * Increments the counter for the given model + platform + chat.
 */
export async function recordModelUsage(env, db, model, platform = "telegram") {
  const modelKey = normalizeModelName(model);
  if (!modelKey || modelKey === "unknown") return;

  const now = Date.now();
  const nowIso = new Date(now).toISOString();
  const prefix = `${platform}:model:${modelKey}`;

  const limitKeys = [`${prefix}:5m`, `${prefix}:1d`];
  for (const limitKey of limitKeys) {
    const row = await db.prepare(
      `SELECT window_started_at, request_count FROM telegram_chat_limits WHERE limit_key = ?`
    ).bind(limitKey).first();

    let nextCount = 1;
    let windowStartedAt = nowIso;
    if (row?.window_started_at) {
      const elapsed = now - Date.parse(row.window_started_at);
      const windowMs = limitKey.endsWith(":5m") ? 5 * 60 * 1000 : 24 * 60 * 60 * 1000;
      if (!Number.isNaN(elapsed) && elapsed < windowMs) {
        nextCount = Number(row.request_count || 0) + 1;
        windowStartedAt = row.window_started_at;
      }
    }

    await db.prepare(
      `
      INSERT INTO telegram_chat_limits (limit_key, bucket_name, window_started_at, request_count, last_request_at, platform)
      VALUES (?, ?, ?, ?, ?, ?)
      ON CONFLICT(limit_key) DO UPDATE SET
        bucket_name = excluded.bucket_name,
        window_started_at = excluded.window_started_at,
        request_count = excluded.request_count,
        last_request_at = excluded.last_request_at
      `
    ).bind(
      limitKey,
      limitKey.endsWith(":5m") ? "model_5m" : "model_1d",
      windowStartedAt,
      nextCount,
      nowIso,
      platform
    ).run();
  }
}
