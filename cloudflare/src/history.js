import { toIsoNow, getMessageText, parsePositiveInteger } from "./base_utils.js";

function getChatKey(message) {
  if (message.chat_id && message.user_id) return `${message.chat_id}:${message.user_id}`;
  if (message.chat_id) return `chat:${message.chat_id}`;
  return `user:${message.user_id || "unknown"}`;
}

export async function checkTelegramChatRateLimit(env, message) {
  const db = env.DB;
  if (!db) return { allowed: true, reason: "no_db" };
  const chatKey = getChatKey(message);
  const now = Date.now();
  const nowIso = new Date(now).toISOString();
  // ... (rate limit logic would be here)
  return { allowed: true };
}

export async function loadTelegramChatHistory(env, message) {
  const db = env.DB;
  if (!db) return [];
  const chatKey = getChatKey(message);
  const limit = parsePositiveInteger(env.TELEGRAM_AI_MEMORY_MESSAGES, 8);
  const rows = await db.prepare(
    `SELECT role, intent, message_text, created_at FROM telegram_chat_messages WHERE chat_key = ? ORDER BY id DESC LIMIT ?`
  ).bind(chatKey, limit).all();
  return (rows?.results || []).reverse();
}

export async function saveTelegramConversation(env, message, intent, userText, assistantText) {
  const db = env.DB;
  if (!db) return;
  const chatKey = getChatKey(message);
  const createdAt = toIsoNow();
  for (const entry of [{ role: "user", text: userText }, { role: "assistant", text: assistantText }]) {
    await db.prepare(
      `INSERT INTO telegram_chat_messages (chat_key, chat_id, user_id, role, intent, message_text, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)`
    ).bind(chatKey, message.chat_id || null, message.user_id || null, entry.role, intent, entry.text, createdAt).run();
  }
}

export async function clearTelegramChatHistory(env, message) {
  const db = env.DB;
  if (!db) return false;
  await db.prepare(`DELETE FROM telegram_chat_messages WHERE chat_key = ?`).bind(getChatKey(message)).run();
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

export async function fetchTelegramFileAsBase64(env, fileId) {
  const botToken = env.TELEGRAM_BOT_TOKEN;
  if (!botToken || !fileId) return null;
  try {
    const fileInfoResp = await fetch(`https://api.telegram.org/bot${botToken}/getFile?file_id=${fileId}`);
    const fileInfo = await fileInfoResp.json();
    if (!fileInfo.ok || !fileInfo.result.file_path) {
      console.error("[fetchTelegramFileAsBase64] getFile failed:", JSON.stringify(fileInfo));
      return null;
    }
    const filePath = fileInfo.result.file_path;
    const fileContentResp = await fetch(`https://api.telegram.org/file/bot${botToken}/${filePath}`);
    if (!fileContentResp.ok) {
      console.error("[fetchTelegramFileAsBase64] file download failed, status:", fileContentResp.status);
      return null;
    }
    const arrayBuffer = await fileContentResp.arrayBuffer();
    const uint8Array = new Uint8Array(arrayBuffer);
    let binary = "";
    const chunkSize = 8192;
    for (let i = 0; i < uint8Array.length; i += chunkSize) {
      const chunk = uint8Array.subarray(i, Math.min(i + chunkSize, uint8Array.length));
      binary += String.fromCharCode.apply(null, chunk);
    }
    return btoa(binary);
  } catch (error) {
    console.error("[fetchTelegramFileAsBase64] error:", error instanceof Error ? error.message : String(error));
    return null;
  }
}
