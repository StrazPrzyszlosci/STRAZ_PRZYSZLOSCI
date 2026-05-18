import {
  buildChatThrottleReply,
  buildCommandReply,
  buildIssueBody,
  buildIssueModerationReply,
  buildIssueThrottleReply,
  buildIssueTitle,
  checkTelegramChatRateLimit,
  clearTelegramChatHistory,
  draftIssueBody,
  generateChatReply,
  isTruthy,
  loadTelegramChatHistory,
  moderateIssueCandidate,
  parsePositiveInteger,
  recordIssueModerationAudit,
  recommendOnboardingPath,
  routeTelegramIntent,
  saveTelegramConversation,
  handleRecycledKnowledgeLookup,
  recognizeDeviceAndListParts,
  recognizePartAndRecord,
  recordRecycledSubmission,
  getUserSession,
  upsertUserSession,
  closeUserSession,
  closeAllUserSessions,
  getDeviceById,
  buildDeviceCatalogReply,
  getPartsForModel,
handleResistorAnalysis,
validateManualEntry,
getResistorLegendText,
runResistorVerification,
  initDatasheetWorkflow,
  handleFinalDatasheetRag,
  handleFinalDatasheetRagFinal,
  answerDeviceLookupQuestion,
  answerPartLookupQuestion,
  attachPdfToDatasheetSession,
  recognizePartForScanFlow,
  recognizeDeviceForScanFlow,
  saveScanFlowPart,
  createScanPartPayload,
  readScanPartPayload,
  createBatchScanPayload,
  readBatchScanPayload,
  isValidPdfUrl,
} from "./telegram_ai.js";
import { buildVerificationResultReply } from "./vision.js";
import { sanitizeUserInput } from "./input_sanitizer.js";
import { sanitizeTelegramReply, sendTelegramReply, getMainMenuKeyboard } from "./telegram_utils.js";
import { fetchWithTimeout, fetchTelegramFileAsBase64 } from "./base_utils.js";
import { checkPayloadSize } from "./payload_size.js";
import { jsonResponse as secureJsonResponse } from "./security_headers.js";

function jsonResponse(payload, status = 200, env = null, request = null) {
  return secureJsonResponse(payload, status, env, request);
}

function parseAllowedIds(rawValue) {
  if (!rawValue || !rawValue.trim()) {
    return null;
  }
  if (rawValue.trim() === "*") {
    return null;
  }

  const allowlist = new Set();
  for (const item of rawValue.split(",")) {
    const normalized = item.trim();
    if (normalized) {
      allowlist.add(normalized);
    }
  }
  return allowlist.size ? allowlist : null;
}

function getConfiguredLabels(kind, env) {
  const labels = [];
  const channelLabel = (env.TELEGRAM_CHANNEL_LABEL || "").trim();
  const kindLabel =
    kind === "idea"
      ? (env.TELEGRAM_IDEA_LABEL || "").trim()
      : (env.TELEGRAM_FEEDBACK_LABEL || "").trim();

  if (kindLabel) {
    labels.push(kindLabel);
  }
  if (channelLabel) {
    labels.push(channelLabel);
  }
  return labels;
}

function withMenuRow(inlineKeyboard = []) {
  return {
    inline_keyboard: [
      ...inlineKeyboard,
      [{ text: "🏠 Menu główne", callback_data: "command_start" }],
    ],
  };
}

function getScanMenuKeyboard() {
  return withMenuRow([
    [{ text: "🔎 Skanuj i rozpoznaj część", callback_data: "scan_part_start" }],
    [{ text: "🧩 Rozpocznij tryb dodawania wielu części dla podanego urządzenia/elektrośmiecia", callback_data: "scan_batch_start" }],
  ]);
}

function getScanPartPreviewKeyboard() {
  return withMenuRow([
    [
      { text: "✅ Dodaj część do bazy danych", callback_data: "scan_part_add" },
      { text: "✏️ Edytuj rozpoznane oznaczenie części", callback_data: "scan_part_edit" },
    ],
  ]);
}

function getScanPartModelKeyboard() {
  return withMenuRow([
    [{ text: "🤷 Nie mam modelu", callback_data: "scan_part_no_model" }],
  ]);
}

function getScanPartModelPreviewKeyboard() {
  return withMenuRow([
    [
      { text: "✅ Użyj tego modelu", callback_data: "scan_part_model_use" },
      { text: "✏️ Edytuj rozpoznane oznaczenie modelu/elektrośmiecia", callback_data: "scan_part_model_edit" },
    ],
  ]);
}

function getBatchChoiceKeyboard() {
  return withMenuRow([
    [
      { text: "✍️ Wpisz model ręcznie", callback_data: "scan_batch_enter_model" },
      { text: "📷 Rozpoznaj model ze zdjęcia", callback_data: "scan_batch_photo_model" },
    ],
  ]);
}

function getBatchModelPreviewKeyboard() {
  return withMenuRow([
    [
      { text: "✅ Użyj tego modelu", callback_data: "scan_batch_model_use" },
      { text: "✏️ Edytuj rozpoznane oznaczenie modelu/elektrośmiecia", callback_data: "scan_batch_model_edit" },
    ],
  ]);
}

function getBatchCollectKeyboard() {
  return withMenuRow([
    [
      { text: "🔁 Zmień model elektrośmiecia źródłowego", callback_data: "scan_batch_change_model" },
      { text: "✅ Zakończ dodawanie", callback_data: "scan_batch_finish" },
    ],
  ]);
}

function getDatasheetModelKeyboard() {
  return withMenuRow([
    [{ text: "🤷‍♂️ Nie znam modelu", callback_data: "datasheet_no_model" }],
    [{ text: "❌ Anuluj analizę", callback_data: "cancel_session:datasheet_wait_model" }],
  ]);
}

function getPlainCommandAlias(text) {
  const normalized = String(text || "").trim().toLowerCase();
  const aliases = {
    reset: "reset",
    restart: "reset",
    wyczysc: "reset",
    "wyczyść": "reset",
    stop: "stop",
    anuluj: "stop",
    przerwij: "stop",
    koniec: "stop",
  };
  return aliases[normalized] || null;
}

function getPartQuestionKeyboard(partId) {
  return withMenuRow([
    [{ text: "💬 Zapytaj o tę część", callback_data: `part_question_start:${partId}` }],
  ]);
}

function parseJsonSafeLocal(value, fallback = null) {
  if (value == null || value === "") {
    return fallback;
  }
  if (typeof value === "object") {
    return value;
  }
  try {
    return JSON.parse(String(value));
  } catch {
    return fallback;
  }
}

function buildDatasheetQuestionPayload(partQuery, session = null, overrides = {}) {
  const parsed = parseJsonSafeLocal(session?.active_device_name, null);
  if (parsed && typeof parsed === "object" && parsed.version === 2) {
    return {
      version: 2,
      part_number: parsed.part_number || partQuery,
      master_part_id: parsed.master_part_id || null,
      donor_device_model: parsed.donor_device_model || "",
      donor_device_id: parsed.donor_device_id || null,
      pdf_url: parsed.pdf_url || "",
      pdf_file_id: parsed.pdf_file_id || "",
      db_hit: Boolean(parsed.db_hit),
      source: overrides.source || parsed.source || "",
      file_name: parsed.file_name || "",
      scan_summary: parsed.scan_summary || "",
      ...overrides,
    };
  }

  const legacyParts = String(session?.active_device_name || "").split("|");
  const legacyPdfUrl = legacyParts.find((item) => /^https?:\/\//i.test(item)) || "";
  return {
    version: 2,
    part_number: partQuery || legacyParts[0] || "",
    master_part_id: null,
    donor_device_model: legacyParts.length > 2 ? legacyParts.slice(2).filter((item) => !/^https?:\/\//i.test(item)).join(" | ") : "",
    donor_device_id: null,
    pdf_url: legacyPdfUrl,
    pdf_file_id: "",
    db_hit: false,
    source: overrides.source || "callback_legacy",
    file_name: "",
    scan_summary: "",
    ...overrides,
  };
}

function buildDatasheetQuestionPayloadFromSubmission(lastSub, fallbackPartQuery = "") {
  const lastPayload = parseJsonSafeLocal(lastSub?.raw_payload_json, {}) || {};
  const partQuery =
    fallbackPartQuery ||
    lastSub?.matched_part_number ||
    lastSub?.matched_part_name ||
    lastPayload.part_number ||
    "";
  return {
    version: 2,
    part_number: partQuery,
    master_part_id: lastSub?.master_part_id || null,
    donor_device_model: lastPayload.device || lastSub?.query_text || "",
    donor_device_id: null,
    pdf_url: lastPayload.pdf_url || "",
    pdf_file_id: lastSub?.attachment_file_id || lastPayload.pdf_file_id || "",
    db_hit: Boolean(lastSub?.master_part_id),
    source: "callback_continue",
    file_name: lastPayload.file_name || "",
    scan_summary: lastPayload.scan_summary || "",
  };
}

function parseManualPartEntry(text) {
  const parts = String(text || "").split("|").map((item) => item.trim()).filter(Boolean);
  if (parts.length > 1) {
    return {
      part_name: parts[0] || "Część urządzenia",
      part_number: parts.slice(1).join(" | "),
    };
  }
  return {
    part_name: "Część urządzenia",
    part_number: parts[0] || String(text || "").trim(),
  };
}

async function closeScanPartFlowSessions(env, chatId, userId) {
  for (const sessionType of [
    "scan_part_wait_photo",
    "scan_part_preview",
    "scan_part_edit",
    "scan_part_wait_model",
    "scan_part_model_preview",
    "scan_part_model_edit",
  ]) {
    await closeUserSession(env, chatId, userId, sessionType);
  }
}

async function closeBatchFlowSessions(env, chatId, userId) {
  for (const sessionType of [
    "scan_batch_wait_model_text",
    "scan_batch_wait_model_photo",
    "scan_batch_model_preview",
    "scan_batch_model_edit",
    "scan_batch_collect_parts",
  ]) {
    await closeUserSession(env, chatId, userId, sessionType);
  }
}

async function activateBatchCollectSession(env, chatId, userId, payload) {
  await closeBatchFlowSessions(env, chatId, userId);
  await upsertUserSession(env, chatId, userId, "scan_batch_collect_parts", null, createBatchScanPayload(payload));
}

function buildBatchCollectReply(deviceModel) {
  return {
    reply_text: [
      `✅ Tryb dodawania wielu części aktywny dla modelu: *${deviceModel}*.`,
      "",
      "Możesz teraz wpisywać dokładne oznaczenia części albo wysyłać zdjęcia części.",
      "Gdy skończysz, użyj przycisku *Zakończ dodawanie*.",
    ].join("\n"),
    reply_markup: getBatchCollectKeyboard(),
  };
}

function buildBatchPartSavedReply(partRecord, deviceModel, pdfUrl = "") {
  const keyboardRows = [];
  if (pdfUrl) {
    keyboardRows.push([{ text: "📄 Otwórz PDF z linka", url: pdfUrl }]);
  }
  keyboardRows.push(
    [{ text: "🔁 Zmień model elektrośmiecia źródłowego", callback_data: "scan_batch_change_model" }],
    [{ text: "✅ Zakończ dodawanie", callback_data: "scan_batch_finish" }]
  );
  return {
    reply_text: [
      `✅ Zapisano część dla modelu *${deviceModel}*.`,
      partRecord?.part_name ? `Nazwa: ${partRecord.part_name}` : "",
      partRecord?.part_number ? `Oznaczenie: \`${partRecord.part_number}\`` : "",
      pdfUrl ? "Znalazłem też link do PDF dla tej części." : "PDF nie został znaleziony automatycznie.",
      "",
      "Możesz dodać kolejną część, zmienić model źródłowy albo zakończyć dodawanie.",
    ].filter(Boolean).join("\n"),
    reply_markup: withMenuRow(keyboardRows),
  };
}

async function startBatchWithModel(env, chatId, userId, deviceModel, source = "known_device") {
  const normalizedModel = String(deviceModel || "").trim();
  await closeAllUserSessions(env, chatId, userId);
  await activateBatchCollectSession(env, chatId, userId, {
    device_model: normalizedModel,
    source,
  });
  return buildBatchCollectReply(normalizedModel);
}


function getTelegramThrottleKey(message) {
  if (message.chat_id && message.user_id) {
    return `${message.chat_id}:${message.user_id}`;
  }
  if (message.chat_id) {
    return `chat:${message.chat_id}`;
  }
  if (message.user_id) {
    return `user:${message.user_id}`;
  }
  return "unknown";
}

function elapsedSecondsSince(isoTimestamp) {
  if (typeof isoTimestamp !== "string" || !isoTimestamp.trim()) {
    return null;
  }
  const parsed = Date.parse(isoTimestamp);
  if (Number.isNaN(parsed)) {
    return null;
  }
  return Math.floor((Date.now() - parsed) / 1000);
}

async function ensureTelegramThrottleSchema(db) {
  await db.prepare(
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
  ).run();
}

async function checkTelegramThrottle(env, message) {
  const db = env.DB;
  if (!db) {
    return { allowed: true, reason: "no_db" };
  }

  const throttleWindowSeconds = parsePositiveInteger(
    env.TELEGRAM_MIN_INTERVAL_SECONDS,
    60
  );
  if (throttleWindowSeconds <= 0) {
    return { allowed: true, reason: "disabled" };
  }

  await ensureTelegramThrottleSchema(db);

  const throttleKey = getTelegramThrottleKey(message);
  const row = await db.prepare(
    `
    SELECT last_accepted_at
    FROM telegram_issue_throttle
    WHERE throttle_key = ?
    `
  ).bind(throttleKey).first();

  if (row?.last_accepted_at) {
    const elapsedSeconds = elapsedSecondsSince(row.last_accepted_at);
    if (elapsedSeconds !== null && elapsedSeconds < throttleWindowSeconds) {
      return {
        allowed: false,
        reason: "too_many_requests",
        retry_after_seconds: throttleWindowSeconds - elapsedSeconds,
      };
    }
  }

  return {
    allowed: true,
    throttleKey,
    throttleWindowSeconds,
  };
}

async function recordTelegramThrottle(env, message, throttleKey) {
  const db = env.DB;
  if (!db) {
    return;
  }

  await ensureTelegramThrottleSchema(db);
  await db.prepare(
    `
    INSERT INTO telegram_issue_throttle (
      throttle_key,
      last_accepted_at,
      last_message_id,
      last_update_id,
      message_count
    ) VALUES (?, ?, ?, ?, 1)
    ON CONFLICT(throttle_key) DO UPDATE SET
      last_accepted_at = excluded.last_accepted_at,
      last_message_id = excluded.last_message_id,
      last_update_id = excluded.last_update_id,
      message_count = telegram_issue_throttle.message_count + 1
    `
  ).bind(
    throttleKey,
    new Date().toISOString(),
    message.message_id || null,
    message.update_id || null
  ).run();
}

function collectInboundMessages(payload) {
  const result = [];
  const candidates = [
    payload.message,
    payload.edited_message,
    payload.channel_post,
    payload.edited_channel_post,
  ];

  for (const item of candidates) {
    if (!item) continue;

    const rawText = item.text || item.caption; // Handle captions for photos
    const chatId = item.chat?.id !== undefined ? String(item.chat.id) : null;
    const userId = item.from?.id !== undefined ? String(item.from.id) : null;
    const messageId = item.message_id || null;
    const sanitizedInput = rawText
      ? sanitizeUserInput(rawText, {
          chat_id: chatId,
          user_id: userId,
          message_id: messageId,
        })
      : null;
    const text = sanitizedInput ? sanitizedInput.safeText : null;
    const inputBlocked = Boolean(sanitizedInput?.wasBlocked);
    const photo = item.photo; // Array of PhotoSize
    const document = item.document;
    const voice = item.voice;
    const audio = item.audio;

    if (typeof text !== "string" && !inputBlocked && !photo && !document && !voice && !audio) {
      continue;
    }

    let fileId = null;
    let mimeType = null;
    let fileName = null;

    if (photo && photo.length > 0) {
      // Get the largest photo size
      fileId = photo[photo.length - 1].file_id;
      mimeType = "image/jpeg";
    } else if (voice) {
      fileId = voice.file_id;
      mimeType = voice.mime_type || "audio/ogg";
    } else if (audio) {
      fileId = audio.file_id;
      mimeType = audio.mime_type || "audio/mpeg";
      fileName = audio.file_name || null;
    } else if (document) {
      fileId = document.file_id;
      mimeType = document.mime_type;
      fileName = document.file_name;
    }

    result.push({
      update_id: payload.update_id || null,
      message_id: messageId,
      text: text || null,
      input_blocked: inputBlocked,
      input_blocked_reply: sanitizedInput?.wrappedText || null,
      file_id: fileId,
      file_name: fileName,
      mime_type: mimeType,
      is_audio: Boolean(voice || audio),
      date: item.date || null,
      chat_id: chatId,
      chat_type: item.chat?.type || null,
      user_id: userId,
      username: item.from?.username || null,
      first_name: item.from?.first_name || null,
    });
  }

  return result;
}

async function createGitHubIssue(env, draft) {
  const owner = (env.GITHUB_REPO_OWNER || "").trim();
  const repo = (env.GITHUB_REPO_NAME || "").trim();
  const token = env.GITHUB_TOKEN;

  if (!owner || !repo) {
    throw new Error("Brak konfiguracji repozytorium GitHub dla integracji Telegram.");
  }
  if (!token) {
    throw new Error("Brak sekretu GITHUB_TOKEN dla integracji Telegram.");
  }

  const response = await fetchWithTimeout(`https://api.github.com/repos/${owner}/${repo}/issues`, {
    method: "POST",
    headers: {
      accept: "application/vnd.github+json",
      authorization: `Bearer ${token}`,
      "content-type": "application/json; charset=utf-8",
      "user-agent": "straz-przyszlosci-telegram-bridge",
      "x-github-api-version": "2022-11-28",
    },
    body: JSON.stringify({
      title: draft.title,
      body: draft.body,
      labels: draft.labels,
    }),
  }, 15000);

  const payload = await response.json();
  if (!response.ok) {
    const message =
      payload?.message || "GitHub API odrzuciło próbę utworzenia Issue.";
    throw new Error(message);
  }

  return payload;
}

function getExpectedTelegramWebhookPath(env) {
  const pathSegment = (env.TELEGRAM_WEBHOOK_PATH_SEGMENT || "").trim();
  if (pathSegment) {
    return `/integrations/telegram/webhook/${pathSegment}`;
  }
  return "/integrations/telegram/webhook";
}

export function isTelegramWebhookRequest(url, env) {
  return url.pathname === getExpectedTelegramWebhookPath(env);
}

async function verifyTelegramSecretToken(request, env) {
  const expected = (env.TELEGRAM_WEBHOOK_SECRET_TOKEN || "").trim();
  if (!expected) {
    return true;
  }

  const received =
    request.headers.get("X-Telegram-Bot-Api-Secret-Token") ||
    request.headers.get("x-telegram-bot-api-secret-token");
  if (!received || received.length !== expected.length) {
    return false;
  }
  if (typeof crypto !== "undefined" && crypto.subtle) {
    try {
      const a = new TextEncoder().encode(received);
      const b = new TextEncoder().encode(expected);
      return crypto.subtle.timingSafeEqual(a, b);
    } catch (_e) {
      // Fallback to constant-time comparison
    }
  }
  let result = 0;
  for (let i = 0; i < received.length; i++) {
    result |= received.charCodeAt(i) ^ expected.charCodeAt(i);
  }
  return result === 0;
}

function buildIssueReplyText(kind, payload = {}) {
  if (kind === "created") {
    const issueNumber = payload.issue_number ? ` #${payload.issue_number}` : "";
    const issueUrl = payload.issue_url ? `\n${payload.issue_url}` : "";
    return `Zgłoszenie przyjęte.${issueNumber ? ` Utworzono Issue${issueNumber}.` : ""}${issueUrl}`;
  }

  if (kind === "dry_run") {
    return "Zgłoszenie przeszło moderację i redakcję, ale bot działa w trybie testowym, więc Issue nie zostało utworzone.";
  }

  if (kind === "issues_disabled") {
    return 'Kanał GitHub Issues jest aktualnie wyłączony. Możesz nadal rozmawiać z botem albo wrócić później z prefiksem "Pomysl:" lub "Uwaga:".';
  }

  if (kind === "error") {
    return "Nie udało się zapisać zgłoszenia w repozytorium. Spróbuj ponownie za chwilę.";
  }

  if (kind === "unrecognized") {
    return 'Jeśli chcesz utworzyć GitHub Issue, wyślij wiadomość zaczynającą się od "Pomysl: ..." albo "Uwaga: ...". Jeśli chcesz onboarding lub zwykłą rozmowę, napisz po prostu normalnie.';
  }

  if (kind === "ai_unavailable") {
    let msg = "Serwis AI jest chwilowo niedostępny. Spróbuj ponownie za chwilę.";
    if (payload.error) {
      msg += `\n\n❌ Błąd: \`${payload.error}\``;
    }
    if (payload.location) {
      msg += `\n📍 Lokalizacja: \`${payload.location}\``;
    }
    return msg;
  }

  return null;
}

function isTelegramIntegrationEnabled(env) {
  return isTruthy(env.TELEGRAM_ISSUES_ENABLED || "") || isTruthy(env.TELEGRAM_AI_ENABLED || "");
}

async function processIssueMessage(env, message, classification, dryRun) {
  if (!isTruthy(env.TELEGRAM_ISSUES_ENABLED || "")) {
    const notificationSent = await sendTelegramReply(
      env,
      message,
      buildIssueReplyText("issues_disabled"),
      getMainMenuKeyboard()
    );
    return {
      update_id: message.update_id,
      message_id: message.message_id,
      status: "issues_disabled",
      notification_sent: notificationSent,
    };
  }

  const throttleCheck = await checkTelegramThrottle(env, message);
  if (!throttleCheck.allowed) {
    const notificationSent = await sendTelegramReply(
      env,
      message,
      buildIssueThrottleReply(throttleCheck.retry_after_seconds || null),
      getMainMenuKeyboard()
    );
    return {
      update_id: message.update_id,
      message_id: message.message_id,
      status: "throttled",
      retry_after_seconds: throttleCheck.retry_after_seconds || null,
      kind: classification.kind,
      notification_sent: notificationSent,
    };
  }

  const history = isTruthy(env.TELEGRAM_AI_ENABLED || "")
    ? await loadTelegramChatHistory(env, message)
    : [];

  let moderation;
  try {
    moderation = await moderateIssueCandidate(env, classification, message, history);
  } catch (error) {
    const notificationSent = await sendTelegramReply(
      env,
      message,
      buildIssueReplyText("ai_unavailable", {
        error: error instanceof Error ? error.message : String(error),
        location: "moderateIssueCandidate"
      }),
      getMainMenuKeyboard()
    );
    return {
      update_id: message.update_id,
      message_id: message.message_id,
      status: "ai_unavailable",
      kind: classification.kind,
      error: error instanceof Error ? error.message : "ai_unavailable",
      notification_sent: notificationSent,
    };
  }

  await recordIssueModerationAudit(env, moderation);
  const moderationReply = buildIssueModerationReply(moderation);
  if (moderationReply) {
    const notificationSent = await sendTelegramReply(env, message, moderationReply);
    return {
      update_id: message.update_id,
      message_id: message.message_id,
      status: moderation.decision,
      kind: classification.kind,
      reason_code: moderation.reason_code,
      reason_text: moderation.reason_text,
      notification_sent: notificationSent,
    };
  }

  const draft = await draftIssueBody(env, classification, history);
  const issueDraft = {
    title: buildIssueTitle(classification),
    body: buildIssueBody(message, classification, draft),
    labels: getConfiguredLabels(classification.kind, env),
  };

  if (dryRun) {
    await recordTelegramThrottle(env, message, throttleCheck.throttleKey);
    const notificationSent = await sendTelegramReply(
      env,
      message,
      buildIssueReplyText("dry_run")
    );
    return {
      update_id: message.update_id,
      message_id: message.message_id,
      status: "dry_run",
      kind: classification.kind,
      title: issueDraft.title,
      notification_sent: notificationSent,
    };
  }

  let issue;
  try {
    issue = await createGitHubIssue(env, issueDraft);
  } catch (error) {
    const notificationSent = await sendTelegramReply(
      env,
      message,
      buildIssueReplyText("error"),
      getMainMenuKeyboard()
    );
    return {
      update_id: message.update_id,
      message_id: message.message_id,
      status: "error",
      kind: classification.kind,
      error: error instanceof Error ? error.message : "unknown_error",
      notification_sent: notificationSent,
    };
  }

  await recordTelegramThrottle(env, message, throttleCheck.throttleKey);
  const notificationSent = await sendTelegramReply(
    env,
    message,
    buildIssueReplyText("created", {
      issue_number: issue.number,
      issue_url: issue.html_url,
    }),
    getMainMenuKeyboard()
  );
  return {
    update_id: message.update_id,
    message_id: message.message_id,
    status: "created",
    kind: classification.kind,
    issue_number: issue.number,
    issue_url: issue.html_url,
    notification_sent: notificationSent,
  };
}

async function handleActiveSessions(env, message, ctx) {
  // --- SESJA ODCZYTU REZYSTORA ---
  const resistorSession = await getUserSession(env, message.chat_id, message.user_id, "resistor_wait_photo");
  if (resistorSession) {
    if (message.file_id || (message.text && !message.text.startsWith("/"))) {
      await closeUserSession(env, message.chat_id, message.user_id, "resistor_wait_photo");
      const result = await handleResistorAnalysis(env, message);
      if (result && result._resistor_edit_data) {
        // Fix: Don't store JSON in active_device_id (INTEGER FK). Use active_device_name (TEXT).
        const packedMetadata = JSON.stringify({
          ai: result._ai_resistor || null,
          edit: result._resistor_edit_data
        });
        await upsertUserSession(env, message.chat_id, message.user_id, "resistor_edit_bands", null, packedMetadata);
        delete result._resistor_edit_data;
        delete result._ai_resistor;
      }
      return result;
    } else if (message.text && message.text.startsWith("/")) {
      return null;
    } else {
      return {
        reply_text: "Oczekuję na zdjęcie rezystora lub wpisane kolory pasków. Czy chcesz przerwać?",
        reply_markup: {
          inline_keyboard: [[{ text: "❌ Anuluj", callback_data: "cancel_session:resistor_wait_photo" }]]
        }
      };
    }
  }

  // --- SESJA WERYFIKACJI REZYSTORA ---
  const editBandSession = await getUserSession(env, message.chat_id, message.user_id, "resistor_edit_bands");
  if (editBandSession) {
    if (message.text && !message.text.startsWith("/")) {
      let prevData = editBandSession.active_device_name || "";
      let aiInfoRaw = editBandSession.active_device_id || "";
      let aiInfo = null;

      // Backward compatibility & Packed metadata detection
      if (prevData.startsWith("{")) {
        try {
          const packed = JSON.parse(prevData);
          if (packed.ai || packed.edit) {
            aiInfo = packed.ai;
            prevData = packed.edit;
            aiInfoRaw = aiInfo ? JSON.stringify(aiInfo) : "";
          }
        } catch(_) {}
      }

      if (!aiInfo) {
        try { aiInfo = aiInfoRaw ? JSON.parse(aiInfoRaw) : null; } catch(_) {}
      }

      const aiValue = aiInfo ? aiInfo.value : null;
      const aiTolerance = aiInfo ? aiInfo.tolerance : null;
      const aiFormat = aiInfo ? aiInfo.code_format : null;
      const aiOhms = aiInfo ? aiInfo.value_ohm : null;
      const verText = runResistorVerification(aiValue, aiTolerance, aiFormat, prevData, message.text);
      await closeUserSession(env, message.chat_id, message.user_id, "resistor_edit_bands");
      
      const newMetadata = JSON.stringify({ ai: aiInfo, edit: prevData });
      await upsertUserSession(env, message.chat_id, message.user_id, "resistor_edit_bands", null, newMetadata);
      return {
        reply_text: verText,
        reply_markup: {
          inline_keyboard: [
            [{ text: "✏️ Edytuj kolory", callback_data: "resistor_edit_bands" }],
            [{ text: "📖 Legenda kolorów", callback_data: "resistor_legend" }],
            [{ text: "🏠 Menu główne", callback_data: "command_start" }]
          ]
        }
      };
    } else if (message.text && message.text.startsWith("/")) {
      return null;
    } else {
      let prevData = editBandSession.active_device_name || "";
      if (prevData.startsWith("{")) {
        try {
          const packed = JSON.parse(prevData);
          if (packed.edit) prevData = packed.edit;
        } catch(_) {}
      }
      const prevDisplay = prevData.replace(/^(THT|SMD):/, "").replace(/,/g, " → ");
      return {
        reply_text: `🔍 Weryfikacja rezystora\n\n📌 Rozpoznane kolory/kod: ${prevDisplay || "brak danych"}\n\nWpisz poprawione wartości (np. \`brązowy, czarny, czerwony, złoty\` lub \`103\`), a przeliczę algorytmem:`,
        reply_markup: {
          inline_keyboard: [[{ text: "📖 Legenda kolorów", callback_data: "resistor_legend" }], [{ text: "❌ Anuluj", callback_data: "cancel_session:resistor_edit_bands" }]]
        }
      };
    }
  }

  // --- SESJA ZGŁASZANIA POMYSŁU ---
  const issueSession = await getUserSession(env, message.chat_id, message.user_id, "issue_wait_idea");
  if (issueSession) {
    if (message.text && !message.text.startsWith("/")) {
      await closeUserSession(env, message.chat_id, message.user_id, "issue_wait_idea");
      const classification = { kind: "idea", label: "pomysł", content: message.text, original_text: message.text };
      const dryRun = isTruthy(env.TELEGRAM_ISSUES_DRY_RUN || "");
      const issueResult = await processIssueMessage(env, message, classification, dryRun);
      return { skip_reply: true, reply_text: "[Zgłoszenie przetworzone]", ...issueResult };
    }
  }

  // --- SESJA SKANU POJEDYNCZEJ CZĘŚCI: OCZEKIWANIE NA ZDJĘCIE ---
  const scanPartWaitPhotoSession = await getUserSession(env, message.chat_id, message.user_id, "scan_part_wait_photo");
  if (scanPartWaitPhotoSession) {
    if (message.text && message.text.startsWith("/")) {
      return null;
    }
    if (!message.file_id || message.mime_type === "application/pdf") {
      return {
        reply_text: "Dodaj zdjęcie części. W tym trybie nie obsługuję PDF.",
        reply_markup: getScanMenuKeyboard(),
      };
    }

    await closeUserSession(env, message.chat_id, message.user_id, "scan_part_wait_photo");
    await sendTelegramReply(env, message, "Otrzymałem zdjęcie części. Analizuję oznaczenia i komponenty...");
    const base64 = await fetchTelegramFileAsBase64(env, message.file_id);
    if (!base64) {
      return { reply_text: "Nie udało się pobrać zdjęcia części do analizy." };
    }

    const scanResult = await recognizePartForScanFlow(env, message, base64, { source: "single_part_scan" });
    if (scanResult.type === "preview" && scanResult.payload) {
      await upsertUserSession(env, message.chat_id, message.user_id, "scan_part_preview", null, createScanPartPayload(scanResult.payload));
      return {
        reply_text: scanResult.reply_text,
        reply_markup: getScanPartPreviewKeyboard(),
      };
    }
    if (scanResult.type === "existing_part" && scanResult.match?.id) {
      return {
        reply_text: scanResult.reply_text,
        reply_markup: getPartQuestionKeyboard(scanResult.match.id),
      };
    }
    return {
      reply_text: scanResult.reply_text || "Nie udało się przygotować podglądu części.",
      reply_markup: getScanMenuKeyboard(),
    };
  }

  // --- SESJA PODGLĄDU CZĘŚCI ---
  const scanPartPreviewSession = await getUserSession(env, message.chat_id, message.user_id, "scan_part_preview");
  if (scanPartPreviewSession) {
    if (message.text && message.text.startsWith("/")) {
      return null;
    }
    if (message.text || message.file_id) {
      return {
        reply_text: "Użyj przycisków pod wynikiem, aby dodać część do bazy albo poprawić rozpoznane oznaczenie.",
        reply_markup: getScanPartPreviewKeyboard(),
      };
    }
  }

  // --- SESJA EDYCJI PODGLĄDU CZĘŚCI ---
  const scanPartEditSession = await getUserSession(env, message.chat_id, message.user_id, "scan_part_edit");
  if (scanPartEditSession) {
    if (message.text && message.text.startsWith("/")) {
      return null;
    }
    if (!message.text) {
      return {
        reply_text: "Podaj poprawione oznaczenie części. Możesz wpisać samo oznaczenie albo format `Nazwa | Oznaczenie`.",
        reply_markup: withMenuRow([[{ text: "❌ Anuluj", callback_data: "cancel_session:scan_part_edit" }]]),
      };
    }

    const isValid = await validateManualEntry(env, message.text);
    if (!isValid) {
      return { reply_text: "🚫 To nie wygląda na sensowne oznaczenie części. Spróbuj ponownie albo anuluj edycję." };
    }

    const payload = readScanPartPayload(scanPartEditSession.active_device_name);
    const parts = String(message.text || "").split("|").map((item) => item.trim()).filter(Boolean);
    const nextPayload = {
      ...payload,
      part_name: parts.length > 1 ? parts[0] : (payload.part_name || "Część urządzenia"),
      part_number: parts.length > 1 ? parts.slice(1).join(" | ") : String(message.text || "").trim(),
    };
    await closeUserSession(env, message.chat_id, message.user_id, "scan_part_edit");
    await upsertUserSession(env, message.chat_id, message.user_id, "scan_part_preview", null, createScanPartPayload(nextPayload));
    return {
      reply_text: [
        "✏️ Zaktualizowałem podgląd części.",
        "",
        `Nazwa: ${nextPayload.part_name}`,
        nextPayload.part_number ? `Oznaczenie: \`${nextPayload.part_number}\`` : "",
      ].filter(Boolean).join("\n"),
      reply_markup: getScanPartPreviewKeyboard(),
    };
  }

  // --- SESJA OCZEKIWANIA NA MODEL DLA POJEDYNCZEJ CZĘŚCI ---
  const scanPartWaitModelSession = await getUserSession(env, message.chat_id, message.user_id, "scan_part_wait_model");
  if (scanPartWaitModelSession) {
    if (message.text && message.text.startsWith("/")) {
      return null;
    }
    if (message.file_id && message.mime_type === "application/pdf") {
      return {
        reply_text: "Na tym etapie potrzebuję modelu elektrośmiecia źródłowego jako tekst albo zdjęcie etykiety. Jeśli go nie masz, kliknij *Nie mam modelu*.",
        reply_markup: getScanPartModelKeyboard(),
      };
    }
    const payload = readScanPartPayload(scanPartWaitModelSession.active_device_name);

    if (message.file_id) {
      await sendTelegramReply(env, message, "Otrzymałem zdjęcie modelu. Rozpoznaję oznaczenie elektrośmiecia...");
      const base64 = await fetchTelegramFileAsBase64(env, message.file_id);
      if (!base64) {
        return { reply_text: "Nie udało się pobrać zdjęcia modelu do analizy." };
      }
      const modelResult = await recognizeDeviceForScanFlow(env, message, base64, { source: "single_part_model_photo" });
      if (modelResult.type === "preview" && modelResult.payload) {
        await closeUserSession(env, message.chat_id, message.user_id, "scan_part_wait_model");
        await upsertUserSession(
          env,
          message.chat_id,
          message.user_id,
          "scan_part_model_preview",
          null,
          createScanPartPayload({ ...payload, donor_device_model: modelResult.payload.device_model })
        );
        return {
          reply_text: modelResult.reply_text,
          reply_markup: getScanPartModelPreviewKeyboard(),
        };
      }
      return {
        reply_text: modelResult.reply_text || "Nie udało się rozpoznać modelu ze zdjęcia.",
        reply_markup: getScanPartModelKeyboard(),
      };
    }

    if (!message.text) {
      return {
        reply_text: "Podaj model elektrośmiecia źródłowego tekstem, wyślij zdjęcie etykiety albo kliknij *Nie mam modelu*.",
        reply_markup: getScanPartModelKeyboard(),
      };
    }

    const isValid = await validateManualEntry(env, message.text);
    if (!isValid) {
      return { reply_text: "🚫 To nie wygląda na poprawny model urządzenia. Spróbuj ponownie albo użyj przycisku *Nie mam modelu*." };
    }

    await closeScanPartFlowSessions(env, message.chat_id, message.user_id);
    const saveResult = await saveScanFlowPart(env, message, payload, { donor_device_model: message.text });
    return saveResult.reply;
  }

  // --- SESJA PODGLĄDU MODELU DLA POJEDYNCZEJ CZĘŚCI ---
  const scanPartModelPreviewSession = await getUserSession(env, message.chat_id, message.user_id, "scan_part_model_preview");
  if (scanPartModelPreviewSession) {
    if (message.text && message.text.startsWith("/")) {
      return null;
    }
    if (message.text || message.file_id) {
      return {
        reply_text: "Użyj przycisków pod wynikiem, aby potwierdzić model albo poprawić rozpoznane oznaczenie.",
        reply_markup: getScanPartModelPreviewKeyboard(),
      };
    }
  }

  // --- SESJA EDYCJI MODELU DLA POJEDYNCZEJ CZĘŚCI ---
  const scanPartModelEditSession = await getUserSession(env, message.chat_id, message.user_id, "scan_part_model_edit");
  if (scanPartModelEditSession) {
    if (message.text && message.text.startsWith("/")) {
      return null;
    }
    if (!message.text) {
      return {
        reply_text: "Podaj poprawione oznaczenie modelu elektrośmiecia źródłowego.",
        reply_markup: withMenuRow([[{ text: "❌ Anuluj", callback_data: "cancel_session:scan_part_model_edit" }]]),
      };
    }

    const isValid = await validateManualEntry(env, message.text);
    if (!isValid) {
      return { reply_text: "🚫 To nie wygląda na poprawny model urządzenia. Spróbuj ponownie." };
    }

    const payload = readScanPartPayload(scanPartModelEditSession.active_device_name);
    await closeScanPartFlowSessions(env, message.chat_id, message.user_id);
    const saveResult = await saveScanFlowPart(env, message, payload, { donor_device_model: message.text });
    return saveResult.reply;
  }

  // --- SESJA PYTAŃ O CZĘŚĆ Z BAZY ---
  const partQuestionSession = await getUserSession(env, message.chat_id, message.user_id, "part_lookup_question");
  if (partQuestionSession) {
    if (message.text && message.text.startsWith("/")) {
      return null;
    }
    if (!message.text) {
      return {
        reply_text: "💬 Wpisz pytanie tekstem o tę część, a odpowiem na podstawie lokalnej bazy i znanych donorów.",
        reply_markup: getMainMenuKeyboard(),
      };
    }
    return await answerPartLookupQuestion(env, partQuestionSession, message.text);
  }

  // --- SESJA WYBORU MODELU BATCH: TEKST ---
  const batchWaitModelTextSession = await getUserSession(env, message.chat_id, message.user_id, "scan_batch_wait_model_text");
  if (batchWaitModelTextSession) {
    if (message.text && message.text.startsWith("/")) {
      return null;
    }
    if (!message.text) {
      return {
        reply_text: "Wpisz model elektrośmiecia ręcznie, najlepiej dokładne oznaczenie z etykiety.",
        reply_markup: getBatchChoiceKeyboard(),
      };
    }
    const isValid = await validateManualEntry(env, message.text);
    if (!isValid) {
      return { reply_text: "🚫 To nie wygląda na poprawny model. Spróbuj ponownie lub wróć do wyboru sposobu wprowadzenia modelu." };
    }
    await activateBatchCollectSession(env, message.chat_id, message.user_id, {
      device_model: message.text.trim(),
      source: "manual_text",
    });
    return buildBatchCollectReply(message.text.trim());
  }

  // --- SESJA WYBORU MODELU BATCH: ZDJĘCIE ---
  const batchWaitModelPhotoSession = await getUserSession(env, message.chat_id, message.user_id, "scan_batch_wait_model_photo");
  if (batchWaitModelPhotoSession) {
    if (message.text && message.text.startsWith("/")) {
      return null;
    }
    if (!message.file_id || message.mime_type === "application/pdf") {
      return {
        reply_text: "Dodaj zdjęcie etykiety lub obudowy urządzenia. Jeśli wolisz, możesz też wrócić do wpisania modelu ręcznie.",
        reply_markup: getBatchChoiceKeyboard(),
      };
    }
    await sendTelegramReply(env, message, "Otrzymałem zdjęcie modelu. Analizuję oznaczenie elektrośmiecia...");
    const base64 = await fetchTelegramFileAsBase64(env, message.file_id);
    if (!base64) {
      return { reply_text: "Nie udało się pobrać zdjęcia modelu do analizy." };
    }

    const modelResult = await recognizeDeviceForScanFlow(env, message, base64, { source: "batch_model_photo" });
    if (modelResult.type === "preview" && modelResult.payload) {
      await closeUserSession(env, message.chat_id, message.user_id, "scan_batch_wait_model_photo");
      await upsertUserSession(env, message.chat_id, message.user_id, "scan_batch_model_preview", null, createBatchScanPayload(modelResult.payload));
      return {
        reply_text: modelResult.reply_text,
        reply_markup: getBatchModelPreviewKeyboard(),
      };
    }
    return {
      reply_text: modelResult.reply_text || "Nie udało się rozpoznać modelu ze zdjęcia.",
      reply_markup: getBatchChoiceKeyboard(),
    };
  }

  // --- SESJA PODGLĄDU MODELU BATCH ---
  const batchModelPreviewSession = await getUserSession(env, message.chat_id, message.user_id, "scan_batch_model_preview");
  if (batchModelPreviewSession) {
    if (message.text && message.text.startsWith("/")) {
      return null;
    }
    if (message.text || message.file_id) {
      return {
        reply_text: "Użyj przycisków pod wynikiem, aby potwierdzić model albo go poprawić.",
        reply_markup: getBatchModelPreviewKeyboard(),
      };
    }
  }

  // --- SESJA EDYCJI MODELU BATCH ---
  const batchModelEditSession = await getUserSession(env, message.chat_id, message.user_id, "scan_batch_model_edit");
  if (batchModelEditSession) {
    if (message.text && message.text.startsWith("/")) {
      return null;
    }
    if (!message.text) {
      return {
        reply_text: "Podaj poprawione oznaczenie modelu elektrośmiecia źródłowego.",
        reply_markup: withMenuRow([[{ text: "❌ Anuluj", callback_data: "cancel_session:scan_batch_model_edit" }]]),
      };
    }
    const isValid = await validateManualEntry(env, message.text);
    if (!isValid) {
      return { reply_text: "🚫 To nie wygląda na poprawny model. Spróbuj ponownie." };
    }
    await activateBatchCollectSession(env, message.chat_id, message.user_id, {
      device_model: message.text.trim(),
      source: "manual_edit",
    });
    return buildBatchCollectReply(message.text.trim());
  }

  // --- SESJA DODAWANIA WIELU CZĘŚCI ---
  const batchCollectSession = await getUserSession(env, message.chat_id, message.user_id, "scan_batch_collect_parts");
  if (batchCollectSession) {
    if (message.text && message.text.startsWith("/")) {
      return null;
    }
    const batchPayload = readBatchScanPayload(batchCollectSession.active_device_name);

    if (message.file_id && message.mime_type !== "application/pdf") {
      await sendTelegramReply(env, message, "Otrzymałem zdjęcie części. Przygotowuję podgląd przed zapisem do bazy...");
      const base64 = await fetchTelegramFileAsBase64(env, message.file_id);
      if (!base64) {
        return { reply_text: "Nie udało się pobrać zdjęcia części do analizy." };
      }
      const scanResult = await recognizePartForScanFlow(env, message, base64, {
        source: "batch_part_scan",
        batch_mode: true,
        donor_device_model: batchPayload.device_model,
      });
      if (scanResult.type === "preview" && scanResult.payload) {
        await upsertUserSession(
          env,
          message.chat_id,
          message.user_id,
          "scan_part_preview",
          null,
          createScanPartPayload({
            ...scanResult.payload,
            donor_device_model: batchPayload.device_model,
            batch_mode: true,
          })
        );
        return {
          reply_text: scanResult.reply_text,
          reply_markup: getScanPartPreviewKeyboard(),
        };
      }
      if (scanResult.type === "existing_part" && scanResult.match?.id) {
        return {
          reply_text: scanResult.reply_text,
          reply_markup: getPartQuestionKeyboard(scanResult.match.id),
        };
      }
      return {
        reply_text: scanResult.reply_text || "Nie udało się przygotować podglądu części.",
        reply_markup: getBatchCollectKeyboard(),
      };
    }

    if (message.file_id && message.mime_type === "application/pdf") {
      return {
        reply_text: "W trybie dodawania wielu części przyjmuję zdjęcia części albo wpisane oznaczenia tekstem. PDF analizuj przez *Analiza Datasheet* z menu głównego.",
        reply_markup: getBatchCollectKeyboard(),
      };
    }

    if (!message.text) {
      return {
        reply_text: "Wpisz oznaczenie części w formacie `Nazwa | Oznaczenie` albo wyślij zdjęcie części.",
        reply_markup: getBatchCollectKeyboard(),
      };
    }

    const isValid = await validateManualEntry(env, message.text);
    if (!isValid) {
      return { reply_text: "🚫 To nie wygląda na sensowne oznaczenie części. Spróbuj ponownie." };
    }

    const manualPart = parseManualPartEntry(message.text);
    const saveResult = await saveScanFlowPart(env, message, {
      ...manualPart,
      description: "",
      category: "",
      keywords: [manualPart.part_name, manualPart.part_number],
      parameters: {},
      source: "batch_manual_text",
      batch_mode: true,
    }, {
      donor_device_model: batchPayload.device_model,
    });
    return buildBatchPartSavedReply(saveResult.part_record, batchPayload.device_model, saveResult.pdf_url);
  }

  // --- SESJA PYTAŃ O URZĄDZENIE Z BAZY ---
  const deviceQuestionSession = await getUserSession(env, message.chat_id, message.user_id, "device_lookup_question");
  if (deviceQuestionSession) {
    if (message.text && message.text.startsWith("/")) {
      return null;
    }
    if (!message.text) {
      return {
        reply_text: "💬 Wpisz pytanie tekstem o to urządzenie, a odpowiem na podstawie lokalnej bazy części i danych reuse.",
        reply_markup: getMainMenuKeyboard(),
      };
    }
    return await answerDeviceLookupQuestion(env, deviceQuestionSession, message.text);
  }

  // --- SESJA EDYCJI CZEŚCI ---
  const editSession = await getUserSession(env, message.chat_id, message.user_id, "recycled_parts_edit");
  if (editSession && message.text) {
    if (message.text.startsWith("/")) return null; // komendy anulują

    const isValid = await validateManualEntry(env, message.text);
    if (!isValid) {
      return { reply_text: "🚫 Wprowadzony tekst wydaje się być niepoprawny lub nie na temat. Spróbuj ponownie lub kliknij *Anuluj edycję*." };
    }

    const parts = (message.text || "").split("|").map(s => s.trim());
    const name = parts[0] || "Nieznana część";
    const number = parts.length > 1 ? parts[1] : "";
    
    const rawName = editSession.active_device_name || "";
    const submissionIdFromSession = rawName.startsWith("submission:")
      ? rawName.replace("submission:", "")
      : editSession.active_device_id;

    await env.DB.prepare("UPDATE recycled_device_submissions SET matched_part_name = ?, matched_part_number = ?, status = 'approved' WHERE id = ?")
      .bind(name, number, submissionIdFromSession).run();
    
        await closeUserSession(env, message.chat_id, message.user_id, "recycled_parts_edit");
        return { reply_text: `✅ Ręcznie zaktualizowano część: *${name}*. Status: Zatwierdzono.\n\nCo chcesz zrobić dalej?`, reply_markup: getMainMenuKeyboard() };
  } else if (editSession && message.file_id) {
    return { reply_text: "✏️ Oczekuję na tekst w formacie: `Nazwa | Numer`. Zdjęcia nie są obsługiwane w trybie edycji części." };
  }

  // --- SESJA DATASHEET (TARGET) ---
  const datasheetTargetSession = await getUserSession(env, message.chat_id, message.user_id, "datasheet_wait_target");
  if (datasheetTargetSession) {
    if ((message.text && !message.text.startsWith("/")) || message.file_id) {
      await closeUserSession(env, message.chat_id, message.user_id, "datasheet_wait_target");
      return await initDatasheetWorkflow(env, message, "datasheet_analysis");
    }
  }

  // --- SESJA DATASHEET (MODEL) ---
  const datasheetSession = await getUserSession(env, message.chat_id, message.user_id, "datasheet_wait_model");
  if (datasheetSession) {
    if (message.text && message.text.startsWith("/")) {
      return null; // Komendy (np. /stop) niech anulują sesję normalnie
    }
    if (message.file_id && message.mime_type === "application/pdf") {
      return {
        reply_text: "Na tym etapie potrzebuję jeszcze *modelu elektrośmiecia*, z którego pochodzi część. Jeśli go nie znasz, kliknij *Nie znam modelu*, a przejdziemy do pytania o dokument.",
        reply_markup: getDatasheetModelKeyboard(),
      };
    }
    
    let deviceModel = message.text || "Zidentyfikowany ze zdjęcia";
    if (message.file_id) {
      await sendTelegramReply(env, message, "Otrzymałem zdjęcie. Identyfikuję model urządzenia...");
      const base64 = await fetchTelegramFileAsBase64(env, message.file_id);
      const vision = await recognizeDeviceAndListParts(env, message, base64);
      
      if (vision && vision.type === "resistor") {
        await closeUserSession(env, message.chat_id, message.user_id, "datasheet_wait_model");
        if (vision._resistor_edit_data) {
          const aiInfoStr = vision._ai_resistor ? JSON.stringify(vision._ai_resistor) : null;
          await upsertUserSession(env, message.chat_id, message.user_id, "resistor_edit_bands", aiInfoStr, vision._resistor_edit_data);
          delete vision._resistor_edit_data;
          delete vision._ai_resistor;
        }
        return vision;
      }
      
      deviceModel = vision.recognized_model || "Nieznany model ze zdjęcia";
    }
    
    await closeUserSession(env, message.chat_id, message.user_id, "datasheet_wait_model");
    return await handleFinalDatasheetRag(env, message, datasheetSession, deviceModel, ctx);
  }

  // --- SESJA DATASHEET (PYTANIE) ---
  const questionSession = await getUserSession(env, message.chat_id, message.user_id, "datasheet_wait_question");
  if (questionSession) {
    if (message.text && message.text.startsWith("/")) {
      return null;
    }
    if (message.file_id && message.mime_type === "application/pdf") {
      const ingest = await attachPdfToDatasheetSession(env, message, questionSession);
      return {
        reply_text: [
          "📄 Przyjąłem Twój PDF, zeskanowałem go i zaktualizowałem dane części w bazie.",
          ingest?.payload?.scan_summary ? `Opis z dokumentu: ${ingest.payload.scan_summary}` : "",
          "",
          "Teraz wpisz pytanie, na które mam odpowiedzieć na podstawie tego dokumentu.",
        ].filter(Boolean).join("\n"),
        reply_markup: getMainMenuKeyboard(),
      };
    }
    if (!message.text) {
      return { reply_text: "✍️ Wpisz pytanie tekstem (np. \"Jaki jest pinout?\") lub prześlij plik PDF z dokumentacją." };
    }
    return await handleFinalDatasheetRagFinal(env, message, questionSession, message.text, ctx);
  }

  // --- SESJA DODAWANIA CZĘŚCI (MEDIA) ---
  const partsSession = await getUserSession(env, message.chat_id, message.user_id, "recycled_parts");
  if (partsSession) {
    if (message.file_id) {
      await sendTelegramReply(env, message, "Otrzymałem zdjęcie części. Analizuje oznaczenia i układy...");
      const base64 = await fetchTelegramFileAsBase64(env, message.file_id);
      if (base64) {
        return await recognizePartAndRecord(env, message, base64, partsSession, ctx);
      }
      return { reply_text: "Nie udało się pobrać zdjęcia części do analizy." };
    } else if (message.text && !message.text.startsWith("/")) {
      return {
        reply_text: "Oczekuję na zdjęcie części. Czy chcesz przerwać?",
        reply_markup: {
          inline_keyboard: [[{ text: "❌ Anuluj dodawanie", callback_data: "cancel_session:recycled_parts" }]]
        }
      };
    }
  }

  return null;
}

async function processConversationMessage(env, message, intent, ctx = null) {
  const plainCommand = getPlainCommandAlias(message.text);
  if (plainCommand) {
    return await processCommandMessage(env, message, plainCommand);
  }

  if (message.text && (message.text.toLowerCase().trim() === "menu" || message.text.toLowerCase().trim() === "pomoc" || message.text.toLowerCase().trim() === "start")) {
    return await processCommandMessage(env, message, "help");
  }

  if (!isTruthy(env.TELEGRAM_AI_ENABLED || "")) {
    const notificationSent = await sendTelegramReply(env, message, buildIssueReplyText("unrecognized"), getMainMenuKeyboard());
    return {
      update_id: message.update_id,
      message_id: message.message_id,
      status: "ignored_unrecognized_format",
      notification_sent: notificationSent,
    };
  }

  const limitCheck = await checkTelegramChatRateLimit(env, message);
  if (!limitCheck.allowed) {
    const notificationSent = await sendTelegramReply(env, message, buildChatThrottleReply(limitCheck.retry_after_seconds || null));
    return {
      update_id: message.update_id,
      message_id: message.message_id,
      status: "chat_rate_limited",
      retry_after_seconds: limitCheck.retry_after_seconds || null,
      notification_sent: notificationSent,
    };
  }

  const history = await loadTelegramChatHistory(env, message);

  try {
    if (message.is_audio || String(message.mime_type || "").startsWith("audio/") || message.mime_type === "application/ogg") {
      const response = {
        reply_text: "❌ Kod błędu: `UNSUPPORTED-AUDIO`\nTen bot obsługuje tekst, zdjęcia i PDF, ale nie obsługuje dźwięku.",
        reply_markup: getMainMenuKeyboard(),
      };
      await saveTelegramConversation(env, message, intent, "[audio]", response.reply_text);
      const notificationSent = await sendTelegramReply(env, message, response.reply_text, response.reply_markup);
      return {
        update_id: message.update_id,
        message_id: message.message_id,
        status: "audio_not_supported",
        notification_sent: notificationSent,
      };
    }

    // 1. Handle Active Sessions
    let response = await handleActiveSessions(env, message, ctx);

    // 2. Handle Base Intents if no session active
    if (!response) {
      switch (intent) {
        case "device_media":
          await sendTelegramReply(env, message, "Otrzymałem zdjęcie. Proszę o chwilę, analizuję model urządzenia...");
          const base64 = await fetchTelegramFileAsBase64(env, message.file_id);
          response = base64 
            ? await recognizeDeviceAndListParts(env, message, base64)
            : { reply_text: "Nie udało się pobrać zdjęcia do analizy." };
          break;
        case "datasheet_analysis":
          response = await initDatasheetWorkflow(env, message, intent);
          break;
        case "resistor_reader":
          response = await handleResistorAnalysis(env, message);
          break;
        case "device_lookup":
          response = await handleRecycledKnowledgeLookup(env, message);
          break;
        case "onboarding":
          response = await recommendOnboardingPath(env, message, history);
          break;
      default:
        response = await generateChatReply(env, message, history);
    }

  if (response && response._resistor_edit_data) {
  const aiInfoStr = response._ai_resistor ? JSON.stringify(response._ai_resistor) : null;
  await upsertUserSession(env, message.chat_id, message.user_id, "resistor_edit_bands", aiInfoStr, response._resistor_edit_data);
  delete response._resistor_edit_data;
  delete response._ai_resistor;
}

    // Jeśli jesteśmy w zwykłej konwersacji (generateChatReply), dołączamy menu główne
      if (intent === "unknown" && response && !response.reply_markup) {
        // Menu jest już przypinane wewnątrz buildCommandReply / generateChatReply w telegram_ai.js
      }
    }

    if (response && !response.skip_reply && !response.reply_markup) {
      response.reply_markup = getMainMenuKeyboard();
    } else if (response && !response.skip_reply && response.reply_markup?.inline_keyboard) {
      const hasMenu = response.reply_markup.inline_keyboard.some((row) =>
        Array.isArray(row) && row.some((button) => button?.callback_data === "command_start")
      );
      if (!hasMenu) {
        response.reply_markup = {
          inline_keyboard: [
            ...response.reply_markup.inline_keyboard,
            [{ text: "🏠 Menu główne", callback_data: "command_start" }],
          ],
        };
      }
    }

    await saveTelegramConversation(env, message, intent, message.text || "[media]", response.reply_text);
    let notificationSent = false;
    if (!response.skip_reply) {
      notificationSent = await sendTelegramReply(env, message, response.reply_text, response.reply_markup);
    }
    return {
      update_id: message.update_id,
      message_id: message.message_id,
      status:
        intent === "onboarding"
          ? "onboarding_replied"
          : intent === "device_media"
            ? "media_processed"
            : intent === "device_lookup"
              ? "lookup_replied"
              : "chat_replied",
      notification_sent: notificationSent,
    };
  } catch (error) {
    const errorString = error instanceof Error ? error.message : JSON.stringify(error);
    console.error(`[DEBUG AI ERROR]: ${errorString}`);
    const notificationSent = await sendTelegramReply(
      env,
      message,
      buildIssueReplyText("ai_unavailable", {
        error: errorString,
        location: "processConversationMessage"
      }),
      getMainMenuKeyboard()
    );
    return {
      update_id: message.update_id,
      message_id: message.message_id,
      status: "ai_unavailable",
      error: error instanceof Error ? error.message : "ai_unavailable",
      notification_sent: notificationSent,
    };
  }
}

async function processCommandMessage(env, message, command) {
  // Każda komenda przerywa aktywne sesje
  await closeAllUserSessions(env, message.chat_id, message.user_id);

  if (command === "reset" || command === "restart") {
    await clearTelegramChatHistory(env, message);
    await sendTelegramReply(env, message, "Zresetowałem całą historię i aktywne sesje. Możesz zacząć od nowa.", getMainMenuKeyboard());
    return { status: "reset_complete" };
  } else if (command === "start" || command === "help" || command === "menu") {
    // Sesje zamknięte wyżej
  } else if (command === "stop" || command === "anuluj") {
    const session = await getUserSession(env, message.chat_id, message.user_id, "recycled_parts");
    await closeAllUserSessions(env, message.chat_id, message.user_id);
    
    let stopMsg = "Zakończyłem aktywne sesje i anulowałem operację.";
    if (session && session.active_device_id) {
      const device = await getDeviceById(env, session.active_device_id);
      if (device) {
        const partsInfo = await getPartsForModel(env, device.model);
        if (partsInfo) {
          stopMsg += "\n\nOto aktualna zawartość katalogu dla tego modelu:\n" + buildDeviceCatalogReply(partsInfo);
        }
      }
    }
    await sendTelegramReply(env, message, stopMsg, getMainMenuKeyboard());
    return { status: "session_closed" };
  } else if (command === "niemammodelu") {
    const session = await getUserSession(env, message.chat_id, message.user_id, "datasheet_wait_model");
    if (session) {
        await closeUserSession(env, message.chat_id, message.user_id, "datasheet_wait_model");
        const res = await handleFinalDatasheetRag(env, message, session, "Nieznany (użytkownik nie posiada)");
        // handleFinalDatasheetRag wysyła "Przyjąłem model", ale prompt do pytania musimy wysłać sami
        if (res && res.reply_text) {
            await sendTelegramReply(env, message, res.reply_text, getMainMenuKeyboard());
        }
        return { status: "datasheet_processed" };
    }
    await sendTelegramReply(env, message, "Nie jesteś obecnie w procesie analizy części. Wyślij PDF lub nazwę części, aby zacząć.", getMainMenuKeyboard());
    return { status: "command_ignored" };
  }
  const reply = buildCommandReply(command);
  const replyText = typeof reply === "object" ? reply.text : reply;
  const replyMarkup = typeof reply === "object" ? reply.reply_markup : getMainMenuKeyboard();
  const notificationSent = await sendTelegramReply(env, message, replyText, replyMarkup);
  return {
    update_id: message.update_id,
    message_id: message.message_id,
    status: `command_${command}`,
    notification_sent: notificationSent,
  };
}

const CALLBACK_HANDLERS = {
  "recycled_add_parts": async (env, id, chat_id, user_id, message, data) => {
    const parts = data.split(":");
    const deviceId = parts.length > 1 ? parseInt(parts[1]) : NaN;
    if (isNaN(deviceId)) {
      await answerCallbackQuery(env, id, "Błędny identyfikator urządzenia.");
      return;
    }
    const device = await getDeviceById(env, deviceId);
    const deviceName = device ? `${device.brand || ""} ${device.model || ""}`.trim() : null;
    const reply = await startBatchWithModel(env, chat_id, user_id, deviceName || "urządzenia", "known_device");
    await answerCallbackQuery(env, id, "Tryb dodawania wielu części aktywny.");
    await sendTelegramReply(env, { chat_id, message_id: message.message_id }, reply.reply_text, reply.reply_markup);
  },
  "recycled_add_parts_unknown": async (env, id, chat_id, user_id, message, data) => {
    const deviceName = data.substring("recycled_add_parts_unknown:".length);
    const reply = await startBatchWithModel(env, chat_id, user_id, deviceName, "recognized_unknown_device");
    await answerCallbackQuery(env, id, "Tryb dodawania wielu części aktywny.");
    await sendTelegramReply(env, { chat_id, message_id: message.message_id }, reply.reply_text, reply.reply_markup);
  },
  "recycled_cancel": async (env, id, chat_id, user_id, message) => {
    await closeUserSession(env, chat_id, user_id, "recycled_parts");
    await closeBatchFlowSessions(env, chat_id, user_id);
    await answerCallbackQuery(env, id, "Anulowano.");
    await sendTelegramReply(env, { chat_id, message_id: message.message_id }, "Przerwałem proces dodawania części. Wybierz, co chcesz zrobić dalej:", getMainMenuKeyboard());
  },
  "recycled_show_info": async (env, id, chat_id, user_id, message, data) => {
    const parts = data.split(":");
    const deviceId = parts.length > 1 ? parseInt(parts[1]) : NaN;
    if (isNaN(deviceId)) {
      await answerCallbackQuery(env, id, "Błędny identyfikator urządzenia.");
      return;
    }
    await closeUserSession(env, chat_id, user_id, "recycled_parts");
    const device = await getDeviceById(env, deviceId);
    if (device) {
      const partsInfo = await getPartsForModel(env, device.model);
      await answerCallbackQuery(env, id, "Wyświetlam katalog.");
      await sendTelegramReply(env, { chat_id, message_id: message.message_id }, buildDeviceCatalogReply(partsInfo));
    } else {
      await answerCallbackQuery(env, id, "Błąd.");
      await sendTelegramReply(env, { chat_id, message_id: message.message_id }, "Nie znaleziono urządzenia.");
    }
  },
  "recycled_part_add": async (env, id, chat_id, user_id, message, data) => {
    const submissionId = data.split(":")[1];
    await env.DB.prepare("UPDATE recycled_device_submissions SET status = 'approved' WHERE id = ?").bind(submissionId).run();
    await answerCallbackQuery(env, id, "Zatwierdzono!");
    await sendTelegramReply(env, { chat_id: chat_id, message_id: message?.message_id }, "✅ Część została zatwierdzona i dodana do bazy!");
  },
  "recycled_part_edit": async (env, id, chat_id, user_id, message, data) => {
    const submissionId = data.split(":")[1];
    await upsertUserSession(env, chat_id, user_id, "recycled_parts_edit", null, `submission:${submissionId}`);
    await answerCallbackQuery(env, id, "Tryb edycji aktywny.");
    await sendTelegramReply(env, { chat_id: chat_id, message_id: message?.message_id }, "Proszę, podaj poprawną nazwę i numer części w formacie: `Nazwa | Numer` (np. `Karta WiFi | 631954-001`).", {
      inline_keyboard: [[{ text: "❌ Anuluj edycję", callback_data: "cancel_session:recycled_parts_edit" }]]
    });
  },
  "menu_scan": async (env, id, chat_id, user_id, message, data) => {
    await closeAllUserSessions(env, chat_id, user_id);
    await answerCallbackQuery(env, id, "Instrukcja skanowania.");
    await sendTelegramReply(
      env,
      { chat_id, message_id: message?.message_id },
      "Prześlij mi zdjęcie elementu elektronicznego (procesora) lub pojedynczego układu. Rozpoznam komponenty, omówię je, a w razie potrzeby poproszę o założenie nowej bazy urządzenia.",
      getScanMenuKeyboard()
    );
  },
  "scan_part_start": async (env, id, chat_id, user_id, message) => {
    await closeAllUserSessions(env, chat_id, user_id);
    await upsertUserSession(env, chat_id, user_id, "scan_part_wait_photo");
    await answerCallbackQuery(env, id, "Czekam na zdjęcie części.");
    await sendTelegramReply(env, { chat_id, message_id: message?.message_id }, "Dodaj zdjęcie części.", getScanMenuKeyboard());
  },
  "scan_part_edit": async (env, id, chat_id, user_id, message) => {
    const session = await getUserSession(env, chat_id, user_id, "scan_part_preview");
    if (!session) {
      await answerCallbackQuery(env, id, "Brak aktywnego podglądu części.");
      return;
    }
    await closeUserSession(env, chat_id, user_id, "scan_part_preview");
    await upsertUserSession(env, chat_id, user_id, "scan_part_edit", null, session.active_device_name);
    await answerCallbackQuery(env, id, "Edytuj oznaczenie części.");
    await sendTelegramReply(
      env,
      { chat_id, message_id: message?.message_id },
      "Podaj poprawione oznaczenie części. Możesz wpisać samo oznaczenie albo format `Nazwa | Oznaczenie`.",
      withMenuRow([[{ text: "❌ Anuluj", callback_data: "cancel_session:scan_part_edit" }]])
    );
  },
  "scan_part_add": async (env, id, chat_id, user_id, message) => {
    const session = await getUserSession(env, chat_id, user_id, "scan_part_preview");
    if (!session) {
      await answerCallbackQuery(env, id, "Brak aktywnego podglądu części.");
      return;
    }
    const payload = readScanPartPayload(session.active_device_name);
    await closeUserSession(env, chat_id, user_id, "scan_part_preview");

    if (payload.batch_mode && payload.donor_device_model) {
      const saveResult = await saveScanFlowPart(env, { chat_id, user_id, message_id: message?.message_id }, payload, {
        donor_device_model: payload.donor_device_model,
      });
      const reply = buildBatchPartSavedReply(saveResult.part_record, payload.donor_device_model, saveResult.pdf_url);
      await answerCallbackQuery(env, id, "Część zapisana.");
      await sendTelegramReply(
        env,
        { chat_id, message_id: message?.message_id },
        reply.reply_text,
        reply.reply_markup
      );
      return;
    }

    await upsertUserSession(env, chat_id, user_id, "scan_part_wait_model", null, createScanPartPayload(payload));
    await answerCallbackQuery(env, id, "Podaj model źródłowy.");
    await sendTelegramReply(
      env,
      { chat_id, message_id: message?.message_id },
      "Podaj model elektrośmiecia źródłowego tekstem, wyślij zdjęcie modelu/etykiety albo kliknij *Nie mam modelu*.",
      getScanPartModelKeyboard()
    );
  },
  "scan_part_no_model": async (env, id, chat_id, user_id, message) => {
    const session = await getUserSession(env, chat_id, user_id, "scan_part_wait_model");
    if (!session) {
      await answerCallbackQuery(env, id, "Brak aktywnej sesji dodawania części.");
      return;
    }
    const payload = readScanPartPayload(session.active_device_name);
    await closeScanPartFlowSessions(env, chat_id, user_id);
    const saveResult = await saveScanFlowPart(env, { chat_id, user_id, message_id: message?.message_id }, payload, {
      donor_device_model: "bez urządzenia źródłowego",
    });
    await answerCallbackQuery(env, id, "Zapisuję bez urządzenia źródłowego.");
    await sendTelegramReply(env, { chat_id, message_id: message?.message_id }, saveResult.reply.reply_text, saveResult.reply.reply_markup);
  },
  "scan_part_model_use": async (env, id, chat_id, user_id, message) => {
    const session = await getUserSession(env, chat_id, user_id, "scan_part_model_preview");
    if (!session) {
      await answerCallbackQuery(env, id, "Brak aktywnego podglądu modelu.");
      return;
    }
    const payload = readScanPartPayload(session.active_device_name);
    await closeScanPartFlowSessions(env, chat_id, user_id);
    const saveResult = await saveScanFlowPart(env, { chat_id, user_id, message_id: message?.message_id }, payload, {
      donor_device_model: payload.donor_device_model,
    });
    await answerCallbackQuery(env, id, "Część zapisana.");
    if (payload.batch_mode && payload.donor_device_model) {
      const reply = buildBatchPartSavedReply(saveResult.part_record, payload.donor_device_model, saveResult.pdf_url);
      await sendTelegramReply(env, { chat_id, message_id: message?.message_id }, reply.reply_text, reply.reply_markup);
      return;
    }
    await sendTelegramReply(env, { chat_id, message_id: message?.message_id }, saveResult.reply.reply_text, saveResult.reply.reply_markup);
  },
  "scan_part_model_edit": async (env, id, chat_id, user_id, message) => {
    const session = await getUserSession(env, chat_id, user_id, "scan_part_model_preview");
    if (!session) {
      await answerCallbackQuery(env, id, "Brak aktywnego podglądu modelu.");
      return;
    }
    await closeUserSession(env, chat_id, user_id, "scan_part_model_preview");
    await upsertUserSession(env, chat_id, user_id, "scan_part_model_edit", null, session.active_device_name);
    await answerCallbackQuery(env, id, "Edytuj model elektrośmiecia.");
    await sendTelegramReply(
      env,
      { chat_id, message_id: message?.message_id },
      "Podaj poprawione oznaczenie modelu elektrośmiecia źródłowego.",
      withMenuRow([[{ text: "❌ Anuluj", callback_data: "cancel_session:scan_part_model_edit" }]])
    );
  },
  "part_question_start": async (env, id, chat_id, user_id, message, data) => {
    const partId = Number.parseInt(data.split(":")[1] || "", 10);
    if (!Number.isFinite(partId)) {
      await answerCallbackQuery(env, id, "Błędny identyfikator części.");
      return;
    }
    await upsertUserSession(env, chat_id, user_id, "part_lookup_question", partId, JSON.stringify({ version: 1, part_id: partId }));
    await answerCallbackQuery(env, id, "Zadaj pytanie o część.");
    await sendTelegramReply(env, { chat_id, message_id: message?.message_id }, "💬 Wpisz pytanie o tę część, a odpowiem na podstawie lokalnej bazy i znanych donorów.", getMainMenuKeyboard());
  },
  "scan_batch_start": async (env, id, chat_id, user_id, message) => {
    await closeAllUserSessions(env, chat_id, user_id);
    await answerCallbackQuery(env, id, "Tryb dodawania wielu części.");
    await sendTelegramReply(
      env,
      { chat_id, message_id: message?.message_id },
      "Ten tryb służy do przypisywania wielu części do jednego modelu elektrośmiecia. Najpierw podaj model urządzenia źródłowego ręcznie albo rozpoznaj go ze zdjęcia.",
      getBatchChoiceKeyboard()
    );
  },
  "scan_batch_enter_model": async (env, id, chat_id, user_id, message) => {
    await closeBatchFlowSessions(env, chat_id, user_id);
    await upsertUserSession(env, chat_id, user_id, "scan_batch_wait_model_text");
    await answerCallbackQuery(env, id, "Wpisz model ręcznie.");
    await sendTelegramReply(env, { chat_id, message_id: message?.message_id }, "Wpisz dokładny model elektrośmiecia źródłowego ręcznie.", getBatchChoiceKeyboard());
  },
  "scan_batch_photo_model": async (env, id, chat_id, user_id, message) => {
    await closeBatchFlowSessions(env, chat_id, user_id);
    await upsertUserSession(env, chat_id, user_id, "scan_batch_wait_model_photo");
    await answerCallbackQuery(env, id, "Wyślij zdjęcie modelu.");
    await sendTelegramReply(env, { chat_id, message_id: message?.message_id }, "Dodaj zdjęcie etykiety albo obudowy urządzenia, a rozpoznam model.", getBatchChoiceKeyboard());
  },
  "scan_batch_model_use": async (env, id, chat_id, user_id, message) => {
    const session = await getUserSession(env, chat_id, user_id, "scan_batch_model_preview");
    if (!session) {
      await answerCallbackQuery(env, id, "Brak aktywnego podglądu modelu.");
      return;
    }
    const payload = readBatchScanPayload(session.active_device_name);
    const reply = await startBatchWithModel(env, chat_id, user_id, payload.device_model, payload.source || "image_confirmed");
    await answerCallbackQuery(env, id, "Model zaakceptowany.");
    await sendTelegramReply(env, { chat_id, message_id: message?.message_id }, reply.reply_text, reply.reply_markup);
  },
  "scan_batch_model_edit": async (env, id, chat_id, user_id, message) => {
    const session = await getUserSession(env, chat_id, user_id, "scan_batch_model_preview");
    if (!session) {
      await answerCallbackQuery(env, id, "Brak aktywnego podglądu modelu.");
      return;
    }
    await closeUserSession(env, chat_id, user_id, "scan_batch_model_preview");
    await upsertUserSession(env, chat_id, user_id, "scan_batch_model_edit", null, session.active_device_name);
    await answerCallbackQuery(env, id, "Edytuj model.");
    await sendTelegramReply(
      env,
      { chat_id, message_id: message?.message_id },
      "Podaj poprawione oznaczenie modelu elektrośmiecia źródłowego.",
      withMenuRow([[{ text: "❌ Anuluj", callback_data: "cancel_session:scan_batch_model_edit" }]])
    );
  },
  "scan_batch_change_model": async (env, id, chat_id, user_id, message) => {
    await closeBatchFlowSessions(env, chat_id, user_id);
    await answerCallbackQuery(env, id, "Zmieniam model źródłowy.");
    await sendTelegramReply(
      env,
      { chat_id, message_id: message?.message_id },
      "Podaj nowy model elektrośmiecia źródłowego ręcznie albo rozpoznaj go ze zdjęcia.",
      getBatchChoiceKeyboard()
    );
  },
  "scan_batch_finish": async (env, id, chat_id, user_id, message) => {
    await closeBatchFlowSessions(env, chat_id, user_id);
    await closeScanPartFlowSessions(env, chat_id, user_id);
    await answerCallbackQuery(env, id, "Zakończono dodawanie.");
    await sendTelegramReply(env, { chat_id, message_id: message?.message_id }, "Zakończyłem tryb dodawania wielu części. Wybierz, co chcesz zrobić dalej:", getMainMenuKeyboard());
  },
  "menu_datasheet": async (env, id, chat_id, user_id, message, data) => {
    await closeAllUserSessions(env, chat_id, user_id);
    await upsertUserSession(env, chat_id, user_id, "datasheet_wait_target");
    await answerCallbackQuery(env, id, "Analiza Datasheet.");
    await sendTelegramReply(env, { chat_id, message_id: message?.message_id }, "Prześlij mi plik PDF z dokumentacją albo wpisz *oznaczenie części* (np. `NE555`, `TDA7294`). Gdy wpiszesz część tekstem, zapytam osobno o *model elektrośmiecia*, z którego pochodzi.", {
      inline_keyboard: [[{ text: "❌ Anuluj", callback_data: "cancel_session:datasheet_wait_target" }]]
    });
  },
  "menu_search": async (env, id, chat_id, user_id, message, data) => {
    await closeAllUserSessions(env, chat_id, user_id);
    await answerCallbackQuery(env, id, "Instrukcja Wyszukiwania.");
    await sendTelegramReply(env, { chat_id, message_id: message?.message_id }, "Wpisz zapytanie (np. `Jakie części ma Xbox 360?` albo `Szukam kondensatora 10uF`), a ja przeszukam nasz zrecyklingowany katalog.");
  },
  "menu_issue": async (env, id, chat_id, user_id, message, data) => {
    await closeAllUserSessions(env, chat_id, user_id);
    await upsertUserSession(env, chat_id, user_id, "issue_wait_idea");
    await answerCallbackQuery(env, id, "Tryb zgłaszania pomysłu.");
    await sendTelegramReply(env, { chat_id, message_id: message?.message_id }, "Jasne! Opisz mi krótko swój pomysł lub uwagę. Co chciałbyś zgłosić do projektu?", {
      inline_keyboard: [[{ text: "❌ Anuluj", callback_data: "cancel_session:issue_wait_idea" }]]
    });
  },
  "menu_onboarding": async (env, id, chat_id, user_id, message, data) => {
    await closeAllUserSessions(env, chat_id, user_id);
    await answerCallbackQuery(env, id, "Onboarding.");
    await sendTelegramReply(env, { chat_id, message_id: message?.message_id }, "Napisz mi kilka słów o sobie, czym się zajmujesz lub co potrafisz, a ja zasugeruję Ci pasujące zadania i miejsce w projekcie Straż Przyszłości.");
  },
  "menu_resistor": async (env, id, chat_id, user_id, message, data) => {
  await closeAllUserSessions(env, chat_id, user_id);
  await upsertUserSession(env, chat_id, user_id, "resistor_wait_photo");
  await answerCallbackQuery(env, id, "Odczyt rezystora.");
  await sendTelegramReply(env, { chat_id, message_id: message?.message_id }, "Prześlij mi proszę zdjęcie rezystora (THT lub SMD) *ALBO* wpisz jego kolory (np. `brązowy, czarny, czerwony, złoty`), a ja odczytam jego wartość.", {
    inline_keyboard: [[{ text: "📖 Legenda kolorów", callback_data: "resistor_legend" }], [{ text: "❌ Anuluj", callback_data: "cancel_session:resistor_wait_photo" }]]
  });
},
  "datasheet_start_search": async (env, id, chat_id, user_id, message, data) => {
    const partQuery = data.substring("datasheet_start_search:".length);
    const mockMessage = { chat_id, user_id, text: partQuery };
    const res = await initDatasheetWorkflow(env, mockMessage, "datasheet_analysis");
    await answerCallbackQuery(env, id, "Uruchamiam asystenta datasheet.");
    await sendTelegramReply(env, { chat_id, message_id: message?.message_id }, res.reply_text, res.reply_markup);
  },
  "cancel_session": async (env, id, chat_id, user_id, message, data) => {
    const sessionType = data.split(":")[1] || "recycled_parts";
    await closeUserSession(env, chat_id, user_id, sessionType);
    await answerCallbackQuery(env, id, "Sesja została anulowana.");
    await sendTelegramReply(env, { chat_id, message_id: message?.message_id }, "Przerwałem proces. Wybierz, co chcesz zrobić dalej:", getMainMenuKeyboard());
  },
  "command_start": async (env, id, chat_id, user_id, message, data) => {
    await closeAllUserSessions(env, chat_id, user_id);
    await answerCallbackQuery(env, id, "Menu główne.");
    const startReply = buildCommandReply("start");
    await sendTelegramReply(env, { chat_id, message_id: message?.message_id }, startReply.text, startReply.reply_markup);
  },
  "resistor_legend": async (env, id, chat_id, user_id, message, data) => {
  await answerCallbackQuery(env, id, "Legenda kolorów.");
  await sendTelegramReply(env, { chat_id, message_id: message?.message_id }, getResistorLegendText(), {
    inline_keyboard: [[{ text: "🏠 Menu główne", callback_data: "command_start" }]]
  });
},
  "datasheet_no_model": async (env, id, chat_id, user_id, message, data) => {
    const session = await getUserSession(env, chat_id, user_id, "datasheet_wait_model");
    if (!session) {
      await answerCallbackQuery(env, id, "Brak aktywnej sesji datasheet.");
      return;
    }
    await closeUserSession(env, chat_id, user_id, "datasheet_wait_model");
    const mockMessage = { chat_id, user_id, message_id: message?.message_id };
    const res = await handleFinalDatasheetRag(env, mockMessage, session, "Nieznany (użytkownik nie posiada)");
    await answerCallbackQuery(env, id, "Kontynuuję bez modelu.");
    if (res && res.reply_text) {
      await sendTelegramReply(env, { chat_id, message_id: message?.message_id }, res.reply_text, res.reply_markup);
    }
  },
  "resistor_edit_bands": async (env, id, chat_id, user_id, message, data) => {
  const existingSession = await getUserSession(env, chat_id, user_id, "resistor_edit_bands");
  const prevData = existingSession ? existingSession.active_device_name : null;
  const aiInfoStr = existingSession ? existingSession.active_device_id : null;
  const prevDisplay = prevData ? prevData.replace(/^(THT|SMD):/, "").replace(/,/g, " → ") : "";
  await upsertUserSession(env, chat_id, user_id, "resistor_edit_bands", aiInfoStr || null, prevData || "");
  await answerCallbackQuery(env, id, "Weryfikacja algorytmiczna.");
  const editMsg = prevDisplay
    ? `🔍 *Weryfikacja algorytmiczna*\n\n📌 Rozpoznane kolory/kod: ${prevDisplay}\n\nWpisz poprawione wartości (np. \`brązowy, czarny, czerwony, złoty\` lub \`103\`), a przeliczę algorytmem i porównam z AI:`
    : "🔍 Wpisz kolory pasków (np. `brązowy, czarny, czerwony, złoty`) lub kod SMD (np. `103`), a przeliczę algorytmem:";
  await sendTelegramReply(env, { chat_id, message_id: message?.message_id }, editMsg, {
    inline_keyboard: [[{ text: "📖 Legenda kolorów", callback_data: "resistor_legend" }], [{ text: "❌ Anuluj", callback_data: "cancel_session:resistor_edit_bands" }]]
  });
  },
  "datasheet_ask": async (env, id, chat_id, user_id, message, data) => {
    const partQuery = data.substring("datasheet_ask:".length);
    const activeSession =
      (await getUserSession(env, chat_id, user_id, "datasheet_wait_model")) ||
      (await getUserSession(env, chat_id, user_id, "datasheet_wait_question"));
    const payload = buildDatasheetQuestionPayload(partQuery, activeSession, {
      source: "callback_ask",
    });
    await closeUserSession(env, chat_id, user_id, "datasheet_wait_model");
    await upsertUserSession(env, chat_id, user_id, "datasheet_wait_question", null, JSON.stringify(payload));
    await answerCallbackQuery(env, id, "Zadaj pytanie.");
    await sendTelegramReply(env, { chat_id, message_id: message?.message_id }, `💡 Analiza datasheet dla *${partQuery}*. Wpisz pytanie (np. "Jaki jest pinout?", "Podaj napięcie zasilania"):`, getMainMenuKeyboard());
  },
  "datasheet_continue": async (env, id, chat_id, user_id, message, data) => {
    const partQuery = data.substring("datasheet_continue:".length);
    
    // Próbujemy odzyskać metadane z ostatniego zgłoszenia dla tego użytkownika
    const lastSub = await env.DB.prepare(`
      SELECT * FROM recycled_device_submissions 
      WHERE chat_id = ? AND user_id = ? 
      AND (matched_part_name = ? OR matched_part_number = ?)
      ORDER BY created_at DESC LIMIT 1
    `).bind(chat_id, user_id, partQuery, partQuery).first();

    const metadata = buildDatasheetQuestionPayloadFromSubmission(lastSub, partQuery);

    await upsertUserSession(env, chat_id, user_id, "datasheet_wait_question", null, JSON.stringify(metadata));
    await answerCallbackQuery(env, id, "Kontynuacja analizy.");
    await sendTelegramReply(env, { chat_id, message_id: message?.message_id }, `💡 Kontynuuję analizę dla *${partQuery}*. O co chcesz zapytać?`, getMainMenuKeyboard());
  },
  "datasheet_continue_last": async (env, id, chat_id, user_id, message, data) => {
    const lastSub = await env.DB.prepare(`
      SELECT * FROM recycled_device_submissions
      WHERE chat_id = ? AND user_id = ?
      AND lookup_kind IN ('datasheet_rag_complete', 'datasheet_pdf_ingest')
      ORDER BY created_at DESC LIMIT 1
    `).bind(chat_id, user_id).first();

    if (!lastSub) {
      await answerCallbackQuery(env, id, "Brak ostatniej analizy.");
      await sendTelegramReply(
        env,
        { chat_id, message_id: message?.message_id },
        "Nie mam już zapisanej ostatniej analizy datasheet. Wyślij PDF albo wpisz oznaczenie części ponownie.",
        getMainMenuKeyboard()
      );
      return;
    }

    const metadata = buildDatasheetQuestionPayloadFromSubmission(lastSub);
    const partQuery = metadata.part_number || "ostatniej części";
    await upsertUserSession(env, chat_id, user_id, "datasheet_wait_question", null, JSON.stringify(metadata));
    await answerCallbackQuery(env, id, "Kontynuacja analizy.");
    await sendTelegramReply(env, { chat_id, message_id: message?.message_id }, `💡 Kontynuuję analizę dla *${partQuery}*. O co chcesz zapytać?`, getMainMenuKeyboard());
  }
};

async function handleTelegramCallback(env, callback, ctx = null) {
  const { id, from, message, data } = callback;
  const chat_id = message ? String(message.chat.id) : null;
  const user_id = String(from.id);

  if (!chat_id) {
    await answerCallbackQuery(env, id, "Ten przycisk nie jest już aktywny.");
    return jsonResponse({ status: "error", message: "no_chat_id" });
  }

  try {
    await removeInlineKeyboard(env, chat_id, message?.message_id);

    const actionPrefix = data.split(":")[0];
    const handler = CALLBACK_HANDLERS[actionPrefix];
    
    if (handler) {
      await handler(env, id, chat_id, user_id, message, data);
    } else {
      await sendTelegramReply(env, { chat_id, message_id: message?.message_id }, "Nieznana komenda.", getMainMenuKeyboard());
    }

    return jsonResponse({ status: "ok" });
  } catch (error) {
    const errorString = error instanceof Error ? error.message : String(error);
    await answerCallbackQuery(env, id, "Wystąpił błąd.");
    await sendTelegramReply(env, { chat_id, message_id: message?.message_id }, `⚠️ [CALLBACK ERROR]: ${errorString}`, getMainMenuKeyboard());
    return jsonResponse({ status: "error", error: errorString });
  }
}

async function answerCallbackQuery(env, callbackQueryId, text) {
  const botToken = env.TELEGRAM_BOT_TOKEN;
  await fetchWithTimeout(`https://api.telegram.org/bot${botToken}/answerCallbackQuery`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      callback_query_id: callbackQueryId,
      text: text
    })
  }, 10000);
}

async function removeInlineKeyboard(env, chat_id, message_id) {
  const botToken = env.TELEGRAM_BOT_TOKEN;
  if (!botToken || !chat_id || !message_id) return;

  await fetchWithTimeout(`https://api.telegram.org/bot${botToken}/editMessageReplyMarkup`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      chat_id: chat_id,
      message_id: message_id,
      reply_markup: {
        inline_keyboard: []
      }
    })
  }, 10000);
}

export function checkTelegramPayloadSize(request, env) {
  return checkPayloadSize(request, env, {
    envKey: "TELEGRAM_MAX_WEBHOOK_BODY_BYTES",
    fallbackKey: "MAX_WEBHOOK_BODY_BYTES",
    defaultMax: 5242880,
    responseFactory: (payload, status) =>
      jsonResponse({ error: `Request body too large. Max: ${payload.max_bytes} bytes.` }, status),
  });
}

export async function handleTelegramWebhook(request, env, ctx = null) {
  if (!isTelegramIntegrationEnabled(env)) {
    return jsonResponse(
      {
        status: "disabled",
        message: "Integracja Telegram jest wyłączona.",
      },
      200
    );
  }

  if (!(await verifyTelegramSecretToken(request, env))) {
    return jsonResponse({ error: "Nieprawidłowy sekret webhooka Telegram." }, 403);
  }

  const sizeCheck = checkTelegramPayloadSize(request, env);
  if (sizeCheck) return sizeCheck;

  let payload;
  try {
    payload = await request.json();
    console.log("INBOUND WEBHOOK PAYLOAD:", JSON.stringify(payload, null, 2));
  } catch (error) {
    return jsonResponse({ error: "Nieprawidłowy body JSON." }, 400);
  }

  // Handle Callback Queries (Buttons)
  if (payload.callback_query) {
    return await handleTelegramCallback(env, payload.callback_query, ctx);
  }

  const messages = collectInboundMessages(payload);
  const dryRun = isTruthy(env.TELEGRAM_ISSUES_DRY_RUN || "");
  const allowedChatIds = parseAllowedIds(env.TELEGRAM_ALLOWED_CHAT_IDS || "");

  if (!messages || messages.length === 0) {
    return jsonResponse({ status: "ok", message: "Brak komunikatów do przetworzenia." });
  }

  const results = [];
  for (const message of messages) {
    if (allowedChatIds && !allowedChatIds.has(String(message.chat_id))) {
      results.push({
        update_id: message.update_id,
        message_id: message.message_id,
        status: "ignored_chat_not_allowed",
      });
      continue;
    }
    if (message.input_blocked) {
      const notificationSent = await sendTelegramReply(
        env,
        message,
        message.input_blocked_reply || "Nie mogę przetworzyć tej wiadomości w obecnej formie.",
        getMainMenuKeyboard()
      );
      results.push({
        update_id: message.update_id,
        message_id: message.message_id,
        status: "input_blocked",
        notification_sent: notificationSent,
      });
      continue;
    }
    const routing = routeTelegramIntent(message);
    if (routing.intent === "command") {
      results.push(await processCommandMessage(env, message, routing.command));
      continue;
    }

    if (routing.intent === "issue") {
      results.push(
        await processIssueMessage(env, message, routing.classification, dryRun)
      );
      continue;
    }

    results.push(await processConversationMessage(env, message, routing.intent, ctx));
  }

  return jsonResponse(
    {
      status: "accepted",
      processed_messages: messages.length,
      dry_run: dryRun,
      ai_enabled: isTruthy(env.TELEGRAM_AI_ENABLED || ""),
      results,
    },
    200
  );
}
