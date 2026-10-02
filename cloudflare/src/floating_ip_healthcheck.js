/**
 * Hardening: healthcheck floating-IP (warstwa sieciowa przed Workerem).
 *
 * Problem: floating-IP bez aktywnego healthchecka milcząco wypada z rotacji —
 * ruch trafia w próżnię, a cron/retencja T31 i webhooki B5/T23/T30 milkną.
 *
 * Moduł jest czysty i wstrzykiwalny: fetcher podaje wołający (prod:
 * `fetchWithTimeout` z `base_utils.js`), więc zero zależności sieciowych
 * w teście. Funkcje nigdy nie rzucają — zwracają obiekt unhealthy
 * (monitoring ma być fail-safe, nie fail-open jak limitery).
 * Sekrety: URL healthchecka nie zawiera tokenów; odpowiedź jest przycinana
 * przed logowaniem, żeby nie wynieść nagłówków.
 */

const DEFAULT_TIMEOUT_MS = 10000;
const DEFAULT_MAX_BODY_CHARS = 2000;

function toText(value) {
  return value === undefined || value === null ? "" : String(value);
}

/**
 * Normalizuje dowolny payload health-endpointu do wspólnego kształtu.
 */
export function parseHealthPayload(payload) {
  if (payload === null || payload === undefined) {
    return { ok: false, status: "empty", detail: "pusta odpowiedź healthchecka" };
  }
  if (typeof payload === "string") {
    const trimmed = payload.trim().toLowerCase();
    if (trimmed === "ok" || trimmed === "healthy" || trimmed === "up") {
      return { ok: true, status: "up", detail: payload.trim().slice(0, 120) };
    }
    return { ok: false, status: "unexpected_body", detail: payload.slice(0, 120) };
  }
  if (typeof payload === "object") {
    const ok = payload.ok === true || payload.healthy === true || payload.status === "ok" || payload.status === "up" || payload.status === "healthy";
    return {
      ok,
      status: toText(payload.status || (ok ? "up" : "down")) || (ok ? "up" : "down"),
      detail: toText(payload.detail || payload.message || "").slice(0, 120),
    };
  }
  return { ok: false, status: "unexpected_type", detail: `typ ${typeof payload}` };
}

/**
 * Jednorazowy healthcheck. `fetcher(url, options, timeoutMs)` → `{status, bodyText, bodyJson?}`.
 */
export async function checkFloatingIpHealth(fetcher, url, options = {}) {
  const target = toText(url).trim();
  if (!target) return { healthy: false, reason: "missing_url", statusCode: null, latencyMs: 0 };
  if (typeof fetcher !== "function") return { healthy: false, reason: "missing_fetcher", statusCode: null, latencyMs: 0 };
  const timeoutMs = Math.max(1000, Number(options.timeoutMs || DEFAULT_TIMEOUT_MS));
  const started = Date.now();
  try {
    const response = await fetcher(target, options.requestOptions || {}, timeoutMs);
    const latencyMs = Date.now() - started;
    const statusCode = Number(response?.status ?? response?.statusCode ?? 0) || null;
    let payload = response?.bodyJson;
    if (payload === undefined) {
      const raw = toText(response?.bodyText ?? response?.body ?? "");
      try {
        payload = raw ? JSON.parse(raw) : null;
      } catch {
        payload = raw;
      }
    }
    if (typeof payload === "string") payload = payload.slice(0, Number(options.maxBodyChars || DEFAULT_MAX_BODY_CHARS));
    const parsed = parseHealthPayload(payload);
    const httpOk = statusCode === null || (statusCode >= 200 && statusCode < 300);
    const healthy = parsed.ok && httpOk;
    return {
      healthy,
      reason: healthy ? "healthy" : (parsed.ok ? `http_${statusCode}` : `payload_${parsed.status}`),
      statusCode,
      latencyMs,
      payloadStatus: parsed.status,
      detail: parsed.detail,
    };
  } catch (error) {
    return {
      healthy: false,
      reason: "fetch_error",
      statusCode: null,
      latencyMs: Date.now() - started,
      error: error instanceof Error ? error.message : String(error),
    };
  }
}

/**
 * Jednolinijkowe podsumowanie do logów / dashboardu (bez sekretów).
 */
export function formatFloatingIpHealthSummary(result) {
  if (!result || typeof result !== "object") return "floating-ip health: brak wyniku";
  const state = result.healthy ? "HEALTHY" : "UNHEALTHY";
  const code = result.statusCode ?? "—";
  const latency = Number.isFinite(Number(result.latencyMs)) ? `${result.latencyMs}ms` : "—";
  return `floating-ip health: ${state} (reason=${toText(result.reason) || "?"}, http=${code}, latency=${latency})`;
}
