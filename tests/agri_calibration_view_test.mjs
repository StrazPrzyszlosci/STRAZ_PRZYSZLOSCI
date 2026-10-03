import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  buildCalibrationReview,
  buildCalibrationView,
  formatBandDiffLine,
  formatDelta,
  renderCalibrationDiffMarkdown,
  renderCalibrationDiffText,
} from "../cloudflare/src/agri_calibration_view.js";
import { suggestBandAdjustments } from "../cloudflare/src/agri_calibration.js";

const policy = {
  id: "grow_policy_aquaponics_greens_01",
  grow_cell_id: "phone-aquaponics-observer-01",
  bands: {
    ph: { safe_min: 5.9, safe_max: 6.5, alarm_below: 5.5, alarm_above: 7.0 },
    water_temp_c: { safe_min: 18.0, safe_max: 24.0, alarm_below: 15.0, alarm_above: 28.0 },
  },
};

const correlation = {
  sensors: [
    { sensor: "ph", pearson_r: 0.85, months_with_data: 4, monthly_means: {} },
    { sensor: "water_temp_c", pearson_r: -0.8, months_with_data: 4, monthly_means: {} },
  ],
};

describe("calibration view T40", () => {
  it("formats signed deltas", () => {
    assert.equal(formatDelta(6.5, 6.53), "+0.03");
    assert.equal(formatDelta(18.0, 17.7), "-0.3");
    assert.equal(formatDelta(5.9, 5.9), "±0");
    assert.equal(formatDelta("x", 1), "n/d");
  });

  it("renders one-line diff per sensor with old->new spans", () => {
    const result = suggestBandAdjustments(policy, correlation, {});
    const bySensor = new Map(result.suggestions.map((s) => [s.sensor, s]));
    const line = formatBandDiffLine(bySensor.get("ph"));
    assert.match(line, /ph/);
    assert.match(line, /5\.9–6\.5 → 5\.9–6\.53/);
    assert.match(line, /Δmax \+0\.03/);
    assert.match(line, /górne w górę/);
  });

  it("renders text review with safety gates and hard cut <1800", () => {
    const result = suggestBandAdjustments(policy, correlation, {});
    const text = renderCalibrationDiffText(result);
    assert.match(text, /suggest-only/);
    assert.match(text, /NIC nie zapisano/);
    assert.match(text, /korelacja != przyczynowość/);
    assert.match(text, /merge PR tylko przez człowieka/);
    assert.ok(text.length < 1800);
    assert.ok(!text.includes("aplikowano") && !text.includes("applied"));
  });

  it("handles empty suggestions without crashing", () => {
    const empty = { policy_id: "p", grow_cell_id: "c", suggestions: [], skipped: [] };
    const text = renderCalibrationDiffText(empty);
    assert.match(text, /Brak sugestii/);
    const md = renderCalibrationDiffMarkdown(empty);
    assert.match(md, /brak sugestii/);
  });

  it("renders markdown table for PR body", () => {
    const result = suggestBandAdjustments(policy, correlation, {});
    const md = renderCalibrationDiffMarkdown(result);
    assert.match(md, /\| sensor \| kierunek \| r \|/);
    assert.match(md, /`ph`.*6\.5 → 6\.53/);
    assert.match(md, /korelacja ≠ przyczynowość/);
  });

  it("builds review bundle as suggest-only bundle", () => {
    const result = suggestBandAdjustments(policy, correlation, {});
    const review = buildCalibrationReview(result);
    assert.equal(review.suggest_only, true);
    assert.equal(review.auto_applied, false);
    assert.ok(review.review_text.length > 0);
    assert.ok(review.review_markdown.length > 0);
  });

  it("exposes worker-compatible buildCalibrationView(policy, suggestion)", () => {
    const result = suggestBandAdjustments(policy, correlation, {});
    const view = buildCalibrationView(policy, result);
    assert.equal(view.suggest_only, true);
    assert.equal(view.auto_applied, false);
    assert.equal(view.policy_id, policy.id);
    assert.equal(view.grow_cell_id, policy.grow_cell_id);
    assert.ok(view.review_text.includes("ph"));
    assert.ok(view.review_markdown.includes("| sensor |"));
  });
});
