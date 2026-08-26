import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  computeTelemetryDedupChecksum,
  ingestTelemetry,
  parseTelemetryJsonl,
  pruneSensorReadings,
  resolveSensorReadingRetentionConfig,
} from "../cloudflare/src/sensor_telemetry.js";

function createMockDb() {
  const readings = [];
  const events = [];
  const metrics = [];
  return {
    readings,
    events,
    metrics,
    prepare(sql) {
      return {
        bind(...args) {
          let boundArgs = args;
          return {
            first() {
              if (sql.includes("FROM sensor_readings_staging WHERE dedup_checksum")) {
                return readings.find((row) => row.dedup_checksum === boundArgs[0]) || null;
              }
              if (sql.includes("SELECT AVG(value)")) {
                const [providerId, sensor, dayStart, nextDay] = boundArgs;
                const scoped = readings.filter(
                  (row) => row.provider_id === providerId && row.sensor === sensor
                    && row.recorded_at >= dayStart && row.recorded_at < nextDay
                );
                if (!scoped.length) return { avg_value: null };
                const values = scoped.map((row) => row.value);
                return {
                  avg_value: values.reduce((a, b) => a + b, 0) / values.length,
                  min_value: Math.min(...values),
                  max_value: Math.max(...values),
                };
              }
              return null;
            },
            async run() {
              if (sql.includes("INSERT INTO sensor_readings_staging")) {
                const [provider_id, sensor, value, unit, source, recorded_at, , checksum] = boundArgs;
                readings.push({ provider_id, sensor, value, unit, source, recorded_at, dedup_checksum: checksum });
              } else if (sql.includes("INSERT INTO sensor_telemetry_events")) {
                const kind = sql.match(/VALUES\s*\('([a-z_]+)'/i)?.[1] || "unknown";
                events.push({ kind, inserted_count: boundArgs[2] });
              } else if (sql.includes("INSERT INTO automation_metrics")) {
                const [metric_key, metric_value] = boundArgs;
                metrics.push({ metric_key, metric_value });
              }
              return { meta: {} };
            },
            async all() {
              return { results: [] };
            },
          };
        },
      };
    },
  };
}

const validLine = {
  sensor: "ph",
  value: 6.1,
  recorded_at: "2026-08-26T09:30:00.000Z",
  unit: "pH",
  source: "edge_probe_01",
};

describe("sensor telemetry ingestion T29", () => {
  it("parses NDJSON contract and rejects violations", () => {
    const { rows, errors } = parseTelemetryJsonl(`${JSON.stringify(validLine)}\n\n${JSON.stringify({ ...validLine, sensor: "PH!" })}\n`);
    assert.equal(rows.length, 1);
    assert.equal(errors[0].error, "contract_missing:sensor_pattern_[a-z0-9_]");

    assert.ok(parseTelemetryJsonl(`${JSON.stringify({ ...validLine, value: "six" })}\n`).errors[0].error.includes("value_finite_number"));
    assert.ok(parseTelemetryJsonl(`${JSON.stringify({ ...validLine, recorded_at: "yesterday" })}\n`).errors[0].error.includes("recorded_at_iso_timestamp"));

    // provider_id w linii jest opcjonalny i ignorowany (nadpisuje go endpoint).
    const withProvider = parseTelemetryJsonl(`${JSON.stringify({ ...validLine, provider_id: "spoofed" })}\n`);
    assert.equal(withProvider.errors.length, 0);
  });

  it("computes stable dedup checksum sensitive to reading identity", async () => {
    const a = await computeTelemetryDedupChecksum({ provider_id: "cell-01", ...validLine });
    const b = await computeTelemetryDedupChecksum({ provider_id: "cell-01", ...validLine, source: "other" });
    const c = await computeTelemetryDedupChecksum({ provider_id: "cell-02", ...validLine });
    const d = await computeTelemetryDedupChecksum({ provider_id: "cell-01", ...validLine, value: 6.1000001 });
    assert.equal(a, b);
    assert.notEqual(a, c);
    assert.notEqual(a, d);
  });

  it("ingests staged rows with dedup, audit event and daily aggregates", async () => {
    const db = createMockDb();
    const env = { DB: db };
    const payload = `${JSON.stringify(validLine)}\n${JSON.stringify({ sensor: "air_temp_c", value: 22.5, recorded_at: "2026-08-26T09:31:00.000Z" })}\n`;

    const first = await ingestTelemetry(env, "phone-aquaponics-observer-01", payload, { now: "2026-08-26T10:00:00.000Z" });
    assert.equal(first.success, true);
    assert.equal(first.inserted, 2);
    assert.equal(first.staged_only, true);
    assert.deepEqual(first.aggregates.sensors, ["air_temp_c", "ph"]);

    const second = await ingestTelemetry(env, "phone-aquaponics-observer-01", payload, { now: "2026-08-26T10:05:00.000Z" });
    assert.equal(second.inserted, 0);
    assert.equal(second.skipped, 2);

    assert.equal(db.readings.length, 2);
    assert.deepEqual(db.events.map((event) => event.kind), ["telemetry_ingest", "telemetry_ingest"]);
    const keys = db.metrics.map((m) => m.metric_key).sort();
    assert.ok(keys.includes("telemetry_ph_avg_2026-08-26"));
    assert.ok(keys.includes("telemetry_air_temp_c_max_2026-08-26"));
    assert.equal(db.metrics.length, 6); // 2 sensory x avg/min/max
  });

  it("refuses whole batch on any invalid line or empty payload", async () => {
    const db = createMockDb();
    const bad = `${JSON.stringify(validLine)}\n{"sensor":"ph"}\n`;
    const result = await ingestTelemetry({ DB: db }, "cell-01", bad);
    assert.equal(result.reason, "invalid_payload");
    assert.equal(db.readings.length, 0);

    const empty = await ingestTelemetry({ DB: db }, "cell-01", "\n");
    assert.equal(empty.reason, "empty_payload");
    assert.deepEqual(db.events, []);
  });

  it("prunes stale raw readings while keeping daily aggregates (T31)", async () => {
    const executed = [];
    const db = {
      prepare(sql) {
        return {
          bind(...args) {
            return {
              async run() {
                executed.push({ sql, args });
                return { meta: { changes: 5 } };
              },
            };
          },
        };
      },
    };
    const result = await pruneSensorReadings(db, { retentionDays: 30, now: "2026-08-26T12:00:00.000Z" });
    assert.equal(result.success, true);
    assert.equal(result.pruned, 5);
    assert.equal(result.cutoff_iso, "2026-07-27T12:00:00.000Z");
    assert.match(executed[0].sql, /DELETE FROM sensor_readings_staging WHERE recorded_at </);

    const config = resolveSensorReadingRetentionConfig({ SENSOR_READINGS_RETENTION_DAYS: "45" });
    assert.deepEqual(config, { retention_days: 45 });

    const fallback = await pruneSensorReadings(null);
    assert.equal(fallback.reason, "no_db");
  });
});
