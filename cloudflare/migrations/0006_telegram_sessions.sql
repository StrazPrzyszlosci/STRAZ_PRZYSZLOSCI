-- Migration: 0006_telegram_sessions.sql
-- Description: Table for tracking active user sessions (e.g., adding parts to a specific device)

CREATE TABLE IF NOT EXISTS telegram_user_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    session_type TEXT NOT NULL, -- 'recycled_parts'
    active_device_id INTEGER,
    status TEXT NOT NULL DEFAULT 'active', -- 'active', 'closed'
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(chat_id, user_id, session_type),
    FOREIGN KEY (active_device_id) REFERENCES recycled_devices(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_telegram_user_sessions_user ON telegram_user_sessions(chat_id, user_id);
