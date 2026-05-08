import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { checkGlobalRateLimit } from "../cloudflare/src/global_rate_limiter.js";

// Minimal in-memory DB mock for global rate limiter tests
function createMockDb() {
  const store = new Map();
  return {
    prepare() {
      return {
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
              store.set(key, { window_started_at: new Date(Date.now()).toISOString(), request_count: (store.get(key)?.request_count || 0) + 1 });
              return { changes: 1 };
            },
          };
        },
      };
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
});
