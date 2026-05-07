import { describe, it } from "node:test";
import assert from "node:assert/strict";
import nodeCrypto from "node:crypto";

// ── Replikacje funkcji z discord_api_handler.js do testów ──

function jsonReply(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "content-type": "application/json; charset=utf-8" },
  });
}

async function verifyDiscordSignature(request, rawBody, env) {
  const publicKey = (env.DISCORD_PUBLIC_KEY || "").trim();
  if (!publicKey) {
    return null;
  }

  const signature = request.headers.get("X-Signature-Ed25519");
  const timestamp = request.headers.get("X-Signature-Timestamp");
  if (!signature || !timestamp) {
    return "Missing Ed25519 signature headers";
  }

  try {
    const encoder = new TextEncoder();
    const keyData = Uint8Array.from(
      typeof atob === "function"
        ? atob(publicKey)
        : Buffer.from(publicKey, "base64").toString("binary"),
      (c) => c.charCodeAt(0)
    );
    const sigData = Uint8Array.from(
      typeof atob === "function"
        ? atob(signature)
        : Buffer.from(signature, "base64").toString("binary"),
      (c) => c.charCodeAt(0)
    );

    const key = await crypto.subtle.importKey(
      "raw", keyData, { name: "NODE-ED25519", namedCurve: "NODE-ED25519" },
      false, ["verify"]
    );

    const isValid = await crypto.subtle.verify(
      "NODE-ED25519", key, sigData,
      encoder.encode(timestamp + rawBody)
    );

    return isValid ? null : "Ed25519 signature verification failed";
  } catch (_e) {
    return "Ed25519 verification error: " + (_e.message || "internal error");
  }
}

// Node.js-compatible Ed25519 verification using node:crypto (not Web Crypto)
function verifyEd25519Node(publicKeyDer, timestamp, rawBody, signatureDer) {
  try {
    const publicKeyObj = nodeCrypto.createPublicKey({
      key: Buffer.from(publicKeyDer, "hex"),
      format: "der",
      type: "spki",
    });
    return nodeCrypto.verify(
      null,
      Buffer.from(timestamp + rawBody),
      publicKeyObj,
      Buffer.from(signatureDer, "hex")
    );
  } catch (_e) {
    return false;
  }
}

// Node.js-compatible Ed25519 signing
function signEd25519Node(privateKeyDer, timestamp, rawBody) {
  const privateKeyObj = nodeCrypto.createPrivateKey({
    key: Buffer.from(privateKeyDer, "hex"),
    format: "der",
    type: "pkcs8",
  });
  return nodeCrypto.sign(
    null,
    Buffer.from(timestamp + rawBody),
    privateKeyObj
  );
}

// Replika parseDiscordBody
function parseDiscordBody(body) {
  const text = body.text || body.content || "";
  const stripped = text.trim();

  let command = null;
  let classification = null;

  if (stripped.startsWith("!")) {
    const spaceIdx = stripped.indexOf(" ");
    command = spaceIdx > 1 ? stripped.slice(1, spaceIdx) : stripped.slice(1);
  }

  const lower = stripped.toLowerCase();
  if (!command && (lower.startsWith("pomysl:") || lower.startsWith("pomysł:"))) {
    classification = { kind: "idea", label: "Pomysł", content: stripped };
  } else if (!command && (lower.startsWith("uwaga:") || lower.startsWith("problem:") || lower.startsWith("błąd:") || lower.startsWith("blad:"))) {
    classification = { kind: "feedback", label: "Uwaga", content: stripped };
  }

  return {
    chat_id: body.chat_id || "",
    user_id: body.user_id || "",
    message_id: body.message_id || "",
    text: stripped,
    command,
    classification,
    attachments: body.attachments || [],
    username: body.username || "",
    callback_data: body.callback_data || null,
    type: body.type || "message",
  };
}

// Replika validacji handleDiscordWebhook (bez wywolan do handlerow)
function validateDiscordPayload(body) {
  if (!body.chat_id && !body.user_id && !body.callback_data) {
    return { valid: false, error: "Missing required fields: chat_id, user_id, or callback_data", status: 400 };
  }
  if (typeof body.text === "string" && body.text.length > 4000) {
    return { valid: false, error: "Text too long (max 4000 chars)", status: 400 };
  }
  return { valid: true };
}

// ── Testy ──

describe("verifyDiscordSignature — logika autoryzacji", () => {
  it("brak DISCORD_PUBLIC_KEY → null (skip verification)", async () => {
    const request = new Request("https://example.com/webhook", {
      method: "POST",
      headers: {
        "X-Signature-Ed25519": "dGVzdA==",
        "X-Signature-Timestamp": "1234567890",
      },
      body: "{}",
    });

    const env = {};
    const result = await verifyDiscordSignature(request, "{}", env);
    assert.equal(result, null);
  });

  it("pusty DISCORD_PUBLIC_KEY → null (skip verification)", async () => {
    const request = new Request("https://example.com/webhook", {
      method: "POST",
      headers: {
        "X-Signature-Ed25519": "dGVzdA==",
        "X-Signature-Timestamp": "1234567890",
      },
      body: "{}",
    });

    const env = { DISCORD_PUBLIC_KEY: "" };
    const result = await verifyDiscordSignature(request, "{}", env);
    assert.equal(result, null);
  });

  it("brak X-Signature-Ed25519 → error", async () => {
    const request = new Request("https://example.com/webhook", {
      method: "POST",
      headers: { "X-Signature-Timestamp": "1234567890" },
      body: "{}",
    });

    const env = { DISCORD_PUBLIC_KEY: "dGVzdA==" };
    const result = await verifyDiscordSignature(request, "{}", env);
    assert.equal(result, "Missing Ed25519 signature headers");
  });

  it("brak X-Signature-Timestamp → error", async () => {
    const request = new Request("https://example.com/webhook", {
      method: "POST",
      headers: { "X-Signature-Ed25519": "dGVzdA==" },
      body: "{}",
    });

    const env = { DISCORD_PUBLIC_KEY: "dGVzdA==" };
    const result = await verifyDiscordSignature(request, "{}", env);
    assert.equal(result, "Missing Ed25519 signature headers");
  });

  it("nieprawidlowy public key (nie-base64) → error", async () => {
    const request = new Request("https://example.com/webhook", {
      method: "POST",
      headers: {
        "X-Signature-Ed25519": "dGVzdA==",
        "X-Signature-Timestamp": "1234567890",
      },
      body: "{}",
    });

    const env = { DISCORD_PUBLIC_KEY: "not-valid-base64!!!" };
    const result = await verifyDiscordSignature(request, "{}", env);
    assert.ok(typeof result === "string");
    assert.ok(result.startsWith("Ed25519 verification error:"));
  });

  it("nieprawidlowa sygnatura (nie-base64) → error", async () => {
    const request = new Request("https://example.com/webhook", {
      method: "POST",
      headers: {
        "X-Signature-Ed25519": "invalid-base64!!!",
        "X-Signature-Timestamp": "1234567890",
      },
      body: "{}",
    });

    const env = { DISCORD_PUBLIC_KEY: "dGVzdA==" };
    const result = await verifyDiscordSignature(request, "{}", env);
    assert.ok(typeof result === "string");
    assert.ok(result.startsWith("Ed25519 verification error:"));
  });

  it("pusta sygnatura → error", async () => {
    const request = new Request("https://example.com/webhook", {
      method: "POST",
      headers: {
        "X-Signature-Ed25519": "",
        "X-Signature-Timestamp": "1234567890",
      },
      body: "{}",
    });

    const env = { DISCORD_PUBLIC_KEY: "dGVzdA==" };
    const result = await verifyDiscordSignature(request, "{}", env);
    assert.ok(typeof result === "string");
  });
});

describe("verifyEd25519 — Node.js crypto (realna weryfikacja)", () => {
  it("poprawnie podpisany payload → true", () => {
    const timestamp = "1622471124";
    const rawBody = '{"type":1,"data":{}}';

    const keyPair = nodeCrypto.generateKeyPairSync("ed25519");
    const pubHex = keyPair.publicKey.export({ type: "spki", format: "der" }).toString("hex");
    const privHex = keyPair.privateKey.export({ type: "pkcs8", format: "der" }).toString("hex");

    const sigHex = signEd25519Node(privHex, timestamp, rawBody).toString("hex");

    const result = verifyEd25519Node(pubHex, timestamp, rawBody, sigHex);
    assert.equal(result, true);
  });

  it("nieprawidlowo podpisany payload (inny klucz prywatny) → false", () => {
    const keyPair1 = nodeCrypto.generateKeyPairSync("ed25519");
    const pubHex = keyPair1.publicKey.export({ type: "spki", format: "der" }).toString("hex");

    const keyPair2 = nodeCrypto.generateKeyPairSync("ed25519");
    const wrongPrivHex = keyPair2.privateKey.export({ type: "pkcs8", format: "der" }).toString("hex");

    const sigHex = signEd25519Node(wrongPrivHex, "1622471124", "{}").toString("hex");

    const result = verifyEd25519Node(pubHex, "1622471124", "{}", sigHex);
    assert.equal(result, false);
  });

  it("zmodyfikowany payload → false", () => {
    const keyPair = nodeCrypto.generateKeyPairSync("ed25519");
    const pubHex = keyPair.publicKey.export({ type: "spki", format: "der" }).toString("hex");
    const privHex = keyPair.privateKey.export({ type: "pkcs8", format: "der" }).toString("hex");

    const sigHex = signEd25519Node(privHex, "1622471124", '{"original":"body"}').toString("hex");

    const result = verifyEd25519Node(pubHex, "1622471124", '{"modified":"body"}', sigHex);
    assert.equal(result, false);
  });

  it("zmodyfikowany timestamp → false", () => {
    const keyPair = nodeCrypto.generateKeyPairSync("ed25519");
    const pubHex = keyPair.publicKey.export({ type: "spki", format: "der" }).toString("hex");
    const privHex = keyPair.privateKey.export({ type: "pkcs8", format: "der" }).toString("hex");
    const rawBody = '{"test":"value"}';

    const sigHex = signEd25519Node(privHex, "1622471124", rawBody).toString("hex");

    const result = verifyEd25519Node(pubHex, "9999999999", rawBody, sigHex);
    assert.equal(result, false);
  });
});

describe("parseDiscordBody — parsowanie webhook payload", () => {
  it("pusta wiadomosc", () => {
    const result = parseDiscordBody({});
    assert.equal(result.chat_id, "");
    assert.equal(result.user_id, "");
    assert.equal(result.text, "");
    assert.equal(result.type, "message");
  });

  it("komenda !help", () => {
    const result = parseDiscordBody({
      chat_id: "channel-1",
      user_id: "user-1",
      text: "!help",
    });
    assert.equal(result.command, "help");
  });

  it("komenda !scan ESP32", () => {
    const result = parseDiscordBody({
      text: "!scan ESP32",
      chat_id: "c1",
    });
    assert.equal(result.command, "scan");
  });

  it("pomysl: with text", () => {
    const result = parseDiscordBody({
      text: "Pomysl: dodac OCR",
    });
    assert.equal(result.classification.kind, "idea");
    assert.equal(result.classification.label, "Pomysł");
  });

  it("uwaga: with text", () => {
    const result = parseDiscordBody({
      text: "Uwaga: strona wolno dziala",
    });
    assert.equal(result.classification.kind, "feedback");
    assert.equal(result.classification.label, "Uwaga");
  });

  it("normalna wiadomosc bez prefixu", () => {
    const result = parseDiscordBody({
      text: "Cześć, jak działa ESP32?",
      chat_id: "c2",
      user_id: "u2",
    });
    assert.equal(result.command, null);
    assert.equal(result.classification, null);
    assert.equal(result.text, "Cześć, jak działa ESP32?");
  });

  it("callback type", () => {
    const result = parseDiscordBody({
      type: "callback",
      callback_data: "menu_scan",
      chat_id: "c3",
    });
    assert.equal(result.type, "callback");
    assert.equal(result.callback_data, "menu_scan");
  });

  it("attachments preserved", () => {
    const result = parseDiscordBody({
      chat_id: "c4",
      attachments: [{ name: "test.pdf", contentType: "application/pdf" }],
    });
    assert.equal(result.attachments.length, 1);
    assert.equal(result.attachments[0].name, "test.pdf");
  });
});

describe("validateDiscordPayload — walidacja wejsciowa", () => {
  it("poprawny payload z chat_id", () => {
    const result = validateDiscordPayload({ chat_id: "c1", user_id: "u1" });
    assert.equal(result.valid, true);
  });

  it("poprawny payload z callback_data", () => {
    const result = validateDiscordPayload({ callback_data: "menu_scan" });
    assert.equal(result.valid, true);
  });

  it("pusty payload → odrzucony", () => {
    const result = validateDiscordPayload({});
    assert.equal(result.valid, false);
    assert.ok(result.error.includes("Missing required fields"));
  });

  it("payload z samym username → odrzucony", () => {
    const result = validateDiscordPayload({ username: "test" });
    assert.equal(result.valid, false);
  });

  it("tekst > 4000 znakow → odrzucony", () => {
    const result = validateDiscordPayload({
      chat_id: "c1",
      user_id: "u1",
      text: "x".repeat(4001),
    });
    assert.equal(result.valid, false);
    assert.ok(result.error.includes("too long"));
  });

  it("tekst dokladnie 4000 znakow → poprawny", () => {
    const result = validateDiscordPayload({
      chat_id: "c1",
      user_id: "u1",
      text: "y".repeat(4000),
    });
    assert.equal(result.valid, true);
  });

  it("tekst 1 znak → poprawny", () => {
    const result = validateDiscordPayload({
      chat_id: "c1",
      text: "a",
    });
    assert.equal(result.valid, true);
  });
});

describe("jsonReply — struktura odpowiedzi", () => {
  it("poprawny status 200 i content-type", async () => {
    const resp = jsonReply({ ok: true });
    assert.equal(resp.status, 200);
    assert.equal(resp.headers.get("content-type"), "application/json; charset=utf-8");
    const body = await resp.json();
    assert.deepEqual(body, { ok: true });
  });

  it("status 401 dla bledu", async () => {
    const resp = jsonReply({ error: "Unauthorized" }, 401);
    assert.equal(resp.status, 401);
    const body = await resp.json();
    assert.deepEqual(body, { error: "Unauthorized" });
  });

  it("status 503 dla braku konfiguracji", async () => {
    const resp = jsonReply({ error: "Discord integration not configured on server." }, 503);
    assert.equal(resp.status, 503);
  });
});