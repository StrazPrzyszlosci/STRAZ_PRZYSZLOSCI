export const DEFAULT_WEBHOOK_BODY_BYTES = 5242880;

export function getMaxPayloadBytes(env = {}, opts = {}) {
  const {
    envKey,
    fallbackKey = "MAX_WEBHOOK_BODY_BYTES",
    defaultMax = DEFAULT_WEBHOOK_BODY_BYTES,
  } = opts;
  const specificValue = envKey ? env?.[envKey] : undefined;
  const fallbackValue = fallbackKey ? env?.[fallbackKey] : undefined;
  const rawValue = specificValue || fallbackValue || String(defaultMax);
  return parseInt(rawValue, 10);
}

export function checkPayloadSize(request, env = {}, opts = {}) {
  const {
    envKey,
    fallbackKey = "MAX_WEBHOOK_BODY_BYTES",
    defaultMax = DEFAULT_WEBHOOK_BODY_BYTES,
    responseFactory,
    errorMessage = "Payload Too Large",
    includeMaxBytes = true,
    disableWhenNonPositive = true,
  } = opts;
  const maxBodyBytes = getMaxPayloadBytes(env, { envKey, fallbackKey, defaultMax });
  const contentLength = request?.headers?.get("Content-Length");
  const parsedContentLength = parseInt(contentLength || "", 10);

  if (
    contentLength &&
    Number.isFinite(parsedContentLength) &&
    parsedContentLength > 0 &&
    Number.isFinite(maxBodyBytes) &&
    (!disableWhenNonPositive || maxBodyBytes > 0) &&
    parsedContentLength > maxBodyBytes
  ) {
    const payload = includeMaxBytes
      ? { error: errorMessage, max_bytes: maxBodyBytes }
      : { error: errorMessage };
    return responseFactory(payload, 413, env, request);
  }
  return null;
}
