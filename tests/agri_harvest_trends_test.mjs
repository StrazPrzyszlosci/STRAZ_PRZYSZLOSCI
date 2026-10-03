import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  buildMonthlySeries,
  computeCropTrends,
  computeHarvestTrends,
  cutSeriesToWindow,
  linearRegression,
  normalizeMonthsBack,
  trendDirection,
} from "../cloudflare/src/agri_harvest_trends.js";

function closeTo(actual, expected, eps = 1e-9) {
  assert.ok(
    Math.abs(actual - expected) <= eps,
    `expected ${actual} to be close to ${expected}`
  );
}

function harvestRow(crop, month, day, mass) {
  return {
    crop_profile: crop,
    harvested_at: `${month}-${String(day).padStart(2, "0")}T09:00:00.000Z`,
    mass_g: mass,
  };
}

function createMockDb(rows) {
  return {
    prepare(sql) {
      assert.ok(sql.includes("FROM harvest_records"), "trends read only from harvest_records");
      return {
        bind(cellId) {
          return {
            async all() {
              return { results: rows.filter((r) => r.grow_cell_id === cellId) };
            },
          };
        },
      };
    },
  };
}

describe("harvest trends T41", () => {
  it("fits least-squares line through monthly totals", () => {
    const fit = linearRegression([
      { x: 0, y: 10 },
      { x: 1, y: 12 },
      { x: 2, y: 14 },
    ]);
    closeTo(fit.slope, 2);
    closeTo(fit.intercept, 10);
    assert.equal(fit.n, 3);

    const flat = linearRegression([
      { x: 0, y: 100 },
      { x: 1, y: 100 },
      { x: 2, y: 100 },
    ]);
    closeTo(flat.slope, 0);
    closeTo(flat.intercept, 100);

    assert.equal(linearRegression([{ x: 0, y: 5 }]), null);
    assert.equal(linearRegression([]), null);
    // Zerowa wariancja x (ten sam miesiąc) -> nachylenie nieokreślone.
    assert.equal(
      linearRegression([
        { x: 1, y: 5 },
        { x: 1, y: 7 },
      ]),
      null
    );
  });

  it("classifies trend direction with flat-band tolerance", () => {
    assert.equal(trendDirection(8, 100), "rising");
    assert.equal(trendDirection(-8, 100), "falling");
    assert.equal(trendDirection(2, 100), "stable");
    assert.equal(trendDirection(0, 100), "stable");
    assert.equal(trendDirection(NaN, 100), "unknown");
  });

  it("groups harvest rows into monthly series per crop", () => {
    const series = buildMonthlySeries([
      harvestRow("leafy greens", "2026-06", 10, 100),
      harvestRow("leafy greens", "2026-06", 20, 50),
      harvestRow("leafy greens", "2026-07", 5, 200),
      harvestRow("micro basil", "2026-07", 5, 30),
      // Brudne wiersze pomijane (fail-open).
      { crop_profile: "", harvested_at: "2026-07-01T00:00:00.000Z", mass_g: 10 },
      { crop_profile: "leafy greens", harvested_at: "not-a-date", mass_g: 10 },
      { crop_profile: "leafy greens", harvested_at: "2026-07-02T00:00:00.000Z", mass_g: -4 },
    ]);
    assert.deepEqual(series["leafy greens"], [
      { month: "2026-06", mass_g: 150 },
      { month: "2026-07", mass_g: 200 },
    ]);
    assert.deepEqual(series["micro basil"], [{ month: "2026-07", mass_g: 30 }]);
  });

  it("cuts series to last N months relative to newest data month", () => {
    const series = {
      greens: [
        { month: "2026-05", mass_g: 10 },
        { month: "2026-06", mass_g: 20 },
        { month: "2026-07", mass_g: 30 },
        { month: "2026-08", mass_g: 40 },
      ],
    };
    const cut = cutSeriesToWindow(series, 2);
    assert.equal(cut.maxMonth, "2026-08");
    assert.equal(cut.cutoffMonth, "2026-07");
    assert.deepEqual(
      cut.series.greens.map((p) => p.month),
      ["2026-07", "2026-08"]
    );
    // Przełom roku.
    const yearCut = cutSeriesToWindow({ g: [{ month: "2026-01", mass_g: 5 }] }, 3);
    assert.equal(yearCut.cutoffMonth, "2025-11");

    assert.equal(normalizeMonthsBack(undefined), 12);
    assert.equal(normalizeMonthsBack("abc"), 12);
    assert.equal(normalizeMonthsBack(0), 12);
    assert.equal(normalizeMonthsBack(200), 60);
    assert.equal(normalizeMonthsBack(3.7), 3);
  });

  it("computes per-crop trends from ledger rows via mock DB", async () => {
    const cell = "phone-aquaponics-observer-01";
    const rows = [
      { grow_cell_id: cell, ...harvestRow("greens", "2026-06", 10, 100) },
      { grow_cell_id: cell, ...harvestRow("greens", "2026-07", 10, 150) },
      { grow_cell_id: cell, ...harvestRow("greens", "2026-08", 10, 200) },
      { grow_cell_id: cell, ...harvestRow("herbs", "2026-06", 10, 300) },
      { grow_cell_id: cell, ...harvestRow("herbs", "2026-07", 10, 200) },
      { grow_cell_id: cell, ...harvestRow("herbs", "2026-08", 10, 100) },
      // Obca komórka nie wycieka do wyniku.
      { grow_cell_id: "other-cell", ...harvestRow("greens", "2026-08", 10, 9999) },
    ];
    const result = await computeHarvestTrends({ DB: createMockDb(rows) }, cell, { monthsBack: 12 });
    assert.equal(result.success, true);
    assert.equal(result.grow_cell_id, cell);
    assert.equal(result.crop_count, 2);
    assert.equal(result.latest_month, "2026-08");
    assert.ok(result.note.includes("nie gwarantuje"));

    assert.equal(result.trends.greens.direction, "rising");
    closeTo(result.trends.greens.slope_g_per_month, 50);
    assert.equal(result.trends.greens.total_g, 450);
    assert.equal(result.trends.herbs.direction, "falling");
    closeTo(result.trends.herbs.slope_g_per_month, -100);

    // Jeden miesiąc -> regresja niemożliwa, kierunek unknown.
    const single = await computeHarvestTrends(
      { DB: createMockDb([{ grow_cell_id: cell, ...harvestRow("greens", "2026-08", 10, 100) }]) },
      cell,
      {}
    );
    assert.equal(single.trends.greens.slope_g_per_month, null);
    assert.equal(single.trends.greens.direction, "unknown");
  });

  it("handles empty ledger and missing DB without writes", async () => {
    const empty = await computeHarvestTrends({ DB: createMockDb([]) }, "cell-01", { monthsBack: 6 });
    assert.equal(empty.success, true);
    assert.equal(empty.crop_count, 0);
    assert.deepEqual(empty.series, {});
    assert.ok(empty.note.includes("POST /v1/agri/harvest"));

    assert.equal((await computeHarvestTrends({}, "cell-01", {})).reason, "no_db");
    assert.equal(
      (await computeHarvestTrends({ DB: createMockDb([]) }, "  ", {})).reason,
      "provider_id_required"
    );
  });

  it("derives crop trends helper for direct series input", () => {
    const trends = computeCropTrends({
      greens: [
        { month: "2026-06", mass_g: 100 },
        { month: "2026-07", mass_g: 100 },
      ],
    });
    assert.equal(trends.greens.months, 2);
    assert.equal(trends.greens.direction, "stable");
    closeTo(trends.greens.slope_g_per_month, 0);
  });
});
