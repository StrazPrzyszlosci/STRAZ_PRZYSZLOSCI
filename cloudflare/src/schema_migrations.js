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
      chat_id TEXT,
      user_id TEXT,
      role TEXT NOT NULL,
      intent TEXT NOT NULL,
      message_text TEXT NOT NULL,
      created_at TEXT NOT NULL,
      platform TEXT NOT NULL DEFAULT 'telegram'
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
      last_accepted_at TEXT NOT NULL,
      last_message_id TEXT,
      last_update_id TEXT,
      message_count INTEGER NOT NULL DEFAULT 0,
      platform TEXT NOT NULL DEFAULT 'telegram'
    );`,
  },
  {
    version: "20240508180005-telegram-chat-sessions",
    name: "Ensure telegram_user_sessions table exists (legacy compat)",
    sql: `CREATE TABLE IF NOT EXISTS telegram_user_sessions (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      chat_id TEXT NOT NULL,
      user_id TEXT NOT NULL,
      session_type TEXT NOT NULL,
      active_device_id INTEGER,
      active_device_name TEXT,
      status TEXT NOT NULL DEFAULT 'active',
      created_at TEXT NOT NULL,
      updated_at TEXT NOT NULL,
      platform TEXT NOT NULL DEFAULT 'telegram',
      UNIQUE(chat_id, user_id, session_type)
    );`,
  },

  {
    version: "20240514120000-kicad-library-sources",
    name: "Ensure kicad_library_sources table exists",
    sql: `CREATE TABLE IF NOT EXISTS kicad_library_sources (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      source_slug TEXT NOT NULL UNIQUE,
      source_url TEXT NOT NULL,
      license_spdx TEXT NOT NULL,
      upstream_commit TEXT,
      kicad_version_family TEXT,
      ingested_at TEXT NOT NULL,
      raw_manifest_json TEXT
    );`,
  },
  {
    version: "20240514120001-kicad-library-components",
    name: "Ensure kicad_library_components table exists",
    sql: `CREATE TABLE IF NOT EXISTS kicad_library_components (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      source_id INTEGER,
      library_name TEXT,
      symbol_name TEXT,
      footprint_name TEXT,
      reference_prefix TEXT,
      description TEXT,
      keywords TEXT,
      manufacturer TEXT,
      mpn TEXT,
      datasheet_url TEXT,
      package TEXT,
      normalized_part_number TEXT,
      raw_symbol_path TEXT,
      raw_footprint_path TEXT,
      raw_metadata_json TEXT,
      created_at TEXT NOT NULL
    );`,
  },
  {
    version: "20240514120002-recycled-part-kicad-links",
    name: "Ensure recycled_part_kicad_links table exists",
    sql: `CREATE TABLE IF NOT EXISTS recycled_part_kicad_links (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      master_part_id INTEGER NOT NULL,
      kicad_component_id INTEGER NOT NULL,
      match_type TEXT NOT NULL,
      confidence REAL,
      review_status TEXT NOT NULL DEFAULT 'suggested',
      reviewed_by TEXT,
      reason TEXT,
      created_at TEXT NOT NULL,
      reviewed_at TEXT,
      UNIQUE(master_part_id, kicad_component_id)
    );`,
  },
  {
    version: "20240514120003-kicad-components-normalized-index",
    name: "Ensure KiCad component normalized part index exists",
    sql: `CREATE INDEX IF NOT EXISTS idx_kicad_components_normalized_part_number
      ON kicad_library_components(normalized_part_number);`,
  },
  {
    version: "20240514120004-kicad-components-symbol-footprint-indexes",
    name: "Ensure KiCad component symbol and footprint indexes exist",
    sql: `CREATE INDEX IF NOT EXISTS idx_kicad_components_symbol_name
      ON kicad_library_components(symbol_name);`,
  },
  {
    version: "20240514120005-kicad-components-footprint-index",
    name: "Ensure KiCad component footprint index exists",
    sql: `CREATE INDEX IF NOT EXISTS idx_kicad_components_footprint_name
      ON kicad_library_components(footprint_name);`,
  },
  {
    version: "20240514120006-kicad-links-review-index",
    name: "Ensure KiCad review status index exists",
    sql: `CREATE INDEX IF NOT EXISTS idx_recycled_part_kicad_links_review_status
      ON recycled_part_kicad_links(review_status);`,
  },

  {
    version: "20240514120007-kicad-review-events",
    name: "Ensure KiCad review event ledger exists",
    sql: `CREATE TABLE IF NOT EXISTS kicad_review_events (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      link_id INTEGER,
      master_part_id INTEGER NOT NULL,
      kicad_component_id INTEGER NOT NULL,
      previous_status TEXT,
      next_status TEXT NOT NULL,
      reviewed_by TEXT,
      reason TEXT,
      created_at TEXT NOT NULL
    );`,
  },
  {
    version: "20240514120008-kicad-review-events-link-index",
    name: "Ensure KiCad review event link index exists",
    sql: `CREATE INDEX IF NOT EXISTS idx_kicad_review_events_link_id
      ON kicad_review_events(link_id);`,
  },
  {
    version: "20260705000001-devices-gpio-pin-map",
    name: "Ensure recycled_devices has gpio_pin_map_json column (Z15 profile template extension)",
    sql: `ALTER TABLE recycled_devices ADD COLUMN gpio_pin_map_json TEXT;`,
  },
  {
    version: "20260706000001-automation-metrics",
    name: "Ensure automation_metrics table + index for B4 dashboard (H2 roadmapa)",
    sql: `CREATE TABLE IF NOT EXISTS automation_metrics (
      metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
      metric_key TEXT NOT NULL,
      metric_value REAL NOT NULL,
      measured_at TEXT NOT NULL,
      window TEXT NOT NULL DEFAULT 'sprint'
    );`,
  },
  {
    version: "20260706000002-automation-metrics-index",
    name: "Ensure automation_metrics index on (metric_key, measured_at) for B4",
    sql: `CREATE INDEX IF NOT EXISTS idx_automation_metrics_key_measured
      ON automation_metrics(metric_key, measured_at);`,
  },
  {
    version: "20260706000003-kicad-import-status-dedup",
    name: "Ensure KiCad component import status and dedup checksum for B1",
    sql: `ALTER TABLE kicad_library_components ADD COLUMN import_status TEXT NOT NULL DEFAULT 'staged';`,
  },
  {
    version: "20260706000004-kicad-import-dedup-checksum",
    name: "Ensure KiCad component dedup checksum column for B1",
    sql: `ALTER TABLE kicad_library_components ADD COLUMN dedup_checksum TEXT;`,
  },
  {
    version: "20260706000005-kicad-import-dedup-index",
    name: "Ensure unique KiCad import dedup checksum index for B1",
    sql: `CREATE UNIQUE INDEX IF NOT EXISTS idx_kicad_components_dedup_checksum
      ON kicad_library_components(dedup_checksum);`,
  },
  {
    version: "20260706000006-kicad-library-events",
    name: "Ensure KiCad library ingest event ledger for B1",
    sql: `CREATE TABLE IF NOT EXISTS kicad_library_events (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      kind TEXT NOT NULL,
      source_slug TEXT NOT NULL,
      upstream_commit TEXT,
      component_count INTEGER NOT NULL DEFAULT 0,
      inserted_count INTEGER NOT NULL DEFAULT 0,
      skipped_count INTEGER NOT NULL DEFAULT 0,
      created_at TEXT NOT NULL
    );`,
  },
  {
    version: "20260706000007-kicad-library-events-kind-index",
    name: "Ensure KiCad library events kind/time index for B1",
    sql: `CREATE INDEX IF NOT EXISTS idx_kicad_library_events_kind_created
      ON kicad_library_events(kind, created_at);`,
  },
  {
    version: "20260706000008-kicad-verifier-note",
    name: "Ensure KiCad verifier note column for B2",
    sql: `ALTER TABLE kicad_library_components ADD COLUMN verify_note TEXT;`,
  },
  {
    version: "20260706000009-kicad-verifier-verified-at",
    name: "Ensure KiCad verifier timestamp column for B2",
    sql: `ALTER TABLE kicad_library_components ADD COLUMN verified_at TEXT;`,
  },
  {
    version: "20260706000010-kicad-library-events-component-status",
    name: "Ensure KiCad library events verifier status columns for B2",
    sql: `ALTER TABLE kicad_library_events ADD COLUMN component_id INTEGER;`,
  },
  {
    version: "20260706000011-kicad-library-events-previous-status",
    name: "Ensure KiCad library events previous status column for B2",
    sql: `ALTER TABLE kicad_library_events ADD COLUMN previous_status TEXT;`,
  },
  {
    version: "20260706000012-kicad-library-events-next-status",
    name: "Ensure KiCad library events next status column for B2",
    sql: `ALTER TABLE kicad_library_events ADD COLUMN next_status TEXT;`,
  },
  {
    version: "20260706000013-kicad-library-events-reason",
    name: "Ensure KiCad library events reason column for B2",
    sql: `ALTER TABLE kicad_library_events ADD COLUMN reason TEXT;`,
  },
  {
    version: "20260706000014-kicad-ocr-queue",
    name: "Ensure KiCad OCR deferred queue for B2",
    sql: `CREATE TABLE IF NOT EXISTS kicad_ocr_queue (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      component_id INTEGER NOT NULL UNIQUE,
      datasheet_url TEXT,
      status TEXT NOT NULL DEFAULT 'pending',
      reason TEXT,
      created_at TEXT NOT NULL
    );`,
  },
  {
    version: "20260706000015-kicad-ocr-queue-status-index",
    name: "Ensure KiCad OCR queue status index for B2",
    sql: `CREATE INDEX IF NOT EXISTS idx_kicad_ocr_queue_status_created
      ON kicad_ocr_queue(status, created_at);`,
  },
  {
    version: "20260706000016-execution-packs",
    name: "Ensure execution_packs table for B5 bot initiator",
    sql: `CREATE TABLE IF NOT EXISTS execution_packs (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      pack_id TEXT NOT NULL,
      status TEXT NOT NULL,
      reviewer TEXT NOT NULL,
      fork_branch TEXT,
      pr_url TEXT,
      canary_mode INTEGER NOT NULL DEFAULT 1,
      initiated_by TEXT,
      platform TEXT NOT NULL DEFAULT 'discord',
      created_at TEXT NOT NULL,
      updated_at TEXT NOT NULL
    );`,
  },
  {
    version: "20260706000017-execution-packs-status-index",
    name: "Ensure execution_packs pack/status index for B5",
    sql: `CREATE INDEX IF NOT EXISTS idx_execution_packs_pack_status
      ON execution_packs(pack_id, status);`,
  },
];

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

export async function ensureRuntimeCompatibilitySchema(db) {
  if (!db) {
    return { success: false, reason: "no_db" };
  }

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

  await runSql(
    db,
    `
    CREATE TABLE IF NOT EXISTS telegram_chat_messages (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      chat_key TEXT NOT NULL,
      chat_id TEXT,
      user_id TEXT,
      role TEXT NOT NULL,
      intent TEXT NOT NULL,
      message_text TEXT NOT NULL,
      created_at TEXT NOT NULL,
      platform TEXT NOT NULL DEFAULT 'telegram'
    )
    `
  );
  await ensureColumn(db, "telegram_chat_messages", "chat_id", "chat_id TEXT");
  await ensureColumn(db, "telegram_chat_messages", "user_id", "user_id TEXT");
  await ensureColumn(db, "telegram_chat_messages", "platform", "platform TEXT NOT NULL DEFAULT 'telegram'");

  await runSql(
    db,
    `
    CREATE TABLE IF NOT EXISTS telegram_issue_throttle (
      throttle_key TEXT PRIMARY KEY,
      last_accepted_at TEXT NOT NULL,
      last_message_id TEXT,
      last_update_id TEXT,
      message_count INTEGER NOT NULL DEFAULT 0,
      platform TEXT NOT NULL DEFAULT 'telegram'
    )
    `
  );
  await ensureColumn(db, "telegram_issue_throttle", "last_message_id", "last_message_id TEXT");
  await ensureColumn(db, "telegram_issue_throttle", "last_update_id", "last_update_id TEXT");
  await ensureColumn(db, "telegram_issue_throttle", "message_count", "message_count INTEGER NOT NULL DEFAULT 0");
  await ensureColumn(db, "telegram_issue_throttle", "platform", "platform TEXT NOT NULL DEFAULT 'telegram'");

  await runSql(
    db,
    `
    CREATE TABLE IF NOT EXISTS telegram_issue_moderation_audit (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      chat_id TEXT,
      user_id TEXT,
      message_id TEXT,
      issue_kind TEXT,
      original_text TEXT NOT NULL,
      decision TEXT NOT NULL,
      reason_code TEXT NOT NULL,
      reason_text TEXT NOT NULL,
      provider_name TEXT,
      model_name TEXT,
      created_at TEXT NOT NULL,
      platform TEXT NOT NULL DEFAULT 'telegram'
    )
    `
  );
  await ensureColumn(db, "telegram_issue_moderation_audit", "platform", "platform TEXT NOT NULL DEFAULT 'telegram'");

  await runSql(
    db,
    `
    CREATE TABLE IF NOT EXISTS telegram_user_sessions (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      chat_id TEXT NOT NULL,
      user_id TEXT NOT NULL,
      session_type TEXT NOT NULL,
      active_device_id INTEGER,
      active_device_name TEXT,
      status TEXT NOT NULL DEFAULT 'active',
      created_at TEXT NOT NULL,
      updated_at TEXT NOT NULL,
      platform TEXT NOT NULL DEFAULT 'telegram',
      UNIQUE(chat_id, user_id, session_type)
    )
    `
  );
  await ensureColumn(db, "telegram_user_sessions", "active_device_name", "active_device_name TEXT");
  await ensureColumn(db, "telegram_user_sessions", "platform", "platform TEXT NOT NULL DEFAULT 'telegram'");

  return { success: true };
}

/**
 * Apply all pending migrations to the given D1 database.
 */
export async function applyMigrations(db) {
  if (!db) return { success: false, reason: "no_db" };

  // Ensure the schema_migrations table exists first (always idempotent)
  try {
    const stmt = await db.prepare(MIGRATIONS[0].sql);
    await stmt.run();
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
    try {
      await ensureRuntimeCompatibilitySchema(db);
    } catch (err) {
      console.error(`[applyMigrations] Runtime compatibility schema failed:`, err);
      return { success: false, reason: "compat_failed", error: err.message };
    }
    return { success: true, reason: "no_migrations", applied: 0 };
  }

  const nowIso = toIsoNow();
  let appliedCount = 0;

  for (const migration of pending) {
    try {
      await runSql(db, migration.sql);
      const stmt2 = await db
        .prepare(`INSERT INTO schema_migrations (version, name, applied_at) VALUES (?, ?, ?)`);
      await stmt2.bind(migration.version, migration.name, nowIso)
        .run();
      appliedCount++;
    } catch (err) {
      console.error(`[applyMigrations] Migration ${migration.version} failed:`, err);
      return { success: false, reason: "migration_failed", version: migration.version, error: err.message };
    }
  }

  try {
    await ensureRuntimeCompatibilitySchema(db);
  } catch (err) {
    console.error(`[applyMigrations] Runtime compatibility schema failed:`, err);
    return { success: false, reason: "compat_failed", error: err.message };
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
