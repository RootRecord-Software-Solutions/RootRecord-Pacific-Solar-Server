/**
 * Paths the one Vercel site may be reached on.
 * Reads are named. Writes are refused except POST /api/chat.
 * Private prefixes stay 404 even if a later page is added under them.
 */

const PUBLIC_PAGES = new Set([
  "/",
  "/timeline",
  "/blog",
  "/dev",
  "/login",
  "/reports",
  "/status",
  "/goals",
  "/goals/new",
  "/favicon.ico",
  "/robots.txt",
]);

const PUBLIC_PREFIX = ["/blog/", "/goals/", "/_next/", "/media/"];

/** Same named reads the Vercel app already proxies. Not every /api/* path. */
const PUBLIC_API = new Set([
  "/api/air-quality/current",
  "/api/dashboard",
  "/api/desk/notifications",
  "/api/disruption-banner",
  "/api/earthquakes/global",
  "/api/kilauea",
  "/api/live",
  "/api/health",
  "/api/media/public",
  "/api/mobile/kilauea-live-streams",
  "/api/mobile/kilauea-situation",
  "/api/news/global",
  "/api/photos/gallery",
  "/api/reports",
  "/api/reports/current",
  "/api/site-config",
  "/api/solar",
  "/api/solar/history",
  "/api/solar/rollups",
  "/api/status",
  "/api/weather",
  "/api/minecraft/status",
]);

const PUBLIC_API_PREFIX = ["/api/photos/file/", "/api/media/public/"];

const PRIVATE_PREFIX = [
  "/ops",
  "/api/ops",
  "/api/business",
  "/api/finance",
  "/api/biz",
  "/api/local",
  "/api/crons",
  "/api/cron",
  "/api/brain",
  "/ecoflow",
  "/minecraft",
  "/system",
  "/host",
];

function hits(path: string, prefixes: string[]): boolean {
  return prefixes.some((prefix) => path === prefix || path.startsWith(prefix + "/"));
}

export function normalisePath(path: string): string {
  if (path.length > 1 && path.endsWith("/")) return path.replace(/\/+$/, "") || "/";
  return path;
}

export function isPrivatePath(path: string): boolean {
  return hits(path, PRIVATE_PREFIX);
}

export function isReadMethod(method: string): boolean {
  return method === "GET" || method === "HEAD";
}

/** The Vercel app's only public write. */
export function isPublicWrite(method: string, path: string): boolean {
  return method === "POST" && path === "/api/chat";
}

export function isPublicRead(path: string): boolean {
  if (isPrivatePath(path)) return false;
  if (PUBLIC_PAGES.has(path) || PUBLIC_API.has(path)) return true;
  if (PUBLIC_PREFIX.some((prefix) => path.startsWith(prefix))) return true;
  return PUBLIC_API_PREFIX.some((prefix) => path.startsWith(prefix));
}
