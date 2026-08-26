import { toIsoNow } from "./base_utils.js";

const DEFAULT_REPO = "StrazPrzyszlosci/STRAZ_PRZYSZLOSCI";
const PACK_ID_RE = /^[a-z0-9][a-z0-9._-]{2,120}$/i;

export class ExecutionPackNotFoundError extends Error { }

function trimText(value) {
  return String(value || "").trim();
}

export function parseExecutionPackStartCommand(text) {
  const normalized = trimText(text);
  const match = normalized.match(/^!(?:execution-pack|execution_pack|pack)\s+start\s+([^\s]+)(?:\s+(.+))?$/i);
  if (!match) return null;
  return {
    action: "start",
    pack_id: match[1],
    reviewer: trimText(match[2]),
  };
}

export function validateExecutionPackId(packId) {
  const value = trimText(packId);
  if (!PACK_ID_RE.test(value)) {
    throw new Error("Nieprawidlowy identyfikator execution_pack. Uzyj 3-120 znakow: litery, cyfry, '.', '_' lub '-'.");
  }
  if (value.includes("..") || value.includes("/") || value.includes("\\")) {
    throw new Error("Identyfikator execution_pack nie moze zawierac sciezek.");
  }
  return value;
}

function resolveReviewer(env, explicitReviewer) {
  const reviewer = trimText(explicitReviewer || env.EXECUTION_PACK_DEFAULT_REVIEWER);
  if (!reviewer) {
    throw new Error("Brak reviewera. Podaj `!execution-pack start <id> <reviewer>` albo ustaw EXECUTION_PACK_DEFAULT_REVIEWER.");
  }
  return reviewer;
}

function actorIdentity(message, platform = "discord") {
  const username = trimText(message?.username);
  const userId = trimText(message?.user_id);
  if (username) return `${platform}:${username}#${userId || "unknown"}`;
  if (userId) return `${platform}:${userId}`;
  return `${platform}:unknown`;
}

function canaryBranchName(packId, nowIso) {
  const stamp = nowIso.replace(/[-:]/g, "").replace(/\.\d+Z$/, "Z");
  return `canary/execution-pack/${packId}/${stamp}`;
}

function buildCanaryPrBody({ packId, reviewer, actor, branch }) {
  return [
    `CANARY_PILOT_PACKET for execution_pack \`${packId}\`.`,
    "",
    "Safety gates:",
    "- bot created a branch/PR proposal only; no merge to main is performed by the bot;",
    "- human review is required before merge or production synchronization;",
    "- no write to `recycled_part_master` is allowed from this initiator.",
    "",
    `Reviewer: ${reviewer}`,
    `Initiated by: ${actor}`,
    `Branch: ${branch}`,
  ].join("\n");
}

async function insertExecutionPackRecord(env, record) {
  if (!env.DB) return { success: false, reason: "no_db" };
  await env.DB.prepare(
    `INSERT INTO execution_packs
      (pack_id, status, reviewer, fork_branch, pr_url, canary_mode, initiated_by, platform, created_at, updated_at)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
  )
    .bind(
      record.pack_id,
      record.status,
      record.reviewer,
      record.fork_branch,
      record.pr_url,
      1,
      record.initiated_by,
      record.platform,
      record.created_at,
      record.updated_at
    )
    .run();
  return { success: true };
}

async function createGitHubCanaryPr(env, request) {
  if (String(env.EXECUTION_PACK_DRY_RUN || "").toLowerCase() === "true" || env.EXECUTION_PACK_DRY_RUN === "1") {
    return {
      pr_url: `https://example.invalid/canary/${encodeURIComponent(request.packId)}`,
      mode: "dry_run",
    };
  }
  const token = trimText(env.GITHUB_TOKEN || env.EXECUTION_PACK_GITHUB_TOKEN);
  if (!token) {
    return { pr_url: null, mode: "no_token" };
  }
  const repo = trimText(env.EXECUTION_PACK_GITHUB_REPO) || DEFAULT_REPO;
  const fetchImpl = env.__TEST_FETCH || fetch;
  const response = await fetchImpl(`https://api.github.com/repos/${repo}/pulls`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: "application/vnd.github+json",
      "Content-Type": "application/json",
      "User-Agent": "straz-przyszlosci-execution-pack-bot",
    },
    body: JSON.stringify({
      title: `CANARY execution_pack: ${request.packId}`,
      head: request.branch,
      base: "main",
      body: request.body,
      draft: true,
      maintainer_can_modify: true,
    }),
  });
  if (!response.ok) {
    throw new Error(`GitHub PR create failed: ${response.status}`);
  }
  const data = await response.json();
  return { pr_url: data.html_url || data.url || null, mode: "github" };
}

export async function startExecutionPack(env, message, options = {}) {
  const packId = validateExecutionPackId(options.pack_id);
  const reviewer = resolveReviewer(env, options.reviewer);
  const now = options.now || toIsoNow();
  const platform = options.platform || "discord";
  const actor = actorIdentity(message, platform);
  const branch = canaryBranchName(packId, now);
  const body = buildCanaryPrBody({ packId, reviewer, actor, branch });
  const pr = await createGitHubCanaryPr(env, { packId, reviewer, actor, branch, body });
  const record = {
    pack_id: packId,
    status: "started",
    reviewer,
    fork_branch: branch,
    pr_url: pr.pr_url,
    initiated_by: actor,
    platform,
    created_at: now,
    updated_at: now,
  };
  await insertExecutionPackRecord(env, record);
  return { ...record, github_mode: pr.mode };
}

export function formatExecutionPackStartReply(result) {
  return [
    `CANARY execution_pack uruchomiony: ${result.pack_id}`,
    `Status: ${result.status}`,
    `Reviewer: ${result.reviewer}`,
    `Branch: ${result.fork_branch}`,
    `PR: ${result.pr_url || "do utworzenia przez operatora/offline job (brak tokenu GitHub w bocie)"}`,
    "Gate: bot nie merge'uje do main i nie pisze do recycled_part_master; wymagany human review.",
  ].join("\n");
}

// T23 — status flow: started -> closed -> merged. Bot nigdy nie merge'uje;
// 'merged' to tylko zapis potwierdzenia merge'a wykonanego przez człowieka.
export const EXECUTION_PACK_STATUS_TRANSITIONS = {
  started: ["closed"],
  closed: ["merged"],
  merged: [],
};

const GITHUB_PR_URL_RE = /^https:\/\/github\.com\/([^/]+)\/([^/]+)\/pull\/(\d+)/;

function parseGitHubPrUrl(prUrl) {
  const match = String(prUrl || "").match(GITHUB_PR_URL_RE);
  if (!match) return null;
  return { owner: match[1], repo: match[2], number: Number(match[3]) };
}

export async function getLatestExecutionPack(env, packId) {
  if (!env?.DB) return null;
  const result = await env.DB.prepare(
    `SELECT id, pack_id, status, reviewer, fork_branch, pr_url, canary_mode, initiated_by, platform, created_at, updated_at
     FROM execution_packs WHERE pack_id = ? ORDER BY id DESC LIMIT 1`
  ).bind(packId).first();
  return result || null;
}

async function closeGitHubPr(env, prUrl) {
  if (String(env.EXECUTION_PACK_DRY_RUN || "").toLowerCase() === "true" || env.EXECUTION_PACK_DRY_RUN === "1") {
    return { closed: true, mode: "dry_run" };
  }
  const token = trimText(env.GITHUB_TOKEN || env.EXECUTION_PACK_GITHUB_TOKEN);
  const pr = parseGitHubPrUrl(prUrl);
  if (!token || !pr) {
    return { closed: false, mode: "no_token_or_pr_url" };
  }
  const fetchImpl = env.__TEST_FETCH || fetch;
  const response = await fetchImpl(`https://api.github.com/repos/${pr.owner}/${pr.repo}/pulls/${pr.number}`, {
    method: "PATCH",
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: "application/vnd.github+json",
      "Content-Type": "application/json",
      "User-Agent": "straz-przyszlosci-execution-pack-bot",
    },
    body: JSON.stringify({ state: "closed" }),
  });
  if (!response.ok) {
    throw new Error(`GitHub PR close failed: ${response.status}`);
  }
  // UWAGA: PATCH state=closed zamyka PR bez merge'a. Bot nie wykonuje PUT /merge.
  return { closed: true, mode: "github" };
}

async function insertExecutionPackStatusRecord(env, previous, nextStatus, now, extra = {}) {
  await env.DB.prepare(
    `INSERT INTO execution_packs
      (pack_id, status, reviewer, fork_branch, pr_url, canary_mode, initiated_by, platform, created_at, updated_at)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
  ).bind(
    previous.pack_id,
    nextStatus,
    extra.reviewer || previous.reviewer,
    previous.fork_branch,
    previous.pr_url,
    previous.canary_mode === 0 ? 0 : 1,
    previous.initiated_by,
    previous.platform,
    previous.created_at,
    now
  ).run();
}

export function parseExecutionPackStatusCommand(text) {
  const normalized = trimText(text);
  const match = normalized.match(/^!(?:execution-pack|execution_pack|pack)\s+(close|merged)\s+([^\s]+)(?:\s+(.+))?$/i);
  if (!match) return null;
  return {
    action: match[1].toLowerCase() === "close" ? "close" : "merged",
    pack_id: match[2],
    reviewer: trimText(match[3]),
  };
}

export async function updateExecutionPackStatus(env, packId, nextStatus, options = {}) {
  const normalizedPackId = validateExecutionPackId(packId);
  if (!EXECUTION_PACK_STATUS_TRANSITIONS.hasOwnProperty(nextStatus)) {
    throw new Error(`Nieznany status execution_pack: ${nextStatus}. Dozwolone: closed, merged.`);
  }
  const previous = options.previous || await getLatestExecutionPack(env, normalizedPackId);
  if (!previous) {
    throw new ExecutionPackNotFoundError(`Nie znaleziono execution_pack: ${normalizedPackId}`);
  }
  const allowed = EXECUTION_PACK_STATUS_TRANSITIONS[previous.status] || [];
  if (!allowed.includes(nextStatus)) {
    throw new Error(
      `Niedozwolona tranzycja ${previous.status} -> ${nextStatus} dla ${normalizedPackId}. Dozwolone: ${allowed.join(", ") || "brak"}.`
    );
  }
  const now = options.now || toIsoNow();

  if (nextStatus === "closed") {
    if (previous.pr_url && options.skipGithubClose !== true) {
      const gh = await closeGitHubPr(env, previous.pr_url);
      if (gh.closed === false && options.requireGithubClose) {
        throw new Error("Brak tokenu GitHub lub rozpoznawalnego PR URL — zamknij PR recznie i uzyj '!execution-pack merged'.");
      }
    }
  }

  if (nextStatus === "merged") {
    if (!previous.pr_url) {
      throw new Error("Status 'merged' wymaga istniejacego PR URL (start -> PR -> close/merge przez czlowieka).");
    }
    const reviewer = trimText(options.reviewer || "");
    if (!reviewer) {
      throw new Error("Status 'merged' wymaga potwierdzenia reviewera: '!execution-pack merged <pack_id> <reviewer>'.");
    }
  }

  await insertExecutionPackStatusRecord(env, previous, nextStatus, now, { reviewer: options.reviewer });
  return {
    pack_id: normalizedPackId,
    previous_status: previous.status,
    status: nextStatus,
    fork_branch: previous.fork_branch,
    pr_url: previous.pr_url,
    reviewer: options.reviewer || previous.reviewer,
    updated_at: now,
    merged_by_human_only: nextStatus === "merged",
  };
}

export function formatExecutionPackStatusReply(result) {
  const lines = [
    `execution_pack ${result.pack_id}: ${result.previous_status} -> ${result.status}`,
    `PR: ${result.pr_url || "brak"}`,
  ];
  if (result.status === "merged") {
    lines.push(`Merge potwierdzony przez czlowieka: ${result.reviewer}`);
  }
  if (result.status === "closed") {
    lines.push("PR zamkniety bez merge (rollback-safe). Bot nie wykonywal merge.");
  }
  return lines.join("\n");
}


export async function handleExecutionPackCommand(env, message, platform = "discord") {
  const parsed = parseExecutionPackStartCommand(message?.text || "");
  if (parsed) {
    const result = await startExecutionPack(env, message, { ...parsed, platform });
    return { reply_text: formatExecutionPackStartReply(result) };
  }
  const statusCommand = parseExecutionPackStatusCommand(message?.text || "");
  if (statusCommand) {
    try {
      const result = await updateExecutionPackStatus(env, statusCommand.pack_id, statusCommand.action === "close" ? "closed" : "merged", {
        reviewer: statusCommand.reviewer,
      });
      return { reply_text: formatExecutionPackStatusReply(result) };
    } catch (err) {
      return { reply_text: `Blad execution_pack: ${err.message}` };
    }
  }
  return {
    reply_text: "Uzycie: `!execution-pack start <pack_id> <reviewer>` | `!execution-pack close <pack_id>` | `!execution-pack merged <pack_id> <reviewer>`",
  };
}

export const __test__ = { actorIdentity, buildCanaryPrBody, canaryBranchName, parseGitHubPrUrl };
