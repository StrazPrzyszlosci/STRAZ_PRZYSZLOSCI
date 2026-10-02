import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  checkFloatingIpHealth,
  formatFloatingIpHealthSummary,
  parseHealthPayload,
} from "../cloudflare/src/floating_ip_healthcheck.js";

describe("floating-ip healthcheck (hardening)", () => {
  it("parses json payloads", () => {
    assert.deepEqual(parseHealthPayload({ ok: true }).ok, true);
    assert.deepEqual(parseHealthPayload({ status: "up" }).ok, true);
    assert.deepEqual(parseHealthPayload({ status: "down" }).ok, false);
    assert.equal(parseHealthPayload(null).ok, false);
    assert.equal(parseHealthPayload("ok").ok, true);
    assert.equal(parseHealthPayload("FUBAR").ok, false);
  });

  it("reports healthy on 200 + ok payload", async () => {
    const fetcher = async () => ({ status: 200, bodyJson: { ok: true, status: "up" } });
    const res = await checkFloatingIpHealth(fetcher, "https://10.0.0.1/health");
    assert.equal(res.healthy, true);
    assert.equal(res.reason, "healthy");
    assert.equal(res.statusCode, 200);
  });

  it("reports unhealthy on http error code", async () => {
    const fetcher = async () => ({ status: 503, bodyJson: { ok: true } });
    const res = await checkFloatingIpHealth(fetcher, "https://10.0.0.1/health");
    assert.equal(res.healthy, false);
    assert.match(res.reason, /http_503/);
  });

  it("reports unhealthy on down payload with 200", async () => {
    const fetcher = async () => ({ status: 200, bodyText: '{"status":"down"}' });
    const res = await checkFloatingIpHealth(fetcher, "https://10.0.0.1/health");
    assert.equal(res.healthy, false);
    assert.match(res.reason, /payload_/);
  });

  it("never throws on fetcher failure", async () => {
    const fetcher = async () => { throw new Error("timeout"); };
    const res = await checkFloatingIpHealth(fetcher, "https://10.0.0.1/health");
    assert.equal(res.healthy, false);
    assert.equal(res.reason, "fetch_error");
    assert.match(res.error, /timeout/);
  });

  it("rejects missing url/fetcher without throwing", async () => {
    assert.equal((await checkFloatingIpHealth(null, "")).reason, "missing_url");
    assert.equal((await checkFloatingIpHealth(null, "https://x/health")).reason, "missing_fetcher");
  });

  it("formats one-line summary without secrets", async () => {
    const fetcher = async () => ({ status: 200, bodyJson: { ok: true } });
    const res = await checkFloatingIpHealth(fetcher, "https://10.0.0.1/health?token=SECRET");
    const summary = formatFloatingIpHealthSummary(res);
    assert.match(summary, /HEALTHY/);
    assert.ok(!summary.includes("SECRET"));
    const bad = formatFloatingIpHealthSummary({ healthy: false, reason: "fetch_error", statusCode: null, latencyMs: 12 });
    assert.match(bad, /UNHEALTHY/);
  });
});
