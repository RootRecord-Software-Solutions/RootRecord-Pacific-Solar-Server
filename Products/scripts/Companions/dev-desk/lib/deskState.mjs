/**
 * Ava Desk UI session state — last tab, window bounds, music intent.
 * Lives under data/state/desk-ui.json (live tree).
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export function deskAvaRoot() {
  const home = process.env.HOME || process.env.USERPROFILE || "";
  const candidates = [
    process.env.AVA_HANDOFF,
    process.env.AVA_HOME,
    path.join(home, "Ava-Core"),
    path.join(home, "ava"),
  ].filter(Boolean);
  for (const c of candidates) {
    const root = path.resolve(c);
    if (
      fs.existsSync(path.join(root, "data", "state")) ||
      fs.existsSync(path.join(root, "apps", "desktop"))
    ) {
      return root;
    }
  }
  return path.join(home, "Ava-Core");
}

export function deskUiStatePath(root = deskAvaRoot()) {
  return path.join(root, "data", "state", "desk-ui.json");
}

const DEFAULTS = {
  page: "terminal",
  bounds: null,
  musicWanted: false,
  startAvaOnLaunch: false,
  radioLocal: false,
  musicTrack: null,
  closedAt: null,
  updatedAt: null,
};

export function loadDeskUiState(root = deskAvaRoot()) {
  const p = deskUiStatePath(root);
  try {
    if (!fs.existsSync(p)) return { ...DEFAULTS };
    const j = JSON.parse(fs.readFileSync(p, "utf8"));
    return {
      ...DEFAULTS,
      ...j,
      page: String(j.page || DEFAULTS.page),
      musicWanted: Boolean(j.musicWanted),
      startAvaOnLaunch: Boolean(j.startAvaOnLaunch),
      radioLocal:
        j.radioLocal === undefined || j.radioLocal === null
          ? null
          : Boolean(j.radioLocal),
      musicTrack: j.musicTrack || null,
      bounds:
        j.bounds && typeof j.bounds === "object"
          ? {
              x: Number(j.bounds.x),
              y: Number(j.bounds.y),
              width: Math.max(640, Number(j.bounds.width) || 1320),
              height: Math.max(480, Number(j.bounds.height) || 920),
            }
          : null,
    };
  } catch {
    return { ...DEFAULTS };
  }
}

export function saveDeskUiState(patch = {}, root = deskAvaRoot()) {
  const next = {
    ...loadDeskUiState(root),
    ...patch,
    updatedAt: new Date().toISOString(),
  };
  if (patch.bounds === null) next.bounds = null;
  const p = deskUiStatePath(root);
  fs.mkdirSync(path.dirname(p), { recursive: true });
  fs.writeFileSync(p, `${JSON.stringify(next, null, 2)}\n`, "utf8");
  return next;
}

function readJson(file, fallback = {}) {
  try {
    if (!fs.existsSync(file)) return fallback;
    return JSON.parse(fs.readFileSync(file, "utf8"));
  } catch {
    return fallback;
  }
}

function hstDayNow() {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: "Pacific/Honolulu",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(new Date());
}

function fileDayHst(filePath) {
  try {
    if (!fs.existsSync(filePath)) return null;
    const mtime = fs.statSync(filePath).mtimeMs;
    return new Intl.DateTimeFormat("en-CA", {
      timeZone: "Pacific/Honolulu",
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
    }).format(new Date(mtime));
  } catch {
    return null;
  }
}

/**
 * Morning report / boot status from existing JSON + markdown on disk.
 * Does not call Grok / Ara.
 */
export function checkMorningReportStatus(root = deskAvaRoot()) {
  const day = hstDayNow();
  const stateDir = path.join(root, "data", "state");
  const reportsDir = path.join(root, "Media", "public", "documents", "reports");

  const morningCurrent = path.join(reportsDir, "morning-report-current.md");
  const bootCurrent = path.join(reportsDir, "morning-boot-current.md");
  const bootDated = path.join(reportsDir, `morning-boot-${day}.md`);

  const morningDay = fileDayHst(morningCurrent);
  const bootCurrentDay = fileDayHst(bootCurrent);
  const bootDatedExists = fs.existsSync(bootDated);

  const replay = readJson(path.join(stateDir, "morning-boot-replay.json"), {});
  const automation = readJson(path.join(stateDir, "morning-boot-automation.json"), {});
  const dayBoard = readJson(path.join(stateDir, "day-board.json"), {});

  const morningDone = morningDay === day;
  const bootDone =
    bootDatedExists ||
    bootCurrentDay === day ||
    (String(replay.mp3 || replay.current || "").includes(day) && Boolean(replay.enabled));

  const dayBoardToday = String(dayBoard.day || "") === day;
  const dayBoardMorningSlots = Array.isArray(dayBoard?.slots?.morning)
    ? dayBoard.slots.morning.length
    : 0;
  const dayBoardFiredMorning = Object.keys(dayBoard.fired || {}).filter((k) =>
    String(k).startsWith("morning_"),
  ).length;

  let summary;
  if (morningDone && bootDone) {
    summary = `Morning report + boot report on file for ${day} HST.`;
  } else if (morningDone && !bootDone) {
    summary = `Morning report on file for ${day} HST — boot report missing.`;
  } else if (!morningDone && bootDone) {
    summary = `Boot report on file for ${day} HST — long-form morning report missing.`;
  } else {
    summary = `No morning report / boot report for ${day} HST yet (check only — no TTS spend).`;
  }

  return {
    ok: true,
    hstDay: day,
    morningReport: {
      done: morningDone,
      path: morningCurrent,
      day: morningDay,
      exists: fs.existsSync(morningCurrent),
    },
    morningBoot: {
      done: bootDone,
      currentPath: bootCurrent,
      datedPath: bootDated,
      currentDay: bootCurrentDay,
      datedExists: bootDatedExists,
      replayEnabled: Boolean(replay.enabled),
      replayMp3: replay.mp3 || replay.last_played || null,
      replayUntil: replay.until || null,
      automationEnabled: Boolean(automation.enabled),
    },
    dayBoard: {
      day: dayBoard.day || null,
      today: dayBoardToday,
      morningSlots: dayBoardMorningSlots,
      morningFired: dayBoardFiredMorning,
    },
    missing: !morningDone || !bootDone,
    summary,
    sources: {
      morningReportCurrent: morningCurrent,
      morningBootCurrent: bootCurrent,
      morningBootDated: bootDated,
      morningBootReplay: path.join(stateDir, "morning-boot-replay.json"),
      morningBootAutomation: path.join(stateDir, "morning-boot-automation.json"),
      dayBoard: path.join(stateDir, "day-board.json"),
      deskUi: deskUiStatePath(root),
    },
  };
}
