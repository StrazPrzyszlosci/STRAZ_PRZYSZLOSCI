import { describe, it } from "node:test";
import assert from "node:assert/strict";
import worker from "../cloudflare/src/worker.js";

const CELL = "phone-aquaponics-observer-01";
const PROVIDER_TOKEN = "test-provider-token-01";
const ADMIN_SECRET = "test-admin-secret";

async function sha256hex(text) {
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
  return Array.from(new Uint8Array(digest), (b) => b.toString(16).padStart(2, "0")).join("");
}

// Miesiące wstecz od RZECZYWISTEGO teraz — computeGrowCorrelation filtruje
// oknem now-monthsBack, więc fixture'y muszą być w oknie niezależnie od daty
// uruchomienia (inaczej time-bomb jak w test_expiry_report).
function recentMonthKeys(count) {
  const now = new Date();
  const keys = [];
  for (let i = count - 1; i >= 0; i -= 1) {
    const d = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth() - i, 1));
    keys.push(d.toISOString().slice(0, 7));
  }
  return keys;
}

function createMockDb({
  providerTokenHash,
  providersRow = "default",
  policyJson,
  registeredCells = [CELL],
  sensorRows,
  harvestSums,
  harvestRows,
}) {
  function dispatchFirst(sql, args) {
    if (sql.includes("FROM providers") && sql.includes("WHERE provider_id")) {
      if (providersRow === null) return null;
      return {
        provider_id: CELL,
        provider_status: "active",
        write_token_hash: providerTokenHash,
      };
    }
    if (sql.includes("FROM agri_grow_policies")) {
      if (sql.includes("policy_json")) {
        return policyJson ? { policy_json: policyJson } : null;
      }
      const wanted = args[0];
      if (registeredCells.includes(wanted)) return { grow_cell_id: wanted };
      return null;
    }
    return null;
  }
  function dispatchAll(sql) {
    if (sql.includes("FROM schema_migrations")) return { results: [] };
    if (sql.includes("FROM sensor_readings_staging")) return { results: sensorRows || [] };
    if (sql.includes("total_mass")) return { results: harvestSums || [] };
    if (sql.includes("FROM harvest_records")) return { results: harvestRows || [] };
    return { results: [] };
  }
  return {
    prepare(sql) {
      return {
        bind(...args) {
          return {
            async first() {
              return dispatchFirst(sql, args);
            },
            async all() {
              return dispatchAll(sql);
            },
            async run() {
              return { success: true };
            },
          };
        },
        async first() {
          return dispatchFirst(sql, []);
        },
        async all() {
          return dispatchAll(sql);
        },
        async run() {
          return { success: true };
        },
      };
    },
  };
}

function trendRows() {
  return [
    { grow_cell_id: CELL, crop_profile: "greens", harvested_at: "2026-06-10T09:00:00.000Z", mass_g: 100 },
    { grow_cell_id: CELL, crop_profile: "greens", harvested_at: "2026-07-10T09:00:00.000Z", mass_g: 150 },
    { grow_cell_id: CELL, crop_profile: "greens", harvested_at: "2026-08-10T09:00:00.000Z", mass_g: 200 },
  ];
}

function correlationFixture() {
  const [m0, m1, m2] = recentMonthKeys(3);
  const sensorRows = [
    { sensor: "ph", month_key: m0, mean_value: 6.0 },
    { sensor: "ph", month_key: m1, mean_value: 6.2 },
    { sensor: "ph", month_key: m2, mean_value: 6.4 },
  ];
  const harvestSums = [
    { month_key: m0, total_mass: 100 },
    { month_key: m1, total_mass: 150 },
    { month_key: m2, total_mass: 200 },
  ];
  const policy = {
    id: "pol-greens-01",
    grow_cell_id: CELL,
    bands: {
      ph: { safe_min: 6.0, safe_max: 7.0, alarm_below: 5.5, alarm_above: 7.5 },
    },
  };
  return { sensorRows, harvestSums, policyJson: JSON.stringify(policy) };
}

function get(path, headers = {}) {
  return new Request(`https://example.com${path}`, { headers });
}

function postJson(path, body, headers = {}) {
  return new Request(`https://example.com${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...headers },
    body: JSON.stringify(body),
  });
}

describe("worker agri routes (T40/T41 fetch-level)", () => {
  it("GET /v1/agri/harvest/trends returns per-crop trends for valid provider token", async () => {
    const env = {
      DB: createMockDb({
        providerTokenHash: await sha256hex(PROVIDER_TOKEN),
        harvestRows: trendRows(),
      }),
    };
    const res = await worker.fetch(
      get(`/v1/agri/harvest/trends?provider_id=${CELL}&months=12`, {
        "X-Provider-Token": PROVIDER_TOKEN,
      }),
      env,
      {}
    );
    assert.equal(res.status, 200);
    const body = await res.json();
    assert.equal(body.success, true);
    assert.equal(body.grow_cell_id, CELL);
    assert.equal(body.trends.greens.direction, "rising");
    assert.ok(body.trends.greens.slope_g_per_month > 0);
  });

  it("GET /v1/agri/harvest/trends rejects bad provider token with 401", async () => {
    const env = {
      DB: createMockDb({
        providerTokenHash: await sha256hex(PROVIDER_TOKEN),
        harvestRows: trendRows(),
      }),
    };
    const res = await worker.fetch(
      get(`/v1/agri/harvest/trends?provider_id=${CELL}`, {
        "X-Provider-Token": "wrong-token",
      }),
      env,
      {}
    );
    assert.equal(res.status, 401);
  });

  it("GET /v1/agri/harvest/trends requires provider_id with 400", async () => {
    const env = {
      DB: createMockDb({ providerTokenHash: await sha256hex(PROVIDER_TOKEN) }),
    };
    const res = await worker.fetch(
      get("/v1/agri/harvest/trends", { "X-Provider-Token": PROVIDER_TOKEN }),
      env,
      {}
    );
    assert.equal(res.status, 400);
  });

  it("preserves deployment gating: compliant prod ID on demo-only worker stays 403", async () => {
    const env = {
      DB: createMockDb({ providerTokenHash: await sha256hex(PROVIDER_TOKEN) }),
      ALLOWED_PROVIDER_ENVIRONMENTS: "demo",
    };
    const res = await worker.fetch(
      get("/v1/agri/harvest/trends?provider_id=cell-prod-node-01", {
        "X-Provider-Token": PROVIDER_TOKEN,
      }),
      env,
      {}
    );
    // ForbiddenError (zły env) nie wpada w fallback komórek.
    assert.equal(res.status, 403);
  });

  it("GET /v1/agri/harvest/trends rejects unknown cell without env segment with 400", async () => {
    const env = {
      DB: createMockDb({ providerTokenHash: await sha256hex(PROVIDER_TOKEN) }),
    };
    const res = await worker.fetch(
      get("/v1/agri/harvest/trends?provider_id=ghost-cell-99", {
        "X-Provider-Token": PROVIDER_TOKEN,
      }),
      env,
      {}
    );
    assert.equal(res.status, 400);
  });

  it("GET /v1/agri/correlation returns monthly correlation for registered cell", async () => {
    const { sensorRows, harvestSums } = correlationFixture();
    const env = {
      DB: createMockDb({
        providerTokenHash: await sha256hex(PROVIDER_TOKEN),
        sensorRows,
        harvestSums,
      }),
    };
    const res = await worker.fetch(
      get(`/v1/agri/correlation?provider_id=${CELL}&months=12`, {
        "X-Provider-Token": PROVIDER_TOKEN,
      }),
      env,
      {}
    );
    assert.equal(res.status, 200);
    const body = await res.json();
    assert.equal(body.success, true);
    assert.ok(Array.isArray(body.sensors) && body.sensors.length >= 1);
    const ph = body.sensors.find((s) => s.sensor === "ph");
    assert.ok(ph.pearson_r > 0.9);
  });

  it("POST /v1/providers/register enrolls a known agri cell despite missing env segment", async () => {
    const env = {
      DB: createMockDb({
        providerTokenHash: await sha256hex(PROVIDER_TOKEN),
        providersRow: null,
      }),
    };
    const res = await worker.fetch(
      postJson("/v1/providers/register", {
        provider_id: CELL,
        provider_kind: "edge_node",
        provider_label: "polka testowa",
      }),
      env,
      {}
    );
    assert.equal(res.status, 201);
    const body = await res.json();
    assert.equal(body.provider_id, CELL);
    assert.ok(typeof body.write_token === "string" && body.write_token.length > 8);
  });

  it("GET /v1/agri/calibration-view is admin-gated with 401", async () => {
    const env = {
      DB: createMockDb({ providerTokenHash: await sha256hex(PROVIDER_TOKEN) }),
      PROVIDER_TRUST_EDITOR_SECRET: ADMIN_SECRET,
    };
    const res = await worker.fetch(
      get("/v1/agri/calibration-view?policy_id=pol-greens-01", {
        "X-Trust-Editor-Secret": "wrong-secret",
      }),
      env,
      {}
    );
    assert.equal(res.status, 401);
  });

  it("GET /v1/agri/calibration-view returns suggestion + normalized view for valid admin", async () => {
    const { sensorRows, harvestSums, policyJson } = correlationFixture();
    const env = {
      DB: createMockDb({
        providerTokenHash: await sha256hex(PROVIDER_TOKEN),
        policyJson,
        sensorRows,
        harvestSums,
      }),
      PROVIDER_TRUST_EDITOR_SECRET: ADMIN_SECRET,
    };
    const res = await worker.fetch(
      get("/v1/agri/calibration-view?policy_id=pol-greens-01&months_back=12", {
        "X-Trust-Editor-Secret": ADMIN_SECRET,
      }),
      env,
      {}
    );
    assert.equal(res.status, 200);
    const body = await res.json();
    assert.equal(body.success, true);
    assert.ok(
      body.suggestion.suggestions.length >= 1,
      "expected at least one band suggestion"
    );
    assert.ok(body.view.text.includes("KALIBRACJA"));
    assert.ok(body.view.markdown.includes("Kalibracja"));
    assert.ok(body.pull_request_body.includes("CALIBRATION SUGGESTION"));
  });
});
