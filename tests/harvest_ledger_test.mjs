import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  computeHarvestDedupChecksum,
  monthKeyFromIso,
  recordHarvest,
  validateHarvestRecord,
} from "../cloudflare/src/harvest_ledger.js";

const NOW = "2026-08-26T12:00:00.000Z";

function validRecord() {
  return {
    crop_profile: "leafy_greens_aquaponics",
    mass_g: 420.5,
    harvested_at: "2026-08-25T09:00:00.000Z",
    quality_note: "dobre liście, bez nitratów",
    source: "operator_anna",
  };
}

function createMockDb({ existingChecksums = [], existingMass = 0 } = {}) {
  const records = [];
  const auditEvents = [];
  const metrics = [];
  let seededMass = existingMass;
  return {
    records,
    auditEvents,
    metrics,
    prepare(sql) {
      return {
        bind(...args) {
          return {
            first() {
              if (sql.includes("FROM harvest_records WHERE dedup_checksum")) {
                const checksum = args[0];
                if (records.some((row) => row.dedup_checksum === checksum)) return { id: 1 };
                if (existingChecksums.includes(checksum)) return { id: 2 };
                return null;
              }
              if (sql.includes("SELECT SUM(mass_g)")) {
                const [cellId, monthKey] = args;
                const scoped = [ ...records, ...existingChecksums.map((c) => ({ grow_cell_id: cellId, mass_g: 0 })) ]
                  .filter((row) => row.grow_cell_id === cellId && row.harvested_at.startsWith(monthKey));
                const total = seededMass + scoped.reduce((sum, row) => sum + (row.mass_g || 0), 0);
                return { total_mass: total };
              }
              return null;
            },
            async run() {
              if (sql.includes("INSERT INTO harvest_records")) {
                const [grow_cell_id, crop_profile, mass_g, , , harvested_at, , checksum] = args;
                records.push({ grow_cell_id, crop_profile, mass_g, harvested_at, dedup_checksum: checksum });
              } else if (sql.includes("INSERT INTO harvest_audit_events")) {
                auditEvents.push({ kind: "harvest_record", mass_g: args[1], month_key: args[2] });
              } else if (sql.includes("INSERT INTO automation_metrics")) {
                metrics.push({ metric_key: args[0], metric_value: args[1], window: "monthly" });
              }
              return { meta: {} };
            },
            async all() {
              return { results: [] };
            },
          };
        },
      };
    },
  };
}

describe("harvest ledger T36", () => {
  it("validates harvest contract", () => {
    assert.deepEqual(validateHarvestRecord(validRecord(), NOW), []);
    const problems = validateHarvestRecord({
      crop_profile: "",
      mass_g: -5,
      harvested_at: "2099-01-01T00:00:00.000Z",
    }, NOW);
    assert.ok(problems.includes("crop_profile_required"));
    assert.ok(problems.some((entry) => entry.startsWith("mass_g_positive")));
    assert.ok(problems.includes("harvested_at_not_in_future"));
    assert.ok(validateHarvestRecord({ crop_profile: "x", mass_g: true, harvested_at: NOW }, NOW).some((entry) => entry.startsWith("mass_g")));
    // 3 minuty w przyszłość mieści się w tolerancji zegara.
    const skewOk = validateHarvestRecord({
      crop_profile: "x",
      mass_g: 10,
      harvested_at: "2026-08-26T12:03:00.000Z",
    }, NOW);
    assert.deepEqual(skewOk, []);
  });

  it("computes identity-sensitive dedup checksum", async () => {
    const base = { grow_cell_id: "cell-01", ...validRecord() };
    const same = await computeHarvestDedupChecksum({ ...base, quality_note: "inna notatka" });
    const otherCell = await computeHarvestDedupChecksum({ ...base, grow_cell_id: "cell-02" });
    const otherMass = await computeHarvestDedupChecksum({ ...base, mass_g: 421 });
    assert.equal(await computeHarvestDedupChecksum(base), same);
    assert.notEqual(await computeHarvestDedupChecksum(base), otherCell);
    assert.notEqual(await computeHarvestDedupChecksum(base), otherMass);
  });

  it("records harvest with audit event and monthly aggregate", async () => {
    const db = createMockDb();
    const result = await recordHarvest(
      { DB: db },
      "phone-aquaponics-observer-01",
      validRecord(),
      { now: NOW }
    );
    assert.equal(result.success, true);
    assert.equal(result.month_key, "2026-08");
    assert.equal(db.records.length, 1);
    assert.equal(db.records[0].grow_cell_id, "phone-aquaponics-observer-01");
    assert.equal(db.auditEvents.length, 1);

    const metric = db.metrics.find((m) => m.metric_key === "harvest_phone-aquaponics-observer-01_2026-08");
    assert.ok(metric, "monthly aggregate metric missing");
    assert.equal(metric.metric_value, 420.5);

    // Duplikat (ten sam plon zgłoszony drugi raz) -> odrzucony, zero nowych wpisów.
    const duplicate = await recordHarvest({ DB: db }, "phone-aquaponics-observer-01", validRecord(), { now: NOW });
    assert.equal(duplicate.reason, "duplicate_harvest");
    assert.equal(db.records.length, 1);
    assert.equal(db.auditEvents.length, 1);
  });

  it("refuses invalid records without writing anything", async () => {
    const db = createMockDb();
    const bad = await recordHarvest({ DB: db }, "cell-01", { mass_g: "dużo" }, { now: NOW });
    assert.equal(bad.reason, "invalid_record");
    assert.ok(bad.errors.includes("crop_profile_required"));
    assert.equal(db.records.length, 0);
    assert.equal(db.metrics.length, 0);

    const noDb = await recordHarvest({}, "cell-01", validRecord());
    assert.equal(noDb.reason, "no_db");
  });

  it("derives month key from ISO timestamp", () => {
    assert.equal(monthKeyFromIso("2026-08-26T12:00:00.000Z"), "2026-08");
    assert.equal(monthKeyFromIso(""), "");
  });
});
