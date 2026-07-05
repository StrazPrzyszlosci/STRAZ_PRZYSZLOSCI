import {
  listPendingKicadReviewLinks,
  buildKicadReviewQueueReply,
  recordKicadReviewDecision,
} from "./kicad_review.js";

const DEFAULT_QUEUE_LIMIT = 5;

function parseList(value, fallback = []) {
  if (!value) return fallback;
  return String(value)
    .split(/[,\s]+/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function isMaintainer(env, message) {
  const allowedIds = parseList(env.KICAD_REVIEW_MAINTAINER_IDS);
  const allowedRoles = parseList(env.KICAD_REVIEW_MAINTAINER_ROLES);
  const userId = String(message?.user_id || "").trim();
  const username = String(message?.username || "").trim().toLowerCase();

  if (userId && allowedIds.includes(userId)) {
    return true;
  }
  if (username && allowedIds.map((id) => id.toLowerCase()).includes(username)) {
    return true;
  }
  const roles = Array.isArray(message?.roles) ? message.roles : [];
  if (roles.length && allowedRoles.length) {
    const normalizedRoles = allowedRoles.map((role) => role.toLowerCase());
    return roles.some((role) => normalizedRoles.includes(String(role).toLowerCase()));
  }
  return false;
}

function reviewerIdentity(message) {
  const username = message?.username || "";
  const userId = message?.user_id || "";
  if (username) return `discord:${username}#${userId || "unknown"}`;
  if (userId) return `discord:${userId}`;
  return "discord:unknown";
}

function parseKicadCallbackData(data) {
  const parts = String(data || "").split(":");
  return {
    action: parts[0] || "",
    masterPartId: Number.parseInt(parts[1] || "", 10),
    kicadComponentId: Number.parseInt(parts[2] || "", 10),
  };
}

export function buildKicadReviewQueueButtons(rows = []) {
  if (!rows.length) return null;
  const buttons = [];
  for (const row of rows.slice(0, DEFAULT_QUEUE_LIMIT)) {
    const value = `kicad_review_approve:${row.master_part_id}:${row.kicad_component_id}`;
    buttons.push({ label: "Zatwierdz", action: "callback", value, style: "success" });
  }
  return { buttons: [buttons] };
}

export async function handleKicadReviewCommand(env, message) {
  const rows = await listPendingKicadReviewLinks(env, { limit: DEFAULT_QUEUE_LIMIT });
  const replyText = buildKicadReviewQueueReply(rows);
  const replyMarkup = buildKicadReviewQueueButtons(rows);
  return { reply_text: replyText, reply_markup: replyMarkup };
}

export async function handleKicadReviewAction(env, message) {
  const data = message?.callback_data || "";
  const parsed = parseKicadCallbackData(data);

  if (!Number.isFinite(parsed.masterPartId) || !Number.isFinite(parsed.kicadComponentId)) {
    return {
      reply_text: "Bledny identyfikator linku KiCad.",
      reply_markup: null,
    };
  }

  const actionMap = {
    kicad_review_approve: { status: "approved", reason: "Discord approve action" },
    kicad_review_reject: { status: "rejected", reason: "Discord reject action" },
    kicad_review_more_data: { status: "needs_more_data", reason: "Discord needs more data action" },
  };
  const action = actionMap[parsed.action];
  if (!action) {
    return { reply_text: "Nieznana akcja review KiCad.", reply_markup: null };
  }

  if (action.status === "approved" && !isMaintainer(env, message)) {
    return {
      reply_text:
        "Tylko uprawniony maintener moze zatwierdzac linki KiCad. Skontaktuj sie z administratorem.",
      reply_markup: null,
    };
  }

  try {
    const result = await recordKicadReviewDecision(env, {
      master_part_id: parsed.masterPartId,
      kicad_component_id: parsed.kicadComponentId,
      review_status: action.status,
      reviewed_by: reviewerIdentity(message),
      reason: action.reason,
    });
    return {
      reply_text: `Link #${result.link_id}: ${result.previous_status} -> ${result.status}. Decyzja zapisana w ledgerze.`,
      reply_markup: null,
    };
  } catch (error) {
    return {
      reply_text: `Blad review KiCad: ${error?.message || "nieznany blad"}`,
      reply_markup: null,
    };
  }
}

export const __test__ = { isMaintainer, parseKicadCallbackData, reviewerIdentity };
