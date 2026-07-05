import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  buildEcoedaCsv,
  buildEcoedaJson,
  exportApprovedEcoeda,
  listApprovedKicadLinks,
  __test__,
} from "../cloudflare/src/ecoeda_export.js";

function createExportDb(approvedRows = []) {
  return {
    prepare(sql) {
      return {
        bind(...args) {
          return {
            async all() {
              if (sql.includes("WHERE rpk.review_status = 'approved'")) {
                return { results: approvedRows.slice(0, args[0] || 500) };
              }
              return { results: [] };
            },
            async first() { return null; },
            async run() { return { changes: 0 }; },
          };
        },
      };
    },
  };
}

function sampleApprovedRow(overrides = {}) {
  return {
    link_id: 1,
    master_part_id: 10,
    kicad_component_id: 20,
    match_type: "exact_mpn",
    confidence: 0.95,
    review_status: "approved",
    reviewed_by: "maintainer-01",
    reviewed_at: "2026-07-05T00:00:00Z",
    part_number: "TPS65994",
    part_name: "USB-C PD controller",
    species: "IC",
    genus: "Interface",
    mounting: "SMD",
    value: "",
    keywords: "usb-c, pd",
    description: "TI USB-C PD controller",
    kicad_symbol: "Interface:TPS65994",
    kicad_footprint: "Package_QFP:TQFP-48",
    kicad_reference: "U",
    kicad_datasheet: "https://example.com/tps65994.pdf",
    quantity: 1,
    symbol_name: "TPS65994",
    footprint_name: "TQFP-48",
    reference_prefix: "U",
    symbol_description: "USB-C PD",
    datasheet_url: "https://example.com/tps65994.pdf",
    source_slug: "cern-kicad-libs",
    source_url: "https://gitlab.cern.ch/.../kicad",
    license_spdx: "CERN-OHL-P-2.0",
    upstream_commit: "abc123def",
    kicad_version_family: "7.0",
    ...overrides,
  };
}

describe("ecoEDA export with CERN provenance (Z91)", () => {
  it("exports only approved links", async () => {
    const db = createExportDb([sampleApprovedRow()]);
    const rows = await listApprovedKicadLinks({ DB: db });
    assert.equal(rows.length, 1);
    assert.equal(rows[0].review_status, "approved");
  });

  it("CSV contains core ecoEDA header + provenance columns, no regression", async () => {
    const row = sampleApprovedRow();
    const csv = buildEcoedaCsv([row]);
    const headerLine = csv.split("\n")[0];
    // Core ecoEDA fields present (no regression vs existing inventory.csv)
    assert.match(headerLine, /Component Name/);
    assert.match(headerLine, /Symbol-KICAD-URL/);
    assert.match(headerLine, /Datasheet/);
    // Provenance added
    assert.match(headerLine, /CERN-Source-Slug/);
    assert.match(headerLine, /CERN-License-SPDX/);
    assert.match(headerLine, /CERN-Upstream-Commit/);
    // Body carries values
    const bodyLines = csv.split("\n").slice(1);
    assert.match(bodyLines[0], /TPS65994/);
    assert.match(bodyLines[0], /cern-kicad-libs/);
    assert.match(bodyLines[0], /CERN-OHL-P-2.0/);
    assert.match(bodyLines[0], /abc123def/);
  });

  it("CSV without provenance keeps original ecoEDA header untouched", () => {
    const row = sampleApprovedRow();
    const csv = buildEcoedaCsv([row], { include_provenance: false });
    const headerLine = csv.split("\n")[0];
    assert.equal(headerLine, __test__.ECOEDA_HEADER.join(","));
    assert.doesNotMatch(headerLine, /CERN-Source-Slug/);
  });

  it("JSON export embeds provenance under provenance key", () => {
    const row = sampleApprovedRow();
    const out = buildEcoedaJson([row]);
    assert.equal(out.schema, "ecoeda_inventory_straz_v1");
    assert.equal(out.only_approved, true);
    assert.equal(out.count, 1);
    assert.equal(out.records[0]["Component Name"], "TPS65994");
    assert.equal(out.records[0].provenance["CERN-License-SPDX"], "CERN-OHL-P-2.0");
    assert.equal(out.records[0].provenance["NSIP-Reviewed-By"], "maintainer-01");
  });

  it("escapes CSV values containing commas and quotes", () => {
    const row = sampleApprovedRow({
      description: 'Has, comma and "quote"',
      keywords: "a,b,c",
    });
    const csv = buildEcoedaCsv([row]);
    const body = csv.split("\n")[1];
    // comma-containing field must be quoted
    assert.match(body, /"a,b,c"/);
    // quotes doubled inside quoted field
    assert.match(body, /"Has, comma and ""quote"""/);
  });

  it("exportApprovedEcoeda returns empty CSV with header when no approved rows", async () => {
    const db = createExportDb([]);
    const result = await exportApprovedEcoeda({ DB: db }, { format: "csv" });
    assert.equal(result.count, 0);
    assert.match(result.content, /Component Name/);
  });

  it("exportApprovedEcoeda JSON format returns schema wrapper", async () => {
    const db = createExportDb([sampleApprovedRow()]);
    const result = await exportApprovedEcoeda({ DB: db }, { format: "json" });
    assert.equal(result.format, "json");
    assert.equal(result.count, 1);
    const parsed = JSON.parse(result.content);
    assert.equal(parsed.schema, "ecoeda_inventory_straz_v1");
    assert.equal(parsed.records[0].provenance["CERN-Source-Slug"], "cern-kicad-libs");
  });

  it("confidence serialized as number when present, empty when null", () => {
    const row = sampleApprovedRow({ confidence: null });
    const out = buildEcoedaJson([row]);
    assert.equal(out.records[0].provenance["NSIP-Confidence"], "");
    const row2 = sampleApprovedRow({ confidence: 0.42 });
    const out2 = buildEcoedaJson([row2]);
    assert.equal(out2.records[0].provenance["NSIP-Confidence"], 0.42);
  });

  it("rejects export when DB missing", async () => {
    await assert.rejects(
      () => listApprovedKicadLinks({}),
      /D1 database is required/
    );
  });
});
