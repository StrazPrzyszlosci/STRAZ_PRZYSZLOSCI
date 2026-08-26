/**
 * T32 — dashboard metryk upraw (read-only, admin-only).
 *
 * Składa snapshot z dwóch źródeł:
 *  - automation_metrics: agregaty dzienne czujników (avg/min/max per sensor,
 *    klucze `telemetry_<sensor>_(avg|min|max)_<YYYY-MM-DD>` z T29),
 *  - agri_autopilot_usage: dzienne zużycie budżetu autopilota per polityka (T27).
 *
 * Odpowiedź JSON dla GET /v1/agri/metrics (X-Trust-Editor-Secret).
 */

const TELEMETRY_KEY_RE = /^telemetry_([a-z0-9_]+)_(avg|min|max)_(\d{4}-\d{2}-\d{2})$/;
const DEFAULT_MAX_DAYS = 30;

function toText(value) {
  return value === undefined || value === null ? "" : String(value);
}

export function parseTelemetryMetricKey(key) {
  const match = TELEMETRY_KEY_RE.exec(toText(key));
  if (!match) return null;
  return { sensor: match[1], suffix: match[2], day_key: match[3] };
}

export function groupTelemetryMetrics(rows) {
  const bySensorDay = new Map();
  for (const row of rows || []) {
    const parsed = parseTelemetryMetricKey(row?.metric_key);
    if (!parsed) continue;
    const mapKey = `${parsed.sensor}|${parsed.day_key}`;
    if (!bySensorDay.has(mapKey)) {
      bySensorDay.set(mapKey, { sensor: parsed.sensor, day_key: parsed.day_key });
    }
    bySensorDay.get(mapKey)[parsed.suffix] = Number(row.metric_value);
  }
  return [...bySensorDay.values()].sort((a, b) =>
    a.day_key === b.day_key ? a.sensor.localeCompare(b.sensor) : b.day_key.localeCompare(a.day_key)
  );
}

export function groupAutopilotUsage(rows) {
  return (rows || [])
    .map((row) => {
      // T35: klucz `policy_id|grow_cell_id|day`; legacy `policy_id|day`.
      const parts = toText(row.usage_key).split("|");
      if (parts.length === 3 && parts[0] && parts[1] && parts[2]) {
        return {
          policy_id: parts[0],
          grow_cell_id: parts[1],
          day_key: parts[2],
          used_count: Number(row.used_count || 0),
          updated_at: toText(row.updated_at) || null,
        };
      }
      if (parts.length === 2 && parts[0] && parts[1]) {
        return {
          policy_id: parts[0],
          grow_cell_id: null,
          day_key: parts[1],
          used_count: Number(row.used_count || 0),
          updated_at: toText(row.updated_at) || null,
        };
      }
      return null;
    })
    .filter(Boolean)
    .sort((a, b) => (a.day_key === b.day_key ? a.policy_id.localeCompare(b.policy_id) : b.day_key.localeCompare(a.day_key)));
}

export async function computeAgriMetrics(env, options = {}) {
  if (!env?.DB) return { success: false, reason: "no_db" };
  const maxDays = Math.max(1, Number(options.maxDays || DEFAULT_MAX_DAYS));
  const now = options.now || new Date().toISOString();

  const telemetryRows = await env.DB.prepare(
    `SELECT metric_key, metric_value, measured_at FROM automation_metrics
     WHERE window = 'daily' AND metric_key LIKE 'telemetry\\_%' ESCAPE '\'
     ORDER BY measured_at DESC LIMIT ?`
  ).bind(maxDays * 300).all();
  const usageRows = await env.DB.prepare(
    `SELECT usage_key, used_count, updated_at FROM agri_autopilot_usage
     ORDER BY updated_at DESC LIMIT ?`
  ).bind(maxDays * 50).all();

  return {
    success: true,
    generated_at: now,
    max_days: maxDays,
    telemetry: groupTelemetryMetrics(telemetryRows?.results || []),
    autopilot_usage: groupAutopilotUsage(usageRows?.results || []),
  };
}

/**
 * T34: format snapshotu jako czytelny reply dla bota `!agri-metrics`
 * (Discord/Telegram). Read-only, bez sekretów. Limit długości pilnowany
 * top-N wpisami (Discord 2000 / Telegram 4096 znaków).
 */
function formatAgriMetricsReply(snapshot) {
  if (!snapshot) return "Brak danych metryk upraw.";
  if (snapshot.error === "no_db" || snapshot.reason === "no_db") {
    return "Metryki upraw niedostępne (brak D1 w środowisku).";
  }
  if (!snapshot.success) {
    return "Metryki upraw niedostępne.";
  }
  const lines = ["🌱 **Metryki upraw**", ""];
  const telemetry = Array.isArray(snapshot.telemetry) ? snapshot.telemetry.slice(0, 5) : [];
  const hiddenTelemetry = Math.max((snapshot.telemetry?.length || 0) - telemetry.length, 0);

  if (!telemetry.length) {
    lines.push("Telemetria: brak agregatów dziennych (uruchom /v1/agri/telemetry).");
  } else {
    lines.push("**Czujniki (najnowsze dni):**");
    for (const entry of telemetry) {
      const parts = [entry.avg !== undefined ? `avg=${entry.avg}` : null,
        entry.min !== undefined ? `min=${entry.min}` : null,
        entry.max !== undefined ? `max=${entry.max}` : null].filter(Boolean);
      lines.push(`• ${entry.sensor} @ ${entry.day_key}: ${parts.join(" / ")}`);
    }
    if (hiddenTelemetry > 0) lines.push(`…oraz ${hiddenTelemetry} starszych wpisów.`);
  }

  lines.push("", "**Autopilot (budżet dzienny):**");
  const usage = Array.isArray(snapshot.autopilot_usage) ? snapshot.autopilot_usage.slice(0, 5) : [];
  if (!usage.length) {
    lines.push("Brak użyć autopilota.");
  } else {
    for (const entry of usage) {
      lines.push(`• ${entry.policy_id} @ ${entry.day_key}: użyto ${entry.used_count}`);
    }
  }

  const text = lines.join("\n");
  // Twarde ograniczenie bezpieczeństwa na wypadek nietypowych danych.
  return text.length > 1800 ? `${text.slice(0, 1790)}…` : text;
}

export { formatAgriMetricsReply };
