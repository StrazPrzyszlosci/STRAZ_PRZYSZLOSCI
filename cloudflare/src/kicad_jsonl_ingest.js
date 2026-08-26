/**
 * T21 / B1 — real upstream ingestion path dla JSONL wygenerowanego przez
 * `pipelines/import_cern_kicad_library.py`.
 *
 * Kontrakt pliku (NDJSON / JSONL, UTF-8, jeden obiekt JSON na linie):
 *   WYMAGANE per linia:
 *     - source_slug      (niepusty string)
 *     - upstream_commit  (niepusty string)
 *     - symbol_name lub footprint_name (przynajmniej jedno niepuste)
 *   OPCJONALNE stringi:
 *     - source_url, license_spdx, kicad_version_family, library_name,
 *       reference_prefix, description, keywords, manufacturer, mpn,
 *       datasheet_url, package, normalized_part_number, raw_symbol_path,
 *       raw_footprint_path, raw_metadata_json
 *   LIMITY: max 5000 linii, max 64KB na linie.
 *
 * Gwarancje bezpieczenstwa:
 *  - dedup: SHA-256 checksum (source_slug, upstream_commit, symbol, footprint, mpn),
 *    duplikaty sa pomijane (skipped), nie nadpisuja istniejacych wierszy,
 *  - audit event: kazdy udany import dopisuje wpis do kicad_library_events
 *    (kind='ingest' z ingestKicadComponents + kind='jsonl_ingest' dla sciezki endpointu),
 *  - staging only: wszystkie wiersze trafiaja z import_status='staged'; zadne dane
 *    NIE sa promowane do katalogu bez verifier/curator/human review (T3/T4/Z90).
 */

import { ingestKicadComponents } from "./scheduled_kicad_importer.js";

export const JSONL_INGEST_MAX_LINES = 5000;
export const JSONL_INGEST_MAX_LINE_LENGTH = 65536;

const OPTIONAL_STRING_FIELDS = [
  "source_url",
  "license_spdx",
  "kicad_version_family",
  "library_name",
  "reference_prefix",
  "description",
  "keywords",
  "manufacturer",
  "mpn",
  "datasheet_url",
  "package",
  "normalized_part_number",
  "raw_symbol_path",
  "raw_footprint_path",
  "raw_metadata_json",
];

function toText(value) {
  return value === undefined || value === null ? "" : String(value);
}

export function validateJsonlRow(row) {
  if (!row || typeof row !== "object" || Array.isArray(row)) {
    return ["line_must_be_json_object"];
  }
  const missing = [];
  if (!toText(row.source_slug).trim()) missing.push("source_slug");
  if (!toText(row.upstream_commit).trim()) missing.push("upstream_commit");
  if (!toText(row.symbol_name).trim() && !toText(row.footprint_name).trim()) {
    missing.push("symbol_name_or_footprint_name");
  }
  for (const field of OPTIONAL_STRING_FIELDS) {
    const value = row[field];
    if (value !== undefined && value !== null && typeof value !== "string") {
      missing.push(`${field}_must_be_string`);
    }
  }
  return missing;
}

export function parseKicadJsonl(text) {
  const rows = [];
  const errors = [];
  const lines = toText(text).split(/\r?\n/);
  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index].trim();
    if (!line) continue;
    const lineNumber = index + 1;
    if (line.length > JSONL_INGEST_MAX_LINE_LENGTH) {
      errors.push({ line: lineNumber, error: `line longer than ${JSONL_INGEST_MAX_LINE_LENGTH} bytes` });
      continue;
    }
    let parsed;
    try {
      parsed = JSON.parse(line);
    } catch (err) {
      errors.push({ line: lineNumber, error: `invalid_json: ${err.message}` });
      continue;
    }
    const missing = validateJsonlRow(parsed);
    if (missing.length) {
      errors.push({ line: lineNumber, error: `contract_missing:${missing.join(",")}` });
      continue;
    }
    rows.push(parsed);
    if (rows.length >= JSONL_INGEST_MAX_LINES) {
      break;
    }
  }
  return { rows, errors };
}

export async function ingestKicadJsonlPayload(env, text, options = {}) {
  const { rows, errors } = parseKicadJsonl(text);
  if (errors.length) {
    return { success: false, reason: "invalid_payload", accepted: rows.length, errors };
  }
  if (!rows.length) {
    return { success: false, reason: "empty_payload", accepted: 0, errors: [] };
  }
  const result = await ingestKicadComponents(env, rows, options);
  if (!result?.success) {
    return { ...result, success: false };
  }

  // Audit event dla sciezki JSONL (odrębny od cron ingest, łatwy do wyszukania).
  if (env?.DB) {
    const now = options.now || new Date().toISOString();
    await env.DB.prepare(
      `INSERT INTO kicad_library_events (kind, source_slug, upstream_commit, component_count, inserted_count, skipped_count, created_at)
       VALUES ('jsonl_ingest', ?, ?, ?, ?, ?, ?)`
    ).bind(result.source_slug || "", result.upstream_commit || "", result.count || 0, result.inserted || 0, result.skipped || 0, now).run();
  }

  return {
    success: true,
    kind: "jsonl_ingest",
    source_slug: result.source_slug,
    upstream_commit: result.upstream_commit,
    count: result.count,
    inserted: result.inserted,
    skipped: result.skipped,
    staged_only: true,
  };
}
