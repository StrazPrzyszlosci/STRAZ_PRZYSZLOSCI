import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  checkProviderRateLimit,
  ensureProviderRateLimitSchema,
} from "../cloudflare/src/provider_rate_limiter.js";

/**
 * Mock D1 dla provider_rate_limiter: pojedyncza tabela telegram_chat_limits
 * Zahacza o CREATE TABLE IF NOT EXISTS, ensureColumn ALTER i upsert.
 */
function createDb() {
  const store = new Map();
  let columnsAdded = false;
  const tableColumns = new Set([
    "limit_key",
    "bucket_name",
    "window_started_at",
    "request_count",
    "last_request_at",
    "platform",
  ]);
  return {
    _store: store,
    _tableColumns: tableColumns,
    prepare(sql) {
      return {
        bind(...args) {
          return {
            async first() {
              if (sql.includes("FROM telegram_chat_limits WHERE limit_key = ?")) {
                return store.get(args[0]) || null;
              }
              if (sql.includes("PRAGMA table_info(telegram_chat_limits)")) {
                return { results: Array.from(tableColumns).map((name) => ({ name })) };
              }
              return null;
            },
            async all() {
              if (sql.includes("PRAGMA table_info(telegram_chat_limits)")) {
                return { results: Array.from(tableColumns).map((name) => ({ name })) };
              }
              return { results: [] };
            },
            async run() {
              if (sql.includes("CREATE TABLE IF NOT EXISTS telegram_chat_limits")) {
                return { success: true };
              }
              if (sql.startsWith("ALTER TABLE telegram_chat_limits ADD COLUMN")) {
                const match = sql.match(/ADD COLUMN (\w+)/);
                if (match) tableColumns.add(match[1]);
                return { success: true };
              }
              if (sql.includes("INSERT INTO telegram_chat_limits")) {
                const key = args[0];
                store.set(key, {
                  limit_key: args[0],
                  bucket_name: args[1],
                  window_started_at: args[2],
                  request_count: args[3],
                  last_request_at: args[4],
                  platform: args[5],
                });
                return { success: true };
              }
              return { success: true };
            },
          };
        },
        async run() {
          if (sql.includes("CREATE TABLE IF NOT EXISTS telegram_chat_limits")) {
            return { success: true };
          }
          if (sql.startsWith("ALTER TABLE telegram_chat_limits ADD COLUMN")) {
            const match = sql.match(/ADD COLUMN (\w+)/);
            if (match) tableColumns.add(match[1]);
            return { success: true };
          }
          return { success: true };
        },
        async all() {
          if (sql.includes("PRAGMA table_info(telegram_chat_limits)")) {
            return { results: Array.from(tableColumns).map((name) => ({ name })) };
          }
          return { results: [] };
        },
      };
    },
  };
}

describe("Provider rate limiter (S2-A)", () => {
  it("returns allowed when DB is missing (fail-open)", async () => {
    const env = { DB: null, PROVIDER_MAX_RPM: 30 };
    const result = await checkProviderRateLimit(env, "pond-edge-01");
    assert.equal(result.allowed, true);
    assert.equal(result.reason, "no_db");
  });

  it("returns allowed when provider_id is missing", async () => {
    const env = { DB: createDb(), PROVIDER_MAX_RPM: 30 };
    const result = await checkProviderRateLimit(env, "");
    assert.equal(result.allowed, true);
    assert.equal(result.reason, "no_provider_id");
  });

  it("returns allowed when PROVIDER_MAX_RPM <= 0 (disabled)", async () => {
    const env = { DB: createDb(), PROVIDER_MAX_RPM: 0 };
    const result = await checkProviderRateLimit(env, "pond-edge-01");
    assert.equal(result.allowed, true);
    assert.equal(result.reason, "disabled");
  });

  it("allows first request under limit", async () => {
    const db = createDb();
    const env = { DB: db, PROVIDER_MAX_RPM: 3 };
    const r1 = await checkProviderRateLimit(env, "pond-edge-01");
    assert.equal(r1.allowed, true);
    assert.equal(r1.current, 1);
    assert.equal(r1.limit, 3);
  });

  it("blocks request exceeding PROVIDER_MAX_RPM in same window", async () => {
    const db = createDb();
    const env = { DB: db, PROVIDER_MAX_RPM: 2 };
    const r1 = await checkProviderRateLimit(env, "pond-edge-01");
    assert.equal(r1.allowed, true);
    const r2 = await checkProviderRateLimit(env, "pond-edge-01");
    assert.equal(r2.allowed, true);
    const r3 = await checkProviderRateLimit(env, "pond-edge-01");
    assert.equal(r3.allowed, false);
    assert.equal(r3.reason, "rate_limited_provider");
    assert.equal(r3.limit, 2);
    assert.equal(r3.current, 2);
    assert.ok(r3.retry_after_seconds >= 1);
  });

  it("buckets are independent per provider_id", async () => {
    const db = createDb();
    const env = { DB: db, PROVIDER_MAX_RPM: 1 };
    const a = await checkProviderRateLimit(env, "pond-A");
    const b = await checkProviderRateLimit(env, "pond-B");
    assert.equal(a.allowed, true);
    assert.equal(b.allowed, true);
    const a2 = await checkProviderRateLimit(env, "pond-A");
    assert.equal(a2.allowed, false);
    const b2 = await checkProviderRateLimit(env, "pond-B");
    assert.equal(b2.allowed, false);
  });

  it("ensureProviderRateLimitSchema creates table and columns idempotently", async () => {
    const db = createDb();
    await ensureProviderRateLimitSchema(db);
    await ensureProviderRateLimitSchema(db);
    for (const col of ["limit_key", "bucket_name", "window_started_at", "request_count", "last_request_at", "platform"]) {
      assert.ok(db._tableColumns.has(col), `missing column ${col}`);
    }
  });

  it("default fallback when PROVIDER_MAX_RPM unset", async () => {
    const env = { DB: createDb() };
    const r = await checkProviderRateLimit(env, "pond-edge-01");
    assert.equal(r.allowed, true);
    assert.equal(r.current, 1);
    assert.equal(r.limit, 30);
  });
});
