// ecoeda_export.js — eksport approved linkow KiCad/NSIP do ecoEDA + JSON z provenance CERN.
// Z91: tylko review_status='approved'; nie nadpisuje istniejacego ecoEDA_inventory.csv
// (generuje osobny plik / returns obiekt — konsument decyduje gdzie zapisac).

const ECOEDA_HEADER = [
  "Component Name",
  "Species",
  "Genus",
  "Mounting",
  "Value",
  "Keywords",
  "Description",
  "Symbol-KICAD-URL",
  "Footprint-KICAD-URL",
  "Datasheet",
  "Source",
  "Teardown Link",
  "Quantity",
  "PCB Designator",
];

// Opcjonalne kolumny provenance (dodawane jako osobne pola, nie psuja dotychczasowych konsumentow).
const PROVENANCE_FIELDS = {
  source_slug: "CERN-Source-Slug",
  source_url: "CERN-Source-URL",
  license_spdx: "CERN-License-SPDX",
  upstream_commit: "CERN-Upstream-Commit",
  kicad_version_family: "CERN-KiCad-Version",
  match_type: "NSIP-Match-Type",
  confidence: "NSIP-Confidence",
  review_status: "NSIP-Review-Status",
  reviewed_by: "NSIP-Reviewed-By",
  reviewed_at: "NSIP-Reviewed-At",
};

function assertDb(env) {
  const db = env?.DB;
  if (!db) throw new Error("D1 database is required for ecoEDA export.");
  return db;
}

function escapeCsv(value) {
  if (value === null || value === undefined) return "";
  const s = String(value);
  if (/[",\n\r]/.test(s)) {
    return `"${s.replace(/"/g, '""')}"`;
  }
  return s;
}

function mapRowToEcoeda(row) {
  const partNumber = row.part_number || "";
  const partName = row.part_name || row.symbol_name || "";
  const componentName = partNumber || partName || `master_${row.master_part_id}`;
  return {
    "Component Name": componentName,
    "Species": row.species || "",
    "Genus": row.genus || "",
    "Mounting": row.mounting || "",
    "Value": row.value || "",
    "Keywords": row.keywords || "",
    "Description": row.description || row.symbol_description || "",
    "Symbol-KICAD-URL": row.symbol_name || row.kicad_symbol || "",
    "Footprint-KICAD-URL": row.footprint_name || row.kicad_footprint || "",
    "Datasheet": row.datasheet_url || row.kicad_datasheet || "",
    "Source": row.source_slug || "",
    "Teardown Link": row.source_url || "",
    "Quantity": row.quantity || 1,
    "PCB Designator": row.reference_prefix || "",
  };
}

function mapRowProvenance(row) {
  return {
    [PROVENANCE_FIELDS.source_slug]: row.source_slug || "",
    [PROVENANCE_FIELDS.source_url]: row.source_url || "",
    [PROVENANCE_FIELDS.license_spdx]: row.license_spdx || "",
    [PROVENANCE_FIELDS.upstream_commit]: row.upstream_commit || "",
    [PROVENANCE_FIELDS.kicad_version_family]: row.kicad_version_family || "",
    [PROVENANCE_FIELDS.match_type]: row.match_type || "",
    [PROVENANCE_FIELDS.confidence]: row.confidence !== null && row.confidence !== undefined ? Number(row.confidence) : "",
    [PROVENANCE_FIELDS.review_status]: row.review_status || "",
    [PROVENANCE_FIELDS.reviewed_by]: row.reviewed_by || "",
    [PROVENANCE_FIELDS.reviewed_at]: row.reviewed_at || "",
  };
}

export async function listApprovedKicadLinks(env, options = {}) {
  const db = assertDb(env);
  const limit = Math.max(1, Math.min(Number(options.limit || 500), 5000));
  const rows = await db
    .prepare(
      `
      SELECT
        rpk.id AS link_id,
        rpk.master_part_id,
        rpk.kicad_component_id,
        rpk.match_type,
        rpk.confidence,
        rpk.review_status,
        rpk.reviewed_by,
        rpk.reviewed_at,
        pm.part_number,
        pm.part_name,
        pm.species,
        pm.genus,
        pm.mounting,
        pm.value,
        pm.keywords,
        pm.description,
        pm.kicad_symbol,
        pm.kicad_footprint,
        pm.kicad_reference,
        pm.kicad_datasheet,
        pm.quantity,
        kc.symbol_name,
        kc.footprint_name,
        kc.reference_prefix,
        kc.description AS symbol_description,
        kc.datasheet_url,
        src.source_slug,
        src.source_url,
        src.license_spdx,
        src.upstream_commit,
        src.kicad_version_family
      FROM recycled_part_kicad_links rpk
      LEFT JOIN recycled_part_master pm ON pm.id = rpk.master_part_id
      LEFT JOIN kicad_library_components kc ON kc.id = rpk.kicad_component_id
      LEFT JOIN kicad_library_sources src ON src.id = kc.source_id
      WHERE rpk.review_status = 'approved'
      ORDER BY rpk.reviewed_at ASC
      LIMIT ?
      `
    )
    .bind(limit)
    .all();
  return rows?.results || [];
}

export function buildEcoedaCsv(rows, options = {}) {
  const includeProvenance = options.include_provenance !== false;
  const header = [...ECOEDA_HEADER];
  if (includeProvenance) {
    header.push(...Object.values(PROVENANCE_FIELDS));
  }
  const lines = [header.map(escapeCsv).join(",")];
  for (const row of rows) {
    const ecoeda = mapRowToEcoeda(row);
    const line = ECOEDA_HEADER.map((col) => escapeCsv(ecoeda[col]));
    if (includeProvenance) {
      const prov = mapRowProvenance(row);
      for (const key of Object.keys(PROVENANCE_FIELDS)) {
        line.push(escapeCsv(prov[PROVENANCE_FIELDS[key]]));
      }
    }
    lines.push(line.join(","));
  }
  return lines.join("\n");
}

export function buildEcoedaJson(rows, options = {}) {
  const includeProvenance = options.include_provenance !== false;
  const records = rows.map((row) => {
    const ecoeda = mapRowToEcoeda(row);
    const record = { ...ecoeda };
    if (includeProvenance) {
      record.provenance = mapRowProvenance(row);
    }
    return record;
  });
  return {
    schema: "ecoeda_inventory_straz_v1",
    generated_at: new Date().toISOString(),
    only_approved: true,
    count: records.length,
    records,
  };
}

export async function exportApprovedEcoeda(env, options = {}) {
  const format = (options.format || "csv").toLowerCase();
  const rows = await listApprovedKicadLinks(env, options);
  if (!rows.length) {
    return {
      format,
      count: 0,
      content: format === "json" ? JSON.stringify({ schema: "ecoeda_inventory_straz_v1", count: 0, records: [] }) : ECOEDA_HEADER.map(escapeCsv).join(","),
    };
  }
  const content = format === "json"
    ? JSON.stringify(buildEcoedaJson(rows, options), null, 2)
    : buildEcoedaCsv(rows, options);
  return { format, count: rows.length, content };
}

export const __test__ = {
  ECOEDA_HEADER,
  PROVENANCE_FIELDS,
  escapeCsv,
  mapRowToEcoeda,
  mapRowProvenance,
};
