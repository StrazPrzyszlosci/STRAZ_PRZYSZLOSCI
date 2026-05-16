import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  buildKicadReviewMetricsReply,
  buildKicadReviewQueueReply,
  getKicadReviewQueueMetrics,
  listPendingKicadReviewLinks,
  recordKicadReviewDecision,
  suggestKicadLink,
} from "../cloudflare/src/kicad_review.js";

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
                  part_number: "TPS65994",
                  symbol_name: "TPS65994",
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

describe("KiCad human review ledger (Z90)", () => {
  it("creates suggestions and ledger events", async () => {
    const db = createReviewDb();
    const result = await suggestKicadLink({ DB: db }, {
      master_part_id: 1,
      kicad_component_id: 2,
      match_type: "exact_mpn",
      confidence: 0.97,
      suggested_by: "ai",
      reason: "Exact MPN match",
    });
    assert.equal(result.created, true);
    assert.equal(result.status, "suggested");
    assert.equal(db._links.length, 1);
    assert.equal(db._events[0].next_status, "suggested");
  });

  it("rejects AI approval but allows human maintainer approval", async () => {
    const db = createReviewDb();
    await suggestKicadLink({ DB: db }, { master_part_id: 1, kicad_component_id: 2 });
    await assert.rejects(
      () => recordKicadReviewDecision({ DB: db }, { master_part_id: 1, kicad_component_id: 2, review_status: "approved", reviewed_by: "ai" }),
      /AI cannot approve/
    );
    const result = await recordKicadReviewDecision({ DB: db }, {
      master_part_id: 1,
      kicad_component_id: 2,
      review_status: "approved",
      reviewed_by: "maintainer-01",
      reason: "Verified symbol and footprint",
    });
    assert.equal(result.previous_status, "suggested");
    assert.equal(result.status, "approved");
    assert.equal(db._links[0].review_status, "approved");
    assert.equal(db._events.at(-1).reviewed_by, "maintainer-01");
  });

  it("lists pending links and builds operator reply", async () => {
    const db = createReviewDb();
    await suggestKicadLink({ DB: db }, { master_part_id: 1, kicad_component_id: 2, confidence: 0.8 });
    const rows = await listPendingKicadReviewLinks({ DB: db });
    assert.equal(rows.length, 1);
    const reply = buildKicadReviewQueueReply(rows);
    assert.match(reply, /KiCad review queue/);
    assert.match(reply, /maintenera-człowieka/);
  });
});

describe("KiCad review queue SLA metrics (Z97)", () => {
  function createMetricsDb({ statusRows = [], decisionRows = [] } = {}) {
    return {
      prepare(sql) {
        return {
          bind(...args) {
            return {
              async all() {
                if (sql.includes("FROM recycled_part_kicad_links") && sql.includes("GROUP BY review_status")) {
                  return { results: statusRows };
                }
                if (sql.includes("FROM kicad_review_events") && sql.includes("GROUP BY next_status")) {
                  assert.equal(args.length, 1);
                  assert.match(args[0], /^2026-05-09T12:00:00/);
                  return { results: decisionRows };
                }
                return { results: [] };
              },
            };
          },
        };
      },
    };
  }

  it("returns empty read-only metrics for an empty queue", async () => {
    const metrics = await getKicadReviewQueueMetrics(
      { DB: createMetricsDb() },
      { now: "2026-05-16T12:00:00.000Z" }
    );
    const reply = buildKicadReviewMetricsReply(metrics);

    assert.equal(metrics.pending_count, 0);
    assert.equal(metrics.oldest_pending_at, null);
    assert.equal(metrics.decisions_last_7_days, 0);
    assert.equal(metrics.approval_ratio, null);
    assert.match(reply, /Read-only metrics/);
  });

  it("aggregates pending age, seven-day decisions and approval ratio", async () => {
    const metrics = await getKicadReviewQueueMetrics(
      {
        DB: createMetricsDb({
          statusRows: [
            { review_status: "suggested", count: 2, oldest_created_at: "2026-05-15T06:00:00.000Z" },
            { review_status: "needs_more_data", count: 1, oldest_created_at: "2026-05-14T12:00:00.000Z" },
            { review_status: "approved", count: 5, oldest_created_at: "2026-05-10T00:00:00.000Z" },
            { review_status: "rejected", count: 3, oldest_created_at: "2026-05-11T00:00:00.000Z" },
          ],
          decisionRows: [
            { next_status: "approved", count: 4 },
            { next_status: "rejected", count: 1 },
          ],
        }),
      },
      { now: "2026-05-16T12:00:00.000Z" }
    );
    const reply = buildKicadReviewMetricsReply(metrics);

    assert.equal(metrics.pending_count, 3);
    assert.equal(metrics.oldest_pending_at, "2026-05-14T12:00:00.000Z");
    assert.equal(metrics.oldest_pending_age_hours, 48);
    assert.equal(metrics.decisions_last_7_days, 5);
    assert.equal(metrics.approval_ratio, 0.8);
    assert.match(reply, /Pending: 3/);
    assert.match(reply, /Approval ratio: 80%/);
  });
});
