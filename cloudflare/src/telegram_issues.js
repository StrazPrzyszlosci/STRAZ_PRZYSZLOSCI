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
  fetchTelegramFileAsBase64,
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
  attachPdfToDatasheetSession,
} from "./telegram_ai.js";
import { buildVerificationResultReply } from "./vision.js";
import { sanitizeTelegramReply, sendTelegramReply, getMainMenuKeyboard } from "./telegram_utils.js";

function jsonResponse(payload, status = 200) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
    },
  });
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
      message_count INTEGER NOT NULL DEFAULT 0
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

    const text = item.text || item.caption; // Handle captions for photos
    const photo = item.photo; // Array of PhotoSize
    const document = item.document;
    const voice = item.voice;
    const audio = item.audio;

    if (typeof text !== "string" && !photo && !document && !voice && !audio) {
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
      message_id: item.message_id || null,
      text: text || null,
      file_id: fileId,
      file_name: fileName,
      mime_type: mimeType,
      is_audio: Boolean(voice || audio),
      date: item.date || null,
      chat_id: item.chat?.id !== undefined ? String(item.chat.id) : null,
      chat_type: item.chat?.type || null,
      user_id: item.from?.id !== undefined ? String(item.from.id) : null,
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

  const response = await fetch(`https://api.github.com/repos/${owner}/${repo}/issues`, {
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
  });

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

function verifyTelegramSecretToken(request, env) {
  const expected = (env.TELEGRAM_WEBHOOK_SECRET_TOKEN || "").trim();
  if (!expected) {
    return true;
  }

  const received =
    request.headers.get("X-Telegram-Bot-Api-Secret-Token") ||
    request.headers.get("x-telegram-bot-api-secret-token");
  return received === expected;
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
        const aiInfoStr = result._ai_resistor ? JSON.stringify(result._ai_resistor) : null;
        await upsertUserSession(env, message.chat_id, message.user_id, "resistor_edit_bands", aiInfoStr, result._resistor_edit_data);
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
      const prevData = editBandSession.active_device_name || "";
      const aiInfoRaw = editBandSession.active_device_id || "";
      let aiInfo = null;
      try { aiInfo = aiInfoRaw ? JSON.parse(aiInfoRaw) : null; } catch(_) {}
      const aiValue = aiInfo ? aiInfo.value : null;
      const aiTolerance = aiInfo ? aiInfo.tolerance : null;
      const aiFormat = aiInfo ? aiInfo.code_format : null;
      const aiOhms = aiInfo ? aiInfo.value_ohm : null;
      const verText = runResistorVerification(aiValue, aiTolerance, aiFormat, prevData, message.text);
      await closeUserSession(env, message.chat_id, message.user_id, "resistor_edit_bands");
      const newEditData = prevData;
      await upsertUserSession(env, message.chat_id, message.user_id, "resistor_edit_bands", aiInfoRaw || null, newEditData);
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
      const prevData = editBandSession.active_device_name || "";
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
        reply_text: "Na tym etapie potrzebuję jeszcze *modelu elektrośmiecia*, z którego pochodzi część. Jeśli go nie znasz, kliknij *Nie znam modelu*, a PDF możesz wysłać w następnym kroku.",
        reply_markup: getMainMenuKeyboard(),
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

  if (command === "reset") {
    await clearTelegramChatHistory(env, message);
    await sendTelegramReply(env, message, "Zresetowałem całą historię i aktywne sesje.", getMainMenuKeyboard());
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
    await upsertUserSession(env, chat_id, user_id, "recycled_parts", deviceId, deviceName);
    await answerCallbackQuery(env, id, "Tryb dodawania części aktywny!");
    await sendTelegramReply(env, { chat_id, message_id: message.message_id }, `✅ Tryb dodawania części AKTYWNY dla: ${deviceName || "urządzenia"}. Każde kolejne zdjęcie zostanie przypisane do tego modelu.`, {
      inline_keyboard: [[{ text: "❌ Anuluj dodawanie", callback_data: "cancel_session:recycled_parts" }]]
    });
  },
  "recycled_add_parts_unknown": async (env, id, chat_id, user_id, message, data) => {
    const deviceName = data.substring("recycled_add_parts_unknown:".length);
    await upsertUserSession(env, chat_id, user_id, "recycled_parts", null, deviceName);
    await answerCallbackQuery(env, id, "Tryb dodawania części aktywny!");
    await sendTelegramReply(env, { chat_id, message_id: message.message_id }, `✅ Tryb dodawania części AKTYWNY dla: ${deviceName}. Każde kolejne zdjęcie zostanie przypisane do tego urządzenia.`, {
      inline_keyboard: [[{ text: "❌ Anuluj dodawanie", callback_data: "cancel_session:recycled_parts" }]]
    });
  },
  "recycled_cancel": async (env, id, chat_id, user_id, message) => {
    await closeUserSession(env, chat_id, user_id, "recycled_parts");
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
    await sendTelegramReply(env, { chat_id, message_id: message?.message_id }, "Prześlij mi zdjęcie płyty głównej (PCB) lub pojedynczego układu / rezystora. Rozpoznam komponenty, a w razie potrzeby poproszę o założenie nowej bazy urządzenia.", getMainMenuKeyboard());
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
    await upsertUserSession(env, chat_id, user_id, "datasheet_wait_question", null, JSON.stringify({
      version: 2,
      part_number: partQuery,
      master_part_id: null,
      donor_device_model: "",
      donor_device_id: null,
      pdf_url: "",
      pdf_file_id: "",
      db_hit: false,
      source: "callback_ask",
      file_name: "",
      scan_summary: "",
    }));
    await answerCallbackQuery(env, id, "Zadaj pytanie.");
    await sendTelegramReply(env, { chat_id, message_id: message?.message_id }, `💡 Analiza datasheet dla *${partQuery}*. Wpisz pytanie (np. "Jaki jest pinout?", "Podaj napięcie zasilania"):`, getMainMenuKeyboard());
  },
  "datasheet_continue": async (env, id, chat_id, user_id, message, data) => {
    const partQuery = data.substring("datasheet_continue:".length);
    await upsertUserSession(env, chat_id, user_id, "datasheet_wait_question", null, JSON.stringify({
      version: 2,
      part_number: partQuery,
      master_part_id: null,
      donor_device_model: "",
      donor_device_id: null,
      pdf_url: "",
      pdf_file_id: "",
      db_hit: false,
      source: "callback_continue",
      file_name: "",
      scan_summary: "",
    }));
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
  await fetch(`https://api.telegram.org/bot${botToken}/answerCallbackQuery`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      callback_query_id: callbackQueryId,
      text: text
    })
  });
}

async function removeInlineKeyboard(env, chat_id, message_id) {
  const botToken = env.TELEGRAM_BOT_TOKEN;
  if (!botToken || !chat_id || !message_id) return;

  await fetch(`https://api.telegram.org/bot${botToken}/editMessageReplyMarkup`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      chat_id: chat_id,
      message_id: message_id,
      reply_markup: {
        inline_keyboard: []
      }
    })
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

  if (!verifyTelegramSecretToken(request, env)) {
    return jsonResponse({ error: "Nieprawidłowy sekret webhooka Telegram." }, 403);
  }

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
