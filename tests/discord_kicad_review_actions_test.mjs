import { describe, it } from "node:test";
import assert from "node:assert/strict";

import { handleDiscordWebhook } from "../cloudflare/src/discord_api_handler.js";

function createReviewDb() {
  const links = [{
    id: 1,
    master_part_id: 10,
    kicad_component_id: 20,
    match_type: "ai_suggested",
    confidence: 0.91,
    review_status: "suggested",
    reviewed_by: "ai",
    reason: "fixture",
    created_at: "2026-05-14T00:00:00.000Z",
    reviewed_at: null,
    part_number: "TPS65994",
    symbol_name: "TPS65994",
    footprint_name: "QFN-56",
    source_slug: "cern-kicad-libs",
    license_spdx: "CERN-OHL-P-2.0",
  }];
  const events = [];
  let nextLinkId = 2;
  return {
    _links: links,
    _events: events,
    prepare(sql) {
      return {
        bind(...args) {
          return {
            async first() {
              if (sql.includes("FROM recycled_part_kicad_links") && sql.includes("WHERE master_part_id = ? AND kicad_component_id = ?")) {
                return links.find((row) => row.master_part_id === args[0] && row.kicad_component_id === args[1]) || null;
              }
              return null;
            },
            async all() {
              if (sql.includes("FROM recycled_part_kicad_links rpk")) {
                return { results: links.filter((row) => ["suggested", "needs_more_data"].includes(row.review_status)).slice(0, args[0] || 10) };
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
                  part_number: "NE555",
                  symbol_name: "NE555",
                  source_slug: "cern-kicad-libs",
                  license_spdx: "CERN-OHL-P-2.0",
                });
              } else if (sql.includes("UPDATE recycled_part_kicad_links")) {
                const row = links.find((item) => item.master_part_id === args[4] && item.kicad_component_id === args[5]);
                if (row) {
                  row.review_status = args[0];
                  row.reviewed_by = args[1];
                  row.reason = args[2];
                  row.reviewed_at = args[3];
                }
              } else if (sql.includes("INSERT INTO kicad_review_events")) {
                events.push({
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

function makeRequest(body) {
  return new Request("https://example.test/discord", {
    method: "POST",
    headers: {
      "content-type": "application/json",
      "X-Discord-Bot-Secret": "test-secret",
    },
    body: JSON.stringify(body),
  });
}

async function postDiscord(env, body) {
  const response = await handleDiscordWebhook(makeRequest(body), env);
  return await response.json();
}

describe("Discord KiCad review actions (Z94)", () => {
  it("shows pending review queue with maintainer action buttons", async () => {
    const env = { DB: createReviewDb(), DISCORD_BOT_SECRET: "test-secret", DISCORD_KICAD_REVIEWER_IDS: "maintainer-1" };
    const json = await postDiscord(env, { chat_id: "c1", user_id: "maintainer-1", callback_data: "kicad_review:queue", type: "callback" });

    assert.match(json.reply_text, /KiCad review queue/);
    assert.equal(json.reply_markup.buttons[0][0].value, "kicad_review:approve:10:20");
    assert.equal(json.reply_markup.buttons[0][1].value, "kicad_review:reject:10:20");
  });

  it("blocks approval from non-maintainers before touching the ledger", async () => {
    const db = createReviewDb();
    const env = { DB: db, DISCORD_BOT_SECRET: "test-secret", DISCORD_KICAD_REVIEWER_IDS: "maintainer-1" };
    const json = await postDiscord(env, { chat_id: "c1", user_id: "volunteer-1", callback_data: "kicad_review:approve:10:20", type: "callback" });

    assert.match(json.reply_text, /tylko maintainer/);
    assert.equal(db._links[0].review_status, "suggested");
    assert.equal(db._events.length, 0);
  });

  it("records maintainer approvals through the shared KiCad review ledger", async () => {
    const db = createReviewDb();
    const env = { DB: db, DISCORD_BOT_SECRET: "test-secret", DISCORD_KICAD_REVIEWER_IDS: "maintainer-1" };
    const json = await postDiscord(env, { chat_id: "c1", user_id: "maintainer-1", callback_data: "kicad_review:approve:10:20", type: "callback" });

    assert.match(json.reply_text, /Decyzja zapisana/);
    assert.equal(db._links[0].review_status, "approved");
    assert.equal(db._links[0].reviewed_by, "discord:maintainer-1");
    assert.equal(db._events.at(-1).previous_status, "suggested");
    assert.equal(db._events.at(-1).next_status, "approved");
  });

  it("allows Discord users to send candidate links into review without approving them", async () => {
    const db = createReviewDb();
    const env = { DB: db, DISCORD_BOT_SECRET: "test-secret", DISCORD_KICAD_REVIEWER_IDS: "maintainer-1" };
    const json = await postDiscord(env, { chat_id: "c1", user_id: "volunteer-1", callback_data: "kicad_review:suggest:11:21", type: "callback" });

    assert.match(json.reply_text, /wysłany do review/);
    assert.equal(db._links.find((row) => row.master_part_id === 11 && row.kicad_component_id === 21).review_status, "suggested");
    assert.equal(db._events.at(-1).next_status, "suggested");
  });
});

function createExportPreviewDb() {
  const approvedRows = [{
    master_part_id: 1,
    part_number: "TPS65994",
    part_name: "USB-C PD Controller",
    species: "IC",
    genus: "Power",
    mounting: "SMD",
    value: "",
    keywords: "usb-c, pd",
    description: "Approved controller",
    datasheet_url: "https://example.test/tps.pdf",
    kicad_symbol: "",
    kicad_footprint: "",
    kicad_reference: "U",
    kicad_component_id: 20,
    symbol_name: "CERN_Power:TPS65994",
    footprint_name: "Package_QFN:QFN-56",
    reference_prefix: "U",
    source_slug: "cern-kicad-libs",
    source_url: "https://gitlab.com/ohwr/cern-kicad-libs",
    license_spdx: "CERN-OHL-P-2.0",
    review_status: "approved",
    reviewed_by: "discord:maintainer-1",
    reviewed_at: "2026-05-16T12:00:00.000Z",
    reason: "Verified",
  }];
  let queryCount = 0;
  return {
    _queryCount: () => queryCount,
    prepare(sql) {
      return {
        bind(...args) {
          return {
            async first() {
              return null;
            },
            async all() {
              if (sql.includes("FROM recycled_part_kicad_links rpk") && sql.includes("WHERE rpk.review_status = 'approved'")) {
                queryCount += 1;
                assert.ok(args[0] === 5 || args[0] === 1000);
                return { results: approvedRows.slice(0, args[0]) };
              }
              return { results: [] };
            },
          };
        },
      };
    },
  };
}

describe("Discord KiCad approved export preview (Z101)", () => {
  it("blocks approved export preview for non-maintainers before querying export data", async () => {
    const db = createExportPreviewDb();
    const env = { DB: db, DISCORD_BOT_SECRET: "test-secret", DISCORD_KICAD_REVIEWER_IDS: "maintainer-1" };
    const json = await postDiscord(env, { chat_id: "c1", user_id: "volunteer-1", text: "/kicad_export_preview" });

    assert.match(json.reply_text, /tylko dla operatora\/maintainera/);
    assert.equal(db._queryCount(), 0);
  });

  it("returns maintainer approved-only export preview with receipt hash and provenance warning", async () => {
    const db = createExportPreviewDb();
    const env = { DB: db, DISCORD_BOT_SECRET: "test-secret", DISCORD_KICAD_REVIEWER_IDS: "maintainer-1" };
    const json = await postDiscord(env, { chat_id: "c1", user_id: "maintainer-1", text: "/kicad_export_preview" });

    assert.match(json.reply_text, /KiCad approved ecoEDA export preview/);
    assert.match(json.reply_text, /Rows: 1/);
    assert.match(json.reply_text, /Filter: approved only/);
    assert.match(json.reply_text, /SHA-256: [a-f0-9]{64}/);
    assert.match(json.reply_text, /CERN\/source columns included/);
    assert.match(json.reply_text, /TPS65994/);
  });
});

function createAuditPreviewDb() {
  const auditRows = [{
    event_id: 7,
    link_id: 3,
    master_part_id: 1,
    part_number: "TPS65994",
    part_name: "USB-C PD Controller",
    kicad_component_id: 20,
    symbol_name: "CERN_Power:TPS65994",
    footprint_name: "Package_QFN:QFN-56",
    previous_status: "suggested",
    next_status: "approved",
    current_review_status: "approved",
    reviewed_by: "discord:maintainer-1",
    reason: "Verified symbol and footprint",
    event_created_at: "2026-05-16T12:00:00.000Z",
    link_reviewed_at: "2026-05-16T12:00:00.000Z",
    source_slug: "cern-kicad-libs",
    source_url: "https://gitlab.com/ohwr/cern-kicad-libs",
    license_spdx: "CERN-OHL-P-2.0",
    upstream_commit: "abc123",
    kicad_version_family: "9.x",
  }];
  let queryCount = 0;
  return {
    _queryCount: () => queryCount,
    prepare(sql) {
      return {
        bind(...args) {
          return {
            async first() {
              return null;
            },
            async all() {
              if (sql.includes("FROM kicad_review_events kre")) {
                queryCount += 1;
                assert.equal(args[0], 5);
                return { results: auditRows };
              }
              return { results: [] };
            },
          };
        },
      };
    },
  };
}

describe("Discord KiCad review audit preview (Z106)", () => {
  it("blocks audit preview for non-maintainers before querying audit data", async () => {
    const db = createAuditPreviewDb();
    const env = { DB: db, DISCORD_BOT_SECRET: "test-secret", DISCORD_KICAD_REVIEWER_IDS: "maintainer-1" };
    const json = await postDiscord(env, { chat_id: "c1", user_id: "volunteer-1", text: "/kicad_audit_preview" });

    assert.match(json.reply_text, /audytu KiCad review.*tylko dla operatora\/maintainera/);
    assert.equal(db._queryCount(), 0);
  });

  it("returns maintainer audit preview with reviewer, reason, source, license and receipt hash", async () => {
    const db = createAuditPreviewDb();
    const env = { DB: db, DISCORD_BOT_SECRET: "test-secret", DISCORD_KICAD_REVIEWER_IDS: "maintainer-1" };
    const json = await postDiscord(env, { chat_id: "c1", user_id: "maintainer-1", text: "/kicad_audit_preview" });

    assert.match(json.reply_text, /KiCad review audit preview/);
    assert.match(json.reply_text, /Rows: 1/);
    assert.match(json.reply_text, /Filter: review events only/);
    assert.match(json.reply_text, /SHA-256: [a-f0-9]{64}/);
    assert.match(json.reply_text, /discord:maintainer-1/);
    assert.match(json.reply_text, /Verified symbol and footprint/);
    assert.match(json.reply_text, /cern-kicad-libs/);
    assert.match(json.reply_text, /CERN-OHL-P-2\.0/);
  });
});
