#!/usr/bin/env node
'use strict';

/**
 * Telegram insurance relay for the Hawaii network-globe collector.
 *
 * Role, exactly as scoped in Claude_Current_Understanding.md:
 *  - This is NOT part of AWS's live feed. Nothing sent here is ever
 *    replayed into AWS, on reconnect or otherwise.
 *  - It exists purely as an off-box, durable copy of what the collector
 *    saw while SSH to AWS was unreachable, for later human reference.
 *  - No on-disk buffering. Batches live in memory only; if the process
 *    dies mid-outage, the in-flight batch is lost -- that's an accepted
 *    tradeoff for "never accumulate anything," not an oversight. If you
 *    want disk durability for this specific in-memory-loss case, that's
 *    a deliberate call to make later, not a default.
 *  - Matches the existing "Root Record Data Relay" channel convention:
 *    zip files named rootrecord-YYYYMMDD-HHMM-<hash>.zip, same shape as
 *    what rr-packer was already producing there.
 *
 * Config (env, all loaded from /home/rootrecord/master/master-key.env via
 * loadMasterEnv() -- this is the SAME file and SAME var names packer.py
 * (the AWS-side half of this bot pair) reads, confirmed by reading
 * packer.py's own source. Verified working 2026-09-22 via the three-gate
 * check: getMe -> rootsender_bot, sendMessage -> ok:true, getChat title
 * -> "Root Record Data Relay".
 *   RR_DATAPACK_CHAT_ID      - required to actually send; channel/chat id
 *                              for "Root Record Data Relay"
 *   RR_DATAPACK_SEND_BOT_TOKEN (fallback RR_DATAPACK_BOT_TOKEN, then
 *                              RR_TELEGRAM_BOT_TOKEN) - bot token for
 *                              @rootsender_bot, same fallback order
 *                              packer.py uses
 *   TELEGRAM_BATCH_MS        - default 900000 (15 min), matches existing
 *                              channel cadence
 *   TELEGRAM_BATCH_MAX_RECORDS - default 5000, safety valve so a very
 *                              long outage doesn't grow one batch forever;
 *                              flushes early if hit
 *
 * NOTE: CHAT_ID must NOT be read as a top-level const at module-load time
 * -- master-key.env hasn't been loaded yet at that point, so it would
 * always resolve to ''. It's read lazily via getChatId(), same pattern
 * as getBotToken(), the first time it's actually needed.
 */

const { spawn } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');
const crypto = require('crypto');

const MASTER_ENV = '/home/rootrecord/master/master-key.env';
const BATCH_MS = Number(process.env.TELEGRAM_BATCH_MS || 15 * 60 * 1000);
const BATCH_MAX_RECORDS = Number(process.env.TELEGRAM_BATCH_MAX_RECORDS || 5000);

let botToken = '';
let chatId = '';
let batch = [];
let flushTimer = null;
let sending = false;
let started = false;

function loadMasterEnv() {
  try {
    if (!fs.existsSync(MASTER_ENV)) return;
    for (const line of fs.readFileSync(MASTER_ENV, 'utf8').split('\n')) {
      const t = line.trim();
      if (!t || t.startsWith('#') || !t.includes('=')) continue;
      const [k, ...rest] = t.split('=');
      const key = k.trim();
      const val = rest.join('=').trim().replace(/^['"]|['"]$/g, '');
      if (key && !(key in process.env)) process.env[key] = val;
    }
  } catch {}
}

function getBotToken() {
  if (botToken) return botToken;
  loadMasterEnv();
  botToken = (
    process.env.RR_DATAPACK_SEND_BOT_TOKEN
    || process.env.RR_DATAPACK_BOT_TOKEN
    || process.env.RR_TELEGRAM_BOT_TOKEN
    || ''
  ).trim();
  return botToken;
}

function getChatId() {
  if (chatId) return chatId;
  loadMasterEnv();
  chatId = (process.env.RR_DATAPACK_CHAT_ID || '').trim();
  return chatId;
}

function apiBase() {
  const token = getBotToken();
  return token ? `https://api.telegram.org/bot${token}` : '';
}

// Same filename shape already in use in the relay channel:
// rootrecord-YYYYMMDD-HHMM-<hash>.zip
function makePackName() {
  const d = new Date();
  const stamp = `${d.getUTCFullYear()}${String(d.getUTCMonth() + 1).padStart(2, '0')}${String(d.getUTCDate()).padStart(2, '0')}`
    + `-${String(d.getUTCHours()).padStart(2, '0')}${String(d.getUTCMinutes()).padStart(2, '0')}`;
  const hash = crypto.randomBytes(6).toString('hex');
  return `rootrecord-${stamp}-${hash}.zip`;
}

function zipFile(srcPath, destPath) {
  return new Promise((resolve, reject) => {
    const p = spawn('zip', ['-j', '-q', destPath, srcPath], { stdio: ['ignore', 'ignore', 'pipe'] });
    let err = '';
    p.stderr.on('data', c => { err += c; });
    p.on('close', code => code === 0 ? resolve() : reject(new Error(`zip exit ${code}: ${err.trim()}`)));
    p.on('error', reject);
  });
}

async function sendDocument(zipPath, caption) {
  const base = apiBase();
  if (!base || !getChatId()) return false;
  const fileBuf = fs.readFileSync(zipPath);
  const form = new FormData();
  form.set('chat_id', String(getChatId()));
  form.set('caption', caption.slice(0, 1024));
  form.set('document', new Blob([fileBuf]), path.basename(zipPath));
  const res = await fetch(`${base}/sendDocument`, { method: 'POST', body: form, signal: AbortSignal.timeout(30000) });
  let body = {};
  try { body = await res.json(); } catch {}
  if (!res.ok || !body.ok) {
    console.error(`telegram-relay: sendDocument failed: ${JSON.stringify(body).slice(0, 300)}`);
    return false;
  }
  return true;
}

async function flush() {
  if (sending || batch.length === 0) return;
  if (!apiBase() || !getChatId()) {
    // No token / no chat id configured -- nothing we can do, drop silently
    // rather than grow forever. This is insurance, not the source of truth.
    batch = [];
    return;
  }
  sending = true;
  const records = batch;
  batch = [];
  const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'rr-relay-'));
  const ndjsonPath = path.join(tmpDir, 'records.ndjson');
  const zipName = makePackName();
  const zipPath = path.join(tmpDir, zipName);
  try {
    fs.writeFileSync(ndjsonPath, records.map(r => JSON.stringify(r)).join('\n') + '\n');
    await zipFile(ndjsonPath, zipPath);
    const caption = `RootRecord datapack ${zipName}\nHawaii insurance relay — ${records.length} records, SSH to AWS unreachable at send time.\nNot replayed into AWS.`;
    const ok = await sendDocument(zipPath, caption);
    if (!ok) {
      console.error(`telegram-relay: dropping batch of ${records.length} records (send failed, no internet or bad config)`);
    }
  } catch (e) {
    console.error(`telegram-relay: flush error: ${e.message}`);
  } finally {
    try { fs.rmSync(tmpDir, { recursive: true, force: true }); } catch {}
    sending = false;
  }
}

function offer(record) {
  if (!started) return;
  batch.push(record);
  if (batch.length >= BATCH_MAX_RECORDS) flush().catch(() => {});
}

function start() {
  if (started) return;
  started = true;
  if (!getChatId()) {
    console.error('telegram-relay: RR_DATAPACK_CHAT_ID not set — insurance relay is inert until configured');
  }
  flushTimer = setInterval(() => flush().catch(() => {}), BATCH_MS);
}

function stop() {
  started = false;
  if (flushTimer) clearInterval(flushTimer);
  // Deliberately not flushing on shutdown -- an in-flight batch at
  // process-exit time is an accepted loss, per the no-disk-buffering
  // design. If that turns out to matter in practice, revisit.
}

module.exports = { offer, start, stop };
