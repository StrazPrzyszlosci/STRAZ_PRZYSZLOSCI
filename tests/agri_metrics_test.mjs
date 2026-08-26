import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  computeAgriMetrics,
  formatAgriMetricsReply,
  groupAutopilotUsage,
  groupTelemetryMetrics,
  parseTelemetryMetricKey,
} from "../cloudflare/src/agri_metrics.js";

function createMockDb({ telemetryRows = [], usageRows = [] } = {}) {
  return {
    prepare(sql) {
      return {
        bind(...args) {
          return {
            async all() {
              if (sql.includes("FROM automation_metrics")) return { results: telemetryRows };
              if (sql.includes("FROM agri_autopilot_usage")) return { results: usageRows };
              return { results: [] };
            },
          };
        },
      };
    },
  };
}

describe("agri metrics dashboard T32", () => {
  it("parses telemetry metric keys and rejects foreign ones", () => {
    assert.deepEqual(parseTelemetryMetricKey("telemetry_ph_avg_2026-08-26"), {
      sensor: "ph",
      suffix: "avg",
      day_key: "2026-08-26",
    });
    assert.equal(parseTelemetryMetricKey("acceptance_rate_sprint"), null);
    assert.equal(parseTelemetryMetricKey("telemetry_"), null);
  });

  it("groups telemetry rows per sensor+day with avg/min/max", () => {
    const grouped = groupTelemetryMetrics([
      { metric_key: "telemetry_ph_avg_2026-08-26", metric_value: 6.1, measured_at: "2026-08-26T00:00:00.000Z" },
      { metric_key: "telemetry_ph_min_2026-08-26", metric_value: 5.7, measured_at: "2026-08-26T00:00:00.000Z" },
      { metric_key: "telemetry_ph_max_2026-08-26", metric_value: 6.5, measured_at: "2026-08-26T00:00:00.000Z" },
      { metric_key: "telemetry_air_temp_c_avg_2026-08-25", metric_value: 21.4, measured_at: "2026-08-25T00:00:00.000Z" },
      { metric_key: "acceptance_rate", metric_value: 0.9, measured_at: "2026-08-26T00:00:00.000Z" },
    ]);
    assert.equal(grouped.length, 2);
    const phToday = grouped.find((entry) => entry.sensor === "ph");
    assert.deepEqual(phToday, { sensor: "ph", day_key: "2026-08-26", avg: 6.1, min: 5.7, max: 6.5 });
    // Nowszy dzień pierwszy na liście.
    assert.equal(grouped[0].day_key >= grouped[1].day_key, true);
  });

  it("groups autopilot usage from policy|day keys", () => {
    const usage = groupAutopilotUsage([
      { usage_key: "grow_policy_aquaponics_greens_01|2026-08-26", used_count: 3, updated_at: "2026-08-26T12:00:00.000Z" },
      { usage_key: "malformed-key", used_count: 9, updated_at: "2026-08-26T12:00:00.000Z" },
      { usage_key: "grow_policy_microgreens_shelf_01|2026-08-25", used_count: 1, updated_at: "2026-08-25T12:00:00.000Z" },
    ]);
    assert.equal(usage.length, 2);
    assert.equal(usage[0].policy_id, "grow_policy_aquaponics_greens_01");
    assert.equal(usage[0].used_count, 3);
    // Legacy klucze nie mają instancji.
    assert.equal(usage[0].grow_cell_id, null);
  });

  it("parses per-instance usage keys with grow cell (T35)", () => {
    const usage = groupAutopilotUsage([
      { usage_key: "grow_policy_aquaponics_greens_01|grow-cell-A|2026-08-26", used_count: 6, updated_at: "2026-08-26T12:00:00.000Z" },
      { usage_key: "grow_policy_aquaponics_greens_01|grow-cell-B|2026-08-26", used_count: 1, updated_at: "2026-08-26T12:06:00.000Z" },
    ]);
    assert.equal(usage.length, 2);
    assert.deepEqual(usage.map((entry) => entry.grow_cell_id).sort(), ["grow-cell-A", "grow-cell-B"]);
    assert.ok(usage.every((entry) => entry.day_key === "2026-08-26"));
    const reply = formatAgriMetricsReply({ success: true, telemetry: [], autopilot_usage: usage });
    assert.match(reply, /użyto 6/);
  });

  it("computes full snapshot from DB or fails open on no_db", async () => {
    const db = createMockDb({
      telemetryRows: [
        { metric_key: "telemetry_ec_ms_cm_max_2026-08-26", metric_value: 1.4, measured_at: "2026-08-26T00:00:00.000Z" },
      ],
      usageRows: [
        { usage_key: "grow_policy_aquaponics_greens_01|2026-08-26", used_count: 2, updated_at: "2026-08-26T13:00:00.000Z" },
      ],
    });
    const snapshot = await computeAgriMetrics({ DB: db }, { now: "2026-08-26T14:00:00.000Z" });
    assert.equal(snapshot.success, true);
    assert.equal(snapshot.generated_at, "2026-08-26T14:00:00.000Z");
    assert.equal(snapshot.telemetry.length, 1);
    assert.equal(snapshot.telemetry[0].sensor, "ec_ms_cm");
    assert.equal(snapshot.autopilot_usage[0].used_count, 2);

    const noDb = await computeAgriMetrics({});
    assert.equal(noDb.reason, "no_db");
  });

  it("formats bot reply within platform limits (T34)", () => {
    // no_db i brak snapshota -> czytelne komunikaty zamiast rzucania.
    assert.match(formatAgriMetricsReply(null), /Brak danych/);
    assert.match(formatAgriMetricsReply({ reason: "no_db" }), /niedostępne/);

    const empty = formatAgriMetricsReply({ success: true, telemetry: [], autopilot_usage: [] });
    assert.match(empty, /brak agregatów/);
    assert.match(empty, /Brak użyć autopilota/);

    const full = formatAgriMetricsReply({
      success: true,
      generated_at: "2026-08-26T14:00:00.000Z",
      telemetry: [
        { sensor: "ph", day_key: "2026-08-26", avg: 6.1, min: 5.7, max: 6.5 },
        { sensor: "air_temp_c", day_key: "2026-08-25", avg: 21.4 },
      ],
      autopilot_usage: [
        { policy_id: "grow_policy_aquaponics_greens_01", day_key: "2026-08-26", used_count: 2 },
      ],
    });
    assert.match(full, /🌱 \*\*Metryki upraw\*\*/);
    assert.match(full, /ph @ 2026-08-26: avg=6\.1 \/ min=5\.7 \/ max=6\.5/);
    assert.match(full, /użyto 2/);
    assert.ok(full.length < 1800);
  });
});
