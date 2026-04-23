#!/usr/bin/env python3
"""Lightweight lookup helper for D1/SQLite organization_agent_v1 tables.

Provides quick access to the most common operational queries from the
D1/SQLite Query Cookbook without requiring manual sqlite3 invocation.

Usage:
    python3 pipelines/org_lookup.py --db-path /tmp/org.sqlite3 status-summary
    python3 pipelines/org_lookup.py --db-path /tmp/org.sqlite3 pack-ready
    python3 pipelines/org_lookup.py --db-path /tmp/org.sqlite3 review-queue
    python3 pipelines/org_lookup.py --db-path /tmp/org.sqlite3 blocked
    python3 pipelines/org_lookup.py --db-path /tmp/org.sqlite3 full-chain
    python3 pipelines/org_lookup.py --db-path /tmp/org.sqlite3 integrity-high
    python3 pipelines/org_lookup.py --db-path /tmp/org.sqlite3 recent-approvals
    python3 pipelines/org_lookup.py --db-path /tmp/org.sqlite3 fk-check
"""

import argparse
import sqlite3
import sys


LOOKUPS = {}


def register(name):
    def decorator(fn):
        LOOKUPS[name] = fn
        return fn
    return decorator


def fmt_row(headers, row):
    parts = []
    for h, v in zip(headers, row):
        val = str(v) if v is not None else "NULL"
        if len(val) > 60:
            val = val[:57] + "..."
        parts.append(f"{h}={val}")
    return "  ".join(parts)


def run_query(conn, sql, params=None):
    cur = conn.execute(sql, params or [])
    rows = cur.fetchall()
    headers = [d[0] for d in cur.description] if cur.description else []
    return headers, rows


@register("status-summary")
def status_summary(conn, _args):
    tables = [
        "organization_resource_records",
        "organization_potential_dossiers",
        "organization_capability_gaps",
        "organization_experiments",
        "organization_execution_packs",
        "organization_tasks",
        "organization_runs",
        "organization_artifacts",
        "organization_integrity_risk_assessments",
        "organization_approvals",
        "organization_readiness_gates",
    ]
    print("=== Status Summary ===")
    for tbl in tables:
        try:
            row = conn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()
            print(f"  {tbl}: {row[0]} rows")
        except Exception as exc:
            print(f"  {tbl}: ERROR {exc}")


@register("pack-ready")
def pack_ready(conn, _args):
    sql = (
        "SELECT pack_id, title, status, execution_mode, target_output_kind "
        "FROM organization_execution_packs "
        "WHERE status = 'ready' "
        "ORDER BY created_at ASC"
    )
    headers, rows = run_query(conn, sql)
    print("=== Packs Ready for Execution ===")
    if not rows:
        print("  (none)")
    for r in rows:
        print("  " + fmt_row(headers, r))


@register("review-queue")
def review_queue(conn, _args):
    sql = (
        "SELECT a.artifact_id, a.artifact_kind, a.title, a.review_status, "
        "r.pack_id, a.created_at "
        "FROM organization_artifacts a "
        "JOIN organization_runs r ON r.run_id = a.run_id "
        "WHERE a.review_status IN ('review_ready', 'pending_review') "
        "ORDER BY a.created_at DESC"
    )
    headers, rows = run_query(conn, sql)
    print("=== Review Queue ===")
    if not rows:
        print("  (empty)")
    for r in rows:
        print("  " + fmt_row(headers, r))


@register("blocked")
def blocked(conn, _args):
    queries = [
        (
            "open_gap",
            "SELECT 'open_gap', gap_id, title, severity, status "
            "FROM organization_capability_gaps "
            "WHERE status NOT IN ('resolved', 'closed')",
        ),
        (
            "failed_run",
            "SELECT 'failed_run', run_id, operator_kind, environment_kind, status "
            "FROM organization_runs WHERE status = 'failed'",
        ),
        (
            "failed_gate",
            "SELECT 'failed_gate', gate_id, gate_kind, subject_id, status "
            "FROM organization_readiness_gates WHERE status = 'fail'",
        ),
    ]
    print("=== Blocked Items ===")
    found = False
    for label, sql in queries:
        _, rows = run_query(conn, sql)
        for r in rows:
            found = True
            print(f"  [{label}] " + fmt_row(["id", "title", "detail", "status"], r[1:]))
    if not found:
        print("  (no blockers found)")


@register("full-chain")
def full_chain(conn, _args):
    sql = (
        "SELECT d.dossier_id, d.title AS dossier_title, "
        "g.gap_id, g.title AS gap_title, g.severity, "
        "e.experiment_id, e.status AS experiment_status, "
        "p.pack_id, p.title AS pack_title, p.status AS pack_status, "
        "t.task_id, t.status AS task_status, "
        "r.run_id, r.status AS run_status "
        "FROM organization_potential_dossiers d "
        "LEFT JOIN organization_capability_gaps g ON g.dossier_id = d.dossier_id "
        "LEFT JOIN organization_experiments e ON e.gap_id = g.gap_id "
        "LEFT JOIN organization_execution_packs p ON p.linked_subject_kind = 'experiment' AND p.linked_subject_id = e.experiment_id "
        "LEFT JOIN organization_tasks t ON t.pack_id = p.pack_id "
        "LEFT JOIN organization_runs r ON r.pack_id = p.pack_id "
        "ORDER BY d.overall_priority_score DESC, g.severity, p.created_at"
    )
    headers, rows = run_query(conn, sql)
    print("=== Full Chain: Dossier -> Gap -> Experiment -> Pack -> Task -> Run ===")
    if not rows:
        print("  (no data)")
    for r in rows:
        print("  " + fmt_row(headers, r))


@register("integrity-high")
def integrity_high(conn, _args):
    sql = (
        "SELECT assessment_id, subject_kind, subject_id, assessment_scope, risk_level, status "
        "FROM organization_integrity_risk_assessments "
        "WHERE risk_level IN ('high', 'critical') AND status != 'mitigated' "
        "ORDER BY assessed_at DESC"
    )
    headers, rows = run_query(conn, sql)
    print("=== High/Critical Integrity Risks ===")
    if not rows:
        print("  (none)")
    for r in rows:
        print("  " + fmt_row(headers, r))


@register("recent-approvals")
def recent_approvals(conn, _args):
    sql = (
        "SELECT approval_id, artifact_id, decision, approval_scope, reviewer_role, decided_at "
        "FROM organization_approvals "
        "ORDER BY decided_at DESC LIMIT 20"
    )
    headers, rows = run_query(conn, sql)
    print("=== Recent Approvals ===")
    if not rows:
        print("  (none)")
    for r in rows:
        print("  " + fmt_row(headers, r))


@register("fk-check")
def fk_check(conn, _args):
    print("=== FK Integrity Checks ===")
    checks = [
        (
            "runs without pack",
            "SELECT r.run_id, r.pack_id FROM organization_runs r "
            "LEFT JOIN organization_execution_packs p ON p.pack_id = r.pack_id "
            "WHERE p.pack_id IS NULL",
        ),
        (
            "artifacts without run",
            "SELECT a.artifact_id, a.run_id FROM organization_artifacts a "
            "LEFT JOIN organization_runs r ON r.run_id = a.run_id "
            "WHERE r.run_id IS NULL",
        ),
        (
            "tasks without pack",
            "SELECT t.task_id, t.pack_id FROM organization_tasks t "
            "LEFT JOIN organization_execution_packs p ON p.pack_id = t.pack_id "
            "WHERE p.pack_id IS NULL",
        ),
        (
            "gaps without dossier",
            "SELECT g.gap_id, g.dossier_id FROM organization_capability_gaps g "
            "LEFT JOIN organization_potential_dossiers d ON d.dossier_id = g.dossier_id "
            "WHERE d.dossier_id IS NULL",
        ),
    ]
    found = False
    for label, sql in checks:
        _, rows = run_query(conn, sql)
        if rows:
            found = True
            print(f"  {label}: {len(rows)} orphan(s)")
            for r in rows:
                print("    " + fmt_row(["id", "fk"], r))
    if not found:
        print("  (all FK constraints satisfied)")


def main():
    parser = argparse.ArgumentParser(
        description="Lookup helper for D1/SQLite organization_agent_v1 tables"
    )
    parser.add_argument(
        "--db-path",
        required=True,
        help="Path to local SQLite database file",
    )
    parser.add_argument(
        "lookup",
        choices=sorted(LOOKUPS.keys()),
        help="Lookup query to run",
    )
    args = parser.parse_args()

    if not hasattr(args, "db_path") or not args.db_path:
        parser.error("--db-path is required")

    conn = sqlite3.connect(args.db_path)
    conn.execute("PRAGMA foreign_keys=ON")

    fn = LOOKUPS[args.lookup]
    fn(conn, args)

    conn.close()


if __name__ == "__main__":
    main()
