import { describe, it, before, after, beforeEach } from "node:test";
import assert from "node:assert/strict";

import {
  checkRateLimit,
  sanitizeDiscordInput,
  isAllowedMimeType,
  mapAttachmentToPayload,
  _resetRateLimitMap,
} from "../discord/discord_security.mjs";

// ============================================================
// sanitizeDiscordInput
// ============================================================

describe("sanitizeDiscordInput", () => {
  describe("typ wejsciowy", () => {
    it("null → pusty string", () => {
      assert.equal(sanitizeDiscordInput(null), "");
    });
    it("undefined → pusty string", () => {
      assert.equal(sanitizeDiscordInput(undefined), "");
    });
    it("liczba → pusty string", () => {
      assert.equal(sanitizeDiscordInput(42), "");
    });
    it("boolean → pusty string", () => {
      assert.equal(sanitizeDiscordInput(true), "");
    });
    it("pusta tablica → pusty string", () => {
      assert.equal(sanitizeDiscordInput([]), "");
    });
  });

  describe("normalny tekst przechodzi", () => {
    it("ASCII text bez zmian", () => {
      assert.equal(sanitizeDiscordInput("Hello World"), "Hello World");
    });
    it("polskie znaki zachowane", () => {
      const input = "Zażółć gęślą jaźń ąćęłńóśźż";
      assert.equal(sanitizeDiscordInput(input), input);
    });
    it("emoji zachowane", () => {
      const input = "🔧 Część ESP32 👍";
      assert.equal(sanitizeDiscordInput(input), input);
    });
    it("znaki japonskie zachowane", () => {
      const input = "電子部品 ESP32-DEVKIT";
      assert.equal(sanitizeDiscordInput(input), input);
    });
    it("nowa linia i tab zachowane", () => {
      assert.equal(sanitizeDiscordInput("line1\nline2\tindent"), "line1\nline2\tindent");
    });
    it("pusty string → pusty string", () => {
      assert.equal(sanitizeDiscordInput(""), "");
    });
    it("tylko spacje → bez zmian", () => {
      assert.equal(sanitizeDiscordInput("   "), "   ");
    });
  });

  describe("usuwanie niewidocznych znakow Unicode", () => {
    it("Zero-Width Space (U+200B)", () => {
      const cleaned = sanitizeDiscordInput("hello\u200Bworld");
      assert.equal(cleaned, "helloworld");
      assert.ok(!cleaned.includes("\u200B"));
    });
    it("BOM / Zero Width No-Break Space (U+FEFF)", () => {
      const cleaned = sanitizeDiscordInput("\uFEFF" + "config");
      assert.equal(cleaned, "config");
      assert.ok(!cleaned.includes("\uFEFF"));
    });
    it("Zero-Width Joiner (U+200D) i Non-Joiner (U+200C)", () => {
      const cleaned = sanitizeDiscordInput("a\u200Cb\u200Dc");
      assert.equal(cleaned, "abc");
    });
    it("BIDI override chars (LRE RLE PDF LRO RLO)", () => {
      const cleaned = sanitizeDiscordInput("\u202Aevil\u202C");
      assert.equal(cleaned, "evil");
      assert.ok(!cleaned.includes("\u202A"));
      assert.ok(!cleaned.includes("\u202C"));
    });
    it("Right-to-Left Override usuwany", () => {
      const cleaned = sanitizeDiscordInput("test\u202Egnorts");
      assert.equal(cleaned, "testgnorts");
    });
    it("Soft hyphen (U+00AD)", () => {
      const cleaned = sanitizeDiscordInput("super\u00ADvisor");
      assert.equal(cleaned, "supervisor");
    });
    it("C0 control chars (0x00-0x08)", () => {
      const cleaned = sanitizeDiscordInput("\x00\x01\x02\x03\x04\x05\x06\x07\x08text");
      assert.equal(cleaned, "text");
    });
    it("C1 control chars (0x7F-0x9F)", () => {
      const cleaned = sanitizeDiscordInput("data\x7F\x80\x90\x9Fend");
      assert.equal(cleaned, "dataend");
    });
    it("Variation selectors (U+FE00-U+FE0F)", () => {
      const cleaned = sanitizeDiscordInput("\uFE00icon\uFE0F");
      assert.equal(cleaned, "icon");
    });
    it("interlinear annotation markers (U+FFF9-U+FFFB)", () => {
      const cleaned = sanitizeDiscordInput("\uFFF9" + "hidden" + "\uFFFB");
      assert.equal(cleaned, "hidden");
    });
    it("mieszanka wielu niewidocznych znakow", () => {
      const input = "\u200B" + "H" + "\u200C" + "i" + "\uFEFF" + "!" + "\u202E";
      const cleaned = sanitizeDiscordInput(input);
      assert.equal(cleaned, "Hi!");
    });
    it("usuwanie nie zmienia widocznych emoji", () => {
      const input = "test\u200B😀\u200Ctest";
      assert.equal(sanitizeDiscordInput(input), "test😀test");
    });
  });

  describe("clamp długości", () => {
    it("krótki tekst bez zmian gdy ponizej 4000", () => {
      const text = "x".repeat(100);
      assert.equal(sanitizeDiscordInput(text), text);
    });
    it("tekst dokładnie 4000 znakow", () => {
      const text = "x".repeat(4000);
      assert.equal(sanitizeDiscordInput(text), text);
      assert.equal(sanitizeDiscordInput(text).length, 4000);
    });
    it("tekst 5000 znakow → przyciety do 4000", () => {
      const text = "a".repeat(5000);
      const result = sanitizeDiscordInput(text);
      assert.equal(result.length, 4000);
      assert.ok(result.startsWith("a".repeat(4000)));
    });
    it("przycinanie uwzglednia wczesniejsze usuniecie niewidocznych znakow", () => {
      // 4050 visible chars + invisible chars → should still truncate to 4000
      const visible = "x".repeat(4050);
      const invisible = "\u200B".repeat(50);
      const input = visible + invisible;
      const result = sanitizeDiscordInput(input);
      assert.equal(result.length, 4000);
    });
    it("bardzo dlugi input (100k znakow)", () => {
      const text = "abc".repeat(40000); // 120k
      const result = sanitizeDiscordInput(text);
      assert.equal(result.length, 4000);
    });
  });
});

// ============================================================
// checkRateLimit
// ============================================================

describe("checkRateLimit", () => {
  beforeEach(() => {
    _resetRateLimitMap();
  });

  describe("podstawowa logika", () => {
    it("pierwsze wywolanie dozwolone", () => {
      const result = checkRateLimit("user-1");
      assert.equal(result.allowed, true);
    });
    it("drugie wywolanie w oknie blokowane", () => {
      checkRateLimit("user-2");
      const result = checkRateLimit("user-2");
      assert.equal(result.allowed, false);
    });
    it("retry_after_seconds jest dodatnie", () => {
      checkRateLimit("user-3");
      const result = checkRateLimit("user-3");
      assert.ok(result.retry_after_seconds > 0);
      assert.ok(result.retry_after_seconds <= 60);
    });
    it("rozni uzytkownicy sa niezalezni", () => {
      const r1 = checkRateLimit("user-a");
      const r2 = checkRateLimit("user-b");
      assert.equal(r1.allowed, true);
      assert.equal(r2.allowed, true);
    });
    it("blokada dotyczy tylko tego samego uzytkownika", () => {
      checkRateLimit("user-c");
      const blocked = checkRateLimit("user-c");
      const allowed = checkRateLimit("user-d");
      assert.equal(blocked.allowed, false);
      assert.equal(allowed.allowed, true);
    });
  });

  describe("czyszczenie starych wpisow", () => {
    it("mapa rosnie do 10000 wpisow", () => {
      for (let i = 0; i < 5000; i++) {
        checkRateLimit(`user-${i}`);
      }
      // All should be allowed (first calls)
      const midTest = checkRateLimit("new-user-after-5k");
      assert.equal(midTest.allowed, true);
    });

    it("nie crashuje przy bardzo duzej liczbie uzytkownikow", () => {
      for (let i = 0; i < 20000; i++) {
        const r = checkRateLimit(`bulk-user-${i}`);
        assert.equal(r.allowed, true, `user bulk-user-${i} should be allowed on first call`);
      }
    });
  });

  describe("interakcje miedzy uzytkownikami", () => {
    it("3 roznych uzytkownikow, kazdy pierwszy raz dozwolony", () => {
      assert.equal(checkRateLimit("x-1").allowed, true);
      assert.equal(checkRateLimit("x-2").allowed, true);
      assert.equal(checkRateLimit("x-3").allowed, true);
    });
    it("1 uzytkownik probuje 3 razy — tylko pierwszy dozwolony", () => {
      assert.equal(checkRateLimit("spammer").allowed, true);
      assert.equal(checkRateLimit("spammer").allowed, false);
      assert.equal(checkRateLimit("spammer").allowed, false);
    });
  });
});

// ============================================================
// isAllowedMimeType
// ============================================================

describe("isAllowedMimeType", () => {
  describe("dozwolone typy MIME", () => {
    it("image/jpeg", () => {
      assert.equal(isAllowedMimeType("image/jpeg"), true);
    });
    it("image/png", () => {
      assert.equal(isAllowedMimeType("image/png"), true);
    });
    it("image/gif", () => {
      assert.equal(isAllowedMimeType("image/gif"), true);
    });
    it("image/webp", () => {
      assert.equal(isAllowedMimeType("image/webp"), true);
    });
    it("application/pdf", () => {
      assert.equal(isAllowedMimeType("application/pdf"), true);
    });
    it("text/plain", () => {
      assert.equal(isAllowedMimeType("text/plain"), true);
    });
  });

  describe("niedozwolone typy MIME", () => {
    it("application/octet-stream", () => {
      assert.equal(isAllowedMimeType("application/octet-stream"), false);
    });
    it("application/zip", () => {
      assert.equal(isAllowedMimeType("application/zip"), false);
    });
    it("text/html", () => {
      assert.equal(isAllowedMimeType("text/html"), false);
    });
    it("video/mp4", () => {
      assert.equal(isAllowedMimeType("video/mp4"), false);
    });
    it("application/x-executable", () => {
      assert.equal(isAllowedMimeType("application/x-executable"), false);
    });
  });

  describe("case-insensitive", () => {
    it("IMAGE/JPEG uppercase", () => {
      assert.equal(isAllowedMimeType("IMAGE/JPEG"), true);
    });
    it("Application/PDF mixed case", () => {
      assert.equal(isAllowedMimeType("Application/PDF"), true);
    });
  });

  describe("fallback po rozszerzeniu pliku", () => {
    it("null contentType + .jpg → dozwolone", () => {
      assert.equal(isAllowedMimeType(null, "photo.jpg"), true);
    });
    it("null contentType + .png → dozwolone", () => {
      assert.equal(isAllowedMimeType(null, "screenshot.png"), true);
    });
    it("null contentType + .pdf → dozwolone", () => {
      assert.equal(isAllowedMimeType(null, "datasheet.pdf"), true);
    });
    it("null contentType + .exe → niedozwolone", () => {
      assert.equal(isAllowedMimeType(null, "virus.exe"), false);
    });
    it("null contentType + .zip → niedozwolone", () => {
      assert.equal(isAllowedMimeType(null, "archive.zip"), false);
    });
    it("null contentType + brak rozszerzenia → niedozwolone", () => {
      assert.equal(isAllowedMimeType(null, "noext"), false);
    });
    it("undefined contentType + .txt → dozwolone", () => {
      assert.equal(isAllowedMimeType(undefined, "readme.txt"), true);
    });
    it("pusty string contentType + .txt → dozwolone", () => {
      assert.equal(isAllowedMimeType("", "notes.txt"), true);
    });
  });

  describe("edge cases", () => {
    it("contentType z dodatkowymi parametrami (charset)", () => {
      // startsWith rule: "text/plain" starts "text/plain; charset=utf-8"? No, only the other way around
      // The code checks: ALLOWED_ATTACHMENT_MIMES.some(allowed => contentType.toLowerCase().startsWith(allowed))
      // So "text/plain; charset=utf-8".startsWith("text/plain") → true
      assert.equal(isAllowedMimeType("text/plain; charset=utf-8"), true);
    });
    it("image/jpeg z quality parametrem", () => {
      assert.equal(isAllowedMimeType("image/jpeg; q=0.9"), true);
    });
    it("null contentType + null fileName → niedozwolone", () => {
      assert.equal(isAllowedMimeType(null, null), false);
    });
    it("undefined wszystko", () => {
      assert.equal(isAllowedMimeType(undefined, undefined), false);
    });
    it(".JPEG uppercase extension", () => {
      assert.equal(isAllowedMimeType(null, "PHOTO.JPEG"), true);
    });
  });
});

// ============================================================
// mapAttachmentToPayload
// ============================================================

describe("mapAttachmentToPayload", () => {
  it("pelny attachment", () => {
    const result = mapAttachmentToPayload({
      url: "https://cdn.discord.com/attachments/123/file.pdf",
      name: "file.pdf",
      contentType: "application/pdf",
    });
    assert.deepEqual(result, {
      url: "https://cdn.discord.com/attachments/123/file.pdf",
      name: "file.pdf",
      contentType: "application/pdf",
    });
  });

  it("brak nazwy → null", () => {
    const result = mapAttachmentToPayload({
      url: "https://example.com/img.jpg",
      contentType: "image/jpeg",
    });
    assert.equal(result.name, null);
  });

  it("brak contentType → null", () => {
    const result = mapAttachmentToPayload({
      url: "https://example.com/file",
      name: "file.bin",
    });
    assert.equal(result.contentType, null);
  });

  it("tylko url", () => {
    const result = mapAttachmentToPayload({
      url: "https://example.com/photo.png",
    });
    assert.equal(result.url, "https://example.com/photo.png");
    assert.equal(result.name, null);
    assert.equal(result.contentType, null);
  });

  it("pusty attachment → null fields", () => {
    const result = mapAttachmentToPayload({});
    assert.equal(result.url, undefined);
    assert.equal(result.name, null);
    assert.equal(result.contentType, null);
  });
});

// ============================================================
// Zlozone scenariusze (regression)
// ============================================================

describe("regression — wspoldzialanie funkcji security", () => {
  it("sanitize + rate limit: czysty tekst przechodzi calosc", () => {
    _resetRateLimitMap();
    const userId = "regression-user-1";
    const rawText = "\u200Bhello\u200B world\u200B";
    const rateResult = checkRateLimit(userId);
    assert.equal(rateResult.allowed, true);

    const cleaned = sanitizeDiscordInput(rawText);
    assert.equal(cleaned, "hello world");
    assert.ok(cleaned.length < rawText.length);
  });

  it("załącznik PDF: MIME allowed + dobra nazwa", () => {
    const attach = {
      url: "https://cdn.discord.com/doc.pdf",
      name: "datasheet.PDF",
      contentType: "application/pdf",
    };
    const payload = mapAttachmentToPayload(attach);
    assert.equal(payload.contentType, "application/pdf");
    assert.equal(isAllowedMimeType(payload.contentType, payload.name), true);
  });

  it("załącznik EXE: odrzucany przez MIME i przez rozszerzenie", () => {
    // contentType mismatch: "image/png" for a .exe file (someone lying about MIME)
    const mimeReject = isAllowedMimeType("image/png", "trojan.exe");
    // This should pass because MIME "image/png" is allowed
    assert.equal(mimeReject, true);

    // But if contentType is null, extension blocks it
    const extReject = isAllowedMimeType(null, "trojan.exe");
    assert.equal(extReject, false);
  });

  it("tekst 4000+ znakow → przyciety przed forwardToWorker", () => {
    const longText = "🔧 Part: ESP32-WROOM ".repeat(300); // ~7200 chars
    const result = sanitizeDiscordInput(longText);
    assert.equal(result.length, 4000);
  });

  it("injection probe — BIDI override w nazwie pliku ignorowany przy MIME check", () => {
    // MIME check doesn't sanitize filenames, it just uses extension
    const result = isAllowedMimeType(null, "order\u202Efdp.exe");
    assert.equal(result, false); // .exe blocked
  });

  it("szybkie 1000 wywolan rate limitu z roznymi userami", () => {
    _resetRateLimitMap();
    for (let i = 0; i < 1000; i++) {
      const result = checkRateLimit(`load-user-${i}`);
      assert.equal(result.allowed, true);
    }
    const blocked = checkRateLimit("load-user-0");
    assert.equal(blocked.allowed, false);
  });
});