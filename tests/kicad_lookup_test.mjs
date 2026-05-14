import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  buildKicadLookupReply,
  findKicadLookupMatches,
  normalizeKicadPartNumber,
} from "../cloudflare/src/kicad_lookup.js";

function createMockDb({ masterRows = [], componentRows = [], throwOnComponents = false } = {}) {
  return {
    prepare(sql) {
      return {
        bind(..._args) {
          return {
            async all() {
              if (sql.includes("FROM recycled_part_master")) {
                return { results: masterRows };
              }
              if (sql.includes("FROM kicad_library_components")) {
                if (throwOnComponents) throw new Error("no such table: kicad_library_components");
                return { results: componentRows };
              }
              return { results: [] };
            },
          };
        },
      };
    },
  };
}

describe("KiCad lookup shared module (Z89)", () => {
  it("normalizes part numbers for exact matching", () => {
    assert.equal(normalizeKicadPartNumber(" TPS-65994 AD "), "TPS65994AD");
  });

  it("returns NSIP master matches before KiCad staging matches", async () => {
    const env = {
      DB: createMockDb({
        masterRows: [{
          id: 7,
          part_number: "TPS65994",
          normalized_part_number: "TPS65994",
          part_name: "USB-C PD controller",
          kicad_symbol: "Power_Management:TPS65994",
          kicad_footprint: "Package_QFN:QFN-56-1EP_7x7mm_P0.4mm",
          kicad_reference: "U",
        }],
        componentRows: [{
          id: 11,
          symbol_name: "TPS65994",
          footprint_name: "Package_QFN:QFN-56-1EP_7x7mm_P0.4mm",
          mpn: "TPS65994AD",
          normalized_part_number: "TPS65994AD",
          source_slug: "cern-kicad-libs",
          source_url: "https://gitlab.com/ohwr/cern-kicad-libs",
          license_spdx: "CERN-OHL-P-2.0",
        }],
      }),
    };

    const result = await findKicadLookupMatches(env, "TPS65994", { limit: 5 });
    assert.equal(result.error, null);
    assert.equal(result.matches.length, 2);
    assert.equal(result.matches[0].result_type, "nsip_master");
    assert.equal(result.matches[0].symbol_name, "Power_Management:TPS65994");
    assert.equal(result.matches[1].result_type, "kicad_component");
    assert.equal(result.matches[1].license_spdx, "CERN-OHL-P-2.0");
  });


  it("still returns NSIP master matches if KiCad staging query fails", async () => {
    const result = await findKicadLookupMatches({
      DB: createMockDb({
        masterRows: [{ id: 1, part_number: "LM3886", normalized_part_number: "LM3886", part_name: "Audio amplifier" }],
        throwOnComponents: true,
      }),
    }, "LM3886", { limit: 5 });
    assert.equal(result.matches.length, 1);
    assert.equal(result.matches[0].result_type, "nsip_master");
    assert.match(result.error, /no such table/);
  });

  it("builds a reply with provenance, license and review status", async () => {
    const reply = buildKicadLookupReply({
      query: "TPS65994",
      matches: [{
        result_type: "kicad_component",
        part_number: "TPS65994AD",
        part_name: "USB-C PD controller",
        symbol_name: "TPS65994",
        footprint_name: "Package_QFN:QFN-56-1EP_7x7mm_P0.4mm",
        reference_prefix: "U",
        source_slug: "cern-kicad-libs",
        license_spdx: "CERN-OHL-P-2.0",
        review_status: "suggested",
        confidence: 0.98,
        raw_path: "power/CERN_Power.kicad_sym",
      }],
    });
    assert.match(reply, /CERN-OHL-P-2\.0/);
    assert.match(reply, /suggested/);
    assert.match(reply, /human review/i);
  });

  it("fails closed to empty matches when staging tables are absent", async () => {
    const result = await findKicadLookupMatches({ DB: createMockDb({ throwOnComponents: true }) }, "ABC", { limit: 5 });
    assert.equal(result.matches.length, 0);
    assert.match(result.error, /no such table/);
  });
});
