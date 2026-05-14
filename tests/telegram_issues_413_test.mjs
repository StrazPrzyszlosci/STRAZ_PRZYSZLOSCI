import { describe, it } from "node:test";
import assert from "node:assert/strict";

import { checkTelegramPayloadSize } from "../cloudflare/src/telegram_issues.js";

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

describe("Telegram Webhook Content-Length 413", () => {
  it("payload within 5MB limit → no 413", () => {
    const req = createMockRequest("1000");
    const result = checkTelegramPayloadSize(req, {});
    assert.equal(result, null);
  });

  it("payload at exact limit → no 413", () => {
    const req = createMockRequest("5242880");
    const result = checkTelegramPayloadSize(req, {});
    assert.equal(result, null);
  });

  it("payload exceeding default 5MB → 413", () => {
    const req = createMockRequest("5242881");
    const result = checkTelegramPayloadSize(req, {});
    assert.ok(result instanceof Response);
    assert.equal(result.status, 413);
  });

  it("custom TELEGRAM_MAX_WEBHOOK_BODY_BYTES → 413 above custom", () => {
    const req = createMockRequest("1001");
    const result = checkTelegramPayloadSize(req, { TELEGRAM_MAX_WEBHOOK_BODY_BYTES: "1000" });
    assert.ok(result instanceof Response);
    assert.equal(result.status, 413);
  });

  it("custom TELEGRAM_MAX_WEBHOOK_BODY_BYTES → ok below custom", () => {
    const req = createMockRequest("999");
    const result = checkTelegramPayloadSize(req, { TELEGRAM_MAX_WEBHOOK_BODY_BYTES: "1000" });
    assert.equal(result, null);
  });

  it("fallback MAX_WEBHOOK_BODY_BYTES → 413 above", () => {
    const req = createMockRequest("500");
    const result = checkTelegramPayloadSize(req, { MAX_WEBHOOK_BODY_BYTES: "499" });
    assert.ok(result instanceof Response);
    assert.equal(result.status, 413);
  });

  it("prefers TELEGRAM_MAX_WEBHOOK_BODY_BYTES over MAX_WEBHOOK_BODY_BYTES", () => {
    const req = createMockRequest("500");
    const result = checkTelegramPayloadSize(req, { TELEGRAM_MAX_WEBHOOK_BODY_BYTES: "100", MAX_WEBHOOK_BODY_BYTES: "1000" });
    assert.ok(result instanceof Response);
    assert.equal(result.status, 413);
  });

  it("missing Content-Length header → no 413", () => {
    const req = createMockRequest(null);
    const result = checkTelegramPayloadSize(req, {});
    assert.equal(result, null);
  });

  it("empty Content-Length string → no 413", () => {
    const req = createMockRequest("");
    const result = checkTelegramPayloadSize(req, {});
    assert.equal(result, null);
  });

  it("zero Content-Length → no 413", () => {
    const req = createMockRequest("0");
    const result = checkTelegramPayloadSize(req, {});
    assert.equal(result, null);
  });

  it("very large payload (100MB) → 413", () => {
    const req = createMockRequest(String(100 * 1024 * 1024));
    const result = checkTelegramPayloadSize(req, {});
    assert.ok(result instanceof Response);
    assert.equal(result.status, 413);
  });

  it("response body contains max_bytes info", async () => {
    const req = createMockRequest("5242881");
    const result = checkTelegramPayloadSize(req, {});
    const body = await result.json();
    assert.ok(body.error.includes("Request body too large"));
    assert.ok(body.error.includes("5242880"));
  });

  it("non-numeric Content-Length → parseInt yields NaN, so no 413 (NaN comparison safe)", () => {
    const req = createMockRequest("abc123");
    const result = checkTelegramPayloadSize(req, {});
    assert.equal(result, null);
  });

  it("negative Content-Length → no 413", () => {
    const req = createMockRequest("-100");
    const result = checkTelegramPayloadSize(req, {});
    assert.equal(result, null);
  });
});