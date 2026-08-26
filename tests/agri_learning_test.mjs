import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  alignMonthlySeries,
  computeGrowCorrelation,
  pearsonR,
} from "../cloudflare/src/agri_correlation.js";
import {
  buildCalibrationPrBody,
  suggestBandAdjustments,
} from "../cloudflare/src/agri_calibration.js";

const policy = {
  id: "grow_policy_aquaponics_greens_01",
  grow_cell_id: "phone-aquaponics-observer-01",
  bands: {
    ph: { safe_min: 5.9, safe_max: 6.5, alarm_below: 5.5, alarm_above: 7.0 },
    water_temp_c: { safe_min: 18.0, safe_max: 24.0, alarm_below: 15.0, alarm_above: 28.0 },
    light_ppfd: { safe_min: 150.0, safe_max: 400.0, alarm_below: 80.0, alarm_above: 600.0 },
  },
};

describe("grow correlation T37", () => {
  it("computes pearson r with zero-variance guard", () => {
    assert.equal(pearsonR([1, 2, 3], [2, 4, 6]), 1);
    assert.equal(pearsonR([1, 2, 3], [6, 4, 2]), -1);
    assert.equal(pearsonR([1, 1, 1], [1, 2, 3]), null);
    assert.equal(pearsonR([1], [1]), null);
    assert.equal(pearsonR([], []), null);
  });

  it("aligns monthly sensor means with harvest mass and correlates", () => {
    const telemetryRows = [
      { sensor: "ph", month_key: "2026-06", mean_value: 6.0 },
      { sensor: "ph", month_key: "2026-07", mean_value: 6.2 },
      { sensor: "ph", month_key: "2026-08", mean_value: 6.4 },
      { sensor: "ph", month_key: "2026-05", mean_value: 9.9 }, // brak plonu -> ignorowany
      { sensor: "water_temp_c", month_key: "2026-06", mean_value: 21 },
      { sensor: "water_temp_c", month_key: "2026-07", mean_value: 21 },
      { sensor: "water_temp_c", month_key: "2026-08", mean_value: 21 }, // stała -> r=null
    ];
    const harvestRows = [
      { month_key: "2026-06", total_mass: 100 },
      { month_key: "2026-07", total_mass: 200 },
      { month_key: "2026-08", total_mass: 300 },
    ];
    const aligned = alignMonthlySeries(telemetryRows, harvestRows);
    assert.deepEqual(aligned.months, ["2026-06", "2026-07", "2026-08"]);
    const ph = aligned.sensors.find((s) => s.sensor === "ph");
    assert.equal(ph.pearson_r, 1);
    const temp = aligned.sensors.find((s) => s.sensor === "water_temp_c");
    assert.equal(temp.pearson_r, null);
  });

  it("queries staging + harvest per cell or fails without db/cell", async () => {
    const executed = [];
    const db = {
      prepare(sql) {
        return {
          bind(...args) {
            return {
              async all() {
                executed.push({ sql, args });
                if (sql.includes("FROM sensor_readings_staging")) {
                  return { results: [{ sensor: "ph", month_key: "2026-07", mean_value: 6.1 }] };
                }
                return { results: [{ month_key: "2026-07", total_mass: 250 }] };
              },
            };
          },
        };
      },
    };
    const result = await computeGrowCorrelation({ DB: db }, "phone-aquaponics-observer-01", {
      now: "2026-08-26T12:00:00.000Z",
      monthsBack: 3,
    });
    assert.equal(result.success, true);
    assert.equal(executed.length, 2);
    assert.match(executed[0].sql, /FROM sensor_readings_staging/);
    assert.match(executed[1].sql, /FROM harvest_records/);
    assert.equal(result.mass_by_month["2026-07"], 250);
    assert.ok(result.note.includes("przyczynowość"));

    assert.equal((await computeGrowCorrelation({}, "x")).reason, "no_db");
    assert.equal((await computeGrowCorrelation({ DB: db }, "")).reason, "provider_id_required");
  });
});

describe("calibration suggestions T38", () => {
  const correlation = (overrides = []) => ({
    sensors: [
      { sensor: "ph", pearson_r: 0.85, months_with_data: 4, monthly_means: {} },
      { sensor: "water_temp_c", pearson_r: -0.8, months_with_data: 4, monthly_means: {} },
      { sensor: "light_ppfd", pearson_r: 0.2, months_with_data: 4, monthly_means: {} },
      ...overrides,
    ],
  });

  it("suggests direction-aware band adjustments only above thresholds", () => {
    const result = suggestBandAdjustments(policy, correlation(), {});
    assert.equal(result.suggest_only, true);
    assert.equal(result.auto_applied, false);

    const bySensor = new Map(result.suggestions.map((s) => [s.sensor, s]));
    // ph: r>0 -> górne krawędzie w górę o 5% szerokości pasma (0.6*0.05=0.03).
    const ph = bySensor.get("ph");
    assert.equal(ph.direction, "raise_upper_edges");
    assert.equal(ph.proposed_band.safe_max, 6.53);
    assert.equal(ph.proposed_band.alarm_above, 7.03);
    assert.equal(ph.proposed_band.safe_min, 5.9);

    // water_temp_c: r<0 -> dolne krawędzie w dół o 5% szerokości (6*0.05=0.3).
    const temp = bySensor.get("water_temp_c");
    assert.equal(temp.direction, "lower_lower_edges");
    assert.equal(temp.proposed_band.safe_min, 17.7);
    assert.equal(temp.proposed_band.alarm_below, 14.7);

    // light_ppfd: |r| poniżej progu -> pominięty z powodem.
    assert.ok(result.skipped.some((entry) => entry.sensor === "light_ppfd" && entry.reason.startsWith("abs_r_below_threshold")));
  });

  it("skips sensors with too few months or no data", () => {
    const result = suggestBandAdjustments(
      policy,
      { sensors: [
        { sensor: "ph", pearson_r: 0.9, months_with_data: 2 },
        { sensor: "light_ppfd", pearson_r: null, months_with_data: 4 },
      ] },
      {}
    );
    assert.ok(result.skipped.some((entry) => entry.reason === "insufficient_months:2/3"));
    assert.ok(result.skipped.some((entry) => entry.reason === "correlation_undefined"));
    assert.equal(result.suggestions.length, 0);
  });

  it("builds PR body with safety gates and never auto-applies", () => {
    const result = suggestBandAdjustments(policy, correlation(), {});
    const body = buildCalibrationPrBody(policy, result);
    assert.match(body, /suggest-only/);
    assert.match(body, /NIE została zapisana w D1/);
    assert.match(body, /autopilot nie zmienia własnych progów/);
    assert.match(body, /safe_max: 6\.5 -> 6\.53/);
    assert.ok(!body.includes("aplikowano") && !body.includes("applied"));
  });
});
