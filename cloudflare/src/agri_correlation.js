/**
 * T37 — korelacja plon↔warunki: "przy jakich odczytach rosło najlepiej?"
 *
 * Wejście: staging telemetrii (T29) + harvest ledger (T36) dla jednej komórki.
 * Metoda: miesięczne średnie każdego czujnika vs suma mass_g w miesiącu;
 * korelacja Pearsona per czujnik (min. 2 wspólne miesiące, inaczej null).
 *
 * Wynik jest read-only analityką — niczego nie zmienia w politykach.
 * Kalibracja na jego podstawie to osobny suggest-only przepływ (T38).
 */

const DEFAULT_MONTHS_BACK = 6;
const MAX_MONTHS_BACK = 24;

function toText(value) {
  return value === undefined || value === null ? "" : String(value);
}

export function pearsonR(xs, ys) {
  if (!Array.isArray(xs) || !Array.isArray(ys)) return null;
  const n = Math.min(xs.length, ys.length);
  if (n < 2) return null;
  const mx = xs.slice(0, n).reduce((a, b) => a + b, 0) / n;
  const my = ys.slice(0, n).reduce((a, b) => a + b, 0) / n;
  let cov = 0;
  let vx = 0;
  let vy = 0;
  for (let i = 0; i < n; i += 1) {
    const dx = xs[i] - mx;
    const dy = ys[i] - my;
    cov += dx * dy;
    vx += dx * dx;
    vy += dy * dy;
  }
  if (vx === 0 || vy === 0) return null;
  return cov / Math.sqrt(vx * vy);
}

function monthWindow(nowIso, monthsBack) {
  const time = Date.parse(nowIso);
  const start = new Date(time);
  start.setUTCMonth(start.getUTCMonth() - monthsBack);
  start.setUTCDate(1);
  start.setUTCHours(0, 0, 0, 0);
  return start.toISOString();
}

/**
 * Zwraca {months, sensors:[{sensor, monthly_means:{month->mean}, pearson_r}]}.
 */
export function alignMonthlySeries(telemetryRows, harvestRows) {
  const massByMonth = new Map();
  for (const row of harvestRows || []) {
    const month = toText(row.month_key).slice(0, 7);
    if (!month) continue;
    massByMonth.set(month, (massByMonth.get(month) || 0) + Number(row.total_mass || 0));
  }

  const bySensorMonth = new Map();
  for (const row of telemetryRows || []) {
    const sensor = toText(row.sensor);
    const month = toText(row.month_key).slice(0, 7);
    if (!sensor || !month || !massByMonth.has(month)) continue;
    if (!bySensorMonth.has(sensor)) bySensorMonth.set(sensor, new Map());
    const means = bySensorMonth.get(sensor);
    // Średnia z miesięcy, w których był też plon; przy wielu wierszach na
    // miesiąc bierzemy ostatni (SQL już agreguje AVG po miesiącach).
    means.set(month, Number(row.mean_value));
  }

  const months = [...new Set([...bySensorMonth.values()].flatMap((m) => [...m.keys()]))]
    .filter((month) => massByMonth.has(month))
    .sort();

  const massSeries = months.map((month) => massByMonth.get(month));
  const sensors = [...bySensorMonth.entries()].map(([sensor, means]) => {
    const monthly_means = {};
    for (const month of months) {
      if (means.has(month)) monthly_means[month] = means.get(month);
    }
    const xs = months.filter((m) => means.has(m)).map((m) => means.get(m));
    const ys = months.filter((m) => means.has(m)).map((m) => massByMonth.get(m));
    return {
      sensor,
      monthly_means,
      pearson_r: pearsonR(xs, ys),
      months_with_data: xs.length,
    };
  }).sort((a, b) => a.sensor.localeCompare(b.sensor));

  return { months, mass_by_month: Object.fromEntries(months.map((m) => [m, massByMonth.get(m)])), sensors };
}

export async function computeGrowCorrelation(env, providerId, options = {}) {
  if (!env?.DB) return { success: false, reason: "no_db" };
  const growCellId = toText(providerId).trim();
  if (!growCellId) return { success: false, reason: "provider_id_required" };
  const nowIso = options.now || new Date().toISOString();
  const requested = Number(options.monthsBack || DEFAULT_MONTHS_BACK);
  const monthsBack = Math.min(Math.max(Math.floor(requested) || DEFAULT_MONTHS_BACK, 2), MAX_MONTHS_BACK);
  const windowStartIso = monthWindow(nowIso, monthsBack);

  const telemetryResult = await env.DB.prepare(
    `SELECT sensor, substr(recorded_at, 1, 7) AS month_key, AVG(value) AS mean_value
     FROM sensor_readings_staging
     WHERE provider_id = ? AND recorded_at >= ?
     GROUP BY sensor, month_key ORDER BY month_key`
  ).bind(growCellId, windowStartIso).all();

  const harvestResult = await env.DB.prepare(
    `SELECT substr(harvested_at, 1, 7) AS month_key, SUM(mass_g) AS total_mass
     FROM harvest_records
     WHERE grow_cell_id = ? AND harvested_at >= ?
     GROUP BY month_key ORDER BY month_key`
  ).bind(growCellId, windowStartIso).all();

  const aligned = alignMonthlySeries(telemetryResult?.results || [], harvestResult?.results || []);

  return {
    success: true,
    grow_cell_id: growCellId,
    generated_at: nowIso,
    window_months: monthsBack,
    window_start: windowStartIso,
    ...aligned,
    note: "pearson_r > 0: wyższe odczyty współwystąpiły z większym plonem; korelacja != przyczynowość",
  };
}
