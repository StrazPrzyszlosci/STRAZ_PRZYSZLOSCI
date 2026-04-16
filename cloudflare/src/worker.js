import { generateRecommendation } from "./recommendation.js";
import {
  handleWhatsAppVerification,
  handleWhatsAppWebhook,
} from "./github_issues.js";
import {
  handleTelegramWebhook,
  isTelegramWebhookRequest,
} from "./telegram_issues.js";

class AuthError extends Error { }
class ConflictError extends Error { }
class NotFoundError extends Error { }
class ForbiddenError extends Error { }

function jsonResponse(payload, status = 200) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "access-control-allow-origin": "*",
      "access-control-allow-methods": "GET,POST,OPTIONS",
      "access-control-allow-headers":
        "content-type,x-provider-token,x-hub-signature-256,x-telegram-bot-api-secret-token",
    },
  });
}

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
  return env.DB.prepare(
    `
    SELECT provider_id, provider_kind, provider_label, node_class,
           supports_water_quality, supports_flow_monitoring, supports_edge_vision_summary,
           schema_version, write_token_hash, registered_at, last_seen_at
    FROM providers
    WHERE provider_id = ?
    `
  )
    .bind(providerId)
    .first();
}

async function requireProviderToken(request, env, providerId) {
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
  return provider;
}

async function updateProviderSeen(env, providerId) {
  await env.DB.prepare(
    `
    UPDATE providers
    SET last_seen_at = ?
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
    SET write_token_hash = ?, last_seen_at = ?
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

async function upsertProvider(env, provider, writeTokenHash) {
  const currentTime = nowIso();
  await env.DB.prepare(
    `
    INSERT INTO providers (
      provider_id, provider_kind, provider_label, node_class,
      supports_water_quality, supports_flow_monitoring, supports_edge_vision_summary,
      schema_version, write_token_hash, registered_at, last_seen_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, 'v1', ?, ?, ?)
    ON CONFLICT(provider_id) DO UPDATE SET
      provider_kind = excluded.provider_kind,
      provider_label = excluded.provider_label,
      node_class = excluded.node_class,
      supports_water_quality = excluded.supports_water_quality,
      supports_flow_monitoring = excluded.supports_flow_monitoring,
      supports_edge_vision_summary = excluded.supports_edge_vision_summary,
      write_token_hash = excluded.write_token_hash,
      last_seen_at = excluded.last_seen_at
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

export default {
  async fetch(request, env) {
    if (request.method === "OPTIONS") {
      return jsonResponse({ ok: true }, 200);
    }

    const url = new URL(request.url);

    try {
      if (request.method === "POST" && isTelegramWebhookRequest(url, env)) {
        return await handleTelegramWebhook(request, env, ctx);
      }

      if (request.method === "GET" && url.pathname === "/integrations/telegram/webhook-info") {
        const botToken = env.TELEGRAM_BOT_TOKEN;
        const resp = await fetch(`https://api.telegram.org/bot${botToken}/getWebhookInfo`);
        return jsonResponse(await resp.json(), 200);
      }

      if (request.method === "GET" && url.pathname === "/integrations/telegram/webhook-reset") {
        const botToken = env.TELEGRAM_BOT_TOKEN;
        // First get current info to preserve url
        const infoResp = await fetch(`https://api.telegram.org/bot${botToken}/getWebhookInfo`);
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

        const setResp = await fetch(`https://api.telegram.org/bot${botToken}/setWebhook`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(resetBody)
        });
        return jsonResponse(await setResp.json(), 200);
      }

      if (request.method === "GET" && url.pathname === "/integrations/whatsapp/webhook") {
        return handleWhatsAppVerification(url, env);
      }

      if (request.method === "POST" && url.pathname === "/integrations/whatsapp/webhook") {
        return await handleWhatsAppWebhook(request, env);
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
        await requireProviderToken(request, env, providerId);
        const response = await rotateProviderToken(env, providerId);
        return jsonResponse(response, 200);
      }

      if (request.method === "POST" && url.pathname === "/v1/observations") {
        const observation = validateObservation(await readJson(request));
        ensureProviderEnvironmentAllowed(
          observation.provider.provider_id,
          deploymentEnvironment,
          allowedProviderEnvironments
        );
        await requireProviderToken(request, env, observation.provider.provider_id);
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
        await requireProviderToken(request, env, eventPayload.provider.provider_id);
        await saveEvent(env, eventPayload);
        await updateProviderSeen(env, eventPayload.provider.provider_id);
        return jsonResponse(
          {
            status: "accepted",
            provider_id: eventPayload.provider.provider_id,
            pond_id: eventPayload.pond.pond_id,
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
        await updateProviderSeen(env, observation.provider.provider_id);
        return jsonResponse(recommendation, 200);
      }

      const statusMatch = url.pathname.match(/^\/v1\/providers\/([^/]+)\/status$/);
      if (request.method === "GET" && statusMatch) {
        const providerId = statusMatch[1];
        const result = await env.DB.prepare(
          `
          SELECT provider_id, schema_version, last_seen_at,
                 supports_water_quality, supports_flow_monitoring, supports_edge_vision_summary
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
            status: "ok",
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
