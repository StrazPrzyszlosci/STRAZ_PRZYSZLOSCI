import { parsePositiveInteger } from "./base_utils.js";

/**
 * Hardening: rate-limity zadań tła (cron `scheduled()` w workerze).
 *
 * Problem: zadania cykliczne (import KiCad, verifier, curator, pruning T31,
 * lifecycle providerów) nie mają żadnych ograniczeń tempa. Zawieszony cron
 * albo ręczne wielokrotne wywołanie potrafi podwoić obciążenie D1.
 *
 * Rozwiązanie: bramka per zadanie w stałym oknie czasowym, na istniejącej
 * tabeli `telegram_chat_limits` (klucze z prefiksem `bg:`, wzorem limitera
 * globalnego Z85 — zero nowych migracji). Przy awarii D1 bramka otwiera się
 * (fail-open, jak `checkGlobalRateLimit`), żeby cron nie stanął.
 */

const DEFAULT_WINDOW_MS = 60 * 60 * 1000; // 1h
const DEFAULT_MAX_RUNS = 6; // maks. 6 uruchomień zadania na okno

function sanitizeTaskName(taskName) {
  return String(taskName || "")
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9_]+/g, "_")
    .slice(0, 64) || "unknown_task";
}

export function backgroundLimitKey(taskName, windowStartedAtMs, windowMs) {
  const windowIndex = Math.floor(Number(windowStartedAtMs) / Number(windowMs));
  return `bg:${sanitizeTaskName(taskName)}:${windowMs}:${windowIndex}`;
}

/**
 * Czysta ocena: czy zadanie może ruszyć w tym oknie.
 * @returns {{allowed:boolean, reason:string, retry_after_seconds:number|null}}
 */
export function evaluateBackgroundAllowance(runCountInWindow, maxRuns, windowMs, nowMs, windowStartedAtMs) {
  if ((runCountInWindow || 0) < maxRuns) {
    return { allowed: true, reason: "within_budget", retry_after_seconds: null };
  }
  const windowEnd = Number(windowStartedAtMs) + Number(windowMs);
  const retryAfter = Math.max(1, Math.ceil((windowEnd - Number(nowMs)) / 1000));
  return { allowed: false, reason: "background_rate_limited", retry_after_seconds: retryAfter };
}

/**
 * Czysty gate interwałowy bez D1: minimalny odstęp między uruchomieniami.
 * @returns {{allowed:boolean, reason:string}}
 */
export function shouldRunBackgroundTask(lastRunAtMs, minIntervalMs, nowMs = Date.now()) {
  const last = Number(lastRunAtMs);
  const minInterval = Math.max(0, Number(minIntervalMs) || 0);
  if (!Number.isFinite(last) || last <= 0) return { allowed: true, reason: "never_run" };
  if (Number(nowMs) - last >= minInterval) return { allowed: true, reason: "interval_elapsed" };
  return { allowed: false, reason: "too_soon" };
}

export function resolveBackgroundTaskConfig(env, taskName) {
  const prefix = `BG_${sanitizeTaskName(taskName).toUpperCase()}_`;
  return {
    task: sanitizeTaskName(taskName),
    windowMs: parsePositiveInteger(env?.[`${prefix}WINDOW_MS`], DEFAULT_WINDOW_MS),
    maxRuns: parsePositiveInteger(env?.[`${prefix}MAX_RUNS`], DEFAULT_MAX_RUNS),
  };
}

/**
 * Bramka D1 per zadanie tła. Fail-open przy braku DB / błędzie (cron nie staje).
 */
export async function checkBackgroundTaskAllowance(db, taskName, options = {}) {
  const now = Number(options.now ?? Date.now());
  const nowIso = new Date(now).toISOString();
  const windowMs = Math.max(1000, Number(options.windowMs || DEFAULT_WINDOW_MS));
  const maxRuns = Math.max(1, Number(options.maxRuns || DEFAULT_MAX_RUNS));
  if (!db) return { allowed: true, reason: "no_db" };
  try {
    const key = backgroundLimitKey(taskName, now, windowMs);
    const row = await db
      .prepare(`SELECT window_started_at, request_count FROM telegram_chat_limits WHERE limit_key = ?`)
      .bind(key)
      .first();
    const windowStart = Math.floor(now / windowMs) * windowMs;
    const count = Number(row?.request_count || 0);
    const verdict = evaluateBackgroundAllowance(count, maxRuns, windowMs, now, windowStart);
    if (!verdict.allowed) return { ...verdict, limit_key: key };
    const next = count + 1;
    await db
      .prepare(
        `INSERT INTO telegram_chat_limits (limit_key, bucket_name, window_started_at, request_count, last_request_at, platform)
         VALUES (?, ?, ?, ?, ?, ?)
         ON CONFLICT(limit_key) DO UPDATE SET
           request_count = excluded.request_count,
           last_request_at = excluded.last_request_at`
      )
      .bind(key, `bg_${sanitizeTaskName(taskName)}`, new Date(windowStart).toISOString(), next, nowIso, "background")
      .run();
    return { allowed: true, reason: "within_budget", run_number: next, limit_key: key };
  } catch (error) {
    console.error("[background_rate_limiter] D1 check failed; allowing task:", error);
    return {
      allowed: true,
      reason: "db_error",
      error: error instanceof Error ? error.message : String(error),
    };
  }
}
