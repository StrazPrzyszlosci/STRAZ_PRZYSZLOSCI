import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  autoDeactivateInactiveProviders,
  isProviderActive,
} from "../cloudflare/src/worker.js";

function createLifecycleDb(rows = []) {
  const providers = rows.map((row) => ({ ...row }));
  const events = [];
  const columns = new Set([
    "provider_id",
    "last_seen_at",
    "provider_status",
    "trust_level",
  ]);
  return {
    _providers: providers,
    _events: events,
    _columns: columns,
    prepare(sql) {
      return {
        bind(...args) {
          return {
            async all() {
              if (sql.includes("PRAGMA table_info(providers)")) {
                return { results: Array.from(columns).map((name) => ({ name })) };
              }
              if (sql.includes("FROM providers") && sql.includes("last_seen_at < ?")) {
                const cutoff = args[0];
                return {
                  results: providers.filter(
                    (row) => row.last_seen_at < cutoff && (row.provider_status || "active") !== "inactive"
                  ),
                };
              }
              return { results: [] };
            },
            async run() {
              if (sql.includes("UPDATE providers") && sql.includes("provider_status = 'inactive'")) {
                const cutoff = args[0];
                let changes = 0;
                for (const row of providers) {
                  if (row.last_seen_at < cutoff && (row.provider_status || "active") !== "inactive") {
                    row.provider_status = "inactive";
                    changes++;
                  }
                }
                return { changes };
              }
              if (sql.includes("INSERT INTO provider_lifecycle_events")) {
                events.push({
                  provider_id: args[0],
                  previous_status: args[1],
                  next_status: args[2],
                  reason: args[3],
                  created_at: args[4],
                });
                return { changes: 1 };
              }
              return { changes: 0 };
            },
          };
        },
        async all() {
          if (sql.includes("PRAGMA table_info(providers)")) {
            return { results: Array.from(columns).map((name) => ({ name })) };
          }
          return { results: [] };
        },
        async run() {
          if (sql.includes("ALTER TABLE providers ADD COLUMN")) {
            const match = sql.match(/ADD COLUMN (\w+)/);
            if (match) columns.add(match[1]);
          }
          return { changes: 0 };
        },
      };
    },
  };
}

describe("Provider lifecycle auto-deactivate (T6)", () => {
  it("deactivates active providers older than 72h and writes lifecycle events", async () => {
    const db = createLifecycleDb([
      { provider_id: "community-demo-old-01", last_seen_at: "2026-07-02T11:59:59.000Z", provider_status: "active" },
      { provider_id: "community-demo-fresh-01", last_seen_at: "2026-07-05T12:00:00.000Z", provider_status: "active" },
      { provider_id: "community-demo-inactive-01", last_seen_at: "2026-07-01T12:00:00.000Z", provider_status: "inactive" },
    ]);

    const result = await autoDeactivateInactiveProviders(
      { DB: db },
      { now: new Date("2026-07-06T12:00:00.000Z"), inactiveHours: 72 }
    );

    assert.equal(result.success, true);
    assert.equal(result.deactivated_count, 1);
    assert.equal(db._providers[0].provider_status, "inactive");
    assert.equal(db._providers[1].provider_status, "active");
    assert.equal(db._events.length, 1);
    assert.equal(db._events[0].provider_id, "community-demo-old-01");
    assert.equal(db._events[0].next_status, "inactive");
    assert.match(db._events[0].reason, /auto_deactivate_no_heartbeat_72h/);
  });

  it("fail-opens when DB is missing", async () => {
    const result = await autoDeactivateInactiveProviders({ DB: null });
    assert.equal(result.success, true);
    assert.equal(result.reason, "no_db");
    assert.equal(result.deactivated_count, 0);
  });

  it("fail-opens when D1 throws", async () => {
    const db = {
      prepare() {
        throw new Error("d1 unavailable");
      },
    };
    const result = await autoDeactivateInactiveProviders({ DB: db });
    assert.equal(result.success, true);
    assert.equal(result.reason, "failed_open");
    assert.equal(result.deactivated_count, 0);
  });

  it("treats missing provider_status as active and inactive as blocked for ingest gates", () => {
    assert.equal(isProviderActive({ provider_status: undefined }), true);
    assert.equal(isProviderActive({ provider_status: "active" }), true);
    assert.equal(isProviderActive({ provider_status: "inactive" }), false);
  });
});
