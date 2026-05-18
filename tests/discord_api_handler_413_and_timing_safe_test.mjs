import { describe, it } from "node:test";
import assert from "node:assert/strict";

import { timingSafeEqualString } from "../cloudflare/src/base_utils.js";
import { checkDiscordPayloadSize } from "../cloudflare/src/discord_api_handler.js";

function createMockRequest(contentLength) {
  return {
    headers: {
      get(name) {
        if (name === "Content-Length") return contentLength;
        return null;
      },
    },
  };
}

// ============================================================
// timingSafeEqualString
// ============================================================

describe("timingSafeEqualString", () => {
  it("equal strings → true", () => {
    assert.equal(timingSafeEqualString("secret", "secret"), true);
    assert.equal(timingSafeEqualString("", ""), true);
    assert.equal(timingSafeEqualString("Hello World", "Hello World"), true);
  });

  it("different strings → false", () => {
    assert.equal(timingSafeEqualString("secret", " Secret"), false);
    assert.equal(timingSafeEqualString("hello", "world"), false);
    assert.equal(timingSafeEqualString("a", "b"), false);
  });

  it("different lengths → false", () => {
    assert.equal(timingSafeEqualString("short", "longer"), false);
    assert.equal(timingSafeEqualString("", "nonempty"), false);
    assert.equal(timingSafeEqualString("nonempty", ""), false);
  });

  it("unicode / multi-byte characters", () => {
    assert.equal(timingSafeEqualString("zażółć", "zażółć"), true);
    assert.equal(timingSafeEqualString("zażółć", "zazolc"), false);
    assert.equal(timingSafeEqualString("日本語", "日本語"), true);
    assert.equal(timingSafeEqualString("日本語", "中文"), false);
  });

  it("non-string arguments → false", () => {
    assert.equal(timingSafeEqualString(null, "str"), false);
    assert.equal(timingSafeEqualString("str", undefined), false);
    assert.equal(timingSafeEqualString(123, 123), false);
    assert.equal(timingSafeEqualString({}, {}), false);
  });

  it("timing-safety: first char difference still runs full loop", () => {
    const startA = performance.now();
    timingSafeEqualString("a".repeat(1000), "b" + "a".repeat(999));
    const endA = performance.now();
    assert.ok(endA - startA < 100); // sanity check it doesn't crash

    const startB = performance.now();
    timingSafeEqualString("a".repeat(1000), "a".repeat(1000));
    const endB = performance.now();
    assert.ok(endB - startB < 100);
  });

  it("length variation: early difference but same prefix", () => {
    assert.equal(timingSafeEqualString("prefixX", "prefixY"), false);
    assert.equal(timingSafeEqualString("prefix", "prefix"), true);
  });
});

// ============================================================
// Discord Content-Length 413
// ============================================================

describe("Discord Content-Length 413", () => {
  it("payload within limit → no 413 returned", () => {
    const req = createMockRequest("1000");
    const result = checkDiscordPayloadSize(req, {});
    assert.equal(result, null);
  });

  it("payload at exact limit → no 413 returned", () => {
    const req = createMockRequest("5242880");
    const result = checkDiscordPayloadSize(req, {});
    assert.equal(result, null);
  });

  it("payload exceeding limit → 413 returned", () => {
    const req = createMockRequest("5242881");
    const result = checkDiscordPayloadSize(req, {});
    assert.ok(result instanceof Response);
    assert.equal(result.status, 413);
  });

  it("custom max via env → respects custom limit", () => {
    const req = createMockRequest("1001");
    const result = checkDiscordPayloadSize(req, { DISCORD_MAX_WEBHOOK_BODY_BYTES: "1000" });
    assert.ok(result instanceof Response);
    assert.equal(result.status, 413);
  });

  it("fallback env var → MAX_WEBHOOK_BODY_BYTES", () => {
    const req = createMockRequest("500");
    // 500 < 5242880, but if we override with 499, 500 > 499 should 413
    const result = checkDiscordPayloadSize(req, { MAX_WEBHOOK_BODY_BYTES: "499" });
    assert.ok(result instanceof Response);
    assert.equal(result.status, 413);
  });

  it("missing Content-Length header → no 413", () => {
    const req = createMockRequest(null);
    const result = checkDiscordPayloadSize(req, {});
    assert.equal(result, null);
  });

  it("negative/zero max → treated as valid and may 413 if contentLength > 0", () => {
    // When maxBodyBytes <= 0, the if condition fails (maxBodyBytes > 0 check)
    const req = createMockRequest("1");
    const result = checkDiscordPayloadSize(req, { DISCORD_MAX_WEBHOOK_BODY_BYTES: "0" });
    assert.equal(result, null);
  });

  it("response body contains error info", async () => {
    const req = createMockRequest("5242881");
    const result = checkDiscordPayloadSize(req, {});
    const body = await result.json();
    assert.equal(body.error, "Payload Too Large");
    assert.equal(body.max_bytes, 5242880);
  });
});
