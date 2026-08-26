import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  dayKeyFromIso,
  deactivateAgriPolicy,
  evaluateAgriReadings,
  getActiveAgriPolicy,
  runAgriEvaluate,
  upsertAgriPolicy,
  validateAgriPolicyRecord,
} from "../cloudflare/src/agri_evaluate.js";

// Fixture = podzbiór agri_autopilot/seed_policy.json (parzystość Python <-> JS).
const policy = {
  id: "grow_policy_aquaponics_greens_01",
  grow_cell_id: "phone-aquaponics-observer-01",
  crop_profile: "leafy_greens_aquaponics",
  sensors: ["ph", "water_temp_c", "ec_ms_cm", "air_temp_c", "humidity_pct", "light_ppfd"],
  bands: {
    ph: { safe_min: 5.9, safe_max: 6.5, alarm_below: 5.5, alarm_above: 7.0 },
    water_temp_c: { safe_min: 18.0, safe_max: 24.0, alarm_below: 15.0, alarm_above: 28.0 },
    ec_ms_cm: { safe_min: 0.8, safe_max: 1.8, alarm_below: 0.4, alarm_above: 2.5 },
    air_temp_c: { safe_min: 18.0, safe_max: 26.0, alarm_below: 10.0, alarm_above: 32.0 },
    humidity_pct: { safe_min: 50.0, safe_max: 70.0, alarm_below: 40.0, alarm_above: 85.0 },
    light_ppfd: { safe_min: 150.0, safe_max: 400.0, alarm_below: 80.0, alarm_above: 600.0 },
  },
  advisories: [
    { action_id: "buffer_dose_ph_up", trigger: "ph_below_safe_min", actuation_class: "edge_auto_within_safe_band", max_per_day: 2 },
    { action_id: "reduce_light_hours", trigger: "air_temp_c_above_safe_max", actuation_class: "advisory_only" },
    { action_id: "shade_cloth_deploy", trigger: "light_ppfd_above_safe_max", actuation_class: "requires_human_approval" },
    { action_id: "top_up_water_low_ec", trigger: "ec_ms_cm_below_safe_min", actuation_class: "advisory_only" },
  ],
  autopilot_limits: { max_auto_actions_per_day: 6 },
  kill_switch_ref: "kill switch: wyłącz zasilacza pompy dozującej (gniazdo R1)",
  human_control_point: "operator przegląda każde zdarzenie przed zmianą biologiczną",
};

function createMockDb(existingPolicies = []) {
  // Wiersze zgodne z schematem po T33: active/superseded_by/version.
  const policyRows = new Map(existingPolicies.map((p) => [p.id, {
    policy_id: p.id,
    grow_cell_id: p.grow_cell_id,
    policy_json: JSON.stringify(p),
    active: 1,
    superseded_by: null,
    version: 1,
    updated_at: "2026-08-26T00:00:00.000Z",
  }]));
  const usage = new Map();
  const edgeEvents = [];
  return {
    policies: policyRows,
    usage,
    edgeEvents,
    prepare(sql) {
      return {
        bind(...args) {
          return {
            first() {
              if (sql.includes("FROM agri_grow_policies WHERE policy_id")) {
                const row = policyRows.get(args[0]);
                return row ? { ...row } : null;
              }
              if (sql.includes("FROM agri_grow_policies") && sql.includes("active = 1")) {
                const [growCellId] = args;
                const candidates = [...policyRows.values()]
                  .filter((row) => row.grow_cell_id === growCellId && row.active === 1)
                  .sort((a, b) => b.updated_at.localeCompare(a.updated_at) || b.version - a.version);
                return candidates[0] ? { ...candidates[0] } : null;
              }
              if (sql.includes("FROM agri_autopilot_usage")) {
                return usage.has(args[0]) ? { used_count: usage.get(args[0]) } : null;
              }
              if (sql.includes("FROM edge_event_stream")) return null;
              return null;
            },
            async run() {
              if (sql.includes("INSERT INTO agri_grow_policies")) {
                const [policyId, growCellId, json, createdAt, updatedAt, active] = args;
                const existing = policyRows.get(policyId);
                policyRows.set(policyId, {
                  policy_id: policyId,
                  grow_cell_id: growCellId,
                  policy_json: json,
                  created_at: existing?.created_at || createdAt,
                  updated_at: updatedAt,
                  active,
                  superseded_by: null,
                  version: (existing?.version || 0) + 1,
                });
              } else if (sql.includes("UPDATE agri_grow_policies")) {
                const [supersededBy, updatedAt, policyId] = args;
                const row = policyRows.get(policyId);
                if (row && row.active === 1) {
                  row.active = 0;
                  row.superseded_by = supersededBy;
                  row.updated_at = updatedAt;
                  return { meta: { changes: 1 } };
                }
                return { meta: { changes: 0 } };
              } else if (sql.includes("INSERT INTO agri_autopilot_usage")) {
                const [key, delta] = args;
                usage.set(key, (usage.get(key) || 0) + delta);
              } else if (sql.includes("INSERT INTO edge_event_stream")) {
                const [provider_id, kind, severity, payload_json] = args;
                edgeEvents.push({ provider_id, kind, severity, payload: JSON.parse(payload_json), id: edgeEvents.length + 1 });
              }
              return { meta: {} };
            },
            async all() {
              if (sql.includes("FROM edge_event_stream")) return { results: [] };
              return { results: [] };
            },
          };
        },
      };
    },
  };
}

describe("agri evaluate loop T27", () => {
  it("validates policy contract and rejects physical_actuation", () => {
    assert.deepEqual(validateAgriPolicyRecord(policy), []);
    const bad = structuredClone(policy);
    bad.advisories[0].actuation_class = "physical_actuation";
    assert.ok(validateAgriPolicyRecord(bad).includes("actuation_forbidden:buffer_dose_ph_up"));

    const noBudget = structuredClone(policy);
    delete noBudget.autopilot_limits;
    assert.ok(validateAgriPolicyRecord(noBudget).some((entry) => entry === "daily_budget_required"));
  });

  it("matches Python evaluator parity fixtures", () => {
    const alarm = evaluateAgriReadings(policy, { ph: 5.3 });
    assert.equal(alarm.events[0].kind, "alarm");
    assert.equal(alarm.events[0].severity, "critical");
    assert.equal(alarm.events[0].payload.suggested_action, "buffer_dose_ph_up");

    const warning = evaluateAgriReadings(policy, { air_temp_c: 27.5 });
    assert.equal(warning.events[0].kind, "recommendation");
    assert.equal(warning.summary.alarms, 0);

    const humanApproval = evaluateAgriReadings(policy, { light_ppfd: 500.0 });
    assert.equal(humanApproval.events[0].payload.suggested_action, "shade_cloth_deploy");
    assert.equal(humanApproval.events[0].payload.execution_hint, "requires_human_approval");

    const silent = evaluateAgriReadings(policy, { ph: 6.2, air_temp_c: 21.0 });
    assert.deepEqual(silent.events, []);
    assert.equal(silent.summary.ok, 2);
  });

  it("enforces server-side daily budget across evaluations", () => {
    const withinBudget = evaluateAgriReadings(policy, { ph: 5.7 }, 4);
    assert.equal(withinBudget.summary.auto_suggested, 1);
    const exhausted = evaluateAgriReadings(policy, { ph: 5.7 }, 6);
    assert.equal(exhausted.summary.auto_suggested, 0);
    assert.equal(exhausted.events[0].payload.reason, "daily_autopilot_budget_exhausted");
    assert.equal(dayKeyFromIso("2026-08-26T12:00:00.000Z"), "2026-08-26");
  });

  it("runs full loop: policy upsert, evaluate, budget increment, publish to edge stream", async () => {
    const db = createMockDb();
    const env = { DB: db };

    const saved = await upsertAgriPolicy(env, policy, { now: "2026-08-26T12:00:00.000Z" });
    assert.equal(saved.success, true);

    const first = await runAgriEvaluate(env, policy.id, { ph: 5.7, air_temp_c: 27.5 }, { now: "2026-08-26T12:01:00.000Z" });
    assert.equal(first.success, true);
    assert.equal(first.published, 2);
    assert.equal(first.used_today_after, 1);
    assert.equal(db.edgeEvents.length, 2);
    // ph 5.7 -> ostrzeżenie z akcją auto; air_temp_c 27.5 -> advisory_only.
    assert.deepEqual(db.edgeEvents.map((event) => event.kind).sort(), ["recommendation", "recommendation"]);
    const autoEvent = db.edgeEvents.find((event) => event.payload.autopilot_eligible === true);
    assert.equal(autoEvent.payload.suggested_action, "buffer_dose_ph_up");

    // Kolejne wywołania tego samego dnia widzą budżet z D1 (server-side).
    for (let i = 0; i < 5; i += 1) {
      await runAgriEvaluate(env, policy.id, { ph: 5.7 }, { now: "2026-08-26T12:02:00.000Z" });
    }
    const last = await runAgriEvaluate(env, policy.id, { ph: 5.7 }, { now: "2026-08-26T12:03:00.000Z" });
    assert.equal(last.used_today_before, 6);
    assert.equal(last.summary.auto_suggested, 0);
    const fallback = last.events[0];
    assert.equal(fallback.payload.reason, "daily_autopilot_budget_exhausted");

    const missing = await runAgriEvaluate(env, "no-such-policy", { ph: 6.0 });
    assert.equal(missing.reason, "policy_not_found");
  });

  it("rejects invalid policy on upsert without writing", async () => {
    const db = createMockDb();
    const broken = structuredClone(policy);
    broken.advisories[0].trigger = "nitrate_ppm_below_safe_min";
    const result = await upsertAgriPolicy({ DB: db }, broken);
    assert.equal(result.success, false);
    assert.ok(result.errors.some((entry) => entry.startsWith("trigger_sensor_undeclared")));
    assert.equal(db.policies.size, 0);
  });

  it("versions policies and resolves the active one per grow cell (T33)", async () => {
    const db = createMockDb();
    const env = { DB: db };

    await upsertAgriPolicy(env, policy, { now: "2026-08-20T10:00:00.000Z" });

    // Wersja sezonowa v2: ten sam grow_cell, nowy policy_id.
    const v2 = structuredClone(policy);
    v2.id = "grow_policy_aquaponics_greens_02";
    v2.autopilot_limits = { max_auto_actions_per_day: 4 };
    await upsertAgriPolicy(env, v2, { now: "2026-08-25T10:00:00.000Z" });
    const deactivated = await deactivateAgriPolicy(env, policy.id, v2.id, { now: "2026-08-25T10:00:01.000Z" });
    assert.equal(deactivated.success, true);

    // Lookup aktywnych wskazuje wyłącznie v2.
    const activeRow = await getActiveAgriPolicy(db, policy.grow_cell_id);
    assert.equal(activeRow.id, v2.id);
    assert.equal(activeRow.autopilot_limits.max_auto_actions_per_day, 4);

    // Evaluate z rozwiniętą polityką działa na aktywnej wersji.
    const evaluated = await runAgriEvaluate(env, activeRow.policy_id, { ph: 5.7 }, { now: "2026-08-26T12:01:00.000Z", policy: activeRow });
    assert.equal(evaluated.success, true);
    assert.equal(evaluated.policy_id, v2.id);

    // Bez jawnego policy_id -> brak polityki (worker rozwiązuje przez getActiveAgriPolicy).
    const missing = await runAgriEvaluate(env, "", { ph: 5.7 });
    assert.equal(missing.reason, "policy_not_found");

    // Ponowna dezaktywacja nieaktywnej -> not_found_or_inactive.
    const again = await deactivateAgriPolicy(env, policy.id, v2.id, { now: "2026-08-26T12:02:00.000Z" });
    assert.equal(again.reason, "not_found_or_inactive");

    // Re-upsert podnosi wersję w istniejącym wierszu (insert=1 -> update=2).
    const rebump = await upsertAgriPolicy(env, policy, { now: "2026-08-26T12:03:00.000Z", active: false });
    assert.equal(rebump.success, true);
    assert.equal(rebump.active, false);
    assert.equal(db.policies.get(policy.id).version, 2);
  });

  it("keeps separate daily budgets per grow cell instance (T35)", async () => {
    const db = createMockDb([policy]);
    const env = { DB: db };

    // Komórka A wyczerpuje budżet (6 auto-akcji).
    for (let i = 0; i < 6; i += 1) {
      const run = await runAgriEvaluate(env, policy.id, { ph: 5.7 }, {
        now: "2026-08-26T12:00:00.000Z",
        instanceGrowCellId: "grow-cell-A",
      });
      assert.equal(run.summary.auto_suggested, 1);
    }
    const exhaustedA = await runAgriEvaluate(env, policy.id, { ph: 5.7 }, {
      now: "2026-08-26T12:05:00.000Z",
      instanceGrowCellId: "grow-cell-A",
    });
    assert.equal(exhaustedA.summary.auto_suggested, 0);
    assert.equal(exhaustedA.events[0].payload.reason, "daily_autopilot_budget_exhausted");

    // Komórka B na tej samej polityce ma własny, nietknięty budżet.
    const freshB = await runAgriEvaluate(env, policy.id, { ph: 5.7 }, {
      now: "2026-08-26T12:06:00.000Z",
      instanceGrowCellId: "grow-cell-B",
    });
    assert.equal(freshB.success, true);
    assert.equal(freshB.instance_grow_cell_id, "grow-cell-B");
    assert.equal(freshB.used_today_before, 0);
    assert.equal(freshB.summary.auto_suggested, 1);

    // Bez instancji domyślnie liczy się grow_cell_id z polityki.
    const defaultInstance = await runAgriEvaluate(env, policy.id, { ph: 5.7 }, { now: "2026-08-26T12:07:00.000Z" });
    assert.equal(defaultInstance.instance_grow_cell_id, policy.grow_cell_id);
    assert.equal(db.usage.size, 3); // A|day, B|day, default|day
  });
});
