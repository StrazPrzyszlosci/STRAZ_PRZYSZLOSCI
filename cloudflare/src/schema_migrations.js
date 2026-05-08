/**
 * D1 Schema Migrations Framework (Z86).
 *
 * Migrations are idempotent by design (IF NOT EXISTS, ADD COLUMN IF NOT EXISTS).
 * Uses the existing D1 binding.
 *
 * Usage in worker.js (on startup):
 *   import { applyMigrations } from "./schema_migrations.js";
 *   // Before handling requests, in the fetch() handler:
 *   await applyMigrations(env.DB);
 *
 * No transactions supported in D1 (BEGIN/COMMIT). Each migration is idempotent.
 */

import { toIsoNow } from "./base_utils.js";

/**
 * Ordered list of idempotent migrations.
 * Each migration is { version, name, sql }.
 * Version is a unique string (e.g., timestamp). Order matters.
 */
export const MIGRATIONS = [
  {
    version: "20240508180000-init",
    name: "Create schema_migrations table",
    sql: `CREATE TABLE IF NOT EXISTS schema_migrations (
      version TEXT PRIMARY KEY,
      name TEXT NOT NULL,
      applied_at TEXT NOT NULL
    );`,
  },
  {
    version: "20240508180001-telegram-limits",
    name: "Ensure telegram_chat_limits table exists (legacy compat)",
    sql: `CREATE TABLE IF NOT EXISTS telegram_chat_limits (
      limit_key TEXT PRIMARY KEY,
      bucket_name TEXT,
      window_started_at TEXT,
      request_count INTEGER,
      last_request_at TEXT,
      platform TEXT NOT NULL DEFAULT 'telegram'
    );`,
  },
  {
    version: "20240508180002-telegram-messages",
    name: "Ensure telegram_chat_messages table exists (legacy compat)",
    sql: `CREATE TABLE IF NOT EXISTS telegram_chat_messages (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      chat_key TEXT NOT NULL,
      role TEXT,
      intent TEXT,
      message_text TEXT,
      created_at TEXT
    );`,
  },
  {
    version: "20240508180003-telegram-issues",
    name: "Ensure telegram_issues table exists (legacy compat)",
    sql: `CREATE TABLE IF NOT EXISTS telegram_issues (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      chat_id TEXT,
      user_id TEXT,
      message_id TEXT,
      issue_kind TEXT,
      original_text TEXT,
      decision TEXT,
      reason_code TEXT,
      reason_text TEXT,
      provider_name TEXT,
      model_name TEXT,
      created_at TEXT
    );`,
  },
  {
    version: "20240508180004-telegram-issue-throttle",
    name: "Ensure telegram_issue_throttle table exists (legacy compat)",
    sql: `CREATE TABLE IF NOT EXISTS telegram_issue_throttle (
      throttle_key TEXT PRIMARY KEY,
      platform TEXT NOT NULL DEFAULT 'telegram',
      last_accepted_at TEXT
    );`,
  },
  {
    version: "20240508180005-telegram-chat-sessions",
    name: "Ensure telegram_chat_sessions table exists (legacy compat)",
    sql: `CREATE TABLE IF NOT EXISTS telegram_chat_sessions (
      chat_id TEXT NOT NULL,
      user_id TEXT NOT NULL,
      session_type TEXT NOT NULL,
      active_device_name TEXT,
      active_device_json TEXT,
      created_at TEXT,
      updated_at TEXT,
      PRIMARY KEY (chat_id, user_id, session_type)
    );`,
  },
];

/**
 * Apply all pending migrations to the given D1 database.
 */
export async function applyMigrations(db) {
  if (!db) return { success: false, reason: "no_db" };

  // Ensure the schema_migrations table exists first (always idempotent)
  try {
    await db.prepare(MIGRATIONS[0].sql).run();
  } catch (err) {
    console.error(`[applyMigrations] Failed to create schema_migrations:`, err);
    return { success: false, reason: "init_failed", error: err.message };
  }

  // Fetch applied versions
  let appliedRows = [];
  try {
    const result = await db.prepare(`SELECT version FROM schema_migrations ORDER BY version`).all();
    appliedRows = result?.results || [];
  } catch (err) {
    console.error(`[applyMigrations] Failed to fetch applied migrations:`, err);
    return { success: false, reason: "fetch_failed", error: err.message };
  }

  const appliedVersions = new Set(appliedRows.map((r) => r.version));
  const pending = MIGRATIONS.filter((m) => !appliedVersions.has(m.version));

  if (pending.length === 0) {
    return { success: true, reason: "no_migrations", applied: 0 };
  }

  const nowIso = toIsoNow();
  let appliedCount = 0;

  for (const migration of pending) {
    try {
      await db.prepare(migration.sql).run();
      await db
        .prepare(`INSERT INTO schema_migrations (version, name, applied_at) VALUES (?, ?, ?)`)
        .bind(migration.version, migration.name, nowIso)
        .run();
      appliedCount++;
    } catch (err) {
      console.error(`[applyMigrations] Migration ${migration.version} failed:`, err);
      return { success: false, reason: "migration_failed", version: migration.version, error: err.message };
    }
  }

  return { success: true, applied: appliedCount };
}

/**
 * Read the current D1 schema version.
 */
export async function getSchemaVersion(db) {
  if (!db) return null;
  try {
    const result = await db
      .prepare(`SELECT version FROM schema_migrations ORDER BY version DESC LIMIT 1`)
      .first();
    return result?.version || null;
  } catch {
    return null;
  }
}
