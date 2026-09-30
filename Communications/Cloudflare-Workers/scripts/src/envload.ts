/**
 * Allowlist loader. Same rule as Energy/lib/envload.py.
 * Reads master-key.env. Never prints values. Never reads a second env file.
 */

import { readFileSync } from "node:fs";

export const MASTER_KEY_ENV = "/home/rootrecord/master/master-key.env";
const ALLOW = new Set(["CLOUDFLARE_ACCOUNT_ID"]);

export function accountIdPresent(path = MASTER_KEY_ENV): boolean {
  let text: string;
  try {
    text = readFileSync(path, "utf8");
  } catch {
    return false;
  }
  for (const line of text.split("\n")) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#") || !trimmed.includes("=")) continue;
    const splitAt = trimmed.indexOf("=");
    const key = trimmed.slice(0, splitAt).trim();
    if (!ALLOW.has(key)) continue;
    const value = trimmed.slice(splitAt + 1).trim().replace(/^["']|["']$/g, "");
    if (value.length > 0) return true;
  }
  return false;
}
