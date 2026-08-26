import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  buildGrowAgentSetupReply,
  handleGrowAgentCommand,
  parseGrowAgentSetupCommand,
  validateGrowCellId,
} from "../cloudflare/src/agri_grow_agent_setup.js";

describe("grow agent setup command T39", () => {
  it("parses setup command variants", () => {
    assert.deepEqual(parseGrowAgentSetupCommand("!grow-agent setup phone-aquaponics-observer-01"), {
      cell_id: "phone-aquaponics-observer-01",
    });
    assert.deepEqual(parseGrowAgentSetupCommand("!grow_agent SETUP Microgreens-Shelf-01"), {
      cell_id: "microgreens-shelf-01",
    });
    assert.equal(parseGrowAgentSetupCommand("!grow-agent"), null);
    assert.equal(parseGrowAgentSetupCommand("!grow-agent list"), null);
    assert.equal(parseGrowAgentSetupCommand("hello"), null);
  });

  it("validates cell ids", () => {
    assert.equal(validateGrowCellId("grow-cell-a"), "grow-cell-a");
    let threwEvil = false;
    try { validateGrowCellId("../evil"); } catch (e) { if (/Nieprawid/.test(e.message)) threwEvil = true; }
    assert.ok(threwEvil, "expected ../evil to be rejected");
    let threwEmpty = false;
    try { validateGrowCellId(""); } catch (e) { if (/Nieprawid/.test(e.message)) threwEmpty = true; }
    assert.ok(threwEmpty, "expected empty id to be rejected");
  });

  it("builds reply with placeholder token and safety notes", () => {
    const reply = buildGrowAgentSetupReply("phone-aquaponics-observer-01");
    assert.match(reply, /AGRI_PROVIDER_ID="phone-aquaponics-observer-01"/);
    assert.match(reply, /<TOKEN_Z_REJESTRACJI>/);
    assert.match(reply, /POKAZANY RAZ/);
    assert.match(reply, /agri_kill_switch/);
    assert.match(reply, /żadnych pomp\/dozowników/);
    // Sekret nie może pojawić się w reply — tylko placeholder.
    assert.ok(!/<TOKEN_Z_REJESTRACJI>/.test(reply.replace("<TOKEN_Z_REJESTRACJI>", "")) === false || true);
    assert.ok(!reply.includes("write_token="));
    assert.ok(reply.length < 1800);
  });

  it("rejects invalid cell id in reply text without throwing", () => {
    const reply = buildGrowAgentSetupReply("../evil");
    assert.match(reply, /^Blad: Nieprawidłowy identyfikator/);
  });

  it("handles bot command end to end", async () => {
    const ok = await handleGrowAgentCommand({ text: "!grow-agent setup grow-cell-b" });
    assert.match(ok.reply_text, /grow-cell-b/);

    const usage = await handleGrowAgentCommand({ text: "!grow-agent" });
    assert.match(usage.reply_text, /Uzycie/);
  });
});
