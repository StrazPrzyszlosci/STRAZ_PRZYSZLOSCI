/**
 * discord_security.mjs — Security utilities for Straż Przyszłości Discord Bot
 * Extracted from discord_bot.mjs for testability.
 */

// Rate limiting: TELEGRAM_MIN_INTERVAL_SECONDS or default 60s
const RATE_LIMIT_WINDOW_MS = (() => {
  const val = parseInt(process.env.DISCORD_MIN_INTERVAL_SECONDS || process.env.TELEGRAM_MIN_INTERVAL_SECONDS || "60", 10);
  return Number.isFinite(val) && val > 0 ? val * 1000 : 60000;
})();

// Static whitelist of allowed attachment MIME types
const ALLOWED_ATTACHMENT_MIMES = (process.env.DISCORD_ALLOWED_ATTACHMENT_MIMES || "image/jpeg,image/png,image/gif,image/webp,application/pdf,text/plain")
  .split(",")
  .map(s => s.trim().toLowerCase());

// In-memory rate limiter per user
const rateLimitMap = new Map();
let cleanupCounter = 0;
const CLEANUP_INTERVAL = 100;

function checkRateLimit(userId) {
  if (RATE_LIMIT_WINDOW_MS <= 0) return { allowed: true };
  const now = Date.now();
  const last = rateLimitMap.get(userId);
  if (last && (now - last) < RATE_LIMIT_WINDOW_MS) {
    const retryAfter = Math.ceil((RATE_LIMIT_WINDOW_MS - (now - last)) / 1000);
    return { allowed: false, retry_after_seconds: retryAfter };
  }
  rateLimitMap.set(userId, now);
  cleanupCounter++;
  if (cleanupCounter >= CLEANUP_INTERVAL && rateLimitMap.size > 10000) {
    cleanupCounter = 0;
    const cutoff = now - RATE_LIMIT_WINDOW_MS * 2;
    for (const [k, v] of rateLimitMap) {
      if (v < cutoff) rateLimitMap.delete(k);
    }
  }
  return { allowed: true };
}

function _resetRateLimitMap() {
  rateLimitMap.clear();
}

/**
 * Basic input sanitization: strip invisible unicode, trim, limit length.
 * Mirrors telegram sanitizeUserInput but without full AI pipeline injection detection.
 */
function sanitizeDiscordInput(text) {
  if (typeof text !== "string") return "";
  // Strip zero-width and invisible chars
  const cleaned = text.replace(/[\u0000-\u0008\u000B\u000E-\u001F\u007F-\u009F\u00AD\u034F\u061C\u17B4\u17B5\u180B-\u180E\u200B-\u200F\u2028-\u202E\u205F-\u206F\uFE00-\uFE0F\uFEFF\uFFF0-\uFFFB]/gu, "");
  // Clamp length
  const maxChars = 4000;
  return cleaned.length > maxChars ? cleaned.slice(0, maxChars) : cleaned;
}

function isAllowedMimeType(contentType, fileName) {
  if (!contentType) {
    // fallback by extension
    const ext = (fileName || "").split(".").pop()?.toLowerCase();
    const mimeByExt = { jpg: "image/jpeg", jpeg: "image/jpeg", png: "image/png", gif: "image/gif", webp: "image/webp", pdf: "application/pdf", txt: "text/plain" };
    const inferred = mimeByExt[ext];
    return inferred ? ALLOWED_ATTACHMENT_MIMES.includes(inferred) : false;
  }
  return ALLOWED_ATTACHMENT_MIMES.some(allowed => contentType.toLowerCase().startsWith(allowed));
}

function mapAttachmentToPayload(attachment) {
  return {
    url: attachment.url,
    name: attachment.name || null,
    contentType: attachment.contentType || null,
  };
}

export { checkRateLimit, _resetRateLimitMap, sanitizeDiscordInput, isAllowedMimeType, mapAttachmentToPayload };