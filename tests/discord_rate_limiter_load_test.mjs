import { describe, it, beforeEach } from "node:test";
import assert from "node:assert/strict";
import { checkRateLimit, _resetRateLimitMap } from "../discord/discord_security.mjs";

describe("checkRateLimit — load test", () => {
  beforeEach(() => {
    _resetRateLimitMap();
  });

  describe("skalowalnosc", () => {
    it("10k unikalnych uzytkownikow — wszyscy dozwoleni (first call)", () => {
      const COUNT = 10000;
      let allowed = 0;
      let blocked = 0;
      const start = performance.now();

      for (let i = 0; i < COUNT; i++) {
        const result = checkRateLimit(`load-u-${i}`);
        if (result.allowed) allowed++;
        else blocked++;
      }

      const elapsed = performance.now() - start;
      assert.equal(allowed, COUNT);
      assert.equal(blocked, 0);
      assert.ok(elapsed < 5000, `${elapsed.toFixed(0)}ms < 5000ms`);
    });

    it("10k razy ten sam uzytkownik — tylko pierwszy dozwolony", () => {
      for (let i = 0; i < 10000; i++) {
        const result = checkRateLimit("spammer");
        if (i === 0) {
          assert.equal(result.allowed, true);
        } else {
          assert.equal(result.allowed, false);
          assert.ok(result.retry_after_seconds > 0);
        }
      }
    });

    it("15k uzytkownikow — cleanup powyzej 10k", () => {
      for (let i = 0; i < 15000; i++) {
        const result = checkRateLimit(`mass-u-${i}`);
        assert.equal(result.allowed, true);
      }
    });
  });

  describe("mechanizm czyszczenia", () => {
    it("po 10001 wpisach starszy user nadal zablokowany", () => {
      for (let i = 0; i < 10001; i++) {
        checkRateLimit(`cleanup-test-${i}`);
      }
      const oldUser = checkRateLimit("cleanup-test-0");
      assert.equal(oldUser.allowed, false);
    });

    it("nowy user po cleanup dozwolony", () => {
      for (let i = 0; i < 11000; i++) {
        checkRateLimit(`cl-up-${i}`);
      }
      const newUser = checkRateLimit("cl-up-new");
      assert.equal(newUser.allowed, true);
    });
  });

  describe("wydajnosc", () => {
    it("30k wywolan z roznymi userami", () => {
      const COUNT = 30000;
      const start = performance.now();
      for (let i = 0; i < COUNT; i++) {
        checkRateLimit(`perf-u-${i}`);
      }
      const elapsed = performance.now() - start;
      assert.ok(elapsed < 10000, `30k w ${elapsed.toFixed(0)}ms`);
    });

    it("50k wywolan tego samego usera", () => {
      const start = performance.now();
      for (let i = 0; i < 50000; i++) {
        checkRateLimit("perf-spammer");
      }
      const elapsed = performance.now() - start;
      assert.ok(elapsed < 3000, `50k powtorzen w ${elapsed.toFixed(0)}ms`);
    });
  });

  describe("przeplot — mieszanka userow", () => {
    it("przeplot A B A C B D A E A — poprawna kolejka", () => {
      const users = ["A", "B", "A", "C", "B", "D", "A", "E", "A"];
      const expected = [true, true, false, true, false, true, false, true, false];
      users.forEach((u, i) => {
        const r = checkRateLimit(`inter-${u}`);
        assert.equal(r.allowed, expected[i], `user ${u} na pozycji ${i}`);
      });
    });

    it("200 userow, kazdy 2 razy", () => {
      for (let i = 0; i < 200; i++) {
        assert.equal(checkRateLimit(`dual-u-${i}`).allowed, true, `user ${i} first`);
        assert.equal(checkRateLimit(`dual-u-${i}`).allowed, false, `user ${i} second`);
      }
    });
  });

  describe("edge cases", () => {
    it("pusty userId", () => {
      assert.equal(checkRateLimit("").allowed, true);
    });

    it("userId z znakami specjalnymi", () => {
      assert.equal(checkRateLimit("user:123!@#$%").allowed, true);
    });

    it("userId 1000 znakow", () => {
      const longId = "x".repeat(1000);
      assert.equal(checkRateLimit(longId).allowed, true);
      assert.equal(checkRateLimit(longId).allowed, false);
    });
  });

  describe("memory stability", () => {
    it("10 iteracji po 1000 userow", () => {
      for (let round = 0; round < 10; round++) {
        for (let i = 0; i < 1000; i++) {
          checkRateLimit(`mem-${round}-${i}`);
        }
      }
    });
  });
});

describe("checkRateLimit — regression cross-check z z60", () => {
  beforeEach(() => {
    _resetRateLimitMap();
  });

  it("identyczne zachowanie: pierwsze dozwolone, drugie blokowane", () => {
    assert.equal(checkRateLimit("cross-user").allowed, true);
    assert.equal(checkRateLimit("cross-user").allowed, false);
  });

  it("rozni userzy niezalezni", () => {
    checkRateLimit("cross-a");
    assert.equal(checkRateLimit("cross-a").allowed, false);
    assert.equal(checkRateLimit("cross-b").allowed, true);
  });

  it("szybki test 1000 userow (zgodny z z60)", () => {
    for (let i = 0; i < 1000; i++) {
      assert.equal(checkRateLimit(`cross-${i}`).allowed, true);
    }
    assert.equal(checkRateLimit("cross-0").allowed, false);
    assert.equal(checkRateLimit("cross-999").allowed, false);
  });
});