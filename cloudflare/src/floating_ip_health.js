/**
 * HARDENING — healthcheck dla monitoringu floating-IP / load-balancera.
 *
 * Istniejący `GET /health` zwracał gołe `{status:"ok"}` bez weryfikacji D1,
 * więc monitor nie odróżniał workera żywego od workera gotowego (z padniętym D1).
 *
 * `checkFloatingIpHealth()` nigdy nie rzuca: przy braku/błędzie D1 zwraca
 * `ready:false` (HTTP nadal 200 — LB nie flapuje na transientach, a monitoring
 * alarmuje po fladze `ready`, nie po kodzie).
 */

export async function checkFloatingIpHealth(env = {}, options = {}) {
  const nowIso = new Date(typeof options.nowMs === "number" ? options.nowMs : Date.now()).toISOString();
  const version = env.DEPLOY_VERSION || env.CF_VERSION || "dev";
  const base = { status: "ok", ready: true, version, now: nowIso };
  const db = env.DB;
  if (!db) return { ...base, ready: true, db: "unconfigured" };
  try {
    const row = await db.prepare(`SELECT 1 AS ok`).first();
    if (row && (row.ok === 1 || row.ok === "1" || row.ok === true)) {
      return { ...base, db: "ok" };
    }
    return { ...base, ready: false, db: "unexpected_result" };
  } catch (error) {
    return {
      ...base,
      ready: false,
      db: "unreachable",
      db_error: error instanceof Error ? error.message : String(error),
    };
  }
}
