import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  EXECUTION_PACK_STATUS_TRANSITIONS,
  handleExecutionPackCommand,
  parseExecutionPackStatusCommand,
  updateExecutionPackStatus,
  __test__,
} from "../cloudflare/src/execution_pack_initiator.js";

function createMockDb(initialPack) {
  const rows = initialPack ? [{ id: 1, canary_mode: 1, ...initialPack }] : [];
  return {
    rows,
    prepare(sql) {
      return {
        bind(...args) {
          return {
            first() {
              if (sql.includes("FROM execution_packs")) {
                const packId = args[0];
                const sorted = [...rows].sort((a, b) => b.id - a.id);
                return sorted.find((row) => row.pack_id === packId) || null;
              }
              return null;
            },
            run() {
              if (sql.includes("INSERT INTO execution_packs")) {
                const [pack_id, status, reviewer, fork_branch, pr_url] = args;
                rows.push({
                  id: rows.length + 1,
                  pack_id,
                  status,
                  reviewer,
                  fork_branch,
                  pr_url,
                  canary_mode: 1,
                });
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

describe("execution pack status flow T23", () => {
  it("allows only safe transitions started -> closed -> merged", () => {
    assert.deepEqual(EXECUTION_PACK_STATUS_TRANSITIONS.started, ["closed"]);
    assert.deepEqual(EXECUTION_PACK_STATUS_TRANSITIONS.closed, ["merged"]);
    assert.deepEqual(EXECUTION_PACK_STATUS_TRANSITIONS.merged, []);
  });

  it("parses close and merged commands", () => {
    assert.deepEqual(parseExecutionPackStatusCommand("!execution-pack close pack-01"), {
      action: "close",
      pack_id: "pack-01",
      reviewer: "",
    });
    assert.deepEqual(parseExecutionPackStatusCommand("!pack merged pack-01 maintainer_core"), {
      action: "merged",
      pack_id: "pack-01",
      reviewer: "maintainer_core",
    });
    assert.equal(parseExecutionPackStatusCommand("!execution-pack start pack-01 rev"), null);
  });

  it("rolls back start -> PR -> closed without merge via GitHub PATCH", async () => {
    const calls = [];
    const db = createMockDb(startedPack);
    const env = {
      DB: db,
      GITHUB_TOKEN: "test-token",
      __TEST_FETCH: async (url, init) => {
        calls.push({ url, method: init.method, body: JSON.parse(init.body) });
        return { ok: true, json: async () => ({}) };
      },
    };
    const result = await updateExecutionPackStatus(env, startedPack.pack_id, "closed", { now: "2026-08-26T11:00:00.000Z" });

    assert.equal(result.status, "closed");
    assert.equal(result.previous_status, "started");
    assert.equal(calls.length, 1);
    assert.equal(calls[0].method, "PATCH");
    assert.equal(calls[0].body.state, "closed");
    assert.ok(!calls.some((call) => call.method === "PUT"), "bot must never call merge endpoint");
    assert.equal(db.rows.length, 2);
    assert.equal(db.rows[1].status, "closed");
  });

  it("requires PR URL and reviewer before marking merged", async () => {
    const closedNoPrDb = createMockDb({ ...startedPack, status: "closed", pr_url: null });
    await assert.rejects(
      updateExecutionPackStatus({ DB: closedNoPrDb }, startedPack.pack_id, "merged", { reviewer: "maintainer_core" }),
      /PR URL/
    );

    const db = createMockDb({ ...startedPack, status: "closed" });
    await assert.rejects(
      updateExecutionPackStatus({ DB: db }, startedPack.pack_id, "merged", {}),
      /reviewera/
    );

    const result = await updateExecutionPackStatus(
      { DB: createMockDb({ ...startedPack, status: "closed" }) },
      startedPack.pack_id,
      "merged",
      { reviewer: "maintainer_core" }
    );
    assert.equal(result.status, "merged");
    assert.equal(result.merged_by_human_only, true);
  });

  it("rejects invalid transitions and unknown packs", async () => {
    const mergedDb = createMockDb({ ...startedPack, status: "merged" });
    await assert.rejects(
      updateExecutionPackStatus({ DB: mergedDb }, startedPack.pack_id, "closed"),
      /Niedozwolona tranzycja/
    );
    await assert.rejects(
      updateExecutionPackStatus({ DB: createMockDb(null) }, startedPack.pack_id, "closed"),
      /Nie znaleziono/
    );
  });

  it("handles bot commands end to end with error replies instead of throws", async () => {
    const db = createMockDb(startedPack);
    const env = { DB: db };
    const closeReply = await handleExecutionPackCommand(env, { text: `!execution-pack close ${startedPack.pack_id}` });
    assert.match(closeReply.reply_text, /started -> closed/);
    assert.match(closeReply.reply_text, /bez merge/);

    const badTransition = await handleExecutionPackCommand(env, { text: `!execution-pack close ${startedPack.pack_id}` });
    assert.match(badTransition.reply_text, /Blad execution_pack/);

    const usage = await handleExecutionPackCommand(env, { text: "hello" });
    assert.match(usage.reply_text, /Uzycie/);
  });

  it("parses GitHub PR URLs for the close flow", () => {
    const parsed = __test__.parseGitHubPrUrl(startedPack.pr_url);
    assert.deepEqual(parsed, { owner: "StrazPrzyszlosci", repo: "STRAZ_PRZYSZLOSCI", number: 42 });
    assert.equal(__test__.parseGitHubPrUrl("https://example.invalid/x"), null);
  });
});
