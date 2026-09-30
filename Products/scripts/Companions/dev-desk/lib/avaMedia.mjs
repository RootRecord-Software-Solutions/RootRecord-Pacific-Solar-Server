/**
 * Central Ava media directory. Canonical path: $AVA_HOME/Media
 * (override AVA_MEDIA_DIR). public/{type}/{category} and private/{type}/{category}.
 */
import fs from "node:fs";
import path from "node:path";
import os from "node:os";

const IMAGE_EXT = new Set([
  ".png",
  ".jpg",
  ".jpeg",
  ".gif",
  ".webp",
  ".bmp",
  ".mp4",
  ".webm",
  ".mov",
]);

export function handoffRoot() {
  return (
    process.env.AVA_HANDOFF ||
    process.env.AVA_HOME ||
    path.join(os.homedir(), "Ava-Core")
  );
}

export function mediaRoot() {
  const fromEnv = String(process.env.AVA_MEDIA_DIR || "").trim();
  if (fromEnv) return fromEnv;
  const homeMedia = path.join(os.homedir(), "Media");
  if (fs.existsSync(homeMedia)) return homeMedia;
  const staged = path.join(handoffRoot(), "apps", "media");
  if (fs.existsSync(staged)) return staged;
  return homeMedia;
}

export function ensureMediaDirs() {
  const root = mediaRoot();
  for (const sub of [
    "public/audio/station",
    "public/audio/reports",
    "public/audio/crons",
    "public/audio/words",
    "public/audio/numbers",
    "public/audio/time_clips",
    "public/audio/sounds",
    "public/audio/voice",
    "public/audio/voice/generated",
    "public/audio/current",
    "public/video/clips",
    "public/video/reports",
    "public/video/current",
    "public/video/appearance",
    "public/images/channels",
    "public/images/character",
    "public/images/thumbnails",
    "public/images/discord",
    "public/images/slack",
    "public/images/telegram",
    "public/images/brand",
    "public/images/emojis/discord",
    "public/images/imports",
    "public/images/qrcodes",
    "public/documents/discord",
    "public/documents/reports",
    "public/documents/slack",
    "public/documents/telegram",
    "public/documents/persona",
    "public/documents/notes",
    "public/documents/plans",
    "public/documents/docs",
    "public/stream/overlays",
    "public/stream/obs-cams",
    "private/1-1/discord",
    "private/1-1/slack",
    "private/1-1/telegram",
    "private/life-story",
    "private/profiling",
    "private/accounts",
    "private/users",
    "private/documents/logs",
  ]) {
    fs.mkdirSync(path.join(root, sub), { recursive: true });
  }
  const voiceGen = path.join(root, "public", "audio", "voice", "generated");
  fs.mkdirSync(voiceGen, { recursive: true });
  const generatedAlias = path.join(root, "public", "audio", "generated");
  if (!fs.existsSync(generatedAlias)) {
    try {
      fs.symlinkSync("voice/generated", generatedAlias);
    } catch {
      fs.mkdirSync(generatedAlias, { recursive: true });
    }
  }
  return root;
}

export function mimeForFile(filePath) {
  const lower = String(filePath || "").toLowerCase();
  if (lower.endsWith(".png")) return "image/png";
  if (lower.endsWith(".jpg") || lower.endsWith(".jpeg")) return "image/jpeg";
  if (lower.endsWith(".gif")) return "image/gif";
  if (lower.endsWith(".webp")) return "image/webp";
  if (lower.endsWith(".bmp")) return "image/bmp";
  if (lower.endsWith(".mp4")) return "video/mp4";
  if (lower.endsWith(".webm")) return "video/webm";
  if (lower.endsWith(".mov")) return "video/quicktime";
  return "application/octet-stream";
}

export function isMediaFile(filePath) {
  return IMAGE_EXT.has(path.extname(String(filePath || "")).toLowerCase());
}

export function isImageFile(filePath) {
  const ext = path.extname(String(filePath || "")).toLowerCase();
  return [".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"].includes(ext);
}

/**
 * Recursively list media files under media root (follows library symlinks).
 */
export function listMediaFiles({ limit = 200, under = "" } = {}) {
  const root = ensureMediaDirs();
  const start = under
    ? path.join(root, under)
    : root;
  const out = [];
  const walk = (dir, depth = 0) => {
    if (out.length >= limit || depth > 6) return;
    let entries = [];
    try {
      entries = fs.readdirSync(dir, { withFileTypes: true });
    } catch {
      return;
    }
    for (const ent of entries) {
      if (out.length >= limit) break;
      if (ent.name.startsWith(".")) continue;
      if (ent.name === "private" && depth === 0) continue;
      if (ent.name === "files.log") continue;
      if (ent.name === "direct messages") continue;
      if (ent.name === "obs-backup") continue;
      if (ent.name === "__pycache__") continue;
      if (ent.name === "node_modules") continue;
      const abs = path.join(dir, ent.name);
      let st;
      try {
        st = fs.statSync(abs);
      } catch {
        continue;
      }
      if (st.isDirectory()) {
        walk(abs, depth + 1);
        continue;
      }
      if (!st.isFile() || !isMediaFile(abs)) continue;
      out.push({
        path: abs,
        name: ent.name,
        size: st.size,
        mtime: st.mtimeMs,
        relative: path.relative(root, abs),
        image: isImageFile(abs),
      });
    }
  };
  if (fs.existsSync(start)) walk(start);
  out.sort((a, b) => b.mtime - a.mtime);
  return { ok: true, root, under: under || "", files: out.slice(0, limit) };
}

/**
 * Copy external files into media/imports and return absolute paths.
 */
export function importMediaFiles(filePaths = [], { kind = "images" } = {}) {
  const root = ensureMediaDirs();
  const destDir =
    kind === "audio"
      ? path.join(root, "public", "audio", "reports")
      : path.join(root, "public", "images", "imports");
  fs.mkdirSync(destDir, { recursive: true });
  const imported = [];
  for (const raw of filePaths || []) {
    const src = path.resolve(String(raw || ""));
    if (!src || !fs.existsSync(src) || !fs.statSync(src).isFile()) continue;
    const base = path.basename(src);
    const stamp = new Date().toISOString().replace(/[:.]/g, "-").slice(0, 19);
    const dest = path.join(destDir, `${stamp}_${base}`);
    fs.copyFileSync(src, dest);
    imported.push({
      path: dest,
      name: path.basename(dest),
      size: fs.statSync(dest).size,
      relative: path.relative(root, dest).split(path.sep).join("/"),
      image: isImageFile(dest),
      audio: kind === "audio",
    });
  }
  return { ok: true, root, imported };
}

/** Validate paths exist and are files; return absolute paths. */
export function resolveExistingFiles(filePaths = [], { max = 10 } = {}) {
  const out = [];
  for (const raw of filePaths || []) {
    if (out.length >= max) break;
    const abs = path.resolve(String(raw || "").trim());
    if (!abs) continue;
    try {
      const st = fs.statSync(abs);
      if (!st.isFile()) continue;
      out.push(abs);
    } catch {
      /* skip */
    }
  }
  return out;
}
