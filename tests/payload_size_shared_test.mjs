import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { checkPayloadSize, getMaxPayloadBytes } from "../cloudflare/src/payload_size.js";

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

function jsonReply(payload, status = 200) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { "content-type": "application/json; charset=utf-8" },
  });
}

describe("Shared webhook payload size helper (Z83)", () => {
  it("uses provider-specific env var before fallback and default", () => {
    assert.equal(getMaxPayloadBytes({ DISCORD_MAX_WEBHOOK_BODY_BYTES: "100", MAX_WEBHOOK_BODY_BYTES: "200" }, { envKey: "DISCORD_MAX_WEBHOOK_BODY_BYTES" }), 100);
    assert.equal(getMaxPayloadBytes({ MAX_WEBHOOK_BODY_BYTES: "200" }, { envKey: "DISCORD_MAX_WEBHOOK_BODY_BYTES" }), 200);
    assert.equal(getMaxPayloadBytes({}, { envKey: "DISCORD_MAX_WEBHOOK_BODY_BYTES" }), 5242880);
  });

  it("returns null when Content-Length is missing, invalid, negative, or within limit", () => {
    for (const contentLength of [null, "", "abc123", "-100", "1000"]) {
      const result = checkPayloadSize(createMockRequest(contentLength), {}, {
        envKey: "DISCORD_MAX_WEBHOOK_BODY_BYTES",
        responseFactory: jsonReply,
      });
      assert.equal(result, null);
    }
  });

  it("returns 413 with max_bytes when Content-Length exceeds limit", async () => {
    const result = checkPayloadSize(createMockRequest("1001"), { DISCORD_MAX_WEBHOOK_BODY_BYTES: "1000" }, {
      envKey: "DISCORD_MAX_WEBHOOK_BODY_BYTES",
      responseFactory: jsonReply,
      errorMessage: "Payload Too Large",
    });
    assert.ok(result instanceof Response);
    assert.equal(result.status, 413);
    assert.deepEqual(await result.json(), { error: "Payload Too Large", max_bytes: 1000 });
  });

  it("can disable checks when configured max is zero or negative", () => {
    const result = checkPayloadSize(createMockRequest("1"), { MAX_WEBHOOK_BODY_BYTES: "0" }, {
      responseFactory: jsonReply,
    });
    assert.equal(result, null);
  });
});
