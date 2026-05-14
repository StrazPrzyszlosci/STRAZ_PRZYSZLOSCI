export function getCorsAllowOrigin(env, request) {
  if (!env) return "*";
  const configured = (env.CORS_ALLOWED_ORIGINS || "").trim();
  if (!configured || configured === "*") return "*";
  const allowed = new Set(configured.split(",").map((s) => s.trim()).filter(Boolean));
  if (allowed.size === 0) return "*";
  if (!request) return Array.from(allowed)[0];
  const origin = request.headers.get("Origin");
  if (origin && allowed.has(origin)) return origin;
  return Array.from(allowed)[0];
}

export function getSecurityHeaders(env = null, request = null) {
  const corsOrigin = env ? getCorsAllowOrigin(env, request) : "*";
  return {
    "content-type": "application/json; charset=utf-8",
    "access-control-allow-origin": corsOrigin,
    "access-control-allow-methods": "GET,POST,OPTIONS",
    "access-control-allow-headers":
      "content-type,x-provider-token,x-hub-signature-256,x-telegram-bot-api-secret-token,x-discord-bot-secret",
    "strict-transport-security": "max-age=31536000; includeSubDomains",
    "x-content-type-options": "nosniff",
    "x-frame-options": "DENY",
    "referrer-policy": "strict-origin-when-cross-origin",
    "content-security-policy": "default-src 'none'; frame-ancestors 'none'",
    "permissions-policy": "geolocation=(), camera=(), microphone=(), accelerometer=(), magnetometer=(), gyroscope=(), payment=(), usb=()",
  };
}

export function jsonResponse(payload, status = 200, env = null, request = null) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: getSecurityHeaders(env, request),
  });
}
