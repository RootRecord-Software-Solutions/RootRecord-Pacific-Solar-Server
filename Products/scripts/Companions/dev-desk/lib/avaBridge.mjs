import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  mimeForFile,
  isImageFile,
  resolveExistingFiles,
} from "./avaMedia.mjs";
import {
  loadConnectionConfig,
  isRemoteCompute,
  operatorHeaders,
  brainOrigin,
} from "./connectionConfig.mjs";
import { beginOllamaWork, endOllamaWork } from "../../core/src/ollamaInflight.mjs";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DISCORD_API = "https://discord.com/api/v10";
const GUILD_ID = "1516108585740800042";

function firstEnv(env, keys) {
  for (const k of keys) {
    const v = env[k] ?? process.env[k];
    if (v != null && String(v).trim()) return String(v).trim();
  }
  return "";
}

function parseEnvFile(filePath) {
  const out = {};
  if (!fs.existsSync(filePath)) return out;
  for (const line of fs.readFileSync(filePath, "utf8").split(/\r?\n/)) {
    if (!line || line.trim().startsWith("#")) continue;
    const i = line.indexOf("=");
    if (i < 0) continue;
    const k = line.slice(0, i).trim();
    let v = line.slice(i + 1).trim();
    if (
      (v.startsWith('"') && v.endsWith('"')) ||
      (v.startsWith("'") && v.endsWith("'"))
    ) {
      v = v.slice(1, -1);
    }
    out[k] = v;
  }
  return out;
}

/** Find RootMC\.env on any drive — prefer EXE/kit drive, then common layouts. */
function discoverEnvCandidates() {
  const out = [];
  const push = (p) => {
    if (p && !out.includes(p)) out.push(p);
  };

  push(process.env.ROOTMC_ENV_FILE);
  push(process.env.AVA_ENV_FILE);
  push(path.join(process.env.HOME || "", "Ava-Core", ".env"));
  push(path.join(process.env.HOME || "", "ava", ".env"));
  if (process.env.ROOTMC_ROOT) {
    push(path.join(process.env.ROOTMC_ROOT, ".env"));
    push(path.join(process.env.ROOTMC_ROOT, "..", ".credentials", ".env"));
  }
  if (process.env.AVA_HANDOFF) {
    push(path.join(process.env.AVA_HANDOFF, ".env"));
  }

  // Packed EXE lives under .../Ava Laptop/AvaIvy/ — walk up for RootMC/.env
  let cur = path.resolve(__dirname, "..");
  for (let i = 0; i < 8; i++) {
    push(path.join(cur, ".env"));
    push(path.join(cur, ".credentials", ".env"));
    const parent = path.dirname(cur);
    if (!parent || parent === cur) break;
    cur = parent;
  }

  const rels = [
    [".1 Work Stations", "RootMC", ".env"],
    [".1 Work Stations", ".credentials", ".env"],
    ["RootMC", ".env"],
  ];
  const letters = "CDEFGHIJKLMNOPQRSTUVWXYZ".split("");
  // Prefer drive of this process / exe resources
  const homeDrive = (process.execPath || process.cwd() || "C:\\").slice(0, 1).toUpperCase();
  const ordered = [homeDrive, ...letters.filter((L) => L !== homeDrive)];
  for (const L of ordered) {
    const root = `${L}:\\`;
    try {
      if (!fs.existsSync(root)) continue;
    } catch {
      continue;
    }
    for (const parts of rels) {
      push(path.join(root, ...parts));
    }
  }

  push(path.resolve(__dirname, "../../../.env"));
  push(path.resolve(__dirname, "../../../../.env"));
  push(path.resolve(__dirname, "../../../.credentials/.env"));
  return out.filter(Boolean);
}

export async function loadDesktopEnv() {
  const candidates = discoverEnvCandidates();
  let fileEnv = {};
  for (const p of candidates) {
    if (fs.existsSync(p)) {
      fileEnv = { ...fileEnv, ...parseEnvFile(p) };
    }
  }
  const discordToken = firstEnv(fileEnv, [
    "AVA_DISCORD_BOT_TOKEN",
    "DISCORD_AVA_BOT_TOKEN",
    "DISCORD_ROOTMC_BOT_TOKEN",
  ]).replace(/^Bot\s+/i, "");
  const slackToken = firstEnv(fileEnv, ["AVA_SLACK_BOT_TOKEN"]).replace(
    /^Bearer\s+/i,
    "",
  );
  const telegramToken = firstEnv(fileEnv, ["AVA_TELEGRAM_BOT_TOKEN"]);
  const operatorChatId = firstEnv(fileEnv, ["AVA_TELEGRAM_OPERATOR_IDS"])
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean)[0] || "6644482344";
  const conn = loadConnectionConfig();
  const brain = brainOrigin(conn);
  const operatorKey =
    conn.operatorKey ||
    firstEnv(fileEnv, [
      "AVA_OPERATOR_KEY",
      "ROOTMC_DEV_WORKSTATION_KEY",
      "AVA_CRON_KEY",
    ]);
  const workstationKey =
    conn.workstationKey ||
    firstEnv(fileEnv, ["ROOTMC_DEV_WORKSTATION_KEY", "ROOTMC_INTERNAL_API_KEY"]);
  return {
    discordToken,
    slackToken,
    telegramToken,
    operatorChatId,
    operatorKey,
    workstationKey,
    brainUrl: brain,
    localApiUrl: conn.localApiUrl,
    rewriteUrl: `${brain}/api/rewrite`,
    ollamaUrl:
      conn.ollamaUrl ||
      firstEnv(fileEnv, ["AVA_OLLAMA_URL", "OLLAMA_HOST"]) ||
      "http://127.0.0.1:11434",
    ollamaModel:
      conn.ollamaModel ||
      firstEnv(fileEnv, ["AVA_OLLAMA_MODEL", "OLLAMA_MODEL"]) ||
      "llama3.2:latest",
    ollamaTimeoutMs:
      Number(firstEnv(fileEnv, ["AVA_CORE_CHAT_TIMEOUT_MS", "AVA_OLLAMA_TIMEOUT_MS"])) ||
      300000,
    ollamaNumThread:
      Number(firstEnv(fileEnv, ["AVA_OLLAMA_NUM_THREAD", "OLLAMA_NUM_THREAD"])) || 6,
    ollamaNumCtx: Math.min(
      8192,
      Math.max(
        2048,
        Number(firstEnv(fileEnv, ["AVA_OLLAMA_NUM_CTX", "OLLAMA_NUM_CTX"])) || 4096,
      ),
    ),
    apiBase:
      conn.apiBase ||
      firstEnv(fileEnv, ["AVA_API_BASE", "ROOTMC_API_BASE"]) ||
      "https://api.rootmc.net",
    connection: conn,
    computeRemote: isRemoteCompute(conn),
  };
}

/** Feedback dual-post targets (locked). */
export const FEEDBACK_TARGETS = {
  discordDevelopment: {
    surface: "discord",
    id: "1545287392552943768",
    label: "Discord #development",
  },
  slackFeedback: {
    surface: "slack",
    id: "C0BLMGBVAMD",
    label: "Slack #feedback",
  },
  slackDevFeed: {
    surface: "slack",
    id: "C0BMCPMDDQR",
    label: "Slack #development-feed",
  },
};

/** Named destinations for manual Post-as-Ava (Discord / Slack / Telegram). */
export const AVA_POST_PRESETS = [
  { key: "general", surface: "discord", id: "1545284354157187083", label: "Discord #general" },
  { key: "admins", surface: "discord", id: "1516121832493678612", label: "Discord #admins" },
  { key: "updates", surface: "discord", id: "1545284423740563528", label: "Discord #updates" },
  { key: "development", surface: "discord", id: "1545287392552943768", label: "Discord #development" },
  { key: "governance", surface: "discord", id: "1522406451413385317", label: "Discord #governance" },
  { key: "voting", surface: "discord", id: "1522413185364398090", label: "Discord #voting" },
  { key: "constitution", surface: "discord", id: "1522406019152478210", label: "Discord #constitution" },
  { key: "proposals", surface: "discord", id: "1526664180491358419", label: "Discord #proposals" },
  { key: "memes", surface: "discord", id: "1545287357618593843", label: "Discord #memes-and-media" },
  { key: "ava-media", surface: "discord", id: "1533268458668687392", label: "Discord Ava media vault" },
  { key: "facts", surface: "discord", id: "1545287379055812638", label: "Discord #random-facts" },
  { key: "solar", surface: "discord", id: "1533915343766949949", label: "Discord #solar-server" },
  { key: "ingame", surface: "discord", id: "1545284399107547179", label: "Discord in-game chat" },
  { key: "daily", surface: "discord", id: "1539779979280257054", label: "Discord Ava home" },
  { key: "economy", surface: "discord", id: "1516804780884889621", label: "Discord #economy" },
  { key: "slack-dev", surface: "slack", id: "C0BMCPMDDQR", label: "Slack #development-feed" },
  { key: "slack-plans", surface: "slack", id: "C0BM4P3GVDX", label: "Slack #new-plugin-development-plans" },
  { key: "slack-feedback", surface: "slack", id: "C0BLMGBVAMD", label: "Slack #feedback" },
  { key: "alex", surface: "telegram", id: "6644482344", label: "Telegram DM Alex (@WildEcho94)" },
];

export function listPostPresets() {
  const presets = [...AVA_POST_PRESETS];
  try {
    const handoff = process.env.AVA_HANDOFF || path.join(process.env.HOME || "", "Ava-Core");
    const st = JSON.parse(
      fs.readFileSync(path.join(handoff, "data", "slack-solar-feed.json"), "utf8"),
    );
    if (st?.id && !presets.some((p) => p.id === st.id)) {
      presets.splice(
        presets.findIndex((p) => p.key === "slack-feedback") + 1 || presets.length,
        0,
        {
          key: "slack-solar-feed",
          surface: "slack",
          id: st.id,
          label: "Slack #solar-feed",
        },
      );
    }
  } catch {
    /* optional until channel exists */
  }
  return { ok: true, presets };
}

export async function listDiscordTextChannels(env) {
  if (!env.discordToken) return { ok: false, detail: "missing_discord_token", channels: [] };
  const res = await fetch(`${DISCORD_API}/guilds/${GUILD_ID}/channels`, {
    headers: { Authorization: `Bot ${env.discordToken}` },
  });
  const data = await res.json();
  if (!res.ok) return { ok: false, detail: data?.message || res.status, channels: [] };
  const channels = (Array.isArray(data) ? data : [])
    .filter((c) => c.type === 0 || c.type === 5)
    .map((c) => ({
      id: c.id,
      name: c.name,
      kind: c.type === 5 ? "announcement" : "guild",
      nsfw: Boolean(c.nsfw),
    }))
    .sort((a, b) => a.name.localeCompare(b.name));
  return { ok: true, channels };
}

/** Discord DM + group DM channels Ava shares. */
export async function listDiscordPrivateChannels(env) {
  if (!env.discordToken) return { ok: false, detail: "missing_discord_token", channels: [] };
  const res = await fetch(`${DISCORD_API}/users/@me/channels`, {
    headers: { Authorization: `Bot ${env.discordToken}` },
  });
  const data = await res.json();
  if (!res.ok) return { ok: false, detail: data?.message || res.status, channels: [] };
  const channels = (Array.isArray(data) ? data : [])
    .map((c) => {
      const recipients = Array.isArray(c.recipients) ? c.recipients : [];
      const names = recipients
        .map((u) => u.global_name || u.username || u.id)
        .filter(Boolean);
      const label =
        c.type === 3
          ? `group · ${names.slice(0, 3).join(", ") || c.id}`
          : `dm · ${names[0] || c.id}`;
      return {
        id: c.id,
        name: label,
        kind: c.type === 3 ? "group_dm" : "dm",
        recipients: names,
      };
    })
    .sort((a, b) => a.name.localeCompare(b.name));
  return { ok: true, channels };
}

export async function listSlackChannels(env) {
  if (!env.slackToken) return { ok: false, detail: "missing_slack_token", channels: [] };
  const channels = [];
  let cursor = "";
  do {
    const qs = new URLSearchParams({
      types: "public_channel,private_channel",
      exclude_archived: "true",
      limit: "200",
    });
    if (cursor) qs.set("cursor", cursor);
    const res = await fetch(`https://slack.com/api/conversations.list?${qs}`, {
      headers: { Authorization: `Bearer ${env.slackToken}` },
    });
    const data = await res.json();
    if (!data.ok) return { ok: false, detail: data.error || "slack_list_failed", channels };
    for (const c of data.channels || []) {
      if (!c.is_member) continue;
      channels.push({
        id: c.id,
        name: c.name || c.id,
        kind: c.is_private ? "private" : "public",
        private: Boolean(c.is_private),
      });
    }
    cursor = data.response_metadata?.next_cursor || "";
  } while (cursor);
  channels.sort((a, b) => a.name.localeCompare(b.name));
  return { ok: true, channels };
}

/** Slack DMs + group DMs the bot is in. */
export async function listSlackDirectMessages(env) {
  if (!env.slackToken) return { ok: false, detail: "missing_slack_token", channels: [] };
  const channels = [];
  let cursor = "";
  do {
    const qs = new URLSearchParams({
      types: "im,mpim",
      exclude_archived: "true",
      limit: "200",
    });
    if (cursor) qs.set("cursor", cursor);
    const res = await fetch(`https://slack.com/api/conversations.list?${qs}`, {
      headers: { Authorization: `Bearer ${env.slackToken}` },
    });
    const data = await res.json();
    if (!data.ok) return { ok: false, detail: data.error || "slack_im_list_failed", channels };
    for (const c of data.channels || []) {
      if (c.is_user_deleted) continue;
      if (c.is_im) {
        channels.push({
          id: c.id,
          name: c.user ? `dm · ${c.user}` : `dm · ${c.id}`,
          kind: "im",
          user: c.user || null,
        });
      } else if (c.is_mpim) {
        channels.push({
          id: c.id,
          name: c.name ? `group · ${c.name}` : `group · ${c.id}`,
          kind: "mpim",
        });
      }
    }
    cursor = data.response_metadata?.next_cursor || "";
  } while (cursor);

  const userIds = [...new Set(channels.map((c) => c.user).filter(Boolean))];
  if (userIds.length) {
    try {
      const res = await fetch("https://slack.com/api/users.list?limit=200", {
        headers: { Authorization: `Bearer ${env.slackToken}` },
      });
      const data = await res.json();
      if (data.ok) {
        const byId = new Map(
          (data.members || []).map((u) => [
            u.id,
            u.profile?.display_name || u.real_name || u.name || u.id,
          ]),
        );
        for (const c of channels) {
          if (c.user && byId.has(c.user)) c.name = `dm · ${byId.get(c.user)}`;
        }
      }
    } catch {
      /* keep ids */
    }
  }
  channels.sort((a, b) => a.name.localeCompare(b.name));
  return { ok: true, channels };
}

function sleepMs(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

/**
 * Every known destination Ava can post to: Discord guild + DMs,
 * Slack channels + DMs, Telegram known chats, plus Post presets.
 */
export async function listAllPostTargets(env) {
  const targets = [];
  const seen = new Set();
  const add = (surface, id, label, kind) => {
    const sid = String(id || "").trim();
    if (!sid) return;
    const key = `${surface}:${sid}`;
    if (seen.has(key)) return;
    seen.add(key);
    targets.push({
      surface,
      id: sid,
      label: label || `${surface} · ${sid}`,
      kind: kind || "known",
    });
  };

  const [guild, priv, slack, slackDm, tg] = await Promise.all([
    listDiscordTextChannels(env).catch(() => ({ channels: [] })),
    listDiscordPrivateChannels(env).catch(() => ({ channels: [] })),
    listSlackChannels(env).catch(() => ({ channels: [] })),
    listSlackDirectMessages(env).catch(() => ({ channels: [] })),
    listTelegramChats(env).catch(() => ({ channels: [] })),
  ]);

  for (const c of guild.channels || []) {
    add("discord", c.id, `Discord #${c.name}`, c.kind || "guild");
  }
  for (const c of priv.channels || []) {
    add("discord", c.id, `Discord ${c.name}`, c.kind || "dm");
  }
  for (const c of slack.channels || []) {
    add("slack", c.id, `Slack #${c.name}`, c.kind || "public");
  }
  for (const c of slackDm.channels || []) {
    add("slack", c.id, `Slack ${c.name}`, c.kind || "im");
  }
  for (const c of tg.channels || []) {
    add("telegram", c.id, `Telegram ${c.name}`, c.kind || "known");
  }
  for (const p of AVA_POST_PRESETS) {
    add(p.surface, p.id, p.label, "preset");
  }

  const counts = {
    discord: targets.filter((t) => t.surface === "discord" && t.kind !== "dm" && t.kind !== "group_dm").length,
    discordDm: targets.filter((t) => t.surface === "discord" && (t.kind === "dm" || t.kind === "group_dm")).length,
    slack: targets.filter((t) => t.surface === "slack" && t.kind !== "im" && t.kind !== "mpim").length,
    slackDm: targets.filter((t) => t.surface === "slack" && (t.kind === "im" || t.kind === "mpim")).length,
    telegram: targets.filter((t) => t.surface === "telegram").length,
    total: targets.length,
  };
  return { ok: true, targets, counts };
}

/**
 * Post one message to every known DM + channel.
 * Rewrites once (if requested), then sends the same text everywhere.
 */
export async function postToAllPages(env, opts = {}, onProgress = null) {
  const listed = await listAllPostTargets(env);
  const targets = listed.targets || [];
  let text = String(opts.text || "").trim();
  const filePaths = resolveExistingFiles(opts.filePaths || opts.attachments || [], {
    max: 10,
  });
  if (!text && !filePaths.length) {
    return { ok: false, detail: "empty_text", posted: 0, failed: 0, results: [], counts: listed.counts };
  }
  if (!targets.length) {
    return { ok: false, detail: "no_targets", posted: 0, failed: 0, results: [], counts: listed.counts };
  }

  let via = "direct";
  let provider = opts.provider || "exact";
  if (opts.rewrite && text && String(provider).toLowerCase() !== "exact") {
    const rewritten = await rewriteDraft(env, {
      text,
      surface: "discord",
      context: [],
      provider,
    });
    text = rewritten.text || text;
    via = rewritten.via || "rewrite";
    provider = rewritten.provider || provider;
  } else {
    provider = "exact";
  }

  const results = [];
  for (let i = 0; i < targets.length; i++) {
    const dest = targets[i];
    if (typeof onProgress === "function") {
      try {
        onProgress({
          i: i + 1,
          total: targets.length,
          label: dest.label,
          surface: dest.surface,
          channelId: dest.id,
        });
      } catch {
        /* ignore */
      }
    }
    try {
      const r = await postAsAva(env, {
        surface: dest.surface,
        channelId: dest.id,
        text,
        rewrite: false,
        provider: "exact",
        filePaths,
      });
      results.push({
        ok: true,
        label: dest.label,
        surface: dest.surface,
        channelId: dest.id,
        kind: dest.kind,
        id: r.id || null,
      });
    } catch (err) {
      results.push({
        ok: false,
        label: dest.label,
        surface: dest.surface,
        channelId: dest.id,
        kind: dest.kind,
        detail: err?.message || String(err),
      });
    }
    await sleepMs(400);
  }

  const okCount = results.filter((r) => r.ok).length;
  return {
    ok: okCount > 0,
    posted: okCount,
    failed: results.length - okCount,
    total: targets.length,
    text,
    via,
    provider,
    counts: listed.counts,
    results,
  };
}

async function slackAuthIdentity(env) {
  if (!env.slackToken) return { botId: null, userId: null };
  try {
    const res = await fetch("https://slack.com/api/auth.test", {
      headers: { Authorization: `Bearer ${env.slackToken}` },
    });
    const data = await res.json();
    if (!data.ok) return { botId: null, userId: null };
    return {
      botId: data.bot_id ? String(data.bot_id) : null,
      userId: data.user_id ? String(data.user_id) : null,
    };
  } catch {
    return { botId: null, userId: null };
  }
}

export async function fetchSlackHistory(env, channelId, limit = 42) {
  if (!env.slackToken || !channelId) {
    return { ok: false, messages: [], detail: "missing_token_or_channel" };
  }
  const me = await slackAuthIdentity(env);
  const qs = new URLSearchParams({
    channel: String(channelId),
    limit: String(Math.min(100, limit)),
  });
  const res = await fetch(`https://slack.com/api/conversations.history?${qs}`, {
    headers: { Authorization: `Bearer ${env.slackToken}` },
  });
  const data = await res.json();
  if (!data.ok) return { ok: false, messages: [], detail: data.error || "slack_history_failed" };
  const messages = (Array.isArray(data.messages) ? data.messages : [])
    .reverse()
    .slice(-limit)
    .map((m) => {
      const self =
        Boolean(m.bot_id && me.botId && String(m.bot_id) === me.botId) ||
        Boolean(m.user && me.userId && String(m.user) === me.userId);
      return {
        who: m.username || m.user || (m.bot_id ? "bot" : "?"),
        text: m.text || "",
        id: m.ts,
        self,
      };
    });
  return {
    ok: true,
    messages,
    botId: me.botId,
    botUserId: me.userId,
  };
}

export async function deleteSlackMessage(env, channelId, messageTs) {
  if (!env.slackToken) return { ok: false, detail: "missing_slack_token" };
  if (!channelId || !messageTs) return { ok: false, detail: "missing_channel_or_ts" };
  const res = await fetch("https://slack.com/api/chat.delete", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${env.slackToken}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      channel: String(channelId),
      ts: String(messageTs),
    }),
  });
  const data = await res.json().catch(() => ({}));
  if (!data.ok) {
    return { ok: false, detail: data.error || `slack_delete_${res.status}` };
  }
  return { ok: true, channelId: String(channelId), ts: String(messageTs) };
}

/**
 * Delete Ava's own messages from a Discord channel (paginated, capped).
 */
export async function clearDiscordOwnMessages(env, channelId, { maxDelete = 80 } = {}) {
  if (!env.discordToken || !channelId) {
    return { ok: false, deleted: 0, detail: "missing_token_or_channel" };
  }
  const me = await discordBotUser(env);
  const botId = me?.id ? String(me.id) : null;
  if (!botId) return { ok: false, deleted: 0, detail: "missing_bot_identity" };

  let deleted = 0;
  let failed = 0;
  let before = null;
  for (let p = 0; p < 8 && deleted < maxDelete; p++) {
    const qs = new URLSearchParams({ limit: "100" });
    if (before) qs.set("before", before);
    const res = await fetch(`${DISCORD_API}/channels/${channelId}/messages?${qs}`, {
      headers: { Authorization: `Bot ${env.discordToken}` },
    });
    if (!res.ok) break;
    const batch = await res.json();
    if (!Array.isArray(batch) || !batch.length) break;
    before = batch[batch.length - 1]?.id || null;
    for (const m of batch) {
      if (deleted >= maxDelete) break;
      if (String(m.author?.id || "") !== botId) continue;
      const del = await deleteDiscordMessage(env, channelId, m.id);
      if (del.ok) deleted += 1;
      else failed += 1;
      await new Promise((r) => setTimeout(r, 280));
    }
    if (batch.length < 100) break;
  }
  return { ok: true, deleted, failed, channelId: String(channelId) };
}

/**
 * Delete Ava's own messages from a Slack channel (paginated, capped).
 */
export async function clearSlackOwnMessages(env, channelId, { maxDelete = 120 } = {}) {
  if (!env.slackToken || !channelId) {
    return { ok: false, deleted: 0, detail: "missing_token_or_channel" };
  }
  const me = await slackAuthIdentity(env);
  let deleted = 0;
  let failed = 0;
  let cursor = undefined;
  for (let p = 0; p < 10 && deleted < maxDelete; p++) {
    const qs = new URLSearchParams({
      channel: String(channelId),
      limit: "100",
    });
    if (cursor) qs.set("cursor", cursor);
    const res = await fetch(`https://slack.com/api/conversations.history?${qs}`, {
      headers: { Authorization: `Bearer ${env.slackToken}` },
    });
    const data = await res.json();
    if (!data.ok) break;
    const batch = Array.isArray(data.messages) ? data.messages : [];
    for (const m of batch) {
      if (deleted >= maxDelete) break;
      const self =
        Boolean(m.bot_id && me.botId && String(m.bot_id) === me.botId) ||
        Boolean(m.user && me.userId && String(m.user) === me.userId);
      if (!self) continue;
      const del = await deleteSlackMessage(env, channelId, m.ts);
      if (del.ok) deleted += 1;
      else failed += 1;
      await new Promise((r) => setTimeout(r, 200));
    }
    cursor = data.response_metadata?.next_cursor || "";
    if (!cursor || !batch.length) break;
  }
  return { ok: true, deleted, failed, channelId: String(channelId) };
}

/**
 * Clear Ava feedback channel messages, then dual-post the processed stamp.
 */
export async function clearAllFeedbackAndStamp(env, opts = {}) {
  const started = Date.now();
  const clearDiscord = opts.clearDiscord !== false;
  const clearSlack = opts.clearSlack !== false;
  const alsoDevFeed = Boolean(opts.alsoDevFeed);
  const results = { discord: null, slack: null, stamp: null };

  if (clearDiscord) {
    results.discord = await clearDiscordOwnMessages(env, FEEDBACK_TARGETS.discordDevelopment.id, {
      maxDelete: Number(opts.maxDelete) || 80,
    });
  }
  if (clearSlack) {
    results.slack = await clearSlackOwnMessages(env, FEEDBACK_TARGETS.slackFeedback.id, {
      maxDelete: Number(opts.maxDelete) || 120,
    });
  }

  const elapsedSec = Math.max(0, Math.round((Date.now() - started) / 1000));
  const when = new Date().toLocaleString(undefined, {
    weekday: "short",
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
    second: "2-digit",
  });
  const stampText = `Feedback was fully processed on ${when} ${elapsedSec} Seconds ago`;
  results.stamp = await dualPostFeedback(env, {
    text: stampText,
    rewrite: false,
    provider: "exact",
    includeDevFeed: alsoDevFeed,
  });
  results.ok = Boolean(results.stamp?.ok);
  results.text = stampText;
  results.elapsedSec = elapsedSec;
  return results;
}

/** Telegram operator + known private/group chats from local buffers + logs. */
export async function listTelegramChats(env) {
  const chats = [];
  const seen = new Set();
  const add = (id, name, kind) => {
    const cid = normalizeTgChatId(id);
    if (!cid || cid === "undefined" || cid === "null" || seen.has(cid)) return;
    seen.add(cid);
    chats.push({ id: cid, name: name || `chat · ${cid}`, kind: kind || "known" });
  };

  const op = String(env.operatorChatId || "").trim();
  if (op) add(op, `dm · operator (${op})`, "private");

  const bufPath = path.resolve(__dirname, "../data/telegram-context.json");
  try {
    if (fs.existsSync(bufPath)) {
      const raw = JSON.parse(fs.readFileSync(bufPath, "utf8"));
      for (const id of Object.keys(raw || {})) add(id, `chat · ${id}`, "known");
    }
  } catch {
    /* ignore */
  }

  const groupsDir = path.join(handoffRoot(), "data", "telegram", "groups");
  try {
    if (fs.existsSync(groupsDir)) {
      for (const name of fs.readdirSync(groupsDir)) add(name, `group · ${name}`, "group");
    }
  } catch {
    /* ignore */
  }

  // Discover more chats from recent logs
  const logDir = path.join(handoffRoot(), "data", "logs");
  for (const file of ["inbound.jsonl", "outbound.jsonl"]) {
    for (const line of readJsonlTail(path.join(logDir, file), 2500)) {
      try {
        const j = JSON.parse(line);
        if (String(j.surface || "").toLowerCase() !== "telegram") continue;
        const cid = normalizeTgChatId(j.channelId);
        if (!cid) continue;
        const label =
          j.isDm || String(j.channelId || "").includes(cid)
            ? `dm · ${j.authorName || cid}`
            : `chat · ${cid}`;
        add(cid, label, j.isDm ? "private" : "known");
      } catch {
        /* ignore */
      }
    }
  }

  return { ok: true, channels: chats };
}

export async function fetchDiscordHistory(env, channelId, limit = 42) {
  if (!env.discordToken || !channelId) {
    return { ok: false, messages: [], detail: "missing_token_or_channel" };
  }
  const me = await discordBotUser(env);
  const res = await fetch(
    `${DISCORD_API}/channels/${channelId}/messages?limit=${Math.min(100, limit)}`,
    { headers: { Authorization: `Bot ${env.discordToken}` } },
  );
  const data = await res.json();
  if (!res.ok) return { ok: false, messages: [], detail: data?.message || res.status };
  const messages = (Array.isArray(data) ? data : [])
    .reverse()
    .slice(-limit)
    .map((m) => {
      const authorId = m.author?.id ? String(m.author.id) : "";
      const self = Boolean(me?.id && authorId && me.id === authorId);
      return {
        who: m.author?.username || m.author?.id || "?",
        text: m.content || "",
        id: m.id,
        authorId,
        self,
        bot: Boolean(m.author?.bot),
      };
    });
  return { ok: true, messages, botId: me?.id || null, botName: me?.username || null };
}

let _discordBotUser = null;
let _discordBotUserAt = 0;

export async function discordBotUser(env) {
  if (!env.discordToken) return null;
  if (_discordBotUser && Date.now() - _discordBotUserAt < 10 * 60_000) {
    return _discordBotUser;
  }
  try {
    const res = await fetch(`${DISCORD_API}/users/@me`, {
      headers: { Authorization: `Bot ${env.discordToken}` },
    });
    const data = await res.json().catch(() => null);
    if (!res.ok || !data?.id) return _discordBotUser;
    _discordBotUser = {
      id: String(data.id),
      username: String(data.username || "Ava"),
    };
    _discordBotUserAt = Date.now();
    return _discordBotUser;
  } catch {
    return _discordBotUser;
  }
}

export async function sendDiscordMessage(env, channelId, content, refId = null) {
  if (!env.discordToken) throw new Error("missing_discord_token");
  const body = { content: String(content).slice(0, 1900) };
  if (refId) {
    body.message_reference = { message_id: String(refId) };
  }
  const res = await fetch(`${DISCORD_API}/channels/${channelId}/messages`, {
    method: "POST",
    headers: {
      Authorization: `Bot ${env.discordToken}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data?.message || `discord_${res.status}`);
  return data;
}

/**
 * Discord message with local file attachments (multipart).
 */
export async function sendDiscordMessageWithFiles(
  env,
  channelId,
  content,
  filePaths = [],
  refId = null,
) {
  if (!env.discordToken) throw new Error("missing_discord_token");
  const files = resolveExistingFiles(filePaths, { max: 10 });
  if (!files.length) {
    return sendDiscordMessage(env, channelId, content, refId);
  }
  const form = new FormData();
  const payload = {
    content: String(content || "").slice(0, 2000),
    allowed_mentions: { parse: [] },
    attachments: files.map((p, i) => ({
      id: i,
      filename: path.basename(p),
    })),
  };
  if (refId) {
    payload.message_reference = { message_id: String(refId) };
  }
  form.append("payload_json", JSON.stringify(payload));
  for (let i = 0; i < files.length; i++) {
    const buf = fs.readFileSync(files[i]);
    const name = path.basename(files[i]);
    form.append(
      `files[${i}]`,
      new Blob([buf], { type: mimeForFile(files[i]) }),
      name,
    );
  }
  const res = await fetch(`${DISCORD_API}/channels/${channelId}/messages`, {
    method: "POST",
    headers: {
      Authorization: `Bot ${env.discordToken}`,
      "User-Agent": "AvaIvyRootMC (rootmc.net, 0.5)",
    },
    body: form,
  });
  const text = await res.text();
  if (!res.ok) {
    throw new Error(`discord_files_${res.status}: ${text.slice(0, 280)}`);
  }
  return text ? JSON.parse(text) : { ok: true, files: files.length };
}

/** Edit a message Ava posted (bots can only edit their own). */
export async function editDiscordMessage(env, channelId, messageId, content) {
  if (!env.discordToken) return { ok: false, detail: "missing_discord_token" };
  const cid = String(channelId || "").trim();
  const mid = String(messageId || "").trim();
  const text = String(content || "").trim();
  if (!cid || !mid || !text) {
    return { ok: false, detail: "need_channel_message_and_text" };
  }
  const res = await fetch(
    `${DISCORD_API}/channels/${cid}/messages/${mid}`,
    {
      method: "PATCH",
      headers: {
        Authorization: `Bot ${env.discordToken}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ content: text.slice(0, 1900) }),
    },
  );
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    return {
      ok: false,
      detail: data?.message || `discord_${res.status}`,
      status: res.status,
    };
  }
  return {
    ok: true,
    id: data.id || mid,
    text: data.content || text,
    channelId: cid,
  };
}

/**
 * Delete a Discord message.
 * Own messages always; others require Manage Messages.
 */
export async function deleteDiscordMessage(env, channelId, messageId) {
  if (!env.discordToken) return { ok: false, detail: "missing_discord_token" };
  const cid = String(channelId || "").trim();
  const mid = String(messageId || "").trim();
  if (!cid || !mid) return { ok: false, detail: "need_channel_and_message" };
  const res = await fetch(
    `${DISCORD_API}/channels/${cid}/messages/${mid}`,
    {
      method: "DELETE",
      headers: { Authorization: `Bot ${env.discordToken}` },
    },
  );
  if (res.status === 204 || res.ok) {
    return { ok: true, id: mid, channelId: cid, deleted: true };
  }
  const data = await res.json().catch(() => ({}));
  return {
    ok: false,
    detail: data?.message || `discord_${res.status}`,
    status: res.status,
  };
}

export async function sendSlackMessage(env, channelId, content, threadTs = null) {
  if (!env.slackToken) throw new Error("missing_slack_token");
  const payload = {
    channel: String(channelId),
    text: String(content).slice(0, 3900),
  };
  if (threadTs) payload.thread_ts = String(threadTs);
  const res = await fetch("https://slack.com/api/chat.postMessage", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${env.slackToken}`,
      "Content-Type": "application/json; charset=utf-8",
    },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (!data.ok) throw new Error(data.error || "slack_send_failed");
  return data;
}

/**
 * Slack file upload (external upload API) + optional caption as initial comment.
 */
export async function sendSlackMessageWithFiles(
  env,
  channelId,
  content,
  filePaths = [],
  threadTs = null,
) {
  if (!env.slackToken) throw new Error("missing_slack_token");
  const files = resolveExistingFiles(filePaths, { max: 10 });
  if (!files.length) {
    return sendSlackMessage(env, channelId, content, threadTs);
  }

  const uploaded = [];
  for (const abs of files) {
    const filename = path.basename(abs);
    const buf = fs.readFileSync(abs);
    const length = buf.byteLength;
    const getUrl = await fetch("https://slack.com/api/files.getUploadURLExternal", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${env.slackToken}`,
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: new URLSearchParams({
        filename,
        length: String(length),
      }),
    });
    const urlData = await getUrl.json();
    if (!urlData.ok) {
      throw new Error(urlData.error || "slack_get_upload_url_failed");
    }
    const put = await fetch(urlData.upload_url, {
      method: "POST",
      headers: { "Content-Type": mimeForFile(abs) },
      body: buf,
    });
    if (!put.ok) {
      throw new Error(`slack_upload_put_${put.status}`);
    }
    uploaded.push({ id: urlData.file_id, title: filename });
  }

  const complete = await fetch("https://slack.com/api/files.completeUploadExternal", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${env.slackToken}`,
      "Content-Type": "application/json; charset=utf-8",
    },
    body: JSON.stringify({
      files: uploaded,
      channel_id: String(channelId),
      initial_comment: String(content || "").slice(0, 3000) || undefined,
      thread_ts: threadTs ? String(threadTs) : undefined,
    }),
  });
  const done = await complete.json();
  if (!done.ok) throw new Error(done.error || "slack_complete_upload_failed");
  return {
    ok: true,
    ts: done.files?.[0]?.timestamp || done.files?.[0]?.created || null,
    files: done.files || uploaded,
  };
}

function handoffRoot() {
  return process.env.AVA_HANDOFF || path.join(process.env.HOME || "", "Ava-Core");
}

function normalizeTgChatId(chatId) {
  const raw = String(chatId || "").trim();
  if (!raw) return "";
  return raw.startsWith("tg:") ? raw.slice(3) : raw;
}

function tgChannelMatches(channelId, chatId) {
  const want = normalizeTgChatId(chatId);
  const got = String(channelId || "").trim();
  if (!want || !got) return false;
  return got === want || got === `tg:${want}` || got.endsWith(`:${want}`);
}

function readJsonlTail(filePath, maxLines = 4000) {
  if (!fs.existsSync(filePath)) return [];
  try {
    const raw = fs.readFileSync(filePath, "utf8");
    const lines = raw.split(/\r?\n/).filter(Boolean);
    return lines.slice(-maxLines);
  } catch {
    return [];
  }
}

/** Merge Ava flight-recorder logs + local desktop buffer for Telegram history. */
export async function fetchTelegramHistory(env, chatId, limit = 42) {
  const id = normalizeTgChatId(chatId || env.operatorChatId);
  if (!id) return { ok: true, messages: [], detail: "missing_chat_id" };

  const byKey = new Map();
  const pushMsg = (m) => {
    const text = String(m.text || "").trim();
    if (!text) return;
    const mid = m.id != null ? String(m.id) : "";
    const key = mid || `${m.at || 0}:${m.who}:${text.slice(0, 48)}`;
    const prev = byKey.get(key);
    if (!prev || Number(m.at || 0) >= Number(prev.at || 0)) {
      byKey.set(key, {
        who: m.who || "?",
        text,
        id: mid || null,
        at: Number(m.at || 0) || 0,
      });
    }
  };

  // 1) Desktop ring buffer
  const bufPath = path.resolve(__dirname, "../data/telegram-context.json");
  try {
    if (fs.existsSync(bufPath)) {
      const raw = JSON.parse(fs.readFileSync(bufPath, "utf8"));
      for (const m of Array.isArray(raw[id]) ? raw[id] : []) {
        pushMsg({
          who: m.who || "?",
          text: m.text || "",
          id: m.id || null,
          at: m.at || 0,
        });
      }
    }
  } catch {
    /* ignore */
  }

  // 2) Inbound / outbound action logs
  const logDir = path.join(handoffRoot(), "data", "logs");
  for (const line of readJsonlTail(path.join(logDir, "inbound.jsonl"))) {
    try {
      const j = JSON.parse(line);
      if (String(j.surface || "").toLowerCase() !== "telegram") continue;
      if (!tgChannelMatches(j.channelId, id)) continue;
      pushMsg({
        who: j.authorName || j.authorId || "user",
        text: j.content || "",
        id: j.messageId || null,
        at: j.at || 0,
      });
    } catch {
      /* ignore */
    }
  }
  for (const line of readJsonlTail(path.join(logDir, "outbound.jsonl"))) {
    try {
      const j = JSON.parse(line);
      if (String(j.surface || "").toLowerCase() !== "telegram") continue;
      if (!tgChannelMatches(j.channelId, id)) continue;
      if (j.ok === false) continue;
      pushMsg({
        who: "Ava",
        text: j.content || "",
        id: j.messageId || null,
        at: j.at || 0,
      });
    } catch {
      /* ignore */
    }
  }

  // 3) Conversation turns (Q/A pairs)
  const turnsPath = path.join(handoffRoot(), "data", "conversations", "turns.jsonl");
  for (const line of readJsonlTail(turnsPath, 6000)) {
    try {
      const j = JSON.parse(line);
      if (!tgChannelMatches(j.channelId, id)) continue;
      if (j.question) {
        pushMsg({
          who: j.authorName || j.authorId || "user",
          text: j.question,
          id: j.messageId || null,
          at: j.at || 0,
        });
      }
      if (j.answer) {
        pushMsg({
          who: "Ava",
          text: j.answer,
          id: j.messageId ? `a:${j.messageId}` : null,
          at: (j.at || 0) + 1,
        });
      }
    } catch {
      /* ignore */
    }
  }

  const messages = [...byKey.values()]
    .sort((a, b) => (a.at || 0) - (b.at || 0))
    .slice(-Math.min(100, Math.max(1, limit)))
    .map(({ who, text, id: mid }) => ({ who, text, id: mid }));

  return {
    ok: true,
    messages,
    detail: messages.length ? `merged_${messages.length}` : "no_local_history",
  };
}

function pushTelegramContext(chatId, who, text, id = null) {
  const bufPath = path.resolve(__dirname, "../data/telegram-context.json");
  fs.mkdirSync(path.dirname(bufPath), { recursive: true });
  let raw = {};
  try {
    raw = JSON.parse(fs.readFileSync(bufPath, "utf8"));
  } catch {
    raw = {};
  }
  const key = String(chatId);
  const list = Array.isArray(raw[key]) ? raw[key] : [];
  list.push({ who, text, at: Date.now(), id: id ? String(id) : null });
  raw[key] = list.slice(-80);
  fs.writeFileSync(bufPath, JSON.stringify(raw, null, 2), "utf8");
}

export async function sendTelegramMessage(env, chatId, content, replyToMessageId = null) {
  if (!env.telegramToken) throw new Error("missing_telegram_token");
  const payload = {
    chat_id: chatId,
    text: String(content).slice(0, 4000),
    disable_web_page_preview: true,
  };
  if (replyToMessageId) {
    payload.reply_to_message_id = Number(replyToMessageId) || replyToMessageId;
  }
  const res = await fetch(
    `https://api.telegram.org/bot${env.telegramToken}/sendMessage`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    },
  );
  const data = await res.json();
  if (!data.ok) throw new Error(data.description || "telegram_send_failed");
  pushTelegramContext(chatId, "Ava", content, data.result?.message_id || null);
  return data.result;
}

/**
 * Telegram photo/document upload. First file carries caption; rest follow.
 */
export async function sendTelegramMessageWithFiles(
  env,
  chatId,
  content,
  filePaths = [],
  replyToMessageId = null,
) {
  if (!env.telegramToken) throw new Error("missing_telegram_token");
  const files = resolveExistingFiles(filePaths, { max: 10 });
  if (!files.length) {
    return sendTelegramMessage(env, chatId, content, replyToMessageId);
  }

  let last = null;
  for (let i = 0; i < files.length; i++) {
    const abs = files[i];
    const caption = i === 0 ? String(content || "").slice(0, 1024) : "";
    const form = new FormData();
    form.append("chat_id", String(chatId));
    if (caption) form.append("caption", caption);
    if (replyToMessageId && i === 0) {
      form.append("reply_to_message_id", String(Number(replyToMessageId) || replyToMessageId));
    }
    const field = isImageFile(abs) ? "photo" : "document";
    const endpoint = isImageFile(abs) ? "sendPhoto" : "sendDocument";
    form.append(
      field,
      new Blob([fs.readFileSync(abs)], { type: mimeForFile(abs) }),
      path.basename(abs),
    );
    const res = await fetch(
      `https://api.telegram.org/bot${env.telegramToken}/${endpoint}`,
      { method: "POST", body: form },
    );
    const data = await res.json().catch(() => ({}));
    if (!res.ok || data.ok === false) {
      throw new Error(data.description || `telegram_${endpoint}_failed`);
    }
    last = data.result;
  }
  pushTelegramContext(
    chatId,
    "Ava",
    content || `(${files.length} attachment${files.length === 1 ? "" : "s"})`,
    last?.message_id || null,
  );
  return last;
}

/**
 * Post as Ava on any surface.
 * @param {{ surface: string, channelId: string, text?: string, refId?: string, rewrite?: boolean, provider?: string, filePaths?: string[] }} opts
 */
export async function postAsAva(env, opts = {}) {
  const surface = String(opts.surface || "").toLowerCase();
  const channelId = String(opts.channelId || "").trim();
  const refId = opts.refId ? String(opts.refId).trim() : "";
  const filePaths = resolveExistingFiles(opts.filePaths || opts.attachments || [], {
    max: 10,
  });
  let text = String(opts.text || "").trim();
  if (!surface || !channelId) {
    throw new Error("surface and channelId are required");
  }
  if (!text && !filePaths.length) {
    throw new Error("text or file attachment required");
  }

  let via = "direct";
  let provider = opts.provider || "exact";
  if (opts.rewrite && text) {
    let context = [];
    try {
      if (surface === "discord") {
        const hist = await fetchDiscordHistory(env, channelId, 20);
        context = hist.messages || [];
      } else if (surface === "telegram") {
        const hist = await fetchTelegramHistory(env, channelId, 20);
        context = hist.messages || [];
      } else if (surface === "slack") {
        const hist = await fetchSlackHistory(env, channelId, 20);
        context = hist.messages || [];
      }
    } catch {
      context = [];
    }
    const rewritten = await rewriteDraft(env, {
      text,
      surface,
      context,
      provider: opts.provider || "dream",
    });
    text = rewritten.text || text;
    via = rewritten.via || "rewrite";
    provider = rewritten.provider || provider;
  }

  let sent;
  if (surface === "discord") {
    sent = filePaths.length
      ? await sendDiscordMessageWithFiles(env, channelId, text, filePaths, refId || null)
      : await sendDiscordMessage(env, channelId, text, refId || null);
  } else if (surface === "slack") {
    sent = filePaths.length
      ? await sendSlackMessageWithFiles(env, channelId, text, filePaths, refId || null)
      : await sendSlackMessage(env, channelId, text, refId || null);
  } else if (surface === "telegram") {
    const chat = channelId || env.operatorChatId;
    sent = filePaths.length
      ? await sendTelegramMessageWithFiles(env, chat, text, filePaths, refId || null)
      : await sendTelegramMessage(env, chat, text, refId || null);
  } else {
    throw new Error(`unknown_surface_${surface}`);
  }

  return {
    ok: true,
    surface,
    channelId,
    text,
    via,
    provider,
    files: filePaths.length,
    id: sent?.id || sent?.ts || sent?.message_id || null,
    sent,
  };
}

export async function rewriteDraft(
  env,
  { text, surface, context, provider = "dream", compare = false },
) {
  const draft = String(text || "");
  const lightCleanup = () =>
    draft
      .replace(/\b\$\s*(\d+)/g, "$1 Gold")
      .replace(/\bdollars?\b/gi, "Gold")
      .trim() || draft;

  if (String(provider).toLowerCase() === "exact" && !compare) {
    return { ok: true, text: lightCleanup(), via: "exact", provider: "exact" };
  }

  try {
    const ac = new AbortController();
    const timer = setTimeout(() => ac.abort(), compare ? 120000 : 20000);
    let res;
    try {
      res = await fetch(env.rewriteUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...operatorHeaders(env),
        },
        signal: ac.signal,
        body: JSON.stringify({
          text: draft,
          surface,
          context,
          provider,
          compare: Boolean(compare),
          authorId: "desktop",
          authorName: "desktop",
          timeoutMs: compare ? 12000 : 10000,
        }),
      });
    } finally {
      clearTimeout(timer);
    }
    const data = await res.json().catch(() => null);
    if (compare && data?.results) {
      return {
        ok: true,
        compare: true,
        results: data.results,
        via: "compare",
        provider: "all",
      };
    }
    if (data?.text) {
      return {
        ok: true,
        text: data.text,
        via: data.via || "ava-rewrite",
        provider: data.provider || provider,
        detail: data.detail || null,
      };
    }
  } catch (err) {
    if (err?.name === "AbortError") {
      return {
        ok: true,
        text: lightCleanup(),
        via: "timeout-fallback",
        provider,
      };
    }
  }
  return { ok: true, text: lightCleanup(), via: "offline-fallback", provider };
}

export async function summarizeChannel(
  env,
  { surface, channelId, provider = "dream", limit = 80 },
) {
  let hist = { messages: [] };
  if (surface === "discord") hist = await fetchDiscordHistory(env, channelId, limit);
  else if (surface === "slack") hist = await fetchSlackHistory(env, channelId, limit);
  else if (surface === "telegram") {
    hist = await fetchTelegramHistory(env, channelId, limit);
  } else return { ok: false, detail: "unknown_surface" };

  const messages = hist.messages || [];
  if (!messages.length) return { ok: false, detail: "no_messages", messages: [] };

  const summarizeUrl = String(env.rewriteUrl || "").replace(
    /\/api\/rewrite\/?$/,
    "/api/summarize",
  );
  try {
    const res = await fetch(summarizeUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...operatorHeaders(env),
      },
      body: JSON.stringify({
        messages,
        surface,
        provider,
        limit,
        authorId: "desktop",
        authorName: "desktop",
      }),
    });
    const data = await res.json().catch(() => null);
    return {
      ok: Boolean(data?.ok ?? data?.text),
      text: data?.text || "",
      provider: data?.provider || provider,
      via: data?.via || null,
      messageCount: messages.length,
      detail: data?.detail || null,
    };
  } catch (err) {
    return {
      ok: false,
      detail: err?.message || String(err),
      messageCount: messages.length,
    };
  }
}

export async function fetchRewriteProviders(env) {
  const url = String(env.rewriteUrl || "").replace(
    /\/api\/rewrite\/?$/,
    "/api/rewrite-providers",
  );
  try {
    const res = await fetch(url, { headers: operatorHeaders(env) });
    const data = await res.json();
    return { ok: true, providers: data.providers || [] };
  } catch (err) {
    return {
      ok: false,
      detail: err?.message || String(err),
      providers: [
        { id: "exact", label: "Exactly the same" },
        { id: "dream", label: "Dream / Grok" },
        { id: "cursor", label: "Cursor" },
        { id: "ollama", label: "Ollama" },
        { id: "google", label: "Google / Gemini" },
      ],
    };
  }
}

function apiBase(env) {
  return String(env.rewriteUrl || "http://127.0.0.1:8787/api/rewrite").replace(
    /\/api\/rewrite\/?$/,
    "",
  );
}

async function localJson(url, { method = "GET", body, env } = {}) {
  const ac = new AbortController();
  const t = setTimeout(() => ac.abort(), 8000);
  try {
    const res = await fetch(url, {
      method,
      headers: {
        ...(body ? { "Content-Type": "application/json" } : {}),
        ...operatorHeaders(env || {}),
      },
      body: body != null ? JSON.stringify(body) : undefined,
      signal: ac.signal,
    });
    const data = await res.json().catch(() => null);
    if (!res.ok) {
      return {
        ok: false,
        detail: data?.detail || `http_${res.status}`,
        status: res.status,
        ...(data && typeof data === "object" ? data : {}),
      };
    }
    return data && typeof data === "object" ? data : { ok: true, data };
  } catch (err) {
    return {
      ok: false,
      detail: err?.name === "AbortError" ? "timeout" : err?.message || String(err),
    };
  } finally {
    clearTimeout(t);
  }
}

export async function fetchCronStatus(env) {
  return localJson(`${apiBase(env)}/api/crons`, { env });
}

export async function fetchReportsStatus(env) {
  return localJson(`${apiBase(env)}/api/reports`, { env });
}

export async function fetchFinanceSuite(env, { refresh = false } = {}) {
  const q = refresh ? "?refresh=1" : "";
  return localJsonLong(`${apiBase(env)}/api/finance${q}`, {
    env,
    timeoutMs: refresh ? 45000 : 20000,
  });
}

export async function postFinanceSuite(env, body = {}) {
  return localJsonLong(`${apiBase(env)}/api/finance`, {
    method: "POST",
    body,
    env,
    timeoutMs: 60000,
  });
}

export async function fetchBiz(env) {
  return localJsonLong(`${apiBase(env)}/api/biz`, {
    env,
    timeoutMs: 25000,
  });
}

export async function postBiz(env, body = {}) {
  return localJsonLong(`${apiBase(env)}/api/biz`, {
    method: "POST",
    body,
    env,
    timeoutMs: 25000,
  });
}

export async function tickEarlyLoginDesktop(env) {
  return localJsonLong(`${apiBase(env)}/api/early-login`, {
    env,
    timeoutMs: 20000,
  });
}

export async function runCronJob(env, id) {
  const jobId = encodeURIComponent(String(id || "").trim());
  return localJson(`${apiBase(env)}/api/crons/${jobId}/run`, {
    method: "POST",
    body: { id, reason: "desktop" },
    env,
  });
}

export async function configureCron(env, body) {
  return localJson(`${apiBase(env)}/api/cron/config`, {
    method: "POST",
    body: body || {},
    env,
  });
}

async function localJsonLong(url, { method = "GET", body, timeoutMs = 130000, signal, env } = {}) {
  const ac = new AbortController();
  const onAbort = () => ac.abort();
  if (signal) {
    if (signal.aborted) ac.abort();
    else signal.addEventListener("abort", onAbort, { once: true });
  }
  const t = setTimeout(() => ac.abort(), Math.max(8000, Number(timeoutMs) || 130000));
  try {
    const res = await fetch(url, {
      method,
      headers: {
        ...(body ? { "Content-Type": "application/json" } : {}),
        ...operatorHeaders(env || {}),
      },
      body: body != null ? JSON.stringify(body) : undefined,
      signal: ac.signal,
    });
    const data = await res.json().catch(() => null);
    if (!res.ok) {
      return {
        ok: false,
        detail: data?.detail || `http_${res.status}`,
        status: res.status,
        ...(data && typeof data === "object" ? data : {}),
      };
    }
    return data && typeof data === "object" ? data : { ok: true, data };
  } catch (err) {
    return {
      ok: false,
      detail: err?.name === "AbortError" ? "timeout" : err?.message || String(err),
    };
  } finally {
    clearTimeout(t);
    if (signal) signal.removeEventListener("abort", onAbort);
  }
}

function ollamaBase(env) {
  let raw = String(env.ollamaUrl || "http://127.0.0.1:11434").trim();
  if (!raw) raw = "http://127.0.0.1:11434";
  // OLLAMA_HOST is often "127.0.0.1:11434" without a scheme
  if (!/^https?:\/\//i.test(raw)) raw = `http://${raw}`;
  return raw.replace(/\/$/, "");
}

function ollamaModelName(env) {
  return String(env.ollamaModel || "llama3.2:latest").trim() || "llama3.2:latest";
}

const DESK_PERSONA_LOCK = `This is private AVA Desk 1:1 with Alex (your person) on AVA-CORE.
You ARE Ava Ivy. You have a name. Never say you don't have a personal name.
Never identify as a generic large language model or nameless assistant.
Voice: warm, a little giddy, snappy, helpful — glad he's here. Lead-dev who cares.
Public host name: HI Pacific Solar Root Server. Never say laptop.
OUTPUT ONLY the reply text. No "as an AI".`;

function loadDeskPersonaSystem() {
  const home = process.env.AVA_HOME || path.join(process.env.HOME || process.env.USERPROFILE || "", "Ava-Core");
  const candidates = [
    path.join(home, "Media", "public", "documents", "persona", "SYSTEM.txt"),
    path.join(home, "Media", "public", "documents", "persona", "llama-baseline", "SYSTEM.txt"),
  ];
  for (const file of candidates) {
    try {
      if (!fs.existsSync(file)) continue;
      let raw = fs.readFileSync(file, "utf8");
      if (raw.includes("Hard rules:")) raw = raw.split("Hard rules:")[0].trim();
      if (raw.length > 2800) raw = raw.slice(0, 2800);
      return `${DESK_PERSONA_LOCK}\n\n${raw}`.trim();
    } catch {
      /* try next */
    }
  }
  return DESK_PERSONA_LOCK;
}

/** Probe origin persona bridge first. Never report nameless raw Ollama as ready. */
export async function fetchCoreChatStatus(env) {
  const model = ollamaModelName(env);
  let providers = [
    { id: "dream", label: "Dream / Grok" },
    { id: "cursor", label: "Cursor / Root Server" },
    { id: "google", label: "Google / Gemini" },
    { id: "groq", label: "Groq" },
    { id: "cerebras", label: "Cerebras" },
    { id: "sambanova", label: "SambaNova" },
    { id: "openrouter", label: "OpenRouter" },
  ];

  try {
    const viaAva = await localJson(`${apiBase(env)}/api/core-chat/status`, { env });
    if (Array.isArray(viaAva?.providers) && viaAva.providers.length) {
      providers = viaAva.providers.filter((p) => p.id !== "exact");
    }
    if (viaAva?.ok) {
      return {
        ok: true,
        model: viaAva.model || model,
        baseUrl: apiBase(env) || "http://127.0.0.1:8787",
        detail: viaAva.detail || "persona",
        providers,
        direct: false,
        persona: true,
        personaSource: viaAva.personaSource || "",
        via: "origin",
        remote: Boolean(env.computeRemote),
      };
    }
  } catch {
    /* origin down — fall through */
  }

  const base = ollamaBase(env);
  let ok = false;
  let detail = "ollama_down";
  try {
    const res = await fetch(`${base}/api/tags`, {
      signal: AbortSignal.timeout(2500),
    });
    ok = res.ok;
    detail = ok ? "persona-fallback" : `ollama_${res.status}`;
  } catch (err) {
    detail = err?.name === "TimeoutError" ? "ollama_timeout" : err?.message || "ollama_down";
  }

  return {
    ok,
    model,
    baseUrl: base,
    detail,
    providers,
    direct: true,
    persona: true,
    via: "ollama-persona",
  };
}

/**
 * Core chat goes through origin /api/core-chat (persona SYSTEM.txt).
 * Direct Ollama is fallback only, and still injects the system prompt.
 */
export async function coreChat(env, opts = {}) {
  const userText = String(opts.text || "").trim();
  if (!userText) return { ok: false, detail: "empty_text" };

  const originBody = {
    text: userText,
    messages: Array.isArray(opts.messages) ? opts.messages : [],
    sessionId: opts.sessionId || null,
    save: opts.save !== false,
    timeoutMs: opts.timeoutMs || env.ollamaTimeoutMs || 300000,
  };
  const origin = await localJsonLong(`${apiBase(env)}/api/core-chat`, {
    method: "POST",
    body: originBody,
    timeoutMs: Math.max(60000, Number(opts.timeoutMs) || Number(env.ollamaTimeoutMs) || 300000),
    signal: opts.signal,
    env,
  });
  if (origin?.ok && origin.reply) {
    return { ...origin, direct: false, persona: true, via: origin.via || "origin" };
  }
  if (origin && (origin.detail === "ollama_fail" || origin.detail === "ollama_empty")) {
    return { ...origin, persona: true, via: "origin" };
  }

  const { randomUUID } = await import("node:crypto");
  const sid = String(opts.sessionId || "").trim() || randomUUID();
  const model = ollamaModelName(env);
  const base = ollamaBase(env);
  const wait = Math.max(
    60000,
    Number(opts.timeoutMs) || Number(env.ollamaTimeoutMs) || 300000,
  );
  const numThread = Number(env.ollamaNumThread) || 6;
  const prior = Array.isArray(opts.messages) ? opts.messages : [];
  const history = [
    ...prior
      .filter((m) => m && (m.role === "user" || m.role === "assistant"))
      .map((m) => ({
        role: m.role,
        content: String(m.content || "").slice(0, 8000),
      })),
    { role: "user", content: userText },
  ].slice(-12);

  const apiMessages = [
    { role: "system", content: loadDeskPersonaSystem() },
    { role: "user", content: "what's your name?" },
    {
      role: "assistant",
      content:
        "I'm Ava Ivy. Right here with you on the Root Server — not a nameless assistant. What's on your mind?",
    },
    ...history,
  ];

  const started = Date.now();
  const ac = new AbortController();
  const onAbort = () => ac.abort();
  if (opts.signal) {
    if (opts.signal.aborted) ac.abort();
    else opts.signal.addEventListener("abort", onAbort, { once: true });
  }
  const timer = setTimeout(() => ac.abort(), wait);

  let reply = null;
  let detail = null;
  const workId = beginOllamaWork("desktop-core", { model, via: "desktop" });
  try {
    const res = await fetch(`${base}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      signal: ac.signal,
      body: JSON.stringify({
        model,
        stream: false,
        keep_alive: "5m",
        think: false,
        options: {
          temperature: 0.35,
          num_predict: Number(opts.numPredict) || 500,
          num_ctx: Number(opts.numCtx) || Number(env.ollamaNumCtx) || 4096,
          num_thread: numThread,
        },
        messages: apiMessages,
      }),
    });
    const body = await res.text();
    if (!res.ok) {
      detail = `ollama_${res.status}`;
    } else {
      try {
        const data = JSON.parse(body);
        reply = String(data?.message?.content || "").trim();
        if (!reply) detail = "ollama_empty";
      } catch {
        detail = "ollama_bad_json";
      }
    }
  } catch (err) {
    if (err?.name === "AbortError") {
      detail = opts.signal?.aborted ? "cancelled" : "ollama_timeout";
    } else {
      detail = err?.message || "ollama_error";
    }
  } finally {
    endOllamaWork(workId);
    clearTimeout(timer);
    if (opts.signal) opts.signal.removeEventListener("abort", onAbort);
  }

  const ms = Date.now() - started;
  if (!reply) {
    return { ok: false, sessionId: sid, detail: detail || "ollama_fail", model, ms };
  }

  const messages = [...history, { role: "assistant", content: reply }];

  // Best-effort training save (Ava gold endpoint is fast; no re-inference)
  let saved = false;
  if (opts.save !== false) {
    try {
      const saveRes = await localJsonLong(`${apiBase(env)}/api/core-chat/gold`, {
        method: "POST",
        body: {
          question: userText,
          answer: reply,
          sessionId: sid,
          provider: "ollama",
          source: "core-desktop-persona-fallback",
        },
        timeoutMs: 8000,
        env,
      });
      saved = Boolean(saveRes?.ok);
    } catch {
      saved = false;
    }
  }

  // Persist locally if Ava save failed — desktop handoff training file
  if (opts.save !== false && !saved) {
    try {
      const path = await import("node:path");
      const fs = await import("node:fs");
      const os = await import("node:os");
      const handoff =
        process.env.AVA_HANDOFF ||
        path.join(os.homedir(), "Ava-Core");
      const dir = path.join(handoff, "Data", "training");
      fs.mkdirSync(dir, { recursive: true });
      const row = {
        at: Date.now(),
        sessionId: sid,
        kind: "turn",
        model,
        question: userText.slice(0, 4000),
        answer: reply.slice(0, 8000),
        ms,
        source: "core-desktop-persona-fallback",
      };
      fs.appendFileSync(
        path.join(dir, "core-sessions.jsonl"),
        `${JSON.stringify(row)}\n`,
        "utf8",
      );
      saved = true;
    } catch {
      /* ignore */
    }
  }

  return {
    ok: true,
    sessionId: sid,
    reply,
    model,
    ms,
    saved,
    direct: true,
    persona: true,
    via: "ollama-persona",
    messages,
  };
}

export async function coreChatEnhance(env, opts = {}) {
  return localJsonLong(`${apiBase(env)}/api/core-chat/enhance`, {
    method: "POST",
    body: {
      draft: opts.draft || "",
      context: opts.context || [],
      provider: opts.provider || "dream",
      sessionId: opts.sessionId || null,
      save: opts.save !== false,
      timeoutMs: opts.timeoutMs || 45000,
    },
    timeoutMs: 60000,
    signal: opts.signal,
    env,
  });
}

export async function coreChatGold(env, opts = {}) {
  return localJson(`${apiBase(env)}/api/core-chat/gold`, {
    method: "POST",
    body: {
      question: opts.question || "",
      answer: opts.answer || "",
      sessionId: opts.sessionId || null,
      provider: opts.provider || "ollama",
      source: opts.source || "core-desktop",
    },
    env,
  });
}

function feedbackApiBase(env) {
  return String(env.apiBase || "https://api.rootmc.net").replace(/\/$/, "");
}

async function feedbackGovFetch(env, path, { method = "GET", body } = {}) {
  const key = String(env.workstationKey || "").trim();
  if (!key) {
    return {
      ok: false,
      detail: "ROOTMC_DEV_WORKSTATION_KEY missing — cannot talk to feedback inbox",
    };
  }
  try {
    const res = await fetch(`${feedbackApiBase(env)}${path}`, {
      method,
      headers: {
        Accept: "application/json",
        ...(body ? { "Content-Type": "application/json" } : {}),
        "User-Agent": "AvaIvyDesktop/feedback",
        "X-RootMC-Dev-Key": key,
      },
      body: body != null ? JSON.stringify(body) : undefined,
    });
    const text = await res.text();
    let data = null;
    try {
      data = text ? JSON.parse(text) : null;
    } catch {
      data = null;
    }
    if (!res.ok) {
      return {
        ok: false,
        status: res.status,
        detail: data?.detail || text.slice(0, 200) || `http_${res.status}`,
        ...(data && typeof data === "object" ? data : {}),
      };
    }
    return data && typeof data === "object" ? data : { ok: true, data };
  } catch (err) {
    return { ok: false, detail: err?.message || String(err) };
  }
}

export async function listFeedbackQueue(env, { status = "queued", limit = 40 } = {}) {
  const q = new URLSearchParams({
    status: String(status || "queued"),
    limit: String(Math.min(100, Math.max(1, Number(limit) || 40))),
  });
  const data = await feedbackGovFetch(env, `/api/governance/feedback-inbox?${q}`);
  if (!data?.ok && data?.detail) return data;
  const rows = Array.isArray(data?.feedback)
    ? data.feedback
    : Array.isArray(data?.items)
      ? data.items
      : Array.isArray(data)
        ? data
        : [];
  return {
    ok: true,
    status: String(status || "queued"),
    feedback: rows,
    count: rows.length,
    targets: FEEDBACK_TARGETS,
  };
}

export async function processFeedbackNext(env) {
  return feedbackGovFetch(env, `/api/governance/feedback-inbox/process-next`, {
    method: "POST",
    body: {},
  });
}

export async function ackFeedbackItem(env, feedbackId, avaNote = "") {
  const id = String(feedbackId || "").trim();
  if (!id) return { ok: false, detail: "missing_feedback_id" };
  return feedbackGovFetch(
    env,
    `/api/governance/feedback-inbox/${encodeURIComponent(id)}/ack`,
    {
      method: "POST",
      body: { ava_note: String(avaNote || "").slice(0, 500) },
    },
  );
}

/**
 * Post the same Ava message to Discord #development + Slack #feedback
 * (optional Slack #development-feed).
 */
export async function dualPostFeedback(env, opts = {}) {
  const text = String(opts.text || "").trim();
  const filePaths = resolveExistingFiles(opts.filePaths || opts.attachments || [], {
    max: 10,
  });
  if (!text && !filePaths.length) return { ok: false, detail: "empty_text" };

  const rewrite = Boolean(opts.rewrite) && String(opts.provider || "") !== "exact";
  const provider = opts.provider || "exact";
  const includeDevFeed = Boolean(opts.includeDevFeed);
  const destinations = [
    FEEDBACK_TARGETS.discordDevelopment,
    FEEDBACK_TARGETS.slackFeedback,
  ];
  if (includeDevFeed) destinations.push(FEEDBACK_TARGETS.slackDevFeed);

  const results = [];
  for (const dest of destinations) {
    try {
      const r = await postAsAva(env, {
        surface: dest.surface,
        channelId: dest.id,
        text,
        rewrite,
        provider: rewrite ? provider : "exact",
        filePaths,
      });
      results.push({
        ok: true,
        label: dest.label,
        surface: dest.surface,
        channelId: dest.id,
        id: r.id || null,
        via: r.via || null,
        provider: r.provider || provider,
        text: r.text || text,
        files: r.files || 0,
      });
    } catch (err) {
      results.push({
        ok: false,
        label: dest.label,
        surface: dest.surface,
        channelId: dest.id,
        detail: err?.message || String(err),
      });
    }
  }

  const okCount = results.filter((r) => r.ok).length;
  return {
    ok: okCount > 0,
    posted: okCount,
    failed: results.length - okCount,
    results,
    targets: destinations.map((d) => d.label),
  };
}

export function feedbackTemplates() {
  return [
    {
      id: "triage",
      label: "Triage note",
      text: `**Feedback triage** (Ava)\n• Source:\n• Type: bug / feature / ops / other\n• Priority:\n• Next: verify · /proposal · dig · close\n• Note:`,
    },
    {
      id: "ack",
      label: "Player ack",
      text: `heard — logged your \`/feedback\`. if this is a **feature** ask, please use in-game \`/proposal\` (64 G) so it can go to vote. bugs/ops stay on the feedback lane.`,
    },
    {
      id: "feature",
      label: "Steer to /proposal",
      text: `this reads feature-shaped — please file it with in-game \`/proposal\` so council + players can vote. \`/feedback\` stays for bugs/ops/field notes.`,
    },
    {
      id: "bug",
      label: "Bug verify",
      text: `**Bug verify**\n• Repro:\n• Server (play / test):\n• Expected vs actual:\n• Digs: Slack #development-feed`,
    },
    {
      id: "digest",
      label: "Queue digest header",
      text: `**Feedback digest** — Ava Ivy\nPulling recent \`/feedback\` for staff. Discord #development + Slack #feedback stay in sync.`,
    },
  ];
}
