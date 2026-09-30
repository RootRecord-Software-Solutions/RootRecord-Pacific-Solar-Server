/**
 * Live-tree GitHub sync for Ava desktop.
 * Pulls into the live tree so deploys stay aligned with the files this machine runs.
 */
import { spawn } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

const PREFS_NAME = "desktop-git-sync.json";

export function gitSyncPrefsPath(avaHome) {
  return path.join(avaHome, "data", PREFS_NAME);
}

export function loadGitSyncPrefs(avaHome) {
  const p = gitSyncPrefsPath(avaHome);
  const defaults = {
    autoCheck: true,
    autoPull: true,
    intervalMs: 10 * 60 * 1000,
  };
  try {
    if (!fs.existsSync(p)) return defaults;
    const j = JSON.parse(fs.readFileSync(p, "utf8"));
    return {
      autoCheck: j.autoCheck !== false,
      autoPull: j.autoPull !== false,
      intervalMs: Math.max(60_000, Number(j.intervalMs) || defaults.intervalMs),
    };
  } catch {
    return defaults;
  }
}

export function saveGitSyncPrefs(avaHome, patch = {}) {
  const next = { ...loadGitSyncPrefs(avaHome), ...patch };
  const p = gitSyncPrefsPath(avaHome);
  fs.mkdirSync(path.dirname(p), { recursive: true });
  fs.writeFileSync(p, `${JSON.stringify(next, null, 2)}\n`);
  return next;
}

function scriptPath(avaHome) {
  if (process.platform === "win32") {
    return path.join(avaHome, "scripts", "auto-pull.py");
  }
  return path.join(avaHome, "scripts", "git-pull-live.sh");
}

function pythonExe(avaHome) {
  const candidates = [
    path.join(avaHome, ".venv", "Scripts", "python.exe"),
    path.join(avaHome, ".venv", "bin", "python"),
  ];
  for (const c of candidates) {
    if (fs.existsSync(c)) return c;
  }
  return "python";
}

function parseJsonLine(text) {
  const line = String(text || "")
    .split(/\r?\n/)
    .reverse()
    .find((l) => l.startsWith("AVA_GIT_JSON:"));
  if (!line) return null;
  try {
    return JSON.parse(line.slice("AVA_GIT_JSON:".length));
  } catch {
    return null;
  }
}

/**
 * @param {"status"|"check"|"pull"} mode
 * @param {{ avaHome: string, autoPull?: boolean, onLine?: (line: string) => void }} opts
 */
export function runGitLiveSync(mode, opts) {
  const avaHome = opts.avaHome;
  const script = scriptPath(avaHome);
  return new Promise((resolve) => {
    if (!fs.existsSync(script)) {
      resolve({
        ok: false,
        action: mode,
        detail: "missing_script",
        behind: 0,
        ahead: 0,
        dirty: false,
        pulled: false,
        log: "",
      });
      return;
    }
    const env = {
      ...process.env,
      AVA_GIT_AUTO_PULL: opts.autoPull ? "1" : "0",
    };
    const child =
      process.platform === "win32"
        ? spawn(pythonExe(avaHome), [script, mode], {
            cwd: avaHome,
            env,
            stdio: ["ignore", "pipe", "pipe"],
            windowsHide: true,
          })
        : spawn("bash", [script, mode], {
            cwd: avaHome,
            env,
            stdio: ["ignore", "pipe", "pipe"],
          });
    let buf = "";
    const onChunk = (chunk) => {
      const s = chunk.toString("utf8");
      buf += s;
      for (const line of s.split(/\r?\n/)) {
        if (line) opts.onLine?.(line);
      }
    };
    child.stdout?.on("data", onChunk);
    child.stderr?.on("data", onChunk);
    child.on("error", (err) => {
      resolve({
        ok: false,
        action: mode,
        detail: err.message,
        behind: 0,
        ahead: 0,
        dirty: false,
        pulled: false,
        log: buf,
      });
    });
    child.on("close", (code) => {
      const parsed = parseJsonLine(buf) || {};
      resolve({
        ok: Boolean(parsed.ok) && code === 0,
        exitCode: code ?? 1,
        action: mode,
        detail: parsed.detail || (code === 0 ? "ok" : "failed"),
        branch: parsed.branch || null,
        upstream: parsed.upstream || null,
        ahead: Number(parsed.ahead || 0),
        behind: Number(parsed.behind || 0),
        dirty: Boolean(parsed.dirty),
        pulled: Boolean(parsed.pulled),
        changed_core: Boolean(parsed.changed_core),
        changed_desktop: Boolean(parsed.changed_desktop),
        changed_web: Boolean(parsed.changed_web),
        repo: parsed.repo || avaHome,
        log: buf,
      });
    });
  });
}
