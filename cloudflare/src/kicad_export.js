const ECOEDA_BASE_HEADERS = [
  "Component Name",
  "Species",
  "Genus",
  "SMD vs THT",
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

const KICAD_PROVENANCE_HEADERS = [
  "KiCad Review Status",
  "KiCad Reviewed By",
  "KiCad Reviewed At",
  "KiCad Review Reason",
  "KiCad Source Slug",
  "KiCad Source URL",
  "KiCad License SPDX",
  "KiCad Upstream Commit",
  "KiCad Version Family",
  "KiCad Component ID",
  "KiCad Raw Symbol Path",
  "KiCad Raw Footprint Path",
];

export const ECOEDA_WITH_KICAD_PROVENANCE_HEADERS = [
  ...ECOEDA_BASE_HEADERS,
  ...KICAD_PROVENANCE_HEADERS,
];

function toIsoNow() {
  return new Date().toISOString();
}

async function allSql(db, sql, bindings = []) {
  const result = await db.prepare(sql).bind(...bindings).all();
  return result?.results || [];
}

function assertDb(env) {
  const db = env?.DB;
  if (!db) {
    throw new Error("D1 database is required for KiCad ecoEDA export operations.");
  }
  return db;
}

function text(value, fallback = "") {
  if (value === undefined || value === null) return fallback;
  return String(value);
}

function joinKeywords(value) {
  if (Array.isArray(value)) return value.join(", ");
  return text(value);
}

function csvEscape(value) {
  const raw = text(value);
  if (/[",\n\r]/.test(raw)) {
    return `"${raw.replace(/"/g, '""')}"`;
  }
  return raw;
}

export function buildEcoedaKicadProvenanceRow(row = {}) {
  return {
    "Component Name": text(row.part_name || row.part_number || row.symbol_name),
    "Species": text(row.species),
    "Genus": text(row.genus),
    "SMD vs THT": text(row.mounting || row.package),
    "Value": text(row.value),
    "Keywords": joinKeywords(row.keywords),
    "Description": text(row.description || row.kicad_description),
    "Symbol-KICAD-URL": text(row.kicad_symbol || row.symbol_name),
    "Footprint-KICAD-URL": text(row.kicad_footprint || row.footprint_name),
    "Datasheet": text(row.datasheet_url || row.kicad_datasheet_url),
    "Source": text(row.source_slug, "cern-kicad-libs"),
    "Teardown Link": text(row.source_url),
    "Quantity": text(row.quantity || 1),
    "PCB Designator": text(row.kicad_reference || row.reference_prefix),
    "KiCad Review Status": text(row.review_status),
    "KiCad Reviewed By": text(row.reviewed_by),
    "KiCad Reviewed At": text(row.reviewed_at),
    "KiCad Review Reason": text(row.reason),
    "KiCad Source Slug": text(row.source_slug),
    "KiCad Source URL": text(row.source_url),
    "KiCad License SPDX": text(row.license_spdx),
    "KiCad Upstream Commit": text(row.upstream_commit),
    "KiCad Version Family": text(row.kicad_version_family),
    "KiCad Component ID": text(row.kicad_component_id),
    "KiCad Raw Symbol Path": text(row.raw_symbol_path),
    "KiCad Raw Footprint Path": text(row.raw_footprint_path),
  };
}

export function buildEcoedaKicadProvenanceCsv(rows = []) {
  const output = [ECOEDA_WITH_KICAD_PROVENANCE_HEADERS.join(",")];
  for (const row of rows) {
    const mapped = buildEcoedaKicadProvenanceRow(row);
    output.push(ECOEDA_WITH_KICAD_PROVENANCE_HEADERS.map((header) => csvEscape(mapped[header])).join(","));
  }
  return `${output.join("\n")}\n`;
}

export async function listApprovedKicadEcoedaRows(env, options = {}) {
  const db = assertDb(env);
  const limit = Math.max(1, Math.min(Number(options.limit || 100), 1000));
  return await allSql(
    db,
    `
    SELECT
      pm.id AS master_part_id,
      pm.part_number,
      pm.part_name,
      pm.species,
      pm.genus,
      pm.mounting,
      pm.value,
      pm.keywords,
      pm.description,
      pm.datasheet_url,
      pm.kicad_symbol,
      pm.kicad_footprint,
      pm.kicad_reference,
      kc.id AS kicad_component_id,
      kc.symbol_name,
      kc.footprint_name,
      kc.reference_prefix,
      kc.description AS kicad_description,
      kc.datasheet_url AS kicad_datasheet_url,
      kc.package,
      kc.raw_symbol_path,
      kc.raw_footprint_path,
      src.source_slug,
      src.source_url,
      src.license_spdx,
      src.upstream_commit,
      src.kicad_version_family,
      rpk.review_status,
      rpk.reviewed_by,
      rpk.reviewed_at,
      rpk.reason
    FROM recycled_part_kicad_links rpk
    JOIN recycled_part_master pm ON pm.id = rpk.master_part_id
    JOIN kicad_library_components kc ON kc.id = rpk.kicad_component_id
    LEFT JOIN kicad_library_sources src ON src.id = kc.source_id
    WHERE rpk.review_status = 'approved'
    ORDER BY pm.part_name ASC, kc.symbol_name ASC
    LIMIT ?
    `,
    [limit]
  );
}

export async function buildApprovedKicadEcoedaCsv(env, options = {}) {
  const rows = await listApprovedKicadEcoedaRows(env, options);
  return buildEcoedaKicadProvenanceCsv(rows);
}

export const KICAD_REVIEW_AUDIT_HEADERS = [
  "event_id",
  "link_id",
  "master_part_id",
  "part_number",
  "part_name",
  "kicad_component_id",
  "symbol_name",
  "footprint_name",
  "previous_status",
  "next_status",
  "current_review_status",
  "reviewed_by",
  "reason",
  "event_created_at",
  "link_reviewed_at",
  "source_slug",
  "source_url",
  "license_spdx",
  "upstream_commit",
  "kicad_version_family",
  "raw_symbol_path",
  "raw_footprint_path",
];

export function buildKicadReviewAuditRow(row = {}) {
  return {
    event_id: text(row.event_id || row.id),
    link_id: text(row.link_id),
    master_part_id: text(row.master_part_id),
    part_number: text(row.part_number),
    part_name: text(row.part_name),
    kicad_component_id: text(row.kicad_component_id),
    symbol_name: text(row.symbol_name),
    footprint_name: text(row.footprint_name),
    previous_status: text(row.previous_status),
    next_status: text(row.next_status),
    current_review_status: text(row.current_review_status || row.review_status),
    reviewed_by: text(row.reviewed_by),
    reason: text(row.reason),
    event_created_at: text(row.event_created_at || row.created_at),
    link_reviewed_at: text(row.link_reviewed_at || row.reviewed_at),
    source_slug: text(row.source_slug),
    source_url: text(row.source_url),
    license_spdx: text(row.license_spdx),
    upstream_commit: text(row.upstream_commit),
    kicad_version_family: text(row.kicad_version_family),
    raw_symbol_path: text(row.raw_symbol_path),
    raw_footprint_path: text(row.raw_footprint_path),
  };
}

export function buildKicadReviewAuditCsv(rows = []) {
  const output = [KICAD_REVIEW_AUDIT_HEADERS.join(",")];
  for (const row of rows) {
    const mapped = buildKicadReviewAuditRow(row);
    output.push(KICAD_REVIEW_AUDIT_HEADERS.map((header) => csvEscape(mapped[header])).join(","));
  }
  return `${output.join("\n")}\n`;
}

export async function listKicadReviewAuditEvents(env, options = {}) {
  const db = assertDb(env);
  const limit = Math.max(1, Math.min(Number(options.limit || 250), 1000));
  return await allSql(
    db,
    `
    SELECT
      kre.id AS event_id,
      kre.link_id,
      kre.master_part_id,
      pm.part_number,
      pm.part_name,
      kre.kicad_component_id,
      kc.symbol_name,
      kc.footprint_name,
      kre.previous_status,
      kre.next_status,
      rpk.review_status AS current_review_status,
      kre.reviewed_by,
      kre.reason,
      kre.created_at AS event_created_at,
      rpk.reviewed_at AS link_reviewed_at,
      src.source_slug,
      src.source_url,
      src.license_spdx,
      src.upstream_commit,
      src.kicad_version_family,
      kc.raw_symbol_path,
      kc.raw_footprint_path
    FROM kicad_review_events kre
    LEFT JOIN recycled_part_kicad_links rpk ON rpk.id = kre.link_id
    LEFT JOIN recycled_part_master pm ON pm.id = kre.master_part_id
    LEFT JOIN kicad_library_components kc ON kc.id = kre.kicad_component_id
    LEFT JOIN kicad_library_sources src ON src.id = kc.source_id
    WHERE kre.master_part_id IS NOT NULL
      AND kre.kicad_component_id IS NOT NULL
      AND kre.next_status IN ('suggested', 'approved', 'rejected', 'needs_more_data')
    ORDER BY kre.created_at DESC, kre.id DESC
    LIMIT ?
    `,
    [limit]
  );
}

export async function buildKicadReviewAuditCsvFromDb(env, options = {}) {
  const rows = await listKicadReviewAuditEvents(env, options);
  return buildKicadReviewAuditCsv(rows);
}

async function sha256Hex(textValue) {
  const bytes = new TextEncoder().encode(text(textValue));
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  return Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, "0")).join("");
}

function csvDataRowCount(csvText) {
  const lines = text(csvText).split(/\r?\n/).filter((line) => line.length > 0);
  return Math.max(0, lines.length - 1);
}

export async function buildKicadExportReceipt(csvText, options = {}) {
  const exportKind = text(options.export_kind || options.exportKind || "approved_ecoeda_provenance");
  const defaultTables = exportKind === "review_audit"
    ? ["kicad_review_events", "recycled_part_kicad_links", "recycled_part_master", "kicad_library_components", "kicad_library_sources"]
    : ["recycled_part_kicad_links", "recycled_part_master", "kicad_library_components", "kicad_library_sources"];
  return {
    generated_at: options.generated_at || toIsoNow(),
    export_kind: exportKind,
    row_count: Number.isFinite(Number(options.row_count)) ? Number(options.row_count) : csvDataRowCount(csvText),
    sha256: await sha256Hex(csvText),
    status_filter: options.status_filter || (exportKind === "review_audit" ? "review_events" : "approved"),
    source_tables: Array.isArray(options.source_tables) ? options.source_tables : defaultTables,
  };
}
