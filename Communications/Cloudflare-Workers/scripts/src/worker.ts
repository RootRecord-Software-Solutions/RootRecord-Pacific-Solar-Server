/**
 * One worker in front of the one Vercel site.
 * Private paths are 404. Allowlisted paths are forwarded.
 * No cron, no D1, no second site, no holding-page HTML.
 */

import { isPrivatePath, isPublicRead, isPublicWrite, isReadMethod, normalisePath } from "./publicPaths";
import { offlineJson, offlineText, proxyToOrigin } from "./proxy";

export const DEFAULT_ORIGIN = "https://root-record-cloud.vercel.app";

export interface SiteEnv {
  VERCEL_ORIGIN_URL?: string;
}

export function originOf(env: SiteEnv): string {
  const raw = (env.VERCEL_ORIGIN_URL || DEFAULT_ORIGIN).trim().replace(/\/$/, "");
  if (!raw || /pages\.dev/i.test(raw) || /origin\.avaivy\.cloud/i.test(raw)) return DEFAULT_ORIGIN;
  return raw;
}

function gone(status: number): Response {
  return new Response(null, { status, headers: { "cache-control": "no-store" } });
}

export async function handleRequest(
  request: Request,
  env: SiteEnv,
  fetchImpl: typeof fetch = fetch,
): Promise<Response> {
  const url = new URL(request.url);
  const path = normalisePath(url.pathname);
  const origin = originOf(env);

  if (isPrivatePath(path)) return gone(404);

  const forward = () =>
    proxyToOrigin(request, {
      originUrl: origin,
      path,
      fetchImpl,
      offlineFallback: () => (path.startsWith("/api/") ? offlineJson() : offlineText()),
    });

  if (isPublicWrite(request.method, path)) return forward();
  if (!isReadMethod(request.method)) return gone(405);
  if (isPublicRead(path)) return forward();
  return gone(404);
}

export default {
  async fetch(request: Request, env: SiteEnv): Promise<Response> {
    return handleRequest(request, env);
  },
};
