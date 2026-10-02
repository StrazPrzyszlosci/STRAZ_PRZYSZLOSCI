import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { checkFloatingIpHealth } from "../cloudflare/src/floating_ip_health.js";

const okDb = {
  prepare(sql) {
    assert.match(sql, /SELECT 1/);
    return { async first() { return { ok: 1 }; } };
  },
};
const downDb = {
  prepare() { return { async first() { throw new Error("D1 timeout"); } }; },
};
const weirdDb = {
  prepare() { return { async first() { return { nope: true }; } }; },
};

describe("floating-ip health (hardening)", () => {
  it("reports ready with db ok and version", async () => {
    const res = await checkFloatingIpHealth({ DB: okDb, DEPLOY_VERSION: "abc123" }, { nowMs: 0 });
    assert.equal(res.status, "ok");
    assert.equal(res.ready, true);
    assert.equal(res.db, "ok");
    assert.equal(res.version, "abc123");
    assert.ok(res.now);
  });

  it("reports ready with db unconfigured (no DB binding)", async () => {
    const res = await checkFloatingIpHealth({});
    assert.equal(res.status, "ok");
    assert.equal(res.ready, true);
    assert.equal(res.db, "unconfigured");
  });

  it("reports not-ready on db error without throwing", async () => {
    const res = await checkFloatingIpHealth({ DB: downDb });
    assert.equal(res.status, "ok");
    assert.equal(res.ready, false);
    assert.equal(res.db, "unreachable");
    assert.match(res.db_error, /D1 timeout/);
  });

  it("reports not-ready on unexpected db result", async () => {
    const res = await checkFloatingIpHealth({ DB: weirdDb });
    assert.equal(res.ready, false);
    assert.equal(res.db, "unexpected_result");
  });

  it("defaults version to dev", async () => {
    const res = await checkFloatingIpHealth({ DB: okDb });
    assert.equal(res.version, "dev");
  });
});
