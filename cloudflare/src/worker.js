import { generateRecommendation } from "./recommendation.js";
import { fetchWithTimeout } from "./base_utils.js";
import { getCorsAllowOrigin, jsonResponse } from "./security_headers.js";
import { checkGlobalRateLimit } from "./global_rate_limiter.js";
import { checkProviderRateLimit } from "./provider_rate_limiter.js";
import { computeAutomationMetrics } from "./automation_metrics.js";
import { runScheduledKicadImport } from "./scheduled_kicad_importer.js";
import { ingestKicadJsonlPayload } from "./kicad_jsonl_ingest.js";
import { listEdgeEventsSince, parseEdgeStreamQuery, publishEdgeEvent, pruneEdgeEvents, resolveEdgeEventRetentionConfig } from "./edge_events_stream.js";
import { runAgriEvaluate, upsertAgriPolicy, getAgriPolicy, getActiveAgriPolicy, deactivateAgriPolicy } from "./agri_evaluate.js";
import { computeAgriMetrics } from "./agri_metrics.js";
import { ingestTelemetry, pruneSensorReadings, resolveSensorReadingRetentionConfig } from "./sensor_telemetry.js";
import { recordHarvest } from "./harvest_ledger.js";
import { computeGrowCorrelation } from "./agri_correlation.js";
import { buildCalibrationPrBody, suggestBandAdjustments } from "./agri_calibration.js";
import { runKicadVerifier } from "./kicad_verifier.js";
import { runKicadCurator } from "./kicad_curator.js";
import {
  handleWhatsAppVerification,
  handleWhatsAppWebhook,
} from "./github_issues.js";
import {
  handleTelegramWebhook,
  isTelegramWebhookRequest,
} from "./telegram_issues.js";
import { handleDiscordWebhook } from "./discord_api_handler.js";
import { syncExecutionPackFromWebhook, verifyWebhookSignature } from "./execution_pack_webhook.js";
import { applyMigrations } from "./schema_migrations.js";

class AuthError extends Error { }
class ConflictError extends Error { }
class NotFoundError extends Error { }
class ForbiddenError extends Error { }

let startupMigrationPromise = null;

function nowIso() {
  return new Date().toISOString();
}

function badRequest(message) {
  return jsonResponse({ error: message }, 400);
}

function unauthorized(message) {
  return jsonResponse({ error: message }, 401);
}

function conflict(message) {
  return jsonResponse({ error: message }, 409);
}

function forbidden(message) {
  return jsonResponse({ error: message }, 403);
}

function validateProviderDescriptor(payload) {
  const required = ["provider_id", "provider_kind", "provider_label"];
  const missing = required.filter((field) => payload[field] === undefined);
  if (missing.length) {
    throw new Error(`Brak wymaganych pól providera: ${missing.join(", ")}`);
  }
  validateProviderId(payload.provider_id, payload.provider_kind);
  return payload;
}

function validateProviderId(providerId, providerKind) {
  if (typeof providerId !== "string" || providerId.length === 0) {
    throw new Error("Pole provider_id musi być niepustym tekstem.");
  }

  const segments = providerId.split("-");
  if (segments.length < 4) {
    throw new Error(
      "Pole provider_id musi mieć format kind-environment-slug-01, np. community-demo-node-01."
    );
  }

  const segmentPattern = /^[a-z0-9]+$/;
  for (const segment of segments) {
    if (!segment || !segmentPattern.test(segment)) {
      throw new Error(
        "Pole provider_id może zawierać tylko małe litery, cyfry i znak '-'."
      );
    }
  }

  const environment = segments[1];
  const allowedEnvironments = ["local", "demo", "preview", "staging", "prod"];
  if (!allowedEnvironments.includes(environment)) {
    throw new Error(
      `Drugi segment provider_id musi oznaczać środowisko: ${allowedEnvironments.join(", ")}.`
    );
  }

  const suffix = segments[segments.length - 1];
  if (!/^\d{2,}$/.test(suffix)) {
    throw new Error(
      "Ostatni segment provider_id musi być numerycznym sufiksem, np. 01."
    );
  }

  if (providerKind !== undefined) {
    const expectedPrefixes = {
      company: "company",
      farm: "farm",
      community: "community",
      research: "research",
      edge_node: "edge",
    };
    const expectedPrefix = expectedPrefixes[providerKind];
    if (!expectedPrefix) {
      throw new Error(`Nieobsługiwany provider_kind: ${providerKind}.`);
    }
    if (segments[0] !== expectedPrefix) {
      throw new Error(
        `Pierwszy segment provider_id musi odpowiadać provider_kind, np. ${expectedPrefix}-${environment}-...`
      );
    }
  }
}

function getProviderEnvironment(providerId) {
  validateProviderId(providerId);
  return providerId.split("-")[1];
}

function parseAllowedProviderEnvironments(deploymentEnvironment, configuredValue) {
  const allowedEnvironments = ["local", "demo", "preview", "staging", "prod"];
  if (deploymentEnvironment && !allowedEnvironments.includes(deploymentEnvironment)) {
    throw new Error(
      `Nieobsługiwane deployment environment. Dozwolone: ${allowedEnvironments.join(", ")}.`
    );
  }

  if (!configuredValue || !configuredValue.trim()) {
    if (!deploymentEnvironment) {
      return null;
    }
    return new Set([deploymentEnvironment]);
  }

  const normalized = configuredValue.trim().toLowerCase();
  if (normalized === "*") {
    return null;
  }

  const result = new Set();
  for (const part of normalized.split(",")) {
    const environment = part.trim();
    if (!allowedEnvironments.includes(environment)) {
      throw new Error(
        `Nieobsługiwane środowisko providera. Dozwolone: ${allowedEnvironments.join(", ")}.`
      );
    }
    result.add(environment);
  }
  return result;
}

function ensureProviderEnvironmentAllowed(providerId, deploymentEnvironment, allowedEnvironments) {
  const providerEnvironment = getProviderEnvironment(providerId);
  if (allowedEnvironments === null) {
    return providerEnvironment;
  }
  if (!allowedEnvironments.has(providerEnvironment)) {
    const allowed = Array.from(allowedEnvironments).sort().join(", ");
    if (deploymentEnvironment) {
      throw new ForbiddenError(
        `Provider environment nie jest dozwolony w tym środowisku API. provider=${providerEnvironment}, deployment=${deploymentEnvironment}, dozwolone=${allowed}.`
      );
    }
    throw new ForbiddenError(
      `Provider environment nie jest dozwolony w tym środowisku API. provider=${providerEnvironment}, dozwolone=${allowed}.`
    );
  }
  return providerEnvironment;
}

function validateObservation(payload) {
  const required = [
    "schema_version",
    "provider",
    "pond",
    "measurement_time",
    "water_temperature_c",
    "dissolved_oxygen_mg_l",
    "ph",
  ];
  const missing = required.filter((field) => payload[field] === undefined);
  if (missing.length) {
    throw new Error(`Brak wymaganych pól obserwacji: ${missing.join(", ")}`);
  }
  if (payload.schema_version !== "v1") {
    throw new Error("Nieobsługiwana wersja schematu obserwacji.");
  }
  if (!payload.provider || payload.provider.provider_id === undefined) {
    throw new Error("Brak provider.provider_id");
  }
  validateProviderId(payload.provider.provider_id, payload.provider.provider_kind);
  return payload;
}

function validateEvent(payload) {
  const required = ["schema_version", "provider", "pond", "event_time", "event_type"];
  const missing = required.filter((field) => payload[field] === undefined);
  if (missing.length) {
    throw new Error(`Brak wymaganych pól zdarzenia: ${missing.join(", ")}`);
  }
  if (payload.schema_version !== "v1") {
    throw new Error("Nieobsługiwana wersja schematu zdarzenia.");
  }
  if (!payload.provider || payload.provider.provider_id === undefined) {
    throw new Error("Brak provider.provider_id");
  }
  validateProviderId(payload.provider.provider_id, payload.provider.provider_kind);
  if (payload.kind !== undefined && typeof payload.kind !== "string") {
    throw new Error("Pole kind musi być tekstem.");
  }
  return payload;
}

function generateWriteToken() {
  return `fp_${crypto.randomUUID().replace(/-/g, "")}`;
}

async function hashToken(token) {
  const digest = await crypto.subtle.digest(
    "SHA-256",
    new TextEncoder().encode(token)
  );
  return Array.from(new Uint8Array(digest))
    .map((value) => value.toString(16).padStart(2, "0"))
    .join("");
}

async function getProvider(env, providerId) {
  await ensureProviderLifecycleSchema(env);
  return env.DB.prepare(
    `
    SELECT provider_id, provider_kind, provider_label, node_class,
           supports_water_quality, supports_flow_monitoring, supports_edge_vision_summary,
           schema_version, write_token_hash, registered_at, last_seen_at,
           trust_level, provider_status
    FROM providers
    WHERE provider_id = ?
    `
  )
    .bind(providerId)
    .first();
}

async function requireProviderToken(request, env, providerId, options = {}) {
  const token = request.headers.get("X-Provider-Token");
  const provider = await getProvider(env, providerId);
  if (!provider) {
    throw new AuthError("Provider musi zostać najpierw zarejestrowany.");
  }
  if (!token) {
    throw new AuthError("Brak tokenu providera.");
  }
  const tokenHash = await hashToken(token);
  if (provider.write_token_hash !== tokenHash) {
    throw new AuthError("Brak poprawnego tokenu providera.");
  }
  if (!options.allowInactive && !isProviderActive(provider)) {
    throw new ForbiddenError("Provider jest nieaktywny. Wyślij heartbeat lub skontaktuj się z maintainerem.");
  }
  return provider;
}

async function updateProviderSeen(env, providerId) {
  await env.DB.prepare(
    `
    UPDATE providers
    SET last_seen_at = ?, provider_status = 'active'
    WHERE provider_id = ?
    `
  )
    .bind(nowIso(), providerId)
    .run();
}

async function rotateProviderToken(env, providerId) {
  const provider = await getProvider(env, providerId);
  if (!provider) {
    throw new NotFoundError("Nie znaleziono providera.");
  }
  const writeToken = generateWriteToken();
  const writeTokenHash = await hashToken(writeToken);
  await env.DB.prepare(
    `
    UPDATE providers
    SET write_token_hash = ?, last_seen_at = ?, provider_status = 'active'
    WHERE provider_id = ?
    `
  )
    .bind(writeTokenHash, nowIso(), providerId)
    .run();
  return {
    provider_id: providerId,
    rotation_status: "rotated",
    schema_version: "v1",
    message: "Token providera został obrócony.",
    write_token: writeToken,
  };
}

async function ensureProviderLifecycleSchema(env) {
  if (!env?.DB) return { success: false, reason: "no_db" };
  const columns = await env.DB.prepare(`PRAGMA table_info(providers)`).all();
  const names = new Set((columns?.results || []).map((row) => row.name));
  if (!names.has("trust_level")) {
    await env.DB.prepare(
      `ALTER TABLE providers ADD COLUMN trust_level INTEGER NOT NULL DEFAULT 0`
    ).run();
  }
  if (!names.has("provider_status")) {
    await env.DB.prepare(
      `ALTER TABLE providers ADD COLUMN provider_status TEXT NOT NULL DEFAULT 'active'`
    ).run();
  }
  await env.DB.prepare(
    `CREATE TABLE IF NOT EXISTS provider_lifecycle_events (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      provider_id TEXT NOT NULL,
      previous_status TEXT,
      next_status TEXT NOT NULL,
      reason TEXT,
      created_at TEXT NOT NULL
    )`
  ).run();
  await env.DB.prepare(
    `CREATE INDEX IF NOT EXISTS idx_provider_lifecycle_events_provider_created
      ON provider_lifecycle_events(provider_id, created_at)`
  ).run();
  return { success: true };
}

async function ensureProviderTrustLevelColumn(env) {
  return await ensureProviderLifecycleSchema(env);
}

function isProviderActive(provider) {
  return !provider?.provider_status || provider.provider_status === "active";
}

function getProviderTrustLevel(provider) {
  if (!provider) return 0;
  const raw = Number(provider.trust_level);
  if (!Number.isFinite(raw) || raw < 0) return 0;
  return Math.floor(raw);
}

const DECISION_TRUST_LEVEL_REQUIRED = 2;
function getDecisionTrustLevelRequired(env) {
  const raw = Number(env.PROVIDER_DECISION_TRUST_LEVEL);
  if (!Number.isFinite(raw) || raw < 0) return DECISION_TRUST_LEVEL_REQUIRED;
  return Math.floor(raw);
}

async function setProviderTrustLevel(env, providerId, trustLevel) {
  await env.DB.prepare(
    `UPDATE providers SET trust_level = ? WHERE provider_id = ?`
  )
    .bind(trustLevel, providerId)
    .run();
}

function isTrustLevelEditor(env) {
  const editorSecret = env.PROVIDER_TRUST_EDITOR_SECRET;
  if (!editorSecret) return false;
  return true;
}

async function requireTrustLevelEditor(request, env) {
  if (!isTrustLevelEditor(env)) {
    throw new AuthError("Zmiana trust_level wymaga ustawienia PROVIDER_TRUST_EDITOR_SECRET w środowisku Worker.");
  }
  const provided = request.headers.get("X-Trust-Editor-Secret");
  if (!provided || provided !== env.PROVIDER_TRUST_EDITOR_SECRET) {
    throw new AuthError("Brak lub nieprawidłowy X-Trust-Editor-Secret.");
  }
}

function validateTrustLevel(value) {
  const raw = Number(value);
  if (!Number.isInteger(raw) || raw < 0 || raw > 10) {
    throw new Error("trust_level musi być liczbą całkowitą z zakresu 0-10.");
  }
  return raw;
}


function inactiveProviderCutoffIso(now = new Date(), inactiveHours = 72) {
  const hours = Number.isFinite(Number(inactiveHours)) ? Number(inactiveHours) : 72;
  return new Date(now.getTime() - hours * 60 * 60 * 1000).toISOString();
}

export async function autoDeactivateInactiveProviders(env, options = {}) {
  if (!env?.DB) {
    return { success: true, reason: "no_db", deactivated_count: 0 };
  }
  try {
    await ensureProviderLifecycleSchema(env);
    const now = options.now || new Date();
    const inactiveHours = options.inactiveHours || env.PROVIDER_INACTIVE_AFTER_HOURS || 72;
    const cutoff = inactiveProviderCutoffIso(now, inactiveHours);
    const staleRows = await env.DB.prepare(
      `SELECT provider_id, provider_status
       FROM providers
       WHERE last_seen_at < ?
         AND COALESCE(provider_status, 'active') != 'inactive'`
    )
      .bind(cutoff)
      .all();
    const rows = staleRows?.results || [];
    if (!rows.length) {
      return { success: true, deactivated_count: 0, cutoff };
    }
    await env.DB.prepare(
      `UPDATE providers
       SET provider_status = 'inactive'
       WHERE last_seen_at < ?
         AND COALESCE(provider_status, 'active') != 'inactive'`
    )
      .bind(cutoff)
      .run();
    const createdAt = now.toISOString();
    for (const row of rows) {
      await env.DB.prepare(
        `INSERT INTO provider_lifecycle_events
          (provider_id, previous_status, next_status, reason, created_at)
         VALUES (?, ?, ?, ?, ?)`
      )
        .bind(
          row.provider_id,
          row.provider_status || "active",
          "inactive",
          `auto_deactivate_no_heartbeat_${inactiveHours}h`,
          createdAt
        )
        .run();
    }
    return { success: true, deactivated_count: rows.length, cutoff };
  } catch (error) {
    console.error("[provider-lifecycle] auto-deactivate failed open:", error);
    return { success: true, reason: "failed_open", deactivated_count: 0, error: error?.message || String(error) };
  }
}

export {
  validateTrustLevel,
  getProviderTrustLevel,
  getDecisionTrustLevelRequired,
  DECISION_TRUST_LEVEL_REQUIRED,
  isProviderActive,
};

async function upsertProvider(env, provider, writeTokenHash) {
  const currentTime = nowIso();
  await env.DB.prepare(
    `
    INSERT INTO providers (
      provider_id, provider_kind, provider_label, node_class,
      supports_water_quality, supports_flow_monitoring, supports_edge_vision_summary,
      schema_version, write_token_hash, registered_at, last_seen_at, provider_status
    ) VALUES (?, ?, ?, ?, ?, ?, ?, 'v1', ?, ?, ?, 'active')
    ON CONFLICT(provider_id) DO UPDATE SET
      provider_kind = excluded.provider_kind,
      provider_label = excluded.provider_label,
      node_class = excluded.node_class,
      supports_water_quality = excluded.supports_water_quality,
      supports_flow_monitoring = excluded.supports_flow_monitoring,
      supports_edge_vision_summary = excluded.supports_edge_vision_summary,
      write_token_hash = excluded.write_token_hash,
      last_seen_at = excluded.last_seen_at,
      provider_status = 'active'
    `
  )
    .bind(
      provider.provider_id,
      provider.provider_kind,
      provider.provider_label,
      provider.node_class || null,
      provider.supports_water_quality ? 1 : 0,
      provider.supports_flow_monitoring ? 1 : 0,
      provider.supports_edge_vision_summary ? 1 : 0,
      writeTokenHash,
      currentTime,
      currentTime
    )
    .run();
}

async function saveObservation(env, observation) {
  await env.DB.prepare(
    `
    INSERT INTO observations (provider_id, pond_id, measurement_time, payload_json, created_at)
    VALUES (?, ?, ?, ?, ?)
    `
  )
    .bind(
      observation.provider.provider_id,
      observation.pond.pond_id,
      observation.measurement_time,
      JSON.stringify(observation),
      nowIso()
    )
    .run();
}

async function saveEvent(env, eventPayload) {
  await env.DB.prepare(
    `
    INSERT INTO events (provider_id, pond_id, event_time, event_type, payload_json, created_at)
    VALUES (?, ?, ?, ?, ?, ?)
    `
  )
    .bind(
      eventPayload.provider.provider_id,
      eventPayload.pond.pond_id,
      eventPayload.event_time,
      eventPayload.event_type,
      JSON.stringify(eventPayload),
      nowIso()
    )
    .run();
}

async function saveRecommendation(env, recommendation) {
  await env.DB.prepare(
    `
    INSERT INTO recommendations (provider_id, pond_id, analysis_time, payload_json, created_at)
    VALUES (?, ?, ?, ?, ?)
    `
  )
    .bind(
      recommendation.provider_id,
      recommendation.pond_id,
      recommendation.analysis_time,
      JSON.stringify(recommendation),
      nowIso()
    )
    .run();
}

async function readJson(request) {
  try {
    return await request.json();
  } catch {
    throw new Error("Nieprawidłowy JSON.");
  }
}

async function applyStartupMigrations(env) {
  if (!env?.DB) {
    return { success: false, reason: "no_db" };
  }
  if (!startupMigrationPromise) {
    startupMigrationPromise = applyMigrations(env.DB)
      .then((result) => {
        if (!result?.success) {
          startupMigrationPromise = null;
        }
        return result;
      })
      .catch((error) => {
        startupMigrationPromise = null;
        throw error;
      });
  }
  return await startupMigrationPromise;
}

function shouldApplyGlobalRateLimit(request, url, env) {
  if (request.method === "OPTIONS" || url.pathname === "/health") {
    return false;
  }
  if (request.method === "POST" && isTelegramWebhookRequest(url, env)) {
    return false;
  }
  return true;
}

export default {
  async scheduled(_event, env, _ctx) {
    await applyMigrations(env.DB);
    const providerLifecycle = await autoDeactivateInactiveProviders(env);
    const ingest = await runScheduledKicadImport(env);
    const verify = await runKicadVerifier(env);
    const curate = await runKicadCurator(env);
    // T31: retencja streamu zdarzeń i surowych odczytów (agregaty dzienne zostają).
    const eventRetention = resolveEdgeEventRetentionConfig(env);
    const pruneEvents = await pruneEdgeEvents(env.DB, eventRetention);
    const readingRetention = resolveSensorReadingRetentionConfig(env);
    const pruneReadings = await pruneSensorReadings(env.DB, readingRetention);
    return { providerLifecycle, ingest, verify, curate, pruneEvents, pruneReadings };
  },

  async fetch(request, env, ctx) {
    if (request.method === "OPTIONS") {
      return jsonResponse({ ok: true }, 200);
    }

    const url = new URL(request.url);

    // Apply lightweight D1 schema guards once per isolate.
    try {
      const migrationResult = await applyStartupMigrations(env);
      if (migrationResult?.success === false) {
        console.error("[startup] D1 schema migration did not complete:", migrationResult);
      }
    } catch (err) {
      console.error("[startup] D1 schema migration failed:", err);
      // Continue serving requests despite migration failure. Runtime paths also fail open where possible.
    }

    // Global API rate limit check (Z85). Telegram webhooks have chat-level throttling below.
    try {
      if (shouldApplyGlobalRateLimit(request, url, env)) {
        const globalRateLimit = await checkGlobalRateLimit(request, env);
        if (!globalRateLimit.allowed) {
          return jsonResponse({ error: "Too Many Requests", reason: globalRateLimit.reason }, 429);
        }
      }
    } catch (err) {
      console.error("[global-rate-limit] Failed open:", err);
    }

    try {
      if (request.method === "POST" && isTelegramWebhookRequest(url, env)) {
        return await handleTelegramWebhook(request, env, ctx);
      }

      if (request.method === "GET" && url.pathname === "/integrations/telegram/webhook-info") {
        const botToken = env.TELEGRAM_BOT_TOKEN;
        const resp = await fetchWithTimeout(`https://api.telegram.org/bot${botToken}/getWebhookInfo`, {}, 15000);
        return jsonResponse(await resp.json(), 200);
      }

      if (request.method === "GET" && url.pathname === "/integrations/telegram/webhook-reset") {
        const botToken = env.TELEGRAM_BOT_TOKEN;
        // First get current info to preserve url
        const infoResp = await fetchWithTimeout(`https://api.telegram.org/bot${botToken}/getWebhookInfo`, {}, 15000);
        const info = await infoResp.json();
        const currentUrl = info?.result?.url || "https://fish-pond-api-v1-prod.liderpasdom.workers.dev/integrations/telegram/webhook";

        const resetBody = {
          url: currentUrl,
          drop_pending_updates: false,
          allowed_updates: []
        };
        if (env.TELEGRAM_WEBHOOK_SECRET_TOKEN) {
          resetBody.secret_token = env.TELEGRAM_WEBHOOK_SECRET_TOKEN;
        }

        const setResp = await fetchWithTimeout(`https://api.telegram.org/bot${botToken}/setWebhook`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(resetBody)
        }, 15000);
        return jsonResponse(await setResp.json(), 200);
      }

      if (request.method === "GET" && url.pathname === "/integrations/whatsapp/webhook") {
        return handleWhatsAppVerification(url, env);
      }

      if (request.method === "POST" && url.pathname === "/integrations/whatsapp/webhook") {
        return await handleWhatsAppWebhook(request, env);
      }

      if (request.method === "POST" && url.pathname === "/integrations/discord/webhook") {
        return await handleDiscordWebhook(request, env);
      }

      if (request.method === "POST" && url.pathname === "/integrations/github/webhook") {
        // T30: sync statusów execution_packs z GitHub PR webhooks (HMAC, bez merge).
        const secret = env.GITHUB_WEBHOOK_SECRET;
        if (!secret) {
          return jsonResponse({ error: "GitHub webhook not configured." }, 503);
        }
        const rawBody = await request.text();
        const signature = request.headers.get("X-Hub-Signature-256");
        if (!(await verifyWebhookSignature(secret, rawBody, signature))) {
          return jsonResponse({ error: "Invalid signature." }, 401);
        }
        let payload;
        try {
          payload = JSON.parse(rawBody);
        } catch {
          return badRequest("Nieprawidłowy JSON.");
        }
        if (!payload.pull_request) {
          return jsonResponse({ status: "ignored", reason: "not_a_pull_request_event" }, 200);
        }
        const result = await syncExecutionPackFromWebhook(env, payload);
        if (!result.success) {
          return jsonResponse(result, result.reason === "pack_not_found_for_pr_url" ? 404 : 400);
        }
        return jsonResponse(result, 200);
      }

      if (request.method === "GET" && url.pathname === "/health") {
        return jsonResponse({ status: "ok" }, 200);
      }

      if (request.method === "GET" && url.pathname === "/v1/metrics") {
        // Cyber: metryki read-only, ale wymagają X-Trust-Editor-Secret (jak trust-level)
        // aby nie eksponować acceptance rates/false-positive dla anonimów.
        await requireTrustLevelEditor(request, env);
        const snapshot = await computeAutomationMetrics(env);
        return jsonResponse(snapshot, 200);
      }

      if (request.method === "POST" && url.pathname === "/v1/kicad/ingest-jsonl") {
        // T21/B1: realny upstream ingestion path. Admin-only (X-Trust-Editor-Secret).
        // Body: NDJSON z pipelines/import_cern_kicad_library.py. Staging only.
        await requireTrustLevelEditor(request, env);
        const text = await request.text();
        const result = await ingestKicadJsonlPayload(env, text);
        if (!result.success && result.reason === "invalid_payload") {
          return jsonResponse(
            { error: "Invalid JSONL payload", reason: result.reason, errors: result.errors },
            400
          );
        }
        if (!result.success && result.reason === "empty_payload") {
          return jsonResponse({ error: "Empty JSONL payload", reason: result.reason }, 400);
        }
        return jsonResponse(result, 202);
      }

      const deploymentEnvironment = env.DEPLOYMENT_ENVIRONMENT || null;
      const allowedProviderEnvironments = parseAllowedProviderEnvironments(
        deploymentEnvironment,
        env.ALLOWED_PROVIDER_ENVIRONMENTS || ""
      );
      if (request.method === "POST" && url.pathname === "/v1/providers/register") {
        const provider = validateProviderDescriptor(await readJson(request));
        ensureProviderEnvironmentAllowed(
          provider.provider_id,
          deploymentEnvironment,
          allowedProviderEnvironments
        );
        const existingProvider = await getProvider(env, provider.provider_id);
        if (existingProvider) {
          throw new ConflictError("Provider o tym provider_id już istnieje.");
        }
        const writeToken = generateWriteToken();
        const writeTokenHash = await hashToken(writeToken);
        await upsertProvider(env, provider, writeTokenHash);
        return jsonResponse(
          {
            provider_id: provider.provider_id,
            registration_status: "registered",
            schema_version: "v1",
            message: "Provider został zarejestrowany.",
            write_token: writeToken,
          },
          201
        );
      }

      const rotateMatch = url.pathname.match(/^\/v1\/providers\/([^/]+)\/tokens\/rotate$/);
      if (request.method === "POST" && rotateMatch) {
        const providerId = rotateMatch[1];
        ensureProviderEnvironmentAllowed(
          providerId,
          deploymentEnvironment,
          allowedProviderEnvironments
        );
        const existingProvider = await getProvider(env, providerId);
        if (!existingProvider) {
          throw new NotFoundError("Nie znaleziono providera.");
        }
        await requireProviderToken(request, env, providerId, { allowInactive: true });
        const response = await rotateProviderToken(env, providerId);
        return jsonResponse(response, 200);
      }

      const heartbeatMatch = url.pathname.match(/^\/v1\/providers\/([^/]+)\/heartbeat$/);
      if (request.method === "POST" && heartbeatMatch) {
        const providerId = heartbeatMatch[1];
        ensureProviderEnvironmentAllowed(
          providerId,
          deploymentEnvironment,
          allowedProviderEnvironments
        );
        const existingProvider = await getProvider(env, providerId);
        if (!existingProvider) {
          throw new NotFoundError("Nie znaleziono providera.");
        }
        await requireProviderToken(request, env, providerId, { allowInactive: true });
        const providerRateLimit = await checkProviderRateLimit(env, providerId);
        if (!providerRateLimit.allowed) {
          return jsonResponse(
            {
              error: "Too Many Requests for provider",
              reason: providerRateLimit.reason,
              provider_id: providerId,
              retry_after_seconds: providerRateLimit.retry_after_seconds,
            },
            429,
            null,
            null,
            { "Retry-After": String(providerRateLimit.retry_after_seconds || 60) }
          );
        }
        await updateProviderSeen(env, providerId);
        return jsonResponse(
          {
            status: "ok",
            provider_id: providerId,
            last_seen_at_iso: nowIso(),
            trust_level: getProviderTrustLevel(existingProvider),
          },
          200
        );
      }

      const trustLevelMatch = url.pathname.match(/^\/v1\/providers\/([^/]+)\/trust-level$/);
      if (request.method === "PATCH" && trustLevelMatch) {
        const providerId = trustLevelMatch[1];
        ensureProviderEnvironmentAllowed(
          providerId,
          deploymentEnvironment,
          allowedProviderEnvironments
        );
        const existingProvider = await getProvider(env, providerId);
        if (!existingProvider) {
          throw new NotFoundError("Nie znaleziono providera.");
        }
        await requireTrustLevelEditor(request, env);
        const body = await readJson(request);
        const requestedLevel = validateTrustLevel(body?.trust_level);
        await setProviderTrustLevel(env, providerId, requestedLevel);
        return jsonResponse(
          {
            status: "updated",
            provider_id: providerId,
            trust_level: requestedLevel,
            decision_trust_level_required: getDecisionTrustLevelRequired(env),
          },
          200
        );
      }

      if (request.method === "POST" && url.pathname === "/v1/observations") {
        const observation = validateObservation(await readJson(request));
        ensureProviderEnvironmentAllowed(
          observation.provider.provider_id,
          deploymentEnvironment,
          allowedProviderEnvironments
        );
        await requireProviderToken(request, env, observation.provider.provider_id);
        const providerRateLimit = await checkProviderRateLimit(env, observation.provider.provider_id);
        if (!providerRateLimit.allowed) {
          return jsonResponse(
            {
              error: "Too Many Requests for provider",
              reason: providerRateLimit.reason,
              provider_id: observation.provider.provider_id,
              limit: providerRateLimit.limit,
              current: providerRateLimit.current,
              retry_after_seconds: providerRateLimit.retry_after_seconds,
            },
            429,
            null,
            null,
            { "Retry-After": String(providerRateLimit.retry_after_seconds || 60) }
          );
        }
        await saveObservation(env, observation);
        await updateProviderSeen(env, observation.provider.provider_id);
        return jsonResponse(
          {
            status: "accepted",
            provider_id: observation.provider.provider_id,
            pond_id: observation.pond.pond_id,
          },
          202
        );
      }

      if (request.method === "POST" && url.pathname === "/v1/events") {
        const eventPayload = validateEvent(await readJson(request));
        ensureProviderEnvironmentAllowed(
          eventPayload.provider.provider_id,
          deploymentEnvironment,
          allowedProviderEnvironments
        );
        const provider = await requireProviderToken(request, env, eventPayload.provider.provider_id);
        const providerRateLimit = await checkProviderRateLimit(env, eventPayload.provider.provider_id);
        if (!providerRateLimit.allowed) {
          return jsonResponse(
            {
              error: "Too Many Requests for provider",
              reason: providerRateLimit.reason,
              provider_id: eventPayload.provider.provider_id,
              limit: providerRateLimit.limit,
              current: providerRateLimit.current,
              retry_after_seconds: providerRateLimit.retry_after_seconds,
            },
            429,
            null,
            null,
            { "Retry-After": String(providerRateLimit.retry_after_seconds || 60) }
          );
        }
        const eventKind = eventPayload.kind || "telemetry";
        if (eventKind === "decision") {
          const providerTrust = getProviderTrustLevel(provider);
          const required = getDecisionTrustLevelRequired(env);
          if (providerTrust < required) {
            return jsonResponse(
              {
                error: "Forbidden: trust_level insufficient for decision event",
                provider_id: eventPayload.provider.provider_id,
                trust_level: providerTrust,
                required_trust_level: required,
              },
              403
            );
          }
        }
        await saveEvent(env, eventPayload);
        await updateProviderSeen(env, eventPayload.provider.provider_id);
        return jsonResponse(
          {
            status: "accepted",
            provider_id: eventPayload.provider.provider_id,
            pond_id: eventPayload.pond.pond_id,
            event_kind: eventKind,
          },
          202
        );
      }

      if (request.method === "POST" && url.pathname === "/v1/recommendations/fish-pond") {
        const payload = await readJson(request);
        if (!payload.observation) {
          throw new Error("Brak pola observation.");
        }
        const observation = validateObservation(payload.observation);
        ensureProviderEnvironmentAllowed(
          observation.provider.provider_id,
          deploymentEnvironment,
          allowedProviderEnvironments
        );
        await requireProviderToken(request, env, observation.provider.provider_id);
        const lastEvent = payload.last_behavior_event
          ? validateEvent(payload.last_behavior_event)
          : null;
        const recommendation = generateRecommendation(observation, lastEvent);
        await saveRecommendation(env, recommendation);
        // T22: publikuj rekomendację na edge event stream (polling-safe feed).
        try {
          await publishEdgeEvent(env, {
            provider_id: observation.provider.provider_id,
            kind: "recommendation",
            severity: "info",
            payload: recommendation,
          });
        } catch (err) {
          console.error("[edge-event-stream] publish failed:", err);
        }
        await updateProviderSeen(env, observation.provider.provider_id);
        return jsonResponse(recommendation, 200);
      }

      if (request.method === "GET" && url.pathname === "/v1/ws/events") {
        // T22: polling-safe stream zdarzeń dla węzłów edge (alternatywa WebSocket).
        const query = parseEdgeStreamQuery(url);
        await requireProviderToken(request, env, query.provider_id);
        const feed = await listEdgeEventsSince(env.DB, query.provider_id, query.since_id, query.limit);
        return jsonResponse(feed, 200);
      }

      if (request.method === "POST" && url.pathname === "/v1/agri/policy") {
        // T27: admin-only upsert polityki uprawy (kontrakt agri_autopilot/schema.json).
        await requireTrustLevelEditor(request, env);
        const policy = await readJson(request);
        const result = await upsertAgriPolicy(env, policy);
        if (!result.success) {
          return jsonResponse(
            { error: "Invalid grow policy", reason: result.reason, errors: result.errors || [] },
            400
          );
        }
        return jsonResponse(result, 201);
      }

      if (request.method === "POST" && url.pathname === "/v1/agri/evaluate") {
        // T27/T33/T35: odczyty -> zdarzenia edge. Polityka przez policy_id
        // LUB aktywna wersja dla grow_cell_id. Opcjonalna instancja
        // (instance_grow_cell_id) autoryzuje się własnym tokenem i ma własny budżet.
        const payload = await readJson(request);
        let policy = payload?.policy_id ? await getAgriPolicy(env.DB, payload.policy_id) : null;
        if (!policy && payload?.grow_cell_id) {
          policy = await getActiveAgriPolicy(env.DB, payload.grow_cell_id);
        }
        if (!policy) {
          throw new NotFoundError("Nie znaleziono aktywnej polityki uprawy.");
        }
        const instanceGrowCellId = String(payload?.instance_grow_cell_id || "").trim() || policy.grow_cell_id;
        ensureProviderEnvironmentAllowed(instanceGrowCellId, deploymentEnvironment, allowedProviderEnvironments);
        await requireProviderToken(request, env, instanceGrowCellId);
        const result = await runAgriEvaluate(env, policy.id, payload?.readings || {}, { policy, instanceGrowCellId });
        if (!result.success) {
          return jsonResponse({ error: "Evaluate failed", reason: result.reason }, 400);
        }
        return jsonResponse(result, 200);
      }

      if (request.method === "GET" && url.pathname === "/v1/agri/metrics") {
        // T32: dashboard metryk upraw (read-only, admin-only jak /v1/metrics).
        await requireTrustLevelEditor(request, env);
        const snapshot = await computeAgriMetrics(env);
        return jsonResponse(snapshot, 200);
      }

      const correlationMatch = url.pathname.match(/^\/v1\/agri\/correlation$/);
      if (request.method === "GET" && correlationMatch) {
        // T37: korelacja plon<->telemetria dla komórki (auth tokenem providera).
        const providerId = url.searchParams.get("provider_id") || "";
        if (!providerId.trim()) {
          throw new Error("Parametr provider_id jest wymagany.");
        }
        ensureProviderEnvironmentAllowed(providerId.trim(), deploymentEnvironment, allowedProviderEnvironments);
        await requireProviderToken(request, env, providerId.trim());
        const monthsBack = url.searchParams.get("months");
        const result = await computeGrowCorrelation(env, providerId.trim(), {
          monthsBack: monthsBack ? Number(monthsBack) : undefined,
        });
        return jsonResponse(result, 200);
      }

      if (request.method === "POST" && url.pathname === "/v1/agri/calibration-suggest") {
        // T38: suggest-only kalibracja pasm. Admin-only; wynik NIGDY nie jest
        // zapisywany — człowiek tworzy PR przez flow B5/T23/T30.
        await requireTrustLevelEditor(request, env);
        const payload = await readJson(request);
        let policy = null;
        if (payload?.policy_id) {
          policy = await getAgriPolicy(env.DB, payload.policy_id);
        } else if (payload?.grow_cell_id) {
          policy = await getActiveAgriPolicy(env.DB, payload.grow_cell_id);
        }
        if (!policy) {
          throw new NotFoundError("Nie znaleziono polityki uprawy.");
        }
        const correlation = payload?.correlation
          || await computeGrowCorrelation(env, policy.grow_cell_id, { monthsBack: payload?.months_back });
        if (!correlation.success) {
          return jsonResponse({ error: "Correlation unavailable", reason: correlation.reason }, 400);
        }
        const suggestionResult = suggestBandAdjustments(policy, correlation, {
          minMonths: payload?.min_months,
          minAbsR: payload?.min_abs_r,
          stepPercent: payload?.step_percent,
        });
        return jsonResponse({
          success: true,
          suggestion: suggestionResult,
          pull_request_body: buildCalibrationPrBody(policy, suggestionResult),
        }, 200);
      }

      const agriDeactivateMatch = url.pathname.match(/^\/v1\/agri\/policies\/([^/]+)\/deactivate$/);
      if (request.method === "POST" && agriDeactivateMatch) {
        // T33: dezaktywacja polityki z wskaźnikiem następcy (rotacja sezonowa).
        await requireTrustLevelEditor(request, env);
        const body = await readJson(request).catch(() => ({}));
        const result = await deactivateAgriPolicy(env, decodeURIComponent(agriDeactivateMatch[1]), body?.superseded_by);
        if (!result.success) {
          return jsonResponse(result, result.reason === "not_found_or_inactive" ? 404 : 400);
        }
        return jsonResponse(result, 200);
      }

      if (request.method === "POST" && url.pathname === "/v1/agri/telemetry") {
        // T29: batch NDJSON odczytów czujników -> staging + agregaty dzienne (B4).
        const providerId = url.searchParams.get("provider_id") || "";
        if (!providerId.trim()) {
          throw new Error("Parametr provider_id jest wymagany.");
        }
        ensureProviderEnvironmentAllowed(providerId.trim(), deploymentEnvironment, allowedProviderEnvironments);
        await requireProviderToken(request, env, providerId.trim());
        const text = await request.text();
        const result = await ingestTelemetry(env, providerId.trim(), text);
        if (!result.success && result.reason === "invalid_payload") {
          return jsonResponse({ error: "Invalid telemetry payload", reason: result.reason, errors: result.errors }, 400);
        }
        if (!result.success && result.reason === "empty_payload") {
          return jsonResponse({ error: "Empty telemetry payload", reason: result.reason }, 400);
        }
        return jsonResponse(result, 202);
      }

      if (request.method === "POST" && url.pathname === "/v1/agri/harvest") {
        // T36: rejestr plonu per komórka -> ledger + agregat miesięczny (pętla uczenia).
        const providerId = url.searchParams.get("provider_id") || "";
        if (!providerId.trim()) {
          throw new Error("Parametr provider_id jest wymagany.");
        }
        ensureProviderEnvironmentAllowed(providerId.trim(), deploymentEnvironment, allowedProviderEnvironments);
        await requireProviderToken(request, env, providerId.trim());
        const record = await readJson(request);
        const result = await recordHarvest(env, providerId.trim(), record);
        if (!result.success && result.reason === "invalid_record") {
          return jsonResponse({ error: "Invalid harvest record", reason: result.reason, errors: result.errors }, 400);
        }
        if (!result.success && result.reason === "duplicate_harvest") {
          return jsonResponse(result, 409);
        }
        return jsonResponse(result, 202);
      }

      const statusMatch = url.pathname.match(/^\/v1\/providers\/([^/]+)\/status$/);
      if (request.method === "GET" && statusMatch) {
        await ensureProviderLifecycleSchema(env);
        const providerId = statusMatch[1];
        const result = await env.DB.prepare(
          `
          SELECT provider_id, schema_version, last_seen_at,
                 supports_water_quality, supports_flow_monitoring, supports_edge_vision_summary,
                 provider_status
          FROM providers
          WHERE provider_id = ?
          `
        )
          .bind(providerId)
          .first();

        if (!result) {
          return jsonResponse({ error: "Nie znaleziono providera." }, 404);
        }

        return jsonResponse(
          {
            provider_id: result.provider_id,
            status: result.provider_status || "active",
            last_seen_at: result.last_seen_at,
            schema_version: result.schema_version,
            supports_water_quality: Boolean(result.supports_water_quality),
            supports_flow_monitoring: Boolean(result.supports_flow_monitoring),
            supports_edge_vision_summary: Boolean(result.supports_edge_vision_summary),
          },
          200
        );
      }

      return jsonResponse({ error: "Nie znaleziono zasobu." }, 404);
    } catch (error) {
      if (error instanceof AuthError) {
        return unauthorized(error.message || "Brak autoryzacji.");
      }
      if (error instanceof ConflictError) {
        return conflict(error.message || "Konflikt providera.");
      }
      if (error instanceof NotFoundError) {
        return jsonResponse({ error: error.message || "Nie znaleziono zasobu." }, 404);
      }
      if (error instanceof ForbiddenError) {
        return forbidden(error.message || "Brak uprawnień do tego środowiska.");
      }
      return badRequest(error.message || "Błąd żądania.");
    }
  },
};
