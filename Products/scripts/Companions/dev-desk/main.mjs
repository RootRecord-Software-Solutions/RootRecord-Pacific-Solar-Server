/**
 * Ava Ivy desktop — Electron main.
 */
import { app, BrowserWindow, ipcMain, shell, dialog } from "electron";
import { spawn } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  loadDesktopEnv,
  fetchDiscordHistory,
  fetchTelegramHistory,
  fetchSlackHistory,
  listDiscordTextChannels,
  listDiscordPrivateChannels,
  listSlackChannels,
  listTelegramChats,
  listPostPresets,
  listAllPostTargets,
  postToAllPages,
  postAsAva,
  rewriteDraft,
  summarizeChannel,
  fetchRewriteProviders,
  fetchCronStatus,
  fetchReportsStatus,
  fetchFinanceSuite,
  postFinanceSuite,
  fetchBiz,
  postBiz,
  tickEarlyLoginDesktop,
  runCronJob,
  configureCron,
  fetchCoreChatStatus,
  coreChat,
  coreChatEnhance,
  coreChatGold,
  editDiscordMessage,
  deleteDiscordMessage,
  listFeedbackQueue,
  processFeedbackNext,
  ackFeedbackItem,
  dualPostFeedback,
  feedbackTemplates,
  FEEDBACK_TARGETS,
  deleteSlackMessage,
  clearDiscordOwnMessages,
  clearSlackOwnMessages,
  clearAllFeedbackAndStamp,
} from "./lib/avaBridge.mjs";
import {
  ensureMediaDirs,
  listMediaFiles,
  importMediaFiles,
} from "./lib/avaMedia.mjs";
import { listOpsCatalog, opsCommandById } from "./lib/opsCommands.mjs";
import { listAvaLinks } from "./lib/avaLinks.mjs";
import {
  startAvaSession,
  stopDeskOwnedAudio,
  peekMusicBedStatus,
  restoreMusicBedIfWanted,
} from "./lib/avaLifecycle.mjs";
import {
  loadConnectionConfig,
  connectionFormPayload,
  saveConnectionConfig,
  testConnection,
  brainOrigin,
  operatorHeaders,
} from "./lib/connectionConfig.mjs";
import {
  loadGitSyncPrefs,
  saveGitSyncPrefs,
  runGitLiveSync,
} from "./lib/gitLiveSync.mjs";
import {
  deskAvaRoot,
  loadDeskUiState,
  saveDeskUiState,
  checkMorningReportStatus,
} from "./lib/deskState.mjs";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const CONTEXT_LIMIT = 150;
const AVA_HOME =
  process.env.AVA_HOME ||
  path.join(os.homedir(), "Ava-Core");
const AVA_CORE =
  process.env.AVA_CORE ||
  [
    path.join(AVA_HOME, "apps", "core"),
    path.join(AVA_HOME, "Core"),
  ].find((p) => fs.existsSync(p)) ||
  path.join(AVA_HOME, "apps", "core");

function brainFetchHeaders(extra = {}) {
  return { ...operatorHeaders(loadConnectionConfig()), ...extra };
}

async function brainJson(pathname, { method = "GET", body, timeoutMs = 20000 } = {}) {
  const url = `${brainOrigin()}${pathname}`;
  const ac = new AbortController();
  const t = setTimeout(() => ac.abort(), timeoutMs);
  try {
    const res = await fetch(url, {
      method,
      headers: {
        ...brainFetchHeaders(body ? { "content-type": "application/json" } : {}),
      },
      body: body != null ? JSON.stringify(body) : undefined,
      signal: ac.signal,
      cache: "no-store",
    });
    const json = await res.json().catch(() => ({}));
    if (!res.ok) {
      return {
        ok: false,
        detail: json.detail || json.reason || `http_${res.status}`,
        status: res.status,
        ...json,
      };
    }
    return json && typeof json === "object" ? json : { ok: true, data: json };
  } catch (err) {
    return {
      ok: false,
      detail: err?.name === "AbortError" ? "timeout" : err?.message || String(err),
    };
  } finally {
    clearTimeout(t);
  }
}

let mainWindow = null;
/** @type {import('node:child_process').ChildProcess | null} */
let runningOps = null;
let runningOpsId = null;
/** Guard: window-all-closed + before-quit both fire on Windows quit. */
let deskCloseHandled = false;
/** Operator Clear desk — skip soft music teardown; exit hard. */
let operatorPurgeRunning = false;
let lastDeskPage = "terminal";

const DESK_ROOT = deskAvaRoot();
const OPERATOR_PURGE_SCRIPT = path.join(
  os.homedir(),
  "RootRecord Core Ops",
  "WatchDog",
  "operator_purge.py",
);

function runOperatorPurgeScript(args = []) {
  const python =
    [
      path.join(DESK_ROOT, ".venv", "bin", "python"),
      path.join(DESK_ROOT, ".venv", "Scripts", "python.exe"),
      path.join(DESK_ROOT, ".venv", "Scripts", "pythonw.exe"),
    ].find((p) => fs.existsSync(p)) || (process.platform === "win32" ? "python" : "python3");
  const script = OPERATOR_PURGE_SCRIPT;
  return new Promise((resolve) => {
    let out = "";
    let err = "";
    let settled = false;
    const finish = (payload) => {
      if (settled) return;
      settled = true;
      resolve(payload);
    };
    try {
      const child = spawn(python, [script, ...args], {
        cwd: DESK_ROOT,
        env: { ...process.env, AVA_HOME: DESK_ROOT },
        windowsHide: true,
      });
      const timer = setTimeout(() => {
        try {
          child.kill();
        } catch {
          /* ignore */
        }
        finish({ ok: false, detail: "purge_timeout" });
      }, 45000);
      child.stdout?.on("data", (chunk) => {
        out += String(chunk);
      });
      child.stderr?.on("data", (chunk) => {
        err += String(chunk);
      });
      child.on("error", (e) => {
        clearTimeout(timer);
        finish({ ok: false, detail: e?.message || String(e) });
      });
      child.on("close", (code) => {
        clearTimeout(timer);
        let parsed = null;
        try {
          const start = out.indexOf("{");
          const end = out.lastIndexOf("}");
          if (start >= 0 && end > start) {
            parsed = JSON.parse(out.slice(start, end + 1));
          }
        } catch {
          parsed = null;
        }
        if (parsed && typeof parsed === "object") {
          finish(parsed);
          return;
        }
        finish({
          ok: code === 0,
          detail: code === 0 ? "ok" : `exit_${code}`,
          raw: (out || err || "").slice(0, 800),
        });
      });
    } catch (e) {
      finish({ ok: false, detail: e?.message || String(e) });
    }
  });
}

/** Opening Desk again clears sticky purge and brings Ava tasks/origin back. */
async function clearOperatorPurgeOnOpen() {
  const status = await runOperatorPurgeScript(["--status", "--json"]);
  if (!status?.active) return { ok: true, cleared: false };
  return runOperatorPurgeScript(["--clear", "--json"]);
}

function nodeBin() {
  const home = os.homedir();
  const candidates = [
    process.env.AVA_NODE_BIN,
    path.join(home, ".local", "bin", "node"),
    "/usr/local/bin/node",
    "/usr/bin/node",
  ].filter(Boolean);
  for (const c of candidates) {
    try {
      if (c && fs.existsSync(c)) return c;
    } catch {
      /* ignore */
    }
  }
  return "node";
}

function createWindow() {
  const ui = loadDeskUiState(DESK_ROOT);
  lastDeskPage = ui.page || "terminal";
  const bounds = ui.bounds;
  const opts = {
    width: bounds?.width || 1320,
    height: bounds?.height || 920,
    minWidth: 980,
    minHeight: 680,
    title: "Dev-Desk",
    webPreferences: {
      preload: path.join(__dirname, "preload.cjs"),
      contextIsolation: true,
      nodeIntegration: false,
    },
  };
  // Windows saved a maximized position; do not reuse it on this Linux display.
  if (
    process.platform === "win32" &&
    bounds &&
    Number.isFinite(bounds.x) &&
    Number.isFinite(bounds.y)
  ) {
    opts.x = bounds.x;
    opts.y = bounds.y;
  }
  mainWindow = new BrowserWindow(opts);
  mainWindow.loadFile(path.join(__dirname, "renderer", "index.html"));
  mainWindow.webContents.on("did-fail-load", (_e, code, desc, url) => {
    console.error("desk load failed", code, desc, url);
  });
  mainWindow.webContents.on("did-finish-load", () => {
    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.setTitle("Dev-Desk");
    }
  });

  // Startup voice is owned by Ava Core lifespan (30m cooldown).
  // Do not re-fire from the GUI — reload / brief disconnects were spamming
  // "Root Record is online. I'm back."

  // Closing the GUI is an explicit full AVA shutdown.

  mainWindow.on("close", () => {
    try {
      if (mainWindow && !mainWindow.isDestroyed()) {
        const b = mainWindow.getBounds();
        saveDeskUiState(
          {
            page: lastDeskPage,
            bounds: b,
          },
          DESK_ROOT,
        );
      }
    } catch {
      /* ignore */
    }
  });

  mainWindow.on("closed", () => {
    mainWindow = null;
  });
}

async function handleDeskClose(reason) {
  if (deskCloseHandled) return;
  deskCloseHandled = true;

  if (reason === "window-all-closed" || reason === "before-quit") {
    operatorPurgeRunning = true;
    await runOperatorPurgeScript(["--json"]);
    return;
  }

  try {
    if (mainWindow && !mainWindow.isDestroyed()) {
      try {
        saveDeskUiState(
          {
            page: lastDeskPage,
            bounds: mainWindow.getBounds(),
          },
          DESK_ROOT,
        );
      } catch {
        /* ignore */
      }
    }
    const existing = loadDeskUiState(DESK_ROOT);
    const peek = await peekMusicBedStatus();
    // Speakers intent only — on-air bed must not set musicWanted (that unmuted Desk).
    let radioLocal = false;
    try {
      const rr = await fetch(`http://127.0.0.1:${process.env.AVA_PORT || 8787}/api/radio/status`, {
        signal: AbortSignal.timeout(3000),
      });
      const rj = await rr.json().catch(() => ({}));
      radioLocal = Boolean(rj?.local_playback);
    } catch {
      radioLocal = Boolean(existing.radioLocal);
    }
    let musicWanted;
    if (peek.operatorPaused && !peek.playing) {
      musicWanted = false;
    } else if (radioLocal) {
      musicWanted = true;
    } else {
      // On air alone keeps the bed for the stream; Desk speakers stay off.
      musicWanted = false;
    }
    saveDeskUiState(
      {
        musicWanted,
        radioLocal,
        musicTrack: peek.musicTrack || existing.musicTrack || null,
        closedAt: new Date().toISOString(),
        closeReason: reason,
      },
      DESK_ROOT,
    );
  } catch {
    /* ignore */
  }

  if (runningOps) {
    try {
      runningOps.kill("SIGTERM");
    } catch {
      /* ignore */
    }
    runningOps = null;
    runningOpsId = null;
  }

  // Stop music + MediaPlayer orphans — unless on air (public stream needs the bed).
  let onAir = false;
  try {
    const rr = await fetch(`http://127.0.0.1:${process.env.AVA_PORT || 8787}/api/radio/status`, {
      signal: AbortSignal.timeout(3000),
    });
    const rj = await rr.json().catch(() => ({}));
    onAir = Boolean(rj?.on_air);
  } catch {
    onAir = false;
  }
  if (onAir) {
    try {
      await fetch(`http://127.0.0.1:${process.env.AVA_PORT || 8787}/api/radio`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ local_playback: false, on_air: true }),
        signal: AbortSignal.timeout(8000),
      });
    } catch {
      /* ignore */
    }
  } else {
    await stopDeskOwnedAudio();
  }
}

async function restoreDeskSession() {
  const ui = loadDeskUiState(DESK_ROOT);
  const morning = checkMorningReportStatus(DESK_ROOT);
  sendOps("ava:desk-lifecycle", {
    phase: "start",
    ui,
    morning,
  });
  // Speakers only when Local was on. On-air bed must not unmute Desk.
  const wantSpeakers =
    ui.radioLocal === true || (ui.radioLocal == null && ui.musicWanted === true);
  if (wantSpeakers) {
    const music = await restoreMusicBedIfWanted(true);
    sendOps("ava:desk-lifecycle", {
      phase: "music-restore",
      music,
      track: ui.musicTrack || null,
    });
    try {
      await fetch(`http://127.0.0.1:${process.env.AVA_PORT || 8787}/api/radio`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ local_playback: true }),
        signal: AbortSignal.timeout(8000),
      });
    } catch {
      /* ignore */
    }
  } else {
    try {
      await fetch(`http://127.0.0.1:${process.env.AVA_PORT || 8787}/api/radio`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ local_playback: false }),
        signal: AbortSignal.timeout(8000),
      });
    } catch {
      /* ignore */
    }
  }
  return { ui, morning };
}

function sendOps(channel, payload) {
  if (mainWindow && !mainWindow.isDestroyed()) {
    mainWindow.webContents.send(channel, payload);
  }
}

function appendLine(line) {
  sendOps("ava:ops-line", { line: String(line).replace(/\r?\n$/, "") });
}

let gitSyncTimer = null;
let lastGitSync = null;

function broadcastGitSync(result) {
  lastGitSync = { ...result, at: new Date().toISOString() };
  sendOps("ava:git-sync", lastGitSync);
}

async function runGitSyncMode(mode, { stream = false, autoPull } = {}) {
  const prefs = loadGitSyncPrefs(AVA_HOME);
  const doAuto = autoPull != null ? Boolean(autoPull) : prefs.autoPull;
  if (stream) {
    sendOps("ava:ops-start", {
      id: `git-${mode}`,
      label: mode === "pull" ? "Pull GitHub → live /ava" : "Check GitHub updates",
      detail: `scripts/git-pull-live.sh ${mode}`,
    });
    appendLine(`$ bash scripts/git-pull-live.sh ${mode}`);
  }
  const result = await runGitLiveSync(mode, {
    avaHome: AVA_HOME,
    autoPull: doAuto,
    onLine: stream ? (line) => appendLine(line) : undefined,
  });
  broadcastGitSync(result);
  if (stream) {
    sendOps("ava:ops-done", {
      id: `git-${mode}`,
      code: result.ok ? 0 : result.exitCode || 1,
    });
  }
  return result;
}

function scheduleGitAutoCheck() {
  if (gitSyncTimer) clearInterval(gitSyncTimer);
  gitSyncTimer = null;
  const prefs = loadGitSyncPrefs(AVA_HOME);
  if (!prefs.autoCheck) return;
  const tick = () => {
    runGitSyncMode("check", { autoPull: prefs.autoPull }).catch((err) => {
      broadcastGitSync({
        ok: false,
        action: "check",
        detail: err?.message || String(err),
        behind: 0,
        ahead: 0,
        dirty: false,
        pulled: false,
      });
    });
  };
  // First check shortly after launch, then on interval.
  setTimeout(tick, 20_000);
  gitSyncTimer = setInterval(tick, prefs.intervalMs);
}

if (!app.requestSingleInstanceLock()) {
  app.quit();
} else {
  app.on("second-instance", () => {
    if (mainWindow && !mainWindow.isDestroyed()) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.show();
      mainWindow.focus();
    }
  });
}

app.whenReady().then(async () => {
  if (!app.hasSingleInstanceLock()) return;
  deskCloseHandled = false;
  const launchState = loadDeskUiState(DESK_ROOT);
  createWindow();
  scheduleGitAutoCheck();
  // Origin starts after the window is on screen. Waiting on :8787 first
  // left a blank desktop for up to 45s (or forever if health never returned).
  if (launchState.startAvaOnLaunch && !operatorPurgeRunning) {
    try {
      await clearOperatorPurgeOnOpen();
    } catch (err) {
      console.error("operator purge clear-on-open failed:", err?.message || err);
    }
  }
  if (launchState.startAvaOnLaunch) {
    try {
      await startAvaSession();
    } catch (err) {
      console.error("Ava session start failed:", err?.message || err);
    }
  }
  // After window is up: morning-report JSON check + optional music restore.
  setTimeout(() => {
    restoreDeskSession().catch((err) => {
      console.error("Desk restore failed:", err?.message || err);
    });
  }, 1500);
  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      deskCloseHandled = false;
      const state = loadDeskUiState(DESK_ROOT);
      const resume = state.startAvaOnLaunch ? clearOperatorPurgeOnOpen() : Promise.resolve();
      resume
        .catch(() => {})
        .finally(() => {
          const start = state.startAvaOnLaunch ? startAvaSession() : Promise.resolve();
          start.finally(() => {
            createWindow();
            setTimeout(() => {
              restoreDeskSession().catch(() => {});
            }, 1500);
          });
        });
    }
  });
  loadDesktopEnv()
    .then((env) => tickEarlyLoginDesktop(env))
    .catch(() => {});
});

app.on("window-all-closed", () => {
  void handleDeskClose("window-all-closed").finally(() => {
    if (process.platform !== "darwin") app.quit();
  });
});

app.on("before-quit", (e) => {
  if (deskCloseHandled || operatorPurgeRunning) return;
  e.preventDefault();
  void handleDeskClose("before-quit").finally(() => {
    app.exit(0);
  });
});

ipcMain.handle("ava:env-status", async () => {
  const env = await loadDesktopEnv();
  const conn = loadConnectionConfig();
  return {
    ok: true,
    hasDiscord: Boolean(env.discordToken),
    hasSlack: Boolean(env.slackToken),
    hasTelegram: Boolean(env.telegramToken),
    rewriteUrl: env.rewriteUrl,
    operatorChatId: env.operatorChatId,
    brainUrl: env.brainUrl,
    mode: conn.mode,
    via: conn.via,
    computeRemote: Boolean(env.computeRemote),
    hasOperatorKey: Boolean(env.operatorKey),
  };
});

ipcMain.handle("ava:connection-get", async () => connectionFormPayload());

ipcMain.handle("ava:connection-save", async (_e, patch = {}) => {
  try {
    return saveConnectionConfig(patch || {});
  } catch (err) {
    return { ok: false, detail: err?.message || String(err) };
  }
});

ipcMain.handle("ava:connection-test", async (_e, patch = {}) => {
  const conn = patch && Object.keys(patch).length
    ? { ...loadConnectionConfig(), ...patch }
    : loadConnectionConfig();
  return testConnection(conn);
});

ipcMain.handle("ava:list-discord-channels", async () => {
  const env = await loadDesktopEnv();
  return listDiscordTextChannels(env);
});

ipcMain.handle("ava:list-discord-private", async () => {
  const env = await loadDesktopEnv();
  return listDiscordPrivateChannels(env);
});

ipcMain.handle("ava:list-slack-channels", async () => {
  const env = await loadDesktopEnv();
  return listSlackChannels(env);
});

ipcMain.handle("ava:list-telegram-chats", async () => {
  const env = await loadDesktopEnv();
  return listTelegramChats(env);
});

ipcMain.handle("ava:list-presets", async () => listPostPresets());

ipcMain.handle("ava:history", async (_e, { surface, channelId, limit }) => {
  const env = await loadDesktopEnv();
  const n = Math.min(200, Math.max(1, Number(limit) || CONTEXT_LIMIT));
  if (surface === "telegram") {
    return fetchTelegramHistory(env, channelId || env.operatorChatId, n);
  }
  if (surface === "slack") {
    return fetchSlackHistory(env, channelId, n);
  }
  return fetchDiscordHistory(env, channelId, n);
});

ipcMain.handle("ava:send", async (_e, opts) => {
  const env = await loadDesktopEnv();
  return postAsAva(env, {
    ...opts,
    rewrite: opts.rewrite !== false && String(opts.provider || "") !== "exact",
  });
});

ipcMain.handle("ava:post", async (_e, opts) => {
  const env = await loadDesktopEnv();
  return postAsAva(env, {
    ...opts,
    rewrite: Boolean(opts.rewrite) && String(opts.provider || "") !== "exact",
  });
});

ipcMain.handle("ava:list-all-post-targets", async () => {
  try {
    const env = await loadDesktopEnv();
    return await listAllPostTargets(env);
  } catch (err) {
    return { ok: false, detail: err?.message || String(err), targets: [], counts: { total: 0 } };
  }
});

ipcMain.handle("ava:post-all", async (_e, opts) => {
  try {
    const env = await loadDesktopEnv();
    return await postToAllPages(
      env,
      {
        ...opts,
        rewrite: Boolean(opts?.rewrite) && String(opts?.provider || "") !== "exact",
      },
      (progress) => sendOps("ava:post-all-progress", progress),
    );
  } catch (err) {
    return { ok: false, detail: err?.message || String(err), posted: 0, failed: 0, results: [] };
  }
});

ipcMain.handle("ava:media-root", async () => {
  const root = ensureMediaDirs();
  return { ok: true, root, media: root };
});

ipcMain.handle("ava:media-list", async (_e, opts) => {
  try {
    return listMediaFiles(opts || {});
  } catch (err) {
    return { ok: false, detail: err?.message || String(err), files: [] };
  }
});

ipcMain.handle("ava:media-pick", async (_e, opts) => {
  try {
    const root = ensureMediaDirs();
    const kind = String(opts?.kind || "images").toLowerCase() === "audio" ? "audio" : "images";
    const defaultPath =
      opts?.defaultPath && fs.existsSync(opts.defaultPath)
        ? opts.defaultPath
        : path.join(root, kind === "audio" ? "audio" : "library");
    const win = BrowserWindow.getFocusedWindow() || mainWindow;
    const filters =
      kind === "audio"
        ? [
            {
              name: "Audio",
              extensions: ["mp3", "wav", "ogg", "m4a", "aac", "flac", "opus", "webm"],
            },
            { name: "All files", extensions: ["*"] },
          ]
        : [
            {
              name: "Images & video",
              extensions: ["png", "jpg", "jpeg", "gif", "webp", "bmp", "mp4", "webm", "mov"],
            },
            { name: "All files", extensions: ["*"] },
          ];
    const result = await dialog.showOpenDialog(win, {
      title: opts?.title || (kind === "audio" ? "Attach sound" : "Attach images"),
      defaultPath,
      properties: ["openFile", "multiSelections"],
      filters,
    });
    if (result.canceled || !result.filePaths?.length) {
      return { ok: true, canceled: true, files: [], kind };
    }
    const importAlso = opts?.import !== false;
    let files = result.filePaths.map((p) => ({
      path: p,
      name: path.basename(p),
    }));
    if (importAlso) {
      const imported = importMediaFiles(result.filePaths, { kind });
      if (imported.imported?.length) files = imported.imported;
    }
    return { ok: true, canceled: false, files, root, kind };
  } catch (err) {
    return { ok: false, detail: err?.message || String(err), files: [] };
  }
});

ipcMain.handle("ava:media-import", async (_e, opts) => {
  try {
    const kind = String(opts?.kind || "images").toLowerCase() === "audio" ? "audio" : "images";
    return importMediaFiles(opts?.filePaths || [], { kind });
  } catch (err) {
    return { ok: false, detail: err?.message || String(err), imported: [] };
  }
});

ipcMain.handle("ava:media-open", async () => {
  const root = ensureMediaDirs();
  await shell.openPath(root);
  return { ok: true, root };
});

ipcMain.handle("ava:rewrite-preview", async (_e, opts) => {
  const env = await loadDesktopEnv();
  let context = [];
  try {
    if (opts.surface === "discord" && opts.channelId) {
      context = (await fetchDiscordHistory(env, opts.channelId, 20)).messages || [];
    } else if (opts.surface === "slack" && opts.channelId) {
      context = (await fetchSlackHistory(env, opts.channelId, 20)).messages || [];
    } else if (opts.surface === "telegram" && opts.channelId) {
      context = (await fetchTelegramHistory(env, opts.channelId, 20)).messages || [];
    }
  } catch {
    context = [];
  }
  return rewriteDraft(env, {
    text: opts.text,
    surface: opts.surface,
    context,
    provider: opts.provider || "dream",
    compare: Boolean(opts.compare),
  });
});

ipcMain.handle("ava:summarize", async (_e, opts) => {
  const env = await loadDesktopEnv();
  return summarizeChannel(env, opts);
});

ipcMain.handle("ava:rewrite-providers", async () => {
  const env = await loadDesktopEnv();
  return fetchRewriteProviders(env);
});

ipcMain.handle("ava:core-status", async () => {
  try {
    const env = await loadDesktopEnv();
    return await fetchCoreChatStatus(env);
  } catch (err) {
    return { ok: false, detail: err?.message || String(err) };
  }
});

/** @type {AbortController | null} */
let coreChatAbort = null;

ipcMain.handle("ava:core-chat", async (_e, opts) => {
  try {
    if (coreChatAbort) {
      try {
        coreChatAbort.abort();
      } catch {
        /* ignore */
      }
    }
    coreChatAbort = new AbortController();
    const env = await loadDesktopEnv();
    const result = await coreChat(env, {
      ...(opts || {}),
      signal: coreChatAbort.signal,
    });
    coreChatAbort = null;
    return result;
  } catch (err) {
    coreChatAbort = null;
    return { ok: false, detail: err?.message || String(err) };
  }
});

ipcMain.handle("ava:core-cancel", async () => {
  if (coreChatAbort) {
    try {
      coreChatAbort.abort();
    } catch {
      /* ignore */
    }
    coreChatAbort = null;
    return { ok: true, cancelled: true };
  }
  return { ok: true, cancelled: false };
});

ipcMain.handle("ava:core-enhance", async (_e, opts) => {
  try {
    const env = await loadDesktopEnv();
    return await coreChatEnhance(env, opts || {});
  } catch (err) {
    return { ok: false, detail: err?.message || String(err) };
  }
});

ipcMain.handle("ava:core-gold", async (_e, opts) => {
  try {
    const env = await loadDesktopEnv();
    return await coreChatGold(env, opts || {});
  } catch (err) {
    return { ok: false, detail: err?.message || String(err) };
  }
});

ipcMain.handle("ava:discord-edit", async (_e, opts) => {
  try {
    const env = await loadDesktopEnv();
    return await editDiscordMessage(
      env,
      opts?.channelId,
      opts?.messageId,
      opts?.text,
    );
  } catch (err) {
    return { ok: false, detail: err?.message || String(err) };
  }
});

ipcMain.handle("ava:discord-delete", async (_e, opts) => {
  try {
    const env = await loadDesktopEnv();
    return await deleteDiscordMessage(env, opts?.channelId, opts?.messageId);
  } catch (err) {
    return { ok: false, detail: err?.message || String(err) };
  }
});

ipcMain.handle("ava:feedback-targets", async () => ({
  ok: true,
  targets: FEEDBACK_TARGETS,
  templates: feedbackTemplates(),
}));

ipcMain.handle("ava:feedback-list", async (_e, opts) => {
  try {
    const env = await loadDesktopEnv();
    return await listFeedbackQueue(env, opts || {});
  } catch (err) {
    return { ok: false, detail: err?.message || String(err), feedback: [] };
  }
});

ipcMain.handle("ava:feedback-process-next", async () => {
  try {
    const env = await loadDesktopEnv();
    return await processFeedbackNext(env);
  } catch (err) {
    return { ok: false, detail: err?.message || String(err) };
  }
});

ipcMain.handle("ava:feedback-ack", async (_e, opts) => {
  try {
    const env = await loadDesktopEnv();
    return await ackFeedbackItem(env, opts?.id || opts?.feedbackId, opts?.note || "");
  } catch (err) {
    return { ok: false, detail: err?.message || String(err) };
  }
});

ipcMain.handle("ava:feedback-dual-post", async (_e, opts) => {
  try {
    const env = await loadDesktopEnv();
    return await dualPostFeedback(env, opts || {});
  } catch (err) {
    return { ok: false, detail: err?.message || String(err) };
  }
});

ipcMain.handle("ava:feedback-delete-discord", async (_e, opts) => {
  try {
    const env = await loadDesktopEnv();
    return await deleteDiscordMessage(
      env,
      opts?.channelId || FEEDBACK_TARGETS.discordDevelopment.id,
      opts?.messageId,
    );
  } catch (err) {
    return { ok: false, detail: err?.message || String(err) };
  }
});

ipcMain.handle("ava:feedback-delete-slack", async (_e, opts) => {
  try {
    const env = await loadDesktopEnv();
    return await deleteSlackMessage(
      env,
      opts?.channelId || FEEDBACK_TARGETS.slackFeedback.id,
      opts?.messageTs || opts?.messageId,
    );
  } catch (err) {
    return { ok: false, detail: err?.message || String(err) };
  }
});

ipcMain.handle("ava:feedback-clear-discord", async (_e, opts) => {
  try {
    const env = await loadDesktopEnv();
    return await clearDiscordOwnMessages(
      env,
      opts?.channelId || FEEDBACK_TARGETS.discordDevelopment.id,
      opts || {},
    );
  } catch (err) {
    return { ok: false, detail: err?.message || String(err), deleted: 0 };
  }
});

ipcMain.handle("ava:feedback-clear-slack", async (_e, opts) => {
  try {
    const env = await loadDesktopEnv();
    return await clearSlackOwnMessages(
      env,
      opts?.channelId || FEEDBACK_TARGETS.slackFeedback.id,
      opts || {},
    );
  } catch (err) {
    return { ok: false, detail: err?.message || String(err), deleted: 0 };
  }
});

ipcMain.handle("ava:feedback-clear-all", async (_e, opts) => {
  try {
    const env = await loadDesktopEnv();
    return await clearAllFeedbackAndStamp(env, opts || {});
  } catch (err) {
    return { ok: false, detail: err?.message || String(err) };
  }
});

ipcMain.handle("ava:cron-status", async () => {
  try {
    const env = await loadDesktopEnv();
    return await fetchCronStatus(env);
  } catch (err) {
    return { ok: false, detail: err?.message || String(err), jobs: [] };
  }
});

ipcMain.handle("ava:cron-run", async (_e, { id }) => {
  try {
    const env = await loadDesktopEnv();
    return await runCronJob(env, id);
  } catch (err) {
    return { ok: false, detail: err?.message || String(err) };
  }
});

ipcMain.handle("ava:cron-config", async (_e, body) => {
  try {
    const env = await loadDesktopEnv();
    return await configureCron(env, body);
  } catch (err) {
    return { ok: false, detail: err?.message || String(err) };
  }
});

ipcMain.handle("ava:reports-status", async () => {
  try {
    const env = await loadDesktopEnv();
    return await fetchReportsStatus(env);
  } catch (err) {
    return { ok: false, detail: err?.message || String(err) };
  }
});

ipcMain.handle("ava:finance", async (_e, opts = {}) => {
  try {
    const env = await loadDesktopEnv();
    return await fetchFinanceSuite(env, opts || {});
  } catch (err) {
    return { ok: false, detail: err?.message || String(err) };
  }
});

ipcMain.handle("ava:finance-action", async (_e, body = {}) => {
  try {
    const env = await loadDesktopEnv();
    return await postFinanceSuite(env, body || {});
  } catch (err) {
    return { ok: false, detail: err?.message || String(err) };
  }
});

ipcMain.handle("ava:biz", async () => {
  try {
    const env = await loadDesktopEnv();
    return await fetchBiz(env);
  } catch (err) {
    return { ok: false, detail: err?.message || String(err) };
  }
});

ipcMain.handle("ava:biz-action", async (_e, body = {}) => {
  try {
    const env = await loadDesktopEnv();
    return await postBiz(env, body || {});
  } catch (err) {
    return { ok: false, detail: err?.message || String(err) };
  }
});

ipcMain.handle("ava:early-login", async () => {
  try {
    const env = await loadDesktopEnv();
    return await tickEarlyLoginDesktop(env);
  } catch (err) {
    return { ok: false, detail: err?.message || String(err) };
  }
});

ipcMain.handle("ava:finance-receipt", async (_e, opts = {}) => {
  try {
    const win = BrowserWindow.getFocusedWindow() || mainWindow;
    const picked = await dialog.showOpenDialog(win, {
      title: "Attach receipt (image or PDF)",
      properties: ["openFile"],
      filters: [
        { name: "Receipts", extensions: ["png", "jpg", "jpeg", "gif", "webp", "pdf"] },
        { name: "All files", extensions: ["*"] },
      ],
    });
    if (picked.canceled || !picked.filePaths?.[0]) {
      return { ok: true, canceled: true };
    }
    const filePath = picked.filePaths[0];
    const buf = fs.readFileSync(filePath);
    if (buf.length > 8 * 1024 * 1024) {
      return { ok: false, detail: "file_too_large" };
    }
    const ext = path.extname(filePath).toLowerCase().replace(".", "");
    const mime =
      ext === "pdf"
        ? "application/pdf"
        : `image/${ext === "jpg" ? "jpeg" : ext || "png"}`;
    const env = await loadDesktopEnv();
    return await postFinanceSuite(env, {
      action: "attach-receipt",
      projectId: opts.projectId,
      account: opts.account,
      lineId: opts.lineId,
      filename: path.basename(filePath),
      mime,
      dataBase64: buf.toString("base64"),
    });
  } catch (err) {
    return { ok: false, detail: err?.message || String(err) };
  }
});

function safeAvaPath(target) {
  const folders = {
    reports: path.join(AVA_HOME, "media", "documents", "reports"),
    dumps: path.join(AVA_HOME, "media", "documents", "reports"),
    solarDays: path.join(AVA_HOME, "data", "state", "solar-history"),
    data: path.join(AVA_HOME, "data"),
    weatherGifs: path.join(AVA_HOME, "Media", "public", "images", "weather", "gifs"),
    weatherGifsCollector: path.join(AVA_HOME, "workstations", "weather-gif-collector"),
    claimPlans: path.join(AVA_HOME, "data", "ava-claim-plans"),
    root: AVA_HOME,
  };
  if (target && folders[target]) return folders[target];
  const abs = path.resolve(String(target || ""));
  const root = path.resolve(AVA_HOME);
  if (abs === root || abs.startsWith(root + path.sep)) return abs;
  return null;
}

ipcMain.handle("ava:open-folder", async (_e, { target } = {}) => {
  const dir = safeAvaPath(target || "reports");
  if (!dir) return { ok: false, detail: "path_not_allowed" };
  fs.mkdirSync(dir, { recursive: true });
  const err = await shell.openPath(dir);
  return err ? { ok: false, detail: err, path: dir } : { ok: true, path: dir };
});

ipcMain.handle("ava:open-path", async (_e, { target } = {}) => {
  const abs = safeAvaPath(target);
  if (!abs) return { ok: false, detail: "path_not_allowed" };
  if (!fs.existsSync(abs)) return { ok: false, detail: "missing", path: abs };
  const err = await shell.openPath(abs);
  return err ? { ok: false, detail: err, path: abs } : { ok: true, path: abs };
});

ipcMain.handle("ava:reveal-path", async (_e, { target } = {}) => {
  const abs = safeAvaPath(target);
  if (!abs || !fs.existsSync(abs)) return { ok: false, detail: "missing" };
  shell.showItemInFolder(abs);
  return { ok: true, path: abs };
});

ipcMain.handle("ava:ops-catalog", async () => ({
  ok: true,
  groups: listOpsCatalog(),
  core: AVA_CORE,
  running: runningOpsId,
}));

ipcMain.handle("ava:git-sync-prefs", async () => ({
  ok: true,
  prefs: loadGitSyncPrefs(AVA_HOME),
  last: lastGitSync,
  repo: AVA_HOME,
}));

ipcMain.handle("ava:git-sync-prefs-save", async (_e, patch = {}) => {
  const prefs = saveGitSyncPrefs(AVA_HOME, patch || {});
  scheduleGitAutoCheck();
  return { ok: true, prefs };
});

ipcMain.handle("ava:desk-ui-get", async () => ({
  ok: true,
  state: loadDeskUiState(DESK_ROOT),
  path: path.join(DESK_ROOT, "data", "state", "desk-ui.json"),
}));

ipcMain.handle("ava:desk-ui-save", async (_e, patch = {}) => {
  if (patch?.page) lastDeskPage = String(patch.page);
  const state = saveDeskUiState(patch || {}, DESK_ROOT);
  return { ok: true, state };
});

ipcMain.handle("ava:morning-report-check", async () =>
  checkMorningReportStatus(DESK_ROOT),
);

ipcMain.handle("ava:operator-purge", async () => {
  operatorPurgeRunning = true;
  deskCloseHandled = true;
  const result = await runOperatorPurgeScript(["--json"]);

  // Hard exit after purge (music/origin already stopped). Delay so renderer can show status.
  setTimeout(() => {
    try {
      for (const win of BrowserWindow.getAllWindows()) {
        if (!win.isDestroyed()) win.destroy();
      }
    } catch {
      /* ignore */
    }
    app.exit(0);
  }, 400);
  return result && typeof result === "object" ? result : { ok: false, detail: "no_result" };
});

ipcMain.handle("ava:git-status", async () => runGitSyncMode("status", { autoPull: false }));

ipcMain.handle("ava:git-check", async () =>
  runGitSyncMode("check", { stream: true, autoPull: false }),
);

ipcMain.handle("ava:git-pull", async () => runGitSyncMode("pull", { stream: true, autoPull: false }));

ipcMain.handle("ava:activity", async (_e, opts = {}) => {
  const limit = Number(opts.limit) || 220;
  const brain = await brainJson(`/api/activity?limit=${limit}`, { timeoutMs: 12000 });
  if (brain?.ok) {
    return { ...brain, runningOps: runningOpsId };
  }
  return {
    ok: false,
    detail: brain?.detail || "core unreachable on /api/activity",
    runningOps: runningOpsId,
    logs: [],
    processes: [],
    inflight: [],
  };
});

ipcMain.handle("ava:list-links", async () => listAvaLinks());

ipcMain.handle("ava:release-status", async (_e, { kind } = {}) => {
  const k = kind === "apps" ? "apps" : "plugins";
  return brainJson(`/api/${k}/status`);
});

ipcMain.handle("ava:release-action", async (_e, { kind, action, targets } = {}) => {
  const k = kind === "apps" ? "apps" : "plugins";
  const act = String(action || "").toLowerCase();
  if (!["bump", "build", "release"].includes(act)) {
    return { ok: false, detail: "bad_action" };
  }
  return brainJson(`/api/${k}/${act}`, {
    method: "POST",
    body: { targets: Array.isArray(targets) ? targets : [] },
    timeoutMs: 180000,
  });
});

ipcMain.handle("ava:open-link", async (_e, { url } = {}) => {
  const href = String(url || "").trim();
  if (!/^https?:\/\//i.test(href)) {
    return { ok: false, detail: "invalid_url" };
  }
  try {
    await shell.openExternal(href);
    return { ok: true };
  } catch (err) {
    return { ok: false, detail: err?.message || String(err) };
  }
});

ipcMain.handle("ava:ops-cancel", async () => {
  if (!runningOps) return { ok: true, detail: "idle" };
  try {
    runningOps.kill("SIGTERM");
  } catch (err) {
    return { ok: false, detail: err?.message || String(err) };
  }
  return { ok: true, detail: "signaled" };
});

ipcMain.handle("ava:ops-run", async (_e, { id }) => {
  const cmd = opsCommandById(String(id || ""));
  if (!cmd) return { ok: false, detail: "unknown_command" };
  if (runningOps) return { ok: false, detail: `busy:${runningOpsId}` };

  if (cmd.kind === "git-pull") {
    const result = await runGitSyncMode("pull", { stream: true, autoPull: false });
    return { ok: result.ok, detail: result.detail, result };
  }
  if (cmd.kind === "git-check") {
    const result = await runGitSyncMode("check", { stream: true, autoPull: false });
    return { ok: result.ok, detail: result.detail, result };
  }

  // URL launcher — open in system browser
  if (cmd.kind === "url" && cmd.url) {
    shell.openExternal(cmd.url);
    appendLine(`↗ opened ${cmd.url}`);
    return { ok: true, detail: `opened:${cmd.url}` };
  }

  // New-style: endpoint + body (POST to Python core)
  if (cmd.endpoint) {
    const url = `${brainOrigin()}${cmd.endpoint}`;
    runningOpsId = cmd.id;
    sendOps("ava:ops-start", { id: cmd.id, label: cmd.label, detail: `POST ${url}` });
    appendLine(`$ POST ${url}`);
    try {
      const res = await fetch(url, {
        method: "POST",
        headers: { "content-type": "application/json", ...brainFetchHeaders({}) },
        body: JSON.stringify(cmd.body || {}),
      });
      const text = await res.text();
      appendLine(`← ${res.status} ${text.slice(0, 200)}`);
      sendOps("ava:ops-done", { id: cmd.id, code: res.ok ? 0 : res.status });
      runningOpsId = null;
      return { ok: res.ok, detail: `http_${res.status}` };
    } catch (err) {
      appendLine(`error: ${err?.message || err}`);
      sendOps("ava:ops-done", { id: cmd.id, code: 1 });
      runningOpsId = null;
      return { ok: false, detail: err?.message || String(err) };
    }
  }

  if (cmd.kind === "http") {
    const url = `${brainOrigin()}${cmd.path}`;
    runningOpsId = cmd.id;
    sendOps("ava:ops-start", { id: cmd.id, label: cmd.label, detail: `${cmd.method} ${url}` });
    appendLine(`$ ${cmd.method} ${url}`);
    try {
      const res = await fetch(url, {
        method: cmd.method || "GET",
        headers: brainFetchHeaders(
          cmd.method && cmd.method !== "GET" ? { "content-type": "application/json" } : {},
        ),
      });
      const text = await res.text();
      appendLine(`← ${res.status}`);
      const clipped = text.length > 8000 ? `${text.slice(0, 8000)}\n…(truncated)` : text;
      for (const line of clipped.split(/\r?\n/)) appendLine(line);
      sendOps("ava:ops-done", { id: cmd.id, code: res.ok ? 0 : res.status });
      runningOpsId = null;
      return { ok: res.ok, detail: `http_${res.status}` };
    } catch (err) {
      appendLine(`error: ${err?.message || err}`);
      sendOps("ava:ops-done", { id: cmd.id, code: 1 });
      runningOpsId = null;
      return { ok: false, detail: err?.message || String(err) };
    }
  }

  const scriptPath = path.join(AVA_CORE, "scripts", cmd.script);
  if (!fs.existsSync(scriptPath)) {
    return { ok: false, detail: `missing_script:${cmd.script}` };
  }

  const bin = nodeBin();
  const args = [scriptPath, ...(cmd.args || [])];
  const childEnv = {
    ...process.env,
    PATH: `${path.join(os.homedir(), ".local", "bin")}:${process.env.PATH || ""}`,
    AVA_HANDOFF: AVA_HOME,
    ROOTMC_ENV_FILE: process.env.ROOTMC_ENV_FILE || "/home/rootrecord/.env",
    AVA_ENV_FILE: process.env.AVA_ENV_FILE || "/home/rootrecord/.env",
  };

  runningOpsId = cmd.id;
  sendOps("ava:ops-start", {
    id: cmd.id,
    label: cmd.label,
    detail: `${bin} scripts/${cmd.script} ${(cmd.args || []).join(" ")}`.trim(),
  });
  appendLine(
    `$ node scripts/${cmd.script}${(cmd.args || []).length ? ` ${cmd.args.join(" ")}` : ""}`,
  );

  return await new Promise((resolve) => {
    const child = spawn(bin, args, {
      cwd: AVA_CORE,
      env: childEnv,
      stdio: ["ignore", "pipe", "pipe"],
    });
    runningOps = child;
    const onChunk = (buf) => {
      for (const line of buf.toString("utf8").split(/\r?\n/)) {
        if (line.length) appendLine(line);
      }
    };
    child.stdout?.on("data", onChunk);
    child.stderr?.on("data", onChunk);
    child.on("error", (err) => {
      appendLine(`spawn error: ${err.message}`);
      runningOps = null;
      runningOpsId = null;
      sendOps("ava:ops-done", { id: cmd.id, code: 1 });
      resolve({ ok: false, detail: err.message });
    });
    child.on("close", (code, signal) => {
      appendLine(signal ? `← signal ${signal}` : `← exit ${code ?? "?"}`);
      runningOps = null;
      runningOpsId = null;
      sendOps("ava:ops-done", { id: cmd.id, code: code ?? 1, signal });
      resolve({
        ok: (code ?? 1) === 0,
        detail: signal ? `signal_${signal}` : `exit_${code}`,
      });
    });
  });
});

// Minecraft goes through the core HTTP API in both local and headless mode:
// brainOrigin() is 127.0.0.1:8787 when local, so there is one code path.
ipcMain.handle("ava:mc-status", async () => brainJson("/api/minecraft/status"));

ipcMain.handle("ava:mc-log", async (_e, opts = {}) => {
  const q = new URLSearchParams({
    bytes: String(Number(opts.bytes) || 200_000),
    lines: String(Number(opts.lines) || 220),
  });
  return brainJson(`/api/minecraft/log?${q}`);
});

ipcMain.handle("ava:mc-control", async (_e, { action } = {}) => {
  const a = String(action || "").trim().toLowerCase();
  if (!["start", "stop", "restart"].includes(a)) {
    return { ok: false, detail: "action must be start|stop|restart" };
  }
  return brainJson("/api/minecraft/control", {
    method: "POST",
    body: { action: a },
    timeoutMs: 120000,
  });
});

ipcMain.handle("ava:mc-rcon", async (_e, { command, target, allow } = {}) => {
  const cmd = String(command || "").trim();
  if (!cmd) return { ok: false, reason: "empty" };
  return brainJson("/api/minecraft/rcon", {
    method: "POST",
    body: {
      command: cmd,
      target: String(target || "test").trim() || "test",
      allow: Boolean(allow),
    },
    timeoutMs: 30000,
  });
});

ipcMain.handle("ava:stream-status", async () => {
  const [status, watch, eta, live] = await Promise.all([
    brainJson("/api/obs/status"),
    brainJson("/api/obs/volcano-watch"),
    brainJson("/api/obs/eruption-eta"),
    brainJson("/api/live"),
  ]);
  return {
    ok: status?.ok !== false && !status?.detail,
    status,
    watch: watch?.watch || null,
    eta: eta && typeof eta === "object" ? eta : null,
    live: live && typeof live === "object" ? live : null,
    detail: status?.detail || watch?.detail || eta?.detail || null,
  };
});

ipcMain.handle("ava:stream-preview", async () => brainJson("/api/obs/preview", { timeoutMs: 8000 }));

ipcMain.handle("ava:stream-action", async (_e, opts = {}) => {
  const action = String(opts.action || "").trim();
  const title = opts.title != null ? String(opts.title) : undefined;
  const description = opts.description != null ? String(opts.description) : undefined;
  const scene = opts.scene != null ? String(opts.scene) : undefined;
  if (action === "start" || action === "stop") {
    return {
      ok: false,
      detail: "obs_stream_control_disabled",
      hint: "Start/stop streaming in OBS. Ava does not launch OBS or control the stream transport.",
    };
  }
  if (action === "scene") {
    return brainJson("/api/obs/scene", {
      method: "POST",
      body: { scene: scene || "Be right back" },
    });
  }
  if (
    action === "mode-daily" ||
    action === "mode-all" ||
    action === "mode-weather" ||
    action === "mode-kilauea" ||
    action === "mode-hurricane"
  ) {
    const mode = action.replace("mode-", "");
    return brainJson("/api/obs/mode", {
      method: "POST",
      body: { mode },
    });
  }
  if (action === "metadata" || action === "metadata-restart") {
    return brainJson("/api/obs/metadata", {
      method: "POST",
      body: {
        title,
        description,
        restart: action === "metadata-restart",
        scene: scene || "Be right back",
      },
      timeoutMs: 90000,
    });
  }
  if (action === "watch-enter") {
    return brainJson("/api/obs/volcano-watch", {
      method: "POST",
      body: { action: "enter", title, description },
      timeoutMs: 90000,
    });
  }
  if (action === "watch-exit") {
    return brainJson("/api/obs/volcano-watch", {
      method: "POST",
      body: { action: "exit" },
      timeoutMs: 60000,
    });
  }
  if (action === "toast") {
    return brainJson("/api/obs/toast", {
      method: "POST",
      body: {
        title: title || "Test toast",
        body: description || "Desktop Streaming Ops",
      },
    });
  }
  if (action === "repair") {
    return brainJson("/api/obs/repair-kit", {
      method: "POST",
      body: {},
      timeoutMs: 60000,
    });
  }
  if (
    action === "mode-daily" ||
    action === "mode-all" ||
    action === "mode-hurricane" ||
    action === "mode-kilauea" ||
    action === "mode-weather"
  ) {
    const mode =
      action === "mode-all"
        ? "all"
        : action === "mode-hurricane"
        ? "hurricane"
        : action === "mode-kilauea"
          ? "kilauea"
          : action === "mode-weather"
            ? "weather"
            : "daily";
    return brainJson("/api/obs/mode", {
      method: "POST",
      body: { mode },
      timeoutMs: 120000,
    });
  }
  if (action === "reaction") {
    const reactionId = String(opts.reactionId || opts.id || "").trim();
    if (!reactionId) return { ok: false, detail: "reactionId_required" };
    return brainJson("/api/obs/reaction", {
      method: "POST",
      body: {
        reactionId,
        title: title || undefined,
        body: description || opts.body || "Manual Desktop trigger",
        url: opts.url || undefined,
        force: true,
        comment: opts.comment === true,
      },
      timeoutMs: 30000,
    });
  }
  return { ok: false, detail: "unknown_action" };
});
