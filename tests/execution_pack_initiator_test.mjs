import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  parseExecutionPackStartCommand,
  startExecutionPack,
  formatExecutionPackStartReply,
  handleExecutionPackCommand,
} from "../cloudflare/src/execution_pack_initiator.js";

function createDb() {
  const records = [];
  return {
    _records: records,
    prepare(sql) {
      assert.ok(!sql.includes("recycled_part_master"), "initiator must not touch recycled_part_master");
      return {
        bind(...args) {
          return {
            async run() {
              if (sql.includes("INSERT INTO execution_packs")) {
                records.push({
                  pack_id: args[0],
                  status: args[1],
                  reviewer: args[2],
                  fork_branch: args[3],
                  pr_url: args[4],
                  canary_mode: args[5],
                  initiated_by: args[6],
                  platform: args[7],
                  created_at: args[8],
                  updated_at: args[9],
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

describe("B5 execution_pack bot initiator", () => {
  it("parses start command with reviewer", () => {
    assert.deepEqual(parseExecutionPackStartCommand("!execution-pack start pack-project13-curation-01 alice"), {
      action: "start",
      pack_id: "pack-project13-curation-01",
      reviewer: "alice",
    });
  });

  it("starts canary pack in D1 without merge or recycled_part_master writes", async () => {
    const db = createDb();
    const result = await startExecutionPack(
      { DB: db, EXECUTION_PACK_DRY_RUN: "1" },
      { user_id: "u1", username: "operator" },
      {
        pack_id: "pack-project13-curation-01",
        reviewer: "human-reviewer",
        platform: "discord",
        now: "2026-07-06T12:00:00.000Z",
      }
    );

    assert.equal(result.status, "started");
    assert.equal(result.reviewer, "human-reviewer");
    assert.match(result.fork_branch, /^canary\/execution-pack\/pack-project13-curation-01\/20260706T120000Z$/);
    assert.match(result.pr_url, /^https:\/\/example\.invalid\/canary\//);
    assert.equal(db._records.length, 1);
    assert.equal(db._records[0].canary_mode, 1);
    assert.equal(db._records[0].initiated_by, "discord:operator#u1");
  });

  it("requires a human reviewer", async () => {
    await assert.rejects(
      () => startExecutionPack({ DB: createDb() }, {}, { pack_id: "pack-project13-curation-01" }),
      /Brak reviewera/
    );
  });

  it("rejects path-like pack identifiers", async () => {
    await assert.rejects(
      () => startExecutionPack({ DB: createDb(), EXECUTION_PACK_DEFAULT_REVIEWER: "alice" }, {}, { pack_id: "../secret" }),
      /Nieprawidlowy|sciezek/
    );
  });

  it("formats reply with review-first gate", async () => {
    const reply = formatExecutionPackStartReply({
      pack_id: "pack-project13-curation-01",
      status: "started",
      reviewer: "alice",
      fork_branch: "canary/execution-pack/pack-project13-curation-01/20260706T120000Z",
      pr_url: null,
    });
    assert.match(reply, /human review/);
    assert.match(reply, /nie pisze do recycled_part_master/);
  });

  it("handles bot command end to end", async () => {
    const db = createDb();
    const reply = await handleExecutionPackCommand(
      { DB: db, EXECUTION_PACK_DRY_RUN: "1" },
      { text: "!execution-pack start pack-project13-catalog-export-01 bob", user_id: "u2" },
      "discord"
    );
    assert.match(reply.reply_text, /CANARY execution_pack uruchomiony/);
    assert.equal(db._records[0].pack_id, "pack-project13-catalog-export-01");
  });
});
