export function normalizeKicadPartNumber(value) {
  return String(value || "").toUpperCase().replace(/[^A-Z0-9]/g, "");
}

function normalizeWhitespace(value) {
  return String(value || "").replace(/\s+/g, " ").trim();
}

function rowText(value, fallback = "") {
  return normalizeWhitespace(value) || fallback;
}

function confidenceForRow(row, normalizedQuery, queryText) {
  const normalizedPart = normalizeKicadPartNumber(row.normalized_part_number || row.part_number || row.mpn || row.symbol_name);
  if (normalizedPart && normalizedPart === normalizedQuery) return 0.98;
  if (String(row.part_number || row.mpn || "").toLowerCase() === queryText.toLowerCase()) return 0.94;
  if (String(row.symbol_name || "").toLowerCase() === queryText.toLowerCase()) return 0.9;
  return 0.72;
}

function mapMasterRow(row, normalizedQuery, queryText) {
  return {
    result_type: "nsip_master",
    master_part_id: row.id || row.master_part_id || null,
    kicad_component_id: row.kicad_component_id || null,
    part_number: row.part_number || row.mpn || row.symbol_name || queryText,
    part_name: row.part_name || row.description || row.part_number || queryText,
    symbol_name: row.kicad_symbol || row.symbol_name || "",
    footprint_name: row.kicad_footprint || row.footprint_name || "",
    reference_prefix: row.kicad_reference || row.reference_prefix || "",
    source_slug: row.source_slug || "nsip-recycled-part-master",
    source_url: row.source_url || "",
    license_spdx: row.license_spdx || "NSIP/curated",
    review_status: row.review_status || (row.kicad_component_id ? "approved_or_linked" : "local_master"),
    confidence: confidenceForRow(row, normalizedQuery, queryText),
    raw_path: row.raw_symbol_path || row.raw_footprint_path || "",
  };
}

function mapKicadRow(row, normalizedQuery, queryText) {
  return {
    result_type: "kicad_component",
    master_part_id: row.master_part_id || null,
    kicad_component_id: row.id || row.kicad_component_id || null,
    part_number: row.mpn || row.symbol_name || row.footprint_name || queryText,
    part_name: row.description || row.symbol_name || row.footprint_name || queryText,
    symbol_name: row.symbol_name || "",
    footprint_name: row.footprint_name || "",
    reference_prefix: row.reference_prefix || "",
    source_slug: row.source_slug || "cern-kicad-libs",
    source_url: row.source_url || "https://gitlab.com/ohwr/cern-kicad-libs",
    license_spdx: row.license_spdx || "CERN-OHL-P-2.0",
    review_status: row.review_status || "suggested",
    confidence: confidenceForRow(row, normalizedQuery, queryText),
    raw_path: row.raw_symbol_path || row.raw_footprint_path || "",
  };
}

async function queryAll(db, sql, bindings) {
  const result = await db.prepare(sql).bind(...bindings).all();
  return result?.results || [];
}

export async function findKicadLookupMatches(env, queryText, options = {}) {
  const db = env?.DB;
  const query = normalizeWhitespace(queryText);
  const limit = Math.max(1, Math.min(Number(options.limit || 5), 10));
  if (!db || !query) {
    return { query, matches: [], error: db ? null : "no_db" };
  }

  const normalizedQuery = normalizeKicadPartNumber(query);
  const wildcard = `%${query}%`;

  const errors = [];
  let masterRows = [];
  let componentRows = [];

  try {
    masterRows = await queryAll(
      db,
      `
      SELECT
        pm.id,
        pm.part_number,
        pm.normalized_part_number,
        pm.part_name,
        pm.description,
        pm.kicad_symbol,
        pm.kicad_footprint,
        pm.kicad_reference
      FROM recycled_part_master pm
      WHERE
        LOWER(COALESCE(pm.normalized_part_number, '')) = LOWER(?)
        OR LOWER(COALESCE(pm.part_number, '')) = LOWER(?)
        OR LOWER(COALESCE(pm.part_name, '')) = LOWER(?)
        OR LOWER(COALESCE(pm.part_number, '')) LIKE LOWER(?)
        OR LOWER(COALESCE(pm.part_name, '')) LIKE LOWER(?)
      ORDER BY
        CASE
          WHEN LOWER(COALESCE(pm.normalized_part_number, '')) = LOWER(?) THEN 0
          WHEN LOWER(COALESCE(pm.part_number, '')) = LOWER(?) THEN 1
          ELSE 2
        END,
        pm.part_name ASC
      LIMIT ?
      `,
      [normalizedQuery, query, query, wildcard, wildcard, normalizedQuery, query, limit]
    );
  } catch (error) {
    errors.push(error instanceof Error ? error.message : String(error));
  }

  try {
    componentRows = await queryAll(
      db,
      `
      SELECT
        kc.*,
        src.source_slug,
        src.source_url,
        src.license_spdx,
        rpk.master_part_id,
        rpk.review_status
      FROM kicad_library_components kc
      LEFT JOIN kicad_library_sources src ON src.id = kc.source_id
      LEFT JOIN recycled_part_kicad_links rpk ON rpk.kicad_component_id = kc.id
      WHERE
        LOWER(COALESCE(kc.normalized_part_number, '')) = LOWER(?)
        OR LOWER(COALESCE(kc.mpn, '')) = LOWER(?)
        OR LOWER(COALESCE(kc.symbol_name, '')) = LOWER(?)
        OR LOWER(COALESCE(kc.symbol_name, '')) LIKE LOWER(?)
        OR LOWER(COALESCE(kc.footprint_name, '')) LIKE LOWER(?)
        OR LOWER(COALESCE(kc.description, '')) LIKE LOWER(?)
        OR LOWER(COALESCE(kc.keywords, '')) LIKE LOWER(?)
      ORDER BY
        CASE
          WHEN LOWER(COALESCE(kc.normalized_part_number, '')) = LOWER(?) THEN 0
          WHEN LOWER(COALESCE(kc.mpn, '')) = LOWER(?) THEN 1
          WHEN LOWER(COALESCE(kc.symbol_name, '')) = LOWER(?) THEN 2
          ELSE 3
        END,
        kc.symbol_name ASC
      LIMIT ?
      `,
      [normalizedQuery, query, query, wildcard, wildcard, wildcard, wildcard, normalizedQuery, query, query, limit]
    );
  } catch (error) {
    errors.push(error instanceof Error ? error.message : String(error));
  }

    const matches = [
      ...masterRows.map((row) => mapMasterRow(row, normalizedQuery, query)),
      ...componentRows.map((row) => mapKicadRow(row, normalizedQuery, query)),
    ];

    const deduped = [];
    const seen = new Set();
    for (const match of matches) {
      const key = `${match.result_type}:${match.master_part_id || ""}:${match.kicad_component_id || ""}:${match.part_number}:${match.symbol_name}:${match.footprint_name}`;
      if (!seen.has(key)) {
        seen.add(key);
        deduped.push(match);
      }
      if (deduped.length >= limit) break;
    }

    return { query, matches: deduped, error: errors.length ? errors.join("; ") : null };
}

export function buildKicadLookupReply(lookupResult, options = {}) {
  const query = lookupResult?.query || options.query || "zapytanie";
  const matches = Array.isArray(lookupResult?.matches) ? lookupResult.matches : [];
  if (!matches.length) {
    return [
      `🔎 KiCad/NSIP: brak pewnego dopasowania dla „${query}”.`,
      "Najlepszy następny krok: dodaj wynik do kolejki kuracji albo uruchom dry-run importera CERN na świeżym checkout.",
    ].join("\n");
  }

  const lines = [`🔎 KiCad/NSIP — wyniki dla „${query}”:`, ""];
  for (const [index, match] of matches.entries()) {
    lines.push(`${index + 1}. ${match.part_number || match.part_name}`);
    lines.push(`   Typ: ${match.result_type === "nsip_master" ? "NSIP master" : "KiCad staging"}`);
    if (match.symbol_name) lines.push(`   Symbol: ${match.symbol_name}`);
    if (match.footprint_name) lines.push(`   Footprint: ${match.footprint_name}`);
    if (match.reference_prefix) lines.push(`   Reference: ${match.reference_prefix}`);
    lines.push(`   Źródło: ${rowText(match.source_slug, "unknown")} | Licencja: ${rowText(match.license_spdx, "unknown")}`);
    lines.push(`   Review: ${rowText(match.review_status, "suggested")} | Confidence: ${Math.round((match.confidence || 0) * 100)}%`);
    if (match.raw_path) lines.push(`   Raw path: ${match.raw_path}`);
  }
  lines.push("");
  lines.push("Uwaga: sugestie z KiCad staging wymagają human review przed nadpisaniem pól ecoEDA/NSIP.");
  return lines.join("\n");
}
