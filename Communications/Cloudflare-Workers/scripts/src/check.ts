/**
 * Local proof. No deploy.
 * A private path returns 404. An allowlisted path is forwarded to the Vercel origin.
 */

import { accountIdPresent } from "./envload.ts";
import { handleRequest } from "./worker.ts";

const ORIGIN = "https://root-record-cloud.vercel.app";

function assert(condition: boolean, message: string): void {
  if (!condition) {
    console.error("FAIL " + message);
    process.exit(1);
  }
  console.log("PASS " + message);
}

const forwarded: string[] = [];

const fetchImpl: typeof fetch = async (input) => {
  const target = typeof input === "string" ? input : input instanceof URL ? input.toString() : input.url;
  forwarded.push(target);
  return new Response("ok", { status: 200 });
};

const env = { VERCEL_ORIGIN_URL: ORIGIN };

const privateResponse = await handleRequest(new Request("https://rootrecord.cloud/ops"), env, fetchImpl);
assert(privateResponse.status === 404, "private /ops is 404");
assert(forwarded.length === 0, "private /ops was not forwarded");

const finance = await handleRequest(new Request("https://rootrecord.cloud/api/finance"), env, fetchImpl);
assert(finance.status === 404, "private /api/finance is 404");

const write = await handleRequest(
  new Request("https://rootrecord.cloud/status", { method: "POST" }),
  env,
  fetchImpl,
);
assert(write.status === 405, "POST /status is 405");

const status = await handleRequest(new Request("https://rootrecord.cloud/status"), env, fetchImpl);
assert(status.status === 200, "GET /status forwarded");
assert(forwarded.at(-1) === ORIGIN + "/status", "GET /status target is the Vercel origin");

const solar = await handleRequest(new Request("https://rootrecord.cloud/api/solar"), env, fetchImpl);
assert(solar.status === 200, "GET /api/solar forwarded");
assert(forwarded.at(-1) === ORIGIN + "/api/solar", "GET /api/solar target is the Vercel origin");

console.log(accountIdPresent() ? "PASS CLOUDFLARE_ACCOUNT_ID present" : "FAIL CLOUDFLARE_ACCOUNT_ID missing");
if (!accountIdPresent()) process.exit(1);

console.log("check ok");
