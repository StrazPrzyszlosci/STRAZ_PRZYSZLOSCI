/**
 * T22 — polling-safe events stream dla węzłów edge (H3).
 *
 * Alternatywa dla WebSocket (/v1/ws/events) bez Durable Objects:
 * edge node polluje `GET /v1/ws/events?provider_id=<id>&since_id=<cursor>&limit=<n>`
 * z tokenem providera (X-Provider-Token). Odpowiedź zawiera zdarzenia o id > since_id
 * oraz next_cursor do kolejnego polla. Bezpieczne dla retry/timeoutów (at-least-once
 * delivery po stronie klienta, serwer stateless).
 *
 * Publikacja: publishEdgeEvent() jest wywoływany przy generacji rekomendacji
 * (worker.js /v1/recommendations/fish-pond) i dostępny dla przyszłych alarmów.
 */

const KIND_VALUES = new Set(["recommendation", "alarm", "status", "notice"]);
const SEVERITY_VALUES = new Set(["info", "warning", "critical"]);
const DEFAULT_LIMIT = 100;
const MAX_LIMIT = 500;

function toText(value) {
  return value === undefined || value === null ? "" : String(value);
}

export function validateEdgeEventInput(input) {
  const missing = [];
  if (!toText(input?.provider_id).trim()) missing.push("provider_id");
  if (!KIND_VALUES.has(input?.kind)) missing.push(`kind must be one of ${[...KIND_VALUES].sort().join(",")}`);
  if (input?.severity !== undefined && !SEVERITY_VALUES.has(input.severity)) {
    missing.push(`severity must be one of ${[...SEVERITY_VALUES].sort().join(",")}`);
  }
  return missing;
}

export async function publishEdgeEvent(env, event, options = {}) {
  if (!env?.DB) return { success: false, reason: "no_db" };
  const missing = validateEdgeEventInput(event);
  if (missing.length) {
    return { success: false, reason: `invalid_event:${missing.join(",")}` };
  }
  const now = options.now || new Date().toISOString();
  const payloadJson = event.payload === undefined ? null : JSON.stringify(event.payload);
  const result = await env.DB.prepare(
    `INSERT INTO edge_event_stream (provider_id, kind, severity, payload_json, created_at)
     VALUES (?, ?, ?, ?, ?)`
  ).bind(
    toText(event.provider_id),
    event.kind,
    event.severity || "info",
    payloadJson,
    now
  ).run();
  return { success: true, event_id: result?.meta?.last_row_id || null, created_at: now };
}

export async function listEdgeEventsSince(db, providerId, sinceId = 0, limit = DEFAULT_LIMIT) {
  if (!db) return { success: false, reason: "no_db", events: [], next_cursor: Number(sinceId) || 0 };
  const boundedLimit = Math.min(Math.max(Number(limit) || DEFAULT_LIMIT, 1), MAX_LIMIT);
  const cursor = Number(sinceId) || 0;
  const result = await db.prepare(
    `SELECT id, provider_id, kind, severity, payload_json, created_at
     FROM edge_event_stream
     WHERE provider_id = ? AND id > ?
     ORDER BY id ASC
     LIMIT ?`
  ).bind(toText(providerId), cursor, boundedLimit + 1).all();
  const fetched = result?.results || [];
  const hasMore = fetched.length > boundedLimit;
  const events = (hasMore ? fetched.slice(0, boundedLimit) : fetched).map((row) => {
    let payload = null;
    try {
      payload = row.payload_json ? JSON.parse(row.payload_json) : null;
    } catch {
      payload = null;
    }
    return {
      id: row.id,
      kind: row.kind,
      severity: row.severity || "info",
      payload,
      created_at: row.created_at,
    };
  });
  const nextCursor = events.length ? events[events.length - 1].id : cursor;
  return {
    success: true,
    provider_id: toText(providerId),
    events,
    next_cursor: nextCursor,
    has_more: hasMore,
    limit: boundedLimit,
  };
}

export function parseEdgeStreamQuery(url) {
  const providerId = toText(url.searchParams.get("provider_id")).trim();
  if (!providerId) {
    throw new Error("Parametr provider_id jest wymagany.");
  }
  const rawSince = url.searchParams.get("since_id");
  let sinceId = 0;
  if (rawSince !== null && rawSince !== "") {
    sinceId = Number(rawSince);
    if (!Number.isSafeInteger(sinceId) || sinceId < 0) {
      throw new Error("Parametr since_id musi być nieujemną liczbą całkowitą.");
    }
  }
  const rawLimit = url.searchParams.get("limit");
  let limit = DEFAULT_LIMIT;
  if (rawLimit !== null && rawLimit !== "") {
    limit = Number(rawLimit);
    if (!Number.isInteger(limit) || limit < 1 || limit > MAX_LIMIT) {
      throw new Error(`Parametr limit musi być liczbą 1..${MAX_LIMIT}.`);
    }
  }
  return { provider_id: providerId, since_id: sinceId, limit };
}

// T31: retencja streamu — bez niej tabela rośnie nieograniczenie (publish przy
// każdej rekomendacji/evaluacie). Polityka: wiek wpisów + cap per provider.
export const DEFAULT_EDGE_EVENT_RETENTION_DAYS = 14;
export const DEFAULT_MAX_EVENTS_PER_PROVIDER = 1000;

function positiveIntFromEnv(value, fallback) {
  const parsed = Number(value);
  if (!Number.isFinite(parsed) || parsed <= 0) return fallback;
  return Math.floor(parsed);
}

export function resolveEdgeEventRetentionConfig(env) {
  return {
    retention_days: positiveIntFromEnv(
      env?.EDGE_EVENT_STREAM_RETENTION_DAYS,
      DEFAULT_EDGE_EVENT_RETENTION_DAYS
    ),
    max_per_provider: positiveIntFromEnv(
      env?.EDGE_EVENT_STREAM_MAX_PER_PROVIDER,
      DEFAULT_MAX_EVENTS_PER_PROVIDER
    ),
  };
}

/**
 * Usuwa stare wpisy (starsze niż retention_days) oraz nadmiar ponad cap
 * na providera (zostawia najnowsze). Zwraca liczbę usuniętych wierszy.
 */
export async function pruneEdgeEvents(db, options = {}) {
  if (!db) return { success: false, reason: "no_db", pruned: 0 };
  const retentionDays = Math.max(1, Number(options.retentionDays || DEFAULT_EDGE_EVENT_RETENTION_DAYS));
  const maxPerProvider = Math.max(1, Number(options.maxPerProvider || DEFAULT_MAX_EVENTS_PER_PROVIDER));
  const cutoffIso = new Date(Date.parse(options.now || new Date().toISOString()) - retentionDays * 86400000).toISOString();

  const oldResult = await db.prepare(
    `DELETE FROM edge_event_stream WHERE created_at < ?`
  ).bind(cutoffIso).run();

  const capResult = await db.prepare(
    `DELETE FROM edge_event_stream WHERE id IN (
       SELECT id FROM (
         SELECT id, ROW_NUMBER() OVER (PARTITION BY provider_id ORDER BY id DESC) AS rn
         FROM edge_event_stream
       ) WHERE rn > ?
     )`
  ).bind(maxPerProvider).run();

  const pruned = Number(oldResult?.meta?.changes || 0) + Number(capResult?.meta?.changes || 0);
  return { success: true, pruned, retention_days: retentionDays, max_per_provider: maxPerProvider, cutoff_iso: cutoffIso };
}
