const DEFAULT_SOURCE_SLUG = "cern-kicad-libs";
const DEFAULT_SOURCE_URL = "https://gitlab.com/ohwr/cern-kicad-libs";
const DEFAULT_LICENSE_SPDX = "CERN-OHL-P-2.0";
const DEFAULT_KICAD_VERSION_FAMILY = "9.x";

function toText(value) {
  return value === undefined || value === null ? "" : String(value);
}

function normalizePartNumber(value) {
  return toText(value).toUpperCase().replace(/[^A-Z0-9]/g, "");
}

export async function computeKicadImportDedupChecksum(row) {
  const payload = [
    row.source_slug,
    row.upstream_commit,
    row.symbol_name,
    row.footprint_name,
    row.mpn,
  ].map(toText).join("\u001f");
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(payload));
  return Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, "0")).join("");
}

export function parseScheduledKicadComponents(env) {
  const raw = env?.KICAD_IMPORT_COMPONENTS_JSON || "";
  if (!raw.trim()) return [];
  const parsed = JSON.parse(raw);
  if (!Array.isArray(parsed)) {
    throw new Error("KICAD_IMPORT_COMPONENTS_JSON must be a JSON array.");
  }
  return parsed;
}

export function buildKicadSourceMetadata(env, rows = []) {
  const first = rows[0] || {};
  return {
    source_slug: env?.KICAD_IMPORT_SOURCE_SLUG || first.source_slug || DEFAULT_SOURCE_SLUG,
    source_url: env?.KICAD_IMPORT_SOURCE_URL || first.source_url || DEFAULT_SOURCE_URL,
    license_spdx: env?.KICAD_IMPORT_LICENSE_SPDX || first.license_spdx || DEFAULT_LICENSE_SPDX,
    upstream_commit: env?.KICAD_IMPORT_UPSTREAM_COMMIT || first.upstream_commit || "unknown",
    kicad_version_family: env?.KICAD_IMPORT_VERSION_FAMILY || first.kicad_version_family || DEFAULT_KICAD_VERSION_FAMILY,
  };
}

async function ensureSource(db, metadata, now) {
  await db.prepare(
    `INSERT INTO kicad_library_sources (
      source_slug, source_url, license_spdx, upstream_commit, kicad_version_family, ingested_at, raw_manifest_json
    ) VALUES (?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(source_slug) DO UPDATE SET
      source_url=excluded.source_url,
      license_spdx=excluded.license_spdx,
      upstream_commit=excluded.upstream_commit,
      kicad_version_family=excluded.kicad_version_family,
      ingested_at=excluded.ingested_at,
      raw_manifest_json=excluded.raw_manifest_json`
  ).bind(
    metadata.source_slug,
    metadata.source_url,
    metadata.license_spdx,
    metadata.upstream_commit,
    metadata.kicad_version_family,
    now,
    JSON.stringify(metadata)
  ).run();
  const source = await db.prepare(
    `SELECT id FROM kicad_library_sources WHERE source_slug = ?`
  ).bind(metadata.source_slug).first();
  return source?.id || null;
}

export async function ingestKicadComponents(env, rows, options = {}) {
  if (!env?.DB) return { success: false, reason: "no_db", inserted: 0, skipped: 0 };
  const now = options.now || new Date().toISOString();
  const source = buildKicadSourceMetadata(env, rows);
  const sourceId = await ensureSource(env.DB, source, now);
  let inserted = 0;
  let skipped = 0;

  for (const inputRow of rows) {
    const row = { ...source, ...inputRow };
    const dedupChecksum = await computeKicadImportDedupChecksum(row);
    const existing = await env.DB.prepare(
      `SELECT id FROM kicad_library_components WHERE dedup_checksum = ?`
    ).bind(dedupChecksum).first();
    if (existing) {
      skipped += 1;
      continue;
    }
    await env.DB.prepare(
      `INSERT INTO kicad_library_components (
        source_id, library_name, symbol_name, footprint_name, reference_prefix,
        description, keywords, manufacturer, mpn, datasheet_url, package,
        normalized_part_number, raw_symbol_path, raw_footprint_path, raw_metadata_json,
        import_status, dedup_checksum, created_at
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'staged', ?, ?)`
    ).bind(
      sourceId,
      toText(row.library_name),
      toText(row.symbol_name),
      toText(row.footprint_name),
      toText(row.reference_prefix),
      toText(row.description),
      toText(row.keywords),
      toText(row.manufacturer),
      toText(row.mpn),
      toText(row.datasheet_url),
      toText(row.package),
      toText(row.normalized_part_number) || normalizePartNumber(row.mpn || row.symbol_name || row.footprint_name),
      toText(row.raw_symbol_path),
      toText(row.raw_footprint_path),
      row.raw_metadata_json || JSON.stringify({ source_slug: row.source_slug }),
      dedupChecksum,
      now
    ).run();
    inserted += 1;
  }

  await env.DB.prepare(
    `INSERT INTO kicad_library_events (kind, source_slug, upstream_commit, component_count, inserted_count, skipped_count, created_at)
     VALUES ('ingest', ?, ?, ?, ?, ?, ?)`
  ).bind(source.source_slug, source.upstream_commit, rows.length, inserted, skipped, now).run();

  return { success: true, kind: "ingest", source_slug: source.source_slug, upstream_commit: source.upstream_commit, count: rows.length, inserted, skipped };
}

export async function runScheduledKicadImport(env, options = {}) {
  const rows = options.rows || parseScheduledKicadComponents(env);
  if (!rows.length) {
    return { success: true, kind: "ingest", count: 0, inserted: 0, skipped: 0, reason: "no_components_configured" };
  }
  return ingestKicadComponents(env, rows, options);
}
