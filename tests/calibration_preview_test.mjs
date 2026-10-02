import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  formatCalibrationPreviewReply,
  handleCalibrationCommand,
  parseCalibrationPreviewCommand,
  previewCalibration,
  resolveCalibrationSuggestion,
} from "../cloudflare/src/execution_pack_initiator.js";

const policy = {
  id: "grow_policy_aquaponics_greens_01",
  grow_cell_id: "phone-aquaponics-observer-01",
  bands: {
    ph: { safe_min: 5.9, safe_max: 6.5, alarm_below: 5.5, alarm_above: 7.0 },
  },
};

const strongCorrelation = {
  success: true,
  sensors: [{ sensor: "ph", pearson_r: 0.85, months_with_data: 4, monthly_means: {} }],
};

const weakCorrelation = {
  success: true,
  sensors: [{ sensor: "ph", pearson_r: 0.05, months_with_data: 4, monthly_means: {} }],
};

describe("T43 calibration preview", () => {
  it("parses !calibration preview strictly", () => {
    assert.deepEqual(parseCalibrationPreviewCommand("!calibration preview grow_policy_01"), {
      action: "preview",
      policy_id: "grow_policy_01",
    });
    assert.equal(parseCalibrationPreviewCommand("!calibration apply grow_policy_01"), null);
    assert.equal(parseCalibrationPreviewCommand("!calibration preview"), null);
    assert.equal(parseCalibrationPreviewCommand("!calibration"), null);
  });

  it("previews diff read-only without ledger writes or http", async () => {
    let writes = 0;
    const calls = [];
    const db = {
      prepare() {
        return { bind: () => ({ run: async () => { writes += 1; return { changes: 1 }; } }) };
      },
    };
    const env = { DB: db, __TEST_FETCH: async () => { calls.push(1); return { ok: true }; } };
    const result = await previewCalibration(env, {}, { policy_id: policy.id, policy, correlation: strongCorrelation });
    assert.equal(result.status, "preview");
    assert.equal(result.suggestion_count, 1);
    assert.equal(result.auto_applied, false);
    assert.ok(result.text.includes("ph"));
    assert.ok(result.text.length <= 1800);
    assert.equal(writes, 0);
    assert.equal(calls.length, 0);
  });

  it("reports no_suggestions honestly", async () => {
    const result = await previewCalibration({ DB: null }, {}, { policy_id: policy.id, policy, correlation: weakCorrelation });
    assert.equal(result.status, "no_suggestions");
    assert.match(formatCalibrationPreviewReply(result), /read-only|nie utworzono/i);
  });

  it("resolves suggestion pipeline shared by preview and apply (T44)", async () => {
    const resolved = await resolveCalibrationSuggestion(
      { DB: null }, policy.id, { policy, correlation: strongCorrelation }
    );
    assert.equal(resolved.policy.id, policy.id);
    assert.equal(resolved.correlation.success, true);
    assert.equal(resolved.suggestionResult.suggestions.length, 1);

    await assert.rejects(
      () => resolveCalibrationSuggestion({ DB: null }, "ghost_policy", {}),
      /Nie znaleziono polityki/
    );
    await assert.rejects(
      () => resolveCalibrationSuggestion({ DB: null }, "  ", { policy, correlation: strongCorrelation }),
      /policy_id/
    );
  });

  it("routes preview through bot handler with usage fallback", async () => {
    const ok = await handleCalibrationCommand(
      { DB: null }, { text: "!calibration preview grow_policy_aquaponics_greens_01" }, "telegram"
    );
    // DB null + brak policy w options -> blad jako reply, nie wyjatek
    assert.match(ok.reply_text, /^Blad kalibracji: Nie znaleziono polityki/);

    const withPolicy = await previewCalibration({ DB: null }, {}, { policy_id: policy.id, policy, correlation: strongCorrelation });
    const reply = formatCalibrationPreviewReply(withPolicy);
    assert.match(reply, /read-only/);
    assert.match(reply, /!calibration apply/);

    const usage = await handleCalibrationCommand({ DB: null }, { text: "!calibration" }, "discord");
    assert.match(usage.reply_text, /!calibration preview/);
  });
});
