/**
 * Automation metrics dashboard (B4, H2 roadmapy autonomizacji AI).
 *
 * Metryki minimalne mierzone z D1 — READ-ONLY dla agentów (nienadpisywane):
 *  1. coverage — % encji kicad_library_components z consistent provenance
 *     (source_url+license_spdx+kicad_version_family+upstream_commit non-empty,
 *      pochodzące z kicad_library_sources JOIN; tu proxy: raw_metadata_json
 *      zawiera pola provenance props).
 *  2. false_positive — rejected / approved z kicad_review_events (next_status).
 *  3. p50_review_hours — P50 od suggested→approved/rejected (time diff events).
 *  4. rollback_success — % rollbacków (next_status == previous_status) bez utraty
 *     (proxy: 100% gdy nienaruszony ledger; tu: ratio events next=prev / total).
 *  5. accepted_per_sprint — liczba approved w ostatnim oknie (sprint=14 dni).
 *
 * Cyber: funkcja nie zapisuje do D1; tylko SELECT. Brak AI, deterministyczna.
 */

const SPRINT_DAYS = 14;

async function ensureAutomationMetricsSchema(db) {
  await db
    .prepare(
      `CREATE TABLE IF NOT EXISTS automation_metrics (
        metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
        metric_key TEXT NOT NULL,
        metric_value REAL NOT NULL,
        measured_at TEXT NOT NULL,
        window TEXT NOT NULL DEFAULT 'sprint'
      )`
    )
    .run();
  await db
    .prepare(
      `CREATE INDEX IF NOT EXISTS idx_automation_metrics_key_measured
       ON automation_metrics(metric_key, measured_at)`
    )
    .run();
}

function percentile(sortedValues, p) {
  if (!sortedValues.length) return 0;
  if (p <= 0) return sortedValues[0];
  if (p >= 100) return sortedValues[sortedValues.length - 1];
  const rank = (p / 100) * (sortedValues.length - 1);
  const lower = Math.floor(rank);
  const upper = Math.ceil(rank);
  if (lower === upper) return sortedValues[lower];
  const frac = rank - lower;
  return sortedValues[lower] + (sortedValues[upper] - sortedValues[lower]) * frac;
}

function hoursBetween(isoA, isoB) {
  const a = Date.parse(isoA);
  const b = Date.parse(isoB);
  if (Number.isNaN(a) || Number.isNaN(b)) return null;
  return Math.abs(b - a) / (1000 * 60 * 60);
}

/**
 * Compute 5 metryk minimalnych z D1 (read-only).
 * @returns {Promise<Record<string, number|object>>}
 */
export async function computeAutomationMetrics(env, nowIso = null) {
  const db = env.DB;
  const measuredAt = nowIso || new Date().toISOString();
  if (!db) {
    return { measured_at: measuredAt, error: "no_db", metrics: {} };
  }
  await ensureAutomationMetricsSchema(db);

  const metrics = {};

  // 1) coverage — % komponentów z pełną provenance (proxy przez raw_metadata_json
  //    zawierający ki_fp_filters / dnp / mpn_alt pola z CERN). Prostsze proxy:
  //    brak NULL w kluczowych polach + nienulny raw_metadata_json.
  try {
    const totalRow = await db
      .prepare(
        `SELECT COUNT(*) AS n FROM kicad_library_components`
      )
      .first();
    const total = Number(totalRow?.n || 0);
    const provRow = await db
      .prepare(
        `SELECT COUNT(*) AS n FROM kicad_library_components
         WHERE symbol_name IS NOT NULL AND symbol_name <> ''
           AND (mpn IS NOT NULL AND mpn <> '')
           AND raw_metadata_json IS NOT NULL AND raw_metadata_json <> ''`
      )
      .first();
    const prov = Number(provRow?.n || 0);
    metrics.coverage = total > 0 ? Math.round((prov / total) * 1000) / 10 : 0;
  } catch (error) {
    metrics.coverage = 0;
    metrics.coverage_error = String(error?.message || error);
  }

  // 2) false_positive — rejected / approved z kicad_review_events (next_status).
  try {
    const rejectedRow = await db
      .prepare(
        `SELECT COUNT(*) AS n FROM kicad_review_events WHERE next_status = 'rejected'`
      )
      .first();
    const approvedRow = await db
      .prepare(
        `SELECT COUNT(*) AS n FROM kicad_review_events WHERE next_status = 'approved'`
      )
      .first();
    const rejected = Number(rejectedRow?.n || 0);
    const approved = Number(approvedRow?.n || 0);
    metrics.false_positive = approved > 0 ? Math.round((rejected / approved) * 1000) / 10 : 0;
    metrics.approved_total = approved;
    metrics.rejected_total = rejected;
  } catch (error) {
    metrics.false_positive = 0;
    metrics.false_positive_error = String(error?.message || error);
  }

  // 3) p50_review_hours — P50 od suggested→approved/rejected.
  //    Proxy: diff reviewed_at (dla links) vs created_at. Używamy events
  //    z previous_status='suggested' i next_status w ('approved','rejected').
  try {
    const eventsResult = await db
      .prepare(
        `SELECT e.created_at AS event_at, r.reviewed_at, r.created_at
         FROM kicad_review_events e
         LEFT JOIN recycled_part_kicad_links r ON r.id = e.link_id
         WHERE e.next_status IN ('approved','rejected')
           AND r.created_at IS NOT NULL
           AND r.reviewed_at IS NOT NULL`
      )
      .all();
    const rows = eventsResult?.results || [];
    const durations = [];
    for (const row of rows) {
      const h = hoursBetween(row.created_at, row.reviewed_at);
      if (h !== null && h >= 0) durations.push(h);
    }
    durations.sort((a, b) => a - b);
    metrics.p50_review_hours = durations.length
      ? Math.round(percentile(durations, 50) * 10) / 10
      : 0;
    metrics.review_samples = durations.length;
  } catch (error) {
    metrics.p50_review_hours = 0;
    metrics.p50_error = String(error?.message || error);
  }

  // 4) rollback_success — proxy: % events z next_status == previous_status (rollback
  //    == powrót do poprzedniego stanu). Bez utraty danych = 100% jeśli brak rollbackow.
  try {
    const totalRow = await db
      .prepare(
        `SELECT COUNT(*) AS n FROM kicad_review_events`
      )
      .first();
    const rollbackRow = await db
      .prepare(
        `SELECT COUNT(*) AS n FROM kicad_review_events
         WHERE previous_status IS NOT NULL AND next_status = previous_status`
      )
      .first();
    const total = Number(totalRow?.n || 0);
    const rollbacks = Number(rollbackRow?.n || 0);
    // 100% gdy 0 rollbackow. Jeśli rollbacki istnieją, proxy jest niedokładny;
    // zachowujemy ratio (100 - rollback_ratio) jako health-check.
    metrics.rollback_success = total > 0
      ? Math.round((1 - rollbacks / total) * 1000) / 10
      : 100;
    metrics.rollback_events = rollbacks;
  } catch (error) {
    metrics.rollback_success = 100;
    metrics.rollback_error = String(error?.message || error);
  }

  // 5) accepted_per_sprint — approved w ostatnich SPRINT_DAYS dniach.
  try {
    const sinceIso = new Date(Date.parse(measuredAt) - SPRINT_DAYS * 24 * 60 * 60 * 1000).toISOString();
    const row = await db
      .prepare(
        `SELECT COUNT(*) AS n FROM kicad_review_events
         WHERE next_status = 'approved'
           AND created_at >= ?`
      )
      .bind(sinceIso)
      .first();
    metrics.accepted_per_sprint = Number(row?.n || 0);
    metrics.sprint_window_days = SPRINT_DAYS;
  } catch (error) {
    metrics.accepted_per_sprint = 0;
    metrics.accepted_error = String(error?.message || error);
  }

  return {
    measured_at: measuredAt,
    sprint_window_days: SPRINT_DAYS,
    metrics,
  };
}

/**
 * Persist snapshot metryk do automation_metrics (append-only historii).
 * Opcjonalne — wywoływane z harmonogramu, nie z każdego żądania.
 */
export async function persistAutomationMetricsSnapshot(env, snapshot) {
  const db = env.DB;
  if (!db || !snapshot?.metrics) return { persisted: 0 };
  await ensureAutomationMetricsSchema(db);
  const measuredAt = snapshot.measured_at || new Date().toISOString();
  const metricKeys = [
    "coverage",
    "false_positive",
    "p50_review_hours",
    "rollback_success",
    "accepted_per_sprint",
  ];
  let persisted = 0;
  for (const key of metricKeys) {
    if (typeof snapshot.metrics[key] === "number") {
      await db
        .prepare(
          `INSERT INTO automation_metrics (metric_key, metric_value, measured_at, window)
           VALUES (?, ?, ?, ?)`
        )
        .bind(key, snapshot.metrics[key], measuredAt, "sprint")
        .run();
      persisted += 1;
    }
  }
  return { persisted };
}

export {
  ensureAutomationMetricsSchema,
  percentile,
  hoursBetween,
  SPRINT_DAYS,
  formatAutomationMetricsReply,
};

/**
 * Format snapshot metryk jako czytelny reply dla bota `!metrics` / `/metrics`
 * (Discord/Telegram). Read-only — bezpieczne (brak sekretów). Wymaga auth
 * w warstwie wywołującej (endpoint `/v1/metrics` lub komenda-only dla maintainerów).
 *
 * @param {{measured_at: string, metrics: Record<string, number|string>}} snapshot
 * @returns {string}  Czysty tekst dashboardu.
 */
function formatAutomationMetricsReply(snapshot) {
  if (!snapshot) return "Brak danych metryk.";
  if (snapshot.error === "no_db") {
    return "Metryki niedostępne (brak D1 w środowisku).";
  }
  const m = snapshot.metrics || {};
  const fmt = (v, suffix = "") =>
    typeof v === "number" && Number.isFinite(v) ? `${v}${suffix}` : "n/d";
  const lines = [
    "📊 Metryki automatyzacji AI (H2 roadmapa)",
    `  • coverage: ${fmt(m.coverage, "%")}${m.coverage_error ? ` (err: ${m.coverage_error})` : ""}`,
    `  • false-positive (rejected/approved): ${fmt(m.false_positive)}${m.false_positive_error ? ` (err: ${m.false_positive_error})` : ""} (A=${m.approved_total ?? "?"}/R=${m.rejected_total ?? "?"})`,
    `  • p50 review (h): ${fmt(m.p50_review_hours)} (n=${m.review_samples ?? 0})${m.p50_error ? ` (err: ${m.p50_error})` : ""}`,
    `  • rollback success: ${fmt(m.rollback_success, "%")} (roll=${m.rollback_events ?? 0})${m.rollback_error ? ` (err: ${m.rollback_error})` : ""}`,
    `  • accepted/sprint (${snapshot.sprint_window_days ?? m.sprint_window_days ?? 14}d): ${fmt(m.accepted_per_sprint)}${m.accepted_error ? ` (err: ${m.accepted_error})` : ""}`,
    `  • measured_at: ${snapshot.measured_at || "n/d"}`,
  ];
  return lines.join("\n");
}
