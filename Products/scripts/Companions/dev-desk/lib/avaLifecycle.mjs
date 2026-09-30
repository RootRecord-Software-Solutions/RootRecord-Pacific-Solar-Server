/**
 * Ava session lifecycle — start Python core + voice with the desktop GUI.
 * Origin stays up if the window closes. A watchdog restarts core if /health dies.
 * stopAvaSession() is only for an explicit power-off.
 * Desk close → stopDeskOwnedAudio() (music bed + orphans only; not origin).
 */
import { spawn } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const HOME = process.env.AVA_HOME || path.join(os.homedir(), "Ava-Core");
const AVA_ROOT =
  process.env.AVA_HANDOFF ||
  process.env.AVA_HOME ||
  path.join(os.homedir(), "Ava-Core");
const RUN_DIR = path.join(AVA_ROOT, "data", "run");
const LOG_DIR = path.join(AVA_ROOT, "data", "logs");
const isWin = process.platform === "win32";
const VENV_PY = isWin
  ? path.join(AVA_ROOT, ".venv", "Scripts", "python.exe")
  : path.join(AVA_ROOT, ".venv", "bin", "python");
const VENV_UVICORN = isWin
  ? path.join(AVA_ROOT, ".venv", "Scripts", "uvicorn.exe")
  : path.join(AVA_ROOT, ".venv", "bin", "uvicorn");
const PORT = String(process.env.AVA_PORT || "8787").replace(/\s*#.*$/, "").trim() || "8787";

/** @type {import('node:child_process').ChildProcess[]} */
const children = [];
let startedByUs = false;
let stopping = false;
let restarting = false;
let watchTimer = null;

function ensureDirs() {
  fs.mkdirSync(RUN_DIR, { recursive: true });
  fs.mkdirSync(LOG_DIR, { recursive: true });
}

function appendLog(file, line) {
  try {
    fs.appendFileSync(file, `${new Date().toISOString()} ${line}\n`);
  } catch {
    /* ignore */
  }
}

function childEnv() {
  return {
    ...process.env,
    AVA_HOME: HOME,
    AVA_HANDOFF: AVA_ROOT,
    PYTHONUNBUFFERED: "1",
  };
}

function openLog(name) {
  const preferred = [
    path.join(LOG_DIR, name.replace(/\.log$/, "-session.log")),
    path.join(LOG_DIR, name),
    path.join(os.tmpdir(), `ava-${name}`),
  ];
  let lastErr;
  for (const p of preferred) {
    try {
      return fs.openSync(p, "a");
    } catch (err) {
      lastErr = err;
    }
  }
  throw lastErr || new Error(`cannot open log ${name}`);
}

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

/**
 * Kill leftover Ava runtime processes (same user) so we own a clean session.
 * Does not touch tunnel, mariadb, ollama, minecraft, or phpmyadmin.
 */
export function reapStaleAvaProcesses() {
  // Windows origin is owned by watchdog.py / uvicorn. Do not pkill it.
  if (isWin) {
    return;
  }
  const patterns = [
    "uvicorn apps.core.main:app",
    "apps.voice.director",
    "apps.core.main:app",
  ];
  for (const pat of patterns) {
    try {
      spawn("pkill", ["-u", String(process.getuid?.() ?? 1000), "-f", pat], {
        stdio: "ignore",
        detached: true,
      }).unref();
    } catch {
      /* ignore */
    }
  }
}

function spawnTracked(cmd, args, logName, label) {
  const out = openLog(logName);
  const err = out;
  const child = spawn(cmd, args, {
    cwd: AVA_ROOT,
    env: childEnv(),
    stdio: ["ignore", out, err],
    detached: true,
    windowsHide: true,
  });
  child.unref();
  children.push(child);
  const pidFile = path.join(RUN_DIR, `${label}.pid`);
  try {
    fs.writeFileSync(pidFile, String(child.pid));
  } catch {
    /* ignore */
  }
  child.on("exit", (code, signal) => {
    appendLog(path.join(LOG_DIR, "ava-desktop.log"), `${label} exited code=${code} signal=${signal}`);
    try {
      fs.unlinkSync(pidFile);
    } catch {
      /* ignore */
    }
    if (label === "ava-core" && !stopping) {
      void ensureCoreUp("child-exit");
    }
  });
  return child;
}

async function waitHealth(timeoutMs = 45000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (await healthOk()) return true;
    await sleep(400);
  }
  return false;
}

async function healthOk() {
  try {
    const r = await fetch(`http://127.0.0.1:${PORT}/health`, {
      signal: AbortSignal.timeout(2000),
    });
    return r.ok;
  } catch {
    return false;
  }
}

function spawnCore() {
  if (isWin) {
    const pyw = path.join(AVA_ROOT, ".venv", "Scripts", "pythonw.exe");
    const watch = path.join(process.env.USERPROFILE || "C:\\Users\\rootr", "RootRecord Core Ops", "WatchDog", "watchdog.py");
    const cmd = fs.existsSync(pyw) ? pyw : "pythonw";
    spawn(cmd, [watch], {
      cwd: AVA_ROOT,
      env: childEnv(),
      stdio: "ignore",
      detached: true,
      windowsHide: true,
    }).unref();
    return;
  }
  const uvicornBin = fs.existsSync(VENV_UVICORN) ? VENV_UVICORN : null;
  const pyBin = fs.existsSync(VENV_PY) ? VENV_PY : "python3";
  if (uvicornBin) {
    spawnTracked(
      uvicornBin,
      [
        "apps.core.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        PORT,
        "--log-level",
        "info",
        "--no-access-log",
      ],
      "ava-core.log",
      "ava-core",
    );
  } else {
    spawnTracked(
      pyBin,
      ["-m", "uvicorn", "apps.core.main:app", "--host", "127.0.0.1", "--port", PORT],
      "ava-core.log",
      "ava-core",
    );
  }
}

async function ensureCoreUp(reason) {
  if (stopping || restarting) return;
  if (await healthOk()) return;
  restarting = true;
  try {
    appendLog(path.join(LOG_DIR, "ava-desktop.log"), `watchdog: Ava Core down (${reason}) — restarting`);
    reapStaleAvaProcesses();
    await sleep(800);
    spawnCore();
    await ensureVoiceDirector();
    const ok = await waitHealth(30000);
    appendLog(
      path.join(LOG_DIR, "ava-desktop.log"),
      ok ? "watchdog: Ava Core back" : "watchdog: restart failed",
    );
  } finally {
    restarting = false;
  }
}

function startWatchdog() {
  if (watchTimer) return;
  watchTimer = setInterval(() => {
    void ensureCoreUp("health-poll");
  }, 8000);
}

function stopWatchdog() {
  if (watchTimer) {
    clearInterval(watchTimer);
    watchTimer = null;
  }
}

/**
 * Start Ava Core + Voice Director. Origin is kept alive after the GUI exits.
 */
export async function startAvaSession() {
  stopping = false;
  ensureDirs();
  appendLog(path.join(LOG_DIR, "ava-desktop.log"), "lifecycle: starting Ava session");

  try {
    const r = await fetch(`http://127.0.0.1:${PORT}/health`, {
      signal: AbortSignal.timeout(1500),
    });
    if (r.ok) {
      startedByUs = false;
      appendLog(path.join(LOG_DIR, "ava-desktop.log"), "lifecycle: adopting existing Ava Core");
      if (!isWin) {
        await ensureVoiceDirector();
        startWatchdog();
      }
      return true;
    }
  } catch {
    /* not up yet */
  }

  reapStaleAvaProcesses();
  await sleep(800);
  spawnCore();
  if (!isWin) {
    const pyBin = fs.existsSync(VENV_PY) ? VENV_PY : "python3";
    spawnTracked(pyBin, ["-m", "apps.voice.director"], "ava-voice.log", "ava-voice");
  }

  startedByUs = true;
  const ok = await waitHealth();
  appendLog(
    path.join(LOG_DIR, "ava-desktop.log"),
    ok ? "lifecycle: Ava Core healthy" : "lifecycle: Ava Core health wait timed out",
  );
  if (!isWin) startWatchdog();
  return ok;
}

async function ensureVoiceDirector() {
  if (!isWin) {
    try {
      const { execSync } = await import("node:child_process");
      const out = execSync("pgrep -f 'apps.voice.director' || true", { encoding: "utf8" });
      if (out.trim()) return;
    } catch {
      /* spawn anyway */
    }
  }
  const pyBin = fs.existsSync(VENV_PY) ? VENV_PY : isWin ? "python" : "python3";
  spawnTracked(pyBin, ["-m", "apps.voice.director"], "ava-voice.log", "ava-voice");
}

/**
 * Explicit power-off only. Closing the GUI must not call this.
 */
export function stopAvaSession() {
  stopping = true;
  stopWatchdog();
  appendLog(path.join(LOG_DIR, "ava-desktop.log"), "lifecycle: stopping Ava session (explicit)");

  for (const child of children.splice(0)) {
    try {
      if (child.pid && !child.killed) {
        child.kill("SIGTERM");
      }
    } catch {
      /* ignore */
    }
  }

  setTimeout(() => {
    reapStaleAvaProcesses();
  }, 1500);

  reapStaleAvaProcesses();
  startedByUs = false;

  for (const name of ["ava-core.pid", "ava-voice.pid"]) {
    try {
      fs.unlinkSync(path.join(RUN_DIR, name));
    } catch {
      /* ignore */
    }
  }
}

export function sessionStartedByDesktop() {
  return startedByUs;
}

/**
 * Stop Desk-owned audio helpers only. Origin / watchdog / crons stay up.
 * POSTs /api/voice/music stop (clears bed loop + music-bed-wanted + MediaPlayer orphans).
 * Does not mean "operator wants bed off forever" — that intent is desk-ui musicWanted
 * (saved by handleDeskClose before this runs). Clearing music-bed-wanted.txt only
 * prevents origin recycle from reviving the bed while Desk is closed.
 * If origin is unreachable, still clears wanted flag + best-effort orphan sweep.
 */
export async function stopDeskOwnedAudio() {
  const logPath = path.join(LOG_DIR, "ava-desktop.log");
  appendLog(logPath, "lifecycle: desk close — stopping music bed");
  let api = null;
  try {
    const r = await fetch(`http://127.0.0.1:${PORT}/api/voice/music`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ action: "stop" }),
      signal: AbortSignal.timeout(8000),
    });
    const json = await r.json().catch(() => ({}));
    api = {
      ok: Boolean(r.ok && json.ok !== false),
      status: r.status,
      swept: json.swept ?? null,
      detail: json.detail || null,
    };
    appendLog(
      logPath,
      `lifecycle: music stop http=${r.status} ok=${Boolean(json.ok)} swept=${json.swept ?? "?"}`,
    );
  } catch (err) {
    api = { ok: false, detail: err?.message || String(err) };
    appendLog(
      logPath,
      `lifecycle: music stop failed: ${err?.message || err}`,
    );
  }

  // Clear origin recycle flag only — desk-ui.json keeps resume intent.
  const wantedPath = path.join(AVA_ROOT, "data", "state", "music-bed-wanted.txt");
  try {
    fs.mkdirSync(path.dirname(wantedPath), { recursive: true });
    fs.writeFileSync(wantedPath, "0", "utf8");
  } catch {
    /* ignore */
  }

  let localSwept = 0;
  if (isWin) {
    localSwept = await sweepMusicBedLocal();
    if (localSwept) {
      appendLog(logPath, `lifecycle: local music sweep killed=${localSwept}`);
    }
  }

  return {
    ok: true,
    api,
    localSwept,
    wantedCleared: true,
  };
}

/** Best-effort kill of music-bed OS players via existing director helper (no origin HTTP). */
function sweepMusicBedLocal() {
  return new Promise((resolve) => {
    const py = fs.existsSync(VENV_PY) ? VENV_PY : isWin ? "python" : "python3";
    try {
      const child = spawn(
        py,
        [
          "-c",
          "from apps.voice.director import kill_stray_music_players; print(kill_stray_music_players())",
        ],
        {
          cwd: AVA_ROOT,
          env: childEnv(),
          windowsHide: true,
          stdio: ["ignore", "pipe", "ignore"],
        },
      );
      let out = "";
      child.stdout.on("data", (b) => {
        out += String(b);
      });
      child.on("close", () => {
        const n = parseInt(String(out).trim(), 10);
        resolve(Number.isFinite(n) ? n : 0);
      });
      child.on("error", () => resolve(0));
      setTimeout(() => {
        try {
          child.kill();
        } catch {
          /* ignore */
        }
        resolve(0);
      }, 8000);
    } catch {
      resolve(0);
    }
  });
}

function readMusicBedWantedFile() {
  try {
    const p = path.join(AVA_ROOT, "data", "state", "music-bed-wanted.txt");
    const raw = fs.readFileSync(p, "utf8").trim().toLowerCase();
    return raw === "1" || raw === "true" || raw === "yes" || raw === "on";
  } catch {
    return false;
  }
}

/**
 * Snapshot music intent from origin before stop (for desk-ui restore).
 * Live bed OR music-bed-wanted.txt count as wanted. Operator pause alone does not
 * (intentional pause for the session). Always reads the wanted file too — after a
 * prior desk close the file is 0, so callers must preserve desk-ui when ambiguous.
 */
export async function peekMusicBedStatus() {
  const wantedFile = readMusicBedWantedFile();
  try {
    const r = await fetch(`http://127.0.0.1:${PORT}/api/voice/status`, {
      signal: AbortSignal.timeout(4000),
    });
    const json = await r.json().catch(() => ({}));
    const music = json.music || {};
    const playing = Boolean(json?.currently_playing?.music?.playing);
    const enabled = Boolean(music.enabled);
    const loopAlive = Boolean(music.loop_alive);
    const operatorPaused = Boolean(music.operator_paused);
    // Intentional operator pause ⇒ do not auto-resume on next Desk start.
    const liveWanted = Boolean(enabled || loopAlive || playing || wantedFile);
    const musicWanted = liveWanted && !operatorPaused;
    return {
      ok: Boolean(r.ok && json.ok !== false),
      musicWanted,
      liveWanted,
      operatorPaused,
      enabled,
      loopAlive,
      wantedFile,
      ambiguous: !liveWanted && !operatorPaused,
      musicTrack: music.current || json?.currently_playing?.music?.track || null,
      playing,
    };
  } catch (err) {
    return {
      ok: false,
      detail: err?.message || String(err),
      musicWanted: wantedFile,
      liveWanted: wantedFile,
      operatorPaused: false,
      enabled: false,
      loopAlive: false,
      wantedFile,
      ambiguous: !wantedFile,
      musicTrack: null,
      playing: false,
    };
  }
}

/**
 * Restore music bed after Desk relaunch when last session had it on.
 * POST start clears any leftover operator pause and spins a single bed player.
 */
export async function restoreMusicBedIfWanted(wanted) {
  if (!wanted) return { ok: true, skipped: true };
  const logPath = path.join(LOG_DIR, "ava-desktop.log");
  appendLog(logPath, "lifecycle: desk start — restoring music bed");
  try {
    const r = await fetch(`http://127.0.0.1:${PORT}/api/voice/music`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ action: "start" }),
      signal: AbortSignal.timeout(15000),
    });
    const json = await r.json().catch(() => ({}));
    const track =
      json?.music?.current || json?.currently_playing?.music?.track || null;
    const pid = json?.music?.player_pid ?? null;
    appendLog(
      logPath,
      `lifecycle: music start http=${r.status} ok=${Boolean(json.ok)} track=${track || "—"} pid=${pid ?? "—"} detail=${json.detail || ""}`,
    );
    return {
      ok: Boolean(r.ok && json.ok !== false),
      status: r.status,
      detail: json.detail || null,
      track,
      player_pid: pid,
      tracks: json?.music?.tracks ?? json?.tracks ?? null,
    };
  } catch (err) {
    appendLog(
      logPath,
      `lifecycle: music restore failed: ${err?.message || err}`,
    );
    return { ok: false, detail: err?.message || String(err) };
  }
}
