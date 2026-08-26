import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  findExecutionPackByPr,
  mapPullRequestAction,
  syncExecutionPackFromWebhook,
  verifyWebhookSignature,
} from "../cloudflare/src/execution_pack_webhook.js";

function createMockDb(initialPack) {
  const rows = initialPack ? [{ id: 1, canary_mode: 1, ...initialPack }] : [];
  return {
    rows,
    prepare(sql) {
      return {
        bind(...args) {
          return {
            first() {
              if (sql.includes("FROM execution_packs WHERE pr_url")) {
                const sorted = [...rows].sort((a, b) => b.id - a.id);
                return sorted.find((row) => row.pr_url === args[0]) || null;
              }
              if (sql.includes("FROM execution_packs WHERE pack_id")) {
                const sorted = [...rows].sort((a, b) => b.id - a.id);
                return sorted.find((row) => row.pack_id === args[0]) || null;
              }
              return null;
            },
            run() {
              if (sql.includes("INSERT INTO execution_packs")) {
                const [pack_id, status, reviewer] = args;
                rows.push({ id: rows.length + 1, pack_id, status, reviewer, pr_url: null, canary_mode: 1 });
              }
              return { changes: 1 };
            },
          };
        },
      };
    },
  };
}

const startedPack = {
  pack_id: "pack-phone-aquaponics-observer-01",
  status: "started",
  reviewer: "maintainer_core",
  fork_branch: "canary/execution-pack/pack-phone-aquaponics-observer-01/20260826T100000Z",
  pr_url: "https://github.com/StrazPrzyszlosci/STRAZ_PRZYSZLOSCI/pull/42",
};

function webhookPayload(overrides = {}) {
  return {
    action: "closed",
    sender: { login: "operator_anna" },
    pull_request: {
      html_url: startedPack.pr_url,
      merged: false,
      ...overrides,
    },
  };
}

describe("execution pack github webhook T30", () => {
  it("verifies HMAC signature timing-safely", async () => {
    const secret = "webhook-secret";
    const body = JSON.stringify(webhookPayload());
    const key = await import("node:crypto");
    const hmac = key.createHmac("sha256", secret).update(body).digest("hex");

    assert.equal(await verifyWebhookSignature(secret, body, `sha256=${hmac}`), true);
    assert.equal(await verifyWebhookSignature(secret, body + " ", `sha256=${hmac}`), false);
    assert.equal(await verifyWebhookSignature(secret, body, "sha256=deadbeef"), false);
    assert.equal(await verifyWebhookSignature("", body, `sha256=${hmac}`), false);
    assert.equal(await verifyWebhookSignature(secret, body, "token=abc"), false);
  });

  it("maps only PR close actions to safe statuses", () => {
    assert.deepEqual(mapPullRequestAction(webhookPayload()), {
      nextStatus: "closed",
      prUrl: startedPack.pr_url,
      sender: "operator_anna",
    });
    assert.deepEqual(mapPullRequestAction(webhookPayload({ merged: true })).nextStatus, "merged");
    assert.equal(mapPullRequestAction({ action: "opened", pull_request: { html_url: startedPack.pr_url } }), null);
    assert.equal(mapPullRequestAction({ action: "closed" }), null);
  });

  it("syncs closed-without-merge into ledger without calling GitHub", async () => {
    const db = createMockDb(startedPack);
    const result = await syncExecutionPackFromWebhook(
      { DB: db },
      webhookPayload(),
      { now: "2026-08-26T12:00:00.000Z" }
    );
    assert.equal(result.success, true);
    assert.equal(result.source, "github_webhook");
    assert.equal(result.status, "closed");
    assert.match(result.reviewer, /^github:operator_anna$/);
    assert.equal(db.rows.length, 2);
    assert.equal(db.rows[1].status, "closed");
  });

  it("records human merge confirmation from webhook payload", async () => {
    const db = createMockDb({ ...startedPack, status: "closed" });
    const result = await syncExecutionPackFromWebhook({ DB: db }, webhookPayload({ merged: true }));
    assert.equal(result.status, "merged");
    assert.equal(result.merged_by_human_only, true);
  });

  it("ignores irrelevant actions and unknown PR urls without throwing", async () => {
    const db = createMockDb(startedPack);

    const ignored = await syncExecutionPackFromWebhook({ DB: db }, { action: "synchronize", pull_request: { html_url: startedPack.pr_url } });
    assert.equal(ignored.ignored, true);
    assert.equal(db.rows.length, 1);

    const notFound = await syncExecutionPackFromWebhook({ DB: db }, webhookPayload({
      html_url: "https://github.com/StrazPrzyszlosci/STRAZ_PRZYSZLOSCI/pull/999",
    }));
    assert.equal(notFound.success, false);
    assert.equal(notFound.reason, "pack_not_found_for_pr_url");

    // Ten sam status ponownie -> unchanged, bez nowego wpisu w ledgerze.
    await syncExecutionPackFromWebhook({ DB: createMockDb({ ...startedPack, status: "closed" }) }, webhookPayload());
  });

  it("finds latest pack by PR url", async () => {
    const db = createMockDb(startedPack);
    const found = await findExecutionPackByPr(db, startedPack.pr_url);
    assert.equal(found.pack_id, startedPack.pack_id);
    assert.equal(await findExecutionPackByPr(db, "https://github.com/x/y/pull/1"), null);
  });
});
