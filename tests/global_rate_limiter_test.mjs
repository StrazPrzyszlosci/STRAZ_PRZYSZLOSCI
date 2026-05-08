import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { checkGlobalRateLimit } from "../cloudflare/src/global_rate_limiter.js";

// Minimal in-memory DB mock for global rate limiter tests
function createMockDb(initialColumns = [
  "limit_key",
  "bucket_name",
  "window_started_at",
  "request_count",
  "last_request_at",
  "platform",
]) {
  const store = new Map();
  const columns = new Map([
    ["telegram_chat_limits", new Set(initialColumns)],
  ]);

  function getPragmaTable(sql) {
    const match = String(sql).match(/PRAGMA\s+table_info\(([^)]+)\)/i);
    return match ? match[1] : null;
  }

  return {
    _columns(tableName) {
      return Array.from(columns.get(tableName) || []);
    },
    prepare(sql) {
      const normalizedSql = String(sql).replace(/\s+/g, " ").trim();
      const statement = {
        async run() {
          const createMatch = normalizedSql.match(/CREATE TABLE IF NOT EXISTS\s+(\w+)/i);
          if (createMatch && !columns.has(createMatch[1])) {
            columns.set(createMatch[1], new Set(initialColumns));
          }
          const alterMatch = normalizedSql.match(/ALTER TABLE\s+(\w+)\s+ADD COLUMN\s+(\w+)/i);
          if (alterMatch) {
            if (!columns.has(alterMatch[1])) {
              columns.set(alterMatch[1], new Set());
            }
            columns.get(alterMatch[1]).add(alterMatch[2]);
          }
          return { changes: 1 };
        },
        async all() {
          const tableName = getPragmaTable(normalizedSql);
          if (tableName) {
            return {
              results: Array.from(columns.get(tableName) || []).map((name) => ({ name })),
            };
          }
          return { results: [] };
        },
        bind(...args) {
          return {
            async first() {
              const key = args[0];
              return store.get(key) || null;
            },
            async all() {
              return [];
            },
            async run() {
              const key = args[0];
              store.set(key, {
                window_started_at: args[2],
                request_count: args[3],
                last_request_at: args[4],
                platform: args[5],
              });
              return { changes: 1 };
            },
          };
        },
      };
      return statement;
    },
  };
}

function createMockRequest(headers = {}) {
  return {
    headers: {
      get(name) {
        return headers[name] || null;
      },
    },
  };
}

describe("Global API Rate Limit (Z85)", () => {
  it("allows first request (below all limits)", async () => {
    const env = { DB: createMockDb(), API_MAX_RPM_PER_IP: "60", API_MAX_RPM_PER_API_KEY: "120", API_MAX_RPM_PER_PROJECT: "600" };
    const result = await checkGlobalRateLimit(createMockRequest({ "CF-Connecting-IP": "1.2.3.4" }), env);
    assert.equal(result.allowed, true);
  });

  it("allows multiple requests below limit", async () => {
    const env = { DB: createMockDb(), API_MAX_RPM_PER_IP: "60", API_MAX_RPM_PER_API_KEY: "120", API_MAX_RPM_PER_PROJECT: "600" };
    for (let i = 0; i < 5; i++) {
      const result = await checkGlobalRateLimit(createMockRequest({ "CF-Connecting-IP": "1.2.3.4" }), env);
      assert.equal(result.allowed, true);
    }
  });

  it("blocks when per-IP limit exceeded", async () => {
    const env = { DB: createMockDb(), API_MAX_RPM_PER_IP: "3", API_MAX_RPM_PER_API_KEY: "120", API_MAX_RPM_PER_PROJECT: "600" };
    for (let i = 0; i < 3; i++) {
      const result = await checkGlobalRateLimit(createMockRequest({ "CF-Connecting-IP": "1.2.3.4" }), env);
      assert.equal(result.allowed, true);
    }
    const result = await checkGlobalRateLimit(createMockRequest({ "CF-Connecting-IP": "1.2.3.4" }), env);
    assert.equal(result.allowed, false);
    assert.equal(result.reason, "rate_limited_ip");
    assert.equal(result.retry_after_seconds, 60);
  });

  it("blocks when per-API-key limit exceeded", async () => {
    const env = { DB: createMockDb(), API_MAX_RPM_PER_IP: "60", API_MAX_RPM_PER_API_KEY: "2", API_MAX_RPM_PER_PROJECT: "600" };
    for (let i = 0; i < 2; i++) {
      const result = await checkGlobalRateLimit(createMockRequest({ "X-Provider-Token": "my-api-key", "CF-Connecting-IP": "1.2.3.4" }), env);
      assert.equal(result.allowed, true);
    }
    const result = await checkGlobalRateLimit(createMockRequest({ "X-Provider-Token": "my-api-key", "CF-Connecting-IP": "1.2.3.5" }), env);
    assert.equal(result.allowed, false);
    assert.equal(result.reason, "rate_limited_api_key");
  });

  it("fail-open when DB is missing", async () => {
    const env = { API_MAX_RPM_PER_IP: "60" };
    const result = await checkGlobalRateLimit(createMockRequest(), env);
    assert.equal(result.allowed, true);
    assert.equal(result.reason, "no_db");
  });

  it("fail-open when no CF-Connecting-IP", async () => {
    const env = { DB: createMockDb(), API_MAX_RPM_PER_IP: "60", API_MAX_RPM_PER_API_KEY: "120", API_MAX_RPM_PER_PROJECT: "600" };
    const result = await checkGlobalRateLimit(createMockRequest({}), env);
    assert.equal(result.allowed, true);
  });

  it("self-heals legacy telegram_chat_limits schema without platform column", async () => {
    const db = createMockDb([
      "limit_key",
      "bucket_name",
      "window_started_at",
      "request_count",
      "last_request_at",
    ]);
    const env = { DB: db, API_MAX_RPM_PER_IP: "60", API_MAX_RPM_PER_API_KEY: "120", API_MAX_RPM_PER_PROJECT: "600" };
    const result = await checkGlobalRateLimit(createMockRequest({ "CF-Connecting-IP": "1.2.3.4" }), env);

    assert.equal(result.allowed, true);
    assert.ok(db._columns("telegram_chat_limits").includes("platform"));
  });

  it("fail-open when D1 throws before rate limit state can be read", async () => {
    const env = {
      DB: {
        prepare() {
          throw new Error("D1 unavailable");
        },
      },
      API_MAX_RPM_PER_IP: "1",
    };
    const result = await checkGlobalRateLimit(createMockRequest({ "CF-Connecting-IP": "1.2.3.4" }), env);

    assert.equal(result.allowed, true);
    assert.equal(result.reason, "db_error");
  });
});
