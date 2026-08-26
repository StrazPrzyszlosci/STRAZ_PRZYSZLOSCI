/**
 * T29 — telemetria czujników upraw: batch NDJSON -> staging + agregaty dzienne.
 *
 * Kontrakt (jeden obiekt JSON na linie, UTF-8):
 *   WYMAGANE: sensor ([a-z0-9_]+), value (liczba skończona),
 *             recorded_at (ISO 8601 timestamp)
 *   OPCJONALNE: unit, source (provenance), provider_id (ignorowany —
 *               nadpisywany uwierzytelnionym providerem z endpointu)
 *   LIMITY: max 5000 linii / 64KB na linię.
 *
 * Gwarancje:
 *  - dedup: SHA-256(provider|sensor|recorded_at|value) UNIQUE,
 *  - audit event per batch do sensor_telemetry_events,
 *  - staging only: odczyty nie modyfikują katalogu ani polityk;
 *    agregaty dzienne (avg/min/max per sensor) dopisywane do
 *    automation_metrics (B4) jako read-only snapshoty.
 */

const TELEMETRY_MAX_LINES = 5000;
const TELEMETRY_MAX_LINE_LENGTH = 65536;
const SENSOR_RE = /^[a-z0-9_]+$/;

function toText(value) {
  return value === undefined || value === null ? "" : String(value);
}

export async function computeTelemetryDedupChecksum(row) {
  const payload = [
    toText(row.provider_id),
    toText(row.sensor),
    toText(row.recorded_at),
    String(Number(row.value)),
  ].join("\u001f");
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(payload));
  return Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, "0")).join("");
}

export function parseTelemetryJsonl(text) {
  const rows = [];
  const errors = [];
  const lines = toText(text).split(/\r?\n/);
  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index].trim();
    if (!line) continue;
    const lineNumber = index + 1;
    if (line.length > TELEMETRY_MAX_LINE_LENGTH) {
      errors.push({ line: lineNumber, error: `line longer than ${TELEMETRY_MAX_LINE_LENGTH} bytes` });
      continue;
    }
    let parsed;
    try {
      parsed = JSON.parse(line);
    } catch (err) {
      errors.push({ line: lineNumber, error: `invalid_json: ${err.message}` });
      continue;
    }
    const problems = validateTelemetryRow(parsed);
    if (problems.length) {
      errors.push({ line: lineNumber, error: `contract_missing:${problems.join(",")}` });
      continue;
    }
    rows.push(parsed);
    if (rows.length >= TELEMETRY_MAX_LINES) break;
  }
  return { rows, errors };
}

function validateTelemetryRow(row) {
  if (!row || typeof row !== "object" || Array.isArray(row)) return ["line_must_be_json_object"];
  const problems = [];
  if (!SENSOR_RE.test(toText(row.sensor))) problems.push("sensor_pattern_[a-z0-9_]");
  const value = Number(row.value);
  if (typeof row.value === "boolean" || !Number.isFinite(value)) problems.push("value_finite_number");
  if (!toText(row.recorded_at) || Number.isNaN(Date.parse(toText(row.recorded_at)))) problems.push("recorded_at_iso_timestamp");
  if (row.unit !== undefined && row.unit !== null && typeof row.unit !== "string") problems.push("unit_must_be_string");
  if (row.source !== undefined && row.source !== null && typeof row.source !== "string") problems.push("source_must_be_string");
  return problems;
}

async function refreshDailyAggregates(db, providerId, sensors, dayStartIso, nextDayStartIso, now) {
  for (const sensor of sensors) {
    const stats = await db.prepare(
      `SELECT AVG(value) AS avg_value, MIN(value) AS min_value, MAX(value) AS max_value
       FROM sensor_readings_staging
       WHERE provider_id = ? AND sensor = ? AND recorded_at >= ? AND recorded_at < ?`
    ).bind(providerId, sensor, dayStartIso, nextDayStartIso).first();
    if (!stats || stats.avg_value === null) continue;
    const measuredAt = `${dayKey(dayStartIso)}T00:00:00.000Z`;
    for (const [suffix, rawValue] of [["avg", stats.avg_value], ["min", stats.min_value], ["max", stats.max_value]]) {
      const metricKey = `telemetry_${sensor}_${suffix}_${dayKey(dayStartIso)}`;
      await db.prepare(
        `DELETE FROM automation_metrics WHERE metric_key = ? AND window = 'daily'`
      ).bind(metricKey).run();
      await db.prepare(
        `INSERT INTO automation_metrics (metric_key, metric_value, measured_at, window)
         VALUES (?, ?, ?, 'daily')`
      ).bind(metricKey, Number(rawValue), measuredAt).run();
    }
  }
}

function dayKey(iso) {
  return String(iso).slice(0, 10);
}

function utcDayBounds(isoTimestamp) {
  const time = Date.parse(isoTimestamp);
  const start = new Date(time);
  start.setUTCHours(0, 0, 0, 0);
  const end = new Date(start.getTime());
  end.setUTCDate(end.getUTCDate() + 1);
  return { dayStartIso: start.toISOString(), nextDayStartIso: end.toISOString() };
}

export async function ingestTelemetry(env, providerId, text, options = {}) {
  if (!env?.DB) return { success: false, reason: "no_db" };
  const now = options.now || new Date().toISOString();
  const { rows, errors } = parseTelemetryJsonl(text);
  if (errors.length) return { success: false, reason: "invalid_payload", accepted: rows.length, errors };
  if (!rows.length) return { success: false, reason: "empty_payload" };

  let inserted = 0;
  let skipped = 0;
  const touchedSensors = new Set();

  for (const inputRow of rows) {
    const row = {
      ...inputRow,
      provider_id: toText(providerId),
      value: Number(inputRow.value),
    };
    row.dedup_checksum = await computeTelemetryDedupChecksum(row);
    const existing = await env.DB.prepare(
      `SELECT id FROM sensor_readings_staging WHERE dedup_checksum = ?`
    ).bind(row.dedup_checksum).first();
    if (existing) {
      skipped += 1;
      continue;
    }
    await env.DB.prepare(
      `INSERT INTO sensor_readings_staging
        (provider_id, sensor, value, unit, source, recorded_at, ingested_at, dedup_checksum)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?)`
    ).bind(
      row.provider_id,
      row.sensor,
      row.value,
      toText(row.unit) || null,
      toText(row.source) || null,
      toText(row.recorded_at),
      now,
      row.dedup_checksum
    ).run();
    inserted += 1;
    touchedSensors.add(row.sensor);
  }

  await env.DB.prepare(
    `INSERT INTO sensor_telemetry_events (kind, provider_id, batch_count, inserted_count, skipped_count, created_at)
     VALUES ('telemetry_ingest', ?, ?, ?, ?, ?)`
  ).bind(toText(providerId), rows.length, inserted, skipped, now).run();

  let aggregates = {};
  if (inserted > 0) {
    const bounds = utcDayBounds(now);
    await refreshDailyAggregates(env.DB, toText(providerId), [...touchedSensors], bounds.dayStartIso, bounds.nextDayStartIso, now);
    aggregates = { day_key: dayKey(bounds.dayStartIso), sensors: [...touchedSensors].sort() };
  }

  return {
    success: true,
    kind: "telemetry_ingest",
    provider_id: toText(providerId),
    count: rows.length,
    inserted,
    skipped,
    staged_only: true,
    aggregates,
  };
}

// T31: retencja surowych odczytów — agregaty dzienne zostają w automation_metrics,
// więc staging może być przycinany agresywniej niż stream zdarzeń.
export const DEFAULT_SENSOR_READING_RETENTION_DAYS = 90;

export function resolveSensorReadingRetentionConfig(env) {
  const parsed = Number(env?.SENSOR_READINGS_RETENTION_DAYS);
  const retentionDays = Number.isFinite(parsed) && parsed > 0 ? Math.floor(parsed) : DEFAULT_SENSOR_READING_RETENTION_DAYS;
  return { retention_days: retentionDays };
}

export async function pruneSensorReadings(db, options = {}) {
  if (!db) return { success: false, reason: "no_db", pruned: 0 };
  const retentionDays = Math.max(1, Number(options.retentionDays || DEFAULT_SENSOR_READING_RETENTION_DAYS));
  const cutoffIso = new Date(Date.parse(options.now || new Date().toISOString()) - retentionDays * 86400000).toISOString();
  const result = await db.prepare(
    `DELETE FROM sensor_readings_staging WHERE recorded_at < ?`
  ).bind(cutoffIso).run();
  return { success: true, pruned: Number(result?.meta?.changes || 0), retention_days: retentionDays, cutoff_iso: cutoffIso };
}
