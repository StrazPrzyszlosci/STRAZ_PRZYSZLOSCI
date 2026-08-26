/**
 * T36 — ledger plonów (harvest): domknięcie pętli uczenia rolnictwa
 * autonomicznego. Telemetria (T29) mówi "jak rosło"; harvest mówi "ile
 * urosło" — korelacja obu pozwala kalibrować pasma polityk (T33).
 *
 * Kontrakt rekordu (JSON body):
 *   WYMAGANE: crop_profile (niepusty string), mass_g (liczba > 0, <= 1e6),
 *             harvested_at (ISO 8601; max 5 min w przyszłość)
 *   OPCJONALNE: quality_note, unit_hint, source (provenance)
 *   grow_cell_id jest nadpisywany uwierzytelnionym providerem z endpointu.
 *
 * Gwarancje:
 *  - dedup: SHA-256(cell|crop|harvested_at|mass_g) UNIQUE,
 *  - audit event per wpis do harvest_audit_events,
 *  - agregat miesięczny `harvest_<cell>_<YYYY-MM>` (SUM mass_g) w
 *    automation_metrics (window='monthly') dla dashboardu T32/B4.
 */

const MAX_MASS_G = 1000000;
const MAX_FUTURE_SKEW_MS = 5 * 60 * 1000;

function toText(value) {
  return value === undefined || value === null ? "" : String(value);
}

export function validateHarvestRecord(record, nowIso) {
  if (!record || typeof record !== "object" || Array.isArray(record)) {
    return ["body_must_be_json_object"];
  }
  const problems = [];
  if (!toText(record.crop_profile).trim()) problems.push("crop_profile_required");
  const mass = Number(record.mass_g);
  if (typeof record.mass_g === "boolean" || !Number.isFinite(mass) || mass <= 0 || mass > MAX_MASS_G) {
    problems.push(`mass_g_positive_number_le_${MAX_MASS_G}`);
  }
  const harvestedAt = toText(record.harvested_at);
  const parsedTime = Date.parse(harvestedAt);
  if (!harvestedAt || Number.isNaN(parsedTime)) {
    problems.push("harvested_at_iso_timestamp");
  } else {
    const skew = parsedTime - Date.parse(nowIso || new Date().toISOString());
    if (skew > MAX_FUTURE_SKEW_MS) problems.push("harvested_at_not_in_future");
  }
  for (const field of ["quality_note", "unit_hint", "source"]) {
    if (record[field] !== undefined && record[field] !== null && typeof record[field] !== "string") {
      problems.push(`${field}_must_be_string`);
    }
  }
  return problems;
}

export async function computeHarvestDedupChecksum(row) {
  const payload = [
    toText(row.grow_cell_id),
    toText(row.crop_profile),
    toText(row.harvested_at),
    String(Number(row.mass_g)),
  ].join("\u001f");
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(payload));
  return Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, "0")).join("");
}

export function monthKeyFromIso(isoTimestamp) {
  return String(isoTimestamp || "").slice(0, 7);
}

async function refreshMonthlyAggregate(db, growCellId, monthKey) {
  const prefix = `${toText(growCellId)}|`;
  const stats = await db.prepare(
    `SELECT SUM(mass_g) AS total_mass FROM harvest_records
     WHERE grow_cell_id = ? AND substr(harvested_at, 1, 7) = ?`
  ).bind(toText(growCellId), monthKey).first();
  if (!stats || stats.total_mass === null) return;
  const metricKey = `harvest_${toText(growCellId)}_${monthKey}`;
  await db.prepare(
    `DELETE FROM automation_metrics WHERE metric_key = ? AND window = 'monthly'`
  ).bind(metricKey).run();
  await db.prepare(
    `INSERT INTO automation_metrics (metric_key, metric_value, measured_at, window)
     VALUES (?, ?, ?, 'monthly')`
  ).bind(metricKey, Number(stats.total_mass), `${monthKey}-01T00:00:00.000Z`).run();
}

export async function recordHarvest(env, providerId, record, options = {}) {
  if (!env?.DB) return { success: false, reason: "no_db" };
  const now = options.now || new Date().toISOString();
  const growCellId = toText(providerId).trim();
  const problems = validateHarvestRecord(record, now);
  if (problems.length) {
    return { success: false, reason: "invalid_record", errors: problems };
  }

  const row = {
    ...record,
    grow_cell_id: growCellId,
    mass_g: Number(record.mass_g),
  };
  row.dedup_checksum = await computeHarvestDedupChecksum(row);

  const existing = await env.DB.prepare(
    `SELECT id FROM harvest_records WHERE dedup_checksum = ?`
  ).bind(row.dedup_checksum).first();
  if (existing) {
    return { success: false, reason: "duplicate_harvest", dedup_checksum: row.dedup_checksum };
  }

  await env.DB.prepare(
    `INSERT INTO harvest_records
      (grow_cell_id, crop_profile, mass_g, quality_note, source, harvested_at, ingested_at, dedup_checksum)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?)`
  ).bind(
    growCellId,
    toText(row.crop_profile),
    row.mass_g,
    toText(row.quality_note) || null,
    toText(row.source) || null,
    toText(row.harvested_at),
    now,
    row.dedup_checksum
  ).run();

  const monthKey = monthKeyFromIso(row.harvested_at);
  await env.DB.prepare(
    `INSERT INTO harvest_audit_events (kind, grow_cell_id, mass_g, month_key, created_at)
     VALUES ('harvest_record', ?, ?, ?, ?)`
  ).bind(growCellId, row.mass_g, monthKey, now).run();

  await refreshMonthlyAggregate(env.DB, growCellId, monthKey);

  return {
    success: true,
    kind: "harvest_record",
    grow_cell_id: growCellId,
    crop_profile: row.crop_profile,
    mass_g: row.mass_g,
    month_key: monthKey,
  };
}
