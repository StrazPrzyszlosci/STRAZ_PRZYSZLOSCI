import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { jsonResponse, getCorsAllowOrigin } from "../cloudflare/src/security_headers.js";

describe("Security Headers Regression Tests (Z84/Z81/Z82)", () => {
  // Helper
  async function assertSecurityHeaders(response, expectedCors) {
    const headers = response.headers;
    assert.equal(headers.get("content-type"), "application/json; charset=utf-8");
    assert.equal(headers.get("strict-transport-security"), "max-age=31536000; includeSubDomains");
    assert.equal(headers.get("x-content-type-options"), "nosniff");
    assert.equal(headers.get("x-frame-options"), "DENY");
    assert.equal(headers.get("referrer-policy"), "strict-origin-when-cross-origin");
    assert.equal(headers.get("content-security-policy"), "default-src 'none'; frame-ancestors 'none'");
    assert.equal(headers.get("permissions-policy"), "geolocation=(), camera=(), microphone=(), accelerometer=(), magnetometer=(), gyroscope=(), payment=(), usb=()");
    assert.equal(headers.get("access-control-allow-origin"), expectedCors || "*");
    assert.equal(headers.get("access-control-allow-methods"), "GET,POST,OPTIONS");
    assert.ok(headers.get("access-control-allow-headers"));
  }

  it("jsonResponse default (no env, no request) → all security headers present", async () => {
    const resp = jsonResponse({ status: "ok" }, 200);
    await assertSecurityHeaders(resp, "*");
  });

  it("jsonResponse with env (CORS wildcard) → all security headers present", async () => {
    const env = { CORS_ALLOWED_ORIGINS: "*" };
    const resp = jsonResponse({ status: "ok" }, 200, env);
    await assertSecurityHeaders(resp, "*");
  });

  it("getCorsAllowOrigin with matching Origin → returns matched origin", () => {
    const env = { CORS_ALLOWED_ORIGINS: "https://app.example.com,https://other.example.com" };
    const request = { headers: { get: (name) => name === "Origin" ? "https://app.example.com" : null } };
    assert.equal(getCorsAllowOrigin(env, request), "https://app.example.com");
  });

  it("getCorsAllowOrigin with non-matching Origin → returns first allowed origin", () => {
    const env = { CORS_ALLOWED_ORIGINS: "https://app.example.com,https://other.example.com" };
    const request = { headers: { get: (name) => name === "Origin" ? "https://evil.com" : null } };
    assert.equal(getCorsAllowOrigin(env, request), "https://app.example.com");
  });

  it("getCorsAllowOrigin without request → returns first origin (no info disclosure)", () => {
    const env = { CORS_ALLOWED_ORIGINS: "https://app.example.com,https://other.example.com" };
    assert.equal(getCorsAllowOrigin(env, null), "https://app.example.com");
  });

  it("getCorsAllowOrigin with empty env → returns '*'", () => {
    assert.equal(getCorsAllowOrigin({}, null), "*");
    assert.equal(getCorsAllowOrigin(null, null), "*");
    assert.equal(getCorsAllowOrigin(undefined, null), "*");
  });

  it("jsonResponse with env (CORS whitelist) and no Origin → returns first origin", async () => {
    const env = { CORS_ALLOWED_ORIGINS: "https://app.example.com" };
    const resp = jsonResponse({ status: "ok" }, 200, env);
    await assertSecurityHeaders(resp, "https://app.example.com");
  });

  it("jsonResponse 400 (bad request) → security headers present", async () => {
    const resp = jsonResponse({ error: "bad request" }, 400);
    assert.equal(resp.status, 400);
    await assertSecurityHeaders(resp, "*");
  });

  it("jsonResponse 403 (forbidden) → security headers present", async () => {
    const resp = jsonResponse({ error: "forbidden" }, 403);
    assert.equal(resp.status, 403);
    await assertSecurityHeaders(resp, "*");
  });

  it("jsonResponse 413 (payload too large) → security headers present", async () => {
    const resp = jsonResponse({ error: "too large" }, 413);
    assert.equal(resp.status, 413);
    await assertSecurityHeaders(resp, "*");
  });

  it("jsonResponse with matching Origin and whitelist → CORS reflects matched origin", async () => {
    const env = { CORS_ALLOWED_ORIGINS: "https://app.example.com,https://other.example.com" };
    const request = { headers: { get: (name) => name === "Origin" ? "https://other.example.com" : null } };
    const resp = jsonResponse({ status: "ok" }, 200, env, request);
    await assertSecurityHeaders(resp, "https://other.example.com");
  });

  it("HSTS max-age is 31536000 seconds (1 year)", async () => {
    const resp = jsonResponse({});
    const hsts = resp.headers.get("strict-transport-security");
    assert.ok(hsts.includes("max-age=31536000"));
    assert.ok(hsts.includes("includeSubDomains"));
  });
});