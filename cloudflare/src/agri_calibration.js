/**
 * T38 — suggest-only kalibracja pasm polityki na podstawie korelacji (T37).
 *
 * ŻELAZNE ZASADY:
 *  - sugestia NIGDY nie jest zapisywana do D1 ani aplikowana automatycznie;
 *    jedynym wynikiem jest JSON diff + gotowe body draft-PR dla człowieka
 *    (merge przez flow B5/T23/T30),
 *  - autopilot nie zmienia własnych progów samodzielnie,
 *  - korelacja != przyczynowość — próg |r| i minimalna liczba miesięcy
 *    chronią przed przypadkowymi "kalibracjami".
 */

const DEFAULT_MIN_MONTHS = 3;
const DEFAULT_MIN_ABS_R = 0.7;
const DEFAULT_STEP_PERCENT = 5;

function clampBand(band) {
  const next = { ...band };
  if (!(next.safe_min < next.safe_max)) return null;
  if (next.alarm_below > next.safe_min) next.alarm_below = next.safe_min;
  if (next.alarm_above < next.safe_max) next.alarm_above = next.safe_max;
  return next;
}

function round6(value) {
  return Math.round(value * 1e6) / 1e6;
}

export function suggestBandAdjustments(policy, correlation, options = {}) {
  const minMonths = Math.max(2, Number(options.minMonths || DEFAULT_MIN_MONTHS));
  const minAbsR = Math.min(1, Math.abs(Number(options.minAbsR ?? DEFAULT_MIN_ABS_R)));
  const stepPercent = Math.min(50, Math.max(1, Number(options.stepPercent || DEFAULT_STEP_PERCENT)));

  const suggestions = [];
  const skipped = [];
  const bands = policy?.bands && typeof policy.bands === "object" ? policy.bands : {};
  const sensorEntries = new Map((correlation?.sensors || []).map((entry) => [entry.sensor, entry]));

  for (const [sensor, band] of Object.entries(bands)) {
    const stats = sensorEntries.get(sensor);
    if (!stats) {
      skipped.push({ sensor, reason: "no_correlation_data" });
      continue;
    }
    if ((stats.months_with_data || 0) < minMonths) {
      skipped.push({ sensor, reason: `insufficient_months:${stats.months_with_data}/${minMonths}` });
      continue;
    }
    const r = stats.pearson_r;
    if (r === null || r === undefined || Math.abs(r) < minAbsR) {
      skipped.push({ sensor, reason: r === null || r === undefined ? "correlation_undefined" : `abs_r_below_threshold:${Math.abs(r).toFixed(2)}<${minAbsR}` });
      continue;
    }

    const widthUp = band.safe_max - band.safe_min;
    const step = (widthUp * stepPercent) / 100;
    let proposed;
    let direction;
    if (r > 0) {
      // Wyższe odczyty współwystąpiły z większym plonem -> podnieśmy górne krawędzie.
      direction = "raise_upper_edges";
      proposed = clampBand({
        ...band,
        safe_max: round6(band.safe_max + step),
        alarm_above: round6(band.alarm_above + step),
      });
    } else {
      // Niższe odczyty lepsze -> obniżmy dolne krawędzie.
      direction = "lower_lower_edges";
      proposed = clampBand({
        ...band,
        safe_min: round6(band.safe_min - step),
        alarm_below: round6(band.alarm_below - step),
      });
    }
    if (!proposed) {
      skipped.push({ sensor, reason: "proposal_violates_band_invariants" });
      continue;
    }
    suggestions.push({
      sensor,
      direction,
      pearson_r: Number(r.toFixed(3)),
      months_with_data: stats.months_with_data,
      current_band: band,
      proposed_band: proposed,
      reason: `${direction} przy |pearson_r|=${Math.abs(r).toFixed(2)} (próg ${minAbsR}), krok ${stepPercent}% szerokości pasma`,
    });
  }

  return {
    policy_id: policy?.id || null,
    grow_cell_id: policy?.grow_cell_id || null,
    suggestions,
    skipped,
    suggest_only: true,
    auto_applied: false,
  };
}

export function buildCalibrationPrBody(policy, suggestionResult) {
  const lines = [
    `CALIBRATION SUGGESTION (suggest-only) dla polityki \`${suggestionResult.policy_id}\` / komórki \`${suggestionResult.grow_cell_id}\`.`,
    "",
    "Safety gates:",
    "- propozycja NIE została zapisana w D1 ani seed_policy.json;",
    "- człowiek recenzuje i mergeuje PR; autopilot nie zmienia własnych progów;",
    "- korelacja Pearsona nie dowodzi przyczynowości.",
    "",
    "**Proponowane zmiany pasm:**",
  ];
  if (!suggestionResult.suggestions.length) {
    lines.push("- brak sugestii powyżej progów (za mało danych lub słaba korelacja).");
  }
  for (const s of suggestionResult.suggestions) {
    lines.push(
      `- \`${s.sensor}\`: ${s.direction} (r=${s.pearson_r}, miesiące=${s.months_with_data})`,
      `  - safe_min: ${s.current_band.safe_min} -> ${s.proposed_band.safe_min}`,
      `  - safe_max: ${s.current_band.safe_max} -> ${s.proposed_band.safe_max}`,
      `  - alarm_below: ${s.current_band.alarm_below} -> ${s.proposed_band.alarm_below}`,
      `  - alarm_above: ${s.current_band.alarm_above} -> ${s.proposed_band.alarm_above}`
    );
  }
  const skippedCount = suggestionResult.skipped?.length || 0;
  if (skippedCount) lines.push("", `Pominięte sensory: ${skippedCount} (szczegóły w JSON endpointu).`);
  return lines.join("\n");
}
