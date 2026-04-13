import test from "node:test";
import assert from "node:assert/strict";

import {
  buildIssueBody,
  buildIssueTitle,
  callProviderWithFallback,
  extractJsonObject,
  moderateIssueCandidate,
  recommendOnboardingRouteFromText,
  redactSensitiveContent,
  routeTelegramIntent,
  sanitizeTelegramReply,
} from "../src/telegram_ai.js";
import { handleTelegramWebhook } from "../src/telegram_issues.js";

function jsonResponse(payload, status = 200) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
    },
  });
}

function withMockedFetch(impl, callback) {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = impl;
  return Promise.resolve()
    .then(callback)
    .finally(() => {
      globalThis.fetch = originalFetch;
    });
}

test("routeTelegramIntent keeps onboarding separate from issues", () => {
  assert.deepEqual(routeTelegramIntent("Pomysl: zróbmy panel porównań").intent, "issue");
  assert.deepEqual(routeTelegramIntent("Gdzie mogę pomóc jako backendowiec?").intent, "onboarding");
  assert.deepEqual(routeTelegramIntent("Opowiedz mi więcej o inicjatywie").intent, "chat");
});

test("recommendOnboardingRouteFromText finds data path without hardware", () => {
  const result = recommendOnboardingRouteFromText(
    "Nie mam własnego sprzętu, ale znam backend, API, walidację i mogę pomagać w architekturze danych."
  );
  assert.ok(result);
  assert.equal(result.route.route_id, "data_architecture_without_hardware");
  assert.equal(result.should_suggest_provider_path, true);
});

test("buildIssueTitle keeps original message trimmed without AI rewrite", () => {
  const title = buildIssueTitle({
    content:
      "To jest bardzo długi oryginalny wpis użytkownika, który powinien zostać przycięty, ale bez przepisywania przez AI i bez dodawania prefiksu.",
  });
  assert.equal(title.startsWith("To jest bardzo długi oryginalny wpis użytkownika"), true);
  assert.equal(title.length, 96);
});

test("buildIssueBody stores original and edited text in separate sections", () => {
  const body = buildIssueBody(
    {
      username: "tester",
      chat_id: "123",
      message_id: "7",
      chat_type: "private",
    },
    {
      label: "pomysł",
      content: "surowa tresc telegramowa",
    },
    {
      edited_description: "Uporządkowany opis bez zmiany sensu.",
      additional_context: "Warto powiązać to z istniejącym projektem.",
    }
  );

  assert.match(body, /## Oryginalna wiadomość/);
  assert.match(body, /surowa tresc telegramowa/);
  assert.match(body, /## Zredagowany opis/);
  assert.match(body, /Uporządkowany opis bez zmiany sensu\./);
  assert.match(body, /## Dodatkowe objaśnienie AI/);
});

test("extractJsonObject parses fenced JSON payloads", () => {
  const parsed = extractJsonObject('```json\n{"decision":"accept","reason_code":"ok","reason_text":"OK"}\n```');
  assert.equal(parsed.decision, "accept");
  assert.equal(parsed.reason_code, "ok");
});

test("redaction hides tokens and secret variable names", () => {
  const redacted = redactSensitiveContent(
    "Sekret AIzaSyBardzoTajny123456789012345 i GITHUB_TOKEN oraz Bearer abcdefghijklmnopqrstuvwxyz0123456789"
  );
  assert.doesNotMatch(redacted, /AIza/);
  assert.doesNotMatch(redacted, /GITHUB_TOKEN/);
  assert.doesNotMatch(redacted, /Bearer\s+[A-Za-z0-9._-]{20,}/);
});

test("sanitizeTelegramReply clamps long responses", () => {
  const text = "A".repeat(4000);
  const sanitized = sanitizeTelegramReply(text, { TELEGRAM_AI_MAX_REPLY_CHARS: "200" });
  assert.ok(sanitized.length <= 220);
  assert.match(sanitized, /\[odpowiedź skrócona\]/);
});

test("moderateIssueCandidate returns structured decision from Google provider", async () => {
  const env = {
    TELEGRAM_AI_ENABLED: "true",
    TELEGRAM_AI_PRIMARY_PROVIDER: "google",
    TELEGRAM_AI_FALLBACK_PROVIDER: "nvidia",
    TELEGRAM_AI_GOOGLE_MODEL: "gemma-3-27b-it",
    GEMINI_API_KEY: "test-key",
  };

  const result = await moderateIssueCandidate(
    env,
    {
      kind: "idea",
      label: "pomysł",
      content: "Zróbmy prosty dashboard dla porównań przypadków.",
    },
    {
      chat_id: "123",
      user_id: "456",
      message_id: "9",
      text: "Pomysl: Zróbmy prosty dashboard dla porównań przypadków.",
    },
    [],
    {
      fetchImpl: async () =>
        jsonResponse({
          candidates: [
            {
              content: {
                parts: [
                  {
                    text: '{"decision":"accept","reason_code":"ok","reason_text":"Treść jest konkretna i merytoryczna."}',
                  },
                ],
              },
            },
          ],
        }),
    }
  );

  assert.equal(result.decision, "accept");
  assert.equal(result.reason_code, "ok");
});

test("callProviderWithFallback switches from Google to NVIDIA on 429", async () => {
  const env = {
    TELEGRAM_AI_PRIMARY_PROVIDER: "google",
    TELEGRAM_AI_FALLBACK_PROVIDER: "nvidia",
    TELEGRAM_AI_GOOGLE_MODEL: "gemma-3-27b-it",
    TELEGRAM_AI_NVIDIA_MODEL: "google/gemma-4-31b-it",
    GEMINI_API_KEY: "google-key",
    NVIDIA_API_KEY: "nvidia-key",
  };

  const calls = [];
  const response = await callProviderWithFallback(
    env,
    {
      systemInstruction: "system",
      userPrompt: "user",
      maxTokens: 100,
      temperature: 0.2,
      responseMimeType: "application/json",
    },
    {
      fetchImpl: async (url) => {
        calls.push(url);
        if (url.includes("generativelanguage.googleapis.com")) {
          return jsonResponse(
            {
              error: {
                message: "rate limited",
              },
            },
            429
          );
        }
        return jsonResponse({
          choices: [
            {
              message: {
                content: '{"decision":"accept"}',
              },
            },
          ],
        });
      },
    }
  );

  assert.equal(response.provider_name, "nvidia");
  assert.equal(calls.length, 2);
  assert.ok(calls[0].includes("generativelanguage.googleapis.com"));
  assert.ok(calls[1].includes("integrate.api.nvidia.com"));
});

test("callProviderWithFallback retries Google without developer instruction when model rejects it", async () => {
  const env = {
    TELEGRAM_AI_PRIMARY_PROVIDER: "google",
    TELEGRAM_AI_FALLBACK_PROVIDER: "nvidia",
    TELEGRAM_AI_GOOGLE_MODEL: "gemma-3-27b-it",
    GEMINI_API_KEY: "google-key",
  };

  const requestBodies = [];
  const response = await callProviderWithFallback(
    env,
    {
      systemInstruction: "system guidance",
      userPrompt: "user question",
      maxTokens: 100,
      temperature: 0.2,
      responseMimeType: "application/json",
    },
    {
      fetchImpl: async (_url, init = {}) => {
        requestBodies.push(JSON.parse(init.body));
        if (requestBodies.length === 1) {
          return jsonResponse(
            {
              error: {
                message: "Developer instruction is not enabled for models/gemma-3-27b-it",
              },
            },
            400
          );
        }

        return jsonResponse({
          candidates: [
            {
              content: {
                parts: [
                  {
                    text: '{"decision":"accept"}',
                  },
                ],
              },
            },
          ],
        });
      },
    }
  );

  assert.equal(response.provider_name, "google");
  assert.equal(requestBodies.length, 2);
  assert.ok(requestBodies[0].systemInstruction);
  assert.equal(requestBodies[1].systemInstruction, undefined);
  assert.match(requestBodies[1].contents[0].parts[0].text, /system guidance/);
  assert.match(requestBodies[1].contents[0].parts[0].text, /user question/);
});

test("callProviderWithFallback falls back to NVIDIA when Google still rejects developer instruction mode", async () => {
  const env = {
    TELEGRAM_AI_PRIMARY_PROVIDER: "google",
    TELEGRAM_AI_FALLBACK_PROVIDER: "nvidia",
    TELEGRAM_AI_GOOGLE_MODEL: "gemma-3-27b-it",
    TELEGRAM_AI_NVIDIA_MODEL: "google/gemma-4-31b-it",
    GEMINI_API_KEY: "google-key",
    NVIDIA_API_KEY: "nvidia-key",
  };

  const calls = [];
  const response = await callProviderWithFallback(
    env,
    {
      systemInstruction: "system guidance",
      userPrompt: "user question",
      maxTokens: 100,
      temperature: 0.2,
      responseMimeType: "application/json",
    },
    {
      fetchImpl: async (url, init = {}) => {
        calls.push({
          url,
          body: init.body ? JSON.parse(init.body) : null,
        });
        if (url.includes("generativelanguage.googleapis.com")) {
          return jsonResponse(
            {
              error: {
                message: "Developer instruction is not enabled for models/gemma-3-27b-it",
              },
            },
            400
          );
        }

        return jsonResponse({
          choices: [
            {
              message: {
                content: '{"decision":"accept","reason_code":"ok","reason_text":"Przyjęte przez fallback."}',
              },
            },
          ],
        });
      },
    }
  );

  assert.equal(response.provider_name, "nvidia");
  assert.equal(calls.length, 3);
  assert.ok(calls[0].url.includes("generativelanguage.googleapis.com"));
  assert.ok(calls[1].url.includes("generativelanguage.googleapis.com"));
  assert.ok(calls[2].url.includes("integrate.api.nvidia.com"));
});

test("handleTelegramWebhook routes onboarding without creating GitHub issue", async () => {
  const env = {
    DB: null,
    TELEGRAM_AI_ENABLED: "true",
    TELEGRAM_ISSUES_ENABLED: "true",
    TELEGRAM_ALLOWED_CHAT_IDS: "*",
    TELEGRAM_BOT_TOKEN: "telegram-token",
    GEMINI_API_KEY: "google-key",
    TELEGRAM_AI_PRIMARY_PROVIDER: "google",
    TELEGRAM_AI_FALLBACK_PROVIDER: "nvidia",
  };
  const calls = [];

  await withMockedFetch(async (url, init = {}) => {
    calls.push(url);
    if (url.includes("api.telegram.org")) {
      return jsonResponse({ ok: true });
    }
    if (url.includes("generativelanguage.googleapis.com")) {
      return jsonResponse({
        candidates: [
          {
            content: {
              parts: [
                {
                  text: "Rekomendowana ścieżka: API, adaptery i integracja danych.\nPierwszy materiał: https://github.com/StrazPrzyszlosci/STRAZ_PRZYSZLOSCI/blob/main/docs/PRZYKLADY_GOTOWEGO_KODU.md\nPierwsze zadania: issue:aq-09, issue:aq-13",
                },
              ],
            },
          },
        ],
      });
    }
    throw new Error(`Unexpected URL: ${url}`);
  }, async () => {
    const request = new Request("https://example.workers.dev/integrations/telegram/webhook", {
      method: "POST",
      headers: {
        "content-type": "application/json",
      },
      body: JSON.stringify({
        update_id: 1,
        message: {
          message_id: 2,
          from: { id: 3, username: "tester" },
          chat: { id: 4, type: "private" },
          text: "Gdzie mogę pomóc, jeśli znam backend i API?",
        },
      }),
    });
    const response = await handleTelegramWebhook(request, env);
    const payload = await response.json();

    assert.equal(payload.results[0].status, "onboarding_replied");
    assert.equal(calls.some((url) => String(url).includes("/repos/")), false);
  });
});

test("handleTelegramWebhook creates issue after accepted moderation", async () => {
  const env = {
    DB: null,
    TELEGRAM_AI_ENABLED: "true",
    TELEGRAM_ISSUES_ENABLED: "true",
    TELEGRAM_ISSUES_DRY_RUN: "false",
    TELEGRAM_ALLOWED_CHAT_IDS: "*",
    TELEGRAM_BOT_TOKEN: "telegram-token",
    GEMINI_API_KEY: "google-key",
    GITHUB_TOKEN: "github-token",
    GITHUB_REPO_OWNER: "StrazPrzyszlosci",
    GITHUB_REPO_NAME: "STRAZ_PRZYSZLOSCI",
  };
  const calls = [];
  let googleCall = 0;

  await withMockedFetch(async (url, init = {}) => {
    calls.push(url);
    if (url.includes("api.telegram.org")) {
      return jsonResponse({ ok: true });
    }
    if (url.includes("generativelanguage.googleapis.com")) {
      googleCall += 1;
      if (googleCall === 1) {
        return jsonResponse({
          candidates: [
            {
              content: {
                parts: [
                  {
                    text: '{"decision":"accept","reason_code":"ok","reason_text":"Merytoryczne zgłoszenie."}',
                  },
                ],
              },
            },
          ],
        });
      }
      return jsonResponse({
        candidates: [
          {
            content: {
              parts: [
                {
                  text: '{"edited_description":"Uporządkowany opis pomysłu.","additional_context":"Może być powiązane z dokumentacją adapterów."}',
                },
              ],
            },
          },
        ],
      });
    }
    if (url.includes("api.github.com/repos/StrazPrzyszlosci/STRAZ_PRZYSZLOSCI/issues")) {
      const draft = JSON.parse(init.body);
      assert.equal(draft.title, "Zróbmy prosty dashboard porównujący przypadki.");
      assert.match(draft.body, /## Oryginalna wiadomość/);
      assert.match(draft.body, /## Zredagowany opis/);
      return jsonResponse({
        number: 321,
        html_url: "https://github.com/StrazPrzyszlosci/STRAZ_PRZYSZLOSCI/issues/321",
      });
    }
    throw new Error(`Unexpected URL: ${url}`);
  }, async () => {
    const request = new Request("https://example.workers.dev/integrations/telegram/webhook", {
      method: "POST",
      headers: {
        "content-type": "application/json",
      },
      body: JSON.stringify({
        update_id: 1,
        message: {
          message_id: 2,
          from: { id: 3, username: "tester" },
          chat: { id: 4, type: "private" },
          text: "Pomysl: Zróbmy prosty dashboard porównujący przypadki.",
        },
      }),
    });
    const response = await handleTelegramWebhook(request, env);
    const payload = await response.json();

    assert.equal(payload.results[0].status, "created");
    assert.equal(calls.some((url) => String(url).includes("api.github.com/repos/StrazPrzyszlosci/STRAZ_PRZYSZLOSCI/issues")), true);
  });
});

test("handleTelegramWebhook rejects off-topic issue without GitHub call", async () => {
  const env = {
    DB: null,
    TELEGRAM_AI_ENABLED: "true",
    TELEGRAM_ISSUES_ENABLED: "true",
    TELEGRAM_ISSUES_DRY_RUN: "false",
    TELEGRAM_ALLOWED_CHAT_IDS: "*",
    TELEGRAM_BOT_TOKEN: "telegram-token",
    GEMINI_API_KEY: "google-key",
  };
  const calls = [];

  await withMockedFetch(async (url) => {
    calls.push(url);
    if (url.includes("api.telegram.org")) {
      return jsonResponse({ ok: true });
    }
    if (url.includes("generativelanguage.googleapis.com")) {
      return jsonResponse({
        candidates: [
          {
            content: {
              parts: [
                {
                  text: '{"decision":"reject_off_topic","reason_code":"off_topic","reason_text":"Treść nie dotyczy inicjatywy ani repozytorium."}',
                },
              ],
            },
          },
        ],
      });
    }
    throw new Error(`Unexpected URL: ${url}`);
  }, async () => {
    const request = new Request("https://example.workers.dev/integrations/telegram/webhook", {
      method: "POST",
      headers: {
        "content-type": "application/json",
      },
      body: JSON.stringify({
        update_id: 1,
        message: {
          message_id: 2,
          from: { id: 3, username: "tester" },
          chat: { id: 4, type: "private" },
          text: "Pomysl: sprzedam używany rower.",
        },
      }),
    });
    const response = await handleTelegramWebhook(request, env);
    const payload = await response.json();

    assert.equal(payload.results[0].status, "reject_off_topic");
    assert.equal(calls.some((url) => String(url).includes("api.github.com/repos/")), false);
  });
});
