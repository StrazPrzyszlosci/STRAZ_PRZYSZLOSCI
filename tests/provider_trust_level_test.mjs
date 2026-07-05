import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  validateTrustLevel,
  getProviderTrustLevel,
  getDecisionTrustLevelRequired,
  DECISION_TRUST_LEVEL_REQUIRED,
} from "../cloudflare/src/worker.js";

describe("Provider trust_level helpers (S3)", () => {
  it("validateTrustLevel accepts integers 0-10", () => {
    for (const v of [0, 1, 2, 5, 10]) {
      assert.equal(validateTrustLevel(v), v);
      assert.equal(validateTrustLevel(String(v)), v);
    }
  });

  it("validateTrustLevel rejects out-of-range and non-integer", () => {
    for (const bad of [-1, 11, 2.5, "abc", NaN, Infinity]) {
      assert.throws(() => validateTrustLevel(bad), /trust_level/);
    }
  });

  it("validateTrustLevel coerces null to 0 (treat as level zero)", () => {
    assert.equal(validateTrustLevel(null), 0);
  });

  it("validateTrustLevel rejects undefined (missing field)", () => {
    assert.throws(() => validateTrustLevel(undefined), /trust_level/);
  });

  it("getProviderTrustLevel defaults to 0 when provider missing", () => {
    assert.equal(getProviderTrustLevel(null), 0);
    assert.equal(getProviderTrustLevel(undefined), 0);
    assert.equal(getProviderTrustLevel({}), 0);
  });

  it("getProviderTrustLevel coerces missing/NaN/negative to 0", () => {
    assert.equal(getProviderTrustLevel({ trust_level: undefined }), 0);
    assert.equal(getProviderTrustLevel({ trust_level: "abc" }), 0);
    assert.equal(getProviderTrustLevel({ trust_level: -1 }), 0);
    assert.equal(getProviderTrustLevel({ trust_level: 2.9 }), 2);
  });

  it("getProviderTrustLevel returns provided level", () => {
    assert.equal(getProviderTrustLevel({ trust_level: 0 }), 0);
    assert.equal(getProviderTrustLevel({ trust_level: 2 }), 2);
    assert.equal(getProviderTrustLevel({ trust_level: 5 }), 5);
    assert.equal(getProviderTrustLevel({ trust_level: "3" }), 3);
  });

  it("getDecisionTrustLevelRequired defaults to 2 when env unset or invalid", () => {
    assert.equal(DECISION_TRUST_LEVEL_REQUIRED, 2);
    assert.equal(getDecisionTrustLevelRequired({}), 2);
    assert.equal(getDecisionTrustLevelRequired({ PROVIDER_DECISION_TRUST_LEVEL: "abc" }), 2);
    assert.equal(getDecisionTrustLevelRequired({ PROVIDER_DECISION_TRUST_LEVEL: -1 }), 2);
  });

  it("getDecisionTrustLevelRequired reads from env when set", () => {
    assert.equal(getDecisionTrustLevelRequired({ PROVIDER_DECISION_TRUST_LEVEL: 3 }), 3);
    assert.equal(getDecisionTrustLevelRequired({ PROVIDER_DECISION_TRUST_LEVEL: "1" }), 1);
    assert.equal(getDecisionTrustLevelRequired({ PROVIDER_DECISION_TRUST_LEVEL: 5 }), 5);
  });

  it("decision gate: trust_level=1 below required=2 should block (illustrative)", () => {
    const provider = { trust_level: 1 };
    const required = DECISION_TRUST_LEVEL_REQUIRED;
    assert.ok(getProviderTrustLevel(provider) < required, "trust_level 1 below default required 2");
  });

  it("decision gate: trust_level=2 meets required=2 should pass (illustrative)", () => {
    const provider = { trust_level: 2 };
    const required = DECISION_TRUST_LEVEL_REQUIRED;
    assert.ok(getProviderTrustLevel(provider) >= required);
  });
});
