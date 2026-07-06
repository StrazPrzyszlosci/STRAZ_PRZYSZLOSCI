import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { runKicadCurator, curateKicadComponent, buildKicadNormalizationSuggestion, kicadCuratorInternals } from "../cloudflare/src/kicad_curator.js";
import { recordKicadReviewDecision } from "../cloudflare/src/kicad_review.js";

function createMockDb({ components = [], masters = [] } = {}) {
  const links = [];
  const reviewEvents = [];
  return {
    components,
    masters,
    links,
    reviewEvents,
    masterUpdates: [],
    prepare(sql) {
      return {
        bind(...args) {
          return {
            all() {
              if (sql.includes("FROM kicad_library_components kc") && sql.includes("WHERE kc.import_status = 'verified'")) {
                const limit = args[0] || 50;
                return { results: components.filter((row) => row.import_status === "verified").slice(0, limit) };
              }
              return { results: [] };
            },
            first() {
              if (sql.includes("FROM recycled_part_master")) {
                const normalized = String(args[0] || "").toUpperCase();
                return masters.find((row) => String(row.normalized_part_number || row.part_number || "").toUpperCase() === normalized
                  || String(row.part_number || "").toUpperCase() === normalized) || null;
              }
              if (sql.includes("FROM recycled_part_kicad_links")) {
                const [master_part_id, kicad_component_id] = args;
                return links.find((row) => row.master_part_id === master_part_id && row.kicad_component_id === kicad_component_id) || null;
              }
              return null;
            },
            run() {
              if (sql.includes("INSERT INTO recycled_part_kicad_links")) {
                const [master_part_id, kicad_component_id, match_type, confidence, reviewed_by, reason, created_at] = args;
                links.push({ id: links.length + 1, master_part_id, kicad_component_id, match_type, confidence, review_status: "suggested", reviewed_by, reason, created_at, reviewed_at: null });
              } else if (sql.includes("UPDATE recycled_part_kicad_links")) {
                const [review_status, reviewed_by, reason, reviewed_at, master_part_id, kicad_component_id] = args;
                const link = links.find((row) => row.master_part_id === master_part_id && row.kicad_component_id === kicad_component_id);
                if (link) Object.assign(link, { review_status, reviewed_by, reason, reviewed_at });
              } else if (sql.includes("INSERT INTO kicad_review_events")) {
                const [link_id, master_part_id, kicad_component_id, previous_status, next_status, reviewed_by, reason, created_at] = args;
                reviewEvents.push({ link_id, master_part_id, kicad_component_id, previous_status, next_status, reviewed_by, reason, created_at });
              } else if (sql.includes("UPDATE recycled_part_master")) {
                this.masterUpdates.push({ sql, args });
              }
              return { changes: 1 };
            },
          };
        },
      };
    },
  };
}

function verifiedComponent(overrides = {}) {
  return {
    id: 101,
    import_status: "verified",
    symbol_name: "TPS65994AD",
    footprint_name: "Package_QFP:TQFP-64",
    mpn: "TPS65994AD",
    normalized_part_number: "TPS65994AD",
    package: "TQFP-64",
    description: "USB-C PD controller",
    keywords: "usb pd",
    ...overrides,
  };
}

const master = { id: 7, part_number: "TPS65994AD", normalized_part_number: "TPS65994AD", part_name: "USB-C PD controller" };

describe("KiCad curator B3", () => {
  it("creates only suggested KiCad links for verified records and records review event", async () => {
    const db = createMockDb({ components: [verifiedComponent()], masters: [master] });
    const result = await runKicadCurator({ DB: db }, { now: "2026-07-06T05:00:00.000Z" });

    assert.equal(result.processed, 1);
    assert.equal(result.suggested, 1);
    assert.equal(db.links.length, 1);
    assert.equal(db.links[0].review_status, "suggested");
    assert.equal(db.links[0].reviewed_by, "ai");
    assert.equal(db.reviewEvents[0].next_status, "suggested");
    assert.equal(db.masterUpdates.length, 0);
    assert.match(db.links[0].reason, /suggest_only_human_review_required/);
  });

  it("skips non-verified records and records no links", async () => {
    const db = createMockDb({ components: [verifiedComponent({ import_status: "needs_more_data" })], masters: [master] });
    const result = await curateKicadComponent({ DB: db }, db.components[0], { now: "2026-07-06T05:00:00.000Z" });
    assert.equal(result.skipped, true);
    assert.equal(result.reason, "not_verified");
    assert.equal(db.links.length, 0);
  });

  it("skips verified records without NSIP master candidate", async () => {
    const db = createMockDb({ components: [verifiedComponent()], masters: [] });
    const result = await runKicadCurator({ DB: db }, { now: "2026-07-06T05:00:00.000Z" });
    assert.equal(result.skipped, 1);
    assert.equal(db.links.length, 0);
  });

  it("keeps duplicate suggestions idempotent and records duplicate suggestion event", async () => {
    const db = createMockDb({ components: [verifiedComponent()], masters: [master] });
    await runKicadCurator({ DB: db }, { now: "2026-07-06T05:00:00.000Z" });
    const second = await runKicadCurator({ DB: db }, { now: "2026-07-06T05:01:00.000Z" });
    assert.equal(second.existing, 1);
    assert.equal(db.links.length, 1);
    assert.equal(db.reviewEvents.at(-1).next_status, "suggested");
    assert.match(db.reviewEvents.at(-1).reason, /duplicate_suggestion/);
  });

  it("blocks AI approval but allows human maintainer approval after curator suggestion", async () => {
    const db = createMockDb({ components: [verifiedComponent()], masters: [master] });
    await runKicadCurator({ DB: db }, { now: "2026-07-06T05:00:00.000Z" });
    await assert.rejects(
      () => recordKicadReviewDecision({ DB: db }, { master_part_id: 7, kicad_component_id: 101, review_status: "approved", reviewed_by: "ai" }),
      /AI cannot approve/
    );
    const approved = await recordKicadReviewDecision({ DB: db }, { master_part_id: 7, kicad_component_id: 101, review_status: "approved", reviewed_by: "maintainer" });
    assert.equal(approved.status, "approved");
    assert.equal(db.links[0].review_status, "approved");
  });

  it("builds deterministic normalization suggestion from package and footprint", () => {
    const suggestion = buildKicadNormalizationSuggestion(verifiedComponent());
    assert.deepEqual(suggestion, {
      species: "TQFP-64",
      genus: "Package_QFP",
      mounting: "smd",
      source: "curator_b3_heuristic",
    });
    assert.equal(kicadCuratorInternals.inferMounting("Package_DIP:DIP-8", ""), "tht");
  });
});
