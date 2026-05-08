import { toIsoNow, getMessageText, parsePositiveInteger, fetchWithTimeout } from "./base_utils.js";

function getChatKey(message, platform = "telegram") {
  const prefix = platform === "discord" ? "dc:" : "";
  if (message.chat_id && message.user_id) return `${prefix}${message.chat_id}:${message.user_id}`;
  if (message.chat_id) return `${prefix}chat:${message.chat_id}`;
  return `${prefix}user:${message.user_id || "unknown"}`;
}

export async function checkTelegramChatRateLimit(env, message, platform = "telegram") {
  const db = env.DB;
  if (!db) return { allowed: true, reason: "no_db" };
  const chatKey = getChatKey(message, platform);
  const now = Date.now();
  const nowIso = new Date(now).toISOString();

  const rateLimitEnvVar = platform === "discord" ? "DISCORD_MIN_INTERVAL_SECONDS" : "TELEGRAM_MIN_INTERVAL_SECONDS";
  const limit5min = platform === "discord" ? "DISCORD_AI_REQUESTS_PER_5_MIN" : "TELEGRAM_AI_REQUESTS_PER_5_MIN";
  const limitDay = platform === "discord" ? "DISCORD_AI_REQUESTS_PER_DAY" : "TELEGRAM_AI_REQUESTS_PER_DAY";

  const window5min = 5 * 60 * 1000;
  const windowDay = 24 * 60 * 60 * 1000;
  const max5min = parsePositiveInteger(env[limit5min], 10);
  const maxDay = parsePositiveInteger(env[limitDay], 60);

  const recent5min = await db.prepare(
    `SELECT COUNT(*) as cnt FROM telegram_chat_messages WHERE chat_key = ? AND created_at > ?`
  ).bind(chatKey, new Date(now - window5min).toISOString()).first();
  if (recent5min && recent5min.cnt >= max5min) {
    return { allowed: false, reason: "rate_limited_5min", retry_after_seconds: 300 };
  }

  const recentDay = await db.prepare(
    `SELECT COUNT(*) as cnt FROM telegram_chat_messages WHERE chat_key = ? AND created_at > ?`
  ).bind(chatKey, new Date(now - windowDay).toISOString()).first();
  if (recentDay && recentDay.cnt >= maxDay) {
    return { allowed: false, reason: "rate_limited_day", retry_after_seconds: 86400 };
  }

  return { allowed: true };
}

export async function loadTelegramChatHistory(env, message, platform = "telegram") {
  const db = env.DB;
  if (!db) return [];
  const chatKey = getChatKey(message, platform);
  const memoryEnvVar = platform === "discord" ? "DISCORD_AI_MEMORY_MESSAGES" : "TELEGRAM_AI_MEMORY_MESSAGES";
  const limit = parsePositiveInteger(env[memoryEnvVar], 8);
  const rows = await db.prepare(
    `SELECT role, intent, message_text, created_at FROM telegram_chat_messages WHERE chat_key = ? ORDER BY id DESC LIMIT ?`
  ).bind(chatKey, limit).all();
  return (rows?.results || []).reverse();
}

export async function saveTelegramConversation(env, message, intent, userText, assistantText, platform = "telegram") {
  const db = env.DB;
  if (!db) return;
  const chatKey = getChatKey(message, platform);
  const createdAt = toIsoNow();
  for (const entry of [{ role: "user", text: userText }, { role: "assistant", text: assistantText }]) {
    await db.prepare(
      `INSERT INTO telegram_chat_messages (chat_key, chat_id, user_id, role, intent, message_text, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)`
    ).bind(chatKey, message.chat_id || null, message.user_id || null, entry.role, intent, entry.text, createdAt).run();
  }
}

export async function clearTelegramChatHistory(env, message, platform = "telegram") {
  const db = env.DB;
  if (!db) return false;
  await db.prepare(`DELETE FROM telegram_chat_messages WHERE chat_key = ?`).bind(getChatKey(message, platform)).run();
  return true;
}

export async function recordIssueModerationAudit(env, record) {
  const db = env.DB;
  if (!db) return;
  await db.prepare(
    `INSERT INTO telegram_issue_moderation_audit (chat_id, user_id, message_id, issue_kind, original_text, decision, reason_code, reason_text, provider_name, model_name, created_at)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
  ).bind(record.chat_id || null, record.user_id || null, record.message_id || null, record.issue_kind || null, record.original_text || "", record.decision || "reject_off_topic", record.reason_code || "unknown", record.reason_text || "Brak powodu.", record.provider_name || null, record.model_name || null, toIsoNow()).run();
}

import { fetchTelegramFileAsBase64 as _fetchTelegramFileAsBase64 } from "./base_utils.js";
export { _fetchTelegramFileAsBase64 as fetchTelegramFileAsBase64 };

export async function fetchDiscordAttachmentAsBase64(attachmentUrl) {
  if (!attachmentUrl) return null;
  try {
    const response = await fetchWithTimeout(attachmentUrl, {}, 30000);
    if (!response.ok) {
      console.error("[fetchDiscordAttachmentAsBase64] download failed, status:", response.status);
      return null;
    }
    const arrayBuffer = await response.arrayBuffer();
    return Buffer.from(arrayBuffer).toString('base64');
  } catch (error) {
    console.error("[fetchDiscordAttachmentAsBase64] error:", error instanceof Error ? error.message : String(error));
    return null;
  }
}
