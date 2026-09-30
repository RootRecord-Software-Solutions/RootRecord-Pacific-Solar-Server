/**
 * Ava Ivy desktop ↔ brain connection.
 * Local = this machine does compute. Headless = remote origin.
 */
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

/** Documented OptiPlex LAN fallback if live detect fails. */
export const LAN_HOST = "192.168.1.62";

export function detectLanIPv4() {
  const fromEnv = String(process.env.AVA_LAN_HOST || "").trim();
  if (fromEnv) return fromEnv;
  try {
    const nets = os.networkInterfaces();
    for (const addrs of Object.values(nets || {})) {
      for (const a of addrs || []) {
        if (!a || a.internal) continue;
        const family = a.family === 4 || a.family === "IPv4";
        if (!family) continue;
        const ip = String(a.address || "");
        if (
          /^192\.168\./.test(ip) ||
          /^10\./.test(ip) ||
          /^172\.(1[6-9]|2\d|3[0-1])\./.test(ip)
        ) {
          return ip;
        }
      }
    }
  } catch {
    /* ignore */
  }
  return LAN_HOST;
}
export const DEFAULT_BRAIN_PORT = 8787;
export const DEFAULT_LOCAL_API_PORT = 8791;
export const DEFAULT_OLLAMA_PORT = 11434;
export const DEFAULT_PUBLIC_URL = "https://origin.avaivy.cloud";
export const DEFAULT_API_BASE = "https://rootrecord.cloud";

function parseEnvFile(filePath) {
  const out = {};
  if (!filePath || !fs.existsSync(filePath)) return out;
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

export function discoverEnvFile() {
  const candidates = [
    process.env.AVA_ENV_FILE,
    process.env.ROOTMC_ENV_FILE,
    path.join(os.homedir(), "Ava-Core", ".env"),
    path.resolve(__dirname, "../../.env"),
    path.join(os.homedir(), "Ava", ".env"),
  ];
  for (const p of candidates) {
    if (p && fs.existsSync(p)) return p;
  }
  return "";
}

export function serverCredentialDefaults() {
  const env = {
    ...parseEnvFile(discoverEnvFile()),
    ...process.env,
  };
  const port = Number(env.AVA_PORT || DEFAULT_BRAIN_PORT) || DEFAULT_BRAIN_PORT;
  const localApiPort =
    Number(env.AVA_LOCAL_API_PORT || DEFAULT_LOCAL_API_PORT) ||
    DEFAULT_LOCAL_API_PORT;
  const operatorKey = String(
    env.AVA_OPERATOR_KEY ||
      env.ROOTMC_DEV_WORKSTATION_KEY ||
      env.AVA_CRON_KEY ||
      "",
  ).trim();
  const workstationKey = String(
    env.ROOTMC_DEV_WORKSTATION_KEY || env.ROOTMC_INTERNAL_API_KEY || "",
  ).trim();
  return {
    port,
    localApiPort,
    bind: String(env.AVA_BIND || "0.0.0.0").trim() || "0.0.0.0",
    lanHost: String(env.AVA_LAN_HOST || "").trim() || detectLanIPv4(),
    operatorKey,
    workstationKey,
    publicUrl: String(env.AVA_PUBLIC_URL || DEFAULT_PUBLIC_URL)
      .trim()
      .replace(/\/$/, ""),
    apiBase: String(env.AVA_API_BASE || env.ROOTMC_API_BASE || DEFAULT_API_BASE)
      .trim()
      .replace(/\/$/, ""),
    ollamaModel: String(env.AVA_OLLAMA_MODEL || env.OLLAMA_MODEL || "ava-ivy").trim() ||
      "ava-ivy",
    envFile: discoverEnvFile(),
  };
}

function stripSlash(url) {
  return String(url || "").trim().replace(/\/$/, "");
}

export function presetLocal(creds = serverCredentialDefaults()) {
  return {
    mode: "local",
    via: "loopback",
    brainUrl: `http://127.0.0.1:${creds.port}`,
    localApiUrl: `http://127.0.0.1:${creds.localApiPort}`,
    ollamaUrl: `http://127.0.0.1:${DEFAULT_OLLAMA_PORT}`,
    publicUrl: creds.publicUrl,
    apiBase: creds.apiBase,
    operatorKey: creds.operatorKey,
    workstationKey: creds.workstationKey,
    ollamaModel: creds.ollamaModel,
  };
}

export function presetHeadlessLan(creds = serverCredentialDefaults()) {
  const host = creds.lanHost || LAN_HOST;
  return {
    mode: "headless",
    via: "lan",
    brainUrl: `http://${host}:${creds.port}`,
    localApiUrl: `http://${host}:${creds.localApiPort}`,
    ollamaUrl: `http://${host}:${DEFAULT_OLLAMA_PORT}`,
    publicUrl: creds.publicUrl,
    apiBase: creds.apiBase,
    operatorKey: creds.operatorKey,
    workstationKey: creds.workstationKey,
    ollamaModel: creds.ollamaModel,
  };
}

export function presetHeadlessPublic(creds = serverCredentialDefaults()) {
  const lan = presetHeadlessLan(creds);
  return {
    ...lan,
    via: "public",
    brainUrl: creds.publicUrl || DEFAULT_PUBLIC_URL,
    // :8791 is LAN-only; keep LAN local-api even when brain is public tunnel
    localApiUrl: lan.localApiUrl,
    ollamaUrl: lan.ollamaUrl,
  };
}

export function connectionFileCandidates() {
  return [
    process.env.AVA_CONNECTION_FILE,
    path.join(os.homedir(), ".config", "ava-ivy", "connection.json"),
    path.resolve(__dirname, "../data/connection.json"),
  ].filter(Boolean);
}

function readJson(file) {
  try {
    return JSON.parse(fs.readFileSync(file, "utf8"));
  } catch {
    return null;
  }
}

function normalizeConn(raw, creds = serverCredentialDefaults()) {
  const mode = raw?.mode === "headless" ? "headless" : "local";
  const via =
    raw?.via === "public" || raw?.via === "lan" || raw?.via === "loopback"
      ? raw.via
      : mode === "headless"
        ? "lan"
        : "loopback";
  const base =
    mode === "local"
      ? presetLocal(creds)
      : via === "public"
        ? presetHeadlessPublic(creds)
        : presetHeadlessLan(creds);
  return {
    ...base,
    mode,
    via,
    brainUrl: stripSlash(raw?.brainUrl) || base.brainUrl,
    localApiUrl: stripSlash(raw?.localApiUrl) || base.localApiUrl,
    ollamaUrl: stripSlash(raw?.ollamaUrl) || base.ollamaUrl,
    publicUrl: stripSlash(raw?.publicUrl) || base.publicUrl,
    apiBase: stripSlash(raw?.apiBase) || base.apiBase,
    operatorKey: String(raw?.operatorKey || base.operatorKey || "").trim(),
    workstationKey: String(raw?.workstationKey || base.workstationKey || "").trim(),
    ollamaModel: String(raw?.ollamaModel || base.ollamaModel || "ava-ivy").trim(),
  };
}

export function loadConnectionConfig() {
  const creds = serverCredentialDefaults();
  for (const file of connectionFileCandidates()) {
    const raw = readJson(file);
    if (raw && typeof raw === "object") {
      return { ...normalizeConn(raw, creds), source: file };
    }
  }
  return { ...presetLocal(creds), source: "defaults" };
}

export function saveConnectionConfig(patch = {}) {
  const creds = serverCredentialDefaults();
  const next = normalizeConn({ ...loadConnectionConfig(), ...patch }, creds);
  const homeFile = path.join(os.homedir(), ".config", "ava-ivy", "connection.json");
  const repoFile = path.resolve(__dirname, "../data/connection.json");
  const payload = {
    mode: next.mode,
    via: next.via,
    brainUrl: next.brainUrl,
    localApiUrl: next.localApiUrl,
    ollamaUrl: next.ollamaUrl,
    publicUrl: next.publicUrl,
    apiBase: next.apiBase,
    operatorKey: next.operatorKey,
    workstationKey: next.workstationKey,
    ollamaModel: next.ollamaModel,
    updatedAt: new Date().toISOString(),
  };
  const written = [];
  for (const file of [homeFile, repoFile]) {
    try {
      fs.mkdirSync(path.dirname(file), { recursive: true });
      fs.writeFileSync(file, `${JSON.stringify(payload, null, 2)}\n`, {
        encoding: "utf8",
        mode: 0o600,
      });
      try {
        fs.chmodSync(file, 0o600);
      } catch {
        /* ignore */
      }
      written.push(file);
    } catch {
      /* skip unwritable */
    }
  }
  if (!written.length) {
    throw new Error("could not write connection.json");
  }
  return { ok: true, written, connection: { ...next, source: written[0] } };
}

export function brainOrigin(conn = loadConnectionConfig()) {
  return stripSlash(conn.brainUrl) || `http://127.0.0.1:${DEFAULT_BRAIN_PORT}`;
}

export function isRemoteCompute(conn = loadConnectionConfig()) {
  return conn?.mode === "headless";
}

export function operatorHeaders(env = {}) {
  const headers = {};
  const op = String(env.operatorKey || "").trim();
  const ws = String(env.workstationKey || "").trim();
  if (op) headers["X-Ava-Operator-Key"] = op;
  if (ws) headers["X-RootMC-Dev-Key"] = ws;
  return headers;
}

function maskSecret(value) {
  const s = String(value || "");
  if (!s) return "";
  if (s.length <= 8) return "••••";
  return `${"•".repeat(Math.min(12, s.length - 4))}${s.slice(-4)}`;
}

export function connectionPublicView(conn = loadConnectionConfig()) {
  return {
    mode: conn.mode,
    via: conn.via,
    brainUrl: conn.brainUrl,
    localApiUrl: conn.localApiUrl,
    ollamaUrl: conn.ollamaUrl,
    publicUrl: conn.publicUrl,
    apiBase: conn.apiBase,
    ollamaModel: conn.ollamaModel,
    source: conn.source || null,
    hasOperatorKey: Boolean(conn.operatorKey),
    hasWorkstationKey: Boolean(conn.workstationKey),
    operatorKeyMasked: maskSecret(conn.operatorKey),
    workstationKeyMasked: maskSecret(conn.workstationKey),
    computeRemote: isRemoteCompute(conn),
  };
}

export function connectionFormPayload() {
  const creds = serverCredentialDefaults();
  const current = loadConnectionConfig();
  return {
    ok: true,
    current: {
      ...current,
      // full keys only for the settings form on this machine
    },
    view: connectionPublicView(current),
    presets: {
      local: presetLocal(creds),
      headlessLan: presetHeadlessLan(creds),
      headlessPublic: presetHeadlessPublic(creds),
    },
    server: {
      port: creds.port,
      localApiPort: creds.localApiPort,
      bind: creds.bind,
      lanHost: creds.lanHost,
      publicUrl: creds.publicUrl,
      apiBase: creds.apiBase,
      ollamaModel: creds.ollamaModel,
      envFile: creds.envFile || null,
      hasOperatorKey: Boolean(creds.operatorKey),
      hasWorkstationKey: Boolean(creds.workstationKey),
    },
  };
}

async function probe(url, { headers = {}, timeoutMs = 4000 } = {}) {
  const started = Date.now();
  try {
    const res = await fetch(url, {
      headers,
      signal: AbortSignal.timeout(timeoutMs),
      cache: "no-store",
    });
    const text = await res.text();
    let json = null;
    try {
      json = text ? JSON.parse(text) : null;
    } catch {
      json = null;
    }
    return {
      ok: res.ok,
      status: res.status,
      ms: Date.now() - started,
      detail: json?.service || json?.detail || json?.ok || text.slice(0, 80),
    };
  } catch (err) {
    return {
      ok: false,
      status: 0,
      ms: Date.now() - started,
      detail: err?.name === "TimeoutError" ? "timeout" : err?.message || String(err),
    };
  }
}

export async function testConnection(conn = loadConnectionConfig()) {
  const headers = operatorHeaders(conn);
  const brain = brainOrigin(conn);
  const localApi = stripSlash(conn.localApiUrl);
  const ollama = stripSlash(conn.ollamaUrl);
  const probes = {
    brain: await probe(`${brain}/health`, { headers }),
    core: await probe(`${brain}/api/core-chat/status`, { headers }),
  };
  if (localApi) {
    probes.localApi = await probe(`${localApi}/api/status`, {
      headers: {
        ...headers,
        ...(conn.workstationKey ? { "X-RootMC-Dev-Key": conn.workstationKey } : {}),
      },
    });
  }
  if (!isRemoteCompute(conn) && ollama) {
    probes.ollama = await probe(`${ollama}/api/tags`);
  }
  const ok = Boolean(probes.brain?.ok);
  return {
    ok,
    mode: conn.mode,
    via: conn.via,
    brainUrl: brain,
    probes,
  };
}
