-- Migration: 0014_injection_audit_and_package.sql
-- Description: (1) Official migration for injection_audit_log (previously inline-only)
--              (2) Add package column to recycled_part_master and recycled_parts
--              (3) Add indexes for datasheets cache

-- 1. injection_audit_log — was only created inline in input_sanitizer.js
--    This migration ensures the table exists in D1 even without the Worker running
CREATE TABLE IF NOT EXISTS injection_audit_log (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 timestamp TEXT NOT NULL,
 chat_id TEXT,
 user_id TEXT,
 message_id TEXT,
 attack_type TEXT NOT NULL,
 severity TEXT NOT NULL DEFAULT 'low',
 details TEXT,
 action_taken TEXT NOT NULL DEFAULT 'flagged'
);

CREATE INDEX IF NOT EXISTS idx_injection_audit_timestamp
 ON injection_audit_log(timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_injection_audit_severity
 ON injection_audit_log(severity);

CREATE INDEX IF NOT EXISTS idx_injection_audit_chat
 ON injection_audit_log(chat_id, user_id);

-- 2. Add package column to recycled_part_master and recycled_parts
--    package = physical package type (SOT-23, SOIC-8, 0805, DIP-28, etc.)
--    This is DIFFERENT from kicad_footprint which is a KiCad library reference
--    Datasheets table already has this column; now adding consistency
<<<<<<< HEAD
=======
--    Apply this migration before deploying Worker code with inline ensureColumn fallback.
>>>>>>> 5c4d401 (feat: security hardening, market scouting automation, and canary phase closeout)

ALTER TABLE recycled_part_master ADD COLUMN package TEXT;

ALTER TABLE recycled_parts ADD COLUMN package TEXT;

-- 3. Additional indexes for datasheets (supplementing migration 0013)
CREATE INDEX IF NOT EXISTS idx_datasheets_manufacturer
 ON datasheets(manufacturer);

CREATE INDEX IF NOT EXISTS idx_datasheets_mounting
 ON datasheets(mounting, package);
