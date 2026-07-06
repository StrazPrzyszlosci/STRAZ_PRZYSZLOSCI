function toText(value) {
  return value === undefined || value === null ? "" : String(value).trim();
}

function normalizePartNumber(value) {
  return toText(value).toUpperCase().replace(/[^A-Z0-9]/g, "");
}

function isLikelyScannedPdf(row) {
  const url = toText(row.datasheet_url).toLowerCase();
  if (!url.endsWith(".pdf") && !url.includes(".pdf?")) return false;
  const metadata = toText(row.raw_metadata_json).toLowerCase();
  return metadata.includes('"ocr_required":true')
    || metadata.includes('"scan":true')
    || metadata.includes('"pdf_kind":"scan"')
    || metadata.includes('image-only')
    || metadata.includes('scanned');
}

function validateComponentSchema(row) {
  const missing = [];
  if (!toText(row.symbol_name) && !toText(row.footprint_name)) missing.push("symbol_name_or_footprint_name");
  if (!toText(row.mpn) && !toText(row.normalized_part_number)) missing.push("mpn_or_normalized_part_number");
  if (!toText(row.license_spdx)) missing.push("license_spdx");
  if (!toText(row.upstream_commit)) missing.push("upstream_commit");
  if (row.schema_version !== undefined && toText(row.schema_version) !== "v1") missing.push("schema_version_v1");
  return missing;
}

async function recordVerifierEvent(db, row, previousStatus, nextStatus, reason, now) {
  await db.prepare(
    `INSERT INTO kicad_library_events (
      kind, source_slug, upstream_commit, component_count, inserted_count, skipped_count, component_id,
      previous_status, next_status, reason, created_at
    ) VALUES ('verify', ?, ?, 1, 0, 0, ?, ?, ?, ?, ?)`
  ).bind(
    toText(row.source_slug),
    toText(row.upstream_commit),
    row.id,
    previousStatus || "staged",
    nextStatus,
    reason,
    now
  ).run();
}

async function updateComponentStatus(db, row, nextStatus, reason, now) {
  await db.prepare(
    `UPDATE kicad_library_components
     SET import_status = ?, verify_note = ?, verified_at = ?
     WHERE id = ?`
  ).bind(nextStatus, reason, now, row.id).run();
}

async function enqueueOcr(db, row, reason, now) {
  await db.prepare(
    `INSERT INTO kicad_ocr_queue (component_id, datasheet_url, status, reason, created_at)
     VALUES (?, ?, 'pending', ?, ?)
     ON CONFLICT(component_id) DO UPDATE SET
       datasheet_url=excluded.datasheet_url,
       status='pending',
       reason=excluded.reason,
       created_at=excluded.created_at`
  ).bind(row.id, toText(row.datasheet_url), reason, now).run();
}

async function loadStagedComponents(db, limit) {
  const result = await db.prepare(
    `SELECT
      kc.id,
      kc.symbol_name,
      kc.footprint_name,
      kc.mpn,
      kc.normalized_part_number,
      kc.datasheet_url,
      kc.raw_metadata_json,
      kc.import_status,
      kc.created_at,
      src.source_slug,
      src.license_spdx,
      src.upstream_commit,
      src.kicad_version_family
    FROM kicad_library_components kc
    LEFT JOIN kicad_library_sources src ON src.id = kc.source_id
    WHERE COALESCE(kc.import_status, 'staged') = 'staged'
    ORDER BY kc.id
    LIMIT ?`
  ).bind(limit).all();
  return result?.results || [];
}

async function countDuplicates(db, row) {
  const normalized = toText(row.normalized_part_number) || normalizePartNumber(row.mpn || row.symbol_name || row.footprint_name);
  if (!normalized || !toText(row.upstream_commit)) return 0;
  const result = await db.prepare(
    `SELECT COUNT(*) AS n
     FROM kicad_library_components kc
     LEFT JOIN kicad_library_sources src ON src.id = kc.source_id
     WHERE kc.id <> ?
       AND UPPER(COALESCE(kc.normalized_part_number, '')) = UPPER(?)
       AND COALESCE(src.upstream_commit, '') = ?`
  ).bind(row.id, normalized, row.upstream_commit).first();
  return Number(result?.n || 0);
}

export async function verifyKicadComponent(env, row, options = {}) {
  if (!env?.DB) return { success: false, reason: "no_db" };
  const now = options.now || new Date().toISOString();
  const previousStatus = row.import_status || "staged";
  let nextStatus = "verified";
  let reason = "verify_ok";

  const schemaMissing = validateComponentSchema(row);
  if (schemaMissing.length) {
    nextStatus = "needs_more_data";
    reason = `schema_missing:${schemaMissing.join(",")}`;
  } else if (await countDuplicates(env.DB, row) > 0) {
    nextStatus = "duplicate";
    reason = "duplicate:normalized_part_number+upstream_commit";
  } else if (isLikelyScannedPdf(row)) {
    nextStatus = "needs_ocr";
    reason = "ocr_deferred:scanned_pdf";
    await enqueueOcr(env.DB, row, reason, now);
  }

  await updateComponentStatus(env.DB, row, nextStatus, reason, now);
  await recordVerifierEvent(env.DB, row, previousStatus, nextStatus, reason, now);
  return { success: true, component_id: row.id, previous_status: previousStatus, next_status: nextStatus, reason };
}

export async function runKicadVerifier(env, options = {}) {
  if (!env?.DB) return { success: false, reason: "no_db", verified: 0, needs_more_data: 0, duplicate: 0, needs_ocr: 0 };
  const limit = Number(options.limit || env.KICAD_VERIFIER_BATCH_SIZE || 100);
  const rows = options.rows || await loadStagedComponents(env.DB, limit);
  const summary = { success: true, processed: 0, verified: 0, needs_more_data: 0, duplicate: 0, needs_ocr: 0 };
  for (const row of rows) {
    const result = await verifyKicadComponent(env, row, options);
    summary.processed += 1;
    if (result.next_status === "verified") summary.verified += 1;
    if (result.next_status === "needs_more_data") summary.needs_more_data += 1;
    if (result.next_status === "duplicate") summary.duplicate += 1;
    if (result.next_status === "needs_ocr") summary.needs_ocr += 1;
  }
  return summary;
}

export const kicadVerifierInternals = {
  isLikelyScannedPdf,
  validateComponentSchema,
  normalizePartNumber,
};
