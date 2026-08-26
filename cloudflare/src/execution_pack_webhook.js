/**
 * T30 — GitHub webhook sync statusów execution_packs.
 *
 * Webhook `pull_request` (action=closed) aktualizuje ledger execution_packs:
 *  - merged=false -> 'closed' (PR zamknięty bez merge, rollback-safe),
 *  - merged=true  -> 'merged' (człowiek wykonał merge na GitHubie; bot tylko
 *    zapisuje potwierdzenie — nigdy sam nie merge'uje).
 *
 * Bezpieczeństwo: HMAC SHA-256 z GITHUB_WEBHOOK_SECRET, porównanie timing-safe.
 * Inne akcje (opened/synchronize/reopened) są ignorowane.
 */

import { timingSafeEqualString } from "./base_utils.js";
import { updateExecutionPackStatus } from "./execution_pack_initiator.js";

async function hmacSha256Hex(secret, payload) {
  const key = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"]
  );
  const signature = await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(payload));
  return Array.from(new Uint8Array(signature), (byte) => byte.toString(16).padStart(2, "0")).join("");
}

export async function verifyWebhookSignature(secret, rawBody, signatureHeader) {
  if (!secret || typeof rawBody !== "string") return false;
  const headerValue = String(signatureHeader || "");
  if (!headerValue.startsWith("sha256=")) return false;
  const expected = headerValue.slice("sha256=".length).trim().toLowerCase();
  const actual = await hmacSha256Hex(secret, rawBody);
  return timingSafeEqualString(expected, actual);
}

export function mapPullRequestAction(payload) {
  const pr = payload?.pull_request;
  if (!pr || typeof pr !== "object") return null;
  const action = String(payload.action || "");
  if (action !== "closed") return null;
  const merged = pr.merged === true;
  return {
    nextStatus: merged ? "merged" : "closed",
    prUrl: String(pr.html_url || ""),
    sender: String(payload.sender?.login || "webhook"),
  };
}

export async function findExecutionPackByPr(db, prUrl) {
  if (!db) return null;
  const result = await db.prepare(
    `SELECT id, pack_id, status, reviewer, fork_branch, pr_url, canary_mode, initiated_by, platform, created_at, updated_at
     FROM execution_packs WHERE pr_url = ? ORDER BY id DESC LIMIT 1`
  ).bind(String(prUrl || "")).first();
  return result || null;
}

export async function syncExecutionPackFromWebhook(env, payload, options = {}) {
  if (!env?.DB) return { success: false, reason: "no_db" };
  const mapped = mapPullRequestAction(payload);
  if (!mapped) {
    return { success: true, ignored: true, action: String(payload?.action || "") };
  }
  const previous = await findExecutionPackByPr(env.DB, mapped.prUrl);
  if (!previous) {
    return { success: false, reason: "pack_not_found_for_pr_url", pr_url: mapped.prUrl };
  }
  if (previous.status === mapped.nextStatus) {
    return { success: true, unchanged: true, pack_id: previous.pack_id, status: previous.status };
  }
  // Merge/close wykonany przez czlowieka na GitHubie; bot tylko zapisuje w ledgerze.
  const reviewer = `github:${mapped.sender}`;
  const result = await updateExecutionPackStatus(env, previous.pack_id, mapped.nextStatus, {
    previous,
    reviewer,
    skipGithubClose: true,
    now: options.now,
  });
  return { success: true, source: "github_webhook", ...result };
}
