import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  handleKicadReviewCommand,
  handleKicadReviewAction,
  buildKicadReviewQueueButtons,
  __test__,
} from "../cloudflare/src/discord_kicad_actions.js";

function createReviewDb() {
  const links = [];
  const events = [];
  let nextLinkId = 1;
  let nextEventId = 1;
  return {
    _links: links,
    _events: events,
    prepare(sql) {
      return {
        bind(...args) {
          return {
            async first() {
              if (
                sql.includes("FROM recycled_part_kicad_links") &&
                sql.includes("WHERE master_part_id = ? AND kicad_component_id = ?")
              ) {
                return (
                  links.find(
                    (row) =>
                      row.master_part_id === args[0] &&
                      row.kicad_component_id === args[1]
                  ) || null
                );
              }
              return null;
            },
            async all() {
              if (sql.includes("FROM recycled_part_kicad_links rpk")) {
                const pending = links.filter((row) =>
                  ["suggested", "needs_more_data"].includes(row.review_status)
                );
                return { results: pending.slice(0, args[0] || 5) };
              }
              return { results: [] };
            },
            async run() {
              if (sql.includes("INSERT INTO recycled_part_kicad_links")) {
                links.push({
                  id: nextLinkId++,
                  master_part_id: args[0],
                  kicad_component_id: args[1],
                  match_type: args[2],
                  confidence: args[3],
                  review_status: "suggested",
                  reviewed_by: args[4],
                  reason: args[5],
                  created_at: args[6],
                  reviewed_at: null,
                  part_number: "TPS65994",
                  symbol_name: "TPS65994",
                  source_slug: "cern-kicad-libs",
                  license_spdx: "CERN-OHL-P-2.0",
                });
              } else if (sql.includes("UPDATE recycled_part_kicad_links")) {
                const row = links.find(
                  (item) =>
                    item.master_part_id === args[4] &&
                    item.kicad_component_id === args[5]
                );
                if (row) {
                  row.review_status = args[0];
                  row.reviewed_by = args[1];
                  row.reason = args[2];
                  row.reviewed_at = args[3];
                }
              } else if (sql.includes("INSERT INTO kicad_review_events")) {
                events.push({
                  id: nextEventId++,
                  link_id: args[0],
                  master_part_id: args[1],
                  kicad_component_id: args[2],
                  previous_status: args[3],
                  next_status: args[4],
                  reviewed_by: args[5],
                  reason: args[6],
                  created_at: args[7],
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

async function seedLink(db, masterPartId = 1, kicadComponentId = 2) {
  db._links.push({
    id: db._links.length + 1,
    master_part_id: masterPartId,
    kicad_component_id: kicadComponentId,
    match_type: "exact_mpn",
    confidence: 0.9,
    review_status: "suggested",
    reviewed_by: "ai",
    reason: "test",
    created_at: "2026-05-14T00:00:00Z",
    reviewed_at: null,
    part_number: "TPS65994",
    symbol_name: "TPS65994",
    source_slug: "cern-kicad-libs",
    license_spdx: "CERN-OHL-P-2.0",
  });
}

describe("Discord KiCad review actions (Z94)", () => {
  it("builds review queue command reply with approve buttons", async () => {
    const db = createReviewDb();
    await seedLink(db, 1, 2);
    await seedLink(db, 3, 4);
    const reply = await handleKicadReviewCommand({ DB: db }, { user_id: "u1" });
    assert.match(reply.reply_text, /KiCad review queue/);
    assert.ok(reply.reply_markup);
    assert.ok(reply.reply_markup.buttons[0].length > 0);
    const firstButton = reply.reply_markup.buttons[0][0];
    assert.equal(firstButton.value, "kicad_review_approve:1:2");
  });

  it("returns empty message and no buttons when queue is empty", async () => {
    const db = createReviewDb();
    const reply = await handleKicadReviewCommand({ DB: db }, { user_id: "u1" });
    assert.match(reply.reply_text, /Brak link[oó]w/);
    assert.equal(reply.reply_markup, null);
  });

  it("rejects approve action for non-maintainer", async () => {
    const db = createReviewDb();
    await seedLink(db, 1, 2);
    const reply = await handleKicadReviewAction(
      { DB: db },
      {
        callback_data: "kicad_review_approve:1:2",
        user_id: "outsider",
        username: "stranger",
      }
    );
    assert.match(reply.reply_text, /maintener/);
    assert.equal(db._links[0].review_status, "suggested");
  });

  it("allows approve action for maintainer via id allowlist", async () => {
    const db = createReviewDb();
    await seedLink(db, 1, 2);
    const reply = await handleKicadReviewAction(
      { DB: db, KICAD_REVIEW_MAINTAINER_IDS: "maint-1, maint-2" },
      {
        callback_data: "kicad_review_approve:1:2",
        user_id: "maint-1",
        username: "alice",
      }
    );
    assert.match(reply.reply_text, /suggested -> approved/);
    assert.equal(db._links[0].review_status, "approved");
    assert.match(db._events.at(-1).reviewed_by, /discord:alice#maint-1/);
  });

  it("allows approve action for maintainer via role allowlist", async () => {
    const db = createReviewDb();
    await seedLink(db, 1, 2);
    const reply = await handleKicadReviewAction(
      { DB: db, KICAD_REVIEW_MAINTAINER_ROLES: "kicad-maintainer, reviewer" },
      {
        callback_data: "kicad_review_approve:1:2",
        user_id: "u9",
        username: "bob",
        roles: ["member", "kicad-maintainer"],
      }
    );
    assert.match(reply.reply_text, /approved/);
    assert.equal(db._links[0].review_status, "approved");
  });

  it("allows reject action for non-maintainer (no human gate for reject)", async () => {
    const db = createReviewDb();
    await seedLink(db, 1, 2);
    const reply = await handleKicadReviewAction(
      { DB: db },
      {
        callback_data: "kicad_review_reject:1:2",
        user_id: "outsider",
        username: "stranger",
      }
    );
    assert.match(reply.reply_text, /rejected/);
    assert.equal(db._links[0].review_status, "rejected");
  });

  it("records needs_more_data action", async () => {
    const db = createReviewDb();
    await seedLink(db, 1, 2);
    const reply = await handleKicadReviewAction(
      { DB: db },
      {
        callback_data: "kicad_review_more_data:1:2",
        user_id: "u5",
        username: "carol",
      }
    );
    assert.match(reply.reply_text, /needs_more_data/);
    assert.equal(db._links[0].review_status, "needs_more_data");
  });

  it("rejects invalid callback data", async () => {
    const db = createReviewDb();
    const reply = await handleKicadReviewAction(
      { DB: db },
      { callback_data: "kicad_review_approve:abc:def", user_id: "u1" }
    );
    assert.match(reply.reply_text, /Bledny identyfikator/);
  });

  it("isMaintainer checks ids, usernames and roles", () => {
    const { isMaintainer } = __test__;
    assert.ok(isMaintainer({ KICAD_REVIEW_MAINTAINER_IDS: "alpha, beta" }, { user_id: "alpha" }));
    assert.ok(isMaintainer({ KICAD_REVIEW_MAINTAINER_IDS: "Alpha" }, { username: "alpha" }));
    assert.ok(
      isMaintainer(
        { KICAD_REVIEW_MAINTAINER_ROLES: "kicad-reviewer" },
        { roles: ["kicad-reviewer"] }
      )
    );
    assert.equal(
      isMaintainer({ KICAD_REVIEW_MAINTAINER_IDS: "alpha" }, { user_id: "beta" }),
      false
    );
    assert.equal(isMaintainer({}, { user_id: "alpha" }), false);
  });

  it("buildKicadReviewQueueButtons caps to queue limit", () => {
    const rows = Array.from({ length: 10 }, (_, i) => ({
      master_part_id: i + 1,
      kicad_component_id: i + 100,
    }));
    const markup = buildKicadReviewQueueButtons(rows);
    assert.equal(markup.buttons[0].length, 5);
    assert.equal(markup.buttons[0][0].value, "kicad_review_approve:1:100");
  });
});
