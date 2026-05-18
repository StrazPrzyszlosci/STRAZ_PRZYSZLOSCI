import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { applyMigrations, getSchemaVersion, MIGRATIONS } from "../cloudflare/src/schema_migrations.js";

function createMockDb() {
  const tables = new Map();
  tables.set("schema_migrations", []);
  return {
    prepare(sql) {
      return {
        run() {
          if (sql.trim().toLowerCase().startsWith("create table")) {
            const match = sql.match(/CREATE TABLE IF NOT EXISTS\s+(\w+)/i);
            if (match && !tables.has(match[1])) {
              tables.set(match[1], []);
            }
          }
          return { changes: 1 };
        },
        all() {
          return { results: tables.get("schema_migrations") || [] };
        },
        first() {
          const rows = tables.get("schema_migrations") || [];
          return rows[rows.length - 1] || null;
        },
        bind(...args) {
          const insertMatch = sql.match(/INSERT INTO schema_migrations/);
          if (insertMatch) {
            const [version, name, applied_at] = args;
            if (!tables.has("schema_migrations")) tables.set("schema_migrations", []);
            tables.get("schema_migrations").push({ version, name, applied_at });
          }
          return { run: () => ({ changes: 1 }), all: () => ({ results: [] }), first: () => null };
        },
      };
    },
  };
}

describe("D1 Schema Migrations (Z86)", () => {
  it("creates schema_migrations table on first run", async () => {
    const db = createMockDb();
    console.log("db type:", typeof db);
    console.log("db.prepare type:", typeof db.prepare);
    try {
      const result = await applyMigrations(db);
      assert.equal(result.success, true);
      assert.ok(result.applied >= 0);
    } catch (err) {
      console.error("Migration test error:", err);
      throw err;
    }
  });

  it("second run reports no new migrations (idempotent)", async () => {
    const db = createMockDb();
    const first = await applyMigrations(db);
    assert.equal(first.success, true);

    const second = await applyMigrations(db);
    assert.equal(second.success, true);
    assert.equal(second.reason, "no_migrations");
    assert.equal(second.applied, 0);
  });

  it("getSchemaVersion returns the latest applied version", async () => {
    const db = createMockDb();
    await applyMigrations(db);
    const version = await getSchemaVersion(db);
    assert.ok(typeof version === "string");
    assert.ok(version.length > 0);
  });

  it("fail-open when DB is missing", async () => {
    const result = await applyMigrations(null);
    assert.equal(result.success, false);
    assert.equal(result.reason, "no_db");
  });

  it("MIGRATIONS array is ordered and has versions", () => {
    assert.ok(Array.isArray(MIGRATIONS));
    assert.ok(MIGRATIONS.length > 0);
    for (const m of MIGRATIONS) {
      assert.ok(m.version);
      assert.ok(m.name);
      assert.ok(m.sql);
    }
    
    // Versions should be monotonically increasing
    for (let i = 1; i < MIGRATIONS.length; i++) {
      assert.ok(MIGRATIONS[i].version >= MIGRATIONS[i - 1].version);
    }
  });


  it("includes KiCad staging/provenance migrations (Z88)", () => {
    const allSql = MIGRATIONS.map((migration) => migration.sql).join("\n");
    assert.ok(allSql.includes("kicad_library_sources"));
    assert.ok(allSql.includes("kicad_library_components"));
    assert.ok(allSql.includes("recycled_part_kicad_links"));
    assert.ok(allSql.includes("idx_kicad_components_normalized_part_number"));
    assert.ok(allSql.includes("idx_recycled_part_kicad_links_review_status"));
    assert.ok(allSql.includes("kicad_review_events"));
  });

  it("all migrations are idempotent (contain IF NOT EXISTS)", () => {
    for (const m of MIGRATIONS) {
      assert.ok(m.sql.toUpperCase().includes("IF NOT EXISTS"), `Migration ${m.version} not idempotent: ${m.name}`);
    }
  });
});