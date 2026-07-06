import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  computeKicadImportDedupChecksum,
  ingestKicadComponents,
  parseScheduledKicadComponents,
  runScheduledKicadImport,
} from "../cloudflare/src/scheduled_kicad_importer.js";

function createMockDb() {
  const sources = [];
  const components = [];
  const events = [];
  return {
    sources,
    components,
    events,
    prepare(sql) {
      return {
        bind(...args) {
          return {
            run() {
              if (sql.includes("INSERT INTO kicad_library_sources")) {
                const [source_slug, source_url, license_spdx, upstream_commit, kicad_version_family, ingested_at, raw_manifest_json] = args;
                const existing = sources.find((row) => row.source_slug === source_slug);
                const next = { id: existing?.id || sources.length + 1, source_slug, source_url, license_spdx, upstream_commit, kicad_version_family, ingested_at, raw_manifest_json };
                if (existing) Object.assign(existing, next); else sources.push(next);
              } else if (sql.includes("INSERT INTO kicad_library_components")) {
                components.push({ id: components.length + 1, import_status: "staged", dedup_checksum: args[15], normalized_part_number: args[11], mpn: args[8], symbol_name: args[2] });
              } else if (sql.includes("INSERT INTO kicad_library_events")) {
                const [source_slug, upstream_commit, component_count, inserted_count, skipped_count, created_at] = args;
                events.push({ id: events.length + 1, kind: "ingest", source_slug, upstream_commit, component_count, inserted_count, skipped_count, created_at });
              }
              return { changes: 1 };
            },
            first() {
              if (sql.includes("FROM kicad_library_sources")) {
                const row = sources.find((source) => source.source_slug === args[0]);
                return row ? { id: row.id } : null;
              }
              if (sql.includes("FROM kicad_library_components")) {
                return components.find((row) => row.dedup_checksum === args[0]) || null;
              }
              return null;
            },
          };
        },
      };
    },
  };
}

const component = {
  source_slug: "cern-kicad-libs",
  source_url: "https://gitlab.com/ohwr/cern-kicad-libs",
  license_spdx: "CERN-OHL-P-2.0",
  upstream_commit: "fixture-commit",
  kicad_version_family: "9.x",
  library_name: "Power_Management",
  symbol_name: "TPS65994AD",
  footprint_name: "Package_QFP:TQFP-64",
  reference_prefix: "U",
  description: "USB-C controller",
  keywords: "usb pd",
  manufacturer: "Texas Instruments",
  mpn: "TPS65994AD",
  datasheet_url: "https://example.invalid/tps65994ad.pdf",
  package: "TQFP-64",
  raw_symbol_path: "symbols/Power_Management.kicad_sym",
  raw_footprint_path: "",
  raw_metadata_json: JSON.stringify({ properties: { MPN: "TPS65994AD" } }),
};

describe("scheduled KiCad importer B1", () => {
  it("computes stable dedup checksum from source, commit, symbol, footprint and mpn", async () => {
    const a = await computeKicadImportDedupChecksum(component);
    const b = await computeKicadImportDedupChecksum({ ...component, description: "changed non-key field" });
    const c = await computeKicadImportDedupChecksum({ ...component, mpn: "TPS65994" });
    assert.equal(a, b);
    assert.notEqual(a, c);
    assert.match(a, /^[a-f0-9]{64}$/);
  });

  it("inserts only new staged components and records one ingest event", async () => {
    const db = createMockDb();
    const env = { DB: db };
    const first = await ingestKicadComponents(env, [component], { now: "2026-07-06T02:17:00.000Z" });
    const second = await ingestKicadComponents(env, [component], { now: "2026-07-06T02:18:00.000Z" });

    assert.equal(first.success, true);
    assert.equal(first.inserted, 1);
    assert.equal(first.skipped, 0);
    assert.equal(second.inserted, 0);
    assert.equal(second.skipped, 1);
    assert.equal(db.components.length, 1);
    assert.equal(db.components[0].import_status, "staged");
    assert.equal(db.events.length, 2);
    assert.deepEqual(db.events.map((event) => event.kind), ["ingest", "ingest"]);
  });

  it("parses configured JSON rows for scheduled cron smoke", async () => {
    const rows = parseScheduledKicadComponents({ KICAD_IMPORT_COMPONENTS_JSON: JSON.stringify([component]) });
    assert.equal(rows.length, 1);
    const db = createMockDb();
    const result = await runScheduledKicadImport({ DB: db, KICAD_IMPORT_COMPONENTS_JSON: JSON.stringify(rows) }, { now: "2026-07-06T02:17:00.000Z" });
    assert.equal(result.inserted, 1);
    assert.equal(db.events[0].source_slug, "cern-kicad-libs");
  });

  it("fail-opens when DB binding is missing", async () => {
    const result = await ingestKicadComponents({}, [component]);
    assert.equal(result.success, false);
    assert.equal(result.reason, "no_db");
  });
});
