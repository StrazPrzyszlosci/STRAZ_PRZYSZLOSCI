/**
 * T41 — trendy plonów: serie sezonowe + regresja liniowa per crop_profile.
 *
 * harvest_records (T36) rosną z każdym zbiorem; sam SUM miesięczny (agregat
 * w automation_metrics) nie mówi, czy plony rosną, czy maleją. Ten moduł
 * zamienia surowe wpisy w czytelne trendy per profil uprawy:
 *   seria miesięczna SUM(mass_g) + regresja liniowa (nachylenie g/miesiąc).
 *
 * Gwarancje (wzorzec T36/T37):
 *  - read-only: zero zapisów do D1, zero mutacji polityk;
 *  - okno czasowe liczone względem NAJNOWSZEGO miesiąca w danych
 *    (deterministyczne — brak time-bombów zegarowych, lekcja z T31);
 *  - regresja wymaga >= 2 miesięcy; przy 1 miesiącu trend = null;
 *  - wynik zawiera note "trend != gwarancja" (kontynuacja zasady T37
 *    "korelacja != przyczynowość").
 */

const DEFAULT_MONTHS_BACK = 12;
const MIN_MONTHS_BACK = 1;
const MAX_MONTHS_BACK = 60;
// Nachylenie poniżej progu (względem średniej) = trend stabilny, nie szum.
const FLAT_SLOPE_RATIO = 0.05;

function toText(value) {
  return value === undefined || value === null ? "" : String(value);
}

export function normalizeMonthsBack(raw) {
  const parsed = Number(raw);
  if (!Number.isFinite(parsed) || parsed <= 0) return DEFAULT_MONTHS_BACK;
  return Math.min(
    MAX_MONTHS_BACK,
    Math.max(MIN_MONTHS_BACK, Math.floor(parsed)),
  );
}

/**
 * Najmniejsze kwadraty dla punktów [{x, y}]. Zwraca null przy < 2 punktów
 * lub zerowej wariancji x (wtedy nachylenie jest nieokreślone).
 */
export function linearRegression(points) {
  const clean = (Array.isArray(points) ? points : []).filter(
    (p) => p && Number.isFinite(Number(p.x)) && Number.isFinite(Number(p.y)),
  );
  const n = clean.length;
  if (n < 2) return null;
  let sumX = 0;
  let sumY = 0;
  let sumXX = 0;
  let sumXY = 0;
  for (const p of clean) {
    const x = Number(p.x);
    const y = Number(p.y);
    sumX += x;
    sumY += y;
    sumXX += x * x;
    sumXY += x * y;
  }
  const denom = n * sumXX - sumX * sumX;
  if (denom === 0) return null;
  const slope = (n * sumXY - sumX * sumY) / denom;
  const intercept = (sumY - slope * sumX) / n;
  return { slope, intercept, n };
}

export function trendDirection(slope, meanValue) {
  if (!Number.isFinite(slope)) return "unknown";
  const threshold = Math.abs(Number(meanValue) || 0) * FLAT_SLOPE_RATIO;
  if (Math.abs(slope) <= threshold) return "stable";
  return slope > 0 ? "rising" : "falling";
}

/**
 * Grupuje wiersze harvest {crop_profile, harvested_at, mass_g} w serie
 * miesięczne per profil: { [crop]: [{ month: "YYYY-MM", mass_g: SUM }] }.
 * Wiersze bez profilu/masy/daty są pomijane (fail-open na brudnych danych).
 * Kluczowanie zagnieżdżonymi Mapami (bez sklejania stringów), więc profile
 * ze spacjami są bezpieczne.
 */
export function buildMonthlySeries(rows) {
  const crops = new Map();
  for (const row of Array.isArray(rows) ? rows : []) {
    const crop = toText(row?.crop_profile).trim();
    const month = toText(row?.harvested_at).slice(0, 7);
    const mass = Number(row?.mass_g);
    if (
      !crop ||
      !/^\d{4}-\d{2}$/.test(month) ||
      !Number.isFinite(mass) ||
      mass <= 0
    )
      continue;
    if (!crops.has(crop)) crops.set(crop, new Map());
    const months = crops.get(crop);
    months.set(month, (months.get(month) || 0) + mass);
  }
  const series = {};
  for (const [crop, months] of crops) {
    series[crop] = [...months.entries()]
      .map(([month, massG]) => ({ month, mass_g: massG }))
      .sort((a, b) => (a.month < b.month ? -1 : a.month > b.month ? 1 : 0));
  }
  return series;
}

function shiftMonthKey(monthKey, deltaMonths) {
  const year = Number(monthKey.slice(0, 4));
  const month = Number(monthKey.slice(5, 7));
  const total = year * 12 + (month - 1) + deltaMonths;
  const y = Math.floor(total / 12);
  const m = (total % 12) + 1;
  return `${String(y).padStart(4, "0")}-${String(m).padStart(2, "0")}`;
}

/**
 * Cięcie serii do ostatnich N miesięcy względem najnowszego miesiąca
 * w danych (nie względem zegara — deterministyczne).
 */
export function cutSeriesToWindow(series, monthsBack) {
  const window = normalizeMonthsBack(monthsBack);
  let maxMonth = "";
  for (const points of Object.values(series)) {
    for (const p of points) {
      if (p.month > maxMonth) maxMonth = p.month;
    }
  }
  if (!maxMonth) return { series: {}, cutoffMonth: "", maxMonth: "" };
  const cutoffMonth = shiftMonthKey(maxMonth, -(window - 1));
  const cut = {};
  for (const [crop, points] of Object.entries(series)) {
    const kept = points.filter((p) => p.month >= cutoffMonth);
    if (kept.length) cut[crop] = kept;
  }
  return { series: cut, cutoffMonth, maxMonth };
}

export function computeCropTrends(series) {
  const trends = {};
  for (const [crop, points] of Object.entries(series)) {
    const total = points.reduce((sum, p) => sum + p.mass_g, 0);
    const mean = points.length ? total / points.length : 0;
    const fit = linearRegression(
      points.map((p, index) => ({ x: index, y: p.mass_g })),
    );
    trends[crop] = {
      months: points.length,
      total_g: total,
      mean_g_per_month: mean,
      slope_g_per_month: fit ? fit.slope : null,
      intercept_g: fit ? fit.intercept : null,
      direction: fit ? trendDirection(fit.slope, mean) : "unknown",
    };
  }
  return trends;
}

export async function computeHarvestTrends(env, providerId, options = {}) {
  if (!env?.DB) return { success: false, reason: "no_db" };
  const growCellId = toText(providerId).trim();
  if (!growCellId) return { success: false, reason: "provider_id_required" };
  const monthsBack = normalizeMonthsBack(options.monthsBack);

  const res = await env.DB.prepare(
    `SELECT crop_profile, harvested_at, mass_g FROM harvest_records
     WHERE grow_cell_id = ?
     ORDER BY harvested_at ASC`,
  )
    .bind(growCellId)
    .all();
  const rows = res?.results || [];
  const fullSeries = buildMonthlySeries(rows);
  const { series, cutoffMonth, maxMonth } = cutSeriesToWindow(
    fullSeries,
    monthsBack,
  );
  const trends = computeCropTrends(series);
  const cropCount = Object.keys(series).length;
  return {
    success: true,
    grow_cell_id: growCellId,
    months_back: monthsBack,
    cutoff_month: cutoffMonth,
    latest_month: maxMonth,
    crop_count: cropCount,
    series,
    trends,
    note:
      cropCount === 0
        ? "Brak wpisów plonu dla tej komórki — najpierw zgłoś zbiory przez POST /v1/agri/harvest."
        : "Trend opisuje przeszłość (regresja liniowa miesięcznych sum), nie gwarantuje przyszłych plonów.",
  };
}
