import {
  buildCommandReply,
  buildIssueModerationReply,
  buildIssueThrottleReply,
  buildChatThrottleReply,
  checkTelegramChatRateLimit,
  clearTelegramChatHistory,
  draftIssueBody,
  generateChatReply,
  getResistorLegendText,
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
  recognizePartForScanFlow,
  recognizeDeviceForScanFlow,
  saveScanFlowPart,
  readScanPartPayload,
  createScanPartPayload,
  createBatchScanPayload,
  readBatchScanPayload,
  buildDeviceCatalogReply,
  getDeviceById,
  getPartsForModel,
  getUserSession,
  upsertUserSession,
  closeUserSession,
  closeAllUserSessions,
  handleResistorAnalysis,
  initDatasheetWorkflow,
  buildIssueTitle,
  buildIssueBody,
  answerDeviceLookupQuestion,
  answerPartLookupQuestion,
  runResistorVerification,
  validateManualEntry,
} from "./telegram_ai.js";
import { fetchWithTimeout, timingSafeEqualString } from "./base_utils.js";
import { jsonResponse } from "./security_headers.js";
import { checkPayloadSize } from "./payload_size.js";

const DISCORD_PLATFORM = "discord";

function jsonReply(data, status = 200, env = null, request = null) {
  return jsonResponse(data, status, env, request);
}

function convertKeyboardToButtons(inlineKeyboard) {
  if (!inlineKeyboard || !inlineKeyboard.length) return null;
  return {
    buttons: inlineKeyboard.map((row) =>
      row.map((btn) => ({
        label: btn.text.slice(0, 80),
        action: btn.url ? "url" : "callback",
        value: btn.callback_data || btn.url,
        style: "primary",
      }))
    ),
  };
}

function buildDiscordResponse(replyData) {
  if (typeof replyData === "string") {
    return { reply_text: replyData, reply_markup: null };
  }
  const markup = replyData.reply_markup?.buttons
    ? replyData.reply_markup
    : convertKeyboardToButtons(replyData.reply_markup?.inline_keyboard);
  return {
    reply_text: replyData.reply_text || replyData.text,
    reply_markup: markup,
    provider_name: replyData.provider_name,
    model_name: replyData.model_name,
  };
}

function getDiscordMainMenuButtons() {
  return {
    buttons: [
      [
        { label: "Skanuj Urzadzenie", action: "callback", value: "menu_scan", style: "primary" },
        { label: "Analiza Datasheet", action: "callback", value: "menu_datasheet", style: "primary" },
        { label: "Odczyt Rezystora", action: "callback", value: "menu_resistor", style: "primary" },
        { label: "Szukaj w Katalogu", action: "callback", value: "menu_search", style: "primary" },
      ],
      [
        { label: "Zglos Pomysl", action: "callback", value: "menu_issue", style: "secondary" },
        { label: "Onboarding", action: "callback", value: "menu_onboarding", style: "secondary" },
        { label: "Pomoc", action: "callback", value: "menu_help", style: "secondary" },
      ],
    ],
  };
}

function parseDiscordBody(body) {
  const text = body.text || body.content || "";
  const stripped = text.trim();

  let command = null;
  let classification = null;

  if (stripped.startsWith("!")) {
    const spaceIdx = stripped.indexOf(" ");
    command = spaceIdx > 1 ? stripped.slice(1, spaceIdx) : stripped.slice(1);
  }

  const lower = stripped.toLowerCase();
  if (!command && (lower.startsWith("pomysl:") || lower.startsWith("pomysł:"))) {
    classification = { kind: "idea", label: "Pomysł", content: stripped };
  } else if (!command && (lower.startsWith("uwaga:") || lower.startsWith("problem:") || lower.startsWith("błąd:") || lower.startsWith("blad:"))) {
    classification = { kind: "feedback", label: "Uwaga", content: stripped };
  }

  return {
    chat_id: body.chat_id || "",
    user_id: body.user_id || "",
    message_id: body.message_id || "",
    text: stripped,
    command,
    classification,
    attachments: body.attachments || [],
    username: body.username || "",
    callback_data: body.callback_data || null,
    type: body.type || "message",
  };
}

async function handleMessage(env, message) {
  if (message.type === "callback" && message.callback_data) {
    const callbackReply = await handleDiscordCallback(env, message);
    return jsonReply(buildDiscordResponse(callbackReply));
  }

  if (!message.text && !message.attachments?.length) {
    return jsonReply({ reply_text: null });
  }

  const sessionReply = await handleActiveDiscordSessions(env, message);
  if (sessionReply) {
    return jsonReply(buildDiscordResponse(sessionReply));
  }

  const routing = routeTelegramIntent(message);
  let replyData;

  if (routing.intent === "command") {
    replyData = await handleCommand(env, message, routing.command);
  } else if (routing.intent === "issue") {
    replyData = await handleIssue(env, message, routing.classification);
  } else {
    replyData = await handleConversation(env, message, routing.intent);
  }

  return jsonReply(buildDiscordResponse(replyData));
}

async function handleCommand(env, message, command) {
  switch (command) {
    case "start":
    case "menu":
    case "help":
    case "reset":
    case "stop": {
      await closeAllUserSessions(env, message.chat_id, message.user_id, DISCORD_PLATFORM);
      const reply = buildCommandReply(command);
      return reply;
    }
    case "scan":
    case "skanuj": {
      if (message.attachments?.length) {
        const attachment = message.attachments[0];
        const mimeType = attachment.contentType || "image/jpeg";
        if (mimeType.startsWith("image/")) {
          const base64 = await fetchDiscordAttachmentBase64(attachment.url);
          if (base64) {
            const msg = {
              ...message,
              file_id: attachment.url,
              mime_type: mimeType,
              file_name: attachment.name,
            };
            const result = await recognizeDeviceAndListParts(env, msg, base64);
            await upsertUserSession(env, message.chat_id, message.user_id, "recycled_parts", null, null, DISCORD_PLATFORM);
            return result;
          }
        }
      }
      return {
        reply_text: "Wyślij zdjęcie urządzenia/elektrośmiecia, a rozpoznam model i pokażę katalog części reuse. Możesz też dodać model jako podpis pod zdjęciem.",
      };
    }
    case "datasheet":
    case "pdf": {
      if (message.attachments?.length) {
        const att = message.attachments[0];
        const mimeType = att.contentType || "";
        if (mimeType === "application/pdf" || att.name?.toLowerCase().endsWith(".pdf")) {
          const msg = {
            ...message,
            file_id: att.url,
            mime_type: "application/pdf",
            file_name: att.name,
            caption: message.text,
          };
          return await initDatasheetWorkflow(env, msg, "datasheet");
        }
      }
      return {
        reply_text: [
          "📄 **Analiza Datasheet**",
          "",
          "Wyślij PDF datasheetu lub wpisz oznaczenie części.",
          "Przykład: `!datasheet LM358`",
        ].join("\n"),
      };
    }
    case "resistor":
    case "rezystor": {
      let resistorBase64 = null;
      const resistorImage = message.attachments?.find(a => (a.contentType || "").startsWith("image/"));
      if (resistorImage) {
        resistorBase64 = await fetchDiscordAttachmentBase64(resistorImage.url);
      }
      const result = await handleResistorAnalysis(env, message, resistorBase64);
      return result;
    }
    case "search":
    case "szukaj": {
      const rest = message.text.replace(/^!\w+\s*/, "").trim();
      if (rest) {
        const lookupMsg = { ...message, text: rest };
        return await handleRecycledKnowledgeLookup(env, lookupMsg);
      }
      return {
        reply_text: "🔍 **Szukaj w katalogu reuse** — wpisz model urządzenia lub oznaczenie części po komendzie, np. `!search ESP32`.",
      };
    }
    case "issue":
    case "zglos":
    case "pomysl":
    case "pomysł": {
      return {
        reply_text: [
          "💡 **Zgłoś pomysł/problem**",
          "",
          "Wpisz wiadomość z prefixem `Pomysl:` lub `Uwaga:`, np.:",
          "`Pomysl: dodać integrację z OctoPrint`",
          "`Uwaga: strona ładuje się wolno na Firefox`",
        ].join("\n"),
      };
    }
    default: {
      await closeAllUserSessions(env, message.chat_id, message.user_id, DISCORD_PLATFORM);
      const reply = buildCommandReply("start");
      return reply;
    }
  }
}

async function handleIssue(env, message, classification) {
  const dryRun = isTruthy(env.TELEGRAM_ISSUES_DRY_RUN || "");
  const issuesEnabled = isTruthy(env.TELEGRAM_ISSUES_ENABLED || "");

  if (!issuesEnabled && !dryRun) {
    return {
      reply_text: "Zgłaszanie pomysłów i uwag jest tymczasowo wyłączone.",
    };
  }

  const throttleWindow = parsePositiveInteger(env.TELEGRAM_MIN_INTERVAL_SECONDS, 60);
  if (throttleWindow > 0) {
    const throttle = await checkTelegramIssueThrottle(env, message, throttleWindow);
    if (!throttle.allowed) {
      return {
        reply_text: buildIssueThrottleReply(throttle.retry_after_seconds),
      };
    }
  }

  let history;
  try {
    history = await loadTelegramChatHistory(env, message, DISCORD_PLATFORM);
  } catch (_e) {
    history = [];
  }

  let moderation;
  try {
    moderation = await moderateIssueCandidate(env, classification, message, history);
  } catch (_e) {
    return {
      reply_text: "Przepraszam, nie mogę teraz przeanalizować Twojego zgłoszenia. Spróbuj ponownie za chwilę.",
    };
  }

  await recordIssueModerationAudit(env, moderation, DISCORD_PLATFORM);
  const reason = buildIssueModerationReply(moderation);

  if (reason) {
    return { reply_text: reason };
  }

  let draft;
  try {
    draft = await draftIssueBody(env, classification, history);
  } catch (_e) {
    return {
      reply_text: "Zaakceptowano zgłoszenie, ale wystąpił błąd przy redakcji treści. Zgłoszenie zostanie utworzone w trybie podstawowym.",
      provider_name: "local",
      model_name: "fallback",
    };
  }

  const actor = message.username || message.user_id;
  const title = buildIssueTitle(classification);
  const body = buildIssueBody(message, classification, draft);

  if (dryRun) {
    return {
      reply_text: [
        "📝 **Nowe zgłoszenie (DRY RUN)**",
        "",
        `**Tytuł**: ${title}`,
        `**Typ**: ${classification.label}`,
        "",
        "```",
        body.slice(0, 1800),
        "```",
        "",
        "Tryb dry-run — zgłoszenie NIE zostało utworzone na GitHub.",
        `Autor: ${actor}`,
      ].join("\n"),
    };
  }

  const githubResult = await createGitHubIssue(env, title, body, classification, ["discord", actor]);
  return {
    reply_text: githubResult.reply_text,
    provider_name: "github",
    model_name: "issues",
  };
}

async function handleConversation(env, message, intent) {
  const aiEnabled = isTruthy(env.TELEGRAM_AI_ENABLED || "");
  if (!aiEnabled) {
    return {
      reply_text: "AI chat jest tymczasowo wyłączony.",
    };
  }

  const rateLimit = await checkTelegramChatRateLimit(env, message, DISCORD_PLATFORM);
  if (!rateLimit.allowed) {
    return {
      reply_text: buildChatThrottleReply(rateLimit.retry_after_seconds),
    };
  }

  const history = await loadTelegramChatHistory(env, message, DISCORD_PLATFORM);

  const onboardingIntent = intent === "onboarding";
  let reply;
  if (onboardingIntent) {
    reply = await recommendOnboardingPath(env, message, history);
  } else {
    const sanitized = (message.text || "").slice(0, 4000);
    const msg = { ...message, text: sanitized };
    reply = await recommendOnboardingPath(env, msg, history);
    if (!reply || !reply.reply_text || reply.reply_text.length < 20) {
      reply = await generateChatReply(env, msg, history);
    }
  }

  await saveTelegramConversation(env, message, intent, message.text, reply.reply_text, DISCORD_PLATFORM);

  return reply;
}

async function checkTelegramIssueThrottle(env, message, windowSeconds) {
  const db = env.DB;
  if (!db) return { allowed: true };

  const throttleKey = `${message.chat_id}:${message.user_id}`;

  const row = await db.prepare(
    `SELECT last_accepted_at FROM telegram_issue_throttle WHERE throttle_key = ? AND platform = ?`
  ).bind(throttleKey, DISCORD_PLATFORM).first();

  const now = Date.now();
  if (row?.last_accepted_at) {
    const elapsed = now - Date.parse(row.last_accepted_at);
    if (!Number.isNaN(elapsed) && elapsed < windowSeconds * 1000) {
      return {
        allowed: false,
        retry_after_seconds: Math.ceil((windowSeconds * 1000 - elapsed) / 1000),
      };
    }
  }

  const nowIso = new Date(now).toISOString();
  await db.prepare(
    `
    INSERT INTO telegram_issue_throttle (throttle_key, last_accepted_at, platform)
    VALUES (?, ?, ?)
    ON CONFLICT(throttle_key) DO UPDATE SET
      last_accepted_at = excluded.last_accepted_at,
      platform = excluded.platform
    `
  ).bind(throttleKey, nowIso, DISCORD_PLATFORM).run();

  return { allowed: true };
}

async function fetchDiscordAttachmentBase64(url) {
  try {
    const resp = await fetchWithTimeout(url, {}, 30000);
    if (!resp.ok) return null;
    const arrayBuffer = await resp.arrayBuffer();
    const uint8 = new Uint8Array(arrayBuffer);
    let binary = "";
    for (let i = 0; i < uint8.length; i++) {
      binary += String.fromCharCode(uint8[i]);
    }
    return btoa(binary);
  } catch (_e) {
    return null;
  }
}

async function createGitHubIssue(env, title, body, classification, labels = []) {
  const token = env.GITHUB_TOKEN;
  const owner = env.GITHUB_REPO_OWNER;
  const repo = env.GITHUB_REPO_NAME;

  if (!token || !owner || !repo) {
    return { reply_text: "Brak konfiguracji GitHub. Zgłoszenie nie zostało utworzone." };
  }

  try {
      const resp = await fetchWithTimeout(`https://api.github.com/repos/${owner}/${repo}/issues`, {
        method: "POST",
        headers: {
          accept: "application/vnd.github+json",
          authorization: `Bearer ${token}`,
          "content-type": "application/json",
          "x-github-api-version": "2022-11-28",
        },
        body: JSON.stringify({ title, body, labels }),
      }, 15000);

    const data = await resp.json();
    if (resp.ok && data.html_url) {
      return {
        reply_text: `✅ Zgłoszenie utworzone: ${data.html_url}`,
      };
    }
    return {
      reply_text: `Błąd GitHub (${resp.status}): ${data.message || "Nieznany błąd"}. Spróbuj ponownie później.`,
    };
  } catch (error) {
    return {
      reply_text: "Nie udało się połączyć z GitHub. Spróbuj ponownie później.",
    };
  }
}

async function handleDiscordCallback(env, message) {
  const data = message.callback_data || "";
  const actionPrefix = data.split(":")[0];

  switch (actionPrefix) {
    case "command_start": {
      await closeAllUserSessions(env, message.chat_id, message.user_id, DISCORD_PLATFORM);
      const reply = buildCommandReply("start");
      return { reply_text: typeof reply === "object" ? reply.text || reply.reply_text : reply, reply_markup: getDiscordMainMenuButtons() };
    }
    case "menu_scan": {
      await closeAllUserSessions(env, message.chat_id, message.user_id, DISCORD_PLATFORM);
      return {
        reply_text: "Przeslij mi zdjecie elementu elektronicznego lub pojedynczego ukladu. Rozpoznam komponenty i omowie je.\n\n**Komendy:**\n`!scan` - skanuj urzadzenie",
        reply_markup: getDiscordMainMenuButtons(),
      };
    }
    case "menu_datasheet": {
      await closeAllUserSessions(env, message.chat_id, message.user_id, DISCORD_PLATFORM);
      await upsertUserSession(env, message.chat_id, message.user_id, "datasheet_wait_target", null, null, DISCORD_PLATFORM);
      return {
        reply_text: "Przeslij mi plik PDF z dokumentacja albo wpisz **oznaczenie czesci** (np. `NE555`, `TDA7294`).",
        reply_markup: getDiscordMainMenuButtons(),
      };
    }
    case "menu_resistor": {
      await closeAllUserSessions(env, message.chat_id, message.user_id, DISCORD_PLATFORM);
      await upsertUserSession(env, message.chat_id, message.user_id, "resistor_wait_photo", null, null, DISCORD_PLATFORM);
      return {
        reply_text: "Przeslij mi zdjecie rezystora (THT lub SMD) **ALBO** wpisz jego kolory (np. `brazowy, czarny, czerwony, zloty`).",
        reply_markup: getDiscordMainMenuButtons(),
      };
    }
    case "menu_search": {
      await closeAllUserSessions(env, message.chat_id, message.user_id, DISCORD_PLATFORM);
      return {
        reply_text: "Wpisz zapytanie, a ja przeszukam nasz zrecyklingowany katalog.\n\n**Komenda:** `!search ESP32`",
        reply_markup: getDiscordMainMenuButtons(),
      };
    }
    case "menu_issue": {
      await closeAllUserSessions(env, message.chat_id, message.user_id, DISCORD_PLATFORM);
      await upsertUserSession(env, message.chat_id, message.user_id, "issue_wait_idea", null, null, DISCORD_PLATFORM);
      return {
        reply_text: "Opisz mi krotko swoj pomysl lub uwage. Mozesz tez uzyc prefixu `Pomysl:` lub `Uwaga:` przed wiadomoscia.",
        reply_markup: getDiscordMainMenuButtons(),
      };
    }
    case "menu_onboarding": {
      await closeAllUserSessions(env, message.chat_id, message.user_id, DISCORD_PLATFORM);
      return {
        reply_text: "Napisz mi kilka slow o sobie, czym sie zajmujesz lub co potrafisz, a zasugeruje Ci pasujace zadania w projekcie Straz Przyszlosci.",
        reply_markup: getDiscordMainMenuButtons(),
      };
    }
    case "menu_help":
    case "menu_menu": {
      await closeAllUserSessions(env, message.chat_id, message.user_id, DISCORD_PLATFORM);
      const reply = buildCommandReply("help");
      return { reply_text: typeof reply === "object" ? reply.text || reply.reply_text : reply, reply_markup: getDiscordMainMenuButtons() };
    }
    case "cancel_session": {
      const sessionType = data.split(":").slice(1).join(":") || null;
      if (sessionType) {
        await closeUserSession(env, message.chat_id, message.user_id, sessionType, DISCORD_PLATFORM);
      }
      await closeAllUserSessions(env, message.chat_id, message.user_id, DISCORD_PLATFORM);
      return { reply_text: "Przerwano proces. Wybierz co chcesz zrobic dalej:", reply_markup: getDiscordMainMenuButtons() };
    }
    case "resistor_legend": {
      return { reply_text: getResistorLegendText(), reply_markup: getDiscordMainMenuButtons() };
    }
    case "resistor_edit_bands": {
      const session = await getUserSession(env, message.chat_id, message.user_id, "resistor_edit_bands", DISCORD_PLATFORM);
      if (!session) return { reply_text: "Brak aktywnej sesji edycji rezystora.", reply_markup: getDiscordMainMenuButtons() };
      await closeUserSession(env, message.chat_id, message.user_id, "resistor_edit_bands", DISCORD_PLATFORM);
      await upsertUserSession(env, message.chat_id, message.user_id, "resistor_wait_photo", null, null, DISCORD_PLATFORM);
      return { reply_text: "Przeslij nowe zdjecie rezystora lub wpisz kolory paskow ponownie.", reply_markup: getDiscordMainMenuButtons() };
    }
    case "recycled_show_info": {
      const deviceId = parseInt(data.split(":")[1]);
      if (isNaN(deviceId)) return { reply_text: "Bledny identyfikator urzadzenia.", reply_markup: getDiscordMainMenuButtons() };
      const device = await getDeviceById(env, deviceId);
      if (device) {
        const partsInfo = await getPartsForModel(env, device.model);
        return { reply_text: buildDeviceCatalogReply(partsInfo), reply_markup: getDiscordMainMenuButtons() };
      }
      return { reply_text: "Nie znaleziono urzadzenia.", reply_markup: getDiscordMainMenuButtons() };
    }
    case "recycled_add_parts": {
      const deviceId = parseInt(data.split(":")[1]);
      if (isNaN(deviceId)) return { reply_text: "Bledny identyfikator urzadzenia.", reply_markup: getDiscordMainMenuButtons() };
      const device = await getDeviceById(env, deviceId);
      const deviceName = device ? (device.brand || "") + " " + (device.model || "") : "urządzenia";
      await upsertUserSession(env, message.chat_id, message.user_id, "recycled_parts", deviceId, deviceName.trim(), DISCORD_PLATFORM);
      return { reply_text: "Tryb dodawania wielu czesci dla **" + deviceName.trim() + "** aktywny. Przeslij zdjecie czesci aby dodac.", reply_markup: getDiscordMainMenuButtons() };
    }
    case "recycled_add_parts_unknown": {
      const deviceName = data.substring("recycled_add_parts_unknown:".length);
      await upsertUserSession(env, message.chat_id, message.user_id, "recycled_parts", null, deviceName, DISCORD_PLATFORM);
      return { reply_text: "Tryb dodawania wielu czesci dla **" + deviceName + "** aktywny. Przeslij zdjecie czesci.", reply_markup: getDiscordMainMenuButtons() };
    }
    case "recycled_cancel": {
      await closeUserSession(env, message.chat_id, message.user_id, "recycled_parts", DISCORD_PLATFORM);
      return { reply_text: "Przerwano proces dodawania czesci.", reply_markup: getDiscordMainMenuButtons() };
    }
    case "recycled_part_add": {
      const submissionId = data.split(":")[1];
      if (!submissionId) return { reply_text: "Bledny identyfikator zgloszenia.", reply_markup: getDiscordMainMenuButtons() };
      await env.DB.prepare("UPDATE recycled_device_submissions SET status = 'approved' WHERE id = ?").bind(submissionId).run();
      return { reply_text: "Czesc zostala zatwierdzona i dodana do bazy.", reply_markup: getDiscordMainMenuButtons() };
    }
    case "recycled_part_edit": {
      const submissionId = data.split(":")[1];
      if (!submissionId) return { reply_text: "Bledny identyfikator zgloszenia.", reply_markup: getDiscordMainMenuButtons() };
      await upsertUserSession(env, message.chat_id, message.user_id, "recycled_parts_edit", null, "submission:" + submissionId, DISCORD_PLATFORM);
      return { reply_text: "Podaj poprawna nazwe i numer czesci w formacie: `Nazwa | Numer` (np. `Karta WiFi | 631954-001`).", reply_markup: getDiscordMainMenuButtons() };
    }
    case "part_question_start": {
      const partId = Number.parseInt(data.split(":")[1] || "", 10);
      if (!Number.isFinite(partId)) return { reply_text: "Bledny identyfikator czesci.", reply_markup: getDiscordMainMenuButtons() };
      await upsertUserSession(env, message.chat_id, message.user_id, "part_lookup_question", partId, JSON.stringify({ version: 1, part_id: partId }), DISCORD_PLATFORM);
      return { reply_text: "Wpisz pytanie o te czesc.", reply_markup: getDiscordMainMenuButtons() };
    }
    case "scan_part_start": {
      await closeAllUserSessions(env, message.chat_id, message.user_id, DISCORD_PLATFORM);
      await upsertUserSession(env, message.chat_id, message.user_id, "scan_part_wait_photo", null, null, DISCORD_PLATFORM);
      return { reply_text: "Dodaj zdjecie czesci elektronicznej, a rozpoznam jej oznaczenia.", reply_markup: getDiscordMainMenuButtons() };
    }
    case "scan_batch_start": {
      await closeAllUserSessions(env, message.chat_id, message.user_id, DISCORD_PLATFORM);
      return { reply_text: "Podaj model urzadzenia zrodlowego recznie albo rozpoznaj go ze zdjecia.", reply_markup: getDiscordMainMenuButtons() };
    }
    case "scan_part_edit": {
      const s = await getUserSession(env, message.chat_id, message.user_id, "scan_part_preview", DISCORD_PLATFORM);
      if (!s) return { reply_text: "Brak aktywnego podgladu czesci.", reply_markup: getDiscordMainMenuButtons() };
      await closeUserSession(env, message.chat_id, message.user_id, "scan_part_preview", DISCORD_PLATFORM);
      await upsertUserSession(env, message.chat_id, message.user_id, "scan_part_edit", null, s.active_device_name, DISCORD_PLATFORM);
      return { reply_text: "Podaj poprawione oznaczenie czesci. Format: `Nazwa | Oznaczenie`.", reply_markup: getDiscordMainMenuButtons() };
    }
    case "scan_part_add": {
      const session = await getUserSession(env, message.chat_id, message.user_id, "scan_part_preview", DISCORD_PLATFORM);
      if (!session) return { reply_text: "Brak aktywnego podgladu czesci.", reply_markup: getDiscordMainMenuButtons() };
      await closeUserSession(env, message.chat_id, message.user_id, "scan_part_preview", DISCORD_PLATFORM);
      const payload = readScanPartPayload(session.active_device_name);
      if (payload.batch_mode && payload.donor_device_model) {
        const saveResult = await saveScanFlowPart(env, { chat_id: message.chat_id, user_id: message.user_id }, payload, { donor_device_model: payload.donor_device_model });
        return { reply_text: saveResult.reply?.reply_text || "Czesc zapisana.", reply_markup: getDiscordMainMenuButtons() };
      }
      await upsertUserSession(env, message.chat_id, message.user_id, "scan_part_wait_model", null, createScanPartPayload(payload), DISCORD_PLATFORM);
      return { reply_text: "Podaj model elektrosmiecia zrodlowego lub wyslij zdjecie tabliczki.", reply_markup: getDiscordMainMenuButtons() };
    }
    case "scan_part_no_model": {
      const s = await getUserSession(env, message.chat_id, message.user_id, "scan_part_wait_model", DISCORD_PLATFORM);
      if (!s) return { reply_text: "Brak aktywnej sesji.", reply_markup: getDiscordMainMenuButtons() };
      const payload = readScanPartPayload(s.active_device_name);
      await closeUserSession(env, message.chat_id, message.user_id, "scan_part_wait_model", DISCORD_PLATFORM);
      const saveResult = await saveScanFlowPart(env, { chat_id: message.chat_id, user_id: message.user_id }, payload, { donor_device_model: "bez urzadzenia zrodlowego" });
      return { reply_text: saveResult.reply?.reply_text || "Zapisano.", reply_markup: getDiscordMainMenuButtons() };
    }
    case "scan_part_model_use": {
      const s = await getUserSession(env, message.chat_id, message.user_id, "scan_part_model_preview", DISCORD_PLATFORM);
      if (!s) return { reply_text: "Brak aktywnego podgladu modelu.", reply_markup: getDiscordMainMenuButtons() };
      const payload = readScanPartPayload(s.active_device_name);
      await closeUserSession(env, message.chat_id, message.user_id, "scan_part_model_preview", DISCORD_PLATFORM);
      await closeUserSession(env, message.chat_id, message.user_id, "scan_part_wait_model", DISCORD_PLATFORM);
      const saveResult = await saveScanFlowPart(env, { chat_id: message.chat_id, user_id: message.user_id }, payload, { donor_device_model: payload.donor_device_model });
      return { reply_text: saveResult.reply?.reply_text || "Czesc zapisana.", reply_markup: getDiscordMainMenuButtons() };
    }
    case "scan_part_model_edit": {
      const s = await getUserSession(env, message.chat_id, message.user_id, "scan_part_model_preview", DISCORD_PLATFORM);
      if (!s) return { reply_text: "Brak aktywnego podgladu modelu.", reply_markup: getDiscordMainMenuButtons() };
      await closeUserSession(env, message.chat_id, message.user_id, "scan_part_model_preview", DISCORD_PLATFORM);
      await upsertUserSession(env, message.chat_id, message.user_id, "scan_part_model_edit", null, s.active_device_name, DISCORD_PLATFORM);
      return { reply_text: "Podaj poprawione oznaczenie modelu elektrosmiecia.", reply_markup: getDiscordMainMenuButtons() };
    }
    case "scan_batch_enter_model":
    case "scan_batch_photo_model": {
      await closeUserSession(env, message.chat_id, message.user_id, "scan_batch_wait_model_text", DISCORD_PLATFORM);
      if (actionPrefix === "scan_batch_enter_model") {
        await upsertUserSession(env, message.chat_id, message.user_id, "scan_batch_wait_model_text", null, null, DISCORD_PLATFORM);
        return { reply_text: "Wpisz dokladny model elektrosmiecia zrodlowego.", reply_markup: getDiscordMainMenuButtons() };
      }
      await upsertUserSession(env, message.chat_id, message.user_id, "scan_batch_wait_model_photo", null, null, DISCORD_PLATFORM);
      return { reply_text: "Przeslij zdjecie etykiety albo obudowy urzadzenia.", reply_markup: getDiscordMainMenuButtons() };
    }
    case "scan_batch_model_use": {
      const s = await getUserSession(env, message.chat_id, message.user_id, "scan_batch_model_preview", DISCORD_PLATFORM);
      if (!s) return { reply_text: "Brak aktywnego podgladu modelu.", reply_markup: getDiscordMainMenuButtons() };
      const payload = readBatchScanPayload(s.active_device_name);
      return { reply_text: "Model **" + (payload.device_model || "Nieznany") + "** zaakceptowany. Wybierz co dalej:", reply_markup: getDiscordMainMenuButtons() };
    }
    case "scan_batch_model_edit": {
      const s = await getUserSession(env, message.chat_id, message.user_id, "scan_batch_model_preview", DISCORD_PLATFORM);
      if (!s) return { reply_text: "Brak aktywnego podgladu modelu.", reply_markup: getDiscordMainMenuButtons() };
      await closeUserSession(env, message.chat_id, message.user_id, "scan_batch_model_preview", DISCORD_PLATFORM);
      await upsertUserSession(env, message.chat_id, message.user_id, "scan_batch_model_edit", null, s.active_device_name, DISCORD_PLATFORM);
      return { reply_text: "Podaj poprawione oznaczenie modelu elektrosmiecia.", reply_markup: getDiscordMainMenuButtons() };
    }
    case "scan_batch_change_model": {
      await closeUserSession(env, message.chat_id, message.user_id, "scan_batch_wait_model_text", DISCORD_PLATFORM);
      await closeUserSession(env, message.chat_id, message.user_id, "scan_batch_wait_model_photo", DISCORD_PLATFORM);
      await closeUserSession(env, message.chat_id, message.user_id, "scan_batch_model_preview", DISCORD_PLATFORM);
      return { reply_text: "Podaj nowy model elektrosmiecia zrodlowego.", reply_markup: getDiscordMainMenuButtons() };
    }
    case "scan_batch_finish": {
      await closeUserSession(env, message.chat_id, message.user_id, "recycled_parts", DISCORD_PLATFORM);
      await closeUserSession(env, message.chat_id, message.user_id, "scan_part_wait_photo", DISCORD_PLATFORM);
      await closeUserSession(env, message.chat_id, message.user_id, "scan_part_wait_model", DISCORD_PLATFORM);
      return { reply_text: "Zakonczono tryb dodawania wielu czesci.", reply_markup: getDiscordMainMenuButtons() };
    }
    case "datasheet_start_search": {
      const partQuery = data.substring("datasheet_start_search:".length);
      const res = await initDatasheetWorkflow(env, { chat_id: message.chat_id, user_id: message.user_id, text: partQuery }, "datasheet_analysis");
      return { reply_text: res.reply_text, reply_markup: getDiscordMainMenuButtons() };
    }
    case "datasheet_no_model": {
      return { reply_text: "Kontynuuje bez modelu. Wpisz pytanie dotyczace czesci.", reply_markup: getDiscordMainMenuButtons() };
    }
    case "datasheet_ask": {
      const partQuery = data.substring("datasheet_ask:".length);
      await upsertUserSession(env, message.chat_id, message.user_id, "datasheet_wait_question", null, JSON.stringify({ version: 1, part_query: partQuery }), DISCORD_PLATFORM);
      return { reply_text: "Analiza datasheet dla **" + partQuery + "**. Wpisz pytanie:", reply_markup: getDiscordMainMenuButtons() };
    }
    case "datasheet_continue": {
      const partQuery = data.substring("datasheet_continue:".length);
      await upsertUserSession(env, message.chat_id, message.user_id, "datasheet_wait_question", null, JSON.stringify({ version: 1, part_query: partQuery }), DISCORD_PLATFORM);
      return { reply_text: "Kontynuacja analizy dla **" + partQuery + "**. O co chcesz zapytac?", reply_markup: getDiscordMainMenuButtons() };
    }
    default: {
      await closeAllUserSessions(env, message.chat_id, message.user_id, DISCORD_PLATFORM);
      return { reply_text: "Nieznana komenda. Wpisz `!help` aby zobaczyc dostepne opcje.", reply_markup: getDiscordMainMenuButtons() };
    }
  }
}

async function handleActiveDiscordSessions(env, message) {
  const resistorSession = await getUserSession(env, message.chat_id, message.user_id, "resistor_wait_photo", DISCORD_PLATFORM);
  if (resistorSession) {
    if (message.attachments?.length || (message.text && !message.text.startsWith("!"))) {
      await closeUserSession(env, message.chat_id, message.user_id, "resistor_wait_photo", DISCORD_PLATFORM);
      const img = message.attachments?.find(a => (a.contentType || "").startsWith("image/"));
      if (img) {
        const base64 = await fetchDiscordAttachmentBase64(img.url);
        if (base64) {
          const msg = { ...message, file_id: img.url, mime_type: img.contentType || "image/jpeg", file_name: img.name };
          const result = await handleResistorAnalysis(env, msg, base64);
          if (result && result._resistor_edit_data) {
            const packed = JSON.stringify({ ai: result._ai_resistor || null, edit: result._resistor_edit_data });
            await upsertUserSession(env, message.chat_id, message.user_id, "resistor_edit_bands", null, packed, DISCORD_PLATFORM);
            delete result._resistor_edit_data;
            delete result._ai_resistor;
          }
          return result;
        }
      }
      const result = await handleResistorAnalysis(env, message);
      if (result && result._resistor_edit_data) {
        const packed = JSON.stringify({ ai: result._ai_resistor || null, edit: result._resistor_edit_data });
        await upsertUserSession(env, message.chat_id, message.user_id, "resistor_edit_bands", null, packed, DISCORD_PLATFORM);
        delete result._resistor_edit_data;
        delete result._ai_resistor;
      }
      return result;
    } else if (message.text && message.text.startsWith("!")) {
      return null;
    }
    return { reply_text: "Oczekuje na zdjecie rezystora lub wpisane kolory paskow. Wpisz `!stop` aby anulowac.", reply_markup: getDiscordMainMenuButtons() };
  }

  const editBandSession = await getUserSession(env, message.chat_id, message.user_id, "resistor_edit_bands", DISCORD_PLATFORM);
  if (editBandSession) {
    if (message.text && !message.text.startsWith("!")) {
      let prevData = editBandSession.active_device_name || "";
      let aiInfo = null;
      try { const packed = JSON.parse(prevData); aiInfo = packed.ai; prevData = packed.edit || prevData; } catch (_) {}
      const verText = runResistorVerification(aiInfo?.value, aiInfo?.tolerance, aiInfo?.code_format, prevData, message.text);
      await closeUserSession(env, message.chat_id, message.user_id, "resistor_edit_bands", DISCORD_PLATFORM);
      const newMeta = JSON.stringify({ ai: aiInfo, edit: prevData });
      await upsertUserSession(env, message.chat_id, message.user_id, "resistor_edit_bands", null, newMeta, DISCORD_PLATFORM);
      return { reply_text: verText, reply_markup: getDiscordMainMenuButtons() };
    } else if (message.text && message.text.startsWith("!")) {
      return null;
    }
    return { reply_text: "Wpisz poprawione wartosci rezystora.", reply_markup: getDiscordMainMenuButtons() };
  }

  const issueSession = await getUserSession(env, message.chat_id, message.user_id, "issue_wait_idea", DISCORD_PLATFORM);
  if (issueSession) {
    if (message.text && !message.text.startsWith("!")) {
      await closeUserSession(env, message.chat_id, message.user_id, "issue_wait_idea", DISCORD_PLATFORM);
      const classification = { kind: "idea", label: "Pomysl", content: message.text, original_text: message.text };
      return await handleIssue(env, message, classification);
    }
  }

  const scanPartWaitPhoto = await getUserSession(env, message.chat_id, message.user_id, "scan_part_wait_photo", DISCORD_PLATFORM);
  if (scanPartWaitPhoto) {
    if (message.text && message.text.startsWith("!")) return null;
    const img = message.attachments?.find(a => (a.contentType || "").startsWith("image/"));
    if (!img) return { reply_text: "Dodaj zdjecie czesci.", reply_markup: getDiscordMainMenuButtons() };
    await closeUserSession(env, message.chat_id, message.user_id, "scan_part_wait_photo", DISCORD_PLATFORM);
    const base64 = await fetchDiscordAttachmentBase64(img.url);
    if (!base64) return { reply_text: "Nie udalo sie pobrac zdjecia.", reply_markup: getDiscordMainMenuButtons() };
    const msg = { ...message, file_id: img.url, mime_type: img.contentType || "image/jpeg", file_name: img.name };
    const scanResult = await recognizePartForScanFlow(env, msg, base64, { source: "single_part_scan" });
    if (scanResult.type === "preview" && scanResult.payload) {
      await upsertUserSession(env, message.chat_id, message.user_id, "scan_part_preview", null, createScanPartPayload(scanResult.payload), DISCORD_PLATFORM);
      return { reply_text: scanResult.reply_text, reply_markup: getDiscordMainMenuButtons() };
    }
    if (scanResult.type === "existing_part" && scanResult.match?.id) {
      return { reply_text: scanResult.reply_text, reply_markup: getDiscordMainMenuButtons() };
    }
    return { reply_text: scanResult.reply_text || "Nie udalo sie rozpoznac czesci.", reply_markup: getDiscordMainMenuButtons() };
  }

  const datasheetWait = await getUserSession(env, message.chat_id, message.user_id, "datasheet_wait_target", DISCORD_PLATFORM);
  if (datasheetWait) {
    if (message.text && message.text.startsWith("!")) return null;
    await closeUserSession(env, message.chat_id, message.user_id, "datasheet_wait_target", DISCORD_PLATFORM);
    if (message.attachments?.length) {
      const pdf = message.attachments.find(a => (a.contentType || "") === "application/pdf" || a.name?.toLowerCase().endsWith(".pdf"));
      if (pdf) {
        const result = await initDatasheetWorkflow(env, { ...message, file_id: pdf.url, mime_type: "application/pdf", file_name: pdf.name }, "datasheet_analysis");
        return { reply_text: result.reply_text, reply_markup: getDiscordMainMenuButtons() };
      }
    }
    const result = await initDatasheetWorkflow(env, { ...message, text: message.text }, "datasheet_analysis");
    return { reply_text: result.reply_text, reply_markup: getDiscordMainMenuButtons() };
  }

  const partLookupSession = await getUserSession(env, message.chat_id, message.user_id, "part_lookup_question", DISCORD_PLATFORM);
  if (partLookupSession) {
    if (message.text && !message.text.startsWith("!")) {
      const result = await answerPartLookupQuestion(env, partLookupSession, message.text);
      await closeUserSession(env, message.chat_id, message.user_id, "part_lookup_question", DISCORD_PLATFORM);
      return { reply_text: result?.reply_text || result, reply_markup: getDiscordMainMenuButtons() };
    }
  }

  const deviceLookupSession = await getUserSession(env, message.chat_id, message.user_id, "device_lookup", DISCORD_PLATFORM);
  if (deviceLookupSession) {
    if (message.text && !message.text.startsWith("!")) {
      const result = await answerDeviceLookupQuestion(env, deviceLookupSession, message.text);
      return { reply_text: result?.reply_text || result, reply_markup: getDiscordMainMenuButtons() };
    }
  }

  const datasheetQuestionSession = await getUserSession(env, message.chat_id, message.user_id, "datasheet_wait_question", DISCORD_PLATFORM);
  if (datasheetQuestionSession) {
    if (message.text && !message.text.startsWith("!")) {
      return await handleConversation(env, message, "datasheet_question");
    }
  }

  const scanPartEditSession = await getUserSession(env, message.chat_id, message.user_id, "scan_part_edit", DISCORD_PLATFORM);
  if (scanPartEditSession) {
    if (message.text && message.text.startsWith("!")) return null;
    if (!message.text) return { reply_text: "Podaj poprawione oznaczenie czesci.", reply_markup: getDiscordMainMenuButtons() };
    const isValid = await validateManualEntry(env, message.text);
    if (!isValid) return { reply_text: "To nie wyglada na sensowne oznaczenie czesci. Sprobuj ponownie.", reply_markup: getDiscordMainMenuButtons() };
    const payload = readScanPartPayload(scanPartEditSession.active_device_name);
    const nameMatch = message.text.match(/^(.+)\s*\|\s*(.+)$/);
    if (nameMatch) {
      payload.part_name = nameMatch[1].trim();
      payload.part_number = nameMatch[2].trim();
    } else {
      payload.part_number = message.text.trim();
    }
    await closeUserSession(env, message.chat_id, message.user_id, "scan_part_edit", DISCORD_PLATFORM);
    await upsertUserSession(env, message.chat_id, message.user_id, "scan_part_preview", null, createScanPartPayload(payload), DISCORD_PLATFORM);
    return { reply_text: "Oznaczenie zaktualizowane. Dodaj czesc do bazy lub edytuj ponownie.", reply_markup: getDiscordMainMenuButtons() };
  }

  const scanPartModelEditSession = await getUserSession(env, message.chat_id, message.user_id, "scan_part_model_edit", DISCORD_PLATFORM);
  if (scanPartModelEditSession) {
    if (message.text && !message.text.startsWith("!")) {
      await closeUserSession(env, message.chat_id, message.user_id, "scan_part_model_edit", DISCORD_PLATFORM);
      return { reply_text: "Model zostal zaktualizowany. Kontynuuj.", reply_markup: getDiscordMainMenuButtons() };
    }
  }

  const batchModelEditSession = await getUserSession(env, message.chat_id, message.user_id, "scan_batch_model_edit", DISCORD_PLATFORM);
  if (batchModelEditSession) {
    if (message.text && !message.text.startsWith("!")) {
      await closeUserSession(env, message.chat_id, message.user_id, "scan_batch_model_edit", DISCORD_PLATFORM);
      return { reply_text: "Model zostal zaktualizowany. Wybierz co dalej.", reply_markup: getDiscordMainMenuButtons() };
    }
  }

  const batchModelPhotoSession = await getUserSession(env, message.chat_id, message.user_id, "scan_batch_wait_model_photo", DISCORD_PLATFORM);
  if (batchModelPhotoSession) {
    if (message.text && message.text.startsWith("!")) return null;
    const img = message.attachments?.find(a => (a.contentType || "").startsWith("image/"));
    if (img) {
      await closeUserSession(env, message.chat_id, message.user_id, "scan_batch_wait_model_photo", DISCORD_PLATFORM);
      const base64 = await fetchDiscordAttachmentBase64(img.url);
      if (base64) {
        const msg = { ...message, file_id: img.url, mime_type: img.contentType || "image/jpeg", file_name: img.name };
        const result = await recognizeDeviceForScanFlow(env, msg, base64);
        await upsertUserSession(env, message.chat_id, message.user_id, "scan_batch_model_preview", null, createBatchScanPayload(result || {}), DISCORD_PLATFORM);
        return { reply_text: result?.reply_text || "Rozpoznano model.", reply_markup: getDiscordMainMenuButtons() };
      }
    }
  }

  const datasheetWaitModelSession = await getUserSession(env, message.chat_id, message.user_id, "datasheet_wait_model", DISCORD_PLATFORM);
  if (datasheetWaitModelSession) {
    if (message.text && !message.text.startsWith("!")) {
      await closeUserSession(env, message.chat_id, message.user_id, "datasheet_wait_model", DISCORD_PLATFORM);
      return { reply_text: "Model zapisany. Kontynuuj zadajac pytanie.", reply_markup: getDiscordMainMenuButtons() };
    }
  }

  return null;
}

async function verifyDiscordSignature(request, rawBody, env) {
  const publicKey = (env.DISCORD_PUBLIC_KEY || "").trim();
  if (!publicKey) {
    return null;
  }

  const signature = request.headers.get("X-Signature-Ed25519");
  const timestamp = request.headers.get("X-Signature-Timestamp");
  if (!signature || !timestamp) {
    return "Missing Ed25519 signature headers";
  }

  try {
    const encoder = new TextEncoder();
    const keyData = Uint8Array.from(atob(publicKey), c => c.charCodeAt(0));
    const sigData = Uint8Array.from(atob(signature), c => c.charCodeAt(0));

    const key = await crypto.subtle.importKey(
      "raw", keyData, { name: "NODE-ED25519", namedCurve: "NODE-ED25519" },
      false, ["verify"]
    );

    const isValid = await crypto.subtle.verify(
      "NODE-ED25519", key, sigData,
      encoder.encode(timestamp + rawBody)
    );

    return isValid ? null : "Ed25519 signature verification failed";
  } catch (_e) {
    return "Ed25519 verification error: " + (_e.message || "internal error");
  }
}

export function checkDiscordPayloadSize(request, env) {
  return checkPayloadSize(request, env, {
    envKey: "DISCORD_MAX_WEBHOOK_BODY_BYTES",
    fallbackKey: "MAX_WEBHOOK_BODY_BYTES",
    defaultMax: 5242880,
    responseFactory: jsonReply,
    errorMessage: "Payload Too Large",
  });
}

export async function handleDiscordWebhook(request, env) {
  // Content-Length check: reject oversized payloads
  const sizeCheck = checkDiscordPayloadSize(request, env);
  if (sizeCheck) return sizeCheck;

  // Verify Discord Ed25519 signature if public key is configured
  if (env.DISCORD_PUBLIC_KEY) {
    const rawBody = await request.clone().text();
    const sigError = await verifyDiscordSignature(request, rawBody, env);
    if (sigError) {
      return jsonReply({ error: "Unauthorized", detail: sigError }, 401);
    }
  }

  // Verify custom bot secret (always required)
  const secret = request.headers.get("X-Discord-Bot-Secret");
  const expected = env.DISCORD_BOT_SECRET;

  if (!expected) {
    return jsonReply({ error: "Discord integration not configured on server." }, 503);
  }

  if (!secret || !timingSafeEqualString(secret, expected)) {
    return jsonReply({ error: "Unauthorized" }, 401);
  }

  let body;
  try {
    body = await request.json();
  } catch (_e) {
    return jsonReply({ error: "Invalid JSON body" }, 400);
  }

  // Input validation: reject payloads with empty/null required fields
  if (!body.chat_id && !body.user_id && !body.callback_data) {
    return jsonReply({ error: "Missing required fields: chat_id, user_id, or callback_data" }, 400);
  }

  const message = parseDiscordBody(body);
  return await handleMessage(env, message);
}