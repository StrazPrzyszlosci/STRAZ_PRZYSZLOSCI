import { describe, it } from "node:test";
import assert from "node:assert/strict";

import {
  buildApprovedKicadEcoedaCsv,
  buildEcoedaKicadProvenanceCsv,
  buildKicadReviewAuditCsv,
  buildKicadReviewAuditCsvFromDb,
  buildKicadExportReceipt,
  ECOEDA_WITH_KICAD_PROVENANCE_HEADERS,
  KICAD_REVIEW_AUDIT_HEADERS,
  listApprovedKicadEcoedaRows,
  listKicadReviewAuditEvents,
} from "../cloudflare/src/kicad_export.js";

function createExportDb() {
  const rows = [
    {
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
      kicad_description: "CERN staging description",
      source_slug: "cern-kicad-libs",
      source_url: "https://gitlab.com/ohwr/cern-kicad-libs",
      license_spdx: "CERN-OHL-P-2.0",
      upstream_commit: "abc123",
      kicad_version_family: "9.x",
      raw_symbol_path: "power/CERN_Power.kicad_sym",
      raw_footprint_path: "qfn.pretty/QFN-56.kicad_mod",
      review_status: "approved",
      reviewed_by: "discord:maintainer-1",
      reviewed_at: "2026-05-16T00:00:00.000Z",
      reason: "Verified symbol and footprint",
    },
  ];
  return {
    prepare(sql) {
      return {
        bind(...args) {
          return {
            async all() {
              assert.match(sql, /WHERE rpk\.review_status = 'approved'/);
              assert.equal(args[0], 100);
              return { results: rows };
            },
          };
        },
      };
    },
  };
}

describe("KiCad approved ecoEDA provenance export (Z91)", () => {
  it("keeps base ecoEDA headers first and appends optional provenance headers", () => {
    assert.deepEqual(ECOEDA_WITH_KICAD_PROVENANCE_HEADERS.slice(0, 3), ["Component Name", "Species", "Genus"]);
    assert.ok(ECOEDA_WITH_KICAD_PROVENANCE_HEADERS.includes("KiCad Source URL"));
    assert.ok(ECOEDA_WITH_KICAD_PROVENANCE_HEADERS.includes("KiCad License SPDX"));
  });

  it("builds CSV with approved CERN provenance without mutating base inventory contract", () => {
    const csv = buildEcoedaKicadProvenanceCsv([{ part_name: "NE555", source_slug: "cern-kicad-libs", license_spdx: "CERN-OHL-P-2.0", review_status: "approved" }]);

    assert.match(csv.split("\n")[0], /^Component Name,Species,Genus,SMD vs THT/);
    assert.match(csv, /KiCad Source Slug/);
    assert.match(csv, /CERN-OHL-P-2\.0/);
  });

  it("queries only approved KiCad review links and renders fallback KiCad symbol data", async () => {
    const env = { DB: createExportDb() };
    const rows = await listApprovedKicadEcoedaRows(env);
    const csv = await buildApprovedKicadEcoedaCsv(env);

    assert.equal(rows.length, 1);
    assert.match(csv, /CERN_Power:TPS65994/);
    assert.match(csv, /discord:maintainer-1/);
    assert.match(csv, /https:\/\/gitlab.com\/ohwr\/cern-kicad-libs/);
  });
});

function createAuditDb() {
  const rows = [
    {
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
      event_created_at: "2026-05-16T00:01:00.000Z",
      link_reviewed_at: "2026-05-16T00:01:00.000Z",
      source_slug: "cern-kicad-libs",
      source_url: "https://gitlab.com/ohwr/cern-kicad-libs",
      license_spdx: "CERN-OHL-P-2.0",
      upstream_commit: "abc123",
      kicad_version_family: "9.x",
      raw_symbol_path: "power/CERN_Power.kicad_sym",
      raw_footprint_path: "qfn.pretty/QFN-56.kicad_mod",
    },
  ];
  return {
    prepare(sql) {
      return {
        bind(...args) {
          return {
            async all() {
              assert.match(sql, /FROM kicad_review_events kre/);
              assert.match(sql, /kre\.next_status IN \('suggested', 'approved', 'rejected', 'needs_more_data'\)/);
              assert.match(sql, /LEFT JOIN recycled_part_kicad_links rpk/);
              assert.equal(args[0], 250);
              return { results: rows };
            },
          };
        },
      };
    },
  };
}

describe("KiCad review audit export (Z96)", () => {
  it("renders audit CSV with event, decision and provenance fields", () => {
    const csv = buildKicadReviewAuditCsv([
      {
        event_id: 7,
        master_part_id: 1,
        kicad_component_id: 20,
        previous_status: "suggested",
        next_status: "approved",
        reviewed_by: "discord:maintainer-1",
        reason: "human verified",
        source_slug: "cern-kicad-libs",
        license_spdx: "CERN-OHL-P-2.0",
      },
    ]);

    assert.deepEqual(KICAD_REVIEW_AUDIT_HEADERS.slice(0, 6), ["event_id", "link_id", "master_part_id", "part_number", "part_name", "kicad_component_id"]);
    assert.match(csv, /previous_status,next_status,current_review_status/);
    assert.match(csv, /discord:maintainer-1/);
    assert.match(csv, /CERN-OHL-P-2\.0/);
  });

  it("queries KiCad review events with source provenance without mutating production data", async () => {
    const env = { DB: createAuditDb() };
    const rows = await listKicadReviewAuditEvents(env);
    const csv = await buildKicadReviewAuditCsvFromDb(env);

    assert.equal(rows.length, 1);
    assert.equal(rows[0].next_status, "approved");
    assert.match(csv, /CERN_Power:TPS65994/);
    assert.match(csv, /Verified symbol and footprint/);
  });
});

describe("KiCad export hash receipt helper (Z108)", () => {
  it("creates a stable approved export receipt with sha256, row count and source tables", async () => {
    const csv = "Component Name,Species\nNE555,IC\nLM7805,IC\n";
    const receipt = await buildKicadExportReceipt(csv, {
      generated_at: "2026-05-16T12:00:00.000Z",
      export_kind: "approved_ecoeda_provenance",
    });

    assert.equal(receipt.generated_at, "2026-05-16T12:00:00.000Z");
    assert.equal(receipt.row_count, 2);
    assert.equal(receipt.status_filter, "approved");
    assert.equal(receipt.sha256, "48753ac96e3d34487849527b1682a4fd0c0b3a06338dfce11aa7557878786937");
    assert.deepEqual(receipt.source_tables, [
      "recycled_part_kicad_links",
      "recycled_part_master",
      "kicad_library_components",
      "kicad_library_sources",
    ]);
  });

  it("creates audit receipts without leaking env secrets or publishing data", async () => {
    const env = { GITHUB_TOKEN: "secret", DISCORD_BOT_SECRET: "secret" };
    const csv = buildKicadReviewAuditCsv([{ event_id: 1, next_status: "approved", reviewed_by: "maintainer" }]);
    const receipt = await buildKicadExportReceipt(csv, {
      generated_at: "2026-05-16T12:00:00.000Z",
      export_kind: "review_audit",
      env,
    });
    const serialized = JSON.stringify(receipt);

    assert.equal(receipt.status_filter, "review_events");
    assert.ok(receipt.source_tables.includes("kicad_review_events"));
    assert.equal(serialized.includes("secret"), false);
    assert.equal(Object.hasOwn(receipt, "upload_url"), false);
  });
});
