/**
 * HARDENING — strażnik zadań tła (single-flight + minimalny interwał).
 *
 * Problem: `scheduled()` workera odpala 6 ciężkich zadań D1 (import, verify,
 * curate, lifecycle, 2× pruning z ROW_NUMBER). Nakładające się invokacje crona
 * mnożą write-rate D1 i grożą limitami globalnymi (Z85).
 *
 * Rozwiązanie: dzierżawa (lease) per zadanie w D1 — drugie wywołanie tego
 * samego zadania w oknie TTL jest pomijane (`skipped`), nie kolejkowane.
 * Fail-open: przy braku/błędzie D1 zadanie PRZEBIEGA (dostępność > oszczędność).
 */

const DEFAULT_TTL_SEC = 600;
const DEFAULT_MIN_INTERVAL_SEC = 300;

function toPositiveInt(value, fallback) {
  const n = Number(value);
  if (!Number.isFinite(n) || n <= 0) return fallback;
  return Math.floor(n);
}

export function resolveBackgroundGuardConfig(env = {}) {
  return {
    ttlSec: toPositiveInt(env.BACKGROUND_LEASE_TTL_SEC, DEFAULT_TTL_SEC),
    minIntervalSec: toPositiveInt(env.BACKGROUND_MIN_INTERVAL_SEC, DEFAULT_MIN_INTERVAL_SEC),
  };
}

export async function ensureBackgroundLeaseSchema(db) {
  await db
    .prepare(
      `CREATE TABLE IF NOT EXISTS background_leases (
        task_name TEXT PRIMARY KEY,
        locked_at TEXT NOT NULL,
        owner TEXT NOT NULL DEFAULT 'scheduled'
      )`
    )
    .run();
}

/**
 * Próba zajęcia dzierżawy. Zwraca {acquired, reason}:
 * - no_db / db_error → acquired:true (fail-open),
 * - lease_active → acquired:false (zadanie pomijane),
 * - ok → acquired:true.
 */
export async function tryAcquireBackgroundLease(db, taskName, options = {}) {
  if (!taskName || typeof taskName !== "string") {
    return { acquired: false, reason: "task_required" };
  }
  if (!db) return { acquired: true, reason: "no_db" };
  const ttlSec = toPositiveInt(options.ttlSec, DEFAULT_TTL_SEC);
  const minIntervalSec = toPositiveInt(options.minIntervalSec, DEFAULT_MIN_INTERVAL_SEC);
  const windowSec = Math.max(ttlSec, minIntervalSec);
  const nowMs = typeof options.nowMs === "number" ? options.nowMs : Date.now();
  const nowIso = new Date(nowMs).toISOString();
  const owner = options.owner || "scheduled";
  try {
    await ensureBackgroundLeaseSchema(db);
    const row = await db
      .prepare(`SELECT locked_at FROM background_leases WHERE task_name = ?`)
      .bind(taskName)
      .first();
    if (row?.locked_at) {
      const elapsedSec = (nowMs - Date.parse(row.locked_at)) / 1000;
      if (!Number.isNaN(elapsedSec) && elapsedSec < windowSec) {
        return { acquired: false, reason: "lease_active" };
      }
    }
    await db
      .prepare(
        `INSERT INTO background_leases (task_name, locked_at, owner)
         VALUES (?, ?, ?)
         ON CONFLICT(task_name) DO UPDATE SET locked_at = excluded.locked_at, owner = excluded.owner`
      )
      .bind(taskName, nowIso, owner)
      .run();
    return { acquired: true, reason: "ok" };
  } catch (error) {
    return {
      acquired: true,
      reason: "db_error",
      error: error instanceof Error ? error.message : String(error),
    };
  }
}

export async function releaseBackgroundLease(db, taskName) {
  if (!db || !taskName) return { released: false, reason: "skip" };
  try {
    await db.prepare(`DELETE FROM background_leases WHERE task_name = ?`).bind(taskName).run();
    return { released: true };
  } catch {
    return { released: false, reason: "db_error" };
  }
}
