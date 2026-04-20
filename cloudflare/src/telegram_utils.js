const DEFAULT_MAX_REPLY_CHARS = 3200;

export function redactSensitiveContent(text) {
  let sanitized = String(text || "");
  const patterns = [
    /AIza[0-9A-Za-z\-_]{20,}/g,
    /gh[pousr]_[A-Za-z0-9]{20,}/g,
    /sk-[A-Za-z0-9]{20,}/g,
    /Bearer\s+[A-Za-z0-9._-]{20,}/gi,
    /\b(?:GITHUB_TOKEN|TELEGRAM_BOT_TOKEN|GEMINI_API_KEY|NVIDIA_API_KEY)\b/gi,
  ];
  for (const pattern of patterns) {
    sanitized = sanitized.replace(pattern, "[ukryto]");
  }
  return sanitized;
}

export function clampReplyLength(text, maxChars) {
  if (text.length <= maxChars) {
    return text;
  }

  const suffix = "\n\n[odpowiedź skrócona]";
  const availableChars = Math.max(40, maxChars - suffix.length);
  const shortened = text.slice(0, availableChars);
  const lastSentence = Math.max(shortened.lastIndexOf("."), shortened.lastIndexOf("\n"));
  if (lastSentence >= maxChars * 0.6) {
    return `${shortened.slice(0, lastSentence + 1).trim()}${suffix}`.slice(0, maxChars);
  }
  const bodyChars = Math.max(20, maxChars - suffix.length - 3);
  return `${text.slice(0, bodyChars).trim()}...${suffix}`.slice(0, maxChars);
}

export function sanitizeTelegramReply(text, env) {
  const maxChars = Number.parseInt(env?.TELEGRAM_AI_MAX_REPLY_CHARS, 10) || DEFAULT_MAX_REPLY_CHARS;
  const normalized = redactSensitiveContent(String(text || "").trim());
  return clampReplyLength(normalized, maxChars);
}

export async function sendTelegramReply(env, message, text, replyMarkup = null) {
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
        reply_markup: replyMarkup || undefined,
        parse_mode: "Markdown",
      }),
    }
  );

  return response.ok;
}

export function getMainMenuKeyboard() {
  return {
    inline_keyboard: [
      [
        { text: "📸 Skanuj Urządzenie/Część", callback_data: "menu_scan" },
        { text: "📖 Analiza Datasheet", callback_data: "menu_datasheet" }
      ],
      [
        { text: "🎨 Odczytaj Rezystor", callback_data: "menu_resistor" },
        { text: "🔍 Szukaj w Bazie", callback_data: "menu_search" }
      ],
      [
        { text: "💡 Zgłoś Pomysł", callback_data: "menu_issue" },
        { text: "❓ Onboarding", callback_data: "menu_onboarding" }
      ]
    ]
  };
}
