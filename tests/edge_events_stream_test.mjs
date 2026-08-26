import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  listEdgeEventsSince,
  parseEdgeStreamQuery,
  pruneEdgeEvents,
  publishEdgeEvent,
  resolveEdgeEventRetentionConfig,
  validateEdgeEventInput,
} from "../cloudflare/src/edge_events_stream.js";

function createMockDb() {
  const events = [];
  let nextId = 1;
  return {
    events,
    prepare(sql) {
      return {
        bind(...args) {
          return {
            async run() {
              if (sql.includes("INSERT INTO edge_event_stream")) {
                const [provider_id, kind, severity, payload_json, created_at] = args;
                const id = nextId++;
                events.push({ id, provider_id, kind, severity: severity || "info", payload_json, created_at });
                return { meta: { last_row_id: id } };
              }
              return { meta: {} };
            },
            async all() {
              if (sql.includes("FROM edge_event_stream")) {
                const [providerId, sinceId, limit] = args;
                const rows = events
                  .filter((event) => event.provider_id === providerId && event.id > sinceId)
                  .sort((a, b) => a.id - b.id)
                  .slice(0, limit);
                return { results: rows.map(({ payload_json, ...rest }) => ({ ...rest, payload_json })) };
              }
              return { results: [] };
            },
          };
        },
      };
    },
  };
}

describe("edge events stream T22", () => {
  it("validates event input contract", () => {
    assert.deepEqual(
      validateEdgeEventInput({ provider_id: "edge_01", kind: "recommendation", severity: "info" }),
      []
    );
    assert.ok(validateEdgeEventInput({ kind: "alarm" }).includes("provider_id"));
    assert.ok(validateEdgeEventInput({ provider_id: "x", kind: "spam" }).some((entry) => entry.startsWith("kind")));
    assert.ok(validateEdgeEventInput({ provider_id: "x", kind: "alarm", severity: "loud" }).some((entry) => entry.startsWith("severity")));
  });

  it("publishes events with monotonic cursor ids", async () => {
    const db = createMockDb();
    const first = await publishEdgeEvent(
      { DB: db },
      { provider_id: "edge_01", kind: "recommendation", payload: { pack: "pack-phone-aquaponics-observer-01" } },
      { now: "2026-08-26T10:00:00.000Z" }
    );
    const second = await publishEdgeEvent(
      { DB: db },
      { provider_id: "edge_01", kind: "alarm", severity: "critical", payload: { ph: 9.4 } },
      { now: "2026-08-26T10:05:00.000Z" }
    );
    assert.equal(first.success, true);
    assert.equal(second.success, true);
    assert.equal(second.event_id, first.event_id + 1);

    const invalid = await publishEdgeEvent({ DB: db }, { provider_id: "", kind: "alarm" });
    assert.equal(invalid.success, false);
  });

  it("returns events after cursor with next_cursor for polling", async () => {
    const db = createMockDb();
    for (const [kind, severity] of [["status", "info"], ["recommendation", "info"], ["alarm", "warning"]]) {
      await publishEdgeEvent({ DB: db }, { provider_id: "edge_01", kind, severity });
    }
    await publishEdgeEvent({ DB: db }, { provider_id: "edge_other", kind: "notice" });

    const page1 = await listEdgeEventsSince(db, "edge_01", 0, 2);
    assert.equal(page1.success, true);
    assert.equal(page1.events.length, 2);
    assert.equal(page1.has_more, true);
    assert.equal(page1.next_cursor, page1.events[1].id);

    const page2 = await listEdgeEventsSince(db, "edge_01", page1.next_cursor, 2);
    assert.equal(page2.events.length, 1);
    assert.equal(page2.events[0].kind, "alarm");
    assert.equal(page2.has_more, false);

    const empty = await listEdgeEventsSince(db, "edge_other", 0, 100);
    assert.equal(empty.events.length, 1);
    assert.equal(empty.events[0].kind, "notice");
  });

  it("parses and validates stream query parameters", () => {
    const ok = parseEdgeStreamQuery(new URL("https://x.invalid/v1/ws/events?provider_id=edge_01&since_id=5&limit=10"));
    assert.deepEqual(ok, { provider_id: "edge_01", since_id: 5, limit: 10 });

    assert.throws(() => parseEdgeStreamQuery(new URL("https://x.invalid/v1/ws/events")), /provider_id/);
    assert.throws(() => parseEdgeStreamQuery(new URL("https://x.invalid/v1/ws/events?provider_id=e&since_id=-3")), /since_id/);
    assert.throws(() => parseEdgeStreamQuery(new URL("https://x.invalid/v1/ws/events?provider_id=e&limit=9999")), /limit/);
  });

  it("prunes old events and enforces per-provider cap (T31)", async () => {
    const executed = [];
    const db = {
      prepare(sql) {
        return {
          bind(...args) {
            return {
              async run() {
                executed.push({ sql, args });
                return { meta: { changes: sql.includes("created_at <") ? 7 : 3 } };
              },
            };
          },
        };
      },
    };
    const result = await pruneEdgeEvents(db, { retentionDays: 21, maxPerProvider: 50, now: "2026-08-26T12:00:00.000Z" });
    assert.equal(result.success, true);
    assert.equal(result.pruned, 10);
    assert.equal(result.retention_days, 21);
    assert.equal(result.max_per_provider, 50);
    assert.equal(result.cutoff_iso, "2026-08-05T12:00:00.000Z");
    assert.equal(executed.length, 2);
    assert.match(executed[0].sql, /DELETE FROM edge_event_stream WHERE created_at </);
    assert.match(executed[1].sql, /ROW_NUMBER\(\) OVER \(PARTITION BY provider_id ORDER BY id DESC\)/);

    const fallback = await pruneEdgeEvents(null);
    assert.equal(fallback.reason, "no_db");

    const config = resolveEdgeEventRetentionConfig({
      EDGE_EVENT_STREAM_RETENTION_DAYS: "7",
      EDGE_EVENT_STREAM_MAX_PER_PROVIDER: "250",
    });
    assert.deepEqual(config, { retention_days: 7, max_per_provider: 250 });
    const defaults = resolveEdgeEventRetentionConfig({});
    assert.equal(defaults.retention_days >= 1 && defaults.max_per_provider >= 1, true);
  });
});
