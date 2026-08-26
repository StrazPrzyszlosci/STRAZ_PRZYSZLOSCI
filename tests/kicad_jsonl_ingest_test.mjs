import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  JSONL_INGEST_MAX_LINES,
  ingestKicadJsonlPayload,
  parseKicadJsonl,
  validateJsonlRow,
} from "../cloudflare/src/kicad_jsonl_ingest.js";

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
            async run() {
              if (sql.includes("INSERT INTO kicad_library_sources")) {
                const [source_slug] = args;
                const existing = sources.find((row) => row.source_slug === source_slug);
                const next = { id: existing?.id || sources.length + 1, source_slug };
                if (existing) Object.assign(existing, next); else sources.push(next);
              } else if (sql.includes("INSERT INTO kicad_library_components")) {
                components.push({
                  id: components.length + 1,
                  import_status: "staged",
                  dedup_checksum: args[15],
                });
              } else if (sql.includes("INSERT INTO kicad_library_events")) {
                const kind = sql.match(/VALUES\s*\('([a-z_]+)'/i)?.[1] || "unknown";
                events.push({ kind, inserted_count: args[3], skipped_count: args[4] });
              }
              return { changes: 1 };
            },
            first() {
              if (sql.includes("FROM kicad_library_sources")) {
                return sources.find((row) => row.source_slug === args[0]) || null;
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

const validRow = {
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
  datasheet_url: "https://example.invalid/ds.pdf",
  package: "TQFP-64",
  normalized_part_number: "TPS65994AD",
  raw_symbol_path: "symbols/Power_Management.kicad_sym",
  raw_footprint_path: "",
  raw_metadata_json: "{}",
};

describe("kicad jsonl ingestion T21", () => {
  it("parses NDJSON payload matching import_cern_kicad_library.py output", () => {
    const payload = `${JSON.stringify(validRow)}\n${JSON.stringify({ ...validRow, symbol_name: "LM5175", footprint_name: "" })}\n`;
    const { rows, errors } = parseKicadJsonl(payload);
    assert.equal(errors.length, 0);
    assert.equal(rows.length, 2);
    assert.equal(rows[1].symbol_name, "LM5175");
  });

  it("rejects lines violating the ingestion contract", () => {
    assert.deepEqual(validateJsonlRow(validRow), []);
    assert.ok(validateJsonlRow({ ...validRow, source_slug: "" }).includes("source_slug"));
    assert.ok(validateJsonlRow({ ...validRow, symbol_name: "", footprint_name: "" }).includes("symbol_name_or_footprint_name"));
    assert.ok(validateJsonlRow({ ...validRow, mpn: 42 }).includes("mpn_must_be_string"));

    const { errors } = parseKicadJsonl("not-json\n");
    assert.equal(errors.length, 1);
    assert.match(errors[0].error, /invalid_json/);

    const { errors: contractErrors } = parseKicadJsonl(`${JSON.stringify({ foo: "bar" })}\n`);
    assert.match(contractErrors[0].error, /contract_missing/);
  });

  it("enforces max line count and reports invalid lines without ingesting anything", () => {
    const many = Array.from({ length: JSONL_INGEST_MAX_LINES + 10 }, () => JSON.stringify(validRow)).join("\n");
    const { rows } = parseKicadJsonl(many);
    assert.equal(rows.length, JSONL_INGEST_MAX_LINES);
  });

  it("ingests staged-only rows with dedup and dual audit events", async () => {
    const db = createMockDb();
    const env = { DB: db };
    const payload = `${JSON.stringify(validRow)}\n`;
    const first = await ingestKicadJsonlPayload(env, payload, { now: "2026-08-26T10:00:00.000Z" });
    assert.equal(first.success, true);
    assert.equal(first.kind, "jsonl_ingest");
    assert.equal(first.inserted, 1);
    assert.equal(first.staged_only, true);

    const second = await ingestKicadJsonlPayload(env, payload, { now: "2026-08-26T10:01:00.000Z" });
    assert.equal(second.inserted, 0);
    assert.equal(second.skipped, 1);

    assert.equal(db.components.length, 1);
    assert.equal(db.components[0].import_status, "staged");
    const kinds = db.events.map((event) => event.kind).sort();
    assert.deepEqual(kinds, ["ingest", "ingest", "jsonl_ingest", "jsonl_ingest"]);
  });

  it("refuses the whole payload when any line is invalid", async () => {
    const db = createMockDb();
    const badPayload = `${JSON.stringify(validRow)}\n{"source_slug":"x"}\n`;
    const result = await ingestKicadJsonlPayload({ DB: db }, badPayload);
    assert.equal(result.success, false);
    assert.equal(result.reason, "invalid_payload");
    assert.equal(db.components.length, 0);
    assert.deepEqual(db.events, []);

    const empty = await ingestKicadJsonlPayload({ DB: db }, "\n\n");
    assert.equal(empty.reason, "empty_payload");
  });
});
