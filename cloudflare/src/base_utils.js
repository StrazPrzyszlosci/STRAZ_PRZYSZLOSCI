import { knowledgeBundle } from "./generated_knowledge_bundle.js";

export class AiProviderError extends Error {
  constructor(message, options = {}) {
    super(message);
    this.name = "AiProviderError";
    this.status = options.status || null;
    this.provider = options.provider || null;
    this.model = options.model || null;
    this.retriable = options.retriable ?? true;
  }
}

export function toIsoNow() {
  return new Date().toISOString();
}

export function isTruthy(value) {
  if (typeof value !== "string") return false;
  return ["1", "true", "yes", "on"].includes(value.trim().toLowerCase());
}

export function parsePositiveInteger(rawValue, fallback) {
  const parsed = Number.parseInt(rawValue, 10);
  if (Number.isFinite(parsed) && parsed > 0) return parsed;
  return fallback;
}

export function parseNumber(rawValue, fallback) {
  const parsed = Number.parseFloat(rawValue);
  if (Number.isFinite(parsed)) return parsed;
  return fallback;
}

export function normalizeWhitespace(text) {
  return String(text || "").replace(/\s+/g, " ").trim();
}

export function normalizeForSearch(text) {
  return String(text || "")
    .toLowerCase()
    .replace(/[ąćęłńóśźż]/g, (char) => ({
      ą: "a", ć: "c", ę: "e", ł: "l", ń: "n", ó: "o", ś: "s", ź: "z", ż: "z",
    })[char] || char)
    .normalize("NFD")
    .replace(/\p{Diacritic}/gu, "")
    .replace(/[^\p{Letter}\p{Number}\s]/gu, " ")
    .replace(/\s+/g, " ")
    .trim();
}

export function tokenize(text) {
  return normalizeForSearch(text)
    .split(" ")
    .map((token) => token.trim())
    .filter((token) => token.length > 2);
}

export function getMessageText(message) {
  if (typeof message === "string") return message;
  if (typeof message?.text === "string") return message.text;
  if (typeof message?.caption === "string") return message.caption;
  return "";
}

export function formatDeviceName(device) {
  return [device?.brand, device?.model].filter(Boolean).join(" ").trim();
}

export function repoBlobUrl(path) {
  return `${knowledgeBundle.github_base_url}${path}`;
}

export function extractJsonObject(text) {
  if (typeof text !== "string" || !text.trim()) throw new Error("Brak tekstu.");
  const direct = text.trim();
  try { return JSON.parse(direct); } catch {}
  const fencedMatch = direct.match(/```json\s*([\s\S]+?)```/i) || direct.match(/```\s*([\s\S]+?)```/i);
  if (fencedMatch?.[1]) return JSON.parse(fencedMatch[1].trim());
  const firstBrace = direct.indexOf("{");
  const lastBrace = direct.lastIndexOf("}");
  if (firstBrace !== -1 && lastBrace !== -1 && lastBrace > firstBrace) return JSON.parse(direct.slice(firstBrace, lastBrace + 1));
  throw new Error("Nie udało się odczytać obiekut JSON.");
}

export function buildPromptPayload(systemInstruction, userPrompt, env, options = {}) {
  return {
    systemInstruction, userPrompt,
    maxTokens: parsePositiveInteger(options.maxTokens || env.TELEGRAM_AI_MAX_OUTPUT_TOKENS, 1200),
    temperature: parseNumber(options.temperature || env.TELEGRAM_AI_TEMPERATURE, 0.35),
    responseMimeType: options.responseMimeType || "text/plain",
    media: Array.isArray(options.media) ? options.media : [],
  };
}

export function buildDeviceCatalogReply(dbResult) {
  const partsList = (dbResult.parts || []).slice(0, 12).map(p => `- ${p.part_name}`).join("\n");
  return `Urzadzenie: ${formatDeviceName(dbResult.device)}\n\nCzesci:\n${partsList}`;
}

export function buildPartLookupReply(queryText, matches) {
  const lines = [`Wyniki dla: ${queryText}`, "", ...matches.map(m => `- ${m.part_name} -> ${formatDeviceName(m.device)}`)];
  return { text: lines.join("\n"), reply_markup: { inline_keyboard: [[{ text: "📄 Datasheet", callback_data: `datasheet_start_search:${queryText}` }]] } };
}

/**
 * fetch with AbortController timeout.
 * Returns the Response or throws on timeout/network error.
 */
export async function fetchWithTimeout(resource, options = {}, timeoutMs = 15000) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(resource, {
      ...options,
      signal: controller.signal,
    });
    return response;
  } catch (err) {
    if (err.name === "AbortError") {
      throw new Error(`Fetch timeout after ${timeoutMs}ms: ${resource}`);
    }
    throw err;
  } finally {
    clearTimeout(timer);
  }
}
