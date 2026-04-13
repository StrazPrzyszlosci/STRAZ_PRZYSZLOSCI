CREATE TABLE IF NOT EXISTS telegram_chat_messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  chat_key TEXT NOT NULL,
  chat_id TEXT,
  user_id TEXT,
  role TEXT NOT NULL,
  intent TEXT NOT NULL,
  message_text TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_telegram_chat_messages_chat_key
  ON telegram_chat_messages(chat_key, id DESC);

CREATE TABLE IF NOT EXISTS telegram_chat_limits (
  limit_key TEXT PRIMARY KEY,
  bucket_name TEXT NOT NULL,
  window_started_at TEXT NOT NULL,
  request_count INTEGER NOT NULL DEFAULT 0,
  last_request_at TEXT NOT NULL
);

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
  created_at TEXT NOT NULL
);
