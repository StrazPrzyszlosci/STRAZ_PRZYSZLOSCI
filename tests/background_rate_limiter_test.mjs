import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  backgroundLimitKey,
  checkBackgroundTaskAllowance,
  evaluateBackgroundAllowance,
  resolveBackgroundTaskConfig,
  shouldRunBackgroundTask,
} from "../cloudflare/src/background_rate_limiter.js";

// Minimalny mock D1 (wzorem global_rate_limiter_test.mjs).
function createMockDb() {
  const store = new Map();
  return {
    prepare() {
      return {
        bind(key) {
          return {
            async first() {
              return store.get(key) || null;
            },
          };
        },
        async run() {
          return { changes: 1 };
        },
      };
    },
    _seed(key, row) {
      store.set(key, row);
    },
  };
}

// Mock zapisujący (do weryfikacji inkrementacji).
function createRecordingDb() {
  const store = new Map();
  const writes = [];
  return {
    writes,
    prepare(sql) {
      const isSelect = /SELECT/i.test(sql);
      return {
        bind(...args) {
          return {
            async first() {
              if (isSelect) return store.get(args[0]) || null;
              return null;
            },
            async run() {
              writes.push(args);
              if (/INSERT/i.test(sql)) {
                store.set(args[0], { window_started_at: args[2], request_count: args[3] });
              }
              return { changes: 1 };
            },
          };
        },
        async run() {
          return { changes: 1 };
        },
      };
    },
  };
}

describe("background rate limiter (hardening)", () => {
  it("evaluates window budget purely", () => {
    const ok = evaluateBackgroundAllowance(2, 6, 3600000, 1000, 0);
    assert.equal(ok.allowed, true);
    const blocked = evaluateBackgroundAllowance(6, 6, 3600000, 3599000, 0);
    assert.equal(blocked.allowed, false);
    assert.equal(blocked.reason, "background_rate_limited");
    assert.equal(blocked.retry_after_seconds, 1);
  });

  it("gates by minimal interval without db", () => {
    assert.equal(shouldRunBackgroundTask(null, 60000).allowed, true);
    assert.equal(shouldRunBackgroundTask(0, 60000).reason, "never_run");
    assert.equal(shouldRunBackgroundTask(1000, 60000, 61001).allowed, true);
    assert.equal(shouldRunBackgroundTask(1000, 60000, 60000).allowed, false);
  });

  it("builds stable window keys per task", () => {
    const a = backgroundLimitKey("Kicad Import", 3600000, 3600000);
    const b = backgroundLimitKey("kicad_import", 3600000, 3600000);
    assert.equal(a, b);
    assert.match(a, /^bg:kicad_import:/);
    assert.notEqual(backgroundLimitKey("x", 0, 3600000), backgroundLimitKey("x", 3600000, 3600000));
  });

  it("resolves per-task config from env with defaults", () => {
    const cfg = resolveBackgroundTaskConfig({}, "prune");
    assert.equal(cfg.windowMs, 3600000);
    assert.equal(cfg.maxRuns, 6);
    const custom = resolveBackgroundTaskConfig({ BG_PRUNE_MAX_RUNS: "2", BG_PRUNE_WINDOW_MS: "60000" }, "prune");
    assert.equal(custom.maxRuns, 2);
    assert.equal(custom.windowMs, 60000);
  });

  it("allows and records run in db", async () => {
    const db = createRecordingDb();
    const res = await checkBackgroundTaskAllowance(db, "prune", { now: 3600000, windowMs: 3600000, maxRuns: 2 });
    assert.equal(res.allowed, true);
    assert.equal(res.run_number, 1);
    assert.equal(db.writes.length, 1);
  });

  it("blocks over-budget task without recording", async () => {
    const db = createMockDb();
    const key = backgroundLimitKey("prune", 3600000, 3600000);
    db._seed(key, { window_started_at: new Date(3600000).toISOString(), request_count: 2 });
    const res = await checkBackgroundTaskAllowance(db, "prune", { now: 3600100, windowMs: 3600000, maxRuns: 2 });
    assert.equal(res.allowed, false);
    assert.equal(res.reason, "background_rate_limited");
  });

  it("fails open without db and on db error", async () => {
    assert.equal((await checkBackgroundTaskAllowance(null, "x")).reason, "no_db");
    const broken = { prepare() { throw new Error("boom"); } };
    const res = await checkBackgroundTaskAllowance(broken, "x");
    assert.equal(res.allowed, true);
    assert.equal(res.reason, "db_error");
  });
});
