import { suggestKicadLink } from "./kicad_review.js";

function toText(value) {
  return value === undefined || value === null ? "" : String(value).trim();
}

function normalizePartNumber(value) {
  return toText(value).toUpperCase().replace(/[^A-Z0-9]/g, "");
}

function inferMounting(footprintName = "", packageName = "") {
  const haystack = `${footprintName} ${packageName}`.toLowerCase();
  if (haystack.includes("smd") || haystack.includes("qfn") || haystack.includes("qfp") || haystack.includes("bga") || haystack.includes("soic") || haystack.includes("sot")) return "smd";
  if (haystack.includes("tht") || haystack.includes("through") || haystack.includes("dip") || haystack.includes("to-220")) return "tht";
  return "unknown";
}

function inferGenus(footprintName = "") {
  const footprint = toText(footprintName);
  const library = footprint.includes(":") ? footprint.split(":")[0] : footprint;
  return library || "unknown";
}

function inferSpecies(packageName = "", footprintName = "") {
  const pkg = toText(packageName);
  if (pkg) return pkg;
  const footprint = toText(footprintName);
  if (footprint.includes(":")) return footprint.split(":").slice(1).join(":") || footprint;
  return footprint || "unknown";
}

export function buildKicadNormalizationSuggestion(component = {}) {
  return {
    species: inferSpecies(component.package, component.footprint_name),
    genus: inferGenus(component.footprint_name),
    mounting: inferMounting(component.footprint_name, component.package),
    source: "curator_b3_heuristic",
  };
}

function scoreMasterMatch(component, master) {
  const componentNorm = normalizePartNumber(component.normalized_part_number || component.mpn || component.symbol_name);
  const masterNorm = normalizePartNumber(master.normalized_part_number || master.part_number);
  if (componentNorm && masterNorm && componentNorm === masterNorm) return { confidence: 0.98, match_type: "exact_mpn" };
  const componentMpn = normalizePartNumber(component.mpn);
  const masterPart = normalizePartNumber(master.part_number);
  if (componentMpn && masterPart && componentMpn === masterPart) return { confidence: 0.94, match_type: "exact_mpn" };
  if (componentNorm && masterNorm && (componentNorm.includes(masterNorm) || masterNorm.includes(componentNorm))) {
    return { confidence: 0.76, match_type: "normalized_part_number" };
  }
  return { confidence: 0.55, match_type: "ai_suggested" };
}

async function loadVerifiedComponents(db, limit) {
  const result = await db.prepare(
    `SELECT
      kc.id,
      kc.symbol_name,
      kc.footprint_name,
      kc.mpn,
      kc.normalized_part_number,
      kc.description,
      kc.keywords,
      kc.package,
      kc.import_status,
      src.source_slug,
      src.upstream_commit,
      src.license_spdx
    FROM kicad_library_components kc
    LEFT JOIN kicad_library_sources src ON src.id = kc.source_id
    WHERE kc.import_status = 'verified'
    ORDER BY kc.id
    LIMIT ?`
  ).bind(limit).all();
  return result?.results || [];
}

async function findMasterCandidate(db, component) {
  const normalized = normalizePartNumber(component.normalized_part_number || component.mpn || component.symbol_name);
  if (!normalized) return null;
  return await db.prepare(
    `SELECT id, part_number, normalized_part_number, part_name, package, category
     FROM recycled_part_master
     WHERE UPPER(COALESCE(normalized_part_number, '')) = UPPER(?)
        OR UPPER(COALESCE(part_number, '')) = UPPER(?)
     ORDER BY
       CASE
         WHEN UPPER(COALESCE(normalized_part_number, '')) = UPPER(?) THEN 0
         WHEN UPPER(COALESCE(part_number, '')) = UPPER(?) THEN 1
         ELSE 2
       END,
       id
     LIMIT 1`
  ).bind(normalized, normalized, normalized, normalized).first();
}

function buildSuggestionReason(component, master, normalization) {
  return JSON.stringify({
    agent: "curator_b3",
    policy: "suggest_only_human_review_required",
    component_id: component.id,
    master_part_id: master.id,
    mpn: component.mpn || "",
    normalized_part_number: component.normalized_part_number || "",
    footprint_name: component.footprint_name || "",
    normalization,
  });
}

export async function curateKicadComponent(env, component, options = {}) {
  if (!env?.DB) return { success: false, reason: "no_db" };
  if (component.import_status !== "verified") {
    return { success: true, skipped: true, reason: "not_verified", component_id: component.id };
  }
  const master = await findMasterCandidate(env.DB, component);
  if (!master) {
    return { success: true, skipped: true, reason: "no_master_candidate", component_id: component.id };
  }
  const normalization = buildKicadNormalizationSuggestion(component);
  const score = scoreMasterMatch(component, master);
  const suggestion = await suggestKicadLink(env, {
    master_part_id: master.id,
    kicad_component_id: component.id,
    match_type: score.match_type,
    confidence: score.confidence,
    suggested_by: options.suggested_by || "ai",
    reason: buildSuggestionReason(component, master, normalization),
    created_at: options.now,
  });
  return {
    success: true,
    skipped: false,
    component_id: component.id,
    master_part_id: master.id,
    status: suggestion.status,
    created: suggestion.created,
    link_id: suggestion.link_id,
    normalization,
  };
}

export async function runKicadCurator(env, options = {}) {
  if (!env?.DB) return { success: false, reason: "no_db", suggested: 0, skipped: 0 };
  const limit = Number(options.limit || env.KICAD_CURATOR_BATCH_SIZE || 50);
  const rows = options.rows || await loadVerifiedComponents(env.DB, limit);
  const summary = { success: true, processed: 0, suggested: 0, existing: 0, skipped: 0 };
  for (const row of rows) {
    const result = await curateKicadComponent(env, row, options);
    summary.processed += 1;
    if (result.skipped) summary.skipped += 1;
    else if (result.created) summary.suggested += 1;
    else summary.existing += 1;
  }
  return summary;
}

export const kicadCuratorInternals = {
  normalizePartNumber,
  inferMounting,
  inferGenus,
  inferSpecies,
  scoreMasterMatch,
};
