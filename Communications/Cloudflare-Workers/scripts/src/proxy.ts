/**
 * Timeout proxy to the one Vercel origin.
 * Offline answers are plain 503 responses. No holding-page HTML.
 */

const EDGE_FAILURE = new Set([502, 503, 522, 523, 524, 530]);

export interface ProxyOptions {
  originUrl: string;
  path: string;
  timeoutMs?: number;
  fetchImpl?: typeof fetch;
  offlineFallback: () => Response;
}

function outboundHeaders(request: Request): Headers {
  const headers = new Headers(request.headers);
  for (const name of [
    "host",
    "cf-connecting-ip",
    "cf-ipcountry",
    "cf-ray",
    "cf-visitor",
    "cf-ew-via",
    "cf-worker",
    "x-forwarded-for",
    "x-forwarded-proto",
    "x-real-ip",
    "connection",
    "content-length",
  ]) {
    headers.delete(name);
  }
  return headers;
}

export function offlineJson(): Response {
  return Response.json({ ok: false, detail: "origin offline" }, { status: 503 });
}

export function offlineText(): Response {
  return new Response("Origin temporarily unavailable.\n", {
    status: 503,
    headers: { "content-type": "text/plain; charset=utf-8", "cache-control": "no-store" },
  });
}

export async function proxyToOrigin(request: Request, opts: ProxyOptions): Promise<Response> {
  const fetchImpl = opts.fetchImpl ?? fetch;
  const timeoutMs = opts.timeoutMs ?? 8000;
  const target = opts.originUrl.replace(/\/$/, "") + opts.path + new URL(request.url).search;
  const method = request.method;
  const canBody = method !== "GET" && method !== "HEAD";
  try {
    const response = await fetchImpl(target, {
      method,
      headers: outboundHeaders(request),
      body: canBody ? request.body : undefined,
      redirect: "manual",
      signal: AbortSignal.timeout(timeoutMs),
    });
    if (EDGE_FAILURE.has(response.status)) return opts.offlineFallback();
    return response;
  } catch {
    return opts.offlineFallback();
  }
}
