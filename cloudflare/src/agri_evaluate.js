/**
 * T27 — zamknięcie pętli rolnictwa autonomicznego: evaluate → edge events.
 *
 * Port logiki `agri_autopilot/evaluate_readings.py` na JS (Worker nie uruchamia
 * Pythona). Polityki trzymane w D1 (`agri_grow_policies`), budżet dzienny
 * autopilota liczony po stronie serwera (`agri_autopilot_usage`).
 *
 * Gwarancje:
 *  - physical_actuation jest odrzucana (walidacja polityki),
 *  - akcje auto tylko w pasmie ostrzegawczym i w dziennym budżecie,
 *  - evaluator tylko sugeruje; zdarzenia trafiają do edge_event_stream (T22),
 *    skąd grow-agent pobiera je przez GET /v1/ws/events.
 */

import { publishEdgeEvent } from "./edge_events_stream.js";

const ACTUATION_CLASSES = new Set([
  "advisory_only",
  "edge_auto_within_safe_band",
  "requires_human_approval",
]);
const POLICY_ID_RE = /^[a-z0-9][a-z0-9_-]{2,80}$/;
const TRIGGER_RE = /^([a-z0-9_]+)_(below_safe_min|above_safe_max)$/;

function toText(value) {
  return value === undefined || value === null ? "" : String(value);
}

export function validateAgriPolicyRecord(policy) {
  const errors = [];
  if (!policy || typeof policy !== "object") return ["policy_must_be_object"];
  const pid = policy.id;
  if (typeof pid !== "string" || !POLICY_ID_RE.test(pid)) errors.push("id_invalid");
  if (!toText(policy.grow_cell_id).trim()) errors.push("grow_cell_id_required");

  const sensors = Array.isArray(policy.sensors) ? policy.sensors : [];
  if (!sensors.length) errors.push("sensors_required");
  const bands = policy.bands && typeof policy.bands === "object" ? policy.bands : {};
  for (const sensor of sensors) {
    const band = bands[sensor];
    if (!band || typeof band !== "object") {
      errors.push(`bands_missing:${sensor}`);
      continue;
    }
    const { safe_min, safe_max, alarm_below, alarm_above } = band;
    if ([safe_min, safe_max, alarm_below, alarm_above].some((v) => typeof v !== "number" || Number.isNaN(v))) {
      errors.push(`bands_numeric:${sensor}`);
      continue;
    }
    if (safe_min >= safe_max) errors.push(`safe_min_lt_safe_max:${sensor}`);
    if (alarm_below > safe_min) errors.push(`alarm_below_le_safe_min:${sensor}`);
    if (alarm_above < safe_max) errors.push(`alarm_above_ge_safe_max:${sensor}`);
  }

  let hasAuto = false;
  const advisories = Array.isArray(policy.advisories) ? policy.advisories : [];
  if (!advisories.length) errors.push("advisories_required");
  for (const advisory of advisories) {
    const actionId = toText(advisory?.action_id);
    if (!POLICY_ID_RE.test(actionId)) errors.push(`advisory_id_invalid:${actionId}`);
    const match = TRIGGER_RE.exec(toText(advisory?.trigger));
    if (!match) errors.push(`trigger_invalid:${actionId}`);
    else if (!sensors.includes(match[1])) errors.push(`trigger_sensor_undeclared:${actionId}`);
    const actuationClass = advisory?.actuation_class;
    if (actuationClass === "physical_actuation") errors.push(`actuation_forbidden:${actionId}`);
    else if (!ACTUATION_CLASSES.has(actuationClass)) errors.push(`actuation_class_invalid:${actionId}`);
    if (actuationClass === "edge_auto_within_safe_band") {
      hasAuto = true;
      const maxPerDay = advisory.max_per_day;
      if (!Number.isInteger(maxPerDay) || maxPerDay < 1 || maxPerDay > 10) {
        errors.push(`max_per_day_required:${actionId}`);
      }
    }
  }
  if (hasAuto) {
    const budget = policy.autopilot_limits?.max_auto_actions_per_day;
    if (!Number.isInteger(budget) || budget < 1 || budget > 12) errors.push("daily_budget_required");
  }
  if (toText(policy.kill_switch_ref).length < 5) errors.push("kill_switch_required");
  if (toText(policy.human_control_point).length < 10) errors.push("human_control_point_required");
  return errors;
}

export async function upsertAgriPolicy(env, policy, options = {}) {
  if (!env?.DB) return { success: false, reason: "no_db" };
  const errors = validateAgriPolicyRecord(policy);
  if (errors.length) {
    return { success: false, reason: "invalid_policy", errors };
  }
  const now = options.now || new Date().toISOString();
  const active = options.active === false ? 0 : 1;
  await env.DB.prepare(
    `INSERT INTO agri_grow_policies (policy_id, grow_cell_id, policy_json, created_at, updated_at, active, version)
     VALUES (?, ?, ?, ?, ?, ?, 1)
     ON CONFLICT(policy_id) DO UPDATE SET
       grow_cell_id=excluded.grow_cell_id,
       policy_json=excluded.policy_json,
       updated_at=excluded.updated_at,
       active=excluded.active,
       version=agri_grow_policies.version + 1`
  ).bind(policy.id, policy.grow_cell_id, JSON.stringify(policy), now, now, active).run();
  return { success: true, policy_id: policy.id, grow_cell_id: policy.grow_cell_id, active: active === 1 };
}

/**
 * T33: dezaktywacja polityki (rotacja sezonowa). Aktywna polityka dostaje
 * wskaźnik superseded_by -> id następcy; evaluate nigdy nie sięgnie po nią
 * przez lookup aktywnych.
 */
export async function deactivateAgriPolicy(env, policyId, supersededBy, options = {}) {
  if (!env?.DB) return { success: false, reason: "no_db" };
  const now = options.now || new Date().toISOString();
  const result = await env.DB.prepare(
    `UPDATE agri_grow_policies
     SET active = 0, superseded_by = ?, updated_at = ?
     WHERE policy_id = ? AND active = 1`
  ).bind(toText(supersededBy) || null, now, toText(policyId)).run();
  if (!Number(result?.meta?.changes || 0)) {
    return { success: false, reason: "not_found_or_inactive", policy_id: toText(policyId) };
  }
  return { success: true, policy_id: toText(policyId), superseded_by: toText(supersededBy) || null };
}

export async function getAgriPolicy(db, policyId) {
  if (!db) return null;
  const row = await db.prepare(
    `SELECT policy_id, grow_cell_id, policy_json FROM agri_grow_policies WHERE policy_id = ?`
  ).bind(toText(policyId)).first();
  if (!row) return null;
  try {
    return JSON.parse(row.policy_json);
  } catch {
    return null;
  }
}

/**
 * T33: najnowsza AKTYWNA polityka dla komórki uprawy (rotacja sezonowa).
 */
export async function getActiveAgriPolicy(db, growCellId) {
  if (!db) return null;
  const row = await db.prepare(
    `SELECT policy_id, grow_cell_id, policy_json FROM agri_grow_policies
     WHERE grow_cell_id = ? AND active = 1
     ORDER BY updated_at DESC, version DESC LIMIT 1`
  ).bind(toText(growCellId)).first();
  if (!row) return null;
  try {
    return JSON.parse(row.policy_json);
  } catch {
    return null;
  }
}

export function dayKeyFromIso(nowIso) {
  return String(nowIso).slice(0, 10);
}

export function advisoryIndex(policy) {
  const index = {};
  for (const advisory of policy?.advisories || []) {
    if (advisory?.trigger) index[advisory.trigger] = advisory;
  }
  return index;
}

/**
 * Port agri_autopilot/evaluate_readings.py — deterministyczny, bez efektów ubocznych.
 */
export function evaluateAgriReadings(policy, readings, usedToday = 0) {
  const events = [];
  const advisories = advisoryIndex(policy);
  const budget = Number(policy?.autopilot_limits?.max_auto_actions_per_day || 0);
  let budgetLeft = Math.max(budget - Number(usedToday || 0), 0);
  const summary = { alarms: 0, warnings: 0, auto_suggested: 0, ok: 0 };
  const growCellId = toText(policy?.grow_cell_id || "unknown-grow-cell");
  const bands = policy?.bands || {};

  for (const [sensor, rawValue] of Object.entries(readings || {})) {
    const band = bands[sensor];
    const value = typeof rawValue === "boolean" ? NaN : Number(rawValue);
    if (!band || !Number.isFinite(value)) continue;

    const basePayload = { sensor, value, policy_id: policy.id };
    const belowAlarm = value < band.alarm_below;
    const aboveAlarm = value > band.alarm_above;
    const belowSafe = value < band.safe_min;
    const aboveSafe = value > band.safe_max;

    if (belowAlarm || aboveAlarm) {
      summary.alarms += 1;
      const trigger = belowAlarm ? `${sensor}_below_safe_min` : `${sensor}_above_safe_max`;
      events.push({
        provider_id: growCellId,
        kind: "alarm",
        severity: "critical",
        payload: {
          ...basePayload,
          direction: belowAlarm ? "below_alarm" : "above_alarm",
          suggested_action: advisories[trigger]?.action_id ?? null,
          execution_hint: "manual_by_operator",
          kill_switch_ref: policy.kill_switch_ref,
        },
      });
      continue;
    }

    if (!belowSafe && !aboveSafe) {
      summary.ok += 1;
      continue;
    }

    const trigger = belowSafe ? `${sensor}_below_safe_min` : `${sensor}_above_safe_max`;
    const advisory = advisories[trigger];
    const actuationClass = advisory?.actuation_class || "advisory_only";
    const payload = {
      ...basePayload,
      direction: belowSafe ? "below_safe_min" : "above_safe_max",
      suggested_action: advisory?.action_id ?? null,
    };

    if (actuationClass === "edge_auto_within_safe_band") {
      if (budgetLeft > 0) {
        budgetLeft -= 1;
        summary.auto_suggested += 1;
        summary.warnings += 1;
        events.push({
          provider_id: growCellId,
          kind: "recommendation",
          severity: "warning",
          payload: {
            ...payload,
            autopilot_eligible: true,
            max_per_day: advisory.max_per_day,
            human_control_point: policy.human_control_point,
          },
        });
      } else {
        summary.warnings += 1;
        events.push({
          provider_id: growCellId,
          kind: "recommendation",
          severity: "warning",
          payload: {
            ...payload,
            autopilot_eligible: false,
            reason: "daily_autopilot_budget_exhausted",
            execution_hint: "manual_by_operator",
          },
        });
      }
      continue;
    }

    summary.warnings += 1;
    events.push({
      provider_id: growCellId,
      kind: "recommendation",
      severity: "warning",
      payload: {
        ...payload,
        actuation_class: actuationClass,
        execution_hint:
          actuationClass === "requires_human_approval"
            ? "requires_human_approval"
            : "manual_by_operator",
        human_control_point: policy.human_control_point,
      },
    });
  }

  return { events, summary };
}

// T35: klucz budżetu zawiera instancję komórki — ta sama polityka może
// obsługiwać wiele komórek i każda ma osobny dzienny limit.
export function usageKey(policyId, growCellId, dayKey) {
  return `${toText(policyId)}|${toText(growCellId)}|${dayKey}`;
}

export async function getUsedToday(db, policyId, growCellId, dayKey) {
  if (!db) return 0;
  const row = await db.prepare(
    `SELECT used_count FROM agri_autopilot_usage WHERE usage_key = ?`
  ).bind(usageKey(policyId, growCellId, dayKey)).first();
  return Number(row?.used_count || 0);
}

export async function incrementUsedToday(db, policyId, growCellId, dayKey, delta, now) {
  await db.prepare(
    `INSERT INTO agri_autopilot_usage (usage_key, used_count, updated_at)
     VALUES (?, ?, ?)
     ON CONFLICT(usage_key) DO UPDATE SET
       used_count = used_count + excluded.used_count,
       updated_at = excluded.updated_at`
  ).bind(usageKey(policyId, growCellId, dayKey), delta, now).run();
}

/**
 * Orkiestracja endpointu: polityka z D1 → ewaluacja → publikacja zdarzeń (T22)
 * + server-side budżet. Zwraca zdarzenia i podsumowanie.
 * T35: options.instanceGrowCellId pozwala liczyć budżet dla instancji komórki
 * innej niż grow_cell_id w polityce (wiele komórek na jednej polityce).
 */
export async function runAgriEvaluate(env, policyId, readings, options = {}) {
  if (!env?.DB) return { success: false, reason: "no_db" };
  const now = options.now || new Date().toISOString();
  const policy = options.policy || await getAgriPolicy(env.DB, policyId);
  if (!policy) {
    return { success: false, reason: "policy_not_found", policy_id: toText(policyId) };
  }
  const instanceGrowCellId = toText(options.instanceGrowCellId || "").trim() || policy.grow_cell_id;
  const dayKey = dayKeyFromIso(now);
  const usedToday = options.usedTodayOverride ?? await getUsedToday(env.DB, policy.id, instanceGrowCellId, dayKey);
  const result = evaluateAgriReadings(policy, readings, usedToday);

  const autoSuggested = result.summary.auto_suggested;
  if (autoSuggested > 0 && !options.dryRun) {
    await incrementUsedToday(env.DB, policy.id, instanceGrowCellId, dayKey, autoSuggested, now);
  }
  let published = 0;
  for (const event of result.events) {
    const publishResult = await publishEdgeEvent(env, event, { now });
    if (publishResult.success) published += 1;
  }

  return {
    success: true,
    policy_id: policy.id,
    grow_cell_id: policy.grow_cell_id,
    instance_grow_cell_id: instanceGrowCellId,
    events: result.events,
    summary: result.summary,
    published,
    used_today_before: usedToday,
    used_today_after: usedToday + autoSuggested,
    day_key: dayKey,
  };
}
