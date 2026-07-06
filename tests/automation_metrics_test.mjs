import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  computeAutomationMetrics,
  percentile,
  hoursBetween,
  SPRINT_DAYS,
  formatAutomationMetricsReply,
} from "../cloudflare/src/automation_metrics.js";

function createMetricsDb(opts = {}) {
  const components = opts.components || [];
  const events = opts.events || [];
  const links = opts.links || [];

  // dispatch helpers — use'd by computeAutomationMetrics both via direct
  // .first() (no bind args) and via .bind(...).first() (with prepared args).
  async function dispatchFirst(upper, bindArgs) {
    // 1) REJECTED
    if (upper.includes("WHERE NEXT_STATUS = 'REJECTED'")) {
      return { n: events.filter((e) => e.next_status === "rejected").length };
    }
    // 2) APPROVED + CREATED_AT >= ?  (sprint window) — bind('since_iso')
    if (
      upper.includes("WHERE NEXT_STATUS = 'APPROVED'") &&
      upper.includes("AND CREATED_AT >=")
    ) {
      const sinceRaw = bindArgs && bindArgs.length ? bindArgs[0] : null;
      const since = sinceRaw ? Date.parse(sinceRaw) : NaN;
      return {
        n: events.filter(
          (e) =>
            e.next_status === "approved" &&
            !Number.isNaN(Date.parse(e.created_at)) &&
            Date.parse(e.created_at) >= since
        ).length,
      };
    }
    // 3) APPROVED total (false_positive numerator)
    if (upper.includes("WHERE NEXT_STATUS = 'APPROVED'")) {
      return { n: events.filter((e) => e.next_status === "approved").length };
    }
    // 4) kicad_library_components provenance — non-empty symbol/mpn/raw_metadata
    if (
      upper.includes("FROM KICAD_LIBRARY_COMPONENTS") &&
      upper.includes("IS NOT NULL") &&
      upper.includes("<> ''")
    ) {
      const n = components.filter(
        (c) => c.symbol_name && c.mpn && c.raw_metadata_json
      ).length;
      return { n };
    }
    // 5) kicad_library_components total
    if (upper.includes("FROM KICAD_LIBRARY_COMPONENTS")) {
      return { n: components.length };
    }
    // 6) rollback — next_status == previous_status
    if (
      upper.includes("WHERE PREVIOUS_STATUS IS NOT NULL AND NEXT_STATUS = PREVIOUS_STATUS")
    ) {
      return {
        n: events.filter(
          (e) => e.previous_status && e.next_status === e.previous_status
        ).length,
      };
    }
    // 7) total events
    if (upper.includes("FROM KICAD_REVIEW_EVENTS")) {
      return { n: events.length };
    }
    return null;
  }

  async function dispatchAll(upper) {
    if (upper.includes("FROM KICAD_REVIEW_EVENTS E")) {
      const rows = [];
      for (const e of events) {
        if (!["approved", "rejected"].includes(e.next_status)) continue;
        const link = links.find((l) => l.id === e.link_id);
        if (!link || !link.created_at || !link.reviewed_at) continue;
        rows.push({
          event_at: e.created_at,
          reviewed_at: link.reviewed_at,
          created_at: link.created_at,
        });
      }
      return { results: rows };
    }
    return { results: [] };
  }

  async function dispatchRun(upper) {
    if (upper.startsWith("CREATE TABLE")) return { success: true };
    if (upper.startsWith("CREATE INDEX")) return { success: true };
    // INSERT INTO automation_metrics (persists snapshot, not asserted)
    if (upper.startsWith("INSERT INTO AUTOMATION_METRICS")) return { success: true };
    return { success: true };
  }

  return {
    _components: components,
    _events: events,
    _links: links,
    prepare(sql) {
      const upper = sql.toUpperCase().replace(/\s+/g, " ").trim();
      const base = {
        async first() {
          return dispatchFirst(upper, []);
        },
        async all() {
          return dispatchAll(upper);
        },
        async run() {
          return dispatchRun(upper);
        },
        bind(...args) {
          return {
            async first() {
              return dispatchFirst(upper, args);
            },
            async all() {
              return dispatchAll(upper);
            },
            async run() {
              return dispatchRun(upper);
            },
          };
        },
      };
      return base;
    },
  };
}

describe("Automation metrics dashboard (B4, H2 roadmapa)", () => {
  it("returns no_db when DB missing (fail-open)", async () => {
    const env = {};
    const snap = await computeAutomationMetrics(env, "2026-07-06T00:00:00Z");
    assert.equal(snap.error, "no_db");
    assert.equal(snap.measured_at, "2026-07-06T00:00:00Z");
  });

  it("percentile handles empty, single, multiple values", () => {
    assert.equal(percentile([], 50), 0);
    assert.equal(percentile([5], 50), 5);
    assert.equal(percentile([10, 20, 30, 40], 50), 25);
    assert.equal(percentile([1, 2, 3, 4, 5], 0), 1);
    assert.equal(percentile([1, 2, 3, 4, 5], 100), 5);
  });

  it("hoursBetween computes absolute delta in hours", () => {
    assert.equal(
      hoursBetween("2026-07-06T00:00:00Z", "2026-07-06T12:00:00Z"),
      12
    );
    assert.equal(hoursBetween("bad", "2026-07-06T00:00:00Z"), null);
  });

  it("coverage = % components with symbol_name + mpn + raw_metadata_json", async () => {
    const db = createMetricsDb({
      components: [
        { symbol_name: "TPS", mpn: "TPS1", raw_metadata_json: '{"k":1}' },
        { symbol_name: "R", mpn: "", raw_metadata_json: "{}" },
        { symbol_name: "", mpn: "X", raw_metadata_json: "{}" },
      ],
    });
    const snap = await computeAutomationMetrics({ DB: db }, "2026-07-06T00:00:00Z");
    assert.equal(snap.metrics.coverage, 33.3);
  });

  it("coverage = 0 when no components", async () => {
    const db = createMetricsDb({ components: [] });
    const snap = await computeAutomationMetrics({ DB: db });
    assert.equal(snap.metrics.coverage, 0);
  });

  it("false_positive = rejected/approved * 100", async () => {
    const db = createMetricsDb({
      events: [
        { next_status: "approved" },
        { next_status: "approved" },
        { next_status: "approved" },
        { next_status: "rejected" },
        { next_status: "rejected" },
        { next_status: "rejected" },
      ],
    });
    const snap = await computeAutomationMetrics({ DB: db });
    assert.equal(snap.metrics.false_positive, 100);
    assert.equal(snap.metrics.approved_total, 3);
    assert.equal(snap.metrics.rejected_total, 3);
  });

  it("false_positive = 0 when no approved (avoid div/0)", async () => {
    const db = createMetricsDb({
      events: [{ next_status: "rejected" }],
    });
    const snap = await computeAutomationMetrics({ DB: db });
    assert.equal(snap.metrics.false_positive, 0);
  });

  it("p50_review_hours computed from link created_at vs reviewed_at", async () => {
    const db = createMetricsDb({
      events: [{ link_id: 1, next_status: "approved", created_at: "2026-07-06T00:00:00Z" }],
      links: [
        {
          id: 1,
          created_at: "2026-07-05T00:00:00Z",
          reviewed_at: "2026-07-05T23:00:00Z",
        },
      ],
    });
    const snap = await computeAutomationMetrics({ DB: db });
    assert.equal(snap.metrics.p50_review_hours, 23);
    assert.equal(snap.metrics.review_samples, 1);
  });

  it("p50_review_hours = 0 when no matching events", async () => {
    const db = createMetricsDb({ events: [], links: [] });
    const snap = await computeAutomationMetrics({ DB: db });
    assert.equal(snap.metrics.p50_review_hours, 0);
    assert.equal(snap.metrics.review_samples, 0);
  });

  it("rollback_success = 100 when no rollback events (next=prev)", async () => {
    const db = createMetricsDb({
      events: [
        { previous_status: "suggested", next_status: "approved" },
        { previous_status: "suggested", next_status: "rejected" },
      ],
    });
    const snap = await computeAutomationMetrics({ DB: db });
    assert.equal(snap.metrics.rollback_success, 100);
    assert.equal(snap.metrics.rollback_events, 0);
  });

  it("rollback_success < 100 when rollback events present", async () => {
    const db = createMetricsDb({
      events: [
        { previous_status: "suggested", next_status: "approved" },
        { previous_status: "approved", next_status: "approved" },
        { previous_status: "approved", next_status: "approved" },
        { previous_status: "suggested", next_status: "rejected" },
      ],
    });
    const snap = await computeAutomationMetrics({ DB: db });
    // 2 rollbackow z 4 = 50% success
    assert.equal(snap.metrics.rollback_events, 2);
    assert.ok(
      Math.abs(snap.metrics.rollback_success - 50) < 0.1,
      `rollback_success=${snap.metrics.rollback_success} ~ 50`
    );
  });

  it("accepted_per_sprint counts approved in last SPRINT_DAYS days", async () => {
    const now = "2026-07-06T00:00:00Z";
    const cutoff = new Date(Date.parse(now) - SPRINT_DAYS * 24 * 60 * 60 * 1000).toISOString();
    const db = createMetricsDb({
      events: [
        { next_status: "approved", created_at: now },
        { next_status: "approved", created_at: cutoff },
        { next_status: "approved", created_at: "2020-01-01T00:00:00Z" },
        { next_status: "rejected", created_at: now },
      ],
    });
    const snap = await computeAutomationMetrics({ DB: db }, now);
    // 2 approved w oknie (2020 excluded, rejected excluded)
    assert.equal(snap.metrics.accepted_per_sprint, 2);
    assert.equal(snap.metrics.sprint_window_days, SPRINT_DAYS);
  });

  it("metrics snapshot includes all 5 minimal metric keys", async () => {
    const db = createMetricsDb({ components: [], events: [], links: [] });
    const snap = await computeAutomationMetrics({ DB: db });
    for (const key of [
      "coverage",
      "false_positive",
      "p50_review_hours",
      "rollback_success",
      "accepted_per_sprint",
    ]) {
      assert.ok(key in snap.metrics, `missing metric ${key}`);
      assert.equal(typeof snap.metrics[key], "number");
    }
    assert.ok(snap.measured_at);
  });

  it("formatAutomationMetricsReply: null snapshot -> fallback text", () => {
    assert.ok(formatAutomationMetricsReply(null).includes("Brak danych"));
  });

  it("formatAutomationMetricsReply: error=no_db -> niedostępne", () => {
    const txt = formatAutomationMetricsReply({ error: "no_db" });
    assert.ok(/niedostępne|D1/.test(txt));
  });

  it("formatAutomationMetricsReply: pełny snapshot z 5 metrykami", async () => {
    const db = createMetricsDb({
      components: [{ symbol_name: "TPS", mpn: "TPS1", raw_metadata_json: "{}" }],
      events: [
        { link_id: 1, next_status: "approved", created_at: "2026-07-06T00:00:00Z" },
        { next_status: "rejected", created_at: "2026-07-06T00:00:00Z" },
      ],
      links: [
        { id: 1, created_at: "2026-07-05T00:00:00Z", reviewed_at: "2026-07-05T10:00:00Z" },
      ],
    });
    const snap = await computeAutomationMetrics({ DB: db }, "2026-07-06T12:00:00Z");
    const txt = formatAutomationMetricsReply(snap);
    assert.ok(txt.includes("coverage"), txt);
    assert.ok(txt.includes("false-positive"), txt);
    assert.ok(txt.includes("p50 review"), txt);
    assert.ok(txt.includes("rollback success"), txt);
    assert.ok(/accepted\/sprint/.test(txt), txt);
    assert.ok(txt.includes("measured_at"), txt);
    // Bez wycieku sekretów — sprawdzimy, że reply nie zawiera identyfikatorów D1
    assert.ok(!/PROVIDER_TRUST_EDITOR_SECRET|write_token/i.test(txt), txt);
  });
});