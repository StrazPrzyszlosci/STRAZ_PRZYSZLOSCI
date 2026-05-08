import { fetchWithTimeout } from "./base_utils.js";

function jsonResponse(payload, status = 200) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
    },
  });
}

function textResponse(payload, status = 200) {
  return new Response(payload, {
    status,
    headers: {
      "content-type": "text/plain; charset=utf-8",
    },
  });
}

function isTruthy(value) {
  if (typeof value !== "string") {
    return false;
  }
  return ["1", "true", "yes", "on"].includes(value.trim().toLowerCase());
}

function normalizeSender(value) {
  if (typeof value !== "string") {
    return "";
  }
  return value.replace(/[^\d+]/g, "");
}

function parseAllowedSenders(rawValue) {
  if (!rawValue || !rawValue.trim()) {
    return null;
  }
  if (rawValue.trim() === "*") {
    return null;
  }

  const allowlist = new Set();
  for (const sender of rawValue.split(",")) {
    const normalized = normalizeSender(sender);
    if (normalized) {
      allowlist.add(normalized);
    }
  }
  return allowlist.size ? allowlist : null;
}

function maskSender(sender) {
  const normalized = normalizeSender(sender);
  if (!normalized) {
    return "nieznany";
  }
  if (normalized.length <= 4) {
    return `${normalized.slice(0, 1)}***`;
  }
  return `${normalized.slice(0, 3)}***${normalized.slice(-2)}`;
}

function stripPrefix(messageText) {
  if (typeof messageText !== "string") {
    return null;
  }
  const trimmed = messageText.trim();
  if (!trimmed) {
    return null;
  }

  const matchers = [
    {
      kind: "idea",
      prefix: "Pomysl",
      pattern: /^\s*(pomysl|pomysł)\s*:\s*/iu,
    },
    {
      kind: "feedback",
      prefix: "Uwaga",
      pattern: /^\s*(uwaga|zastrzezenie|zastrzeżenie)\s*:\s*/iu,
    },
  ];

  for (const matcher of matchers) {
    if (matcher.pattern.test(trimmed)) {
      const content = trimmed.replace(matcher.pattern, "").trim();
      if (!content) {
        return null;
      }
      return {
        kind: matcher.kind,
        prefix: matcher.prefix,
        content,
      };
    }
  }

  return null;
}

function summarizeTitle(prefix, content) {
  const shortened = content.replace(/\s+/g, " ").trim().slice(0, 80);
  return `[${prefix}] ${shortened || "zgloszenie z whatsapp"}`;
}

function getConfiguredLabels(kind, env) {
  const labels = [];
  const channelLabel = (env.WHATSAPP_CHANNEL_LABEL || "").trim();
  const kindLabel =
    kind === "idea"
      ? (env.WHATSAPP_IDEA_LABEL || "").trim()
      : (env.WHATSAPP_FEEDBACK_LABEL || "").trim();

  if (kindLabel) {
    labels.push(kindLabel);
  }
  if (channelLabel) {
    labels.push(channelLabel);
  }
  return labels;
}

function buildIssueDraft(message, classification, env) {
  const title = summarizeTitle(classification.prefix, classification.content);
  const labels = getConfiguredLabels(classification.kind, env);

  const body = [
    "## Kanał wejścia",
    "",
    "Automatyczne zgłoszenie utworzone z wiadomości WhatsApp.",
    "",
    "## Typ zgłoszenia",
    "",
    classification.kind === "idea" ? "pomysł" : "uwaga / zastrzeżenie",
    "",
    "## Treść wiadomości",
    "",
    classification.content,
    "",
    "## Metadane",
    "",
    `- kanał: WhatsApp`,
    `- nadawca: ${maskSender(message.from)}`,
    `- message_id: ${message.id || "brak"}`,
    `- timestamp: ${message.timestamp || "brak"}`,
    `- webhook_received_at: ${new Date().toISOString()}`,
    "",
    "## Uwaga operatorska",
    "",
    "To zgłoszenie zostało utworzone automatycznie przez most komunikator -> GitHub Issues. Warto je doprecyzować, skategoryzować i połączyć z odpowiednim projektem lub dokumentem.",
  ].join("\n");

  return { title, body, labels };
}

function collectInboundMessages(payload) {
  const messages = [];
  for (const entry of payload.entry || []) {
    for (const change of entry.changes || []) {
      const items = change.value?.messages || [];
      for (const item of items) {
        const body = item?.text?.body;
        if (typeof body !== "string") {
          continue;
        }
        messages.push({
          id: item.id || null,
          from: item.from || null,
          timestamp: item.timestamp || null,
          text: body,
        });
      }
    }
  }
  return messages;
}

async function hmacSha256Hex(secret, payload) {
  const key = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"]
  );

  const signature = await crypto.subtle.sign(
    "HMAC",
    key,
    new TextEncoder().encode(payload)
  );

  return Array.from(new Uint8Array(signature))
    .map((value) => value.toString(16).padStart(2, "0"))
    .join("");
}

async function verifyMetaSignature(request, rawBody, env) {
  const appSecret = (env.WHATSAPP_APP_SECRET || "").trim();
  if (!appSecret) {
    return true;
  }

  const headerValue =
    request.headers.get("X-Hub-Signature-256") ||
    request.headers.get("x-hub-signature-256");
  if (!headerValue || !headerValue.startsWith("sha256=")) {
    return false;
  }

  const expected = headerValue.slice("sha256=".length).trim().toLowerCase();
  const actual = await hmacSha256Hex(appSecret, rawBody);
  return expected === actual;
}

async function createGitHubIssue(env, draft) {
  const owner = (env.GITHUB_REPO_OWNER || "").trim();
  const repo = (env.GITHUB_REPO_NAME || "").trim();
  const token = env.GITHUB_TOKEN;

  if (!owner || !repo) {
    throw new Error("Brak konfiguracji repozytorium GitHub dla integracji WhatsApp.");
  }
  if (!token) {
    throw new Error("Brak sekretu GITHUB_TOKEN dla integracji WhatsApp.");
  }

  const response = await fetchWithTimeout(`https://api.github.com/repos/${owner}/${repo}/issues`, {
    method: "POST",
    headers: {
      accept: "application/vnd.github+json",
      authorization: `Bearer ${token}`,
      "content-type": "application/json; charset=utf-8",
      "user-agent": "straz-przyszlosci-whatsapp-bridge",
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

export function handleWhatsAppVerification(url, env) {
  const verifyToken = (env.WHATSAPP_VERIFY_TOKEN || "").trim();
  if (!verifyToken) {
    return textResponse("Brak konfiguracji WHATSAPP_VERIFY_TOKEN.", 500);
  }

  const mode = url.searchParams.get("hub.mode");
  const token = url.searchParams.get("hub.verify_token");
  const challenge = url.searchParams.get("hub.challenge");

  if (mode === "subscribe" && token === verifyToken && challenge) {
    return textResponse(challenge, 200);
  }

  return textResponse("Webhook verification failed.", 403);
}

export async function handleWhatsAppWebhook(request, env) {
  if (!isTruthy(env.WHATSAPP_ISSUES_ENABLED || "")) {
    return jsonResponse(
      {
        status: "disabled",
        message: "Integracja WhatsApp -> GitHub Issues jest wyłączona.",
      },
      200
    );
  }

  const rawBody = await request.text();
  if (!(await verifyMetaSignature(request, rawBody, env))) {
    return textResponse("Invalid WhatsApp signature.", 403);
  }

  let payload;
  try {
    payload = JSON.parse(rawBody);
  } catch {
    return jsonResponse({ error: "Nieprawidłowy JSON webhooka WhatsApp." }, 400);
  }

  const messages = collectInboundMessages(payload);
  const allowlist = parseAllowedSenders(env.WHATSAPP_ALLOWED_SENDERS || "");
  const dryRun = isTruthy(env.WHATSAPP_ISSUES_DRY_RUN || "");
  const results = [];

  for (const message of messages) {
    const normalizedSender = normalizeSender(message.from);
    if (allowlist && !allowlist.has(normalizedSender)) {
      results.push({
        message_id: message.id,
        status: "ignored_sender_not_allowed",
      });
      continue;
    }

    const classification = stripPrefix(message.text);
    if (!classification) {
      results.push({
        message_id: message.id,
        status: "ignored_unrecognized_format",
      });
      continue;
    }

    const draft = buildIssueDraft(message, classification, env);
    if (dryRun) {
      results.push({
        message_id: message.id,
        status: "dry_run",
        kind: classification.kind,
        title: draft.title,
      });
      continue;
    }

    const issue = await createGitHubIssue(env, draft);
    results.push({
      message_id: message.id,
      status: "created",
      kind: classification.kind,
      issue_number: issue.number,
      issue_url: issue.html_url,
    });
  }

  return jsonResponse(
    {
      status: "accepted",
      processed_messages: messages.length,
      dry_run: dryRun,
      results,
    },
    200
  );
}
