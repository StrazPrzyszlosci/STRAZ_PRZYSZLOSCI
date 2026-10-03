import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  buildCalibrationSeedPolicyPatch,
  calibrationPackId,
  formatCalibrationApplyReply,
  handleCalibrationCommand,
  parseCalibrationApplyCommand,
  startCalibrationPack,
  validateExecutionPackId,
} from "../cloudflare/src/execution_pack_initiator.js";
import { suggestBandAdjustments } from "../cloudflare/src/agri_calibration.js";

const policy = {
  id: "grow_policy_aquaponics_greens_01",
  grow_cell_id: "phone-aquaponics-observer-01",
  bands: {
    ph: { safe_min: 5.9, safe_max: 6.5, alarm_below: 5.5, alarm_above: 7.0 },
    water_temp_c: { safe_min: 18.0, safe_max: 24.0, alarm_below: 15.0, alarm_above: 28.0 },
  },
};

const strongCorrelation = {
  success: true,
  sensors: [
    { sensor: "ph", pearson_r: 0.85, months_with_data: 4, monthly_means: {} },
    { sensor: "water_temp_c", pearson_r: -0.8, months_with_data: 4, monthly_means: {} },
  ],
};

const weakCorrelation = {
  success: true,
  sensors: [
    { sensor: "ph", pearson_r: 0.1, months_with_data: 4, monthly_means: {} },
  ],
};

function createDb() {
  const records = [];
  return {
    _records: records,
    prepare(sql) {
      return {
        bind(...args) {
          return {
            async run() {
              if (sql.includes("INSERT INTO execution_packs")) {
                records.push({ pack_id: args[0], status: args[1], reviewer: args[2] });
              }
              return { changes: 1 };
            },
          };
        },
      };
    },
  };
}

describe("T42 calibration draft-PR", () => {
  it("parses !calibration apply with policy and optional reviewer", () => {
    assert.deepEqual(parseCalibrationApplyCommand("!calibration apply grow_policy_01 alice"), {
      action: "apply",
      policy_id: "grow_policy_01",
      reviewer: "alice",
    });
    assert.deepEqual(parseCalibrationApplyCommand("!CALIBRATION APPLY grow_policy_01"), {
      action: "apply",
      policy_id: "grow_policy_01",
      reviewer: "",
    });
    assert.equal(parseCalibrationApplyCommand("!calibration"), null);
    assert.equal(parseCalibrationApplyCommand("!calibration apply"), null);
    assert.equal(parseCalibrationApplyCommand("!execution-pack start x"), null);
  });

  it("builds pack ids valid for the ledger and within limits", () => {
    const id = calibrationPackId(policy.id, "2026-10-02T12:00:00.000Z");
    assert.equal(validateExecutionPackId(id), id);
    assert.ok(id.startsWith("calibration-"));
    assert.ok(id.length <= 120);
  });

  it("builds seed_policy patch with proposed bands only", () => {
    const suggestion = suggestBandAdjustments(policy, strongCorrelation, {});
    const patch = buildCalibrationSeedPolicyPatch(policy, suggestion);
    assert.equal(patch.policy_id, policy.id);
    assert.equal(patch.band_patches.length, 2);
    assert.equal(patch.patch_json.includes("6.53"), true);
    const parsed = JSON.parse(patch.patch_json);
    assert.equal(parsed.proposed_bands.ph.safe_max, 6.53);
    assert.equal(parsed.proposed_bands.water_temp_c.safe_min, 17.7);
  });
});

describe("T42 calibration pack flow", () => {
  it("opens draft pack in DRY_RUN without merge and without secrets in reply", async () => {
    const calls = [];
    const env = {
      DB: createDb(),
      EXECUTION_PACK_DRY_RUN: "1",
      GITHUB_TOKEN: "super-secret-token",
      EXECUTION_PACK_DEFAULT_REVIEWER: "alice",
    };
    const result = await startCalibrationPack(
      env,
      { user_id: "u1", username: "operator" },
      {
        policy_id: policy.id,
        platform: "discord",
        now: "2026-10-02T12:00:00.000Z",
        policy,
        correlation: strongCorrelation,
      }
    );
    assert.equal(result.status, "started");
    assert.equal(result.suggest_only, true);
    assert.equal(result.auto_applied, false);
    assert.equal(result.suggestion_count, 2);
    assert.equal(env.DB._records.length, 1);
    assert.equal(calls.length, 0); // dry_run: zero HTTP

    const reply = formatCalibrationApplyReply(result);
    assert.match(reply, /suggest-only|draft/i);
    assert.match(reply, /nie merge'uje|human review/i);
    assert.ok(!reply.includes("super-secret-token"));
  });

  it("creates GitHub DRAFT pr without any merge call", async () => {
    const calls = [];
    const env = {
      DB: createDb(),
      GITHUB_TOKEN: "tok",
      __TEST_FETCH: async (url, init) => {
        calls.push({ url, method: init?.method, body: JSON.parse(init?.body || "{}") });
        return { ok: true, json: async () => ({ html_url: "https://github.com/o/r/pull/7" }) };
      },
    };
    const result = await startCalibrationPack(
      env,
      { user_id: "u1", username: "operator" },
      { policy_id: policy.id, reviewer: "alice", policy, correlation: strongCorrelation }
    );
    assert.equal(result.pr_url, "https://github.com/o/r/pull/7");
    assert.equal(calls.length, 1);
    assert.equal(calls[0].method, "POST");
    assert.match(calls[0].url, /\/pulls$/);
    assert.equal(calls[0].body.draft, true);
    assert.match(calls[0].body.title, /CALIBRATION/);
    assert.ok(!calls.some((c) => c.url.includes("/merge")));
    assert.ok(calls[0].body.body.includes("seed_policy.json"));
    assert.ok(calls[0].body.body.includes("no_auto_merge"));
  });

  it("skips pack creation when nothing passes thresholds", async () => {
    const db = createDb();
    const result = await startCalibrationPack(
      { DB: db, EXECUTION_PACK_DEFAULT_REVIEWER: "alice" },
      {},
      { policy_id: policy.id, policy, correlation: weakCorrelation }
    );
    assert.equal(result.status, "no_suggestions");
    assert.equal(db._records.length, 0);
    assert.match(formatCalibrationApplyReply(result), /nie utworzony|Brak sugestii/);
  });

  it("handles unknown policy and bad usage as bot replies", async () => {
    const db = createDb();
    const missing = await handleCalibrationCommand(
      { DB: { prepare: () => ({ bind: () => ({ first: async () => null }) }) }, EXECUTION_PACK_DEFAULT_REVIEWER: "alice" },
      { text: "!calibration apply no_such_policy alice" },
      "discord"
    );
    assert.match(missing.reply_text, /^Blad kalibracji: Nie znaleziono polityki/);

    const usage = await handleCalibrationCommand({ DB: db }, { text: "!calibration" }, "telegram");
    assert.match(usage.reply_text, /Uzycie: `!calibration apply/);
    assert.equal(db._records.length, 0);
  });
});
