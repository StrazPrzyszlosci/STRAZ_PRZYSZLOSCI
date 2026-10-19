import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  ensureBackgroundLeaseSchema,
  releaseBackgroundLease,
  resolveBackgroundGuardConfig,
  tryAcquireBackgroundLease,
} from "../cloudflare/src/background_guard.js";

// Minimalny mock D1: prepare() -> {bind()->{first(),run()}}.
function mockDb({ rows = {}, failOn = null } = {}) {
  const store = { ...rows };
  const calls = [];
  return {
    calls,
    store,
    prepare(sql) {
      calls.push(sql);
      return {
        bind(...args) {
          return {
            async first() {
              if (failOn === "first") throw new Error("D1 down");
              const task = args[0];
              return store[task] ? { locked_at: store[task] } : null;
            },
            async run() {
              if (failOn === "run") throw new Error("D1 down");
              if (sql.startsWith("INSERT")) store[args[0]] = args[1];
              if (sql.startsWith("DELETE")) delete store[args[0]];
              return { success: true };
            },
          };
        },
        async run() {
          if (failOn === "run") throw new Error("D1 down");
          return { success: true };
        },
      };
    },
  };
}

describe("background guard (hardening)", () => {
  it("resolves config from env with safe defaults", () => {
    assert.deepEqual(resolveBackgroundGuardConfig({}), { ttlSec: 600, minIntervalSec: 300 });
    assert.deepEqual(resolveBackgroundGuardConfig({ BACKGROUND_LEASE_TTL_SEC: "60", BACKGROUND_MIN_INTERVAL_SEC: "30" }), {
      ttlSec: 60,
      minIntervalSec: 30,
    });
    assert.deepEqual(resolveBackgroundGuardConfig({ BACKGROUND_LEASE_TTL_SEC: "0" }), {
      ttlSec: 600,
      minIntervalSec: 300,
    });
  });

  it("acquires free lease and blocks second acquire inside window", async () => {
    const db = mockDb();
    const first = await tryAcquireBackgroundLease(db, "prune-events", { nowMs: 1_000_000 });
    assert.equal(first.acquired, true);
    assert.equal(first.reason, "ok");
    const second = await tryAcquireBackgroundLease(db, "prune-events", { nowMs: 1_000_000 + 60_000 });
    assert.equal(second.acquired, false);
    assert.equal(second.reason, "lease_active");
  });

  it("re-acquires after window expiry", async () => {
    const db = mockDb();
    await tryAcquireBackgroundLease(db, "curate", { nowMs: 0, ttlSec: 100, minIntervalSec: 100 });
    const later = await tryAcquireBackgroundLease(db, "curate", { nowMs: 200_000, ttlSec: 100, minIntervalSec: 100 });
    assert.equal(later.acquired, true);
  });

  it("fails open without db or on db error", async () => {
    assert.deepEqual(await tryAcquireBackgroundLease(null, "x"), { acquired: true, reason: "no_db" });
    const broken = mockDb({ failOn: "first" });
    const res = await tryAcquireBackgroundLease(broken, "x");
    assert.equal(res.acquired, true);
    assert.equal(res.reason, "db_error");
  });

  it("rejects empty task name and releases leases", async () => {
    const db = mockDb();
    assert.deepEqual(await tryAcquireBackgroundLease(db, ""), { acquired: false, reason: "task_required" });
    await tryAcquireBackgroundLease(db, "ingest", { nowMs: 0 });
    assert.equal((await tryAcquireBackgroundLease(db, "ingest", { nowMs: 1000 })).acquired, false);
    assert.deepEqual(await releaseBackgroundLease(db, "ingest"), { released: true });
    assert.equal((await tryAcquireBackgroundLease(db, "ingest", { nowMs: 2000 })).acquired, true);
  });

  it("creates lease schema idempotently", async () => {
    const db = mockDb();
    await ensureBackgroundLeaseSchema(db);
    assert.ok(db.calls.some((sql) => sql.includes("CREATE TABLE IF NOT EXISTS background_leases")));
  });
});
