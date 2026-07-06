import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { runKicadVerifier, verifyKicadComponent, kicadVerifierInternals } from "../cloudflare/src/kicad_verifier.js";

function createMockDb(existingRows = []) {
  const rows = existingRows.map((row, index) => ({ import_status: "staged", ...row, id: row.id || index + 1 }));
  const events = [];
  const ocrQueue = [];
  return {
    rows,
    events,
    ocrQueue,
    prepare(sql) {
      return {
        bind(...args) {
          return {
            all() {
              if (sql.includes("FROM kicad_library_components kc") && sql.includes("WHERE COALESCE(kc.import_status")) {
                const limit = args[0] || 100;
                return { results: rows.filter((row) => (row.import_status || "staged") === "staged").slice(0, limit) };
              }
              return { results: [] };
            },
            first() {
              if (sql.includes("COUNT(*) AS n")) {
                const [id, normalized, upstream] = args;
                const n = rows.filter((row) => row.id !== id
                  && String(row.normalized_part_number || "").toUpperCase() === String(normalized || "").toUpperCase()
                  && String(row.upstream_commit || "") === String(upstream || "")).length;
                return { n };
              }
              return null;
            },
            run() {
              if (sql.includes("UPDATE kicad_library_components")) {
                const [import_status, verify_note, verified_at, id] = args;
                const row = rows.find((candidate) => candidate.id === id);
                if (row) Object.assign(row, { import_status, verify_note, verified_at });
              } else if (sql.includes("INSERT INTO kicad_library_events")) {
                const [source_slug, upstream_commit, component_id, previous_status, next_status, reason, created_at] = args;
                events.push({ kind: "verify", source_slug, upstream_commit, component_id, previous_status, next_status, reason, created_at });
              } else if (sql.includes("INSERT INTO kicad_ocr_queue")) {
                const [component_id, datasheet_url, reason, created_at] = args;
                const existing = ocrQueue.find((item) => item.component_id === component_id);
                const next = { component_id, datasheet_url, status: "pending", reason, created_at };
                if (existing) Object.assign(existing, next); else ocrQueue.push(next);
              }
              return { changes: 1 };
            },
          };
        },
      };
    },
  };
}

function validRow(overrides = {}) {
  return {
    id: 1,
    source_slug: "cern-kicad-libs",
    license_spdx: "CERN-OHL-P-2.0",
    upstream_commit: "fixture-commit",
    symbol_name: "TPS65994AD",
    footprint_name: "Package_QFP:TQFP-64",
    mpn: "TPS65994AD",
    normalized_part_number: "TPS65994AD",
    datasheet_url: "https://example.invalid/tps65994ad.pdf",
    raw_metadata_json: JSON.stringify({ properties: { MPN: "TPS65994AD" } }),
    import_status: "staged",
    ...overrides,
  };
}

describe("KiCad verifier B2", () => {
  it("marks valid staged row as verified and records verify event", async () => {
    const db = createMockDb([validRow()]);
    const result = await runKicadVerifier({ DB: db }, { now: "2026-07-06T04:00:00.000Z" });
    assert.equal(result.processed, 1);
    assert.equal(result.verified, 1);
    assert.equal(db.rows[0].import_status, "verified");
    assert.equal(db.rows[0].verify_note, "verify_ok");
    assert.equal(db.events[0].next_status, "verified");
  });

  it("marks schema failures as needs_more_data without dropping the row", async () => {
    const db = createMockDb([validRow({ mpn: "", normalized_part_number: "", license_spdx: "" })]);
    const result = await runKicadVerifier({ DB: db }, { now: "2026-07-06T04:00:00.000Z" });
    assert.equal(result.needs_more_data, 1);
    assert.equal(db.rows[0].import_status, "needs_more_data");
    assert.match(db.rows[0].verify_note, /^schema_missing:/);
    assert.equal(db.events[0].next_status, "needs_more_data");
  });

  it("marks duplicate normalized_part_number + upstream_commit as duplicate", async () => {
    const db = createMockDb([
      validRow({ id: 1, normalized_part_number: "TPS65994AD" }),
      validRow({ id: 2, normalized_part_number: "TPS65994AD", import_status: "verified" }),
    ]);
    const result = await verifyKicadComponent({ DB: db }, db.rows[0], { now: "2026-07-06T04:00:00.000Z" });
    assert.equal(result.next_status, "duplicate");
    assert.equal(db.rows[0].import_status, "duplicate");
    assert.equal(db.events[0].reason, "duplicate:normalized_part_number+upstream_commit");
  });

  it("defers scanned PDF OCR to queue and marks needs_ocr", async () => {
    const db = createMockDb([validRow({ raw_metadata_json: JSON.stringify({ ocr_required: true }) })]);
    const result = await runKicadVerifier({ DB: db }, { now: "2026-07-06T04:00:00.000Z" });
    assert.equal(result.needs_ocr, 1);
    assert.equal(db.rows[0].import_status, "needs_ocr");
    assert.equal(db.ocrQueue.length, 1);
    assert.equal(db.ocrQueue[0].status, "pending");
    assert.equal(db.events[0].next_status, "needs_ocr");
  });

  it("does not use AI and fail-opens when DB binding is missing", async () => {
    const result = await runKicadVerifier({}, { rows: [validRow()] });
    assert.equal(result.success, false);
    assert.equal(result.reason, "no_db");
  });

  it("internals recognize schema and scanned PDF deterministically", () => {
    assert.deepEqual(kicadVerifierInternals.validateComponentSchema(validRow()), []);
    assert.equal(kicadVerifierInternals.isLikelyScannedPdf(validRow({ raw_metadata_json: '{"pdf_kind":"scan"}' })), true);
    assert.equal(kicadVerifierInternals.isLikelyScannedPdf(validRow({ datasheet_url: "https://example.invalid/file.html" })), false);
  });
});
