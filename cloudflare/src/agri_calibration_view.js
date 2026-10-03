/**
 * T40 — wizualizacja diff kalibracji pasm (stare → nowe) do review PR.
 *
 * Czytelny, jednoekranowy podgląd wyniku `suggestBandAdjustments()` (T38)
 * dla człowieka w Discordzie/Telegramie oraz wariant Markdown do body PR.
 *
 * ŻELAZNE ZASADY (dziedziczone z T38):
 *  - moduł jest PURE VIEW: niczego nie zapisuje, nie aplikuje, nie woła D1;
 *  - tekst zawsze zawiera bramki bezpieczeństwa (suggest-only, korelacja
 *    != przyczynowość, wymagane review człowieka);
 *  - odpowiedź bota tnie do <1800 znaków (Discord 2000 / Telegram 4096).
 */

const MAX_REPLY_CHARS = 1800;

const DIRECTION_LABELS = {
  raise_upper_edges: "górne w górę",
  lower_lower_edges: "dolne w dół",
};

function num(value) {
  const n = Number(value);
  return Number.isFinite(n) ? n : null;
}

export function formatDelta(oldValue, newValue) {
  const a = num(oldValue);
  const b = num(newValue);
  if (a === null || b === null) return "n/d";
  const d = Math.round((b - a) * 1e6) / 1e6;
  if (d === 0) return "±0";
  return `${d > 0 ? "+" : ""}${d}`;
}

export function formatBandSpan(band) {
  if (!band) return "n/d";
  const smin = num(band.safe_min);
  const smax = num(band.safe_max);
  if (smin === null || smax === null) return "n/d";
  return `${smin}–${smax}`;
}

export function formatBandDiffLine(suggestion) {
  const sensor = suggestion?.sensor || "<nieznany>";
  const cur = suggestion?.proposed_band && suggestion?.current_band
    ? suggestion
    : null;
  if (!cur) return `- ${sensor}: brak danych pasma.`;
  const dMin = formatDelta(cur.current_band.safe_min, cur.proposed_band.safe_min);
  const dMax = formatDelta(cur.current_band.safe_max, cur.proposed_band.safe_max);
  const dLow = formatDelta(cur.current_band.alarm_below, cur.proposed_band.alarm_below);
  const dHigh = formatDelta(cur.current_band.alarm_above, cur.proposed_band.alarm_above);
  const dirPl = DIRECTION_LABELS[cur.direction] || cur.direction || "?";
  const r = cur.pearson_r ?? "?";
  return (
    `- ${sensor} [${dirPl}, r=${r}]: ` +
    `safe ${formatBandSpan(cur.current_band)} → ${formatBandSpan(cur.proposed_band)} ` +
    `(Δmin ${dMin}, Δmax ${dMax}, Δlow ${dLow}, Δhigh ${dHigh})`
  );
}

function truncateHard(text, maxChars = MAX_REPLY_CHARS) {
  if (text.length <= maxChars) return text;
  return `${text.slice(0, maxChars - 1)}…`;
}

export function renderCalibrationDiffText(suggestionResult, options = {}) {
  const maxChars = Number(options.maxChars || MAX_REPLY_CHARS);
  const policyId = suggestionResult?.policy_id || "?";
  const cellId = suggestionResult?.grow_cell_id || "?";
  const suggestions = Array.isArray(suggestionResult?.suggestions)
    ? suggestionResult.suggestions
    : [];
  const skipped = Array.isArray(suggestionResult?.skipped) ? suggestionResult.skipped : [];

  const lines = [
    `KALIBRACJA — podgląd diff (suggest-only) ${policyId} / ${cellId}:`,
  ];
  if (!suggestions.length) {
    lines.push("Brak sugestii powyżej progów (za mało danych lub słaba korelacja).");
  } else {
    for (const s of suggestions) lines.push(formatBandDiffLine(s));
  }
  if (skipped.length) lines.push(`Pominięte sensory: ${skipped.length}.`);
  lines.push(
    "Bramki: NIC nie zapisano (ani D1, ani seed_policy.json);",
    "korelacja != przyczynowość; merge PR tylko przez człowieka."
  );
  return truncateHard(lines.join("\n"), maxChars);
}

export function renderCalibrationDiffMarkdown(suggestionResult) {
  const policyId = suggestionResult?.policy_id || "?";
  const cellId = suggestionResult?.grow_cell_id || "?";
  const suggestions = Array.isArray(suggestionResult?.suggestions)
    ? suggestionResult.suggestions
    : [];
  const skipped = Array.isArray(suggestionResult?.skipped) ? suggestionResult.skipped : [];

  const lines = [
    `### Kalibracja — diff pasm (suggest-only) \`${policyId}\` / \`${cellId}\``,
    "",
    "| sensor | kierunek | r | safe_min | safe_max | alarm_below | alarm_above |",
    "|---|---|---|---|---|---|---|",
  ];
  if (!suggestions.length) {
    lines.push("_brak sugestii powyżej progów_");
  }
  for (const s of suggestions) {
    const dirPl = DIRECTION_LABELS[s.direction] || s.direction || "?";
    lines.push(
      `| \`${s.sensor}\` | ${dirPl} | ${s.pearson_r ?? "?"} ` +
      `| ${s.current_band.safe_min} → ${s.proposed_band.safe_min} (${formatDelta(s.current_band.safe_min, s.proposed_band.safe_min)}) ` +
      `| ${s.current_band.safe_max} → ${s.proposed_band.safe_max} (${formatDelta(s.current_band.safe_max, s.proposed_band.safe_max)}) ` +
      `| ${s.current_band.alarm_below} → ${s.proposed_band.alarm_below} (${formatDelta(s.current_band.alarm_below, s.proposed_band.alarm_below)}) ` +
      `| ${s.current_band.alarm_above} → ${s.proposed_band.alarm_above} (${formatDelta(s.current_band.alarm_above, s.proposed_band.alarm_above)}) |`
    );
  }
  if (skipped.length) {
    lines.push("", `_Pominięte sensory: ${skipped.length} (szczegóły w JSON endpointu)._`);
  }
  lines.push(
    "",
    "> Safety: sugestia NIE została zapisana; autopilot nie zmienia własnych progów; korelacja ≠ przyczynowość."
  );
  return lines.join("\n");
}

export function buildCalibrationReview(suggestionResult, options = {}) {
  return {
    policy_id: suggestionResult?.policy_id || null,
    grow_cell_id: suggestionResult?.grow_cell_id || null,
    suggest_only: true,
    auto_applied: false,
    review_text: renderCalibrationDiffText(suggestionResult, options),
    review_markdown: renderCalibrationDiffMarkdown(suggestionResult),
  };
}

/**
 * Alias zgodny z blokiem T40 w worker.js (`GET /v1/agri/calibration-view`):
 * `buildCalibrationView(policy, suggestionResult)`.
 * Polityka jest już osadzona w suggestionResult (policy_id/grow_cell_id);
 * parametr `policy` służy jako fallback gdyby suggestionResult ich nie miał.
 */
export function buildCalibrationView(policy, suggestionResult, options = {}) {
  const merged = {
    policy_id: suggestionResult?.policy_id || policy?.id || null,
    grow_cell_id: suggestionResult?.grow_cell_id || policy?.grow_cell_id || null,
    suggestions: suggestionResult?.suggestions || [],
    skipped: suggestionResult?.skipped || [],
  };
  return buildCalibrationReview(merged, options);
}
