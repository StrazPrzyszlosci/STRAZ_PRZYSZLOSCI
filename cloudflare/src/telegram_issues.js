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
  sanitizeTelegramReply,
} from "./telegram_ai.js";

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

async function sendTelegramReply(env, message, text) {
  const botToken = env.TELEGRAM_BOT_TOKEN;
  if (!botToken || !message?.chat_id || !text) {
    return false;
  }

  const response = await fetch(
    `https://api.telegram.org/bot${botToken}/sendMessage`,
    {
      method: "POST",
      headers: {
        "content-type": "application/json; charset=utf-8",
      },
      body: JSON.stringify({
        chat_id: message.chat_id,
        text: sanitizeTelegramReply(text, env),
        reply_to_message_id: message.message_id || undefined,
        allow_sending_without_reply: true,
        disable_web_page_preview: true,
      }),
    }
  );

  return response.ok;
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
    const text = item?.text;
    if (typeof text !== "string") {
      continue;
    }

    result.push({
      update_id: payload.update_id || null,
      message_id: item.message_id || null,
      text,
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
    return "Serwis AI jest chwilowo niedostępny. Spróbuj ponownie za chwilę.";
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
      buildIssueReplyText("issues_disabled")
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
      buildIssueThrottleReply(throttleCheck.retry_after_seconds || null)
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
      buildIssueReplyText("ai_unavailable")
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
      buildIssueReplyText("error")
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
    })
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

async function processConversationMessage(env, message, intent) {
  if (!isTruthy(env.TELEGRAM_AI_ENABLED || "")) {
    const notificationSent = await sendTelegramReply(
      env,
      message,
      buildIssueReplyText("unrecognized")
    );
    return {
      update_id: message.update_id,
      message_id: message.message_id,
      status: "ignored_unrecognized_format",
      notification_sent: notificationSent,
    };
  }

  const limitCheck = await checkTelegramChatRateLimit(env, message);
  if (!limitCheck.allowed) {
    const notificationSent = await sendTelegramReply(
      env,
      message,
      buildChatThrottleReply(limitCheck.retry_after_seconds || null)
    );
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
    const response =
      intent === "onboarding"
        ? await recommendOnboardingPath(env, message, history)
        : await generateChatReply(env, message, history);
    await saveTelegramConversation(env, message, intent, message.text, response.reply_text);
    const notificationSent = await sendTelegramReply(env, message, response.reply_text);
    return {
      update_id: message.update_id,
      message_id: message.message_id,
      status: intent === "onboarding" ? "onboarding_replied" : "chat_replied",
      notification_sent: notificationSent,
    };
  } catch (error) {
    const notificationSent = await sendTelegramReply(
      env,
      message,
      buildIssueReplyText("ai_unavailable")
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
  if (command === "reset") {
    await clearTelegramChatHistory(env, message);
  }
  const notificationSent = await sendTelegramReply(env, message, buildCommandReply(command));
  return {
    update_id: message.update_id,
    message_id: message.message_id,
    status: `command_${command}`,
    notification_sent: notificationSent,
  };
}

export async function handleTelegramWebhook(request, env) {
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
  } catch {
    return jsonResponse({ error: "Nieprawidłowy JSON webhooka Telegram." }, 400);
  }

  const messages = collectInboundMessages(payload);
  const dryRun = isTruthy(env.TELEGRAM_ISSUES_DRY_RUN || "");
  const allowedChatIds = parseAllowedIds(env.TELEGRAM_ALLOWED_CHAT_IDS || "");
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

    const routing = routeTelegramIntent(message.text);
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

    results.push(await processConversationMessage(env, message, routing.intent));
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
