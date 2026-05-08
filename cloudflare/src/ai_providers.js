import { AiProviderError, parsePositiveInteger, parseNumber } from "./base_utils.js";
import { checkModelRateLimit, recordModelUsage } from "./ai_model_limits.js";

const DEFAULT_TIMEOUT_MS = 20000;

function extractTextFromGoogle(payload) {
  const text = payload?.candidates?.[0]?.content?.parts
    ?.map((part) => part?.text || "")
    .join("")
    .trim();
  if (!text) {
    throw new AiProviderError("Google AI Studio nie zwrócił treści.", {
      retriable: true,
    });
  }
  return text;
}

function extractTextFromNvidia(payload) {
  const text = payload?.choices?.[0]?.message?.content?.trim();
  if (!text) {
    throw new AiProviderError("NVIDIA NIM nie zwrócił treści.", {
      retriable: true,
    });
  }
  return text;
}

async function runFetchWithTimeout(fetchImpl, url, init, timeoutMs) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetchImpl(url, { ...init, signal: controller.signal });
  } catch (error) {
    if (error?.name === "AbortError") {
      throw new AiProviderError("Upłynął limit czasu odpowiedzi modelu.", {
        retriable: true,
      });
    }
    throw error;
  } finally {
    clearTimeout(timeoutId);
  }
}

function buildGoogleGenerateContentBody(promptPayload, model, options = {}) {
  const isGemma = (model || "").toLowerCase().includes("gemma");
  const inlineSystemInstruction = options.inlineSystemInstruction === true || isGemma;

  const userParts = [];

  if (inlineSystemInstruction && promptPayload.systemInstruction) {
    userParts.push({ text: promptPayload.systemInstruction + "\n\n" });
  }

  if (promptPayload.userPrompt) {
    userParts.push({ text: promptPayload.userPrompt });
  }

  if (promptPayload.media && promptPayload.media.length > 0) {
    for (const mediaItem of promptPayload.media) {
      userParts.push({
        inline_data: {
          mime_type: mediaItem.mime_type,
          data: mediaItem.data,
        },
      });
    }
  }

  const body = {
    contents: [
      {
        role: "user",
        parts: userParts,
      },
    ],
    generationConfig: {
      temperature: promptPayload.temperature,
      topP: 0.95,
      maxOutputTokens: promptPayload.maxTokens,
    },
  };

  if (!isGemma && promptPayload.responseMimeType) {
    body.generationConfig.responseMimeType = promptPayload.responseMimeType;
  }

  if (!inlineSystemInstruction && promptPayload.systemInstruction) {
    body.systemInstruction = {
      parts: [{ text: promptPayload.systemInstruction }],
    };
  }

  return body;
}

function shouldRetryGoogleWithoutDeveloperInstruction(response, payload) {
  if (response?.ok) {
    return false;
  }
  if (response?.status !== 400) {
    return false;
  }

  const errorMessage = String(payload?.error?.message || "").toLowerCase();
  return (
    errorMessage.includes("developer instruction is not enabled") ||
    errorMessage.includes("system instruction") ||
    errorMessage.includes("system instructions")
  );
}

export async function callGoogleProvider(env, promptPayload, options = {}) {
  // Per-model rate limit check
  if (env.DB) {
    const model = (env.TELEGRAM_AI_GOOGLE_MODEL || "gemini-3.1-flash-lite-preview").trim();
    const modelLimitResult = await checkModelRateLimit(env, env.DB, model, "google");
    if (!modelLimitResult.allowed) {
      throw new AiProviderError(`Rate limit Google model (${modelLimitResult.bucket}): try after ${modelLimitResult.retry_after_seconds}s.`, {
        retriable: true,
      });
    }
  }

  const apiKey = (env.GEMINI_API_KEY || "").trim();
  if (!apiKey) {
    throw new AiProviderError("Brak GEMINI_API_KEY.", {
      provider: "google",
      model: env.TELEGRAM_AI_GOOGLE_MODEL || "gemini-3.1-flash-lite-preview",
      retriable: true,
    });
  }

  const model = (env.TELEGRAM_AI_GOOGLE_MODEL || "gemini-3.1-flash-lite-preview").trim();
  const timeoutMs = parsePositiveInteger(env.TELEGRAM_AI_TIMEOUT_MS, DEFAULT_TIMEOUT_MS);
  const fetchImpl = options.fetchImpl || fetch;
  const endpoint = `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${encodeURIComponent(apiKey)}`;

  let response = await runFetchWithTimeout(
    fetchImpl,
    endpoint,
    {
      method: "POST",
      headers: {
        "content-type": "application/json; charset=utf-8",
      },
      body: JSON.stringify(buildGoogleGenerateContentBody(promptPayload, model)),
    },
    timeoutMs
  );

  let payload = await response.json().catch(() => ({}));
  if (shouldRetryGoogleWithoutDeveloperInstruction(response, payload)) {
    response = await runFetchWithTimeout(
      fetchImpl,
      endpoint,
      {
        method: "POST",
        headers: {
          "content-type": "application/json; charset=utf-8",
        },
        body: JSON.stringify(
          buildGoogleGenerateContentBody(promptPayload, model, {
            inlineSystemInstruction: true,
          })
        ),
      },
      timeoutMs
    );
    payload = await response.json().catch(() => ({}));
  }

  if (!response.ok) {
    throw new AiProviderError(payload?.error?.message || "Google AI Studio odrzucił żądanie.", {
      status: response.status,
      provider: "google",
      model,
      retriable:
        response.status === 429 ||
        response.status >= 500 ||
        shouldRetryGoogleWithoutDeveloperInstruction(response, payload),
    });
  }

  if (env.DB) {
    await recordModelUsage(env, env.DB, model, "google").catch(() => {});
  }

  return {
    text: extractTextFromGoogle(payload),
    provider_name: "google",
    model_name: model,
  };
}

export async function callNvidiaProvider(env, promptPayload, options = {}) {
  // Per-model rate limit check
  if (env.DB) {
    const model = (env.TELEGRAM_AI_NVIDIA_MODEL || "google/gemma-4-31b-it").trim();
    const modelLimitResult = await checkModelRateLimit(env, env.DB, model, "nvidia");
    if (!modelLimitResult.allowed) {
      throw new AiProviderError(`Rate limit NVIDIA model (${modelLimitResult.bucket}): try after ${modelLimitResult.retry_after_seconds}s.`, {
        retriable: true,
      });
    }
  }

  const apiKey = (env.NVIDIA_API_KEY || "").trim();
  if (!apiKey) {
    throw new AiProviderError("Brak NVIDIA_API_KEY.", {
      provider: "nvidia",
      model: env.TELEGRAM_AI_NVIDIA_MODEL || "google/gemma-4-31b-it",
      retriable: true,
    });
  }

  const model = (env.TELEGRAM_AI_NVIDIA_MODEL || "google/gemma-4-31b-it").trim();
  const timeoutMs = parsePositiveInteger(env.TELEGRAM_AI_TIMEOUT_MS, DEFAULT_TIMEOUT_MS);
  const fetchImpl = options.fetchImpl || fetch;

  const response = await runFetchWithTimeout(
    fetchImpl,
    "https://integrate.api.nvidia.com/v1/chat/completions",
    {
      method: "POST",
      headers: {
        authorization: `Bearer ${apiKey}`,
        accept: "application/json",
        "content-type": "application/json; charset=utf-8",
      },
      body: JSON.stringify({
        model,
        messages: [
          { role: "system", content: promptPayload.systemInstruction },
          { role: "user", content: promptPayload.userPrompt },
        ],
        max_tokens: promptPayload.maxTokens,
        temperature: promptPayload.temperature,
        top_p: 0.95,
        stream: false,
        chat_template_kwargs: {
          enable_thinking: true,
        },
      }),
    },
    timeoutMs
  );

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new AiProviderError(payload?.error?.message || "NVIDIA NIM odrzucił żądanie.", {
      status: response.status,
      provider: "nvidia",
      model,
      retriable: response.status === 429 || response.status >= 500,
    });
  }

  if (env.DB) {
    await recordModelUsage(env, env.DB, model, "nvidia").catch(() => {});
  }

  return {
    text: extractTextFromNvidia(payload),
    provider_name: "nvidia",
    model_name: model,
  };
}

export async function callProviderWithFallback(env, promptPayload, options = {}) {
  const primary = (env.TELEGRAM_AI_PRIMARY_PROVIDER || "google").trim().toLowerCase();
  const fallback = (env.TELEGRAM_AI_FALLBACK_PROVIDER || "nvidia").trim().toLowerCase();
  const orderedProviders = Array.from(new Set([primary, fallback])).filter(Boolean);
  let lastError = null;

  for (const provider of orderedProviders) {
    try {
      if (provider === "google") {
        return await callGoogleProvider(env, promptPayload, options);
      }
      if (provider === "nvidia") {
        if (promptPayload.media?.length) {
          if (!lastError) {
            lastError = new AiProviderError(
              "NVIDIA fallback w tym workerze nie obsluguje promptow z mediami.",
              {
                provider,
                model: env.TELEGRAM_AI_NVIDIA_MODEL || "google/gemma-4-31b-it",
                retriable: false,
              }
            );
          }
          continue;
        }
        return await callNvidiaProvider(env, promptPayload, options);
      }
      throw new AiProviderError(`Nieobsługiwany provider AI: ${provider}.`, {
        provider,
        retriable: false,
      });
    } catch (error) {
      lastError = error;
      if (!(error instanceof AiProviderError) || !error.retriable) {
        throw error;
      }
    }
  }

  throw lastError || new AiProviderError("Nie udało się połączyć z providerem AI.");
}
