const REVIEW_STATUSES = new Set(["suggested", "approved", "rejected", "needs_more_data"]);
const MATCH_TYPES = new Set(["exact_mpn", "normalized_part_number", "manual", "ai_suggested"]);

function toIsoNow() {
  return new Date().toISOString();
}

function normalizeStatus(status, fallback = "suggested") {
  const normalized = String(status || fallback).trim().toLowerCase();
  if (!REVIEW_STATUSES.has(normalized)) {
    throw new Error(`Unsupported KiCad review status: ${status}`);
  }
  return normalized;
}

function normalizeMatchType(matchType) {
  const normalized = String(matchType || "ai_suggested").trim().toLowerCase();
  return MATCH_TYPES.has(normalized) ? normalized : "ai_suggested";
}

async function runSql(db, sql, bindings = []) {
  return await db.prepare(sql).bind(...bindings).run();
}

async function firstSql(db, sql, bindings = []) {
  return await db.prepare(sql).bind(...bindings).first();
}

async function allSql(db, sql, bindings = []) {
  const result = await db.prepare(sql).bind(...bindings).all();
  return result?.results || [];
}

function assertDb(env) {
  const db = env?.DB;
  if (!db) {
    throw new Error("D1 database is required for KiCad review operations.");
  }
  return db;
}

function assertRequired(value, label) {
  if (value === undefined || value === null || value === "") {
    throw new Error(`${label} is required.`);
  }
}

async function getExistingLink(db, masterPartId, kicadComponentId) {
  return await firstSql(
    db,
    `
    SELECT *
    FROM recycled_part_kicad_links
    WHERE master_part_id = ? AND kicad_component_id = ?
    LIMIT 1
    `,
    [masterPartId, kicadComponentId]
  );
}

async function recordReviewEvent(db, event) {
  await runSql(
    db,
    `
    INSERT INTO kicad_review_events (
      link_id,
      master_part_id,
      kicad_component_id,
      previous_status,
      next_status,
      reviewed_by,
      reason,
      created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    `,
    [
      event.link_id || null,
      event.master_part_id,
      event.kicad_component_id,
      event.previous_status || null,
      event.next_status,
      event.reviewed_by || null,
      event.reason || "",
      event.created_at || toIsoNow(),
    ]
  );
}

export async function suggestKicadLink(env, payload = {}) {
  const db = assertDb(env);
  const masterPartId = payload.master_part_id;
  const kicadComponentId = payload.kicad_component_id;
  assertRequired(masterPartId, "master_part_id");
  assertRequired(kicadComponentId, "kicad_component_id");

  const now = payload.created_at || toIsoNow();
  const matchType = normalizeMatchType(payload.match_type);
  const confidence = Number.isFinite(Number(payload.confidence)) ? Number(payload.confidence) : null;
  const reviewedBy = payload.reviewed_by || payload.suggested_by || "ai";
  const reason = payload.reason || "KiCad staging suggestion";
  const existing = await getExistingLink(db, masterPartId, kicadComponentId);

  if (existing) {
    await recordReviewEvent(db, {
      link_id: existing.id,
      master_part_id: masterPartId,
      kicad_component_id: kicadComponentId,
      previous_status: existing.review_status,
      next_status: existing.review_status,
      reviewed_by: reviewedBy,
      reason: `duplicate_suggestion: ${reason}`,
      created_at: now,
    });
    return { link_id: existing.id, status: existing.review_status, created: false };
  }

  await runSql(
    db,
    `
    INSERT INTO recycled_part_kicad_links (
      master_part_id,
      kicad_component_id,
      match_type,
      confidence,
      review_status,
      reviewed_by,
      reason,
      created_at,
      reviewed_at
    ) VALUES (?, ?, ?, ?, 'suggested', ?, ?, ?, NULL)
    `,
    [masterPartId, kicadComponentId, matchType, confidence, reviewedBy, reason, now]
  );

  const created = await getExistingLink(db, masterPartId, kicadComponentId);
  await recordReviewEvent(db, {
    link_id: created?.id || null,
    master_part_id: masterPartId,
    kicad_component_id: kicadComponentId,
    previous_status: null,
    next_status: "suggested",
    reviewed_by: reviewedBy,
    reason,
    created_at: now,
  });

  return { link_id: created?.id || null, status: "suggested", created: true };
}

export async function recordKicadReviewDecision(env, payload = {}) {
  const db = assertDb(env);
  const masterPartId = payload.master_part_id;
  const kicadComponentId = payload.kicad_component_id;
  assertRequired(masterPartId, "master_part_id");
  assertRequired(kicadComponentId, "kicad_component_id");
  assertRequired(payload.reviewed_by, "reviewed_by");

  const nextStatus = normalizeStatus(payload.review_status || payload.next_status);
  if (nextStatus === "approved" && payload.allow_ai_approval !== true && String(payload.reviewed_by).toLowerCase() === "ai") {
    throw new Error("AI cannot approve KiCad links without a human maintainer.");
  }

  const now = payload.reviewed_at || toIsoNow();
  const reason = payload.reason || "";
  const existing = await getExistingLink(db, masterPartId, kicadComponentId);
  if (!existing) {
    throw new Error("KiCad link suggestion not found for review decision.");
  }
  const previousStatus = existing.review_status;

  await runSql(
    db,
    `
    UPDATE recycled_part_kicad_links
    SET review_status = ?, reviewed_by = ?, reason = ?, reviewed_at = ?
    WHERE master_part_id = ? AND kicad_component_id = ?
    `,
    [nextStatus, payload.reviewed_by, reason, now, masterPartId, kicadComponentId]
  );

  await recordReviewEvent(db, {
    link_id: existing.id,
    master_part_id: masterPartId,
    kicad_component_id: kicadComponentId,
    previous_status: previousStatus,
    next_status: nextStatus,
    reviewed_by: payload.reviewed_by,
    reason,
    created_at: now,
  });

  return { link_id: existing.id, previous_status: previousStatus, status: nextStatus };
}

export async function listPendingKicadReviewLinks(env, options = {}) {
  const db = assertDb(env);
  const limit = Math.max(1, Math.min(Number(options.limit || 10), 50));
  return await allSql(
    db,
    `
    SELECT
      rpk.*,
      pm.part_number,
      pm.part_name,
      kc.symbol_name,
      kc.footprint_name,
      kc.mpn,
      src.source_slug,
      src.license_spdx
    FROM recycled_part_kicad_links rpk
    LEFT JOIN recycled_part_master pm ON pm.id = rpk.master_part_id
    LEFT JOIN kicad_library_components kc ON kc.id = rpk.kicad_component_id
    LEFT JOIN kicad_library_sources src ON src.id = kc.source_id
    WHERE rpk.review_status IN ('suggested', 'needs_more_data')
    ORDER BY rpk.created_at ASC
    LIMIT ?
    `,
    [limit]
  );
}

export function buildKicadReviewQueueReply(rows = []) {
  if (!rows.length) {
    return "✅ Brak linków KiCad oczekujących na review.";
  }
  const lines = ["🧾 KiCad review queue:", ""];
  for (const row of rows) {
    lines.push(`- #${row.id}: ${row.part_number || row.part_name || row.master_part_id} -> ${row.symbol_name || row.footprint_name || row.kicad_component_id}`);
    lines.push(`  Status: ${row.review_status}; Confidence: ${Math.round(Number(row.confidence || 0) * 100)}%; Źródło: ${row.source_slug || "unknown"}; Licencja: ${row.license_spdx || "unknown"}`);
  }
  lines.push("");
  lines.push("AI może sugerować, ale zatwierdzenie wymaga maintenera-człowieka.");
  return lines.join("\n");
}
